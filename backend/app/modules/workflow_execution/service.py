from uuid import UUID, uuid4
from datetime import datetime, timezone, timedelta, date
from fastapi import HTTPException
import sqlalchemy as sa
from sqlalchemy.future import select

from app.modules.workflow_execution.models import WorkflowRun, WorkflowRunStep, WorkflowRunFailure
from app.modules.workflow_scheduler.models import Phase2WorkflowSchedule
from app.modules.registry.repositories import resolve_user_uuid
from app.modules.authorization.decision_service import AuthorizationDecisionService
from app.modules.authorization.schemas import AuthorizationRequest
from app.modules.audit.event_service import GovernanceEventService
from app.modules.audit.event_codes import WorkflowEventCode
from app.shared.response_utils import ResponseHelper
from app.shared.db_compat import db_get, db_flush, execute_statement

from app.modules.workflow_execution.state_machine import WorkflowRunStateError, WorkflowStateMachine
from app.modules.workflow_execution.output_parser import OutputParser
from app.modules.workflow_execution.run_output_service import RunOutputService
from app.modules.notifications.service import ScheduleNotificationService
from app.modules.workflow_scheduler.service import calculate_next_run_at

class WorkflowRunService:
    def __init__(self):
        self.event_service = GovernanceEventService()
        self.notification_service = ScheduleNotificationService()
        self.run_output_service = RunOutputService()

    @staticmethod
    async def create_run(db, schedule_id: UUID, trigger_type: str, current_user) -> WorkflowRun:
        user_id = current_user.id if hasattr(current_user, "id") else current_user
        service = WorkflowRunService()
        return await service.create_run_internal(schedule_id, trigger_type, user_id, db)

    async def create_run_internal(self, schedule_id: UUID, trigger_type: str, triggered_by_user_id: UUID | None, db) -> WorkflowRun:
        sched = await db_get(db, Phase2WorkflowSchedule, schedule_id)
        if not sched:
            raise HTTPException(status_code=404, detail="Workflow schedule not found")
        
        actor_uuid = resolve_user_uuid(db, triggered_by_user_id) if triggered_by_user_id else None
        
        # Concurrency policy check
        concurrency_conflict = False
        sched_policy = sched.concurrency_policy.value if hasattr(sched.concurrency_policy, "value") else str(sched.concurrency_policy)
        
        if sched_policy == "SKIP_IF_RUNNING":
            stmt = select(sa.func.count(WorkflowRun.id)).where(
                WorkflowRun.schedule_id == schedule_id,
                WorkflowRun.run_status.in_(["QUEUED", "RUNNING"])
            )
            res = await execute_statement(db, stmt)
            active_count = res.scalar() or 0
            if active_count > 0:
                concurrency_conflict = True

        status = "SKIPPED" if concurrency_conflict else "QUEUED"
        
        # Generate run code
        today_str = date.today().strftime('%Y%m%d')
        hex_suffix = uuid4().hex[:6].upper()
        run_code = f"RUN-{today_str}-{hex_suffix}"
        
        run = WorkflowRun(
            id=uuid4(),
            tenant_id=sched.tenant_id,
            schedule_id=sched.id,
            workflow_id=sched.workflow_id,
            run_code=run_code,
            trigger_type=trigger_type,
            triggered_by_user_id=actor_uuid,
            triggered_by_actor_type="USER" if triggered_by_user_id else "SYSTEM",
            run_status=status,
            risk_level=sched.risk_level,
            created_by=actor_uuid,
            updated_by=actor_uuid
        )
        db.add(run)
        
        # Update schedule next/last run times
        sched.last_run_at = datetime.now(timezone.utc)
        sched_type = sched.schedule_type.value if hasattr(sched.schedule_type, 'value') else sched.schedule_type
        sched.next_run_at = calculate_next_run_at(sched_type, sched.cron_expression, sched.timezone, sched.start_at, sched.metadata_json)

        await db_flush(db)
        
        await self.event_service.publish_run_queued(run.id, sched.id, db)
        
        return run

    async def start_run(self, run_id: UUID, db) -> WorkflowRun:
        run = await db_get(db, WorkflowRun, run_id)
        if not run:
            raise HTTPException(status_code=404, detail="Workflow run not found")
        
        WorkflowStateMachine.validate_transition(run.run_status, "RUNNING")
        
        run.run_status = "RUNNING"
        run.started_at = datetime.now(timezone.utc)
        await db_flush(db)
        
        await self.event_service.publish_run_started(run_id, run.schedule_id, db)
        
        # Phase 4 Additive Governance Event Publish
        try:
            from app.modules.events.service import EventPublisherService
            from app.modules.events.schemas import GovernanceEventCreate
            publisher = EventPublisherService()
            event_create = GovernanceEventCreate(
                event_type="WORKFLOW_RUN_STARTED",
                event_category="Workflow",
                event_version="1.0",
                occurred_at=datetime.now(timezone.utc),
                source_service="workflow_execution",
                actor_json={"user_id": str(run.triggered_by_user_id or run.tenant_id)},
                subject_json={"entity_type": "workflow_runs", "entity_id": str(run.id)},
                correlation_id=run.id,
                payload_json={"schedule_id": str(run.schedule_id), "workflow_id": str(run.workflow_id), "run_code": run.run_code},
                classification="INTERNAL",
                retention_class="STANDARD_90_DAYS"
            )
            publisher.publish_event(db, event_create, tenant_id=run.tenant_id)
        except Exception as ex:
            print(f"Warning: Phase 4 WORKFLOW_RUN_STARTED publish skipped: {ex}")
            
        return run

    async def execute_run(self, run_id: UUID, db) -> None:
        run = await db_get(db, WorkflowRun, run_id)
        if not run:
            return
        
        schedule = await db_get(db, Phase2WorkflowSchedule, run.schedule_id)
        if not schedule:
            return

        # Pre-create all expected step records in PENDING state (strictly 4 steps)
        step_codes = [
            ("POLICY_CHECK", "POLICY_CHECK", 1),
            ("AGENT_INVOCATION", "INVOCATION", 2),
            ("OUTPUT_PARSE", "PARSING", 3),
            ("AUDIT_PUBLISH", "AUDIT", 4)
        ]
        
        stmt_steps = select(WorkflowRunStep).where(WorkflowRunStep.run_id == run_id)
        res_steps = await execute_statement(db, stmt_steps)
        existing_steps = res_steps.scalars().all()
        steps_map = {s.step_code: s for s in existing_steps}
        
        for code, stype, order in step_codes:
            if code not in steps_map:
                step = WorkflowRunStep(
                    id=uuid4(),
                    tenant_id=run.tenant_id,
                    run_id=run_id,
                    step_code=code,
                    step_order=order,
                    step_type=stype,
                    step_status="PENDING",
                    created_by=run.created_by,
                    updated_by=run.updated_by
                )
                db.add(step)
                steps_map[code] = step
        await db_flush(db)

        try:
            # Start execution
            if run.run_status in ["QUEUED", "RETRY_QUEUED"]:
                run = await self.start_run(run_id, db)

            # Get primary assignment (required for policy & agent steps)
            primary_assignment = None
            if schedule.agent_assignments:
                for ass in schedule.agent_assignments:
                    role_str = ass.assignment_role.value if hasattr(ass.assignment_role, "value") else str(ass.assignment_role)
                    if role_str == "PRIMARY":
                        primary_assignment = ass
                        break
                if not primary_assignment:
                    primary_assignment = schedule.agent_assignments[0]

            # -------------------------------------------------------------
            # STEP 1: POLICY_CHECK
            # -------------------------------------------------------------
            step_policy = steps_map["POLICY_CHECK"]
            step_policy.step_status = "RUNNING"
            step_policy.started_at = datetime.now(timezone.utc)
            await db_flush(db)

            sched_status = schedule.schedule_status.value if hasattr(schedule.schedule_status, "value") else str(schedule.schedule_status)
            if sched_status != "ACTIVE":
                await self.event_service.publish_agent_boundary_failed(
                    run_id=run_id,
                    agent_id=primary_assignment.agent_id if primary_assignment else None,
                    reason=f"Schedule {schedule.schedule_code} is inactive.",
                    db=db
                )
                raise ValueError(f"Schedule {schedule.schedule_code} is not ACTIVE (current: {sched_status})")
            
            if not primary_assignment:
                await self.event_service.publish_agent_boundary_failed(
                    run_id=run_id,
                    agent_id=None,
                    reason="No agent assignments configured.",
                    db=db
                )
                raise ValueError(f"No agent assignments configured for schedule {schedule.schedule_code}")

            await self.event_service.publish_agent_boundary_passed(run_id, primary_assignment.agent_id, db)
            step_policy.step_status = "COMPLETED"
            step_policy.completed_at = datetime.now(timezone.utc)
            await db_flush(db)

            # -------------------------------------------------------------
            # STEP 2: AGENT_INVOCATION
            # -------------------------------------------------------------
            step_agent = steps_map["AGENT_INVOCATION"]
            step_agent.step_status = "RUNNING"
            step_agent.started_at = datetime.now(timezone.utc)
            await db_flush(db)

            from app.modules.agent_runtime.boundary_checker import BoundaryChecker
            checker = BoundaryChecker()
            passed, reason = await checker.check(primary_assignment, requested_tool=None, db=db)
            if not passed:
                raise ValueError(f"Boundary check failed: {reason}")
            
            from app.modules.agent_runtime.service import AgentRuntimeService
            runtime = AgentRuntimeService()
            context = run.context_json or {}
            
            await self.event_service.publish_agent_execution_started(run_id, primary_assignment.agent_id, db)
            
            raw_output = await runtime.invoke_agent(run_id, primary_assignment, context, db)

            await self.event_service.publish_agent_execution_completed(run_id, primary_assignment.agent_id, {}, db)

            step_agent.step_status = "COMPLETED"
            step_agent.completed_at = datetime.now(timezone.utc)
            await db_flush(db)

            # -------------------------------------------------------------
            # STEP 3: OUTPUT_PARSE
            # -------------------------------------------------------------
            step_parse = steps_map["OUTPUT_PARSE"]
            step_parse.step_status = "RUNNING"
            step_parse.started_at = datetime.now(timezone.utc)
            await db_flush(db)

            parsed_output = OutputParser.parse(raw_output)
            output_rec = await self.run_output_service.save_output(run_id, parsed_output, db)
            
            # SLA Check logic inside the try-except wrapper
            started_dt = run.started_at
            if started_dt:
                if started_dt.tzinfo is None:
                    started_dt = started_dt.replace(tzinfo=timezone.utc)
                max_dur = schedule.max_runtime_seconds or 1800
                if datetime.now(timezone.utc) > started_dt + timedelta(seconds=max_dur):
                    raise ValueError("Execution exceeded max runtime SLA")

            await self.event_service.publish_output_generated(run_id, output_rec.id, db)
            
            step_parse.step_status = "COMPLETED"
            step_parse.completed_at = datetime.now(timezone.utc)
            await db_flush(db)

            # -------------------------------------------------------------
            # STEP 4: AUDIT_PUBLISH
            # -------------------------------------------------------------
            step_audit = steps_map["AUDIT_PUBLISH"]
            step_audit.step_status = "RUNNING"
            step_audit.started_at = datetime.now(timezone.utc)
            await db_flush(db)

            run = await self.complete_run(run_id, db, primary_assignment=primary_assignment, parsed_output=parsed_output)
            
            # Check for high/critical outputs for escalation
            if self.run_output_service.check_high_risk(parsed_output):
                # Trigger escalation via notification service
                from app.modules.workflow_execution.models import WorkflowRunFailure
                esc_failure = WorkflowRunFailure(
                    id=uuid4(),
                    tenant_id=run.tenant_id,
                    run_id=run_id,
                    failure_type="HIGH_RISK_DETECTED",
                    failure_code="RISK_THRESHOLD",
                    failure_message=f"High risk output detected (Severity: {parsed_output.severity}, Score: {parsed_output.risk_score})",
                    escalation_required=True,
                    created_by=run.created_by,
                    updated_by=run.updated_by
                )
                db.add(esc_failure)
                await db_flush(db)
                await self.notification_service.notify_run_failed(run, esc_failure, db)

            step_audit.step_status = "COMPLETED"
            step_audit.completed_at = datetime.now(timezone.utc)
            await db_flush(db)

        except ValueError as ve:
            # specifically for SLA or boundary checks inside execute_run
            if "max runtime SLA" in str(ve):
                await self.fail_run(run_id, "SLA_BREACH", "RUN_TIMEOUT", str(ve), None, db)
            elif "Boundary check failed" in str(ve):
                await self.fail_run(run_id, "BOUNDARY_VIOLATION", "AGENT_BLOCKED", str(ve), None, db)
            else:
                await self.fail_run(run_id, "VALIDATION_FAILURE", "SCHEDULE_INACTIVE", str(ve), None, db)
        except Exception as e:
            await self.fail_run(run_id, "EXECUTION_FAILURE", "SYSTEM_ERROR", str(e), None, db)

    async def complete_run(self, run_id: UUID, db, primary_assignment=None, parsed_output=None) -> WorkflowRun:
        run = await db_get(db, WorkflowRun, run_id)
        if not run:
            raise HTTPException(status_code=404, detail="Workflow run not found")
        
        WorkflowStateMachine.validate_transition(run.run_status, "COMPLETED")
        
        run.run_status = "COMPLETED"
        run.completed_at = datetime.now(timezone.utc)
        
        if run.started_at:
            started_dt = run.started_at
            if started_dt.tzinfo is None:
                started_dt = started_dt.replace(tzinfo=timezone.utc)
            duration = run.completed_at - started_dt
            run.duration_ms = int(duration.total_seconds() * 1000)
            
        await db_flush(db)
        
        await self.event_service.publish_run_completed(
            run_id=run_id,
            schedule_id=run.schedule_id,
            workflow_id=run.workflow_id,
            agent_id=primary_assignment.agent_id if primary_assignment else None,
            duration_ms=run.duration_ms,
            risk_level=run.risk_level,
            outputs_summary={"findings_count": len(parsed_output.findings), "recommendations_count": len(parsed_output.recommendations)} if parsed_output else {},
            db=db
        )
        
        # Phase 4 Additive Governance Event Publish
        try:
            from app.modules.events.service import EventPublisherService
            from app.modules.events.schemas import GovernanceEventCreate
            publisher = EventPublisherService()
            resolved_agent_id = str(primary_assignment.agent_id) if primary_assignment and hasattr(primary_assignment, "agent_id") else None
            event_create = GovernanceEventCreate(
                event_type="WORKFLOW_RUN_COMPLETED",
                event_category="Workflow",
                event_version="1.0",
                occurred_at=datetime.now(timezone.utc),
                source_service="workflow_execution",
                actor_json={"user_id": str(run.triggered_by_user_id or run.tenant_id)},
                subject_json={"entity_type": "workflow_runs", "entity_id": str(run.id)},
                correlation_id=run.id,
                payload_json={
                    "schedule_id": str(run.schedule_id),
                    "workflow_id": str(run.workflow_id),
                    "agent_id": resolved_agent_id,
                    "duration_ms": run.duration_ms,
                    "run_code": run.run_code
                },
                classification="INTERNAL",
                retention_class="STANDARD_90_DAYS"
            )
            publisher.publish_event(db, event_create, tenant_id=run.tenant_id)
        except Exception as ex:
            print(f"Warning: Phase 4 WORKFLOW_RUN_COMPLETED publish skipped: {ex}")

        return run

    async def fail_run(self, run_id: UUID, failure_type: str, failure_code: str, failure_message: str, failed_step_id: UUID | None, db) -> WorkflowRun:
        run = await db_get(db, WorkflowRun, run_id)
        if not run:
            raise HTTPException(status_code=404, detail="Workflow run not found")
        
        # Determine previous failure attempts count
        stmt_count = select(sa.func.count(WorkflowRunFailure.id)).where(WorkflowRunFailure.run_id == run_id)
        res_count = await execute_statement(db, stmt_count)
        retry_count = res_count.scalar() or 0
        
        # Load max retries
        schedule = await db_get(db, Phase2WorkflowSchedule, run.schedule_id)
        max_retries = 1
        if schedule and schedule.retry_policy_json:
            max_retries = schedule.retry_policy_json.get("max_retries", 1)

        # Transition run to FAILED
        WorkflowStateMachine.validate_transition(run.run_status, "FAILED")
        run.run_status = "FAILED"
        run.completed_at = datetime.now(timezone.utc)
        if run.started_at:
            started_dt = run.started_at
            if started_dt.tzinfo is None:
                started_dt = started_dt.replace(tzinfo=timezone.utc)
            duration = run.completed_at - started_dt
            run.duration_ms = int(duration.total_seconds() * 1000)
        
        await db_flush(db)

        # Create failure entry
        escalation_required = failure_type in ["SLA_BREACH", "BOUNDARY_VIOLATION"] or retry_count + 1 >= max_retries
        failure_rec = WorkflowRunFailure(
            id=uuid4(),
            tenant_id=run.tenant_id,
            run_id=run_id,
            failure_type=failure_type,
            failure_code=failure_code,
            failure_message=failure_message,
            failed_step_id=failed_step_id,
            retry_count=retry_count + 1,
            max_retries=max_retries,
            escalation_required=escalation_required,
            created_by=run.created_by,
            updated_by=run.updated_by
        )
        db.add(failure_rec)
        await db_flush(db)

        # Publish failed event
        await self.event_service.publish_run_failed(run_id, run.schedule_id, failure_message, db)

        if escalation_required or failure_type == "SLA_BREACH":
            await self.notification_service.notify_run_failed(run, failure_rec, db)

        # Check if retry eligible (exclude structural and timeout/SLA failures)
        if failure_type not in ["SLA_BREACH", "VALIDATION_FAILURE", "BOUNDARY_VIOLATION"] and retry_count + 1 < max_retries:
            WorkflowStateMachine.validate_transition("FAILED", "RETRY_QUEUED")
            run.run_status = "RETRY_QUEUED"
            
            if schedule and schedule.retry_policy_json:
                delay_sec = schedule.retry_policy_json.get("delay_seconds", 60)
                run.next_retry_at = datetime.now(timezone.utc) + timedelta(seconds=delay_sec)
                
            await db_flush(db)
            
            # Publish event for retry queueing
            await self.event_service.publish_run_queued(run_id, run.schedule_id, db)

        return run

    async def cancel_run(self, run_id: UUID, current_user, db) -> WorkflowRun:
        run = await db_get(db, WorkflowRun, run_id)
        if not run:
            raise HTTPException(status_code=404, detail="Workflow run not found")
        
        actor_uuid = resolve_user_uuid(db, current_user.id)
        
        # Check CANCEL_WORKFLOW_RUN permission
        auth_service = AuthorizationDecisionService()
        auth_req = AuthorizationRequest(
            subject_user_id=actor_uuid,
            subject_type="USER",
            object_type="workflow_runs",
            object_id=run_id,
            action="CANCEL_WORKFLOW_RUN"
        )
        auth_res = await auth_service.evaluate(auth_req, db, persist=False)
        if not auth_res.allowed:
            raise HTTPException(
                status_code=403,
                detail=ResponseHelper.error(
                    message="Access denied: missing CANCEL_WORKFLOW_RUN permission",
                    error_code="FORBIDDEN"
                ).model_dump()
            )

        WorkflowStateMachine.validate_transition(run.run_status, "CANCELLED")
        
        run.run_status = "CANCELLED"
        run.completed_at = datetime.now(timezone.utc)
        if run.started_at:
            started_dt = run.started_at
            if started_dt.tzinfo is None:
                started_dt = started_dt.replace(tzinfo=timezone.utc)
            duration = run.completed_at - started_dt
            run.duration_ms = int(duration.total_seconds() * 1000)
            
        run.updated_by = actor_uuid
        await db_flush(db)

        # Publish cancellation event
        await self.event_service.publish_run_cancelled(run_id, run.schedule_id, actor_uuid, "USER", "Manual user cancellation", db)
        return run

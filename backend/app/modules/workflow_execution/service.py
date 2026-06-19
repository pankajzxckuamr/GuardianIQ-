from uuid import UUID, uuid4
from datetime import datetime, timezone, timedelta, date
import inspect
from fastapi import HTTPException
import sqlalchemy as sa
from sqlalchemy.future import select

from app.modules.workflow_execution.models import WorkflowRun, WorkflowRunStep, WorkflowRunOutput, WorkflowRunFailure
from app.modules.workflow_scheduler.models import Phase2WorkflowSchedule, WorkflowScheduleAgentAssignment
from app.modules.registry.repositories import resolve_user_uuid
from app.modules.authorization.decision_service import AuthorizationDecisionService
from app.modules.authorization.schemas import AuthorizationRequest
from app.modules.audit.event_service import GovernanceEventService
from app.modules.audit.event_codes import WorkflowEventCode
from app.shared.response_utils import ResponseHelper
from app.shared.db_compat import db_get, db_flush, execute_statement, commit_session

class WorkflowRunStateError(Exception):
    def __init__(self, from_status: str, to_status: str, message: str = None):
        self.from_status = from_status
        self.to_status = to_status
        self.message = message or f"Invalid transition from {from_status} to {to_status}"
        super().__init__(self.message)


def validate_run_transition(from_status: str, to_status: str):
    from_status_str = from_status.value if hasattr(from_status, "value") else str(from_status)
    to_status_str = to_status.value if hasattr(to_status, "value") else str(to_status)

    valid_transitions = {
        "QUEUED": ["RUNNING", "SKIPPED"],
        "RUNNING": ["COMPLETED", "FAILED", "CANCELLED"],
        "RETRY_QUEUED": ["RUNNING"],
        "FAILED": ["RETRY_QUEUED"]
    }
    
    allowed = valid_transitions.get(from_status_str, [])
    if to_status_str not in allowed:
        raise WorkflowRunStateError(from_status_str, to_status_str)


class WorkflowRunService:
    def __init__(self):
        self.event_service = GovernanceEventService()

    @staticmethod
    async def create_run(db, schedule_id: UUID, trigger_type: str, current_user) -> WorkflowRun:
        # Compatibility wrapper mapping the prompt signature:
        # create_run(schedule_id, trigger_type, triggered_by_user_id, db)
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
        await db_flush(db)
        
        await self.event_service.publish_event(
            event_code=WorkflowEventCode.WORKFLOW_RUN_QUEUED,
            entity_type="workflow_runs",
            entity_id=run.id,
            actor_type="USER" if triggered_by_user_id else "SYSTEM",
            actor_id=actor_uuid,
            action_type="QUEUE_RUN",
            event_summary=f"Workflow run {run_code} queued. Status: {status}.",
            event_payload={"schedule_id": str(sched.id), "workflow_id": str(sched.workflow_id), "status": status},
            db=db
        )
        
        return run

    async def start_run(self, run_id: UUID, db) -> WorkflowRun:
        run = await db_get(db, WorkflowRun, run_id)
        if not run:
            raise HTTPException(status_code=404, detail="Workflow run not found")
        
        validate_run_transition(run.run_status, "RUNNING")
        
        run.run_status = "RUNNING"
        run.started_at = datetime.now(timezone.utc)
        await db_flush(db)
        
        await self.event_service.publish_event(
            event_code=WorkflowEventCode.WORKFLOW_RUN_STARTED,
            entity_type="workflow_runs",
            entity_id=run_id,
            actor_type="SYSTEM",
            actor_id=None,
            action_type="START_RUN",
            event_summary=f"Workflow run {run.run_code} execution started",
            event_payload={},
            db=db
        )
        return run

    async def execute_run(self, run_id: UUID, db) -> None:
        run = await db_get(db, WorkflowRun, run_id)
        if not run:
            return
        
        schedule = await db_get(db, Phase2WorkflowSchedule, run.schedule_id)
        if not schedule:
            return

        # Pre-create all expected step records in PENDING state
        step_codes = [
            ("SCHEDULE_VALIDATION", "VALIDATION", 1),
            ("BOUNDARY_CHECK", "POLICY_CHECK", 2),
            ("AGENT_INVOCATION", "INVOCATION", 3),
            ("OUTPUT_PARSING", "PARSING", 4),
            ("AUDIT_PUBLISHING", "AUDIT", 5),
            ("NOTIFICATION", "ALERT", 6)
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

        # Start execution
        if run.run_status == "QUEUED" or run.run_status == "RETRY_QUEUED":
            run = await self.start_run(run_id, db)

        # 1. SCHEDULE_VALIDATION
        step = steps_map["SCHEDULE_VALIDATION"]
        step.step_status = "RUNNING"
        step.started_at = datetime.now(timezone.utc)
        await db_flush(db)

        try:
            sched_status = schedule.schedule_status.value if hasattr(schedule.schedule_status, "value") else str(schedule.schedule_status)
            if sched_status != "ACTIVE":
                raise ValueError(f"Schedule {schedule.schedule_code} is not ACTIVE (current: {sched_status})")
            
            from app.modules.registry.models import RegistryWorkflow
            wf = await db_get(db, RegistryWorkflow, schedule.workflow_id)
            if not wf or wf.status != "ACTIVE":
                raise ValueError(f"Workflow {schedule.workflow_id} is not ACTIVE")
            
            if not schedule.agent_assignments:
                raise ValueError(f"No agent assignments configured for schedule {schedule.schedule_code}")

            step.step_status = "COMPLETED"
            step.completed_at = datetime.now(timezone.utc)
            await db_flush(db)
        except Exception as e:
            step.step_status = "FAILED"
            step.completed_at = datetime.now(timezone.utc)
            step.error_message = str(e)
            await db_flush(db)
            await self.fail_run(run_id, "VALIDATION_FAILURE", "SCHEDULE_INACTIVE", str(e), step.id, db)
            return

        # SLA Check
        started_dt = run.started_at
        if started_dt:
            if started_dt.tzinfo is None:
                started_dt = started_dt.replace(tzinfo=timezone.utc)
            max_dur = schedule.max_runtime_seconds or 1800
            if datetime.now(timezone.utc) > started_dt + timedelta(seconds=max_dur):
                await self.fail_run(run_id, "SLA_BREACH", "RUN_TIMEOUT", "Execution exceeded max runtime SLA", step.id, db)
                return

        # Get primary assignment
        primary_assignment = None
        for ass in schedule.agent_assignments:
            role_str = ass.assignment_role.value if hasattr(ass.assignment_role, "value") else str(ass.assignment_role)
            if role_str == "PRIMARY":
                primary_assignment = ass
                break
        if not primary_assignment and schedule.agent_assignments:
            primary_assignment = schedule.agent_assignments[0]

        # 2. BOUNDARY_CHECK
        step = steps_map["BOUNDARY_CHECK"]
        step.step_status = "RUNNING"
        step.started_at = datetime.now(timezone.utc)
        await db_flush(db)

        try:
            from app.modules.agent_runtime.boundary_checker import BoundaryChecker
            checker = BoundaryChecker()
            passed, reason = await checker.check(primary_assignment, requested_tool=None, db=db)
            if not passed:
                raise ValueError(reason)

            step.step_status = "COMPLETED"
            step.completed_at = datetime.now(timezone.utc)
            await db_flush(db)
        except Exception as e:
            step.step_status = "FAILED"
            step.completed_at = datetime.now(timezone.utc)
            step.error_message = str(e)
            await db_flush(db)
            await self.fail_run(run_id, "BOUNDARY_VIOLATION", "AGENT_BLOCKED", str(e), step.id, db)
            return

        # 3. AGENT_INVOCATION
        # This step's status updates are handled internally in invoke_agent
        raw_output = None
        try:
            from app.modules.agent_runtime.service import AgentRuntimeService
            runtime = AgentRuntimeService()
            context = run.context_json or {}
            raw_output = await runtime.invoke_agent(run_id, primary_assignment, context, db)
        except Exception as e:
            step = steps_map["AGENT_INVOCATION"]
            step.step_status = "FAILED"
            step.completed_at = datetime.now(timezone.utc)
            step.error_message = str(e)
            await db_flush(db)
            await self.fail_run(run_id, "EXECUTION_FAILURE", "AGENT_ERROR", str(e), step.id, db)
            return

        # 4. OUTPUT_PARSING
        step = steps_map["OUTPUT_PARSING"]
        step.step_status = "RUNNING"
        step.started_at = datetime.now(timezone.utc)
        await db_flush(db)

        try:
            from app.modules.agent_runtime.service import AgentRuntimeService
            runtime = AgentRuntimeService()
            await runtime.parse_output(raw_output, run_id, db)
            
            step.step_status = "COMPLETED"
            step.completed_at = datetime.now(timezone.utc)
            await db_flush(db)
        except Exception as e:
            step.step_status = "FAILED"
            step.completed_at = datetime.now(timezone.utc)
            step.error_message = str(e)
            await db_flush(db)
            await self.fail_run(run_id, "PARSING_FAILURE", "OUTPUT_INVALID", str(e), step.id, db)
            return

        # 5. AUDIT_PUBLISHING
        step = steps_map["AUDIT_PUBLISHING"]
        step.step_status = "RUNNING"
        step.started_at = datetime.now(timezone.utc)
        await db_flush(db)

        try:
            await self.complete_run(run_id, db)
            step.step_status = "COMPLETED"
            step.completed_at = datetime.now(timezone.utc)
            await db_flush(db)
        except Exception as e:
            step.step_status = "FAILED"
            step.completed_at = datetime.now(timezone.utc)
            step.error_message = str(e)
            await db_flush(db)
            await self.fail_run(run_id, "AUDIT_FAILURE", "DB_WRITE_ERROR", str(e), step.id, db)
            return

        # 6. NOTIFICATION
        step = steps_map["NOTIFICATION"]
        step.step_status = "RUNNING"
        step.started_at = datetime.now(timezone.utc)
        await db_flush(db)

        try:
            step.step_status = "COMPLETED"
            step.completed_at = datetime.now(timezone.utc)
            await db_flush(db)
        except Exception:
            step.step_status = "FAILED"
            step.completed_at = datetime.now(timezone.utc)
            await db_flush(db)

    async def complete_run(self, run_id: UUID, db) -> WorkflowRun:
        run = await db_get(db, WorkflowRun, run_id)
        if not run:
            raise HTTPException(status_code=404, detail="Workflow run not found")
        
        validate_run_transition(run.run_status, "COMPLETED")
        
        run.run_status = "COMPLETED"
        run.completed_at = datetime.now(timezone.utc)
        
        if run.started_at:
            started_dt = run.started_at
            if started_dt.tzinfo is None:
                started_dt = started_dt.replace(tzinfo=timezone.utc)
            duration = run.completed_at - started_dt
            run.duration_ms = int(duration.total_seconds() * 1000)
            
        await db_flush(db)
        
        await self.event_service.publish_event(
            event_code=WorkflowEventCode.WORKFLOW_RUN_COMPLETED,
            entity_type="workflow_runs",
            entity_id=run_id,
            actor_type="SYSTEM",
            actor_id=None,
            action_type="COMPLETE_RUN",
            event_summary=f"Workflow run {run.run_code} completed successfully",
            event_payload={"duration_ms": run.duration_ms},
            db=db
        )
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
        validate_run_transition(run.run_status, "FAILED")
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
            escalation_required=False,
            created_by=run.created_by,
            updated_by=run.updated_by
        )
        db.add(failure_rec)
        await db_flush(db)

        # Publish failed event
        await self.event_service.publish_event(
            event_code=WorkflowEventCode.WORKFLOW_RUN_FAILED,
            entity_type="workflow_runs",
            entity_id=run_id,
            actor_type="SYSTEM",
            actor_id=None,
            action_type="FAIL_RUN",
            event_summary=f"Workflow run {run.run_code} failed: {failure_message}",
            event_payload={"failure_type": failure_type, "failure_code": failure_code},
            db=db
        )

        # Check if retry eligible (exclude structural and timeout/SLA failures)
        if failure_type not in ["SLA_BREACH", "VALIDATION_FAILURE", "BOUNDARY_VIOLATION"] and retry_count + 1 < max_retries:
            validate_run_transition("FAILED", "RETRY_QUEUED")
            run.run_status = "RETRY_QUEUED"
            await db_flush(db)
            
            # Publish event for retry queueing
            await self.event_service.publish_event(
                event_code=WorkflowEventCode.WORKFLOW_RUN_QUEUED,
                entity_type="workflow_runs",
                entity_id=run_id,
                actor_type="SYSTEM",
                actor_id=None,
                action_type="RETRY_QUEUE",
                event_summary=f"Workflow run {run.run_code} queued for retry ({retry_count + 1}/{max_retries})",
                event_payload={"retry_count": retry_count + 1},
                db=db
            )

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

        validate_run_transition(run.run_status, "CANCELLED")
        
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
        await self.event_service.publish_event(
            event_code="WORKFLOW_RUN_CANCELLED",
            entity_type="workflow_runs",
            entity_id=run_id,
            actor_type="USER",
            actor_id=actor_uuid,
            action_type="CANCEL",
            event_summary=f"Workflow run {run.run_code} cancelled manually by user",
            event_payload={},
            db=db
        )
        return run

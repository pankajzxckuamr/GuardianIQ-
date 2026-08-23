import inspect
import sqlalchemy as sa
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from uuid import UUID
from app.modules.audit.models import AuditEvent
from app.modules.registry.models import GuardianUser
from app.modules.auth.models import User
from app.modules.audit.event_codes import WorkflowEventCode

class GovernanceEventPublishError(Exception):
    pass

async def execute_statement(db, stmt):
    res = db.execute(stmt)
    if inspect.isawaitable(res):
        return await res
    return res

async def commit_session(db):
    if hasattr(db, "commit") and inspect.iscoroutinefunction(db.commit):
        await db.commit()
    else:
        db.commit()

class GovernanceEventService:
    async def publish_event(
        self,
        event_code: WorkflowEventCode | str,
        entity_type: str,
        entity_id: UUID | str | None,
        actor_type: str,
        actor_id: UUID | str | None,
        action_type: str,
        event_summary: str,
        event_payload: dict,
        db
    ) -> None:
        int_actor_id = None
        if actor_id:
            guardian_stmt = select(GuardianUser.email).where(GuardianUser.id == str(actor_id))
            guardian_res = await execute_statement(db, guardian_stmt)
            email = guardian_res.scalar()
            
            if email:
                user_stmt = select(User.id).where(User.email == email)
                user_res = await execute_statement(db, user_stmt)
                int_actor_id = user_res.scalar()

        meta = {
            "entity_id": str(entity_id) if entity_id else None,
            "actor_type": actor_type,
            "actor_id": str(actor_id) if actor_id else None,
            "event_summary": event_summary,
            "payload": event_payload or {}
        }

        event_type_str = event_code.value if hasattr(event_code, "value") else str(event_code)
        audit_event = AuditEvent(
            event_type=event_type_str,
            entity_type=entity_type,
            entity_id=None,
            actor_user_id=int_actor_id,
            action=action_type,
            event_metadata=meta
        )
        try:
            db.add(audit_event)
            await commit_session(db)
        except SQLAlchemyError as e:
            raise GovernanceEventPublishError(f"Failed to publish event: {str(e)}") from e

    async def publish_batch(self, events: list[dict], db) -> None:
        records = []
        for evt in events:
            event_code = evt.get("event_code")
            entity_type = evt.get("entity_type")
            entity_id = evt.get("entity_id")
            actor_type = evt.get("actor_type")
            actor_id = evt.get("actor_id")
            action_type = evt.get("action_type")
            event_summary = evt.get("event_summary")
            event_payload = evt.get("event_payload", {})

            int_actor_id = None
            if actor_id:
                guardian_stmt = select(GuardianUser.email).where(GuardianUser.id == str(actor_id))
                guardian_res = await execute_statement(db, guardian_stmt)
                email = guardian_res.scalar()
                
                if email:
                    user_stmt = select(User.id).where(User.email == email)
                    user_res = await execute_statement(db, user_stmt)
                    int_actor_id = user_res.scalar()

            meta = {
                "entity_id": str(entity_id) if entity_id else None,
                "actor_type": actor_type,
                "actor_id": str(actor_id) if actor_id else None,
                "event_summary": event_summary,
                "payload": event_payload
            }

            event_type_str = event_code.value if hasattr(event_code, "value") else str(event_code)
            records.append(AuditEvent(
                event_type=event_type_str,
                entity_type=entity_type,
                entity_id=None,
                actor_user_id=int_actor_id,
                action=action_type,
                event_metadata=meta
            ))
        
        try:
            db.add_all(records)
            await commit_session(db)
        except SQLAlchemyError as e:
            raise GovernanceEventPublishError(f"Failed to publish batch: {str(e)}") from e

    async def get_timeline(self, entity_type: str, entity_id: UUID, db) -> list:
        stmt = (
            select(AuditEvent)
            .where(
                AuditEvent.entity_type == entity_type,
                sa.or_(
                    sa.func.cast(AuditEvent.entity_id, sa.String) == str(entity_id),
                    sa.func.json_extract_path_text(AuditEvent.event_metadata, 'entity_id') == str(entity_id)
                )
            )
            .order_by(AuditEvent.created_at.asc())
        )
        res = await execute_statement(db, stmt)
        return list(res.scalars().all())

    # Convenience Methods
    async def publish_schedule_created(self, schedule_id: UUID, actor_id: UUID, db) -> None:
        await self.publish_event(WorkflowEventCode.WORKFLOW_SCHEDULE_CREATED, "workflow_schedules", schedule_id, "USER", actor_id, "CREATE", "Schedule created", {}, db)

    async def publish_schedule_updated(self, schedule_id: UUID, actor_id: UUID, before_json: dict, after_json: dict, db) -> None:
        await self.publish_event(WorkflowEventCode.WORKFLOW_SCHEDULE_UPDATED, "workflow_schedules", schedule_id, "USER", actor_id, "UPDATE", "Schedule updated", {"before": before_json, "after": after_json}, db)

    async def publish_schedule_submitted(self, schedule_id: UUID, actor_id: UUID, approval_cycle_id: UUID, correlation_id: str, db) -> None:
        payload = {
            "schedule_id": str(schedule_id),
            "approval_cycle_id": str(approval_cycle_id),
            "correlation_id": correlation_id
        }
        await self.publish_event(WorkflowEventCode.WORKFLOW_SCHEDULE_SUBMITTED, "workflow_schedules", schedule_id, "USER", actor_id, "SUBMIT", "Schedule submitted for approval", payload, db)

    async def publish_schedule_activated(self, schedule_id: UUID, actor_id: UUID, approval_cycle_id: UUID, correlation_id: str, db) -> None:
        payload = {
            "schedule_id": str(schedule_id),
            "approval_cycle_id": str(approval_cycle_id),
            "correlation_id": correlation_id
        }
        await self.publish_event(WorkflowEventCode.WORKFLOW_SCHEDULE_ACTIVATED, "workflow_schedules", schedule_id, "USER", actor_id, "ACTIVATE", "Schedule activated", payload, db)

    async def publish_layer_skipped(self, schedule_id: UUID, actor_id: UUID, approval_cycle_id: UUID, correlation_id: str, approval_layer: int, department_code: str, parent_approval_id: UUID, approval_id: UUID, skip_reason: str, db) -> None:
        payload = {
            "schedule_id": str(schedule_id),
            "approval_cycle_id": str(approval_cycle_id),
            "correlation_id": correlation_id,
            "approval_layer": approval_layer,
            "department_code": department_code,
            "parent_approval_id": str(parent_approval_id) if parent_approval_id else None,
            "approval_id": str(approval_id),
            "skip_reason": skip_reason
        }
        await self.publish_event(WorkflowEventCode.WORKFLOW_SCHEDULE_LAYER_SKIPPED, "workflow_schedules", schedule_id, "SYSTEM", actor_id, "SKIP_LAYER", "Approval layer auto-skipped", payload, db)

    async def publish_schedule_paused(self, schedule_id: UUID, actor_id: UUID, db) -> None:
        await self.publish_event(WorkflowEventCode.WORKFLOW_SCHEDULE_PAUSED, "workflow_schedules", schedule_id, "USER", actor_id, "PAUSE", "Schedule paused", {}, db)

    async def publish_schedule_retired(self, schedule_id: UUID, actor_id: UUID, db) -> None:
        await self.publish_event(WorkflowEventCode.WORKFLOW_SCHEDULE_RETIRED, "workflow_schedules", schedule_id, "USER", actor_id, "RETIRE", "Schedule retired", {}, db)

    async def publish_run_queued(self, run_id: UUID, schedule_id: UUID, db) -> None:
        await self.publish_event(WorkflowEventCode.WORKFLOW_RUN_QUEUED, "workflow_runs", run_id, "SYSTEM", None, "QUEUE", "Run queued", {"schedule_id": str(schedule_id)}, db)

    async def publish_run_started(self, run_id: UUID, schedule_id: UUID, db) -> None:
        await self.publish_event(WorkflowEventCode.WORKFLOW_RUN_STARTED, "workflow_runs", run_id, "SYSTEM", None, "START", "Run started", {"schedule_id": str(schedule_id)}, db)

    async def publish_run_completed(self, run_id: UUID, schedule_id: UUID, workflow_id: UUID, agent_id: UUID, duration_ms: int, risk_level: str, outputs_summary: dict, db) -> None:
        payload = {
            "schedule_id": str(schedule_id),
            "workflow_id": str(workflow_id) if workflow_id else None,
            "agent_id": str(agent_id) if agent_id else None,
            "duration_ms": duration_ms,
            "risk_level": risk_level,
            "outputs": outputs_summary
        }
        await self.publish_event(WorkflowEventCode.WORKFLOW_RUN_COMPLETED, "workflow_runs", run_id, "SYSTEM", None, "COMPLETE", "Run completed", payload, db)

    async def publish_run_failed(self, run_id: UUID, schedule_id: UUID, failure: str, db) -> None:
        await self.publish_event(WorkflowEventCode.WORKFLOW_RUN_FAILED, "workflow_runs", run_id, "SYSTEM", None, "FAIL", "Run failed", {"schedule_id": str(schedule_id), "failure": failure}, db)

    async def publish_run_escalated(self, run_id: UUID, schedule_id: UUID, reason: str, db) -> None:
        await self.publish_event(WorkflowEventCode.WORKFLOW_RUN_ESCALATED, "workflow_runs", run_id, "SYSTEM", None, "ESCALATE", "Run escalated", {"schedule_id": str(schedule_id), "reason": reason}, db)

    async def publish_run_cancelled(self, run_id: UUID, schedule_id: UUID, actor_id: UUID, actor_type: str, reason: str, db) -> None:
        await self.publish_event(WorkflowEventCode.WORKFLOW_RUN_CANCELLED, "workflow_runs", run_id, actor_type, actor_id, "CANCEL", "Run cancelled", {"schedule_id": str(schedule_id), "reason": reason}, db)

    async def publish_agent_boundary_passed(self, run_id: UUID, agent_id: UUID, db) -> None:
        await self.publish_event(WorkflowEventCode.AGENT_BOUNDARY_CHECK_PASSED, "workflow_runs", run_id, "SYSTEM", None, "BOUNDARY_PASS", "Agent boundary check passed", {"agent_id": str(agent_id)}, db)

    async def publish_agent_boundary_failed(self, run_id: UUID, agent_id: UUID, reason: str, db) -> None:
        await self.publish_event(WorkflowEventCode.AGENT_BOUNDARY_CHECK_FAILED, "workflow_runs", run_id, "SYSTEM", None, "BOUNDARY_FAIL", "Agent boundary check failed", {"agent_id": str(agent_id), "reason": reason}, db)

    async def publish_agent_execution_started(self, run_id: UUID, agent_id: UUID, db) -> None:
        await self.publish_event(WorkflowEventCode.AGENT_EXECUTION_STARTED, "workflow_runs", run_id, "SYSTEM", None, "AGENT_START", "Agent execution started", {"agent_id": str(agent_id)}, db)

    async def publish_agent_execution_completed(self, run_id: UUID, agent_id: UUID, output_summary: dict, db) -> None:
        await self.publish_event(WorkflowEventCode.AGENT_EXECUTION_COMPLETED, "workflow_runs", run_id, "SYSTEM", None, "AGENT_COMPLETE", "Agent execution completed", {"agent_id": str(agent_id), "output": output_summary}, db)

    async def publish_output_generated(self, run_id: UUID, output_id: UUID, db) -> None:
        await self.publish_event(WorkflowEventCode.WORKFLOW_OUTPUT_GENERATED, "workflow_runs", run_id, "SYSTEM", None, "OUTPUT_GENERATE", "Output generated", {"output_id": str(output_id)}, db)

    @staticmethod
    async def publish_authorization_denied(actor_id: UUID, actor_type: str, action: str, entity_type: str, entity_id: UUID, rbac_result: dict, abac_result: dict, denial_reason: list, db) -> None:
        payload = {
            "action": action,
            "rbac_result": rbac_result,
            "abac_result": abac_result,
            "denial_reason": denial_reason
        }
        service = GovernanceEventService()
        await service.publish_event(WorkflowEventCode.AUTHORIZATION_DENIED, entity_type, entity_id, actor_type, actor_id, "DENY", "Authorization denied", payload, db)

from uuid import UUID, uuid4
from datetime import datetime, timezone
import inspect
import pytz
from croniter import croniter
from fastapi import HTTPException
import sqlalchemy as sa
from sqlalchemy.future import select

from app.modules.workflow_scheduler.repository import WorkflowScheduleRepository
from app.modules.workflow_scheduler.validators import WorkflowScheduleValidationService
from app.modules.workflow_scheduler.models import (
    Phase2WorkflowSchedule,
    WorkflowScheduleAgentAssignment,
    WorkflowScheduleApproval,
    WorkflowScheduleHistory,
    ApprovalGroupMember
)
from app.modules.workflow_notifications.models import WorkflowNotification
from app.modules.registry.repositories import resolve_user_uuid
from app.modules.authorization.decision_service import AuthorizationDecisionService
from app.modules.authorization.schemas import AuthorizationRequest
from app.modules.audit.event_service import GovernanceEventService
from app.modules.audit.event_codes import WorkflowEventCode
from app.shared.response_utils import ResponseHelper
from app.shared.enums import RiskLevel, ExecutionMode, ScheduleStatus, ScheduleType

class WorkflowScheduleStateError(Exception):
    def __init__(self, from_status: str, to_status: str, message: str = None):
        self.from_status = from_status
        self.to_status = to_status
        self.message = message or f"Invalid transition from {from_status} to {to_status}"
        super().__init__(self.message)


def validate_transition(from_status: str, to_status: str, approval_required: bool = False):
    from_status_str = from_status.value if hasattr(from_status, "value") else str(from_status)
    to_status_str = to_status.value if hasattr(to_status, "value") else str(to_status)

    valid_transitions = {
        "DRAFT": ["PENDING_APPROVAL", "ACTIVE"] if not approval_required else ["PENDING_APPROVAL"],
        "PENDING_APPROVAL": ["ACTIVE", "DRAFT"],
        "ACTIVE": ["PAUSED", "RETIRED"],
        "PAUSED": ["ACTIVE", "RETIRED"],
        "RETIRED": []
    }
    
    allowed = valid_transitions.get(from_status_str, [])
    if to_status_str not in allowed:
        raise WorkflowScheduleStateError(from_status_str, to_status_str)


def calculate_next_run_at(schedule_type: str, cron_expression: str, timezone_str: str, start_at: datetime = None) -> datetime | None:
    sched_type_str = schedule_type.value if hasattr(schedule_type, "value") else str(schedule_type)
    if sched_type_str == "MANUAL":
        return None
    
    tz = pytz.timezone(timezone_str or "Asia/Kolkata")
    now = datetime.now(tz)
    
    base_time = now
    if start_at:
        if start_at.tzinfo is None:
            start_at = tz.localize(start_at)
        else:
            start_at = start_at.astimezone(tz)
        
        if start_at > now:
            base_time = start_at
            
    if sched_type_str == "CRON":
        if not cron_expression:
            return None
        iter = croniter(cron_expression, base_time)
        return iter.get_next(datetime)
    
    type_cron_map = {
        "DAILY": "0 0 * * *",
        "WEEKLY": "0 0 * * 0",
        "MONTHLY": "0 0 1 * *",
    }
    cron_expr = cron_expression
    if sched_type_str in type_cron_map:
        cron_expr = type_cron_map[sched_type_str]
        
    if cron_expr:
        iter = croniter(cron_expr, base_time)
        return iter.get_next(datetime)
    
    if sched_type_str == "ONE_TIME":
        return start_at if start_at and start_at > now else None
        
    if sched_type_str == "INTERVAL":
        from datetime import timedelta
        return base_time + timedelta(hours=1)
        
    return None


def serialize_schedule_history(schedule: Phase2WorkflowSchedule) -> dict:
    return {
        "id": str(schedule.id),
        "workflow_id": str(schedule.workflow_id),
        "schedule_code": schedule.schedule_code,
        "schedule_name": schedule.schedule_name,
        "schedule_type": schedule.schedule_type.value if hasattr(schedule.schedule_type, "value") else str(schedule.schedule_type),
        "cron_expression": schedule.cron_expression,
        "timezone": schedule.timezone,
        "start_at": schedule.start_at.isoformat() if schedule.start_at else None,
        "end_at": schedule.end_at.isoformat() if schedule.end_at else None,
        "next_run_at": schedule.next_run_at.isoformat() if schedule.next_run_at else None,
        "last_run_at": schedule.last_run_at.isoformat() if schedule.last_run_at else None,
        "concurrency_policy": schedule.concurrency_policy.value if hasattr(schedule.concurrency_policy, "value") else str(schedule.concurrency_policy),
        "max_runtime_seconds": schedule.max_runtime_seconds,
        "retry_policy_json": schedule.retry_policy_json,
        "owner_user_id": str(schedule.owner_user_id) if schedule.owner_user_id else None,
        "owner_department_id": str(schedule.owner_department_id) if schedule.owner_department_id else None,
        "approval_required": schedule.approval_required,
        "approval_group_id": str(schedule.approval_group_id) if schedule.approval_group_id else None,
        "risk_level": schedule.risk_level.value if hasattr(schedule.risk_level, "value") else str(schedule.risk_level),
        "schedule_status": schedule.schedule_status.value if hasattr(schedule.schedule_status, "value") else str(schedule.schedule_status)
    }


def to_dict(obj):
    return {c.name: getattr(obj, c.name) for c in obj.__table__.columns}


from app.shared.db_compat import db_get, execute_statement, db_flush


def format_schedule_list_item(item: Phase2WorkflowSchedule) -> dict:
    workflow_name = item.workflow.workflow_name if item.workflow else "Unknown"
    owner_name = item.owner_user.full_name if item.owner_user else "Unknown"
    
    is_overdue = False
    if item.schedule_status == "ACTIVE" and item.next_run_at:
        next_run = item.next_run_at
        if next_run.tzinfo is None:
            next_run = pytz.UTC.localize(next_run)
        is_overdue = next_run <= datetime.now(timezone.utc)
        
    health_status = "HEALTHY"
    if item.runs:
        sorted_runs = sorted(item.runs, key=lambda r: r.created_at or datetime.min, reverse=True)
        if sorted_runs and sorted_runs[0].run_status == "FAILED":
            health_status = "UNHEALTHY"
            
    return {
        "id": item.id,
        "schedule_code": item.schedule_code,
        "schedule_name": item.schedule_name,
        "workflow_name": workflow_name,
        "schedule_type": item.schedule_type.value if hasattr(item.schedule_type, "value") else str(item.schedule_type),
        "schedule_status": item.schedule_status.value if hasattr(item.schedule_status, "value") else str(item.schedule_status),
        "risk_level": item.risk_level.value if hasattr(item.risk_level, "value") else str(item.risk_level),
        "owner_name": owner_name,
        "next_run_at": item.next_run_at,
        "last_run_at": item.last_run_at,
        "approval_required": item.approval_required,
        "health_status": health_status
    }


def format_schedule_response(item: Phase2WorkflowSchedule) -> dict:
    assignments = []
    for ass in item.agent_assignments:
        assignments.append({
            "id": ass.id,
            "schedule_id": ass.schedule_id,
            "agent_id": ass.agent_id,
            "model_id": ass.model_id,
            "assignment_role": ass.assignment_role.value if hasattr(ass.assignment_role, "value") else str(ass.assignment_role),
            "execution_mode": ass.execution_mode.value if hasattr(ass.execution_mode, "value") else str(ass.execution_mode),
            "confidence_threshold": float(ass.confidence_threshold) if ass.confidence_threshold is not None else None,
            "allowed_tools_json": ass.allowed_tools_json or [],
            "allowed_data_sources_json": ass.allowed_data_sources_json or [],
            "blocked_operations_json": ass.blocked_operations_json or [],
            "boundary_rules_json": ass.boundary_rules_json or {},
            "status": ass.status,
            "version_no": ass.version_no,
            "is_deleted": ass.is_deleted,
            "metadata_json": ass.metadata_json or {},
            "created_at": ass.created_at,
            "updated_at": ass.updated_at,
            "created_by": ass.created_by,
            "updated_by": ass.updated_by
        })
        
    is_overdue = False
    if item.schedule_status == "ACTIVE" and item.next_run_at:
        next_run = item.next_run_at
        if next_run.tzinfo is None:
            next_run = pytz.UTC.localize(next_run)
        is_overdue = next_run <= datetime.now(timezone.utc)
        
    health_status = "HEALTHY"
    if item.runs:
        sorted_runs = sorted(item.runs, key=lambda r: r.created_at or datetime.min, reverse=True)
        if sorted_runs and sorted_runs[0].run_status == "FAILED":
            health_status = "UNHEALTHY"

    workflow_name = item.workflow.workflow_name if hasattr(item, "workflow") and item.workflow else "Unknown"
    owner_name = item.owner_user.full_name if hasattr(item, "owner_user") and item.owner_user else "Unknown"

    return {
        "id": item.id,
        "workflow_id": item.workflow_id,
        "workflow_name": workflow_name,
        "schedule_code": item.schedule_code,
        "schedule_name": item.schedule_name,
        "schedule_type": item.schedule_type.value if hasattr(item.schedule_type, "value") else str(item.schedule_type),
        "cron_expression": item.cron_expression,
        "timezone": item.timezone,
        "start_at": item.start_at,
        "end_at": item.end_at,
        "next_run_at": item.next_run_at,
        "last_run_at": item.last_run_at,
        "concurrency_policy": item.concurrency_policy.value if hasattr(item.concurrency_policy, "value") else str(item.concurrency_policy),
        "max_runtime_seconds": item.max_runtime_seconds,
        "retry_policy_json": item.retry_policy_json or {},
        "owner_user_id": item.owner_user_id,
        "owner_name": owner_name,
        "owner_department_id": item.owner_department_id,
        "approval_required": item.approval_required,
        "approval_group_id": item.approval_group_id,
        "risk_level": item.risk_level.value if hasattr(item.risk_level, "value") else str(item.risk_level),
        "schedule_status": item.schedule_status.value if hasattr(item.schedule_status, "value") else str(item.schedule_status),
        "version_no": item.version_no,
        "is_deleted": item.is_deleted,
        "metadata_json": item.metadata_json or {},
        "created_at": item.created_at,
        "updated_at": item.updated_at,
        "created_by": item.created_by,
        "updated_by": item.updated_by,
        "agent_assignments": assignments,
        "health_status": health_status,
        "is_overdue": is_overdue
    }


class WorkflowScheduleService:
    def __init__(self):
        self.repo = WorkflowScheduleRepository()
        self.event_service = GovernanceEventService()

    async def create_schedule(self, payload, current_user, db) -> Phase2WorkflowSchedule:
        # 1. Validate payload
        errors = await WorkflowScheduleValidationService.validate_create(payload, db)
        if errors:
            details = [{"field": e.field, "message": e.message} for e in errors]
            raise HTTPException(
                status_code=422,
                detail=ResponseHelper.error(
                    message="Validation failed for workflow schedule creation.",
                    error_code="VALIDATION_ERROR",
                    details=details
                ).model_dump()
            )

        actor_uuid = resolve_user_uuid(db, current_user.id)

        # 2. Authorization check
        auth_service = AuthorizationDecisionService()
        auth_req = AuthorizationRequest(
            subject_user_id=actor_uuid,
            subject_type="USER",
            object_type="workflow_schedules",
            action="CREATE_WORKFLOW_SCHEDULE"
        )
        auth_res = await auth_service.evaluate(auth_req, db, persist=False)
        if not auth_res.allowed:
            raise HTTPException(
                status_code=403,
                detail=ResponseHelper.error(
                    message="Access denied: missing CREATE_WORKFLOW_SCHEDULE permission",
                    error_code="FORBIDDEN"
                ).model_dump()
            )

        # 3. Process data structures
        data = payload.model_dump() if hasattr(payload, "model_dump") else payload.copy()
        assignments = data.pop("agent_assignments", [])

        retry_policy = data.pop("retry_policy", None)
        if retry_policy:
            data["retry_policy_json"] = retry_policy.model_dump() if hasattr(retry_policy, "model_dump") else retry_policy

        data["tenant_id"] = actor_uuid
        data["created_by"] = actor_uuid
        data["updated_by"] = actor_uuid

        processed_assignments = []
        for ass in assignments:
            ass_dict = ass.model_dump() if hasattr(ass, "model_dump") else ass.copy()
            ass_dict["allowed_tools_json"] = ass_dict.pop("allowed_tools", [])
            ass_dict["allowed_data_sources_json"] = ass_dict.pop("allowed_data_sources", [])
            ass_dict["blocked_operations_json"] = ass_dict.pop("blocked_operations", [])
            boundary_rules = ass_dict.pop("boundary_rules", None)
            if boundary_rules:
                ass_dict["boundary_rules_json"] = boundary_rules.model_dump() if hasattr(boundary_rules, "model_dump") else boundary_rules
            
            ass_dict["tenant_id"] = actor_uuid
            ass_dict["created_by"] = actor_uuid
            ass_dict["updated_by"] = actor_uuid
            processed_assignments.append(ass_dict)

        # 4. Insert records
        schedule = await self.repo.create(db, data, processed_assignments)

        # 5. Publish event
        await self.event_service.publish_event(
            event_code=WorkflowEventCode.WORKFLOW_SCHEDULE_CREATED,
            entity_type="workflow_schedules",
            entity_id=schedule.id,
            actor_type="USER",
            actor_id=actor_uuid,
            action_type="CREATE",
            event_summary=f"Workflow schedule {schedule.schedule_name} created",
            event_payload={"schedule_code": schedule.schedule_code, "workflow_id": str(schedule.workflow_id)},
            db=db
        )

        return schedule

    async def update_schedule(self, id: UUID, payload, current_user, db) -> Phase2WorkflowSchedule:
        schedule = await self.repo.get_by_id(db, id)
        if not schedule:
            raise HTTPException(
                status_code=404,
                detail=ResponseHelper.error(message="Workflow schedule not found", error_code="NOT_FOUND").model_dump()
            )

        actor_uuid = resolve_user_uuid(db, current_user.id)

        # Only allowed in DRAFT or PAUSED status
        sched_status_str = schedule.schedule_status.value if hasattr(schedule.schedule_status, "value") else str(schedule.schedule_status)
        if sched_status_str not in ["DRAFT", "PAUSED"]:
            raise WorkflowScheduleStateError(sched_status_str, "UPDATE", "Updates are only allowed in DRAFT or PAUSED status")

        # Serialise before JSON for history tracking
        before_json = serialize_schedule_history(schedule)

        # Build merged state for validation check
        update_data = payload.model_dump(exclude_unset=True) if hasattr(payload, "model_dump") else payload.copy()
        
        merged_state = {}
        for col in schedule.__table__.columns:
            merged_state[col.name] = getattr(schedule, col.name)
        
        for k, v in update_data.items():
            merged_state[k] = v

        retry_policy = update_data.pop("retry_policy", None)
        if retry_policy:
            update_data["retry_policy_json"] = retry_policy.model_dump() if hasattr(retry_policy, "model_dump") else retry_policy
            merged_state["retry_policy_json"] = update_data["retry_policy_json"]

        # Validate merge result
        errors = await WorkflowScheduleValidationService.validate_create(merged_state, db)
        if errors:
            details = [{"field": e.field, "message": e.message} for e in errors]
            raise HTTPException(
                status_code=422,
                detail=ResponseHelper.error(
                    message="Validation failed for workflow schedule update.",
                    error_code="VALIDATION_ERROR",
                    details=details
                ).model_dump()
            )

        # Build assignment structures if updating assignments
        assignments = update_data.get("agent_assignments")
        if assignments is not None:
            processed_assignments = []
            for ass in assignments:
                ass_dict = ass.model_dump() if hasattr(ass, "model_dump") else ass.copy()
                ass_dict["allowed_tools_json"] = ass_dict.pop("allowed_tools", [])
                ass_dict["allowed_data_sources_json"] = ass_dict.pop("allowed_data_sources", [])
                ass_dict["blocked_operations_json"] = ass_dict.pop("blocked_operations", [])
                boundary_rules = ass_dict.pop("boundary_rules", None)
                if boundary_rules:
                    ass_dict["boundary_rules_json"] = boundary_rules.model_dump() if hasattr(boundary_rules, "model_dump") else boundary_rules
                
                ass_dict["tenant_id"] = schedule.tenant_id
                ass_dict["created_by"] = actor_uuid
                ass_dict["updated_by"] = actor_uuid
                processed_assignments.append(ass_dict)
            update_data["agent_assignments"] = processed_assignments

        # Update in database
        updated_schedule = await self.repo.update(db, schedule, update_data)
        updated_schedule.updated_by = actor_uuid

        # Write history row
        history_rec = WorkflowScheduleHistory(
            id=uuid4(),
            tenant_id=schedule.tenant_id,
            schedule_id=schedule.id,
            change_type="UPDATE",
            change_summary="Schedule fields updated",
            before_json=before_json,
            after_json=serialize_schedule_history(updated_schedule),
            changed_by=actor_uuid,
            created_by=actor_uuid,
            updated_by=actor_uuid
        )
        db.add(history_rec)
        await db_flush(db)

        # Publish event
        await self.event_service.publish_event(
            event_code=WorkflowEventCode.WORKFLOW_SCHEDULE_UPDATED,
            entity_type="workflow_schedules",
            entity_id=schedule.id,
            actor_type="USER",
            actor_id=actor_uuid,
            action_type="UPDATE",
            event_summary=f"Workflow schedule {schedule.schedule_name} updated",
            event_payload={"schedule_code": schedule.schedule_code},
            db=db
        )

        return updated_schedule

    async def submit_for_approval(self, id: UUID, current_user, db) -> Phase2WorkflowSchedule:
        schedule = await self.repo.get_by_id(db, id)
        if not schedule:
            raise HTTPException(
                status_code=404,
                detail=ResponseHelper.error(message="Workflow schedule not found", error_code="NOT_FOUND").model_dump()
            )

        actor_uuid = resolve_user_uuid(db, current_user.id)

        # Check transition validity
        validate_transition(schedule.schedule_status, "PENDING_APPROVAL", schedule.approval_required)

        # Enforce that schedule has approval required and group set
        if not schedule.approval_required or not schedule.approval_group_id:
            raise HTTPException(
                status_code=400,
                detail=ResponseHelper.error(
                    message="Approval is not required or approval group is not set for this schedule.",
                    error_code="VALIDATION_ERROR"
                ).model_dump()
            )

        # Update status
        await self.repo.update_status(db, schedule, "PENDING_APPROVAL")
        schedule.updated_by = actor_uuid

        # Create approval record
        approval = WorkflowScheduleApproval(
            id=uuid4(),
            tenant_id=schedule.tenant_id,
            schedule_id=schedule.id,
            approval_type="ACTIVATION",
            approval_status="PENDING",
            approval_group_id=schedule.approval_group_id,
            submitted_by=actor_uuid,
            created_by=actor_uuid,
            updated_by=actor_uuid
        )
        db.add(approval)

        # Create notifications for group members
        stmt = select(ApprovalGroupMember.user_id).where(ApprovalGroupMember.approval_group_id == schedule.approval_group_id)
        res = await execute_statement(db, stmt)
        member_ids = [r[0] for r in res.fetchall()]

        for member_id in member_ids:
            notif = WorkflowNotification(
                id=uuid4(),
                tenant_id=schedule.tenant_id,
                recipient_user_id=member_id,
                notification_type="APPROVAL_REQUIRED",
                title="Schedule Approval Required",
                message=f"Approval is required for schedule {schedule.schedule_name} ({schedule.schedule_code}).",
                severity="HIGH",
                entity_type="workflow_schedules",
                entity_id=schedule.id,
                status="UNREAD",
                created_by=actor_uuid,
                updated_by=actor_uuid
            )
            db.add(notif)

        await db_flush(db)

        # Publish event
        await self.event_service.publish_event(
            event_code=WorkflowEventCode.WORKFLOW_SCHEDULE_SUBMITTED,
            entity_type="workflow_schedules",
            entity_id=schedule.id,
            actor_type="USER",
            actor_id=actor_uuid,
            action_type="SUBMIT",
            event_summary=f"Workflow schedule {schedule.schedule_name} submitted for approval",
            event_payload={"approval_id": str(approval.id), "approval_group_id": str(schedule.approval_group_id)},
            db=db
        )

        return schedule

    async def activate_schedule(self, id: UUID, current_user, db, bypass_abac: bool = False) -> Phase2WorkflowSchedule:
        schedule = await self.repo.get_by_id(db, id)
        if not schedule:
            raise HTTPException(
                status_code=404,
                detail=ResponseHelper.error(message="Workflow schedule not found", error_code="NOT_FOUND").model_dump()
            )

        actor_uuid = resolve_user_uuid(db, current_user.id)

        if not bypass_abac:
            # Authorization + ABAC check
            auth_service = AuthorizationDecisionService()
            auth_req = AuthorizationRequest(
                subject_user_id=actor_uuid,
                subject_type="USER",
                object_type="workflow_schedules",
                object_id=id,
                action="ACTIVATE_WORKFLOW_SCHEDULE"
            )
            auth_res = await auth_service.evaluate(auth_req, db, persist=False)
            if not auth_res.allowed:
                raise HTTPException(
                    status_code=403,
                    detail=ResponseHelper.error(
                        message="Access denied: missing ACTIVATE_WORKFLOW_SCHEDULE permission or ABAC validation failed",
                        error_code="FORBIDDEN"
                    ).model_dump()
                )

        # Verify state transition rules
        validate_transition(schedule.schedule_status, "ACTIVE", schedule.approval_required)

        # Recalculate next run time
        next_run = calculate_next_run_at(schedule.schedule_type, schedule.cron_expression, schedule.timezone, schedule.start_at)
        
        # Verify next run complies with end date limit
        if next_run and schedule.end_at:
            end_dt = schedule.end_at
            if end_dt.tzinfo is None:
                tz = pytz.timezone(schedule.timezone or "Asia/Kolkata")
                end_dt = tz.localize(end_dt)
            if next_run > end_dt:
                next_run = None

        schedule.next_run_at = next_run
        await self.repo.update_status(db, schedule, "ACTIVE")
        schedule.updated_by = actor_uuid
        await db_flush(db)

        # Publish event
        await self.event_service.publish_event(
            event_code=WorkflowEventCode.WORKFLOW_SCHEDULE_ACTIVATED,
            entity_type="workflow_schedules",
            entity_id=schedule.id,
            actor_type="USER",
            actor_id=actor_uuid,
            action_type="ACTIVATE",
            event_summary=f"Workflow schedule {schedule.schedule_name} activated",
            event_payload={"next_run_at": next_run.isoformat() if next_run else None},
            db=db
        )

        return schedule

    async def pause_schedule(self, id: UUID, current_user, db) -> Phase2WorkflowSchedule:
        schedule = await self.repo.get_by_id(db, id)
        if not schedule:
            raise HTTPException(
                status_code=404,
                detail=ResponseHelper.error(message="Workflow schedule not found", error_code="NOT_FOUND").model_dump()
            )

        actor_uuid = resolve_user_uuid(db, current_user.id)

        validate_transition(schedule.schedule_status, "PAUSED", schedule.approval_required)

        schedule.next_run_at = None
        await self.repo.update_status(db, schedule, "PAUSED")
        schedule.updated_by = actor_uuid
        await db_flush(db)

        await self.event_service.publish_event(
            event_code=WorkflowEventCode.WORKFLOW_SCHEDULE_PAUSED,
            entity_type="workflow_schedules",
            entity_id=schedule.id,
            actor_type="USER",
            actor_id=actor_uuid,
            action_type="PAUSE",
            event_summary=f"Workflow schedule {schedule.schedule_name} paused",
            event_payload={},
            db=db
        )

        return schedule

    async def resume_schedule(self, id: UUID, current_user, db) -> Phase2WorkflowSchedule:
        schedule = await self.repo.get_by_id(db, id)
        if not schedule:
            raise HTTPException(
                status_code=404,
                detail=ResponseHelper.error(message="Workflow schedule not found", error_code="NOT_FOUND").model_dump()
            )

        actor_uuid = resolve_user_uuid(db, current_user.id)

        validate_transition(schedule.schedule_status, "ACTIVE", schedule.approval_required)

        next_run = calculate_next_run_at(schedule.schedule_type, schedule.cron_expression, schedule.timezone, schedule.start_at)
        if next_run and schedule.end_at:
            end_dt = schedule.end_at
            if end_dt.tzinfo is None:
                tz = pytz.timezone(schedule.timezone or "Asia/Kolkata")
                end_dt = tz.localize(end_dt)
            if next_run > end_dt:
                next_run = None

        schedule.next_run_at = next_run
        await self.repo.update_status(db, schedule, "ACTIVE")
        schedule.updated_by = actor_uuid
        await db_flush(db)

        await self.event_service.publish_event(
            event_code=WorkflowEventCode.WORKFLOW_SCHEDULE_ACTIVATED,
            entity_type="workflow_schedules",
            entity_id=schedule.id,
            actor_type="USER",
            actor_id=actor_uuid,
            action_type="RESUME",
            event_summary=f"Workflow schedule {schedule.schedule_name} resumed",
            event_payload={"next_run_at": next_run.isoformat() if next_run else None},
            db=db
        )

        return schedule

    async def retire_schedule(self, id: UUID, current_user, db) -> Phase2WorkflowSchedule:
        schedule = await self.repo.get_by_id(db, id)
        if not schedule:
            raise HTTPException(
                status_code=404,
                detail=ResponseHelper.error(message="Workflow schedule not found", error_code="NOT_FOUND").model_dump()
            )

        actor_uuid = resolve_user_uuid(db, current_user.id)

        validate_transition(schedule.schedule_status, "RETIRED", schedule.approval_required)

        schedule.next_run_at = None
        await self.repo.update_status(db, schedule, "RETIRED")
        schedule.updated_by = actor_uuid
        await db_flush(db)

        await self.event_service.publish_event(
            event_code=WorkflowEventCode.WORKFLOW_SCHEDULE_RETIRED,
            entity_type="workflow_schedules",
            entity_id=schedule.id,
            actor_type="USER",
            actor_id=actor_uuid,
            action_type="RETIRE",
            event_summary=f"Workflow schedule {schedule.schedule_name} retired",
            event_payload={},
            db=db
        )

        return schedule

    async def decide_approval(self, approval_id: UUID, decision: str, reason: str, current_user, db) -> Phase2WorkflowSchedule:
        # Load approval record
        approval = await db_get(db, WorkflowScheduleApproval, approval_id)
        if not approval:
            # Fallback: check if the approval_id matches a schedule_id
            stmt = select(WorkflowScheduleApproval).where(
                WorkflowScheduleApproval.schedule_id == approval_id
            ).order_by(WorkflowScheduleApproval.created_at.desc()).limit(1)
            res = await execute_statement(db, stmt)
            approval = res.scalar()

        if not approval:
            # Self-healing: if the schedule is in PENDING_APPROVAL but has no record, auto-create it
            schedule = await self.repo.get_by_id(db, approval_id)
            sched_status_str = schedule.schedule_status.value if hasattr(schedule.schedule_status, "value") else str(schedule.schedule_status)
            if schedule and sched_status_str == "PENDING_APPROVAL":
                approval = WorkflowScheduleApproval(
                    id=uuid4(),
                    tenant_id=schedule.tenant_id,
                    schedule_id=schedule.id,
                    approval_type="ACTIVATION",
                    approval_status="PENDING",
                    approval_group_id=schedule.approval_group_id,
                    submitted_by=resolve_user_uuid(db, current_user.id),
                    created_by=resolve_user_uuid(db, current_user.id),
                    updated_by=resolve_user_uuid(db, current_user.id)
                )
                db.add(approval)
            else:
                raise HTTPException(
                    status_code=404,
                    detail=ResponseHelper.error(message="Approval record not found", error_code="NOT_FOUND").model_dump()
                )

        if approval.approval_status not in ["PENDING", "ESCALATED"]:
            raise HTTPException(
                status_code=400,
                detail=ResponseHelper.error(
                    message=f"Schedule has already been decided (Status: {approval.approval_status})",
                    error_code="ALREADY_DECIDED"
                ).model_dump()
            )

        schedule = await self.repo.get_by_id(db, approval.schedule_id)
        if not schedule:
            raise HTTPException(
                status_code=404,
                detail=ResponseHelper.error(message="Workflow schedule not found for approval", error_code="NOT_FOUND").model_dump()
            )

        actor_uuid = resolve_user_uuid(db, current_user.id)

        # Verify decider permissions and group association
        is_member = False
        if approval.approval_group_id is not None:
            member_stmt = select(ApprovalGroupMember).where(
                ApprovalGroupMember.approval_group_id == approval.approval_group_id,
                ApprovalGroupMember.user_id == actor_uuid
            )
            member_res = await execute_statement(db, member_stmt)
            is_member = member_res.scalar() is not None

        role_code = getattr(current_user, "role_code", None)
        is_admin = role_code in ["ADMIN", "GOVERNANCE_MANAGER"]
        is_general_approver = role_code in ["APPROVER", "REVIEWER"]

        if not is_member and not is_admin and not is_general_approver:
            raise HTTPException(
                status_code=403,
                detail=ResponseHelper.error(
                    message="Access denied: only members of the assigned approval group or admins can decide approvals",
                    error_code="FORBIDDEN"
                ).model_dump()
            )

        # Update approval entry
        approval.approver_user_id = actor_uuid
        approval.approval_status = decision
        approval.decision_reason = reason
        approval.decided_at = datetime.now(timezone.utc)
        approval.updated_by = actor_uuid

        if decision == "APPROVED":
            # Transition status and activate
            schedule = await self.activate_schedule(schedule.id, current_user, db, bypass_abac=True)
            
            await self.event_service.publish_event(
                event_code=WorkflowEventCode.WORKFLOW_SCHEDULE_APPROVED,
                entity_type="workflow_schedules",
                entity_id=schedule.id,
                actor_type="USER",
                actor_id=actor_uuid,
                action_type="APPROVE",
                event_summary=f"Approval decision: APPROVED for schedule {schedule.schedule_name}",
                event_payload={"approval_id": str(approval.id), "reason": reason},
                db=db
            )
        elif decision in ["REJECTED", "CHANGES_REQUESTED"]:
            # Transition PENDING_APPROVAL -> DRAFT
            validate_transition(schedule.schedule_status, ScheduleStatus.DRAFT, schedule.approval_required)
            await self.repo.update_status(db, schedule, ScheduleStatus.DRAFT)
            schedule.updated_by = actor_uuid
            
            await self.event_service.publish_event(
                event_code=WorkflowEventCode.WORKFLOW_SCHEDULE_UPDATED,
                entity_type="workflow_schedules",
                entity_id=schedule.id,
                actor_type="USER",
                actor_id=actor_uuid,
                action_type="REJECT" if decision == "REJECTED" else "CHANGES_REQUESTED",
                event_summary=f"Approval decision: {decision} for schedule {schedule.schedule_name}",
                event_payload={"approval_id": str(approval.id), "reason": reason},
                db=db
            )
        elif decision == "ESCALATED":
            # Leaves the schedule in PENDING_APPROVAL, but logs the escalation
            await self.event_service.publish_event(
                event_code=WorkflowEventCode.WORKFLOW_SCHEDULE_UPDATED,
                entity_type="workflow_schedules",
                entity_id=schedule.id,
                actor_type="USER",
                actor_id=actor_uuid,
                action_type="ESCALATE",
                event_summary=f"Approval decision: ESCALATED for schedule {schedule.schedule_name}",
                event_payload={"approval_id": str(approval.id), "reason": reason},
                db=db
            )

        await db_flush(db)
        return schedule

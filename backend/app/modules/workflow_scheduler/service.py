from uuid import UUID, uuid4
from datetime import datetime, timezone
import inspect
try:
    import pytz
except ImportError:
    pytz = None

try:
    from croniter import croniter
except ImportError:
    croniter = None
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
        "DRAFT": ["PENDING_APPROVAL", "ACTIVE", "RETIRED"] if not approval_required else ["PENDING_APPROVAL", "RETIRED"],
        "PENDING_APPROVAL": ["ACTIVE", "DRAFT", "RETIRED"],
        "ACTIVE": ["PAUSED", "RETIRED"],
        "PAUSED": ["ACTIVE", "RETIRED"],
        "RETIRED": []
    }
    
    allowed = valid_transitions.get(from_status_str, [])
    if to_status_str not in allowed:
        raise WorkflowScheduleStateError(from_status_str, to_status_str)


def calculate_next_run_at(schedule_type: str, cron_expression: str, timezone_str: str, start_at: datetime = None, metadata_json: dict = None) -> datetime | None:
    sched_type_str = schedule_type.value if hasattr(schedule_type, "value") else str(schedule_type)
    if sched_type_str == "MANUAL":
        return None
    
    if pytz:
        try:
            tz = pytz.timezone(timezone_str or "Asia/Kolkata")
        except Exception:
            tz = timezone.utc
    else:
        try:
            from zoneinfo import ZoneInfo
            tz = ZoneInfo(timezone_str or "Asia/Kolkata")
        except Exception:
            tz = timezone.utc

    now = datetime.now(tz)
    
    base_time = now
    if start_at:
        if start_at.tzinfo is None:
            if hasattr(tz, 'localize'):
                start_at = tz.localize(start_at)
            else:
                start_at = start_at.replace(tzinfo=tz)
        else:
            start_at = start_at.astimezone(tz)
        
        if start_at > now:
            base_time = start_at
            
    if sched_type_str == "CRON":
        if not cron_expression or not croniter:
            return None
        iter = croniter(cron_expression, base_time)
        return iter.get_next(datetime)
    
    type_cron_map = {
        "DAILY": "0 0 * * *",
        "WEEKLY": "0 0 * * 0",
        "MONTHLY": "0 0 1 * *",
    }
    cron_expr = cron_expression or type_cron_map.get(sched_type_str)
    if cron_expr and croniter:
        iter = croniter(cron_expr, base_time)
        return iter.get_next(datetime)
    
    return None
    
    if sched_type_str == "ONE_TIME":
        return start_at if start_at and start_at > now else None
        
    if sched_type_str == "INTERVAL":
        from datetime import timedelta
        interval_secs = metadata_json.get('interval_seconds', 3600) if metadata_json else 3600
        return base_time + timedelta(seconds=interval_secs)
        
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
            "agent_name": ass.agent.agent_name if ass.agent else "Unknown",
            "model_id": ass.model_id,
            "model_name": ass.model.model_name if ass.model else None,
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

    approval_departments = []
    approval_layers = []
    if hasattr(item, "layer_selections") and item.layer_selections:
        for s in sorted(item.layer_selections, key=lambda x: x.layer_order or 0):
            if hasattr(s, "department") and s.department:
                approval_departments.append(s.department.department_code)
                approval_layers.append({
                    "department_code": s.department.department_code,
                    "department_name": s.department.department_name,
                    "department_id": str(s.department_id),
                    "layer_order": s.layer_order,
                    "approver_user_ids": [str(u) for u in (s.approver_user_ids or [])],
                    "require_all_approvers": s.require_all_approvers if s.require_all_approvers is not None else True
                })

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
        "approval_departments": approval_departments,
        "approval_layers": approval_layers,
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
        actor_uuid = resolve_user_uuid(db, current_user.id)

        # 1. Validate payload
        val_res = await WorkflowScheduleValidationService.validate_create(payload, db, tenant_id=actor_uuid)
        if not val_res["is_valid"]:
            details = [{"field": e.field, "message": e.message} for e in val_res["errors"]]
            raise HTTPException(
                status_code=422,
                detail=ResponseHelper.error(
                    message="Validation failed for workflow schedule creation.",
                    error_code="VALIDATION_ERROR",
                    details=details
                ).model_dump(mode="json")
            )

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
                ).model_dump(mode="json")
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

        approval_layers_input = data.pop("approval_layers", None)
        approval_departments_input = data.pop("approval_departments", None)

        # 4. Insert records
        schedule = await self.repo.create(db, data, processed_assignments)
        
        # Save Layer Selections
        from app.modules.department.models import Department, DepartmentOwnerAssignment
        from app.modules.workflow_scheduler.models import ScheduleApprovalLayerSelection
        from app.shared.db_compat import execute_statement

        if approval_layers_input:
            codes = [l.get("department_code") for l in approval_layers_input if l.get("department_code")]
            if codes:
                stmt = select(Department.id, Department.department_code).where(Department.department_code.in_(codes))
                res = await execute_statement(db, stmt)
                dept_map = {row[1]: row[0] for row in res.fetchall()}
                for i, layer_info in enumerate(approval_layers_input):
                    code = layer_info.get("department_code")
                    dept_id = dept_map.get(code)
                    if dept_id:
                        user_ids = [str(u) for u in layer_info.get("approver_user_ids", [])]
                        req_all = layer_info.get("require_all_approvers", True)
                        if not user_ids:
                            owner_stmt = select(DepartmentOwnerAssignment.owner_user_id).where(DepartmentOwnerAssignment.department_id == dept_id)
                            owner_res = await execute_statement(db, owner_stmt)
                            user_ids = [str(uid) for uid in owner_res.scalars().all() if uid]
                        layer = ScheduleApprovalLayerSelection(
                            id=uuid4(),
                            tenant_id=schedule.tenant_id,
                            schedule_id=schedule.id,
                            department_id=dept_id,
                            layer_order=i+1,
                            approver_user_ids=user_ids,
                            require_all_approvers=req_all
                        )
                        db.add(layer)
        elif approval_departments_input:
            stmt = select(Department.id, Department.department_code).where(Department.department_code.in_(approval_departments_input))
            res = await execute_statement(db, stmt)
            dept_map = {row[1]: row[0] for row in res.fetchall()}
            for i, code in enumerate(approval_departments_input):
                dept_id = dept_map.get(code)
                if dept_id:
                    owner_stmt = select(DepartmentOwnerAssignment.owner_user_id).where(DepartmentOwnerAssignment.department_id == dept_id)
                    owner_res = await execute_statement(db, owner_stmt)
                    user_ids = [str(uid) for uid in owner_res.scalars().all() if uid]
                    layer = ScheduleApprovalLayerSelection(
                        id=uuid4(),
                        tenant_id=schedule.tenant_id,
                        schedule_id=schedule.id,
                        department_id=dept_id,
                        layer_order=i+1,
                        approver_user_ids=user_ids,
                        require_all_approvers=True
                    )
                    db.add(layer)

        history_rec = WorkflowScheduleHistory(
            id=uuid4(),
            tenant_id=schedule.tenant_id,
            schedule_id=schedule.id,
            change_type="CREATE",
            change_summary="Schedule created",
            before_json={},
            after_json=serialize_schedule_history(schedule),
            changed_by=actor_uuid,
            created_by=actor_uuid,
            updated_by=actor_uuid
        )
        db.add(history_rec)

        # If created as PENDING_APPROVAL, create approval record and notifications
        sched_status_str = schedule.schedule_status.value if hasattr(schedule.schedule_status, "value") else str(schedule.schedule_status)
        if sched_status_str == "PENDING_APPROVAL":
            if approval_layers_input or approval_departments_input:
                from app.shared.db_compat import db_flush
                await db_flush(db)
                approval_cycle_id = uuid4()
                already_decided_owner_ids = set()
                await self.resolve_next_layer(schedule.id, approval_cycle_id, already_decided_owner_ids, actor_uuid, db)
            elif schedule.approval_group_id:
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
                
                stmt = select(ApprovalGroupMember.user_id).where(ApprovalGroupMember.approval_group_id == schedule.approval_group_id)
                from app.shared.db_compat import execute_statement
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
                        entity_type="WORKFLOW_SCHEDULE",
                        entity_id=schedule.id,
                        status="UNREAD",
                        created_by=actor_uuid,
                        updated_by=actor_uuid
                    )
                    db.add(notif)
            else:
                approval = WorkflowScheduleApproval(
                    id=uuid4(),
                    tenant_id=schedule.tenant_id,
                    schedule_id=schedule.id,
                    approval_type="ACTIVATION",
                    approval_status="PENDING",
                    submitted_by=actor_uuid,
                    created_by=actor_uuid,
                    updated_by=actor_uuid
                )
                db.add(approval)

        # 5. Publish event
        await self.event_service.publish_schedule_created(schedule.id, actor_uuid, db)

        return schedule

    async def update_schedule(self, id: UUID, payload, current_user, db) -> Phase2WorkflowSchedule:
        schedule = await self.repo.get_by_id(db, id)
        if not schedule:
            raise HTTPException(
                status_code=404,
                detail=ResponseHelper.error(message="Workflow schedule not found", error_code="NOT_FOUND").model_dump()
            )

        actor_uuid = resolve_user_uuid(db, current_user.id)

        # Only allowed in DRAFT, PAUSED or ACTIVE status
        sched_status_str = schedule.schedule_status.value if hasattr(schedule.schedule_status, "value") else str(schedule.schedule_status)
        if sched_status_str not in ["DRAFT", "PAUSED", "ACTIVE"]:
            raise WorkflowScheduleStateError(sched_status_str, "UPDATE", "Updates are only allowed in DRAFT, PAUSED, or ACTIVE status")

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
        val_res = await WorkflowScheduleValidationService.validate_create(
            merged_state, db, tenant_id=schedule.tenant_id, schedule_id=schedule.id
        )
        if not val_res["is_valid"]:
            details = [{"field": e.field, "message": e.message} for e in val_res["errors"]]
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
                ass_dict["allowed_tools_json"] = ass_dict.pop("allowed_tools", ass_dict.get("allowed_tools_json", []))
                ass_dict["allowed_data_sources_json"] = ass_dict.pop("allowed_data_sources", ass_dict.get("allowed_data_sources_json", []))
                ass_dict["blocked_operations_json"] = ass_dict.pop("blocked_operations", ass_dict.get("blocked_operations_json", []))
                boundary_rules = ass_dict.pop("boundary_rules", None)
                if boundary_rules:
                    ass_dict["boundary_rules_json"] = boundary_rules.model_dump() if hasattr(boundary_rules, "model_dump") else boundary_rules
                
                ass_dict["tenant_id"] = schedule.tenant_id
                ass_dict["created_by"] = actor_uuid
                ass_dict["updated_by"] = actor_uuid
                processed_assignments.append(ass_dict)
            update_data["agent_assignments"] = processed_assignments
        approval_layers_input = update_data.pop("approval_layers", None)
        approval_departments_input = update_data.pop("approval_departments", None)

        # Update in database
        updated_schedule = await self.repo.update(db, schedule, update_data)
        updated_schedule.updated_by = actor_uuid
        
        if approval_layers_input is not None or approval_departments_input is not None:
            from app.modules.department.models import Department, DepartmentOwnerAssignment
            from app.modules.workflow_scheduler.models import ScheduleApprovalLayerSelection
            from app.shared.db_compat import execute_statement
            
            # Delete existing
            del_stmt = sa.delete(ScheduleApprovalLayerSelection).where(ScheduleApprovalLayerSelection.schedule_id == schedule.id)
            await execute_statement(db, del_stmt)
            
            if approval_layers_input:
                codes = [l.get("department_code") for l in approval_layers_input if l.get("department_code")]
                if codes:
                    stmt = select(Department.id, Department.department_code).where(Department.department_code.in_(codes))
                    res = await execute_statement(db, stmt)
                    dept_map = {row[1]: row[0] for row in res.fetchall()}
                    for i, layer_info in enumerate(approval_layers_input):
                        code = layer_info.get("department_code")
                        dept_id = dept_map.get(code)
                        if dept_id:
                            user_ids = [str(u) for u in layer_info.get("approver_user_ids", [])]
                            req_all = layer_info.get("require_all_approvers", True)
                            if not user_ids:
                                owner_stmt = select(DepartmentOwnerAssignment.owner_user_id).where(DepartmentOwnerAssignment.department_id == dept_id)
                                owner_res = await execute_statement(db, owner_stmt)
                                user_ids = [str(uid) for uid in owner_res.scalars().all() if uid]
                            layer = ScheduleApprovalLayerSelection(
                                id=uuid4(),
                                tenant_id=schedule.tenant_id,
                                schedule_id=schedule.id,
                                department_id=dept_id,
                                layer_order=i+1,
                                approver_user_ids=user_ids,
                                require_all_approvers=req_all
                            )
                            db.add(layer)
            elif approval_departments_input:
                stmt = select(Department.id, Department.department_code).where(Department.department_code.in_(approval_departments_input))
                res = await execute_statement(db, stmt)
                dept_map = {row[1]: row[0] for row in res.fetchall()}
                for i, code in enumerate(approval_departments_input):
                    dept_id = dept_map.get(code)
                    if dept_id:
                        owner_stmt = select(DepartmentOwnerAssignment.owner_user_id).where(DepartmentOwnerAssignment.department_id == dept_id)
                        owner_res = await execute_statement(db, owner_stmt)
                        user_ids = [str(uid) for uid in owner_res.scalars().all() if uid]
                        layer = ScheduleApprovalLayerSelection(
                            id=uuid4(),
                            tenant_id=schedule.tenant_id,
                            schedule_id=schedule.id,
                            department_id=dept_id,
                            layer_order=i+1,
                            approver_user_ids=user_ids,
                            require_all_approvers=True
                        )
                        db.add(layer)
            from app.shared.db_compat import db_flush
            await db_flush(db)

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
        )
        db.add(history_rec)

        new_status_str = updated_schedule.schedule_status.value if hasattr(updated_schedule.schedule_status, "value") else str(updated_schedule.schedule_status)
        if new_status_str == "PENDING_APPROVAL" and updated_schedule.approval_required:
            from app.modules.workflow_scheduler.models import WorkflowScheduleApproval, ScheduleApprovalLayerSelection
            existing_approvals_count = (await execute_statement(db, sa.select(sa.func.count()).select_from(WorkflowScheduleApproval).where(WorkflowScheduleApproval.schedule_id == updated_schedule.id, WorkflowScheduleApproval.approval_status == "PENDING"))).scalar() or 0
            if existing_approvals_count == 0:
                has_layers = (await execute_statement(db, sa.select(sa.func.count()).select_from(ScheduleApprovalLayerSelection).where(ScheduleApprovalLayerSelection.schedule_id == updated_schedule.id))).scalar()
                if has_layers:
                    approval_cycle_id = uuid4()
                    already_decided_owner_ids = set()
                    await self.resolve_next_layer(updated_schedule.id, approval_cycle_id, already_decided_owner_ids, actor_uuid, db)
                elif updated_schedule.approval_group_id:
                    approval = WorkflowScheduleApproval(
                        id=uuid4(),
                        tenant_id=updated_schedule.tenant_id,
                        schedule_id=updated_schedule.id,
                        approval_type="ACTIVATION",
                        approval_status="PENDING",
                        approval_group_id=updated_schedule.approval_group_id,
                        submitted_by=actor_uuid,
                        created_by=actor_uuid,
                        updated_by=actor_uuid
                    )
                    db.add(approval)
                    
                    stmt = select(ApprovalGroupMember.user_id).where(ApprovalGroupMember.approval_group_id == updated_schedule.approval_group_id)
                    res = await execute_statement(db, stmt)
                    member_ids = [r[0] for r in res.fetchall()]
                    for member_id in member_ids:
                        notif = WorkflowNotification(
                            id=uuid4(),
                            tenant_id=updated_schedule.tenant_id,
                            recipient_user_id=member_id,
                            notification_type="APPROVAL_REQUIRED",
                            title="Schedule Approval Required",
                            message=f"Approval is required for updated schedule {updated_schedule.schedule_name} ({updated_schedule.schedule_code}).",
                            severity="HIGH",
                            status="UNREAD",
                            created_by=actor_uuid,
                            updated_by=actor_uuid
                        )
                        db.add(notif)

        await db_flush(db)

        # Publish event
        await self.event_service.publish_schedule_updated(schedule.id, actor_uuid, before_json, serialize_schedule_history(updated_schedule), db)

        return updated_schedule

    async def resolve_next_layer(self, schedule_id: UUID, approval_cycle_id: UUID, already_decided_owner_ids: set, actor_uuid: UUID, db):
        from app.modules.workflow_scheduler.models import ScheduleApprovalLayerSelection, WorkflowScheduleApproval, Phase2WorkflowSchedule
        from app.modules.department.models import DepartmentOwnerAssignment, Department
        from app.modules.workflow_notifications.models import WorkflowNotification
        
        # Walk this schedule's layer selections in fixed layer_order
        stmt = sa.select(ScheduleApprovalLayerSelection, Department.department_code).join(
            Department, Department.id == ScheduleApprovalLayerSelection.department_id
        ).where(
            ScheduleApprovalLayerSelection.schedule_id == schedule_id
        ).order_by(ScheduleApprovalLayerSelection.layer_order.asc())
        res = await execute_statement(db, stmt)
        selections_with_codes = res.all()

        schedule_res = await execute_statement(db, sa.select(Phase2WorkflowSchedule.schedule_name).where(Phase2WorkflowSchedule.id == schedule_id))
        schedule_name = schedule_res.scalar() or "Workflow Schedule"
        
        for sel, dept_code in selections_with_codes:
            # Skip any department that already has an approval row in this cycle
            check_stmt = sa.select(WorkflowScheduleApproval).where(
                WorkflowScheduleApproval.schedule_id == schedule_id,
                WorkflowScheduleApproval.approval_cycle_id == approval_cycle_id,
                WorkflowScheduleApproval.department_id == sel.department_id
            )
            check_res = await execute_statement(db, check_stmt)
            if check_res.scalar() is not None:
                continue

            # Determine assigned user list for this layer
            assigned_user_ids = [UUID(str(u)) if not isinstance(u, UUID) else u for u in (sel.approver_user_ids or [])]
            fallback_group_id = None

            if not assigned_user_ids:
                owner_stmt = sa.select(DepartmentOwnerAssignment).where(
                    DepartmentOwnerAssignment.department_id == sel.department_id
                )
                owner_res = await execute_statement(db, owner_stmt)
                assignments = owner_res.scalars().all()
                for a in assignments:
                    if a.owner_user_id:
                        assigned_user_ids.append(a.owner_user_id)
                    elif a.owner_group_id:
                        fallback_group_id = a.owner_group_id

            if not assigned_user_ids and not fallback_group_id:
                raise HTTPException(status_code=400, detail=f"No approver users or owner group assigned for department {dept_code or sel.department_id}")

            # Find parent approval id for chaining
            parent_stmt = sa.select(WorkflowScheduleApproval.id).where(
                WorkflowScheduleApproval.schedule_id == schedule_id,
                WorkflowScheduleApproval.approval_cycle_id == approval_cycle_id
            ).order_by(WorkflowScheduleApproval.created_at.desc()).limit(1)
            parent_res = await execute_statement(db, parent_stmt)
            parent_id = parent_res.scalar()

            req_all = sel.require_all_approvers if sel.require_all_approvers is not None else True

            # Deduplication / Auto-Skip evaluation
            assigned_ids_str = [str(u) for u in assigned_user_ids]
            if fallback_group_id:
                assigned_ids_str.append(str(fallback_group_id))

            all_decided = all(uid in already_decided_owner_ids for uid in assigned_ids_str)
            any_decided = any(uid in already_decided_owner_ids for uid in assigned_ids_str)

            should_skip = (req_all and all_decided) or (not req_all and any_decided)

            if should_skip and len(assigned_ids_str) > 0:
                # AUTO-SKIP this layer
                skipped_approval = WorkflowScheduleApproval(
                    id=uuid4(),
                    tenant_id=sel.tenant_id,
                    schedule_id=schedule_id,
                    approval_cycle_id=approval_cycle_id,
                    approval_layer=sel.layer_order,
                    department_id=sel.department_id,
                    approval_type="ACTIVATION",
                    approval_status="SKIPPED",
                    approver_user_id=assigned_user_ids[0] if assigned_user_ids else None,
                    approval_group_id=fallback_group_id,
                    parent_approval_id=parent_id,
                    skip_reason=f"Auto-skipped: assigned approver(s) already decided in an earlier layer of this cycle",
                    decided_by=None,
                    decided_at=datetime.now(timezone.utc),
                    submitted_by=actor_uuid,
                    created_by=actor_uuid,
                    updated_by=actor_uuid
                )
                db.add(skipped_approval)
                await db_flush(db)
                
                await self.event_service.publish_layer_skipped(
                    schedule_id=schedule_id,
                    actor_id=actor_uuid,
                    approval_cycle_id=approval_cycle_id,
                    correlation_id=str(approval_cycle_id),
                    approval_layer=sel.layer_order,
                    department_code=dept_code,
                    parent_approval_id=parent_id,
                    approval_id=skipped_approval.id,
                    skip_reason=skipped_approval.skip_reason,
                    db=db
                )
                continue
            else:
                # Create PENDING rows for each active approver in this layer
                created_approvals = []
                
                # If unanimous with some users already decided, create SKIPPED for those and PENDING for remaining
                for uid in assigned_user_ids:
                    if str(uid) in already_decided_owner_ids and req_all:
                        skip_row = WorkflowScheduleApproval(
                            id=uuid4(),
                            tenant_id=sel.tenant_id,
                            schedule_id=schedule_id,
                            approval_cycle_id=approval_cycle_id,
                            approval_layer=sel.layer_order,
                            department_id=sel.department_id,
                            approval_type="ACTIVATION",
                            approval_status="SKIPPED",
                            approver_user_id=uid,
                            parent_approval_id=parent_id,
                            skip_reason=f"User {uid} already approved in an earlier layer",
                            decided_at=datetime.now(timezone.utc),
                            submitted_by=actor_uuid,
                            created_by=actor_uuid,
                            updated_by=actor_uuid
                        )
                        db.add(skip_row)
                    else:
                        pending_approval = WorkflowScheduleApproval(
                            id=uuid4(),
                            tenant_id=sel.tenant_id,
                            schedule_id=schedule_id,
                            approval_cycle_id=approval_cycle_id,
                            approval_layer=sel.layer_order,
                            department_id=sel.department_id,
                            approval_type="ACTIVATION",
                            approval_status="PENDING",
                            approver_user_id=uid,
                            parent_approval_id=parent_id,
                            submitted_by=actor_uuid,
                            created_by=actor_uuid,
                            updated_by=actor_uuid
                        )
                        db.add(pending_approval)
                        created_approvals.append(pending_approval)
                        
                        # Send individual targeted notification
                        notif = WorkflowNotification(
                            id=uuid4(),
                            tenant_id=sel.tenant_id,
                            recipient_user_id=uid,
                            notification_type="APPROVAL_REQUIRED",
                            title="Schedule Approval Required",
                            message=f"Approval is required for schedule {schedule_name} (Layer {sel.layer_order} - {dept_code}).",
                            severity="HIGH",
                            status="UNREAD",
                            created_by=actor_uuid,
                            updated_by=actor_uuid
                        )
                        db.add(notif)

                if fallback_group_id and not assigned_user_ids:
                    group_approval = WorkflowScheduleApproval(
                        id=uuid4(),
                        tenant_id=sel.tenant_id,
                        schedule_id=schedule_id,
                        approval_cycle_id=approval_cycle_id,
                        approval_layer=sel.layer_order,
                        department_id=sel.department_id,
                        approval_type="ACTIVATION",
                        approval_status="PENDING",
                        approval_group_id=fallback_group_id,
                        parent_approval_id=parent_id,
                        submitted_by=actor_uuid,
                        created_by=actor_uuid,
                        updated_by=actor_uuid
                    )
                    db.add(group_approval)
                    created_approvals.append(group_approval)

                await db_flush(db)
                return created_approvals[0] if created_approvals else None
        
        # Chain exhausted
        return None

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
        
        before_json = serialize_schedule_history(schedule)

        # Enforce exactly one PRIMARY assignment
        from app.modules.workflow_scheduler.models import WorkflowScheduleAgentAssignment, ScheduleApprovalLayerSelection
        stmt = sa.select(sa.func.count()).select_from(WorkflowScheduleAgentAssignment).where(
            WorkflowScheduleAgentAssignment.schedule_id == id,
            WorkflowScheduleAgentAssignment.assignment_role == "PRIMARY",
            WorkflowScheduleAgentAssignment.is_deleted == False
        )
        res = await execute_statement(db, stmt)
        if res.scalar() != 1:
            raise HTTPException(
                status_code=400,
                detail=ResponseHelper.error(
                    message="Schedule must have exactly one PRIMARY agent assignment.",
                    error_code="VALIDATION_ERROR"
                ).model_dump()
            )

        # Enforce that schedule has approval required
        if not schedule.approval_required:
            raise HTTPException(
                status_code=400,
                detail=ResponseHelper.error(
                    message="Approval is not required for this schedule.",
                    error_code="VALIDATION_ERROR"
                ).model_dump()
            )
            
        layer_stmt = sa.select(ScheduleApprovalLayerSelection).where(
            ScheduleApprovalLayerSelection.schedule_id == id
        ).order_by(ScheduleApprovalLayerSelection.layer_order.asc())
        layer_res = await execute_statement(db, layer_stmt)
        layers = layer_res.scalars().all()
        if not layers:
            raise HTTPException(
                status_code=400,
                detail=ResponseHelper.error(
                    message="Schedule must have at least one department approval layer selected.",
                    error_code="VALIDATION_ERROR"
                ).model_dump()
            )

        # Self-Approval Guard: Check if creator is configured as the sole approver in any layer
        if schedule.owner_user_id:
            creator_id = str(schedule.owner_user_id)
            for sel in layers:
                assigned_uids = [str(u) for u in (sel.approver_user_ids or [])]
                if len(assigned_uids) == 1 and assigned_uids[0] == creator_id:
                    raise HTTPException(
                        status_code=400,
                        detail=ResponseHelper.error(
                            message="Self-approval violation: The schedule creator cannot be the sole approver for an approval layer.",
                            error_code="SELF_APPROVAL_VIOLATION"
                        ).model_dump()
                    )

        # Check if >1 departments are selected but they all resolve to the exact same sole approver
        all_layer_users = set()
        for sel in layers:
            uids = [str(u) for u in (sel.approver_user_ids or [])]
            all_layer_users.update(uids)

        if len(layers) > 1 and len(all_layer_users) == 1:
            raise HTTPException(
                status_code=400,
                detail=ResponseHelper.error(
                    message="Entire selected department set resolves to a single owner.",
                    error_code="VALIDATION_ERROR"
                ).model_dump()
            )

        # Update status
        await self.repo.update_status(db, schedule, "PENDING_APPROVAL")
        schedule.updated_by = actor_uuid

        # Create NEW approval_cycle_id for every submission (resubmissions rebuild chain from scratch)
        approval_cycle_id = uuid4()
        already_decided_owner_ids = set()

        next_layer = await self.resolve_next_layer(id, approval_cycle_id, already_decided_owner_ids, actor_uuid, db)
        
        if next_layer is None:
            raise HTTPException(
                status_code=400,
                detail=ResponseHelper.error(
                    message="Approval chain resolved to zero genuine approvals (all skipped or missing owners).",
                    error_code="VALIDATION_ERROR"
                ).model_dump()
            )

        history_rec = WorkflowScheduleHistory(
            id=uuid4(),
            tenant_id=schedule.tenant_id,
            schedule_id=schedule.id,
            change_type="SUBMIT",
            change_summary="Schedule submitted for multi-layer approval",
            before_json=before_json,
            after_json=serialize_schedule_history(schedule),
            changed_by=actor_uuid,
            created_by=actor_uuid,
            updated_by=actor_uuid
        )
        db.add(history_rec)

        await db_flush(db)

        # Publish event
        await self.event_service.publish_schedule_submitted(
            schedule_id=schedule.id,
            actor_id=actor_uuid,
            approval_cycle_id=approval_cycle_id,
            correlation_id=str(approval_cycle_id),
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

        from app.modules.workflow_scheduler.models import WorkflowScheduleApproval
        stmt = sa.select(WorkflowScheduleApproval.approval_cycle_id).where(
            WorkflowScheduleApproval.schedule_id == id
        ).order_by(WorkflowScheduleApproval.created_at.desc()).limit(1)
        res = await execute_statement(db, stmt)
        latest_cycle_id = res.scalar()
        
        if latest_cycle_id:
            pending_check_stmt = sa.select(sa.func.count()).select_from(WorkflowScheduleApproval).where(
                WorkflowScheduleApproval.approval_cycle_id == latest_cycle_id,
                WorkflowScheduleApproval.approval_status == 'PENDING'
            )
            pending_res = await execute_statement(db, pending_check_stmt)
            if pending_res.scalar() > 0:
                raise HTTPException(
                    status_code=400, 
                    detail=ResponseHelper.error(
                        message="Cannot activate schedule: PENDING approvals still exist in the current approval cycle.",
                        error_code="VALIDATION_ERROR"
                    ).model_dump()
                )

        # Verify state transition rules
        validate_transition(schedule.schedule_status, "ACTIVE", schedule.approval_required)
        
        before_json = serialize_schedule_history(schedule)

        # Enforce exactly one PRIMARY assignment
        from app.modules.workflow_scheduler.models import WorkflowScheduleAgentAssignment
        stmt = sa.select(sa.func.count()).select_from(WorkflowScheduleAgentAssignment).where(
            WorkflowScheduleAgentAssignment.schedule_id == id,
            WorkflowScheduleAgentAssignment.assignment_role == "PRIMARY",
            WorkflowScheduleAgentAssignment.is_deleted == False
        )
        res = await execute_statement(db, stmt)
        if res.scalar() != 1:
            raise HTTPException(
                status_code=400,
                detail=ResponseHelper.error(
                    message="Schedule must have exactly one PRIMARY agent assignment.",
                    error_code="VALIDATION_ERROR"
                ).model_dump()
            )

        # Recalculate next run time
        next_run = calculate_next_run_at(schedule.schedule_type, schedule.cron_expression, schedule.timezone, schedule.start_at, schedule.metadata_json)
        
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
        
        db.add(schedule)
        
        history_rec = WorkflowScheduleHistory(
            id=uuid4(),
            tenant_id=schedule.tenant_id,
            schedule_id=schedule.id,
            change_type="ACTIVATE",
            change_summary="Schedule activated",
            before_json=before_json,
            after_json=serialize_schedule_history(schedule),
            changed_by=actor_uuid,
            created_by=actor_uuid,
            updated_by=actor_uuid
        )
        db.add(history_rec)
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

        before_json = serialize_schedule_history(schedule)

        schedule.next_run_at = None
        await self.repo.update_status(db, schedule, "PAUSED")
        schedule.updated_by = actor_uuid
        
        history_rec = WorkflowScheduleHistory(
            id=uuid4(),
            tenant_id=schedule.tenant_id,
            schedule_id=schedule.id,
            change_type="PAUSE",
            change_summary="Schedule paused",
            before_json=before_json,
            after_json=serialize_schedule_history(schedule),
            changed_by=actor_uuid,
            created_by=actor_uuid,
            updated_by=actor_uuid
        )
        db.add(history_rec)
        
        await db_flush(db)

        await self.event_service.publish_schedule_paused(schedule.id, actor_uuid, db)

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

        before_json = serialize_schedule_history(schedule)

        next_run = calculate_next_run_at(schedule.schedule_type, schedule.cron_expression, schedule.timezone, schedule.start_at, schedule.metadata_json)
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
        
        history_rec = WorkflowScheduleHistory(
            id=uuid4(),
            tenant_id=schedule.tenant_id,
            schedule_id=schedule.id,
            change_type="RESUME",
            change_summary="Schedule resumed",
            before_json=before_json,
            after_json=serialize_schedule_history(schedule),
            changed_by=actor_uuid,
            created_by=actor_uuid,
            updated_by=actor_uuid
        )
        db.add(history_rec)
        
        await db_flush(db)

        # Need to find the latest approval cycle id for the correlation_id
        from app.modules.workflow_scheduler.models import WorkflowScheduleApproval
        cycle_stmt = sa.select(WorkflowScheduleApproval.approval_cycle_id).where(
            WorkflowScheduleApproval.schedule_id == schedule.id
        ).order_by(WorkflowScheduleApproval.created_at.desc()).limit(1)
        cycle_res = await execute_statement(db, cycle_stmt)
        latest_cycle_id = cycle_res.scalar() or schedule.id

        await self.event_service.publish_schedule_activated(
            schedule_id=schedule.id, 
            actor_id=actor_uuid, 
            approval_cycle_id=latest_cycle_id,
            correlation_id=str(latest_cycle_id),
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

        before_json = serialize_schedule_history(schedule)

        schedule.next_run_at = None
        await self.repo.update_status(db, schedule, "RETIRED")
        schedule.updated_by = actor_uuid
        
        history_rec = WorkflowScheduleHistory(
            id=uuid4(),
            tenant_id=schedule.tenant_id,
            schedule_id=schedule.id,
            change_type="RETIRE",
            change_summary="Schedule retired",
            before_json=before_json,
            after_json=serialize_schedule_history(schedule),
            changed_by=actor_uuid,
            created_by=actor_uuid,
            updated_by=actor_uuid
        )
        db.add(history_rec)
        
        await db_flush(db)

        await self.event_service.publish_schedule_retired(schedule.id, actor_uuid, db)

        return schedule

    async def reject_schedule(self, id: UUID, rejection_reason: str, current_user, db) -> Phase2WorkflowSchedule:
        schedule = await self.repo.get_by_id(db, id)
        if not schedule:
            raise HTTPException(
                status_code=404,
                detail=ResponseHelper.error(message="Workflow schedule not found", error_code="NOT_FOUND").model_dump()
            )

        actor_uuid = resolve_user_uuid(db, current_user.id)

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
                ).model_dump(mode="json")
            )

        validate_transition(schedule.schedule_status, "DRAFT", schedule.approval_required)

        before_json = serialize_schedule_history(schedule)

        await self.repo.update_status(db, schedule, "DRAFT")
        schedule.updated_by = actor_uuid
        
        history_rec = WorkflowScheduleHistory(
            id=uuid4(),
            tenant_id=schedule.tenant_id,
            schedule_id=schedule.id,
            change_type="REJECT",
            change_summary=f"Schedule rejected. Reason: {rejection_reason}",
            before_json=before_json,
            after_json=serialize_schedule_history(schedule),
            changed_by=actor_uuid,
            created_by=actor_uuid,
            updated_by=actor_uuid
        )
        db.add(history_rec)
        
        await db_flush(db)
        
        if hasattr(self.event_service, 'publish_schedule_rejected'):
            await self.event_service.publish_schedule_rejected(schedule.id, actor_uuid, rejection_reason, db)
            
        return schedule

    async def decide_approval(self, approval_id: UUID, decision: str, reason: str, current_user, db) -> Phase2WorkflowSchedule:
        actor_uuid = resolve_user_uuid(db, current_user.id)
        # Load approval record
        from app.shared.db_compat import db_get
        from app.modules.workflow_scheduler.models import WorkflowScheduleApproval, ScheduleApprovalLayerSelection
        
        approval = await db_get(db, WorkflowScheduleApproval, approval_id)
        if not approval:
            # Fallback: check if the approval_id matches a schedule_id with a pending approval
            stmt = sa.select(WorkflowScheduleApproval).where(
                WorkflowScheduleApproval.schedule_id == approval_id,
                WorkflowScheduleApproval.approval_status.in_(["PENDING", "ESCALATED"])
            ).order_by(WorkflowScheduleApproval.created_at.desc()).limit(1)
            res = await execute_statement(db, stmt)
            approval = res.scalar()

        schedule = await self.repo.get_by_id(db, approval.schedule_id if approval else approval_id)
        if not schedule:
            raise HTTPException(
                status_code=404,
                detail=ResponseHelper.error(message="Workflow schedule not found for approval", error_code="NOT_FOUND").model_dump()
            )

        if not approval:
            if str(schedule.schedule_status) in ["PENDING_APPROVAL", "ScheduleStatus.PENDING_APPROVAL"]:
                approval = WorkflowScheduleApproval(
                    id=uuid4(),
                    tenant_id=schedule.tenant_id,
                    schedule_id=schedule.id,
                    approval_cycle_id=uuid4(),
                    approval_layer=1,
                    approval_type="ACTIVATION",
                    approval_status="PENDING",
                    approval_group_id=schedule.approval_group_id,
                    submitted_by=schedule.owner_user_id or actor_uuid,
                    created_by=actor_uuid,
                    updated_by=actor_uuid
                )
                db.add(approval)
                await db_flush(db)
            else:
                raise HTTPException(
                    status_code=404,
                    detail=ResponseHelper.error(message="Approval record not found", error_code="NOT_FOUND").model_dump()
                )
            
        if approval.approval_cycle_id:
            stale_check_stmt = sa.select(sa.func.count()).select_from(WorkflowScheduleApproval).where(
                WorkflowScheduleApproval.approval_cycle_id == approval.approval_cycle_id,
                WorkflowScheduleApproval.created_at > approval.created_at
            )
            stale_res = await execute_statement(db, stale_check_stmt)
            if stale_res.scalar() > 0:
                raise HTTPException(
                    status_code=400,
                    detail=ResponseHelper.error(message="Approval record is stale (a newer record exists in this cycle).", error_code="STALE_APPROVAL").model_dump()
                )

        if approval.approval_status not in ["PENDING", "ESCALATED"]:
            raise HTTPException(
                status_code=400,
                detail=ResponseHelper.error(
                    message=f"Schedule has already been decided (Status: {approval.approval_status})",
                    error_code="ALREADY_DECIDED"
                ).model_dump()
            )

        # Verify decider permissions and direct assignment/group association
        is_member = False
        if approval.approval_group_id is not None:
            member_stmt = sa.select(ApprovalGroupMember).where(
                ApprovalGroupMember.approval_group_id == approval.approval_group_id,
                ApprovalGroupMember.user_id == actor_uuid
            )
            member_res = await execute_statement(db, member_stmt)
            is_member = member_res.scalar() is not None

        role_code = getattr(current_user, "role_code", None)
        is_superuser = getattr(current_user, "is_superuser", False) or getattr(current_user, "is_admin", False)
        is_admin = is_superuser or role_code in ["ADMIN", "GOVERNANCE_MANAGER", "SUPER_ADMIN"]
        is_general_approver = role_code in ["APPROVER", "REVIEWER"]
        is_direct_user = approval.approver_user_id == actor_uuid

        if not is_member and not is_admin and not is_general_approver and not is_direct_user:
            raise HTTPException(
                status_code=403,
                detail=ResponseHelper.error(
                    message="Access denied: only the assigned approver, members of the assigned approval group, or admins can decide approvals",
                    error_code="FORBIDDEN"
                ).model_dump()
            )

        # Update approval entry
        approval.updated_by = actor_uuid

        # Fetch department code for event payloads
        dept_code = "UNKNOWN"
        if approval.department_id:
            from app.modules.department.models import Department
            dept_res = await execute_statement(db, sa.select(Department.department_code).where(Department.id == approval.department_id))
            fetched = dept_res.scalar()
            if fetched: dept_code = fetched
            
        base_event_payload = {
            "schedule_id": str(schedule.id),
            "approval_cycle_id": str(approval.approval_cycle_id) if approval.approval_cycle_id else str(schedule.id),
            "correlation_id": str(approval.approval_cycle_id) if approval.approval_cycle_id else str(schedule.id),
            "approval_layer": approval.approval_layer or 1,
            "department_code": dept_code,
            "parent_approval_id": str(approval.parent_approval_id) if approval.parent_approval_id else None,
            "approval_id": str(approval.id)
        }

        # Fetch the layer selection configuration to check quorum mode (Unanimous vs Any-One)
        sel_stmt = sa.select(ScheduleApprovalLayerSelection).where(
            ScheduleApprovalLayerSelection.schedule_id == schedule.id,
            ScheduleApprovalLayerSelection.layer_order == approval.approval_layer
        )
        sel_res = await execute_statement(db, sel_stmt)
        layer_selection = sel_res.scalar()
        req_all = layer_selection.require_all_approvers if (layer_selection and layer_selection.require_all_approvers is not None) else True

        if decision == "APPROVED":
            approval.approval_status = "APPROVED"
            approval.decided_by = actor_uuid
            approval.decided_at = datetime.now(timezone.utc)
            approval.decision_reason = reason
            await db_flush(db)

            # If "Any-One" mode (req_all is False), transition all sibling PENDING approvals in this layer to SUPERSEDED
            if not req_all and approval.approval_cycle_id:
                sibling_stmt = sa.select(WorkflowScheduleApproval).where(
                    WorkflowScheduleApproval.approval_cycle_id == approval.approval_cycle_id,
                    WorkflowScheduleApproval.approval_layer == approval.approval_layer,
                    WorkflowScheduleApproval.id != approval.id,
                    WorkflowScheduleApproval.approval_status == "PENDING"
                )
                sibling_res = await execute_statement(db, sibling_stmt)
                siblings = sibling_res.scalars().all()
                decider_name = getattr(current_user, "name", None) or getattr(current_user, "email", "approver")
                for sib in siblings:
                    sib.approval_status = "SUPERSEDED"
                    sib.skip_reason = f"Layer satisfied by approval from {decider_name}"
                    sib.decided_at = datetime.now(timezone.utc)
                await db_flush(db)

            # Check if there are remaining PENDING approvals in this specific layer
            layer_pending_count = 0
            if approval.approval_cycle_id:
                layer_pending_stmt = sa.select(sa.func.count()).select_from(WorkflowScheduleApproval).where(
                    WorkflowScheduleApproval.approval_cycle_id == approval.approval_cycle_id,
                    WorkflowScheduleApproval.approval_layer == approval.approval_layer,
                    WorkflowScheduleApproval.approval_status == 'PENDING'
                )
                layer_pending_count = (await execute_statement(db, layer_pending_stmt)).scalar() or 0

            if layer_pending_count > 0 and req_all:
                # Layer is not yet complete: other assigned users must still approve
                await self.event_service.publish_event(
                    event_code=WorkflowEventCode.WORKFLOW_SCHEDULE_APPROVED,
                    entity_type="workflow_schedules",
                    entity_id=schedule.id,
                    actor_type="USER",
                    actor_id=actor_uuid,
                    action_type="APPROVE_USER_IN_LAYER",
                    event_summary=f"User approved Layer {approval.approval_layer} (waiting for remaining layer approvers) for schedule {schedule.schedule_name}",
                    event_payload={**base_event_payload, "reason": reason},
                    db=db
                )
                return schedule

            # Layer is complete! Check if subsequent layer selections exist
            layer_check_stmt = sa.select(sa.func.count()).select_from(ScheduleApprovalLayerSelection).where(
                ScheduleApprovalLayerSelection.schedule_id == schedule.id
            )
            layer_count = (await execute_statement(db, layer_check_stmt)).scalar() or 0

            if layer_count > 0 and approval.approval_cycle_id:
                # Build the decided-owner set from all APPROVED + SKIPPED rows in this cycle
                stmt = sa.select(WorkflowScheduleApproval).where(
                    WorkflowScheduleApproval.approval_cycle_id == approval.approval_cycle_id,
                    WorkflowScheduleApproval.approval_status.in_(["APPROVED", "SKIPPED"])
                )
                res = await execute_statement(db, stmt)
                decided_rows = res.scalars().all()
                
                already_decided_owner_ids = set()
                for r in decided_rows:
                    owner_id = str(r.approver_user_id) if r.approver_user_id else str(r.approval_group_id)
                    if owner_id:
                        already_decided_owner_ids.add(owner_id)

                next_layer = await self.resolve_next_layer(schedule.id, approval.approval_cycle_id, already_decided_owner_ids, actor_uuid, db)
            else:
                next_layer = None
            
            if next_layer:
                # Schedule stays PENDING_APPROVAL
                await self.event_service.publish_event(
                    event_code=WorkflowEventCode.WORKFLOW_SCHEDULE_APPROVED,
                    entity_type="workflow_schedules",
                    entity_id=schedule.id,
                    actor_type="USER",
                    actor_id=actor_uuid,
                    action_type="APPROVE_LAYER",
                    event_summary=f"Layer {approval.approval_layer} approval granted for schedule {schedule.schedule_name}",
                    event_payload={**base_event_payload, "reason": reason},
                    db=db
                )
            else:
                # Chain exhausted - Verify no PENDING row remains anywhere in this cycle
                if approval.approval_cycle_id:
                    pending_check_stmt = sa.select(sa.func.count()).select_from(WorkflowScheduleApproval).where(
                        WorkflowScheduleApproval.approval_cycle_id == approval.approval_cycle_id,
                        WorkflowScheduleApproval.approval_status == 'PENDING'
                    )
                    pending_res = await execute_statement(db, pending_check_stmt)
                    
                    if pending_res.scalar() > 0:
                        raise HTTPException(
                            status_code=400,
                            detail=ResponseHelper.error(
                                message="Cannot activate schedule: PENDING approvals still exist in this cycle.",
                                error_code="VALIDATION_ERROR"
                            ).model_dump()
                        )
                
                # Activate schedule
                schedule = await self.activate_schedule(schedule.id, current_user, db, bypass_abac=True)
                
                await self.event_service.publish_event(
                    event_code=WorkflowEventCode.WORKFLOW_SCHEDULE_APPROVED,
                    entity_type="workflow_schedules",
                    entity_id=schedule.id,
                    actor_type="USER",
                    actor_id=actor_uuid,
                    action_type="APPROVE",
                    event_summary=f"Final approval decision: APPROVED for schedule {schedule.schedule_name}",
                    event_payload={**base_event_payload, "reason": reason},
                    db=db
                )

        elif decision in ["REJECTED", "CHANGES_REQUESTED"]:
            # Transition PENDING_APPROVAL -> DRAFT
            validate_transition(schedule.schedule_status, ScheduleStatus.DRAFT, schedule.approval_required)
            
            before_json = serialize_schedule_history(schedule)
            
            await self.repo.update_status(db, schedule, ScheduleStatus.DRAFT)
            schedule.updated_by = actor_uuid
            
            history_rec = WorkflowScheduleHistory(
                id=uuid4(),
                tenant_id=schedule.tenant_id,
                schedule_id=schedule.id,
                change_type="REJECT" if decision == "REJECTED" else "CHANGES_REQUESTED",
                change_summary=f"Approval decision: {decision}. Reason: {reason}",
                before_json=before_json,
                after_json=serialize_schedule_history(schedule),
                changed_by=actor_uuid,
                created_by=actor_uuid,
                updated_by=actor_uuid
            )
            db.add(history_rec)
            
            approval.approval_status = decision
            approval.decided_by = actor_uuid
            approval.decided_at = datetime.now(timezone.utc)
            approval.decision_reason = reason

            # Transition all sibling PENDING approvals to SUPERSEDED
            if approval.approval_cycle_id:
                sibling_stmt = sa.select(WorkflowScheduleApproval).where(
                    WorkflowScheduleApproval.approval_cycle_id == approval.approval_cycle_id,
                    WorkflowScheduleApproval.id != approval.id,
                    WorkflowScheduleApproval.approval_status == "PENDING"
                )
                sibling_res = await execute_statement(db, sibling_stmt)
                for sib in sibling_res.scalars().all():
                    sib.approval_status = "SUPERSEDED"
                    sib.skip_reason = f"Cycle terminated by decision: {decision}"
                    sib.decided_at = datetime.now(timezone.utc)

            await db_flush(db)
            
            await self.event_service.publish_event(
                event_code=WorkflowEventCode.WORKFLOW_SCHEDULE_UPDATED,
                entity_type="workflow_schedules",
                entity_id=schedule.id,
                actor_type="USER",
                actor_id=actor_uuid,
                action_type="REJECT" if decision == "REJECTED" else "CHANGES_REQUESTED",
                event_summary=f"Approval decision: {decision} for schedule {schedule.schedule_name}",
                event_payload={**base_event_payload, "reason": reason},
                db=db
            )
            
        elif decision == "ESCALATED":
            approval.approval_status = "ESCALATED"
            await db_flush(db)
            
            history_rec = WorkflowScheduleHistory(
                id=uuid4(),
                tenant_id=schedule.tenant_id,
                schedule_id=schedule.id,
                change_type="ESCALATE",
                change_summary=f"Schedule escalated. Reason: {reason}",
                before_json=serialize_schedule_history(schedule),
                after_json=serialize_schedule_history(schedule),
                changed_by=actor_uuid,
                created_by=actor_uuid,
                updated_by=actor_uuid
            )
            db.add(history_rec)
            
            await self.event_service.publish_event(
                event_code=WorkflowEventCode.WORKFLOW_SCHEDULE_UPDATED,
                entity_type="workflow_schedules",
                entity_id=schedule.id,
                actor_type="USER",
                actor_id=actor_uuid,
                action_type="ESCALATE",
                event_summary=f"Approval decision: ESCALATED for schedule {schedule.schedule_name}",
                event_payload={**base_event_payload, "reason": reason},
                db=db
            )

        return schedule

    async def reassign_approver(self, schedule_id: UUID, old_user_id: UUID, new_user_id: UUID, current_user, db) -> WorkflowScheduleApproval:
        actor_uuid = resolve_user_uuid(db, current_user.id)
        role_code = getattr(current_user, "role_code", None)
        is_admin = getattr(current_user, "is_superuser", False) or getattr(current_user, "is_admin", False) or role_code in ["ADMIN", "GOVERNANCE_ADMIN", "SUPER_ADMIN"]

        if not is_admin:
            raise HTTPException(
                status_code=403,
                detail=ResponseHelper.error(message="Only administrators can reassign pending approvals", error_code="FORBIDDEN").model_dump()
            )

        from app.modules.workflow_scheduler.models import WorkflowScheduleApproval
        from app.modules.workflow_notifications.models import WorkflowNotification
        stmt = sa.select(WorkflowScheduleApproval).where(
            WorkflowScheduleApproval.schedule_id == schedule_id,
            WorkflowScheduleApproval.approver_user_id == old_user_id,
            WorkflowScheduleApproval.approval_status == "PENDING"
        ).order_by(WorkflowScheduleApproval.created_at.desc()).limit(1)
        res = await execute_statement(db, stmt)
        approval = res.scalar()

        if not approval:
            raise HTTPException(
                status_code=404,
                detail=ResponseHelper.error(message="No pending approval found for the specified user on this schedule", error_code="NOT_FOUND").model_dump()
            )

        approval.approver_user_id = new_user_id
        approval.updated_by = actor_uuid

        notif = WorkflowNotification(
            id=uuid4(),
            tenant_id=approval.tenant_id,
            recipient_user_id=new_user_id,
            notification_type="APPROVAL_REQUIRED",
            title="Schedule Approval Reassigned to You",
            message=f"A pending schedule approval has been reassigned to you by an administrator.",
            severity="HIGH",
            status="UNREAD",
            created_by=actor_uuid,
            updated_by=actor_uuid
        )
        db.add(notif)
        await db_flush(db)
        return approval

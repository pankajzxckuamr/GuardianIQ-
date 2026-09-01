import asyncio
from datetime import datetime, timezone
import json
import logging
from uuid import UUID, uuid4
import sqlalchemy
from fastapi import APIRouter, Depends, Request, Query, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.shared.db_compat import execute_statement

from app.db.session import get_db
from app.modules.auth.dependencies import get_current_user, require_permission
from app.modules.workflow_scheduler.service import (
    WorkflowScheduleService,
    WorkflowScheduleStateError,
    format_schedule_response,
    format_schedule_list_item
)
from app.modules.workflow_scheduler.schemas import (
    WorkflowScheduleCreate,
    WorkflowScheduleUpdate
)
from app.modules.workflow_execution.service import WorkflowRunService
from app.modules.workflow_scheduler.models import (
    WorkflowScheduleApproval,
    WorkflowScheduleHistory,
    WorkflowScheduleAgentAssignment,
    Phase2WorkflowSchedule,
    ApprovalGroupMember
)
from app.modules.workflow_notifications.models import WorkflowNotification
from app.modules.registry.repositories import resolve_user_uuid
from app.shared.response_utils import ResponseHelper
from app.modules.workflow_execution.models import WorkflowRun
import sqlalchemy as sa
from sqlalchemy.orm import selectinload

router = APIRouter()
schedule_service = WorkflowScheduleService()

def make_envelope(success: bool, data: any, error: str | None, request_id: str) -> dict:
    return {
        "status": "success" if success else "error",
        "success": success,
        "data": data,
        "error": error,
        "request_id": request_id,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

class CronValidationRequest(BaseModel):
    cron_expression: str

@router.post("/api/v1/workflow-scheduler/validate-cron")
def validate_cron(
    request: Request,
    payload: CronValidationRequest,
    current_user = Depends(get_current_user)
):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    from croniter import croniter
    is_valid = croniter.is_valid(payload.cron_expression)
    
    return {
        "status": "success",
        "data": {"valid": is_valid},
        "message": "Valid cron expression" if is_valid else "Invalid cron expression",
        "request_id": request_id
    }

class UniquenessValidationRequest(BaseModel):
    schedule_name: str | None = None
    schedule_code: str | None = None
    schedule_id: UUID | None = None

@router.post("/api/v1/workflow-scheduler/validate-uniqueness")
def validate_uniqueness(
    request: Request,
    payload: UniquenessValidationRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    
    # get tenant_id for the user
    t_id = resolve_user_uuid(db, current_user.id)
    
    errors = {}
    
    if payload.schedule_name:
        stmt = sa.select(Phase2WorkflowSchedule).where(
            Phase2WorkflowSchedule.tenant_id == t_id,
            sa.func.lower(Phase2WorkflowSchedule.schedule_name) == payload.schedule_name.lower()
        )
        if payload.schedule_id:
            stmt = stmt.where(Phase2WorkflowSchedule.id != payload.schedule_id)
            
        existing_name = db.execute(stmt).scalars().first()
        if existing_name and not existing_name.is_deleted:
            errors["schedule_name"] = "A schedule with this name already exists"
            
    if payload.schedule_code:
        stmt = sa.select(Phase2WorkflowSchedule).where(
            Phase2WorkflowSchedule.tenant_id == t_id,
            sa.func.lower(Phase2WorkflowSchedule.schedule_code) == payload.schedule_code.lower()
        )
        if payload.schedule_id:
            stmt = stmt.where(Phase2WorkflowSchedule.id != payload.schedule_id)
            
        existing_code = db.execute(stmt).scalars().first()
        if existing_code and not existing_code.is_deleted:
            errors["schedule_code"] = "A schedule with this code already exists"
            
    return {
        "status": "success",
        "data": {"valid": len(errors) == 0, "errors": errors},
        "request_id": request_id
    }

@router.get("/api/v1/workflow-scheduler/schedules")
async def list_schedules(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100, alias="per_page"),
    sort_by: str | None = None,
    sort_dir: str | None = None,
    status: str | None = None,
    risk_level: str | None = None,
    owner_user_id: UUID | None = None,
    workflow_id: UUID | None = None,
    schedule_type: str | None = None,
    approver_user_id: UUID | None = None,
    my_approvals: bool | None = None,
    db: Session = Depends(get_db),
    current_user = Depends(require_permission("VIEW_WORKFLOW_SCHEDULE"))
):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    try:
        filters = {}
        if sort_by:
            filters["sort_by"] = sort_by
        if sort_dir:
            filters["sort_dir"] = sort_dir
        if status:
            filters["status"] = status
        if risk_level:
            filters["risk_level"] = risk_level
        if owner_user_id:
            filters["owner_user_id"] = owner_user_id
        if workflow_id:
            filters["workflow_id"] = workflow_id
        if schedule_type:
            filters["schedule_type"] = schedule_type

        user_uuid = resolve_user_uuid(db, current_user.id)
        if my_approvals:
            filters["approver_user_id"] = user_uuid
        elif approver_user_id:
            filters["approver_user_id"] = approver_user_id

        items, total = await schedule_service.repo.list_with_filters(db, page, page_size, filters)
        formatted_items = [format_schedule_list_item(item) for item in items]
        
        data = {
            "items": formatted_items,
            "total": total,
            "page": page,
            "page_size": page_size
        }
        return make_envelope(True, data, None, request_id)
    except Exception as e:
        return make_envelope(False, None, str(e), request_id)


@router.get("/api/v1/workflow-scheduler/agent-assignments")
async def list_agent_assignments(
    request: Request,
    agent_id: UUID = Query(None),
    execution_mode: str = Query(None),
    schedule_status: str = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user = Depends(require_permission("VIEW_WORKFLOW_SCHEDULE"))
):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    try:
        query = (
            sa.select(WorkflowScheduleAgentAssignment)
            .where(WorkflowScheduleAgentAssignment.is_deleted == False)
            .options(
                selectinload(WorkflowScheduleAgentAssignment.agent),
                selectinload(WorkflowScheduleAgentAssignment.model),
                selectinload(WorkflowScheduleAgentAssignment.schedule).selectinload(Phase2WorkflowSchedule.workflow),
            )
        )
        if agent_id:
            query = query.where(WorkflowScheduleAgentAssignment.agent_id == agent_id)
        if execution_mode:
            query = query.where(WorkflowScheduleAgentAssignment.execution_mode == execution_mode)
        if schedule_status:
            query = query.join(WorkflowScheduleAgentAssignment.schedule).where(Phase2WorkflowSchedule.schedule_status == schedule_status)

        # Count total
        count_query = sa.select(sa.func.count()).select_from(query.subquery())
        res_count = await execute_statement(db, count_query)
        total = res_count.scalar()

        # Paginate
        query = query.order_by(WorkflowScheduleAgentAssignment.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        res = await execute_statement(db, query)
        items = res.scalars().all()

        data = []
        for a in items:
            sched = a.schedule
            wf = sched.workflow if sched else None
            data.append({
                "id": str(a.id),
                "schedule_id": str(a.schedule_id),
                "schedule_name": sched.schedule_name if sched else None,
                "workflow_id": str(sched.workflow_id) if sched else None,
                "workflow_name": wf.workflow_name if wf else None,
                "agent_id": str(a.agent_id),
                "agent_name": a.agent.agent_name if a.agent else None,
                "model_id": str(a.model_id) if a.model_id else None,
                "execution_mode": a.execution_mode,
                "confidence_threshold": float(a.confidence_threshold) if a.confidence_threshold is not None else None,
                "allowed_tools_json": a.allowed_tools_json or [],
                "allowed_data_sources_json": a.allowed_data_sources_json or [],
                "blocked_operations_json": a.blocked_operations_json or [],
                "approval_required": sched.approval_required if sched else False,
                "status": a.status,
            })

        return make_envelope(True, {"items": data, "total": total, "page": page, "page_size": page_size}, None, request_id)
    except Exception as e:
        return make_envelope(False, None, str(e), request_id)

@router.get("/api/v1/workflow-scheduler/schedules/{schedule_id}/agent-assignments")
async def get_schedule_agent_assignments(
    schedule_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(require_permission("VIEW_WORKFLOW_SCHEDULE"))
):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    try:
        query = (
            sa.select(WorkflowScheduleAgentAssignment)
            .where(
                WorkflowScheduleAgentAssignment.schedule_id == schedule_id,
                WorkflowScheduleAgentAssignment.is_deleted == False
            )
            .options(
                selectinload(WorkflowScheduleAgentAssignment.agent),
                selectinload(WorkflowScheduleAgentAssignment.model)
            )
            .order_by(WorkflowScheduleAgentAssignment.created_at.desc())
        )
        res = await execute_statement(db, query)
        items = res.scalars().all()

        data = []
        for a in items:
            data.append({
                "id": str(a.id),
                "schedule_id": str(a.schedule_id),
                "agent_id": str(a.agent_id),
                "agent_name": a.agent.agent_name if a.agent else None,
                "assignment_role": a.assignment_role,
                "model_id": str(a.model_id) if a.model_id else None,
                "execution_mode": a.execution_mode,
                "confidence_threshold": float(a.confidence_threshold) if a.confidence_threshold is not None else None,
                "allowed_tools_json": a.allowed_tools_json or [],
                "allowed_data_sources_json": a.allowed_data_sources_json or [],
                "blocked_operations_json": a.blocked_operations_json or [],
                "status": a.status,
            })
        return make_envelope(True, {"items": data}, None, request_id)
    except Exception as e:
        return make_envelope(False, None, str(e), request_id)


@router.post("/api/v1/workflow-scheduler/schedules/{schedule_id}/agent-assignments")
async def create_agent_assignment(
    request: Request,
    schedule_id: UUID,
    payload: dict,
    db: Session = Depends(get_db),
    current_user = Depends(require_permission("UPDATE_WORKFLOW_SCHEDULE"))
):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    try:
        schedule = await schedule_service.repo.get_by_id(db, schedule_id)
        if not schedule:
            raise HTTPException(status_code=404, detail=ResponseHelper.error(message="Workflow schedule not found", error_code="NOT_FOUND").model_dump())
            
        actor_uuid = resolve_user_uuid(db, current_user.id)
        
        # Business Validation
        from app.modules.workflow_scheduler.validators import WorkflowScheduleValidationService
        val_res = await WorkflowScheduleValidationService.validate_agent_assignment(payload, schedule_id, db)
        if not val_res["is_valid"]:
            raise HTTPException(400, detail=ResponseHelper.error(message="Assignment validation failed", error_code="VALIDATION_ERROR", details=[{"field": e.field, "message": e.message} for e in val_res["errors"]]).model_dump())
            
        # Boundary Check
        from app.modules.agent_runtime.boundary_checker import BoundaryChecker
        bc = BoundaryChecker()
        bound_res = await bc.validate_assignment_boundaries(payload, UUID(payload["agent_id"]), db)
        if not bound_res.is_valid:
            raise HTTPException(400, detail=ResponseHelper.error(message="Boundary validation failed", error_code="BOUNDARY_ERROR", details=[{"field": "boundary", "message": err} for err in bound_res.errors]).model_dump())
            
        if bound_res.write_capable_tools:
            schedule.approval_required = True
        
        assignment = WorkflowScheduleAgentAssignment(
            id=uuid4(),
            tenant_id=schedule.tenant_id,
            schedule_id=schedule_id,
            agent_id=UUID(payload["agent_id"]),
            assignment_role=payload.get("assignment_role", "PRIMARY"),
            model_id=UUID(payload["model_id"]) if payload.get("model_id") else None,
            execution_mode=payload.get("execution_mode", "READ_ONLY"),
            confidence_threshold=payload.get("confidence_threshold", 80),
            allowed_tools_json=payload.get("allowed_tools_json", []),
            allowed_data_sources_json=payload.get("allowed_data_sources_json", []),
            blocked_operations_json=payload.get("blocked_operations_json", []),
            status=payload.get("status", "ACTIVE"),
            created_by=actor_uuid,
            updated_by=actor_uuid
        )
        db.add(assignment)
        
        # Publish Event
        from app.modules.audit.event_service import GovernanceEventService
        event_service = GovernanceEventService()
        await event_service.publish_event(
            event_code=WorkflowEventCode.AGENT_ASSIGNED_TO_SCHEDULE,
            entity_type="workflow_schedules",
            entity_id=schedule.id,
            actor_type="USER",
            actor_id=actor_uuid,
            action_type="CREATE",
            event_summary=f"Agent {payload['agent_id']} assigned to schedule {schedule_id}",
            event_payload={"agent_id": payload["agent_id"], "assignment_id": str(assignment.id)},
            db=db
        )

        sched_status_str = schedule.schedule_status.value if hasattr(schedule.schedule_status, "value") else str(schedule.schedule_status)
        if sched_status_str == "ACTIVE" and schedule.approval_required and schedule.approval_group_id:
            await schedule_service.repo.update_status(db, schedule, "PENDING_APPROVAL")
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
            
            stmt = sa.select(ApprovalGroupMember.user_id).where(ApprovalGroupMember.approval_group_id == schedule.approval_group_id)
            res = await execute_statement(db, stmt)
            member_ids = [r[0] for r in res.fetchall()]
            for member_id in member_ids:
                notif = WorkflowNotification(
                    id=uuid4(),
                    tenant_id=schedule.tenant_id,
                    recipient_user_id=member_id,
                    notification_type="APPROVAL_REQUIRED",
                    title="Schedule Approval Required",
                    message=f"Approval is required for updated schedule {schedule.schedule_name} ({schedule.schedule_code}).",
                    severity="HIGH",
                    entity_type="workflow_schedules",
                    entity_id=schedule.id,
                    status="UNREAD",
                    created_by=actor_uuid,
                    updated_by=actor_uuid
                )
                db.add(notif)
        
        db.commit()
        response_data = {"id": str(assignment.id)}
        if bound_res.write_capable_tools:
            response_data["warnings"] = bound_res.warnings
            
        return make_envelope(True, response_data, None, request_id)
    except HTTPException as e:
        db.rollback()
        raise e
    except Exception as e:
        db.rollback()
        return make_envelope(False, None, str(e), request_id)


@router.put("/api/v1/workflow-scheduler/schedules/{schedule_id}/agent-assignments/{assignment_id}")
async def update_agent_assignment(
    request: Request,
    schedule_id: UUID,
    assignment_id: UUID,
    payload: dict,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    try:
        schedule = await schedule_service.repo.get_by_id(db, schedule_id)
        if not schedule:
            raise HTTPException(404, detail=ResponseHelper.error(message="Workflow schedule not found", error_code="NOT_FOUND").model_dump())
            
        sched_status_str = schedule.schedule_status.value if hasattr(schedule.schedule_status, "value") else str(schedule.schedule_status)
        if sched_status_str not in ["DRAFT", "PAUSED", "ACTIVE"]:
            raise HTTPException(400, detail=ResponseHelper.error(message="Updates are only allowed in DRAFT, PAUSED, or ACTIVE status", error_code="STATE_ERROR").model_dump())
            
        stmt = sa.select(WorkflowScheduleAgentAssignment).where(
            WorkflowScheduleAgentAssignment.id == assignment_id,
            WorkflowScheduleAgentAssignment.schedule_id == schedule_id,
            WorkflowScheduleAgentAssignment.is_deleted == False
        )
        res = await execute_statement(db, stmt)
        assignment = res.scalar()
        if not assignment:
            raise HTTPException(404, detail=ResponseHelper.error(message="Agent assignment not found", error_code="NOT_FOUND").model_dump())
            
        # Merge payload with assignment for validation
        test_payload = {
            "agent_id": str(payload.get("agent_id", assignment.agent_id)),
            "assignment_role": payload.get("assignment_role", assignment.assignment_role),
            "execution_mode": payload.get("execution_mode", assignment.execution_mode.value if hasattr(assignment.execution_mode, "value") else str(assignment.execution_mode)),
            "allowed_tools_json": payload.get("allowed_tools_json", assignment.allowed_tools_json),
            "allowed_data_sources_json": payload.get("allowed_data_sources_json", assignment.allowed_data_sources_json),
            "blocked_operations_json": payload.get("blocked_operations_json", assignment.blocked_operations_json)
        }
        
        from app.modules.workflow_scheduler.validators import WorkflowScheduleValidationService
        val_res = await WorkflowScheduleValidationService.validate_agent_assignment(test_payload, schedule_id, db, assignment_id)
        if not val_res["is_valid"]:
            raise HTTPException(400, detail=ResponseHelper.error(message="Assignment validation failed", error_code="VALIDATION_ERROR", details=[{"field": e.field, "message": e.message} for e in val_res["errors"]]).model_dump())

        from app.modules.agent_runtime.boundary_checker import BoundaryChecker
        bc = BoundaryChecker()
        bound_res = await bc.validate_assignment_boundaries(test_payload, UUID(test_payload["agent_id"]), db)
        if not bound_res.is_valid:
            raise HTTPException(400, detail=ResponseHelper.error(message="Boundary validation failed", error_code="BOUNDARY_ERROR", details=[{"field": "boundary", "message": err} for err in bound_res.errors]).model_dump())
            
        if bound_res.write_capable_tools:
            schedule.approval_required = True
        
        actor_uuid = resolve_user_uuid(db, current_user.id)
        
        if "agent_id" in payload:
            assignment.agent_id = UUID(payload["agent_id"])
        if "assignment_role" in payload:
            assignment.assignment_role = payload["assignment_role"]
        if "model_id" in payload:
            assignment.model_id = UUID(payload["model_id"]) if payload["model_id"] else None
        if "execution_mode" in payload:
            assignment.execution_mode = payload["execution_mode"]
        if "confidence_threshold" in payload:
            assignment.confidence_threshold = payload["confidence_threshold"]
        if "allowed_tools_json" in payload:
            assignment.allowed_tools_json = payload["allowed_tools_json"]
        if "allowed_data_sources_json" in payload:
            assignment.allowed_data_sources_json = payload["allowed_data_sources_json"]
        if "blocked_operations_json" in payload:
            assignment.blocked_operations_json = payload["blocked_operations_json"]
        if "status" in payload:
            assignment.status = payload["status"]
            
        assignment.updated_by = actor_uuid
        
        # Publish Event
        from app.modules.audit.event_service import GovernanceEventService
        event_service = GovernanceEventService()
        await event_service.publish_event(
            event_code=WorkflowEventCode.AGENT_ASSIGNMENT_UPDATED,
            entity_type="workflow_schedules",
            entity_id=schedule.id,
            actor_type="USER",
            actor_id=actor_uuid,
            action_type="UPDATE",
            event_summary=f"Agent assignment {assignment_id} updated for schedule {schedule_id}",
            event_payload={"assignment_id": str(assignment.id)},
            db=db
        )
        
        if sched_status_str == "ACTIVE" and schedule.approval_required and schedule.approval_group_id:
            await schedule_service.repo.update_status(db, schedule, "PENDING_APPROVAL")
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
            
            stmt = sa.select(ApprovalGroupMember.user_id).where(ApprovalGroupMember.approval_group_id == schedule.approval_group_id)
            res = await execute_statement(db, stmt)
            member_ids = [r[0] for r in res.fetchall()]
            for member_id in member_ids:
                notif = WorkflowNotification(
                    id=uuid4(),
                    tenant_id=schedule.tenant_id,
                    recipient_user_id=member_id,
                    notification_type="APPROVAL_REQUIRED",
                    title="Schedule Approval Required",
                    message=f"Approval is required for updated schedule {schedule.schedule_name} ({schedule.schedule_code}).",
                    severity="HIGH",
                    entity_type="workflow_schedules",
                    entity_id=schedule.id,
                    status="UNREAD",
                    created_by=actor_uuid,
                    updated_by=actor_uuid
                )
                db.add(notif)
                
        db.commit()
        response_data = {"id": str(assignment.id)}
        if bound_res.write_capable_tools:
            response_data["warnings"] = bound_res.warnings
            
        return make_envelope(True, response_data, None, request_id)
    except HTTPException as e:
        db.rollback()
        raise e
    except Exception as e:
        db.rollback()
        return make_envelope(False, None, str(e), request_id)

@router.delete("/api/v1/workflow-scheduler/schedules/{schedule_id}/agent-assignments/{assignment_id}")
async def delete_agent_assignment(
    request: Request,
    schedule_id: UUID,
    assignment_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(require_permission("UPDATE_WORKFLOW_SCHEDULE"))
):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    try:
        schedule = await schedule_service.repo.get_by_id(db, schedule_id)
        if not schedule:
            raise HTTPException(404, detail=ResponseHelper.error(message="Workflow schedule not found", error_code="NOT_FOUND").model_dump())
            
        sched_status_str = schedule.schedule_status.value if hasattr(schedule.schedule_status, "value") else str(schedule.schedule_status)
        if sched_status_str not in ["DRAFT", "PAUSED"]:
            raise HTTPException(400, detail=ResponseHelper.error(message="Deletes are only allowed in DRAFT or PAUSED status", error_code="STATE_ERROR").model_dump())
            
        stmt = sa.select(WorkflowScheduleAgentAssignment).where(
            WorkflowScheduleAgentAssignment.id == assignment_id,
            WorkflowScheduleAgentAssignment.schedule_id == schedule_id,
            WorkflowScheduleAgentAssignment.is_deleted == False
        )
        res = await execute_statement(db, stmt)
        assignment = res.scalar()
        if not assignment:
            raise HTTPException(404, detail=ResponseHelper.error(message="Agent assignment not found", error_code="NOT_FOUND").model_dump())
            
        actor_uuid = resolve_user_uuid(db, current_user.id)
        
        assignment.is_deleted = True
        assignment.updated_by = actor_uuid
        
        # Publish Event
        from app.modules.audit.event_service import GovernanceEventService
        event_service = GovernanceEventService()
        await event_service.publish_event(
            event_code=WorkflowEventCode.AGENT_ASSIGNMENT_REMOVED,
            entity_type="workflow_schedules",
            entity_id=schedule.id,
            actor_type="USER",
            actor_id=actor_uuid,
            action_type="DELETE",
            event_summary=f"Agent assignment {assignment_id} removed from schedule {schedule_id}",
            event_payload={"assignment_id": str(assignment.id)},
            db=db
        )
        
        db.commit()
        return make_envelope(True, {"success": True}, None, request_id)
    except HTTPException as e:
        db.rollback()
        raise e
    except Exception as e:
        db.rollback()
        return make_envelope(False, None, str(e), request_id)


@router.post("/api/v1/workflow-scheduler/schedules")
async def create_schedule(
    request: Request,
    payload: WorkflowScheduleCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_permission("UPDATE_WORKFLOW_SCHEDULE"))
):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    try:
        schedule = await schedule_service.create_schedule(payload, current_user, db)
        db.commit()
        return make_envelope(True, format_schedule_response(schedule), None, request_id)
    except HTTPException as e:
        db.rollback()
        raise e
    except sqlalchemy.exc.IntegrityError as e:
        db.rollback()
        return make_envelope(
            False, None, 
            "A schedule with this name or code already exists for this tenant. Please use a unique name and code.", 
            request_id
        )
    except WorkflowScheduleStateError as e:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=ResponseHelper.error(message=str(e), error_code="INVALID_STATE_TRANSITION").model_dump()
        )
    except Exception as e:
        db.rollback()
        return make_envelope(False, None, str(e), request_id)


@router.get("/api/v1/workflow-scheduler/schedules/{id}")
async def get_schedule(
    request: Request,
    id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(require_permission("VIEW_WORKFLOW_SCHEDULE"))
):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    try:
        schedule = await schedule_service.repo.get_by_id(db, id)
        if not schedule:
            raise HTTPException(status_code=404, detail=ResponseHelper.error(message="Workflow schedule not found", error_code="NOT_FOUND").model_dump())
            
        stmt = (
            sa.select(WorkflowScheduleApproval)
            .where(WorkflowScheduleApproval.schedule_id == id)
            .order_by(WorkflowScheduleApproval.created_at.desc())
            .limit(1)
        )
        app_res = await execute_statement(db, stmt)
        latest_approval = app_res.scalar()
        latest_approval_dict = None
        if latest_approval:
            latest_approval_dict = {
                "id": str(latest_approval.id),
                "approval_status": latest_approval.approval_status,
                "approver_user_id": str(latest_approval.approver_user_id) if latest_approval.approver_user_id else None,
                "decision_reason": latest_approval.decision_reason,
                "decided_at": latest_approval.decided_at.isoformat() if latest_approval.decided_at else None,
                "submitted_by": str(latest_approval.submitted_by) if latest_approval.submitted_by else None,
                "created_at": latest_approval.created_at.isoformat()
            }
            
        stmt_runs = (
            sa.select(WorkflowRun)
            .where(WorkflowRun.schedule_id == id)
            .order_by(WorkflowRun.created_at.desc())
            .limit(5)
        )
        runs_res = await execute_statement(db, stmt_runs)
        runs = runs_res.scalars().all()
        runs_summary = [
            {
                "id": str(r.id),
                "run_code": r.run_code,
                "run_status": r.run_status,
                "trigger_type": r.trigger_type,
                "started_at": r.started_at.isoformat() if r.started_at else None,
                "completed_at": r.completed_at.isoformat() if r.completed_at else None
            }
            for r in runs
        ]
        
        data = {
            "schedule": format_schedule_response(schedule),
            "latest_approval": latest_approval_dict,
            "last_runs_summary": runs_summary
        }
        return make_envelope(True, data, None, request_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        return make_envelope(False, None, str(e), request_id)


@router.put("/api/v1/workflow-scheduler/schedules/{id}")
async def update_schedule(
    request: Request,
    id: UUID,
    payload: WorkflowScheduleUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(require_permission("UPDATE_WORKFLOW_SCHEDULE"))
):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    try:
        schedule = await schedule_service.update_schedule(id, payload, current_user, db)
        db.commit()
        return make_envelope(True, format_schedule_response(schedule), None, request_id)
    except HTTPException as e:
        db.rollback()
        raise e
    except WorkflowScheduleStateError as e:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=ResponseHelper.error(message=str(e), error_code="INVALID_STATE_TRANSITION").model_dump()
        )
    except Exception as e:
        db.rollback()
        return make_envelope(False, None, str(e), request_id)


@router.post("/api/v1/workflow-scheduler/schedules/{id}/submit")
async def submit_for_approval(
    request: Request,
    id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(require_permission("UPDATE_WORKFLOW_SCHEDULE"))
):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    try:
        schedule = await schedule_service.submit_for_approval(id, current_user, db)
        db.commit()
        return make_envelope(True, format_schedule_response(schedule), None, request_id)
    except HTTPException as e:
        db.rollback()
        raise e
    except WorkflowScheduleStateError as e:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=ResponseHelper.error(message=str(e), error_code="INVALID_STATE_TRANSITION").model_dump()
        )
    except Exception as e:
        db.rollback()
        return make_envelope(False, None, str(e), request_id)


class ActivateScheduleRequest(BaseModel):
    approval_reason: Optional[str] = None

class RejectScheduleRequest(BaseModel):
    rejection_reason: str

@router.post("/api/v1/workflow-scheduler/schedules/{id}/activate")
async def activate_schedule(
    request: Request,
    id: UUID,
    payload: Optional[ActivateScheduleRequest] = None,
    db: Session = Depends(get_db),
    current_user = Depends(require_permission("UPDATE_WORKFLOW_SCHEDULE"))
):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    try:
        schedule = await schedule_service.activate_schedule(id, current_user, db)
        db.commit()
        return make_envelope(True, format_schedule_response(schedule), None, request_id)
    except HTTPException as e:
        db.rollback()
        raise e
    except WorkflowScheduleStateError as e:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=ResponseHelper.error(message=str(e), error_code="INVALID_STATE_TRANSITION").model_dump()
        )
    except Exception as e:
        db.rollback()
        return make_envelope(False, None, str(e), request_id)


@router.post("/api/v1/workflow-scheduler/schedules/{id}/reject")
async def reject_schedule(
    request: Request,
    id: UUID,
    payload: RejectScheduleRequest,
    db: Session = Depends(get_db),
    current_user = Depends(require_permission("UPDATE_WORKFLOW_SCHEDULE"))
):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    try:
        schedule = await schedule_service.reject_schedule(id, payload.rejection_reason, current_user, db)
        db.commit()
        return make_envelope(True, format_schedule_response(schedule), None, request_id)
    except HTTPException as e:
        db.rollback()
        raise e
    except WorkflowScheduleStateError as e:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=ResponseHelper.error(message=str(e), error_code="INVALID_STATE_TRANSITION").model_dump()
        )
    except Exception as e:
        db.rollback()
        return make_envelope(False, None, str(e), request_id)


@router.post("/api/v1/workflow-scheduler/schedules/{id}/pause")
async def pause_schedule(
    request: Request,
    id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(require_permission("UPDATE_WORKFLOW_SCHEDULE"))
):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    try:
        schedule = await schedule_service.pause_schedule(id, current_user, db)
        db.commit()
        return make_envelope(True, format_schedule_response(schedule), None, request_id)
    except HTTPException as e:
        db.rollback()
        raise e
    except WorkflowScheduleStateError as e:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=ResponseHelper.error(message=str(e), error_code="INVALID_STATE_TRANSITION").model_dump()
        )
    except Exception as e:
        db.rollback()
        return make_envelope(False, None, str(e), request_id)


@router.post("/api/v1/workflow-scheduler/schedules/{id}/resume")
async def resume_schedule(
    request: Request,
    id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(require_permission("UPDATE_WORKFLOW_SCHEDULE"))
):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    try:
        schedule = await schedule_service.resume_schedule(id, current_user, db)
        db.commit()
        return make_envelope(True, format_schedule_response(schedule), None, request_id)
    except HTTPException as e:
        db.rollback()
        raise e
    except WorkflowScheduleStateError as e:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=ResponseHelper.error(message=str(e), error_code="INVALID_STATE_TRANSITION").model_dump()
        )
    except Exception as e:
        db.rollback()
        return make_envelope(False, None, str(e), request_id)


@router.post("/api/v1/workflow-scheduler/schedules/{id}/retire")
async def retire_schedule(
    request: Request,
    id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(require_permission("UPDATE_WORKFLOW_SCHEDULE"))
):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    try:
        schedule = await schedule_service.retire_schedule(id, current_user, db)
        db.commit()
        return make_envelope(True, format_schedule_response(schedule), None, request_id)
    except HTTPException as e:
        db.rollback()
        raise e
    except WorkflowScheduleStateError as e:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=ResponseHelper.error(message=str(e), error_code="INVALID_STATE_TRANSITION").model_dump()
        )
    except Exception as e:
        db.rollback()
        return make_envelope(False, None, str(e), request_id)


@router.post("/api/v1/workflow-scheduler/schedules/{id}/run-now")
async def run_now(
    request: Request,
    id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(require_permission("UPDATE_WORKFLOW_SCHEDULE"))
):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    try:
        schedule = await schedule_service.repo.get_by_id(db, id)
        if not schedule:
            raise HTTPException(status_code=404, detail=ResponseHelper.error(message="Workflow schedule not found", error_code="NOT_FOUND").model_dump())
        
        run = await WorkflowRunService.create_run(db, id, "MANUAL", current_user)
        db.commit()
        
        run_data = {
            "id": str(run.id),
            "run_code": run.run_code,
            "run_status": run.run_status,
            "trigger_type": run.trigger_type,
            "triggered_by_user_id": str(run.triggered_by_user_id) if run.triggered_by_user_id else None
        }
        return make_envelope(True, run_data, None, request_id)
    except HTTPException as e:
        db.rollback()
        raise e
    except Exception as e:
        db.rollback()
        return make_envelope(False, None, str(e), request_id)


@router.get("/api/v1/workflow-scheduler/schedules/{id}/approvals")
async def get_schedule_approvals(
    request: Request,
    id: UUID,
    include_prior_cycles: bool = Query(False, description="If true, includes history from previous rejected/re-submitted cycles"),
    db: Session = Depends(get_db),
    current_user = Depends(require_permission("VIEW_WORKFLOW_SCHEDULE"))
):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    try:
        stmt = (
            sa.select(WorkflowScheduleApproval)
            .options(selectinload(WorkflowScheduleApproval.department))
            .where(WorkflowScheduleApproval.schedule_id == id)
            .order_by(WorkflowScheduleApproval.created_at.desc())
        )
        res = await execute_statement(db, stmt)
        all_approvals = res.scalars().all()
        
        # Determine the latest cycle_id
        latest_cycle_id = None
        if all_approvals:
            # Assuming the first one is the most recent because of order_by created_at.desc()
            latest_cycle_id = all_approvals[0].approval_cycle_id
            
        approvals = []
        if include_prior_cycles:
            approvals = all_approvals
        else:
            approvals = [app for app in all_approvals if app.approval_cycle_id == latest_cycle_id]
            
        # Re-sort to show the natural progression order
        approvals = sorted(approvals, key=lambda a: (a.created_at or datetime.min, a.approval_layer or 0))

        # Fetch configured layers
        from app.modules.workflow_scheduler.models import ScheduleApprovalLayerSelection
        layer_stmt = (
            sa.select(ScheduleApprovalLayerSelection)
            .options(selectinload(ScheduleApprovalLayerSelection.department))
            .where(ScheduleApprovalLayerSelection.schedule_id == id)
            .order_by(ScheduleApprovalLayerSelection.layer_order)
        )
        layer_res = await execute_statement(db, layer_stmt)
        configured_layers = layer_res.scalars().all()

        # Resolve all user IDs for human-readable names and emails
        user_ids = set()
        for app in approvals:
            if app.approver_user_id:
                user_ids.add(app.approver_user_id)
            if app.decided_by:
                user_ids.add(app.decided_by)

        for l in configured_layers:
            for uid_str in (l.approver_user_ids or []):
                try:
                    user_ids.add(UUID(str(uid_str)))
                except Exception:
                    pass

        user_map = {}
        if user_ids:
            from app.modules.registry.models import GuardianUser
            u_stmt = sa.select(GuardianUser.id, GuardianUser.full_name, GuardianUser.email).where(GuardianUser.id.in_(user_ids))
            u_res = await execute_statement(db, u_stmt)
            for row in u_res.fetchall():
                user_map[row[0]] = {"name": row[1], "email": row[2]}

        data = []
        if configured_layers:
            # Map approvals by approval_layer
            apprs_by_layer = {}
            for app in approvals:
                layer_num = app.approval_layer or 1
                apprs_by_layer.setdefault(layer_num, []).append(app)

            for l in configured_layers:
                layer_apprs = apprs_by_layer.get(l.layer_order, [])
                if layer_apprs:
                    for app in layer_apprs:
                        data.append({
                            "id": str(app.id),
                            "approval_cycle_id": str(app.approval_cycle_id) if app.approval_cycle_id else None,
                            "approval_layer": app.approval_layer,
                            "department_code": app.department.department_code if app.department else (l.department.department_code if l.department else None),
                            "department_name": app.department.department_name if app.department else (l.department.department_name if l.department else None),
                            "approver_user_id": str(app.approver_user_id) if app.approver_user_id else None,
                            "approver_name": user_map.get(app.approver_user_id, {}).get("name") if app.approver_user_id else None,
                            "approver_email": user_map.get(app.approver_user_id, {}).get("email") if app.approver_user_id else None,
                            "approval_group_id": str(app.approval_group_id) if app.approval_group_id else None,
                            "decided_by": str(app.decided_by) if app.decided_by else None,
                            "decided_by_name": user_map.get(app.decided_by, {}).get("name") if app.decided_by else None,
                            "decided_by_email": user_map.get(app.decided_by, {}).get("email") if app.decided_by else None,
                            "decision_reason": app.decision_reason,
                            "approval_status": app.approval_status,
                            "skip_reason": app.skip_reason,
                            "require_all_approvers": l.require_all_approvers,
                            "decided_at": app.decided_at.isoformat() if app.decided_at else None,
                            "created_at": app.created_at.isoformat() if app.created_at else None
                        })
                else:
                    # Upcoming layer not reached yet
                    assigned_names = []
                    assigned_emails = []
                    for uid_str in (l.approver_user_ids or []):
                        try:
                            uid = UUID(str(uid_str))
                            if uid in user_map:
                                assigned_names.append(user_map[uid]["name"])
                                assigned_emails.append(user_map[uid]["email"])
                        except Exception:
                            pass
                    primary_name = ", ".join(assigned_names) if assigned_names else None
                    primary_email = ", ".join(assigned_emails) if assigned_emails else None

                    data.append({
                        "id": str(l.id),
                        "approval_cycle_id": str(latest_cycle_id) if latest_cycle_id else None,
                        "approval_layer": l.layer_order,
                        "department_code": l.department.department_code if l.department else None,
                        "department_name": l.department.department_name if l.department else None,
                        "approver_user_id": (l.approver_user_ids[0] if l.approver_user_ids else None),
                        "approver_name": primary_name,
                        "approver_email": primary_email,
                        "approval_group_id": None,
                        "decided_by": None,
                        "decided_by_name": None,
                        "decided_by_email": None,
                        "decision_reason": None,
                        "approval_status": "WAITING",
                        "skip_reason": None,
                        "require_all_approvers": l.require_all_approvers,
                        "decided_at": None,
                        "created_at": None
                    })
        else:
            data = [
                {
                    "id": str(app.id),
                    "approval_cycle_id": str(app.approval_cycle_id) if app.approval_cycle_id else None,
                    "approval_layer": app.approval_layer,
                    "department_code": app.department.department_code if app.department else None,
                    "department_name": app.department.department_name if app.department else None,
                    "approver_user_id": str(app.approver_user_id) if app.approver_user_id else None,
                    "approver_name": user_map.get(app.approver_user_id, {}).get("name") if app.approver_user_id else None,
                    "approver_email": user_map.get(app.approver_user_id, {}).get("email") if app.approver_user_id else None,
                    "approval_group_id": str(app.approval_group_id) if app.approval_group_id else None,
                    "decided_by": str(app.decided_by) if app.decided_by else None,
                    "decided_by_name": user_map.get(app.decided_by, {}).get("name") if app.decided_by else None,
                    "decided_by_email": user_map.get(app.decided_by, {}).get("email") if app.decided_by else None,
                    "decision_reason": app.decision_reason,
                    "approval_status": app.approval_status,
                    "skip_reason": app.skip_reason,
                    "decided_at": app.decided_at.isoformat() if app.decided_at else None,
                    "created_at": app.created_at.isoformat() if app.created_at else None
                }
                for app in approvals
            ]
        return make_envelope(True, {"items": data}, None, request_id)
    except Exception as e:
        return make_envelope(False, None, str(e), request_id)


@router.get("/api/v1/workflow-scheduler/schedules/{id}/history")
async def get_history(
    request: Request,
    id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(require_permission("VIEW_WORKFLOW_SCHEDULE"))
):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    try:
        stmt = (
            sa.select(WorkflowScheduleHistory)
            .options(sa.orm.selectinload(WorkflowScheduleHistory.changed_by_user))
            .where(WorkflowScheduleHistory.schedule_id == id)
            .order_by(WorkflowScheduleHistory.created_at.desc())
        )
        res = await execute_statement(db, stmt)
        histories = res.scalars().all()
        data = [
            {
                "id": str(h.id),
                "schedule_id": str(h.schedule_id),
                "change_type": h.change_type,
                "change_summary": h.change_summary,
                "before_json": h.before_json,
                "after_json": h.after_json,
                "changed_by": str(h.changed_by) if h.changed_by else None,
                "changed_by_name": h.changed_by_user.full_name if h.changed_by_user else None,
                "created_at": h.created_at.isoformat()
            }
            for h in histories
        ]
        return make_envelope(True, data, None, request_id)
    except Exception as e:
        return make_envelope(False, None, str(e), request_id)

@router.get("/api/v1/schedule-approvals/metrics/today")
async def get_approval_metrics_today(
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(require_permission("VIEW_WORKFLOW_SCHEDULE"))
):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    try:
        from app.modules.workflow_scheduler.models import WorkflowScheduleApproval, Phase2WorkflowSchedule
        from datetime import datetime, timezone
        
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        
        # 1. Total pending schedules
        stmt_pending = sa.select(sa.func.count(Phase2WorkflowSchedule.id)).where(
            Phase2WorkflowSchedule.schedule_status == 'PENDING_APPROVAL',
            Phase2WorkflowSchedule.is_deleted == False
        )
        res_pending = await execute_statement(db, stmt_pending)
        pending_count = res_pending.scalar() or 0
        
        # 2. Decisions made today
        user_uuid = resolve_user_uuid(db, current_user.id)
        role_code = getattr(current_user, "role_code", None)
        is_admin = getattr(current_user, "is_superuser", False) or getattr(current_user, "is_admin", False) or role_code in ["ADMIN", "GOVERNANCE_MANAGER", "SUPER_ADMIN"]

        stmt_decisions = sa.select(
            WorkflowScheduleApproval.approval_status,
            sa.func.count(WorkflowScheduleApproval.id)
        ).where(
            WorkflowScheduleApproval.decided_at >= today
        )
        if not is_admin:
            stmt_decisions = stmt_decisions.where(
                sa.or_(
                    WorkflowScheduleApproval.decided_by == user_uuid,
                    WorkflowScheduleApproval.approver_user_id == user_uuid
                )
            )
        stmt_decisions = stmt_decisions.group_by(WorkflowScheduleApproval.approval_status)
        res = await execute_statement(db, stmt_decisions)
        counts = dict(res.all())

        # Also count currently open/active ESCALATED approvals
        stmt_open_escalated = sa.select(sa.func.count(WorkflowScheduleApproval.id)).where(
            WorkflowScheduleApproval.approval_status == 'ESCALATED'
        )
        res_open_escalated = await execute_statement(db, stmt_open_escalated)
        open_escalated_count = res_open_escalated.scalar() or 0

        # Also count currently open/active CHANGES_REQUESTED approvals
        stmt_changes = sa.select(sa.func.count(WorkflowScheduleApproval.id)).where(
            WorkflowScheduleApproval.approval_status == 'CHANGES_REQUESTED'
        )
        res_changes = await execute_statement(db, stmt_changes)
        changes_count = res_changes.scalar() or 0

        metrics = {
            "PENDING": pending_count,
            "APPROVED": counts.get("APPROVED", 0),
            "REJECTED": counts.get("REJECTED", 0),
            "ESCALATED": max(counts.get("ESCALATED", 0), open_escalated_count),
            "CHANGES_REQUESTED": max(counts.get("CHANGES_REQUESTED", 0), changes_count)
        }
        return make_envelope(True, metrics, None, request_id)
    except Exception as e:
        return make_envelope(False, None, str(e), request_id)

class ApprovalDecisionRequest(BaseModel):
    decision: str
    reason: str

@router.post("/api/v1/workflow-scheduler/schedule-approvals/{approval_id}/decide")
@router.post("/api/v1/schedule-approvals/{approval_id}/decide")
async def decide_schedule_approval(
    request: Request,
    approval_id: UUID,
    payload: ApprovalDecisionRequest,
    db: Session = Depends(get_db),
    current_user = Depends(require_permission("VIEW_WORKFLOW_SCHEDULE"))
):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    try:
        # Fetch the approval record before to know the schedule_id
        from app.modules.workflow_scheduler.models import WorkflowScheduleApproval
        stmt_app = sa.select(WorkflowScheduleApproval).where(WorkflowScheduleApproval.id == approval_id)
        res_app = await execute_statement(db, stmt_app)
        app_record = res_app.scalar()
        if not app_record:
            # Fallback: check if the approval_id matches a schedule_id
            stmt_sched = sa.select(WorkflowScheduleApproval).where(
                WorkflowScheduleApproval.schedule_id == approval_id
            ).order_by(WorkflowScheduleApproval.created_at.desc()).limit(1)
            app_record = (await execute_statement(db, stmt_sched)).scalar()
            
        # Also snapshot how many SKIPPED rows exist before we decide
        skipped_before = 0
        if app_record and app_record.approval_cycle_id:
            stmt_skipped_before = sa.select(sa.func.count(WorkflowScheduleApproval.id)).where(
                WorkflowScheduleApproval.schedule_id == app_record.schedule_id,
                WorkflowScheduleApproval.approval_cycle_id == app_record.approval_cycle_id,
                WorkflowScheduleApproval.approval_status == 'SKIPPED'
            )
            skipped_before = (await execute_statement(db, stmt_skipped_before)).scalar() or 0
        
        schedule = await schedule_service.decide_approval(
            approval_id,
            payload.decision,
            payload.reason,
            current_user,
            db
        )
        db.commit()
        
        layers_remaining = 0
        skipped_after = []
        if app_record and app_record.approval_cycle_id:
            # Calculate pending layers
            stmt_pending = sa.select(sa.func.count(WorkflowScheduleApproval.id)).where(
                WorkflowScheduleApproval.schedule_id == app_record.schedule_id,
                WorkflowScheduleApproval.approval_cycle_id == app_record.approval_cycle_id,
                WorkflowScheduleApproval.approval_status == 'PENDING'
            )
            layers_remaining = (await execute_statement(db, stmt_pending)).scalar() or 0
            
            # Find which departments were auto-skipped in this exact transaction
            from app.modules.department.models import Department
            stmt_skipped_after = sa.select(Department.department_code).join(
                WorkflowScheduleApproval, Department.id == WorkflowScheduleApproval.department_id
            ).where(
                WorkflowScheduleApproval.schedule_id == app_record.schedule_id,
                WorkflowScheduleApproval.approval_cycle_id == app_record.approval_cycle_id,
                WorkflowScheduleApproval.approval_status == 'SKIPPED'
            ).order_by(WorkflowScheduleApproval.created_at.asc()).offset(skipped_before)
            skipped_after = (await execute_statement(db, stmt_skipped_after)).scalars().all()
        
        schedule_status_str = schedule.schedule_status.value if hasattr(schedule.schedule_status, "value") else str(schedule.schedule_status)
        
        return make_envelope(True, {
            "schedule_id": str(schedule.id),
            "schedule_status": schedule_status_str,
            "layers_remaining": layers_remaining,
            "auto_skipped_departments": skipped_after
        }, None, request_id)
    except HTTPException as e:
        db.rollback()
        raise e
    except WorkflowScheduleStateError as e:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=ResponseHelper.error(message=str(e), error_code="INVALID_STATE_TRANSITION").model_dump()
        )
    except Exception as e:
        db.rollback()
        return make_envelope(False, None, str(e), request_id)


class ReassignApproverRequest(BaseModel):
    schedule_id: UUID
    old_user_id: UUID
    new_user_id: UUID

@router.post("/api/v1/schedule-approvals/reassign")
async def reassign_schedule_approver(
    request: Request,
    payload: ReassignApproverRequest,
    db: Session = Depends(get_db),
    current_user = Depends(require_permission("VIEW_WORKFLOW_SCHEDULE"))
):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    try:
        approval = await schedule_service.reassign_approver(
            payload.schedule_id,
            payload.old_user_id,
            payload.new_user_id,
            current_user,
            db
        )
        db.commit()
        return make_envelope(True, {"message": "Approver reassigned successfully", "approval_id": str(approval.id)}, None, request_id)
    except HTTPException as e:
        db.rollback()
        raise e
    except Exception as e:
        db.rollback()
        return make_envelope(False, None, str(e), request_id)


@router.get("/api/v1/departments/{department_id}/users")
async def list_department_users(
    department_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(require_permission("VIEW_WORKFLOW_SCHEDULE"))
):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    try:
        from app.modules.department.models import Department, DepartmentOwnerAssignment
        from app.modules.auth.models import User
        from app.shared.db_compat import db_get
        
        dept = None
        try:
            dept_uuid = UUID(department_id)
            dept = await db_get(db, Department, dept_uuid)
        except ValueError:
            dept_stmt = sa.select(Department).where(Department.department_code == department_id)
            res_dept = await execute_statement(db, dept_stmt)
            dept = res_dept.scalar()
            
        if not dept:
            dept_stmt = sa.select(Department).where(Department.department_code == department_id)
            res_dept = await execute_statement(db, dept_stmt)
            dept = res_dept.scalar()

        if not dept:
            return make_envelope(True, [], None, request_id)

        # 1. Users directly assigned to department
        user_stmt = sa.select(User).where(User.department_id == dept.id)
        users_direct = (await execute_statement(db, user_stmt)).scalars().all()
        
        # 2. Users assigned via department_owner_assignments
        owner_stmt = sa.select(User).join(DepartmentOwnerAssignment, DepartmentOwnerAssignment.owner_user_id == User.id).where(DepartmentOwnerAssignment.department_id == dept.id)
        users_assigned = (await execute_statement(db, owner_stmt)).scalars().all()
        
        all_users_dict = {u.id: u for u in (list(users_direct) + list(users_assigned))}
        
        data = [
            {
                "id": str(u.id),
                "name": u.name or u.email,
                "email": u.email,
                "role_name": u.user_roles[0].role.role_name if hasattr(u, "user_roles") and u.user_roles and u.user_roles[0].role else None
            }
            for u in all_users_dict.values()
        ]
        return make_envelope(True, data, None, request_id)
    except Exception as e:
        return make_envelope(False, None, str(e), request_id)


@router.get("/api/v1/approval-groups")
async def list_approval_groups(
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(require_permission("VIEW_WORKFLOW_SCHEDULE"))
):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    try:
        from app.modules.workflow_scheduler.models import ApprovalGroup
        stmt = sa.select(ApprovalGroup).order_by(ApprovalGroup.name.asc())
        res = await execute_statement(db, stmt)
        groups = res.scalars().all()
        
        data = [
            {
                "id": str(g.id),
                "name": g.name,
                "tenant_id": str(g.tenant_id) if g.tenant_id else None,
                "created_at": g.created_at.isoformat() if g.created_at else None,
            }
            for g in groups
        ]
        return make_envelope(True, data, None, request_id)
    except Exception as e:
        return make_envelope(False, None, str(e), request_id)


@router.get("/api/v1/audit/events")
async def get_audit_events_timeline(
    request: Request,
    entity_type: str = Query(...),
    entity_id: UUID = Query(...),
    db: Session = Depends(get_db),
    current_user = Depends(require_permission("VIEW_WORKFLOW_SCHEDULE"))
):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    try:
        # Map frontend entity types to database entity types
        entity_type_map = {
            "WORKFLOW_SCHEDULE": "workflow_schedules",
            "WORKFLOW_RUN": "workflow_runs",
            "workflow_schedule": "workflow_schedules",
            "workflow_run": "workflow_runs"
        }
        normalized_entity_type = entity_type_map.get(entity_type, entity_type)

        from app.modules.audit.event_service import GovernanceEventService
        service = GovernanceEventService()
        events = await service.get_timeline(normalized_entity_type, entity_id, db)
        
        # Resolve actor usernames from User IDs
        actor_ids = {ev.actor_user_id for ev in events if ev.actor_user_id is not None}
        actor_map = {}
        if actor_ids:
            from app.modules.auth.models import User
            user_stmt = sa.select(User.id, User.name, User.email).where(User.id.in_(list(actor_ids)))
            user_res = await execute_statement(db, user_stmt)
            for row in user_res.fetchall():
                actor_map[row[0]] = row[1] or row[2]

        data = [
            {
                "id": str(ev.id),
                "action_type": ev.action,
                "event_summary": ev.event_metadata.get("event_summary") if ev.event_metadata else f"Action {ev.action} on {ev.entity_type}",
                "actor_name": actor_map.get(ev.actor_user_id, "System"),
                "created_at": ev.created_at.isoformat() if ev.created_at else None
            }
            for ev in events
        ]
        return make_envelope(True, {"items": data, "total": len(data)}, None, request_id)
    except Exception as e:
        return make_envelope(False, None, str(e), request_id)



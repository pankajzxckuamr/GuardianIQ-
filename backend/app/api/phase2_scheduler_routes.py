from datetime import datetime, timezone
from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, Request, Query, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.shared.db_compat import execute_statement

from app.db.session import get_db
from app.modules.auth.dependencies import get_current_user
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


@router.get("/api/v1/workflow-scheduler/schedules")
async def list_schedules(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100, alias="per_page"),
    status: str | None = None,
    risk_level: str | None = None,
    owner_user_id: UUID | None = None,
    workflow_id: UUID | None = None,
    schedule_type: str | None = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    try:
        filters = {}
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
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
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
            .order_by(WorkflowScheduleAgentAssignment.created_at.desc())
        )
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

        return make_envelope(True, {"items": data, "total": len(data)}, None, request_id)
    except Exception as e:
        return make_envelope(False, None, str(e), request_id)


@router.post("/api/v1/workflow-scheduler/schedules/{schedule_id}/agent-assignments")
async def create_agent_assignment(
    request: Request,
    schedule_id: UUID,
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
            
        actor_uuid = resolve_user_uuid(db, current_user.id)
        
        assignment = WorkflowScheduleAgentAssignment(
            id=uuid4(),
            tenant_id=schedule.tenant_id,
            schedule_id=schedule_id,
            agent_id=UUID(payload["agent_id"]),
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
        return make_envelope(True, {"id": str(assignment.id)}, None, request_id)
    except HTTPException as e:
        db.rollback()
        return make_envelope(False, None, str(e.detail), request_id)
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
            
        actor_uuid = resolve_user_uuid(db, current_user.id)
        
        if "agent_id" in payload:
            assignment.agent_id = UUID(payload["agent_id"])
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
        return make_envelope(True, {"id": str(assignment.id)}, None, request_id)
    except HTTPException as e:
        db.rollback()
        return make_envelope(False, None, str(e.detail), request_id)
    except Exception as e:
        db.rollback()
        return make_envelope(False, None, str(e), request_id)


@router.post("/api/v1/workflow-scheduler/schedules")
async def create_schedule(
    request: Request,
    payload: WorkflowScheduleCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    try:
        schedule = await schedule_service.create_schedule(payload, current_user, db)
        db.commit()
        return make_envelope(True, format_schedule_response(schedule), None, request_id)
    except HTTPException as e:
        db.rollback()
        return make_envelope(False, None, str(e.detail), request_id)
    except WorkflowScheduleStateError as e:
        db.rollback()
        return make_envelope(False, None, str(e), request_id)
    except Exception as e:
        db.rollback()
        return make_envelope(False, None, str(e), request_id)


@router.get("/api/v1/workflow-scheduler/schedules/{id}")
async def get_schedule(
    request: Request,
    id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    try:
        schedule = await schedule_service.repo.get_by_id(db, id)
        if not schedule:
            raise HTTPException(status_code=404, detail="Workflow schedule not found")
            
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
        return make_envelope(False, None, str(e.detail), request_id)
    except Exception as e:
        return make_envelope(False, None, str(e), request_id)


@router.put("/api/v1/workflow-scheduler/schedules/{id}")
async def update_schedule(
    request: Request,
    id: UUID,
    payload: WorkflowScheduleUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    try:
        schedule = await schedule_service.update_schedule(id, payload, current_user, db)
        db.commit()
        return make_envelope(True, format_schedule_response(schedule), None, request_id)
    except HTTPException as e:
        db.rollback()
        return make_envelope(False, None, str(e.detail), request_id)
    except WorkflowScheduleStateError as e:
        db.rollback()
        return make_envelope(False, None, str(e), request_id)
    except Exception as e:
        db.rollback()
        return make_envelope(False, None, str(e), request_id)


@router.post("/api/v1/workflow-scheduler/schedules/{id}/submit")
async def submit_for_approval(
    request: Request,
    id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    try:
        schedule = await schedule_service.submit_for_approval(id, current_user, db)
        db.commit()
        return make_envelope(True, format_schedule_response(schedule), None, request_id)
    except HTTPException as e:
        db.rollback()
        return make_envelope(False, None, str(e.detail), request_id)
    except WorkflowScheduleStateError as e:
        db.rollback()
        return make_envelope(False, None, str(e), request_id)
    except Exception as e:
        db.rollback()
        return make_envelope(False, None, str(e), request_id)


@router.post("/api/v1/workflow-scheduler/schedules/{id}/activate")
async def activate_schedule(
    request: Request,
    id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    try:
        schedule = await schedule_service.activate_schedule(id, current_user, db)
        db.commit()
        return make_envelope(True, format_schedule_response(schedule), None, request_id)
    except HTTPException as e:
        db.rollback()
        return make_envelope(False, None, str(e.detail), request_id)
    except WorkflowScheduleStateError as e:
        db.rollback()
        return make_envelope(False, None, str(e), request_id)
    except Exception as e:
        db.rollback()
        return make_envelope(False, None, str(e), request_id)


@router.post("/api/v1/workflow-scheduler/schedules/{id}/pause")
async def pause_schedule(
    request: Request,
    id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    try:
        schedule = await schedule_service.pause_schedule(id, current_user, db)
        db.commit()
        return make_envelope(True, format_schedule_response(schedule), None, request_id)
    except HTTPException as e:
        db.rollback()
        return make_envelope(False, None, str(e.detail), request_id)
    except WorkflowScheduleStateError as e:
        db.rollback()
        return make_envelope(False, None, str(e), request_id)
    except Exception as e:
        db.rollback()
        return make_envelope(False, None, str(e), request_id)


@router.post("/api/v1/workflow-scheduler/schedules/{id}/resume")
async def resume_schedule(
    request: Request,
    id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    try:
        schedule = await schedule_service.resume_schedule(id, current_user, db)
        db.commit()
        return make_envelope(True, format_schedule_response(schedule), None, request_id)
    except HTTPException as e:
        db.rollback()
        return make_envelope(False, None, str(e.detail), request_id)
    except WorkflowScheduleStateError as e:
        db.rollback()
        return make_envelope(False, None, str(e), request_id)
    except Exception as e:
        db.rollback()
        return make_envelope(False, None, str(e), request_id)


@router.post("/api/v1/workflow-scheduler/schedules/{id}/retire")
async def retire_schedule(
    request: Request,
    id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    try:
        schedule = await schedule_service.retire_schedule(id, current_user, db)
        db.commit()
        return make_envelope(True, format_schedule_response(schedule), None, request_id)
    except HTTPException as e:
        db.rollback()
        return make_envelope(False, None, str(e.detail), request_id)
    except WorkflowScheduleStateError as e:
        db.rollback()
        return make_envelope(False, None, str(e), request_id)
    except Exception as e:
        db.rollback()
        return make_envelope(False, None, str(e), request_id)


@router.post("/api/v1/workflow-scheduler/schedules/{id}/run-now")
async def run_now(
    request: Request,
    id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    try:
        # Verify schedule exists
        schedule = await schedule_service.repo.get_by_id(db, id)
        if not schedule:
            raise HTTPException(status_code=404, detail="Workflow schedule not found")
        
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
        return make_envelope(False, None, str(e.detail), request_id)
    except Exception as e:
        db.rollback()
        return make_envelope(False, None, str(e), request_id)


@router.get("/api/v1/workflow-scheduler/schedules/{id}/approvals")
async def get_approvals(
    request: Request,
    id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    try:
        stmt = sa.select(WorkflowScheduleApproval).where(WorkflowScheduleApproval.schedule_id == id).order_by(WorkflowScheduleApproval.created_at.desc())
        res = await execute_statement(db, stmt)
        approvals = res.scalars().all()
        data = [
            {
                "id": str(app.id),
                "schedule_id": str(app.schedule_id),
                "approval_type": app.approval_type,
                "approval_status": app.approval_status,
                "decision_reason": app.decision_reason,
                "decided_at": app.decided_at.isoformat() if app.decided_at else None,
                "submitted_by": str(app.submitted_by) if app.submitted_by else None,
                "approver_user_id": str(app.approver_user_id) if app.approver_user_id else None,
                "created_at": app.created_at.isoformat()
            }
            for app in approvals
        ]
        return make_envelope(True, data, None, request_id)
    except Exception as e:
        return make_envelope(False, None, str(e), request_id)


@router.get("/api/v1/workflow-scheduler/schedules/{id}/history")
async def get_history(
    request: Request,
    id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    try:
        stmt = sa.select(WorkflowScheduleHistory).where(WorkflowScheduleHistory.schedule_id == id).order_by(WorkflowScheduleHistory.created_at.desc())
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
                "created_at": h.created_at.isoformat()
            }
            for h in histories
        ]
        return make_envelope(True, data, None, request_id)
    except Exception as e:
        return make_envelope(False, None, str(e), request_id)


class ApprovalDecisionRequest(BaseModel):
    decision: str
    reason: str

@router.post("/api/v1/schedule-approvals/{approval_id}/decide")
async def decide_approval(
    request: Request,
    approval_id: UUID,
    payload: ApprovalDecisionRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    try:
        schedule = await schedule_service.decide_approval(
            approval_id,
            payload.decision,
            payload.reason,
            current_user,
            db
        )
        db.commit()
        return make_envelope(True, format_schedule_response(schedule), None, request_id)
    except HTTPException as e:
        db.rollback()
        return make_envelope(False, None, str(e.detail), request_id)
    except WorkflowScheduleStateError as e:
        db.rollback()
        return make_envelope(False, None, str(e), request_id)
    except Exception as e:
        db.rollback()
        return make_envelope(False, None, str(e), request_id)


@router.get("/api/v1/approval-groups")
async def list_approval_groups(
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
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
    current_user = Depends(get_current_user)
):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    try:
        from app.modules.audit.event_service import GovernanceEventService
        service = GovernanceEventService()
        events = await service.get_timeline(entity_type, entity_id, db)
        
        data = [
            {
                "id": str(ev.id),
                "action_type": ev.action,
                "event_summary": ev.event_metadata.get("event_summary") if ev.event_metadata else f"Action {ev.action} on {ev.entity_type}",
                "created_at": ev.created_at.isoformat() if ev.created_at else None
            }
            for ev in events
        ]
        return make_envelope(True, {"items": data, "total": len(data)}, None, request_id)
    except Exception as e:
        return make_envelope(False, None, str(e), request_id)



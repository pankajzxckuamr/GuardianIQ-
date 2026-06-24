from datetime import datetime, timezone
from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, Request, Query, HTTPException
from sqlalchemy.orm import Session
import sqlalchemy as sa
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.workflow_execution.service import WorkflowRunService, WorkflowRunStateError
from app.modules.workflow_execution.models import WorkflowRun, WorkflowRunStep, WorkflowRunOutput
from app.modules.workflow_scheduler.models import Phase2WorkflowSchedule
from app.modules.registry.repositories import resolve_user_uuid
from app.modules.authorization.decision_service import AuthorizationDecisionService
from app.modules.authorization.schemas import AuthorizationRequest
from app.shared.db_compat import execute_statement, db_get

router = APIRouter()
run_service = WorkflowRunService()

def make_envelope(success: bool, data: any, error: str | None, request_id: str) -> dict:
    return {
        "status": "success" if success else "error",
        "success": success,
        "data": data,
        "error": error,
        "request_id": request_id,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.get("/api/v1/workflow-runs")
async def list_runs(
    request: Request,
    run_status: str | None = None,
    risk_level: str | None = None,
    trigger_type: str | None = None,
    schedule_id: UUID | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100, alias="per_page"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    try:
        query = select(WorkflowRun).where(WorkflowRun.is_deleted == False)
        
        if run_status:
            if "," in run_status:
                status_list = [s.strip() for s in run_status.split(",")]
                query = query.where(WorkflowRun.run_status.in_(status_list))
            else:
                query = query.where(WorkflowRun.run_status == run_status)
        if risk_level:
            query = query.where(WorkflowRun.risk_level == risk_level)
        if trigger_type:
            query = query.where(WorkflowRun.trigger_type == trigger_type)
        if schedule_id:
            query = query.where(WorkflowRun.schedule_id == schedule_id)
        if start_date:
            query = query.where(WorkflowRun.created_at >= start_date)
        if end_date:
            query = query.where(WorkflowRun.created_at <= end_date)
            
        # Count total
        count_stmt = select(sa.func.count()).select_from(query.subquery())
        count_res = await execute_statement(db, count_stmt)
        total = count_res.scalar() or 0
        
        # Paginate
        offset = (page - 1) * page_size
        query = query.order_by(WorkflowRun.created_at.desc()).offset(offset).limit(page_size)
        query = query.options(
            selectinload(WorkflowRun.schedule),
            selectinload(WorkflowRun.workflow),
            selectinload(WorkflowRun.triggered_by_user)
        )
        res = await execute_statement(db, query)
        items = res.scalars().all()
        
        formatted_items = []
        for r in items:
            schedule_code = r.schedule.schedule_code if r.schedule else "Unknown"
            workflow_name = r.workflow.workflow_name if r.workflow else "Unknown"
            triggered_by_name = r.triggered_by_user.full_name if r.triggered_by_user else "System"
            
            formatted_items.append({
                "id": str(r.id),
                "run_code": r.run_code,
                "schedule_code": schedule_code,
                "workflow_name": workflow_name,
                "trigger_type": r.trigger_type,
                "run_status": r.run_status,
                "started_at": r.started_at.isoformat() if r.started_at else None,
                "completed_at": r.completed_at.isoformat() if r.completed_at else None,
                "duration_ms": r.duration_ms,
                "risk_level": r.risk_level,
                "triggered_by_name": triggered_by_name
            })
            
        data = {
            "items": formatted_items,
            "total": total,
            "page": page,
            "page_size": page_size
        }
        return make_envelope(True, data, None, request_id)
    except Exception as e:
        return make_envelope(False, None, str(e), request_id)


@router.get("/api/v1/workflow-runs/{run_id}")
async def get_run_detail(
    request: Request,
    run_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    try:
        stmt = (
            select(WorkflowRun)
            .options(
                selectinload(WorkflowRun.steps),
                selectinload(WorkflowRun.outputs),
                selectinload(WorkflowRun.failures),
                selectinload(WorkflowRun.schedule),
                selectinload(WorkflowRun.workflow),
                selectinload(WorkflowRun.triggered_by_user)
            )
            .where(WorkflowRun.id == run_id, WorkflowRun.is_deleted == False)
        )
        res = await execute_statement(db, stmt)
        run = res.scalar()
        if not run:
            raise HTTPException(status_code=404, detail="Workflow run not found")
            
        formatted_steps = [
            {
                "id": str(s.id),
                "run_id": str(s.run_id),
                "step_code": s.step_code,
                "step_order": s.step_order,
                "step_type": s.step_type,
                "step_status": s.step_status,
                "started_at": s.started_at.isoformat() if s.started_at else None,
                "completed_at": s.completed_at.isoformat() if s.completed_at else None,
                "input_json": s.input_json,
                "output_json": s.output_json,
                "error_message": s.error_message,
                "version_no": s.version_no,
                "is_deleted": s.is_deleted,
                "metadata_json": s.metadata_json,
                "created_at": s.created_at.isoformat(),
                "updated_at": s.updated_at.isoformat(),
                "created_by": str(s.created_by) if s.created_by else None,
                "updated_by": str(s.updated_by) if s.updated_by else None
            }
            for s in run.steps
        ]
        
        # Sort steps by step_order
        formatted_steps.sort(key=lambda x: x["step_order"])
        
        # Determine permission for output masking
        actor_uuid = resolve_user_uuid(db, current_user.id)
        auth_service = AuthorizationDecisionService()
        auth_req = AuthorizationRequest(
            subject_user_id=actor_uuid,
            subject_type="USER",
            object_type="workflow_run_outputs",
            object_id=run_id,
            action="VIEW_WORKFLOW_RUN_OUTPUT"
        )
        auth_res = await auth_service.evaluate(auth_req, db, persist=False)
        has_output_perm = auth_res.allowed
        
        formatted_outputs = [
            {
                "id": str(o.id),
                "run_id": str(o.run_id),
                "output_type": o.output_type,
                "severity": o.severity,
                "risk_score": float(o.risk_score) if o.risk_score is not None else None,
                "findings_json": o.findings_json,
                "recommendations_json": o.recommendations_json,
                "evidence_json": o.evidence_json,
                "raw_output_json": o.raw_output_json if has_output_perm else None,
                "parse_status": o.parse_status,
                "version_no": o.version_no,
                "is_deleted": o.is_deleted,
                "metadata_json": o.metadata_json,
                "created_at": o.created_at.isoformat(),
                "updated_at": o.updated_at.isoformat(),
                "created_by": str(o.created_by) if o.created_by else None,
                "updated_by": str(o.updated_by) if o.updated_by else None
            }
            for o in run.outputs
        ]
        
        formatted_failures = [
            {
                "id": str(f.id),
                "run_id": str(f.run_id),
                "failure_type": f.failure_type,
                "failure_code": f.failure_code,
                "failure_message": f.failure_message,
                "failed_step_id": str(f.failed_step_id) if f.failed_step_id else None,
                "retry_count": f.retry_count,
                "max_retries": f.max_retries,
                "escalation_required": f.escalation_required,
                "escalation_sent_at": f.escalation_sent_at.isoformat() if f.escalation_sent_at else None,
                "version_no": f.version_no,
                "is_deleted": f.is_deleted,
                "metadata_json": f.metadata_json,
                "created_at": f.created_at.isoformat(),
                "updated_at": f.updated_at.isoformat(),
                "created_by": str(f.created_by) if f.created_by else None,
                "updated_by": str(f.updated_by) if f.updated_by else None
            }
            for f in run.failures
        ]
        
        schedule_name = run.schedule.schedule_name if run.schedule else "Unknown"
        workflow_name = run.workflow.workflow_name if run.workflow else "Unknown"
        triggered_by_name = run.triggered_by_user.full_name if run.triggered_by_user else "System"

        data = {
            "id": str(run.id),
            "schedule_id": str(run.schedule_id),
            "workflow_id": str(run.workflow_id),
            "schedule_name": schedule_name,
            "workflow_name": workflow_name,
            "run_code": run.run_code,
            "trigger_type": run.trigger_type,
            "triggered_by_user_id": str(run.triggered_by_user_id) if run.triggered_by_user_id else None,
            "triggered_by_actor_type": run.triggered_by_actor_type,
            "triggered_by_name": triggered_by_name,
            "run_status": run.run_status,
            "started_at": run.started_at.isoformat() if run.started_at else None,
            "completed_at": run.completed_at.isoformat() if run.completed_at else None,
            "duration_ms": run.duration_ms,
            "risk_level": run.risk_level,
            "summary": run.summary,
            "context_json": run.context_json,
            "result_json": run.result_json,
            "version_no": run.version_no,
            "is_deleted": run.is_deleted,
            "metadata_json": run.metadata_json,
            "created_at": run.created_at.isoformat(),
            "updated_at": run.updated_at.isoformat(),
            "created_by": str(run.created_by) if run.created_by else None,
            "updated_by": str(run.updated_by) if run.updated_by else None,
            "steps": formatted_steps,
            "outputs": formatted_outputs,
            "failures": formatted_failures
        }
        return make_envelope(True, data, None, request_id)
    except HTTPException as e:
        return make_envelope(False, None, str(e.detail), request_id)
    except Exception as e:
        return make_envelope(False, None, str(e), request_id)


@router.get("/api/v1/workflow-runs/{run_id}/steps")
async def get_run_steps(
    request: Request,
    run_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    try:
        stmt = select(WorkflowRunStep).where(
            WorkflowRunStep.run_id == run_id,
            WorkflowRunStep.is_deleted == False
        ).order_by(WorkflowRunStep.step_order.asc())
        
        res = await execute_statement(db, stmt)
        steps = res.scalars().all()
        
        data = [
            {
                "id": str(s.id),
                "run_id": str(s.run_id),
                "step_code": s.step_code,
                "step_order": s.step_order,
                "step_type": s.step_type,
                "step_status": s.step_status,
                "started_at": s.started_at.isoformat() if s.started_at else None,
                "completed_at": s.completed_at.isoformat() if s.completed_at else None,
                "input_json": s.input_json,
                "output_json": s.output_json,
                "error_message": s.error_message,
                "version_no": s.version_no,
                "is_deleted": s.is_deleted,
                "created_at": s.created_at.isoformat(),
                "updated_at": s.updated_at.isoformat()
            }
            for s in steps
        ]
        return make_envelope(True, data, None, request_id)
    except Exception as e:
        return make_envelope(False, None, str(e), request_id)


@router.get("/api/v1/workflow-runs/{run_id}/outputs")
async def get_run_outputs(
    request: Request,
    run_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    try:
        # Check permissions for VIEW_WORKFLOW_RUN_OUTPUT
        actor_uuid = resolve_user_uuid(db, current_user.id)
        auth_service = AuthorizationDecisionService()
        auth_req = AuthorizationRequest(
            subject_user_id=actor_uuid,
            subject_type="USER",
            object_type="workflow_run_outputs",
            object_id=run_id,
            action="VIEW_WORKFLOW_RUN_OUTPUT"
        )
        auth_res = await auth_service.evaluate(auth_req, db, persist=False)
        has_output_perm = auth_res.allowed
        
        stmt = select(WorkflowRunOutput).where(
            WorkflowRunOutput.run_id == run_id,
            WorkflowRunOutput.is_deleted == False
        )
        res = await execute_statement(db, stmt)
        outputs = res.scalars().all()
        
        data = [
            {
                "id": str(o.id),
                "run_id": str(o.run_id),
                "output_type": o.output_type,
                "severity": o.severity,
                "risk_score": float(o.risk_score) if o.risk_score is not None else None,
                "findings_json": o.findings_json,
                "recommendations_json": o.recommendations_json,
                "evidence_json": o.evidence_json,
                "raw_output_json": o.raw_output_json if has_output_perm else None,
                "parse_status": o.parse_status,
                "version_no": o.version_no,
                "is_deleted": o.is_deleted,
                "created_at": o.created_at.isoformat(),
                "updated_at": o.updated_at.isoformat()
            }
            for o in outputs
        ]
        return make_envelope(True, data, None, request_id)
    except Exception as e:
        return make_envelope(False, None, str(e), request_id)


@router.post("/api/v1/workflow-runs/{run_id}/cancel")
async def cancel_run(
    request: Request,
    run_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    try:
        run = await run_service.cancel_run(run_id, current_user, db)
        db.commit()
        return make_envelope(True, {"id": str(run.id), "run_status": run.run_status}, None, request_id)
    except HTTPException as e:
        db.rollback()
        return make_envelope(False, None, str(e.detail), request_id)
    except WorkflowRunStateError as e:
        db.rollback()
        return make_envelope(False, None, str(e), request_id)
    except Exception as e:
        db.rollback()
        return make_envelope(False, None, str(e), request_id)

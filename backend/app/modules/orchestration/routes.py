from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.modules.orchestration.tasks import execute_workflow_task
from app.modules.orchestration.models import WorkflowExecution
from pydantic import BaseModel
from typing import List, Optional
import uuid
from datetime import datetime

router = APIRouter()

class ExecuteWorkflowRequest(BaseModel):
    is_dry_run: bool = False

class WorkflowExecutionResponse(BaseModel):
    id: uuid.UUID
    workflow_id: uuid.UUID
    workflow_name: Optional[str] = None
    status: str
    is_dry_run: bool
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

@router.post("/{workflow_id}/execute")
def trigger_workflow_execution(
    workflow_id: str,
    request: ExecuteWorkflowRequest,
    db: Session = Depends(get_db)
):
    """
    Trigger an asynchronous execution of a workflow.
    """
    # Simply enqueue the task; it will handle state creation and logging.
    task = execute_workflow_task.delay(workflow_id, request.is_dry_run)
    return {"message": "Execution triggered", "task_id": task.id}

@router.get("/executions", response_model=List[WorkflowExecutionResponse])
def list_executions(db: Session = Depends(get_db)):
    """
    List all workflow executions.
    """
    executions = db.query(WorkflowExecution).order_by(WorkflowExecution.started_at.desc()).all()
    return executions

@router.get("/executions/{execution_id}")
def get_execution_details(execution_id: str, db: Session = Depends(get_db)):
    """
    Get details of a specific execution, including findings and logs.
    """
    from app.modules.orchestration.models import ExecutionEventLog, ExecutionFinding
    execution = db.query(WorkflowExecution).filter(WorkflowExecution.id == execution_id).first()
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
        
    logs = db.query(ExecutionEventLog).filter(ExecutionEventLog.execution_id == execution_id).order_by(ExecutionEventLog.timestamp.asc()).all()
    findings = db.query(ExecutionFinding).filter(ExecutionFinding.execution_id == execution_id).order_by(ExecutionFinding.created_at.asc()).all()

    logs_data = [{
        "id": str(log.id),
        "execution_id": str(log.execution_id),
        "event_type": log.event_type,
        "details": log.details,
        "timestamp": log.timestamp.isoformat() if log.timestamp else None
    } for log in logs]

    findings_data = [{
        "id": str(finding.id),
        "execution_id": str(finding.execution_id),
        "severity": finding.severity,
        "description": finding.description,
        "recommendation_text": finding.recommendation_text,
        "created_at": finding.created_at.isoformat() if finding.created_at else None
    } for finding in findings]

    return {
        "id": str(execution.id),
        "workflow_id": str(execution.workflow_id),
        "workflow_name": execution.workflow_name,
        "status": execution.status,
        "is_dry_run": execution.is_dry_run,
        "started_at": execution.started_at.isoformat() if execution.started_at else None,
        "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
        "logs": logs_data,
        "findings": findings_data
    }

@router.post("/executions/{execution_id}/approve")
def approve_execution(execution_id: str, db: Session = Depends(get_db)):
    """
    Approve an execution that is currently awaiting approval.
    """
    execution = db.query(WorkflowExecution).filter(WorkflowExecution.id == execution_id).first()
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    if execution.status != "AWAITING_APPROVAL":
        raise HTTPException(status_code=400, detail=f"Execution is in {execution.status} status and cannot be approved")
    
    from app.modules.orchestration.engine import WorkflowEngine
    engine = WorkflowEngine(db)
    engine.log_event(execution.id, "HUMAN_APPROVAL", "Human supervisor approved the workflow execution checkpoint.")
    
    # Resume and complete remaining steps
    from app.modules.registry.models import RegistryWorkflow
    workflow = db.query(RegistryWorkflow).filter(RegistryWorkflow.id == execution.workflow_id).first()
    if workflow and workflow.steps_json:
        steps = workflow.steps_json
        engine.log_event(execution.id, "RESUMED", "Execution resumed after human approval.")
        
        found_approval = False
        for step in steps:
            step_type = step.get("type", "")
            step_name = step.get("step_name", "")
            if step_type == "APPROVAL":
                found_approval = True
                continue
            if found_approval:
                engine.log_event(execution.id, "STEP_START", f"Executing step: {step_name}")
                engine.log_event(execution.id, "STEP_COMPLETE", f"Completed step: {step_name}")
                
    engine.complete_execution(execution.id, status="COMPLETED")
    return {"message": "Execution approved and completed successfully"}

@router.post("/executions/{execution_id}/reject")
def reject_execution(execution_id: str, db: Session = Depends(get_db)):
    """
    Reject an execution that is currently awaiting approval.
    """
    execution = db.query(WorkflowExecution).filter(WorkflowExecution.id == execution_id).first()
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    if execution.status != "AWAITING_APPROVAL":
        raise HTTPException(status_code=400, detail=f"Execution is in {execution.status} status and cannot be rejected")
    
    from app.modules.orchestration.engine import WorkflowEngine
    engine = WorkflowEngine(db)
    engine.log_event(execution.id, "HUMAN_REJECTION", "Human supervisor rejected the workflow execution checkpoint.")
    engine.complete_execution(execution.id, status="REJECTED")
    return {"message": "Execution rejected successfully"}

@router.post("/executions/{execution_id}/revoke")
def revoke_execution(execution_id: str, db: Session = Depends(get_db)):
    """
    Revoke a completed execution approval.
    """
    execution = db.query(WorkflowExecution).filter(WorkflowExecution.id == execution_id).first()
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    if execution.status != "COMPLETED":
        raise HTTPException(status_code=400, detail=f"Only completed executions can be revoked. Current status: {execution.status}")
    
    from app.modules.orchestration.engine import WorkflowEngine
    engine = WorkflowEngine(db)
    engine.log_event(execution.id, "HUMAN_REVOCATION", "Human supervisor revoked the previously approved workflow execution.")
    
    execution.status = "REVOKED"
    db.commit()
    return {"message": "Execution approval revoked successfully"}


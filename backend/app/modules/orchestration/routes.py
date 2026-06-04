from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.modules.orchestration.tasks import execute_workflow_task
from app.modules.orchestration.models import WorkflowExecution
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()

class ExecuteWorkflowRequest(BaseModel):
    is_dry_run: bool = False

class WorkflowExecutionResponse(BaseModel):
    id: str
    workflow_id: str
    status: str
    is_dry_run: bool

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
    execution = db.query(WorkflowExecution).filter(WorkflowExecution.id == execution_id).first()
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
        
    return {
        "id": execution.id,
        "workflow_id": execution.workflow_id,
        "status": execution.status,
        "is_dry_run": execution.is_dry_run,
        "started_at": execution.started_at,
        "completed_at": execution.completed_at
    }

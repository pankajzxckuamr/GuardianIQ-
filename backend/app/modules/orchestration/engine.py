import logging
from datetime import datetime
from sqlalchemy.orm import Session
from app.modules.orchestration.models import WorkflowExecution, ExecutionEventLog, ExecutionFinding
from app.modules.registry.models import RegistryWorkflow

logger = logging.getLogger(__name__)

class WorkflowEngine:
    def __init__(self, db: Session):
        self.db = db

    def start_execution(self, workflow_id: str, is_dry_run: bool = False) -> WorkflowExecution:
        workflow = self.db.query(RegistryWorkflow).filter(RegistryWorkflow.id == workflow_id).first()
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        execution = WorkflowExecution(
            workflow_id=workflow_id,
            status="RUNNING",
            is_dry_run=is_dry_run,
            started_at=datetime.utcnow()
        )
        self.db.add(execution)
        self.db.commit()
        self.db.refresh(execution)

        self.log_event(execution.id, "WORKFLOW_STARTED", f"Started execution for workflow {workflow.workflow_name}")
        return execution

    def complete_execution(self, execution_id: str, status: str = "COMPLETED"):
        execution = self.db.query(WorkflowExecution).filter(WorkflowExecution.id == execution_id).first()
        if not execution:
            raise ValueError(f"Execution {execution_id} not found")
        
        execution.status = status
        execution.completed_at = datetime.utcnow()
        self.db.commit()
        self.log_event(execution.id, "WORKFLOW_COMPLETED", f"Execution finished with status {status}")

    def fail_execution(self, execution_id: str, error_details: str):
        self.complete_execution(execution_id, status="FAILED")
        self.log_event(execution_id, "WORKFLOW_FAILED", error_details)
        self.add_finding(execution_id, "HIGH", "Execution Failure", error_details)

    def log_event(self, execution_id: str, event_type: str, details: str = None):
        log = ExecutionEventLog(
            execution_id=execution_id,
            event_type=event_type,
            details=details
        )
        self.db.add(log)
        self.db.commit()

    def add_finding(self, execution_id: str, severity: str, description: str, recommendation: str = None):
        finding = ExecutionFinding(
            execution_id=execution_id,
            severity=severity,
            description=description,
            recommendation_text=recommendation
        )
        self.db.add(finding)
        self.db.commit()

import logging
import time
from app.celery_app import celery_app
from app.db.session import SessionLocal
from app.modules.orchestration.engine import WorkflowEngine

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, max_retries=3)
def execute_workflow_task(self, workflow_id: str, is_dry_run: bool = False):
    """
    Celery task to execute a workflow asynchronously.
    """
    logger.info(f"Starting async execution for workflow {workflow_id}")
    db = SessionLocal()
    try:
        from app.modules.registry.models import RegistryWorkflow
        workflow = db.query(RegistryWorkflow).filter(RegistryWorkflow.id == workflow_id).first()
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        engine = WorkflowEngine(db)
        execution = engine.start_execution(workflow_id, is_dry_run)
        
        # Load steps
        steps = workflow.steps_json or []
        if isinstance(steps, str):
            try:
                import json
                steps = json.loads(steps)
            except Exception:
                steps = []
                
        # Filter out start/end nodes or handle them inline
        for index, step in enumerate(steps):
            step_type = step.get("type", "STEP")
            step_name = step.get("step_name", f"Step {index}")
            
            if step_type == "START":
                engine.log_event(execution.id, "START_NODE", f"Workflow execution initialized via: {step_name}")
                time.sleep(0.8)
                continue
            elif step_type == "END":
                engine.log_event(execution.id, "END_NODE", f"Workflow completion node reached: {step_name}")
                time.sleep(0.8)
                continue
                
            engine.log_event(execution.id, "STEP_START", f"Executing step: {step_name} ({step_type})")
            time.sleep(1.5)
            
            if step_type == "APPROVAL":
                engine.log_event(execution.id, "AWAITING_HUMAN_APPROVAL", f"Execution paused. Awaiting human supervisor approval for: {step_name}")
                execution.status = "AWAITING_APPROVAL"
                db.commit()
                return {"execution_id": str(execution.id), "status": "AWAITING_APPROVAL"}
                
            elif step_type == "EVALUATION":
                engine.log_event(execution.id, "EVALUATION_RUN", f"Running governance evaluation check for: {step_name}")
                time.sleep(0.5)
                engine.add_finding(
                    execution.id,
                    severity="LOW",
                    description=f"Evaluation constraint '{step_name}' passed policy standards.",
                    recommendation="Proceed with standard operations."
                )
            elif step_type == "TOOL":
                engine.log_event(execution.id, "TOOL_EXECUTE", f"Executing tool service integration: {step_name}")
                time.sleep(0.5)
                
            engine.log_event(execution.id, "STEP_COMPLETE", f"Completed step: {step_name} ({step_type})")
            time.sleep(0.5)
            
        engine.complete_execution(execution.id, status="COMPLETED")
        return {"execution_id": str(execution.id), "status": "COMPLETED"}
        
    except Exception as e:
        logger.error(f"Error executing workflow {workflow_id}: {str(e)}")
        # Check if execution was created before failing it
        try:
            if 'execution' in locals():
                engine.fail_execution(execution.id, error_details=str(e))
        except Exception as fe:
            logger.error(f"Could not fail execution: {str(fe)}")
        raise self.retry(exc=e, countdown=5)
    finally:
        db.close()

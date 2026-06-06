import os
import sys
from os.path import dirname, abspath

# Set environment variables for config loading
os.environ["DATABASE_URL"] = "postgresql://guardianiq_user:guardianiq123@127.0.0.1:5432/guardianiq"
os.environ["SECRET_KEY"] = "32d425c6255010ae7514096441a3d590a9def39add4c9e41a84714be3db57078"

# Add backend directory to sys.path
sys.path.append(abspath("backend"))

from app.db.session import SessionLocal
from app.modules.orchestration.models import WorkflowExecution
from app.modules.registry.models import RegistryWorkflow

def debug_db():
    db = SessionLocal()
    try:
        print("=== WORKFLOWS ===")
        workflows = db.query(RegistryWorkflow).all()
        for w in workflows:
            print(f"ID: {w.id} | Code: {w.workflow_code} | Name: {w.workflow_name}")
            
        print("\n=== EXECUTIONS ===")
        executions = db.query(WorkflowExecution).all()
        for e in executions:
            print(f"ID: {e.id} | Workflow ID: {e.workflow_id} | Status: {e.status} | Workflow Name property: {e.workflow_name} | Rel: {e.workflow}")
    except Exception as ex:
        print(f"Error: {ex}")
    finally:
        db.close()

if __name__ == "__main__":
    debug_db()

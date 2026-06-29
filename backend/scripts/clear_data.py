import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(r"d:\GuardianIQ--1\backend"))

from dotenv import load_dotenv
load_dotenv(os.path.join(r"d:\GuardianIQ--1\backend", ".env"))

from app.db.session import SessionLocal
from sqlalchemy import delete
from app.modules.workflow_scheduler.models import (
    Phase2WorkflowSchedule,
    WorkflowScheduleAgentAssignment,
    WorkflowScheduleApproval,
    WorkflowScheduleHistory,
)
from app.modules.workflow_execution.models import (
    WorkflowRun,
    WorkflowRunStep,
    WorkflowRunOutput,
    WorkflowRunFailure,
)

def clear_data():
    with SessionLocal() as db:
        print("Clearing data...")
        
        # Bottom-up deletion to avoid FK violations
        db.execute(delete(WorkflowRunOutput))
        print("Deleted WorkflowRunOutput")
        
        db.execute(delete(WorkflowRunFailure))
        print("Deleted WorkflowRunFailure")
        
        db.execute(delete(WorkflowRunStep))
        print("Deleted WorkflowRunStep")
        
        db.execute(delete(WorkflowRun))
        print("Deleted WorkflowRun")
        
        db.execute(delete(WorkflowScheduleAgentAssignment))
        print("Deleted WorkflowScheduleAgentAssignment")
        
        db.execute(delete(WorkflowScheduleApproval))
        print("Deleted WorkflowScheduleApproval")
        
        db.execute(delete(WorkflowScheduleHistory))
        print("Deleted WorkflowScheduleHistory")
        
        db.execute(delete(Phase2WorkflowSchedule))
        print("Deleted Phase2WorkflowSchedule")
        
        db.commit()
        print("Done!")

if __name__ == "__main__":
    clear_data()

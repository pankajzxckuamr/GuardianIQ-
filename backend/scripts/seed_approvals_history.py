import sys
import os
import uuid
import datetime
import pytz

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.session import SessionLocal
from app.modules.workflow_scheduler.models import Phase2WorkflowSchedule, WorkflowScheduleHistory, WorkflowScheduleApproval

def seed_data():
    db = SessionLocal()
    try:
        schedules = db.query(Phase2WorkflowSchedule).all()
        print(f"Found {len(schedules)} schedules.")
        
        for schedule in schedules:
            # Seed History
            history_count = db.query(WorkflowScheduleHistory).filter(WorkflowScheduleHistory.schedule_id == schedule.id).count()
            if history_count == 0:
                print(f"Adding initial history for schedule: {schedule.schedule_name}")
                history_rec = WorkflowScheduleHistory(
                    id=uuid.uuid4(),
                    tenant_id=schedule.tenant_id,
                    schedule_id=schedule.id,
                    change_type="CREATE",
                    change_summary="Schedule created (seeded)",
                    before_json={},
                    after_json={},
                    changed_by=schedule.owner_user_id,
                    created_by=schedule.owner_user_id,
                    updated_by=schedule.owner_user_id,
                    created_at=schedule.created_at or datetime.datetime.now(datetime.timezone.utc)
                )
                db.add(history_rec)
                
                # Add another history event if it's ACTIVE
                sched_status_str = schedule.schedule_status.value if hasattr(schedule.schedule_status, "value") else str(schedule.schedule_status)
                if sched_status_str == "ACTIVE":
                    history_rec2 = WorkflowScheduleHistory(
                        id=uuid.uuid4(),
                        tenant_id=schedule.tenant_id,
                        schedule_id=schedule.id,
                        change_type="ACTIVATE",
                        change_summary="Schedule activated after approval",
                        before_json={},
                        after_json={},
                        changed_by=schedule.owner_user_id,
                        created_by=schedule.owner_user_id,
                        updated_by=schedule.owner_user_id,
                        created_at=datetime.datetime.now(datetime.timezone.utc)
                    )
                    db.add(history_rec2)

            # Seed Approvals
            approval_count = db.query(WorkflowScheduleApproval).filter(WorkflowScheduleApproval.schedule_id == schedule.id).count()
            if approval_count == 0:
                sched_status_str = schedule.schedule_status.value if hasattr(schedule.schedule_status, "value") else str(schedule.schedule_status)
                if sched_status_str == "ACTIVE":
                    print(f"Adding mock approval for schedule: {schedule.schedule_name}")
                    approval = WorkflowScheduleApproval(
                        id=uuid.uuid4(),
                        tenant_id=schedule.tenant_id,
                        schedule_id=schedule.id,
                        approval_type="ACTIVATION",
                        approval_status="APPROVED",
                        decision_reason="Approved per security policies",
                        decided_at=datetime.datetime.now(datetime.timezone.utc),
                        approval_group_id=schedule.approval_group_id,
                        submitted_by=schedule.owner_user_id,
                        approver_user_id=schedule.owner_user_id,
                        created_by=schedule.owner_user_id,
                        updated_by=schedule.owner_user_id,
                        created_at=schedule.created_at or datetime.datetime.now(datetime.timezone.utc)
                    )
                    db.add(approval)
                    
        db.commit()
        print("Successfully seeded approval and history data!")
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()

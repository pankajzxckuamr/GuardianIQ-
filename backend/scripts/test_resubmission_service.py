import sys
import os
import uuid
import logging
import asyncio
from datetime import datetime
from sqlalchemy import text

sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from app.db.session import AsyncSessionLocal
from app.modules.workflow_scheduler.service import WorkflowScheduleService
from app.modules.workflow_scheduler.models import ScheduleStatus
from app.modules.registry.models import User

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_resubmission_test():
    async with AsyncSessionLocal() as db:
        # Get an active user
        user_res = await db.execute(text("SELECT id FROM users LIMIT 1"))
        user_id = user_res.scalar()
        if not user_id:
            logger.error("No users found.")
            return

        class DummyUser:
            id = user_id
            role_code = "ADMIN"

        current_user = DummyUser()

        # Get a schedule
        sched_res = await db.execute(text("SELECT id FROM workflow_schedules LIMIT 1"))
        schedule_id = sched_res.scalar()
        if not schedule_id:
            logger.error("No schedules found.")
            return

        logger.info(f"Using schedule_id: {schedule_id}")
        
        service = WorkflowScheduleService()
        
        # 1. Reset schedule to DRAFT
        await db.execute(text("UPDATE workflow_schedules SET schedule_status = 'DRAFT', approval_required = true WHERE id = :id"), {"id": schedule_id})
        
        # Ensure it has a PRIMARY assignment
        await db.execute(text("DELETE FROM workflow_schedule_agent_assignments WHERE schedule_id = :id"), {"id": schedule_id})
        await db.execute(text("""
            INSERT INTO workflow_schedule_agent_assignments (id, tenant_id, schedule_id, agent_id, assignment_role, is_deleted)
            VALUES (:id, (SELECT tenant_id FROM workflow_schedules WHERE id = :sched), :sched, :agent, 'PRIMARY', false)
        """), {"id": uuid.uuid4(), "sched": schedule_id, "agent": uuid.uuid4()})

        # Ensure layers are assigned
        await db.execute(text("DELETE FROM schedule_approval_layer_selections WHERE schedule_id = :id"), {"id": schedule_id})
        dept_res = await db.execute(text("SELECT id FROM departments LIMIT 2"))
        depts = dept_res.scalars().all()
        
        if len(depts) < 2:
            logger.error("Not enough departments found.")
            return

        for i, d_id in enumerate(depts):
            await db.execute(text("""
                INSERT INTO schedule_approval_layer_selections (id, tenant_id, schedule_id, department_id, layer_order)
                VALUES (:id, (SELECT tenant_id FROM workflow_schedules WHERE id = :sched), :sched, :dept, :order)
            """), {"id": uuid.uuid4(), "sched": schedule_id, "dept": d_id, "order": i+1})
            
            # Ensure owner assignment exists
            owner_res = await db.execute(text("SELECT id FROM department_owner_assignments WHERE department_id = :d"), {"d": d_id})
            if not owner_res.scalar():
                await db.execute(text("""
                    INSERT INTO department_owner_assignments (id, tenant_id, department_id, owner_user_id)
                    VALUES (:id, (SELECT tenant_id FROM departments WHERE id = :d), :d, :u)
                """), {"id": uuid.uuid4(), "d": d_id, "u": user_id})

        await db.commit()

        # 2. First Submission
        logger.info("Submitting for cycle 1...")
        await service.submit_for_approval(schedule_id, current_user, db)
        
        # Find the pending approval
        app_res = await db.execute(text("SELECT id FROM workflow_schedule_approvals WHERE schedule_id = :id AND approval_status = 'PENDING' ORDER BY created_at DESC LIMIT 1"), {"id": schedule_id})
        approval_id = app_res.scalar()

        # Reject it
        logger.info(f"Rejecting approval {approval_id}...")
        await service.decide_approval(approval_id, "REJECTED", "Needs work", current_user, db)
        
        # 3. Resubmit
        logger.info("Resubmitting for cycle 2...")
        await service.submit_for_approval(schedule_id, current_user, db)

        # 4. Query all approvals for this schedule
        logger.info("--- APPROVALS HISTORY ---")
        hist_res = await db.execute(text("""
            SELECT approval_cycle_id, approval_layer, approval_status, skip_reason, created_at 
            FROM workflow_schedule_approvals 
            WHERE schedule_id = :id 
            ORDER BY created_at ASC
        """), {"id": schedule_id})
        
        for row in hist_res:
            logger.info(f"Cycle: {row.approval_cycle_id} | Layer: {row.approval_layer} | Status: {row.approval_status} | Skipped: {row.skip_reason} | Date: {row.created_at}")

if __name__ == "__main__":
    asyncio.run(run_resubmission_test())

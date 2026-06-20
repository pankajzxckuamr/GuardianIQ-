import os
import asyncio
import signal
from datetime import datetime

from sqlalchemy.future import select

from app.shared.db import get_db_session
from app.workers.next_run_calculator import calculate_next_run
from app.modules.workflow_execution.service import WorkflowRunService
from app.modules.workflow_scheduler.models import Phase2WorkflowSchedule
from app.modules.workflow_scheduler.repository import WorkflowScheduleRepository
from app.shared.enums import TriggerType
from app.shared.db_compat import execute_statement

POLL_INTERVAL = int(os.getenv('SCHEDULER_POLL_INTERVAL_SECONDS', 60))
BATCH_SIZE = int(os.getenv('SCHEDULER_BATCH_SIZE', 25))
ENABLED = os.getenv('SCHEDULER_ENABLED', 'true').lower() == 'true'

class SchedulerWorker:
    def __init__(self): 
        self._running = False

    async def run_loop(self):
        self._running = True
        print(f"Scheduler worker started. Poll interval: {POLL_INTERVAL}s")
        while self._running:
            try:
                await self.poll_and_trigger()
            except Exception as e:
                print(f"Worker cycle error: {e}")
            await asyncio.sleep(POLL_INTERVAL)

    async def poll_and_trigger(self):
        async with get_db_session() as db:
            schedules = await self.get_due_schedules(db)
            for schedule in schedules:
                try:
                    await self.trigger_schedule(schedule, db)
                except Exception as e:
                    print(f"Failed to trigger schedule {schedule.id}: {e}")
                    # Do NOT re-raise — continue with next schedule

    async def get_due_schedules(self, db):
        # SELECT ... FROM workflow_schedules WHERE schedule_status='ACTIVE'
        # AND next_run_at <= NOW() AND is_deleted=false
        # FOR UPDATE SKIP LOCKED LIMIT {BATCH_SIZE}
        stmt = (
            select(Phase2WorkflowSchedule)
            .where(
                Phase2WorkflowSchedule.schedule_status == 'ACTIVE',
                Phase2WorkflowSchedule.next_run_at <= datetime.utcnow(),
                Phase2WorkflowSchedule.is_deleted == False
            )
            .with_for_update(skip_locked=True)
            .limit(BATCH_SIZE)
        )
        res = await execute_statement(db, stmt)
        return res.scalars().all()

    async def trigger_schedule(self, schedule, db):
        # We use create_run_internal because create_run requires the db as first parameter and a valid current_user
        run = await WorkflowRunService().create_run_internal(schedule.id, TriggerType.SCHEDULED.value, None, db)
        next_run = calculate_next_run(schedule)
        
        await WorkflowScheduleRepository().update(db, schedule, {
            'next_run_at': next_run,
            'last_run_at': datetime.utcnow()
        })
        # Commit inside this transaction so next_run_at update and run creation are atomic
        # The update method from repository already calls commit_session(db)
        
        await WorkflowRunService().start_run(run.id, db)
        await WorkflowRunService().execute_run(run.id, db)

    def shutdown(self):
        self._running = False
        print("Scheduler worker shutting down gracefully")

if __name__ == '__main__':
    if not ENABLED:
        print("Scheduler disabled via SCHEDULER_ENABLED=false")
        exit(0)
    worker = SchedulerWorker()
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, worker.shutdown)
    loop.run_until_complete(worker.run_loop())

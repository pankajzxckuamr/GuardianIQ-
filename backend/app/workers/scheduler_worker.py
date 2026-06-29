import os
import asyncio
import signal
import json
import uuid
import time
from datetime import datetime, timezone
import uvicorn
from fastapi import FastAPI, Response, status

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
WORKER_ID = os.getenv('SCHEDULER_WORKER_ID', str(uuid.uuid4()))

class SchedulerWorker:
    def __init__(self): 
        self._running = False
        self.last_poll_at = None
        self.last_successful_cycle_at = None
        self.consecutive_errors = 0

    def log(self, event: str, **kwargs):
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "worker_id": WORKER_ID,
            "event": event,
            **kwargs
        }
        print(json.dumps(log_entry))

    async def run_loop(self):
        self._running = True
        self.log("WORKER_START", poll_interval=POLL_INTERVAL)
        while self._running:
            self.last_poll_at = datetime.now(timezone.utc)
            start_time = time.time()
            try:
                found_count = await self.poll_and_trigger()
                self.last_successful_cycle_at = datetime.now(timezone.utc)
                self.consecutive_errors = 0
                duration_ms = int((time.time() - start_time) * 1000)
                self.log("CYCLE_END", schedules_found=found_count, duration_ms=duration_ms)
            except Exception as e:
                self.consecutive_errors += 1
                self.log("CYCLE_ERROR", error_msg=str(e))
            
            await asyncio.sleep(POLL_INTERVAL)

    async def poll_and_trigger(self) -> int:
        count = 0
        async with get_db_session() as db:
            schedules = await self.get_due_schedules(db)
            count = len(schedules)
            if count > 0:
                self.log("CYCLE_START", schedules_found=count)
            for schedule in schedules:
                try:
                    await self.trigger_schedule(schedule, db)
                except Exception as e:
                    self.log("TRIGGER_ERROR", schedule_id=str(schedule.id), error_msg=str(e))
                    # Do NOT re-raise — continue with next schedule
        return count

    async def get_due_schedules(self, db):
        stmt = (
            select(Phase2WorkflowSchedule)
            .where(
                Phase2WorkflowSchedule.schedule_status == 'ACTIVE',
                Phase2WorkflowSchedule.next_run_at <= datetime.now(timezone.utc),
                Phase2WorkflowSchedule.is_deleted == False
            )
            .order_by(Phase2WorkflowSchedule.next_run_at.asc())
            .with_for_update(skip_locked=True)
            .limit(BATCH_SIZE)
        )
        res = await execute_statement(db, stmt)
        return res.scalars().all()

    async def trigger_schedule(self, schedule, db):
        run = await WorkflowRunService().create_run_internal(schedule.id, TriggerType.SCHEDULED.value, None, db)
        next_run = calculate_next_run(schedule)
        
        await WorkflowScheduleRepository().update(db, schedule, {
            'next_run_at': next_run,
            'last_run_at': datetime.now(timezone.utc)
        })
        # Commit inside this transaction so next_run_at update and run creation are atomic
        
        self.log("TRIGGER_SCHEDULE", schedule_id=str(schedule.id), schedule_code=schedule.schedule_code, run_id=str(run.id))
        
        # Execute asynchronously without blocking the loop
        asyncio.create_task(self._execute_run_async(run.id))

    async def _execute_run_async(self, run_id):
        # Must run inside its own DB session
        async with get_db_session() as background_db:
            try:
                await WorkflowRunService().start_run(run_id, background_db)
                await WorkflowRunService().execute_run(run_id, background_db)
            except Exception as e:
                self.log("ASYNC_RUN_ERROR", run_id=str(run_id), error_msg=str(e))

    def shutdown(self):
        self._running = False
        self.log("WORKER_SHUTDOWN")


# Health API setup
worker = SchedulerWorker()
app = FastAPI(title="Scheduler Worker Health API")

@app.get("/health/scheduler")
def health_check(response: Response):
    now = datetime.now(timezone.utc)
    
    if worker.consecutive_errors > 5:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "down", "reason": "too_many_errors", "errors": worker.consecutive_errors}
        
    if worker.last_successful_cycle_at:
        seconds_since = (now - worker.last_successful_cycle_at).total_seconds()
        if seconds_since > (3 * POLL_INTERVAL):
            response.status_code = status.HTTP_200_OK
            return {"status": "degraded", "reason": "stale_cycle", "seconds_since": seconds_since}
            
    return {"status": "healthy"}

async def start_health_server():
    config = uvicorn.Config(app, host="0.0.0.0", port=int(os.getenv("SCHEDULER_HEALTH_PORT", 8081)), log_level="error")
    server = uvicorn.Server(config)
    await server.serve()

async def main():
    if not ENABLED:
        print(json.dumps({"event": "SCHEDULER_DISABLED", "msg": "Scheduler disabled via SCHEDULER_ENABLED=false"}))
        return
        
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, worker.shutdown)
        
    # Start both the worker loop and health server concurrently
    await asyncio.gather(
        worker.run_loop(),
        start_health_server()
    )

if __name__ == '__main__':
    asyncio.run(main())

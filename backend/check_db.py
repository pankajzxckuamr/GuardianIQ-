import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(r"d:\GuardianIQ--1\backend"))

from app.db.session import SessionLocal
from sqlalchemy import select
from app.modules.workflow_scheduler.models import Phase2WorkflowSchedule

async def check_duplicates():
    async with SessionLocal() as db:
        stmt = select(Phase2WorkflowSchedule)
        res = await db.execute(stmt)
        schedules = res.scalars().all()
        print(f"Total schedules: {len(schedules)}")
        for s in schedules:
            print(f"ID: {s.id}, Name: '{s.schedule_name}', Code: '{s.schedule_code}', Tenant ID: {getattr(s, 'tenant_id', None)}, Owner ID: {s.owner_user_id}, Deleted: {s.is_deleted}")

if __name__ == "__main__":
    import asyncio
    loop = asyncio.get_event_loop()
    loop.run_until_complete(check_duplicates())

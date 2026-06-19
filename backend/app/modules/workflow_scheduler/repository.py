import inspect
from uuid import UUID
from datetime import datetime, timezone
import sqlalchemy as sa
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.modules.workflow_scheduler.models import (
    Phase2WorkflowSchedule,
    WorkflowScheduleAgentAssignment,
    WorkflowScheduleApproval,
    WorkflowScheduleHistory
)
from app.modules.workflow_execution.models import WorkflowRun

from app.shared.db_compat import execute_statement, commit_session, db_flush

class WorkflowScheduleRepository:
    async def create(self, db, obj_in: dict, agent_assignments_in: list[dict] = None) -> Phase2WorkflowSchedule:
        schedule = Phase2WorkflowSchedule(**obj_in)
        db.add(schedule)
        await db_flush(db)  # populate ID
        
        if agent_assignments_in:
            for assignment in agent_assignments_in:
                assignment["schedule_id"] = schedule.id
                db.add(WorkflowScheduleAgentAssignment(**assignment))
        
        await commit_session(db)
        # Refresh schedule to load relationships
        stmt = (
            select(Phase2WorkflowSchedule)
            .options(
                selectinload(Phase2WorkflowSchedule.agent_assignments),
                selectinload(Phase2WorkflowSchedule.approvals),
                selectinload(Phase2WorkflowSchedule.runs)
            )
            .where(Phase2WorkflowSchedule.id == schedule.id)
        )
        res = await execute_statement(db, stmt)
        return res.scalar_one()

    async def get_by_id(self, db, id: UUID) -> Phase2WorkflowSchedule | None:
        stmt = (
            select(Phase2WorkflowSchedule)
            .options(
                selectinload(Phase2WorkflowSchedule.agent_assignments),
                selectinload(Phase2WorkflowSchedule.approvals),
                selectinload(Phase2WorkflowSchedule.runs)
            )
            .where(Phase2WorkflowSchedule.id == id, Phase2WorkflowSchedule.is_deleted == False)
        )
        res = await execute_statement(db, stmt)
        return res.scalar()

    async def list_with_filters(self, db, page: int, page_size: int, filters: dict) -> tuple[list[Phase2WorkflowSchedule], int]:
        query = select(Phase2WorkflowSchedule).where(Phase2WorkflowSchedule.is_deleted == False)
        
        # Apply filters
        if "status" in filters and filters["status"]:
            query = query.where(Phase2WorkflowSchedule.schedule_status == filters["status"])
        if "risk_level" in filters and filters["risk_level"]:
            query = query.where(Phase2WorkflowSchedule.risk_level == filters["risk_level"])
        if "owner_user_id" in filters and filters["owner_user_id"]:
            query = query.where(Phase2WorkflowSchedule.owner_user_id == filters["owner_user_id"])
        if "workflow_id" in filters and filters["workflow_id"]:
            query = query.where(Phase2WorkflowSchedule.workflow_id == filters["workflow_id"])
        if "schedule_type" in filters and filters["schedule_type"]:
            query = query.where(Phase2WorkflowSchedule.schedule_type == filters["schedule_type"])
            
        # Count total
        count_stmt = select(sa.func.count()).select_from(query.subquery())
        count_res = await execute_statement(db, count_stmt)
        total = count_res.scalar() or 0
        
        # Paginate
        offset = (page - 1) * page_size
        query = query.order_by(Phase2WorkflowSchedule.created_at.desc()).offset(offset).limit(page_size)
        query = query.options(
            selectinload(Phase2WorkflowSchedule.agent_assignments),
            selectinload(Phase2WorkflowSchedule.approvals)
        )
        res = await execute_statement(db, query)
        items = list(res.scalars().all())
        
        return items, total

    async def update(self, db, db_obj: Phase2WorkflowSchedule, obj_in: dict) -> Phase2WorkflowSchedule:
        # Check if we are updating agent assignments
        assignments_data = obj_in.pop("agent_assignments", None)
        
        for k, v in obj_in.items():
            setattr(db_obj, k, v)
        db_obj.updated_at = sa.func.now()
        db_obj.version_no += 1
        
        if assignments_data is not None:
            # Recreate agent assignments
            # 1. Delete existing
            delete_stmt = sa.delete(WorkflowScheduleAgentAssignment).where(
                WorkflowScheduleAgentAssignment.schedule_id == db_obj.id
            )
            await execute_statement(db, delete_stmt)
            
            # 2. Add new
            for assignment in assignments_data:
                assignment["schedule_id"] = db_obj.id
                db.add(WorkflowScheduleAgentAssignment(**assignment))
                
        await commit_session(db)
        return db_obj

    async def update_status(self, db, db_obj: Phase2WorkflowSchedule, new_status: str) -> Phase2WorkflowSchedule:
        db_obj.schedule_status = new_status
        db_obj.updated_at = sa.func.now()
        db_obj.version_no += 1
        await commit_session(db)
        return db_obj

    async def get_due_schedules(self, db) -> list[Phase2WorkflowSchedule]:
        now = datetime.now(timezone.utc)
        stmt = (
            select(Phase2WorkflowSchedule)
            .where(
                Phase2WorkflowSchedule.schedule_status == "ACTIVE",
                Phase2WorkflowSchedule.next_run_at <= now,
                Phase2WorkflowSchedule.is_deleted == False
            )
            .with_for_update(skip_locked=True)
            .limit(25)
        )
        res = await execute_statement(db, stmt)
        return list(res.scalars().all())

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
    WorkflowScheduleHistory,
    ScheduleApprovalLayerSelection
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
                if "allowed_tools" in assignment:
                    assignment["allowed_tools_json"] = assignment.pop("allowed_tools")
                if "allowed_data_sources" in assignment:
                    assignment["allowed_data_sources_json"] = assignment.pop("allowed_data_sources")
                if "blocked_operations" in assignment:
                    assignment["blocked_operations_json"] = assignment.pop("blocked_operations")
                if "boundary_rules" in assignment:
                    br = assignment.pop("boundary_rules")
                    assignment["boundary_rules_json"] = br.model_dump() if hasattr(br, "model_dump") else br
                db.add(WorkflowScheduleAgentAssignment(**assignment))
        
        await commit_session(db)
        # Refresh schedule to load relationships
        stmt = (
            select(Phase2WorkflowSchedule)
            .options(
                selectinload(Phase2WorkflowSchedule.agent_assignments).selectinload(WorkflowScheduleAgentAssignment.agent),
                selectinload(Phase2WorkflowSchedule.agent_assignments).selectinload(WorkflowScheduleAgentAssignment.model),
                selectinload(Phase2WorkflowSchedule.approvals),
                selectinload(Phase2WorkflowSchedule.runs),
                selectinload(Phase2WorkflowSchedule.layer_selections).selectinload(ScheduleApprovalLayerSelection.department)
            )
            .where(Phase2WorkflowSchedule.id == schedule.id)
        )
        res = await execute_statement(db, stmt)
        return res.scalar_one()

    async def get_by_id(self, db, id: UUID) -> Phase2WorkflowSchedule | None:
        stmt = (
            select(Phase2WorkflowSchedule)
            .options(
                selectinload(Phase2WorkflowSchedule.agent_assignments).selectinload(WorkflowScheduleAgentAssignment.agent),
                selectinload(Phase2WorkflowSchedule.agent_assignments).selectinload(WorkflowScheduleAgentAssignment.model),
                selectinload(Phase2WorkflowSchedule.approvals),
                selectinload(Phase2WorkflowSchedule.runs),
                selectinload(Phase2WorkflowSchedule.workflow),
                selectinload(Phase2WorkflowSchedule.owner_user),
                selectinload(Phase2WorkflowSchedule.layer_selections).selectinload(ScheduleApprovalLayerSelection.department)
            )
            .where(Phase2WorkflowSchedule.id == id, Phase2WorkflowSchedule.is_deleted == False)
        )
        res = await execute_statement(db, stmt)
        return res.scalar()

    async def list_with_filters(self, db, page: int, page_size: int, filters: dict) -> tuple[list[Phase2WorkflowSchedule], int]:
        query = select(Phase2WorkflowSchedule).where(Phase2WorkflowSchedule.is_deleted == False)
        
        # Apply filters
        if "status" in filters and filters["status"]:
            status_val = filters["status"]
            if isinstance(status_val, str) and "," in status_val:
                status_val = [s.strip() for s in status_val.split(",")]
            
            if isinstance(status_val, list):
                query = query.where(Phase2WorkflowSchedule.schedule_status.in_(status_val))
            else:
                query = query.where(Phase2WorkflowSchedule.schedule_status == status_val)
        if "risk_level" in filters and filters["risk_level"]:
            query = query.where(Phase2WorkflowSchedule.risk_level == filters["risk_level"])
        if "owner_user_id" in filters and filters["owner_user_id"]:
            query = query.where(Phase2WorkflowSchedule.owner_user_id == filters["owner_user_id"])
        if "workflow_id" in filters and filters["workflow_id"]:
            query = query.where(Phase2WorkflowSchedule.workflow_id == filters["workflow_id"])
        if "schedule_type" in filters and filters["schedule_type"]:
            query = query.where(Phase2WorkflowSchedule.schedule_type == filters["schedule_type"])
        if "approver_user_id" in filters and filters["approver_user_id"]:
            from app.modules.workflow_scheduler.models import WorkflowScheduleApproval
            subq = select(WorkflowScheduleApproval.schedule_id).where(
                WorkflowScheduleApproval.approver_user_id == filters["approver_user_id"],
                WorkflowScheduleApproval.approval_status == "PENDING"
            )
            query = query.where(Phase2WorkflowSchedule.id.in_(subq))
        elif "approval_group_ids" in filters and filters["approval_group_ids"]:
            from app.modules.workflow_scheduler.models import WorkflowScheduleApproval
            subq = select(WorkflowScheduleApproval.schedule_id).where(
                WorkflowScheduleApproval.approval_group_id.in_(filters["approval_group_ids"]),
                WorkflowScheduleApproval.approval_status == "PENDING"
            )
            query = query.where(Phase2WorkflowSchedule.id.in_(subq))
            
        # Count total
        count_query = select(sa.func.count(Phase2WorkflowSchedule.id))
        if query.whereclause is not None:
            count_query = count_query.where(query.whereclause)
        count_res = await execute_statement(db, count_query)
        total = count_res.scalar() or 0
        
        # Sort
        sort_by = filters.get("sort_by", "created_at")
        sort_dir = filters.get("sort_dir", "desc")
        
        sort_attr = getattr(Phase2WorkflowSchedule, sort_by, Phase2WorkflowSchedule.created_at)
        if sort_dir.lower() == "asc":
            query = query.order_by(sort_attr.asc())
        else:
            query = query.order_by(sort_attr.desc())
        
        # Paginate
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        query = query.options(
            selectinload(Phase2WorkflowSchedule.agent_assignments),
            selectinload(Phase2WorkflowSchedule.approvals),
            selectinload(Phase2WorkflowSchedule.workflow),
            selectinload(Phase2WorkflowSchedule.owner_user),
            selectinload(Phase2WorkflowSchedule.layer_selections).selectinload(ScheduleApprovalLayerSelection.department)
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
                if "allowed_tools" in assignment:
                    assignment["allowed_tools_json"] = assignment.pop("allowed_tools")
                if "allowed_data_sources" in assignment:
                    assignment["allowed_data_sources_json"] = assignment.pop("allowed_data_sources")
                if "blocked_operations" in assignment:
                    assignment["blocked_operations_json"] = assignment.pop("blocked_operations")
                if "boundary_rules" in assignment:
                    br = assignment.pop("boundary_rules")
                    assignment["boundary_rules_json"] = br.model_dump() if hasattr(br, "model_dump") else br
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

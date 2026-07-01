from uuid import UUID
import sqlalchemy as sa
from sqlalchemy.future import select

from app.modules.registry.models import RegistryWorkflow, RegistryAIAgent, RegistryAIModel
from app.modules.audit.event_service import GovernanceEventService
from app.modules.audit.event_codes import WorkflowEventCode
from app.shared.db_compat import db_get, execute_statement

import dataclasses
from uuid import UUID
import sqlalchemy as sa
from sqlalchemy.future import select

from app.modules.registry.models import RegistryWorkflow, RegistryAIAgent, RegistryAIModel, RegistryDataSource, RegistryTool
from app.modules.audit.event_service import GovernanceEventService
from app.modules.audit.event_codes import WorkflowEventCode
from app.shared.db_compat import db_get, execute_statement
from app.modules.workflow_scheduler.registry_check_service import RegistryCheckService

EXECUTION_MODE_RANK = {
    "READ_ONLY": 1,
    "RECOMMEND_ONLY": 2,
    "APPROVAL_REQUIRED": 3,
    "LIMITED_EXECUTION": 4,
    "FULLY_BLOCKED": 5
}

@dataclasses.dataclass
class BoundaryValidationResult:
    is_valid: bool
    write_capable_tools: bool
    errors: list[str]
    warnings: list[str]
    requires_approval: bool

class BoundaryChecker:
    def __init__(self):
        self.event_service = GovernanceEventService()

    async def validate_assignment_boundaries(self, assignment_payload: dict, agent_id: UUID, db) -> BoundaryValidationResult:
        errors = []
        warnings = []
        write_capable = False
        
        # 1. Check tools
        allowed_tools = assignment_payload.get("allowed_tools_json", [])
        agent_tools = await RegistryCheckService.get_agent_allowed_tools(agent_id, db)
        
        for tool in allowed_tools:
            if tool not in agent_tools:
                errors.append(f"Tool {tool} is not linked to agent {agent_id} or is not ACTIVE")
            
            is_write = await RegistryCheckService.check_tool_is_write_capable(tool, db)
            if is_write:
                write_capable = True
                warnings.append(f"Tool {tool} is write-capable. Approval will be required.")

        # 2. Check data sources
        allowed_data_sources = assignment_payload.get("allowed_data_sources_json", [])
        for ds in allowed_data_sources:
            is_uuid = False
            try:
                UUID(ds)
                is_uuid = True
            except ValueError:
                pass
            
            if is_uuid:
                stmt = sa.select(RegistryDataSource).where(
                    RegistryDataSource.id == UUID(ds),
                    RegistryDataSource.status == "ACTIVE"
                )
            else:
                stmt = sa.select(RegistryDataSource).where(
                    sa.or_(
                        RegistryDataSource.source_code == ds,
                        RegistryDataSource.source_name == ds
                    ),
                    RegistryDataSource.status == "ACTIVE"
                )
            res = await execute_statement(db, stmt)
            if not res.scalar():
                errors.append(f"Data source {ds} is not ACTIVE or does not exist")

        # 3. Contradiction check
        blocked_operations = assignment_payload.get("blocked_operations_json", [])
        for tool in allowed_tools:
            if tool in blocked_operations:
                errors.append(f"Contradiction: {tool} is both allowed and blocked")

        return BoundaryValidationResult(
            is_valid=len(errors) == 0,
            write_capable_tools=write_capable,
            errors=errors,
            warnings=warnings,
            requires_approval=write_capable
        )

    async def validate_runtime_boundary(self, assignment, tool_name: str, operation: str, db) -> tuple[bool, str | None]:
        # 1. tool_name in allowed_tools_json
        allowed_tools = assignment.allowed_tools_json or []
        
        # Get both tool code and name from DB to check against allowed_tools
        stmt = sa.select(RegistryTool).where(
            sa.or_(
                RegistryTool.tool_name == tool_name,
                RegistryTool.tool_code == tool_name
            ),
            RegistryTool.status == "ACTIVE"
        )
        res = await execute_statement(db, stmt)
        tool_obj = res.scalar()
        
        # We check both identifiers
        identifiers = [tool_name]
        if tool_obj:
            identifiers.extend([tool_obj.tool_code, tool_obj.tool_name])
            
        if not any(ident in allowed_tools for ident in identifiers):
            reason = f"Tool {tool_name} is not in allowed_tools_json"
            await self._publish_failure(assignment, reason, db)
            return False, reason

        # 2. operation NOT in blocked_operations_json
        blocked_ops = assignment.blocked_operations_json or []
        if operation in blocked_ops:
            reason = f"Operation {operation} is blocked by blocked_operations_json"
            await self._publish_failure(assignment, reason, db)
            return False, reason

        # 3. execution_mode permits
        assign_mode = assignment.execution_mode.value if hasattr(assignment.execution_mode, "value") else str(assignment.execution_mode)
        if assign_mode == "FULLY_BLOCKED":
            reason = "Execution mode is FULLY_BLOCKED"
            await self._publish_failure(assignment, reason, db)
            return False, reason

        if assign_mode in ["READ_ONLY", "RECOMMEND_ONLY"]:
            is_write = await RegistryCheckService.check_tool_is_write_capable(tool_name, db)
            if is_write:
                reason = f"Tool {tool_name} is write-capable but mode is {assign_mode}"
                await self._publish_failure(assignment, reason, db)
                return False, reason

        # Success
        await self.event_service.publish_event(
            event_code=WorkflowEventCode.AGENT_BOUNDARY_CHECK_PASSED,
            entity_type="workflow_schedules",
            entity_id=assignment.schedule_id,
            actor_type="SYSTEM",
            actor_id=None,
            action_type="BOUNDARY_CHECK",
            event_summary=f"Agent boundary check passed for tool {tool_name}",
            event_payload={"agent_id": str(assignment.agent_id), "requested_tool": tool_name},
            db=db
        )
        return True, None

    async def _publish_failure(self, assignment, reason: str, db):
        await self.event_service.publish_event(
            event_code=WorkflowEventCode.AGENT_BOUNDARY_CHECK_FAILED,
            entity_type="workflow_schedules",
            entity_id=assignment.schedule_id,
            actor_type="SYSTEM",
            actor_id=None,
            action_type="BOUNDARY_CHECK",
            event_summary=f"Agent boundary check failed: {reason}",
            event_payload={"agent_id": str(assignment.agent_id), "reason": reason},
            db=db
        )

    async def check(self, assignment, requested_tool: str | None, db) -> tuple[bool, str | None]:
        # 1. Load active entities
        agent = await db_get(db, RegistryAIAgent, assignment.agent_id)
        if not agent or agent.status != "ACTIVE":
            reason = f"Agent {assignment.agent_id} is not ACTIVE"
            await self._publish_failure(assignment, reason, db)
            return False, reason

        # Note: model_id might be optional in schemas, let's check if model exists
        if assignment.model_id:
            model = await db_get(db, RegistryAIModel, assignment.model_id)
            if not model or model.status != "ACTIVE":
                reason = f"Model {assignment.model_id} is not ACTIVE"
                await self._publish_failure(assignment, reason, db)
                return False, reason

        # Load workflow active status
        workflow = await db_get(db, RegistryWorkflow, assignment.schedule.workflow_id)
        if not workflow or workflow.status != "ACTIVE":
            reason = f"Workflow {assignment.schedule.workflow_id} is not ACTIVE"
            await self._publish_failure(assignment, reason, db)
            return False, reason

        # 2. Verify: if requested_tool is set, it must be in assignment.allowed_tools_json
        if requested_tool:
            allowed_tools = assignment.allowed_tools_json or []
            if requested_tool not in allowed_tools:
                reason = f"Requested tool {requested_tool} is not allowed by assignment policy"
                await self._publish_failure(assignment, reason, db)
                return False, reason

        # 3. Verify: execution_mode not exceeded
        # Rank of assignment.execution_mode cannot exceed rank of agent.execution_mode
        assign_mode = assignment.execution_mode.value if hasattr(assignment.execution_mode, "value") else str(assignment.execution_mode)
        agent_mode = agent.execution_mode.value if hasattr(agent.execution_mode, "value") else str(agent.execution_mode)
        
        if EXECUTION_MODE_RANK.get(assign_mode, 0) > EXECUTION_MODE_RANK.get(agent_mode, 0):
            reason = f"Assignment execution mode {assign_mode} exceeds agent's max registered mode {agent_mode}"
            await self._publish_failure(assignment, reason, db)
            return False, reason

        # Passed boundary verification
        await self.event_service.publish_event(
            event_code=WorkflowEventCode.AGENT_BOUNDARY_CHECK_PASSED,
            entity_type="workflow_schedules",
            entity_id=assignment.schedule_id,
            actor_type="SYSTEM",
            actor_id=None,
            action_type="BOUNDARY_CHECK",
            event_summary=f"Agent boundary check passed for agent {assignment.agent_id}",
            event_payload={"agent_id": str(assignment.agent_id), "requested_tool": requested_tool},
            db=db
        )
        return True, None

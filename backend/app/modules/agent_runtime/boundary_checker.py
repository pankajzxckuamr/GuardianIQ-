from uuid import UUID
import sqlalchemy as sa
from sqlalchemy.future import select

from app.modules.registry.models import RegistryWorkflow, RegistryAIAgent, RegistryAIModel
from app.modules.audit.event_service import GovernanceEventService
from app.modules.audit.event_codes import WorkflowEventCode
from app.shared.db_compat import db_get, execute_statement

EXECUTION_MODE_RANK = {
    "READ_ONLY": 1,
    "RECOMMEND_ONLY": 2,
    "APPROVAL_REQUIRED": 3,
    "LIMITED_EXECUTION": 4,
    "FULLY_BLOCKED": 5
}

class BoundaryChecker:
    def __init__(self):
        self.event_service = GovernanceEventService()

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

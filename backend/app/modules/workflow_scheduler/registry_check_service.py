from uuid import UUID
import sqlalchemy as sa
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.modules.registry.models import RegistryWorkflow, RegistryAIAgent, RegistryAIModel, RegistryAITool, RegistryAIAgentToolMapping

class RegistryCheckService:
    @classmethod
    async def get_active_agent(cls, agent_id: UUID, db: Session):
        stmt = sa.select(RegistryAIAgent).where(RegistryAIAgent.id == agent_id, RegistryAIAgent.is_deleted == False)
        from app.shared.db_compat import execute_statement
        res = await execute_statement(db, stmt)
        agent = res.scalar()
        if not agent or agent.status != "ACTIVE":
            raise HTTPException(status_code=422, detail="Agent not found or not ACTIVE")
        return agent

    @classmethod
    async def get_active_model(cls, model_id: UUID, db: Session):
        stmt = sa.select(RegistryAIModel).where(RegistryAIModel.id == model_id, RegistryAIModel.is_deleted == False)
        from app.shared.db_compat import execute_statement
        res = await execute_statement(db, stmt)
        model = res.scalar()
        if not model or model.status != "ACTIVE":
            raise HTTPException(status_code=422, detail="Model not found or not ACTIVE")
        return model

    @classmethod
    async def get_active_workflow(cls, workflow_id: UUID, db: Session):
        stmt = sa.select(RegistryWorkflow).where(RegistryWorkflow.id == workflow_id, RegistryWorkflow.is_deleted == False)
        from app.shared.db_compat import execute_statement
        res = await execute_statement(db, stmt)
        workflow = res.scalar()
        if not workflow or workflow.status != "ACTIVE":
            raise HTTPException(status_code=422, detail="Workflow not found or not ACTIVE")
        return workflow

    @classmethod
    def get_agent_max_execution_mode(cls, agent: RegistryAIAgent) -> str:
        return agent.execution_mode.value if hasattr(agent.execution_mode, "value") else str(agent.execution_mode)

    @classmethod
    async def get_agent_allowed_tools(cls, agent_id: UUID, db: Session) -> list[str]:
        stmt = (
            sa.select(RegistryAITool.tool_name)
            .join(RegistryAIAgentToolMapping, RegistryAIAgentToolMapping.tool_id == RegistryAITool.id)
            .where(
                RegistryAIAgentToolMapping.agent_id == agent_id,
                RegistryAIAgentToolMapping.is_deleted == False,
                RegistryAITool.is_deleted == False,
                RegistryAITool.status == "ACTIVE"
            )
        )
        from app.shared.db_compat import execute_statement
        res = await execute_statement(db, stmt)
        return [row[0] for row in res.fetchall()]

    @classmethod
    async def check_tool_is_write_capable(cls, tool_name: str, db: Session) -> bool:
        stmt = sa.select(RegistryAITool).where(
            RegistryAITool.tool_name == tool_name,
            RegistryAITool.is_deleted == False
        )
        from app.shared.db_compat import execute_statement
        res = await execute_statement(db, stmt)
        tool = res.scalar()
        if not tool:
            return False
        
        cap = tool.capability_type.value if hasattr(tool.capability_type, "value") else str(tool.capability_type)
        return cap in ["WRITE", "EXECUTE"]

from uuid import UUID
import sqlalchemy as sa
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.modules.registry.models import RegistryWorkflow, RegistryAIAgent, RegistryAIModel, RegistryTool, RegistryRelationship, RegistryRegisterAll

class RegistryCheckService:
    @classmethod
    async def get_active_agent(cls, agent_id: UUID, db: Session):
        stmt = sa.select(RegistryAIAgent).where(RegistryAIAgent.id == agent_id)
        from app.shared.db_compat import execute_statement
        res = await execute_statement(db, stmt)
        agent = res.scalar()
        if not agent or agent.status != "ACTIVE":
            raise HTTPException(status_code=422, detail="Agent not found or not ACTIVE")
        return agent

    @classmethod
    async def get_active_model(cls, model_id: UUID, db: Session):
        stmt = sa.select(RegistryAIModel).where(RegistryAIModel.id == model_id)
        from app.shared.db_compat import execute_statement
        res = await execute_statement(db, stmt)
        model = res.scalar()
        if not model or model.status != "ACTIVE":
            raise HTTPException(status_code=422, detail="Model not found or not ACTIVE")
        return model

    @classmethod
    async def get_active_workflow(cls, workflow_id: UUID, db: Session):
        stmt = sa.select(RegistryWorkflow).where(RegistryWorkflow.id == workflow_id)
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
        from app.shared.db_compat import execute_statement
        
        tool_identifiers = set()
        
        # 1. Query via RegistryRegisterAll (bundles where agent is linked to tools)
        stmt1 = (
            sa.select(RegistryTool.tool_code, RegistryTool.tool_name)
            .join(RegistryRegisterAll, RegistryRegisterAll.tool_id == RegistryTool.id)
            .where(
                RegistryRegisterAll.agent_id == agent_id,
                RegistryTool.status == "ACTIVE"
            )
        )
        res1 = await execute_statement(db, stmt1)
        for row in res1.fetchall():
            tool_identifiers.add(row[0]) # tool_code
            tool_identifiers.add(row[1]) # tool_name
            
        # 2. Query direct AGENT -> TOOL relationships
        stmt2 = (
            sa.select(RegistryTool.tool_code, RegistryTool.tool_name)
            .join(RegistryRelationship, RegistryRelationship.target_entity_id == RegistryTool.id)
            .where(
                RegistryRelationship.source_entity_type == "AGENT",
                RegistryRelationship.source_entity_id == agent_id,
                RegistryRelationship.target_entity_type == "TOOL",
                RegistryRelationship.relationship_type == "USES",
                RegistryRelationship.status == "ACTIVE",
                RegistryTool.status == "ACTIVE"
            )
        )
        res2 = await execute_statement(db, stmt2)
        for row in res2.fetchall():
            tool_identifiers.add(row[0]) # tool_code
            tool_identifiers.add(row[1]) # tool_name
            
        # 3. Query indirect AGENT -> WORKFLOW -> TOOL relationships
        # First get workflows executed by agent
        stmt3_wf = (
            sa.select(RegistryRelationship.target_entity_id)
            .where(
                RegistryRelationship.source_entity_type == "AGENT",
                RegistryRelationship.source_entity_id == agent_id,
                RegistryRelationship.target_entity_type == "WORKFLOW",
                RegistryRelationship.relationship_type == "EXECUTES",
                RegistryRelationship.status == "ACTIVE"
            )
        )
        res3_wf = await execute_statement(db, stmt3_wf)
        wf_ids = [row[0] for row in res3_wf.fetchall()]
        
        if wf_ids:
            stmt3_tools = (
                sa.select(RegistryTool.tool_code, RegistryTool.tool_name)
                .join(RegistryRelationship, RegistryRelationship.target_entity_id == RegistryTool.id)
                .where(
                    RegistryRelationship.source_entity_type == "WORKFLOW",
                    RegistryRelationship.source_entity_id.in_(wf_ids),
                    RegistryRelationship.target_entity_type == "TOOL",
                    RegistryRelationship.relationship_type == "USES",
                    RegistryRelationship.status == "ACTIVE",
                    RegistryTool.status == "ACTIVE"
                )
            )
            res3_tools = await execute_statement(db, stmt3_tools)
            for row in res3_tools.fetchall():
                tool_identifiers.add(row[0]) # tool_code
                tool_identifiers.add(row[1]) # tool_name
                
        return list(tool_identifiers)

    @classmethod
    async def check_tool_is_write_capable(cls, tool_name_or_code: str, db: Session) -> bool:
        stmt = sa.select(RegistryTool).where(
            sa.or_(
                RegistryTool.tool_name == tool_name_or_code,
                RegistryTool.tool_code == tool_name_or_code
            ),
            RegistryTool.status == "ACTIVE"
        )
        from app.shared.db_compat import execute_statement
        res = await execute_statement(db, stmt)
        tool = res.scalar()
        if not tool:
            return False
        
        cap = tool.access_mode.value if hasattr(tool.access_mode, "value") else str(tool.access_mode)
        return cap in ["WRITE", "EXECUTE", "ADMIN"]

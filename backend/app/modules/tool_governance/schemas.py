from typing import Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel
from app.modules.policy_engine.enums import AccessMode


class ToolCapabilityCreate(BaseModel):
    tool_id: UUID
    capability_name: str
    description: Optional[str] = None
    access_mode: AccessMode = AccessMode.EXECUTE
    requires_approval: bool = False
    input_schema_json: Optional[Dict[str, Any]] = None
    rate_limit: Optional[int] = None


class AgentToolPermissionCreate(BaseModel):
    agent_id: UUID
    tool_id: UUID
    capability_id: Optional[UUID] = None
    permission_level: str = "EXECUTE"
    max_calls_per_run: Optional[int] = None
    require_approval: bool = False
    is_active: bool = True

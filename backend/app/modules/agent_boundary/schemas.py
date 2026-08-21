from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field
from app.modules.policy_engine.enums import AutonomyLevel, AccessMode


class AgentRuntimeBoundaryCreate(BaseModel):
    agent_id: UUID
    max_autonomy_level: AutonomyLevel = AutonomyLevel.HUMAN_SUPERVISED
    allowed_access_modes_json: List[AccessMode] = Field(default_factory=lambda: [AccessMode.READ_ONLY])
    rate_limit_per_minute: Optional[int] = 120
    max_concurrency: Optional[int] = 5
    allow_sub_agent_spawn: bool = False
    require_approval_threshold: Optional[float] = None
    is_active: bool = True


class AgentRuntimeBoundaryResponse(BaseModel):
    id: UUID
    agent_id: UUID
    max_autonomy_level: str
    allowed_access_modes_json: List[str]
    rate_limit_per_minute: Optional[int]
    max_concurrency: Optional[int]
    allow_sub_agent_spawn: bool
    require_approval_threshold: Optional[float]
    is_active: bool

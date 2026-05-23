from pydantic import BaseModel
from typing import Optional
from app.shared.enums.execution_mode import ExecutionMode

class AgentBase(BaseModel):
    agent_name: str
    description: Optional[str] = None
    execution_mode: Optional[ExecutionMode] = ExecutionMode.APPROVAL_REQUIRED
    ai_model_id: Optional[int] = None

class AgentCreate(AgentBase):
    pass

class AgentUpdate(BaseModel):
    agent_name: Optional[str] = None
    description: Optional[str] = None
    execution_mode: Optional[ExecutionMode] = None
    ai_model_id: Optional[int] = None

class AgentResponse(AgentBase):
    id: int

    class Config:
        from_attributes = True

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict

class AuthorizationRequest(BaseModel):
    subject_user_id: UUID | None = None
    subject_agent_id: UUID | None = None
    subject_type: str | None = None
    object_type: str
    object_id: UUID | None = None
    action: str
    context_json: dict | None = None

    model_config = ConfigDict(from_attributes=True)


class AuthorizationResponse(BaseModel):
    allowed: bool
    decision: str
    rbac_result: dict
    abac_result: dict
    relationship_result: dict
    deny_reasons: list[str]
    evaluated_at: datetime

    model_config = ConfigDict(from_attributes=True)

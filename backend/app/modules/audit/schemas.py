from typing import Optional
from datetime import datetime

from pydantic import BaseModel


class AuditEventCreate(BaseModel):
    event_type: str

    entity_type: str

    entity_id: Optional[int] = None

    actor_user_id: Optional[int] = None

    action: str

    event_metadata: Optional[dict] = None


class AuditEventResponse(BaseModel):
    id: int

    event_type: str

    entity_type: str

    entity_id: Optional[int]

    actor_user_id: Optional[int]

    action: str

    event_metadata: Optional[dict]

    created_at: datetime

    class Config:
        from_attributes = True

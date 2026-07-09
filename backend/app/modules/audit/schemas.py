from typing import Optional
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel

class AuditEventCreate(BaseModel):
    event_type: str

    entity_type: str

    entity_id: Optional[str] = None

    actor_user_id: Optional[UUID] = None

    action: str

    event_metadata: Optional[dict] = None


class AuditEventResponse(BaseModel):
    id: int
    event_type: str
    entity_type: str
    entity_id: Optional[str] = None
    actor_user_id: Optional[UUID] = None
    actor_username: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    status: str = "success"
    detail: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AuditEventPaginated(BaseModel):
    items: list[AuditEventResponse]
    total: int
    page: int
    per_page: int
    pages: int


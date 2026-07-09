from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from app.db.session import Base

class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(Integer, primary_key=True, index=True)

    event_type = Column(
        String,
        nullable=False
    )

    entity_type = Column(
        String,
        nullable=False
    )

    entity_id = Column(String(100), nullable=True)

    actor_user_id = Column(UUID(as_uuid=True))

    action = Column(
        String,
        nullable=False
    )

    event_metadata = Column(JSON)

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        index=True
    )

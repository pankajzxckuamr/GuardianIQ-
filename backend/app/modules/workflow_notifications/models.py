from sqlalchemy import Column, String, Text, TIMESTAMP, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.shared.mixins import WorkflowBaseMixin

class WorkflowNotification(Base, WorkflowBaseMixin):
    __tablename__ = "workflow_notifications"


    recipient_user_id = Column(UUID(as_uuid=True), ForeignKey("guardian_users.id"), nullable=False)
    notification_type = Column(String(100), nullable=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=True)
    severity = Column(String(50), server_default="MEDIUM", nullable=True, default="MEDIUM")
    entity_type = Column("related_entity_type", String(100), nullable=True)
    entity_id = Column("related_entity_id", UUID(as_uuid=True), nullable=True)
    status = Column(String(50), server_default="UNREAD", nullable=True, default="UNREAD")
    read_at = Column(TIMESTAMP(timezone=True), nullable=True)
    acknowledged_at = Column(TIMESTAMP(timezone=True), nullable=True)

    # Relationships
    recipient_user = relationship("GuardianUser", foreign_keys=[recipient_user_id])

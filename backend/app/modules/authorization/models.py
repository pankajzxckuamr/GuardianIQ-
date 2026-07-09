from sqlalchemy import Column, String, TIMESTAMP, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.shared.mixins import WorkflowBaseMixin

class WorkflowAuthorizationDecision(Base, WorkflowBaseMixin):
    __tablename__ = "workflow_authorization_decisions"


    subject_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    subject_agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=True)
    subject_type = Column(String(50), nullable=True)
    object_type = Column(String(100), nullable=True)
    object_id = Column(UUID(as_uuid=True), nullable=True)
    action = Column(String(100), nullable=True)
    decision = Column(String(20), nullable=False)
    reason_json = Column(JSONB, server_default="{}", nullable=True, default=None)
    rbac_result = Column(JSONB, server_default="{}", nullable=True, default=None)
    abac_result = Column(JSONB, server_default="{}", nullable=True, default=None)
    relationship_result = Column(JSONB, server_default="{}", nullable=True, default=None)
    evaluated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=True)

    # Relationships
    subject_user = relationship("User", foreign_keys=[subject_user_id])
    subject_agent = relationship("Agent", foreign_keys=[subject_agent_id])


class WorkflowDelegation(Base, WorkflowBaseMixin):
    __tablename__ = "workflow_delegations"


    delegator_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    delegatee_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    start_at = Column(TIMESTAMP(timezone=True), nullable=False)
    end_at = Column(TIMESTAMP(timezone=True), nullable=False)
    status = Column(String(50), server_default="ACTIVE", nullable=True, default="ACTIVE")

    # Relationships
    delegator = relationship("User", foreign_keys=[delegator_user_id])
    delegatee = relationship("User", foreign_keys=[delegatee_user_id])


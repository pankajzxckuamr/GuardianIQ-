from uuid import uuid4
from sqlalchemy import Column, String, Boolean, Integer, Numeric, Text, TIMESTAMP, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.shared.mixins import WorkflowBaseMixin

class GenericRelationship(Base, WorkflowBaseMixin):
    __tablename__ = "generic_relationships"

    source_type = Column(String(100), nullable=False, index=True)
    source_id = Column(String(255), nullable=False, index=True)
    relationship_type = Column(String(100), nullable=False, index=True)
    target_type = Column(String(100), nullable=False, index=True)
    target_id = Column(String(255), nullable=False, index=True)
    relationship_scope = Column(String(255), nullable=True)
    scope_json = Column(JSONB, nullable=True)
    responsibility_type = Column(String(100), nullable=True)
    effective_from = Column(TIMESTAMP(timezone=True), nullable=False)
    effective_to = Column(TIMESTAMP(timezone=True), nullable=True)
    status = Column(String(50), nullable=False, default="PROPOSED")
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

class ObjectResponsibility(Base, WorkflowBaseMixin):
    __tablename__ = "object_responsibilities"

    object_type = Column(String(100), nullable=False, index=True)
    object_id = Column(String(255), nullable=False, index=True)
    actor_type = Column(String(50), nullable=False)
    actor_id = Column(String(255), nullable=False, index=True)
    responsibility_type = Column(String(50), nullable=False)
    is_primary = Column(Boolean, nullable=False, default=False)
    effective_from = Column(TIMESTAMP(timezone=True), nullable=False)
    effective_to = Column(TIMESTAMP(timezone=True), nullable=True)
    status = Column(String(50), nullable=False, default="ACTIVE")

class RelationshipValidationResult(Base):
    __tablename__ = "relationship_validation_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    request_id = Column(String(150), nullable=False, index=True)
    relationship_id = Column(UUID(as_uuid=True), nullable=True)
    validation_rule_id = Column(String(50), nullable=False)
    validation_status = Column(String(50), nullable=False)
    severity = Column(String(50), nullable=False)
    message = Column(Text, nullable=False)
    resolution_hint = Column(Text, nullable=True)
    payload_json = Column(JSONB, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

class RelationshipGraphSnapshot(Base):
    __tablename__ = "relationship_graph_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    root_object_type = Column(String(100), nullable=False, index=True)
    root_object_id = Column(String(255), nullable=False, index=True)
    depth = Column(Integer, nullable=False)
    snapshot_json = Column(JSONB, nullable=False)
    generated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(TIMESTAMP(timezone=True), nullable=False)

class PolicyBinding(Base, WorkflowBaseMixin):
    __tablename__ = "policy_bindings"

    policy_id = Column(UUID(as_uuid=True), ForeignKey("policies.id"), nullable=False)
    target_type = Column(String(100), nullable=False, index=True)
    target_id = Column(String(255), nullable=False, index=True)
    binding_scope = Column(String(255), nullable=True)
    priority = Column(Integer, nullable=False, default=0)
    is_mandatory = Column(Boolean, nullable=False, default=True)
    effective_from = Column(TIMESTAMP(timezone=True), nullable=False)
    effective_to = Column(TIMESTAMP(timezone=True), nullable=True)
    status = Column(String(50), nullable=False, default="ACTIVE")

class EvidenceLink(Base, WorkflowBaseMixin):
    __tablename__ = "evidence_links"

    evidence_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    target_type = Column(String(100), nullable=False, index=True)
    target_id = Column(String(255), nullable=False, index=True)
    link_type = Column(String(100), nullable=False)
    confidence_score = Column(Numeric(5, 2), nullable=True)
    source_system = Column(String(150), nullable=True)

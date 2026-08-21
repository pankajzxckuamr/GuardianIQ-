from uuid import uuid4
from sqlalchemy import (
    Column,
    String,
    Boolean,
    Integer,
    Numeric,
    Text,
    TIMESTAMP,
    ForeignKey,
    func,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.db.session import Base
from app.shared.mixins import GovernableMixin, WorkflowBaseMixin


class GovernancePolicy(Base, GovernableMixin):
    __tablename__ = "governance_policies"

    policy_code = Column(String(100), nullable=False, unique=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=False, default="GENERAL")
    enforcement_mode = Column(String(50), nullable=False, default="BLOCKING")
    priority = Column(Integer, nullable=False, default=100)
    effective_from = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now())
    effective_to = Column(TIMESTAMP(timezone=True), nullable=True)

    # Relationships
    versions = relationship("PolicyVersion", back_populates="policy", cascade="all, delete-orphan")
    exceptions = relationship("PolicyException", back_populates="policy", cascade="all, delete-orphan")


class PolicyVersion(Base, WorkflowBaseMixin):
    __tablename__ = "policy_versions"

    policy_id = Column(UUID(as_uuid=True), ForeignKey("governance_policies.id", ondelete="CASCADE"), nullable=False, index=True)
    version_number = Column(Integer, nullable=False)
    status = Column(String(50), nullable=False, default="DRAFT")  # DRAFT, ACTIVE, DEPRECATED, ARCHIVED
    changelog = Column(Text, nullable=True)
    rules_count = Column(Integer, nullable=False, default=0)
    activated_at = Column(TIMESTAMP(timezone=True), nullable=True)
    activated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    checksum = Column(String(64), nullable=True)

    # Relationships
    policy = relationship("GovernancePolicy", back_populates="versions")
    rules = relationship("PolicyRule", back_populates="version", cascade="all, delete-orphan")


class PolicyRule(Base, WorkflowBaseMixin):
    __tablename__ = "policy_rules"

    policy_version_id = Column(UUID(as_uuid=True), ForeignKey("policy_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    rule_code = Column(String(100), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    rule_type = Column(String(100), nullable=False)  # TOOL_BOUNDARY, DATA_ACCESS, RATE_LIMIT, AUTONOMY
    target_type = Column(String(100), nullable=False)  # AGENT, TOOL, DATA_SOURCE, WORKFLOW, MODEL
    target_id = Column(String(255), nullable=True)  # Target entity ID or '*'
    condition_expression = Column(Text, nullable=True)
    condition_json = Column(JSONB, nullable=False, default=dict)
    action = Column(String(50), nullable=False, default="DENY")  # ALLOW, DENY, MODIFY, REQUIRE_APPROVAL
    severity = Column(String(50), nullable=False, default="HIGH")  # LOW, MEDIUM, HIGH, CRITICAL
    execution_order = Column(Integer, nullable=False, default=10)
    is_active = Column(Boolean, nullable=False, default=True)

    # Relationships
    version = relationship("PolicyVersion", back_populates="rules")


class PolicyException(Base, WorkflowBaseMixin):
    __tablename__ = "policy_exceptions"

    policy_id = Column(UUID(as_uuid=True), ForeignKey("governance_policies.id", ondelete="CASCADE"), nullable=False, index=True)
    policy_version_id = Column(UUID(as_uuid=True), ForeignKey("policy_versions.id", ondelete="SET NULL"), nullable=True)
    target_type = Column(String(100), nullable=False, index=True)
    target_id = Column(String(255), nullable=False, index=True)
    reason = Column(Text, nullable=False)
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    valid_from = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now())
    valid_to = Column(TIMESTAMP(timezone=True), nullable=False)
    status = Column(String(50), nullable=False, default="ACTIVE")  # ACTIVE, EXPIRED, REVOKED

    # Relationships
    policy = relationship("GovernancePolicy", back_populates="exceptions")


class PolicyEvaluation(Base, WorkflowBaseMixin):
    __tablename__ = "policy_evaluations"

    request_id = Column(String(150), nullable=False, index=True)
    correlation_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    causation_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    policy_id = Column(UUID(as_uuid=True), ForeignKey("governance_policies.id"), nullable=False, index=True)
    policy_version_id = Column(UUID(as_uuid=True), ForeignKey("policy_versions.id"), nullable=True)
    target_type = Column(String(100), nullable=False, index=True)
    target_id = Column(String(255), nullable=False, index=True)
    trigger_event = Column(String(100), nullable=False)
    decision = Column(String(50), nullable=False)  # ALLOW, DENY, MODIFY, REQUIRE_APPROVAL
    reasons_json = Column(JSONB, nullable=True)
    evaluation_latency_ms = Column(Numeric(10, 2), nullable=True)
    context_snapshot_json = Column(JSONB, nullable=True)

    # Relationships
    rule_evaluations = relationship("PolicyRuleEvaluation", back_populates="evaluation", cascade="all, delete-orphan")


class PolicyRuleEvaluation(Base, WorkflowBaseMixin):
    __tablename__ = "policy_rule_evaluations"

    evaluation_id = Column(UUID(as_uuid=True), ForeignKey("policy_evaluations.id", ondelete="CASCADE"), nullable=False, index=True)
    rule_id = Column(UUID(as_uuid=True), ForeignKey("policy_rules.id", ondelete="CASCADE"), nullable=False, index=True)
    matched = Column(Boolean, nullable=False)
    decision = Column(String(50), nullable=False)
    reason = Column(Text, nullable=True)
    execution_order = Column(Integer, nullable=False, default=10)
    latency_ms = Column(Numeric(10, 2), nullable=True)

    # Relationships
    evaluation = relationship("PolicyEvaluation", back_populates="rule_evaluations")


class EnforcementDecision(Base, WorkflowBaseMixin):
    __tablename__ = "enforcement_decisions"

    request_id = Column(String(150), nullable=False, index=True)
    correlation_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=True, index=True)
    workflow_run_id = Column(UUID(as_uuid=True), ForeignKey("workflow_runs.id"), nullable=True, index=True)
    tool_id = Column(UUID(as_uuid=True), ForeignKey("tools.id"), nullable=True, index=True)
    decision = Column(String(50), nullable=False)
    execution_permitted = Column(Boolean, nullable=False, default=True)
    modified_payload_json = Column(JSONB, nullable=True)
    violations_json = Column(JSONB, nullable=True)
    approval_required = Column(Boolean, nullable=False, default=False)
    enforced_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())


class PolicyApproval(Base, WorkflowBaseMixin):
    __tablename__ = "policy_approvals"

    request_id = Column(String(150), nullable=False, index=True)
    correlation_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    policy_id = Column(UUID(as_uuid=True), ForeignKey("governance_policies.id"), nullable=False, index=True)
    evaluation_id = Column(UUID(as_uuid=True), ForeignKey("policy_evaluations.id"), nullable=True, index=True)
    approval_tier = Column(Integer, nullable=False, default=1)
    required_role = Column(String(100), nullable=False)
    status = Column(String(50), nullable=False, default="PENDING")  # PENDING, APPROVED, REJECTED, EXPIRED
    approver_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    decision_reason = Column(Text, nullable=True)
    timeout_at = Column(TIMESTAMP(timezone=True), nullable=False)

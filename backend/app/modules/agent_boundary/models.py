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
from app.shared.mixins import WorkflowBaseMixin


class AgentRuntimeBoundary(Base, WorkflowBaseMixin):
    __tablename__ = "agent_runtime_boundaries"

    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    max_autonomy_level = Column(String(50), nullable=False, default="HUMAN_SUPERVISED")
    allowed_access_modes_json = Column(JSONB, nullable=False, default=list)
    rate_limit_per_minute = Column(Integer, nullable=True)
    max_concurrency = Column(Integer, nullable=True, default=5)
    allow_sub_agent_spawn = Column(Boolean, nullable=False, default=False)
    require_approval_threshold = Column(Numeric(12, 2), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)


class ToolCapability(Base, WorkflowBaseMixin):
    __tablename__ = "tool_capabilities"

    tool_id = Column(UUID(as_uuid=True), ForeignKey("tools.id", ondelete="CASCADE"), nullable=False, index=True)
    capability_name = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    access_mode = Column(String(50), nullable=False, default="EXECUTE")
    requires_approval = Column(Boolean, nullable=False, default=False)
    input_schema_json = Column(JSONB, nullable=True)
    rate_limit = Column(Integer, nullable=True)


class AgentToolPermission(Base, WorkflowBaseMixin):
    __tablename__ = "agent_tool_permissions"

    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)
    tool_id = Column(UUID(as_uuid=True), ForeignKey("tools.id", ondelete="CASCADE"), nullable=False, index=True)
    capability_id = Column(UUID(as_uuid=True), ForeignKey("tool_capabilities.id", ondelete="CASCADE"), nullable=True, index=True)
    permission_level = Column(String(50), nullable=False, default="EXECUTE")
    max_calls_per_run = Column(Integer, nullable=True)
    require_approval = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)


class DataSourceField(Base, WorkflowBaseMixin):
    __tablename__ = "data_source_fields"

    data_source_id = Column(UUID(as_uuid=True), ForeignKey("data_sources.id", ondelete="CASCADE"), nullable=False, index=True)
    field_name = Column(String(255), nullable=False)
    data_type = Column(String(100), nullable=False, default="STRING")
    classification = Column(String(50), nullable=False, default="INTERNAL")
    sensitivity_level = Column(String(50), nullable=False, default="MEDIUM")
    is_pii = Column(Boolean, nullable=False, default=False)
    masking_strategy = Column(String(50), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)


class AgentDataPermission(Base, WorkflowBaseMixin):
    __tablename__ = "agent_data_permissions"

    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)
    data_source_id = Column(UUID(as_uuid=True), ForeignKey("data_sources.id", ondelete="CASCADE"), nullable=False, index=True)
    field_id = Column(UUID(as_uuid=True), ForeignKey("data_source_fields.id", ondelete="CASCADE"), nullable=True, index=True)
    allowed_operations_json = Column(JSONB, nullable=False, default=list)
    max_classification = Column(String(50), nullable=False, default="CONFIDENTIAL")
    max_sensitivity = Column(String(50), nullable=False, default="HIGH")
    is_active = Column(Boolean, nullable=False, default=True)


class RuntimeAuthorization(Base, WorkflowBaseMixin):
    __tablename__ = "runtime_authorizations"

    request_id = Column(String(150), nullable=False, index=True)
    correlation_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False, index=True)
    operation = Column(String(100), nullable=False)
    authorized = Column(Boolean, nullable=False)
    reason = Column(Text, nullable=True)
    expires_at = Column(TIMESTAMP(timezone=True), nullable=True)


class RuntimeEnforcementLog(Base, WorkflowBaseMixin):
    __tablename__ = "runtime_enforcement_log"

    request_id = Column(String(150), nullable=False, index=True)
    correlation_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    causation_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=True, index=True)
    tool_id = Column(UUID(as_uuid=True), ForeignKey("tools.id"), nullable=True, index=True)
    decision = Column(String(50), nullable=False)
    action_taken = Column(String(100), nullable=False)
    latency_ms = Column(Numeric(10, 2), nullable=True)

"""
SQLAlchemy ORM models for Phase 4 Governance Event Store & Auxiliary Tables
WBS Reference: 4.2.1, 4.3.2
"""
from uuid import uuid4
from sqlalchemy import Column, String, Integer, Boolean, Text, ForeignKey, TIMESTAMP, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.db.session import Base

class GovernanceEvent(Base):
    __tablename__ = "governance_events"

    event_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, server_default=func.gen_random_uuid())
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    event_type = Column(String(100), nullable=False, index=True)
    event_category = Column(String(50), nullable=False, index=True)
    event_version = Column(String(20), nullable=False, server_default="1.0")
    
    occurred_at = Column(TIMESTAMP(timezone=True), nullable=False, index=True)
    recorded_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    
    source_service = Column(String(100), nullable=False)
    source_system = Column(String(100), nullable=False, server_default="guardianiq-backend")
    
    actor_json = Column(JSONB, nullable=False)
    subject_json = Column(JSONB, nullable=False)
    
    correlation_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    causation_id = Column(UUID(as_uuid=True), nullable=True)
    
    risk_context_json = Column(JSONB, nullable=True)
    policy_context_json = Column(JSONB, nullable=True)
    
    payload_json = Column(JSONB, nullable=False)
    classification = Column(String(50), nullable=False, server_default="INTERNAL")
    retention_class = Column(String(50), nullable=False, server_default="STANDARD_90_DAYS")
    
    event_hash = Column(String(64), nullable=False)
    previous_event_hash = Column(String(64), nullable=True)


class EventOutbox(Base):
    __tablename__ = "event_outbox"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, server_default=func.gen_random_uuid())
    event_id = Column(UUID(as_uuid=True), ForeignKey("governance_events.event_id", ondelete="CASCADE"), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    destination = Column(String(100), nullable=False, server_default="internal_bus")
    payload_json = Column(JSONB, nullable=False)
    
    status = Column(String(30), nullable=False, server_default="PENDING")
    retry_count = Column(Integer, nullable=False, server_default="0")
    max_retries = Column(Integer, nullable=False, server_default="5")
    
    error_message = Column(Text, nullable=True)
    
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    dispatched_at = Column(TIMESTAMP(timezone=True), nullable=True)
    next_retry_at = Column(TIMESTAMP(timezone=True), nullable=True)


class EventProcessingLog(Base):
    __tablename__ = "event_processing_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, server_default=func.gen_random_uuid())
    event_id = Column(UUID(as_uuid=True), ForeignKey("governance_events.event_id", ondelete="CASCADE"), nullable=False, index=True)
    consumer_id = Column(String(100), nullable=False)
    
    status = Column(String(30), nullable=False, server_default="PROCESSED")
    processed_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    execution_time_ms = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)


class EventDeadLetter(Base):
    __tablename__ = "event_dead_letter"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, server_default=func.gen_random_uuid())
    outbox_id = Column(UUID(as_uuid=True), ForeignKey("event_outbox.id", ondelete="CASCADE"), nullable=False)
    event_id = Column(UUID(as_uuid=True), ForeignKey("governance_events.event_id", ondelete="CASCADE"), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    failure_reason = Column(Text, nullable=False)
    failed_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    retry_attempts = Column(Integer, nullable=False)
    
    status = Column(String(30), nullable=False, server_default="UNRESOLVED")
    resolved_at = Column(TIMESTAMP(timezone=True), nullable=True)
    resolved_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)


class EventSchemaRegistry(Base):
    __tablename__ = "event_schema_registry"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, server_default=func.gen_random_uuid())
    event_type = Column(String(100), nullable=False)
    version = Column(String(20), nullable=False, server_default="1.0")
    
    json_schema = Column(JSONB, nullable=False)
    is_active = Column(Boolean, nullable=False, server_default="true")
    
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)


class EventRetentionRule(Base):
    __tablename__ = "event_retention_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, server_default=func.gen_random_uuid())
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    event_category = Column(String(50), nullable=False)
    retention_days = Column(Integer, nullable=False, server_default="90")
    action = Column(String(30), nullable=False, server_default="PURGE")
    
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())


class EventExportLog(Base):
    __tablename__ = "event_export_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, server_default=func.gen_random_uuid())
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    exported_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    filter_params_json = Column(JSONB, nullable=False)
    format = Column(String(20), nullable=False, server_default="JSON")
    record_count = Column(Integer, nullable=False, server_default="0")
    file_hash = Column(String(64), nullable=True)
    
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

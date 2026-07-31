"""
Pydantic Schemas for Phase 4 Governance Event Store & API Contracts
WBS Reference: 4.3.1
"""
from datetime import datetime
from uuid import UUID, uuid4
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, ConfigDict

# 1. Actor & Subject Context Schemas
class ActorContext(BaseModel):
    user_id: UUID
    roles: List[str] = Field(default_factory=list)
    ip_address: Optional[str] = None

class SubjectContext(BaseModel):
    entity_type: str
    entity_id: str
    entity_name: Optional[str] = None

# 2. Event Creation Ingest Request
class GovernanceEventCreate(BaseModel):
    event_type: str = Field(..., max_length=100)
    event_category: str = Field(..., max_length=50)
    event_version: str = Field(default="1.0", max_length=20)
    occurred_at: datetime
    source_service: str = Field(..., max_length=100)
    source_system: str = Field(default="guardianiq-backend", max_length=100)
    
    actor_json: Dict[str, Any]
    subject_json: Dict[str, Any]
    
    correlation_id: Optional[UUID] = None
    causation_id: Optional[UUID] = None
    
    risk_context_json: Optional[Dict[str, Any]] = None
    policy_context_json: Optional[Dict[str, Any]] = None
    
    payload_json: Dict[str, Any]
    classification: str = Field(default="INTERNAL", max_length=50)
    retention_class: str = Field(default="STANDARD_90_DAYS", max_length=50)
    previous_event_hash: Optional[str] = Field(None, min_length=64, max_length=64)

# 3. Canonical 20-Field Governance Event Response
class GovernanceEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    event_id: UUID
    tenant_id: UUID
    event_type: str
    event_category: str
    event_version: str
    occurred_at: datetime
    recorded_at: datetime
    source_service: str
    source_system: str
    actor_json: Dict[str, Any]
    subject_json: Dict[str, Any]
    correlation_id: Optional[UUID] = None
    causation_id: Optional[UUID] = None
    risk_context_json: Optional[Dict[str, Any]] = None
    policy_context_json: Optional[Dict[str, Any]] = None
    payload_json: Dict[str, Any]
    classification: str
    retention_class: str
    event_hash: str
    previous_event_hash: Optional[str] = None

# 4. Search Filter Parameters (Matching Spec Section 6.3)
class GovernanceEventSearchFilter(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    event_type: Optional[str] = None
    event_category: Optional[str] = None
    subject_type: Optional[str] = None
    subject_id: Optional[str] = None
    actor_id: Optional[str] = None
    correlation_id: Optional[UUID] = None
    risk_level: Optional[str] = None
    source_service: Optional[str] = None
    classification: Optional[str] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=500)

# 5. Timeline Reconstruction Response
class TimelineResponse(BaseModel):
    subject_type: Optional[str] = None
    subject_id: Optional[str] = None
    correlation_id: Optional[UUID] = None
    total_events: int
    events: List[GovernanceEventResponse]

# 6. Event Outbox Queue Record Response
class EventOutboxResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    event_id: UUID
    tenant_id: UUID
    destination: str
    payload_json: Dict[str, Any]
    status: str
    retry_count: int
    max_retries: int
    error_message: Optional[str] = None
    created_at: datetime
    dispatched_at: Optional[datetime] = None
    next_retry_at: Optional[datetime] = None

# 7. Dead Letter Queue (DLQ) Record Response
class EventDeadLetterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    outbox_id: UUID
    event_id: UUID
    tenant_id: UUID
    failure_reason: str
    failed_at: datetime
    retry_attempts: int
    status: str
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[UUID] = None

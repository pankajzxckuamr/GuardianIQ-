"""
FastAPI REST API Router for Phase 4 Governance Event Store
WBS Reference: 4.3.5
Endpoints: /api/v1/events
"""
from typing import Optional
from uuid import UUID
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.models import User
from app.modules.auth.dependencies import get_current_user, require_permission
from app.shared.response_utils import ResponseHelper
from app.modules.events.schemas import (
    GovernanceEventCreate,
    GovernanceEventResponse,
    GovernanceEventSearchFilter,
    TimelineResponse
)
from app.modules.events.service import EventPublisherService, EventMetricsService
from app.modules.events.repository import EventRepository
from app.modules.audit.export_service import AuditExportService
from app.modules.audit.timeline_service import AuditTimelineService

router = APIRouter(prefix="/api/v1/events", tags=["Governance Events"])
publisher_service = EventPublisherService()

@router.get("/metrics")
def get_event_metrics_api(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("VIEW_EVENTS"))
):
    """
    Get aggregated dashboard event metrics (counts by type/category, violations, SLA breaches, outbox lag, DLQ count).
    Strict tenant isolation manually enforced on every query.
    """
    tenant_id = current_user.id
    metrics = EventMetricsService.get_dashboard_metrics(db, tenant_id)
    return ResponseHelper.success(
        data=metrics,
        message="Governance event metrics retrieved successfully"
    )

@router.post("", status_code=status.HTTP_201_CREATED)
def create_governance_event(
    event_data: GovernanceEventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("CREATE_EVENT"))
):
    """
    Ingest & publish a new governance event (internal/admin restricted).
    Persists to governance_events and event_outbox in the same transaction.
    """
    tenant_id = current_user.id
    try:
        event = publisher_service.publish_event(db, event_data, tenant_id)
        db.commit()
        response_data = GovernanceEventResponse.model_validate(event)
        return ResponseHelper.success(
            data=response_data.model_dump(mode="json"),
            message="Governance event created and queued in outbox successfully",
            status_code=201
        )
    except ValueError as ve:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to publish governance event: {str(e)}")


@router.get("")
def search_governance_events(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    event_type: Optional[str] = Query(None),
    event_category: Optional[str] = Query(None),
    subject_type: Optional[str] = Query(None),
    subject_id: Optional[str] = Query(None),
    actor_id: Optional[str] = Query(None),
    correlation_id: Optional[UUID] = Query(None),
    risk_level: Optional[str] = Query(None),
    source_service: Optional[str] = Query(None),
    classification: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("VIEW_EVENTS"))
):
    """
    Search governance events with mandatory tenant isolation and multi-field filters.
    """
    tenant_id = current_user.id
    filters = GovernanceEventSearchFilter(
        start_date=start_date,
        end_date=end_date,
        event_type=event_type,
        event_category=event_category,
        subject_type=subject_type,
        subject_id=subject_id,
        actor_id=actor_id,
        correlation_id=correlation_id,
        risk_level=risk_level,
        source_service=source_service,
        classification=classification,
        page=page,
        page_size=page_size
    )

    try:
        events, total_count = EventRepository.search_events(db, tenant_id, filters)
        event_responses = [GovernanceEventResponse.model_validate(e).model_dump(mode="json") for e in events]
        return ResponseHelper.success(
            data={
                "events": event_responses,
                "total": total_count,
                "page": page,
                "page_size": page_size
            },
            message="Governance events retrieved successfully"
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))



audit_timeline_router = APIRouter(prefix="/api/v1/audit/timeline", tags=["Audit Timeline"])

@router.get("/subject/{entity_type}/{entity_id}")
@router.get("/timeline/{entity_type}/{entity_id}")
@audit_timeline_router.get("/{entity_type}/{entity_id}")
def get_subject_audit_timeline(
    entity_type: str,
    entity_id: str,
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("VIEW_AUDIT_TIMELINE"))
):
    """
    Reconstruct chronological audit timeline for a specific subject entity.
    """
    tenant_id = current_user.id
    timeline_data = AuditTimelineService.build_subject_timeline(db, tenant_id, entity_type, entity_id, limit=limit)
    return ResponseHelper.success(
        data=timeline_data,
        message=f"Subject timeline for {entity_type}:{entity_id} reconstructed successfully"
    )


@router.get("/correlation/{correlation_id}")
def get_correlation_trace_stream(
    correlation_id: UUID,
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("VIEW_AUDIT_TIMELINE"))
):
    """
    Reconstruct correlated event stream trace across multi-step execution flows.
    """
    tenant_id = current_user.id
    timeline_data = AuditTimelineService.build_correlation_timeline(db, tenant_id, correlation_id, limit=limit)
    return ResponseHelper.success(
        data=timeline_data,
        message=f"Correlation trace stream for {correlation_id} retrieved successfully"
    )


from app.modules.events.models import EventDeadLetter, EventOutbox
from app.modules.events.schemas import EventDeadLetterResponse

@router.get("/dead-letter")
def list_dead_letter_events(
    status_filter: Optional[str] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("VIEW_DEAD_LETTER"))
):
    """
    List failed Dead Letter Queue (DLQ) records with tenant isolation.
    """
    tenant_id = current_user.id
    query = db.query(EventDeadLetter).filter(EventDeadLetter.tenant_id == tenant_id)
    if status_filter:
        query = query.filter(EventDeadLetter.status == status_filter)

    total_count = query.count()
    offset = (page - 1) * page_size
    records = query.order_by(EventDeadLetter.failed_at.desc()).offset(offset).limit(page_size).all()

    dlq_responses = [EventDeadLetterResponse.model_validate(r).model_dump(mode="json") for r in records]
    return ResponseHelper.success(
        data={
            "dead_letters": dlq_responses,
            "total": total_count,
            "page": page,
            "page_size": page_size
        },
        message="Dead letter queue records retrieved successfully"
    )


@router.post("/dead-letter/{id}/retry")
def retry_dead_letter_event(
    id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("RETRY_DEAD_LETTER"))
):
    """
    Retry a failed dead letter item: re-queues outbox record, resolves DLQ item, and emits audit event.
    """
    tenant_id = current_user.id
    dlq_record = db.query(EventDeadLetter).filter(
        EventDeadLetter.id == id,
        EventDeadLetter.tenant_id == tenant_id
    ).first()

    if not dlq_record:
        raise HTTPException(status_code=404, detail=f"Dead letter record '{id}' not found")

    now = datetime.now(timezone.utc)

    # 1. Re-queue Outbox Record
    outbox_record = db.query(EventOutbox).filter_by(id=dlq_record.outbox_id).first()
    if outbox_record:
        outbox_record.status = "PENDING"
        outbox_record.retry_count = 0
        outbox_record.next_retry_at = now
        outbox_record.error_message = f"Manually retried by user {current_user.id} at {now.isoformat()}"

    # 2. Update DLQ Record
    dlq_record.status = "RESOLVED"
    dlq_record.resolved_at = now
    dlq_record.resolved_by = current_user.id

    # 3. Emit Audit Trail Governance Event for Retry Action
    audit_event_create = GovernanceEventCreate(
        event_type="DEAD_LETTER_EVENT_RETRIED",
        event_category="Audit",
        event_version="1.0",
        occurred_at=now,
        source_service="event_management",
        actor_json={"user_id": str(current_user.id)},
        subject_json={"entity_type": "event_dead_letter", "entity_id": str(dlq_record.id)},
        payload_json={
            "outbox_id": str(dlq_record.outbox_id),
            "original_event_id": str(dlq_record.event_id),
            "retried_by": str(current_user.id),
            "retried_at": now.isoformat()
        },
        classification="INTERNAL",
        retention_class="STANDARD_90_DAYS"
    )
    publisher_service.publish_event(db, audit_event_create, tenant_id)

    db.commit()

    response_data = EventDeadLetterResponse.model_validate(dlq_record)
    return ResponseHelper.success(
        data=response_data.model_dump(mode="json"),
        message=f"Dead letter event '{id}' successfully re-queued and audit event logged"
    )


# -----------------------------------------------------------------------------
# Audit Export Endpoints (WBS 4.5.1)
# -----------------------------------------------------------------------------

audit_export_router = APIRouter(prefix="/api/v1/audit/export", tags=["Audit Export"])

@router.get("/export")
@audit_export_router.get("")
def list_audit_exports_api(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("EXPORT_AUDIT_PACKAGE"))
):
    tenant_id = current_user.id
    results = AuditExportService.list_exports(
        db=db,
        tenant_id=tenant_id,
        limit=limit
    )
    return ResponseHelper.success(
        data=results,
        message="Audit package exports history retrieved successfully"
    )

@router.post("/export", status_code=status.HTTP_201_CREATED)
@audit_export_router.post("", status_code=status.HTTP_201_CREATED)
def create_audit_export_api(
    filter_params: Optional[dict] = None,
    export_format: str = Query("JSON"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("EXPORT_AUDIT_PACKAGE"))
):
    tenant_id = current_user.id
    result = AuditExportService.create_export(
        db=db,
        tenant_id=tenant_id,
        requested_by=current_user.id,
        filter_params=filter_params or {},
        export_format=export_format
    )
    return ResponseHelper.success(
        data=result,
        message="Audit package export generated successfully"
    )

@router.get("/export/{id}")
@audit_export_router.get("/{id}")
def get_audit_export_status_api(
    id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("EXPORT_AUDIT_PACKAGE"))
):
    tenant_id = current_user.id
    result = AuditExportService.get_export_status(
        db=db,
        tenant_id=tenant_id,
        export_id=id
    )
    return ResponseHelper.success(
        data=result,
        message="Audit package export status retrieved successfully"
    )


# -----------------------------------------------------------------------------
# Event Schema Registry and Retention Rules Endpoints (Phase 4 Extension)
# -----------------------------------------------------------------------------
from app.modules.events.models import EventSchemaRegistry, EventRetentionRule
from app.modules.events.schemas import (
    EventSchemaRegistryCreate, EventSchemaRegistryUpdate, EventSchemaRegistryResponse,
    EventRetentionRuleCreate, EventRetentionRuleUpdate, EventRetentionRuleResponse
)

@router.get("/schemas")
def list_event_schemas(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("VIEW_REFERENCE_DATA"))
):
    schemas = db.query(EventSchemaRegistry).order_by(EventSchemaRegistry.created_at.desc()).all()
    response_data = [EventSchemaRegistryResponse.model_validate(s).model_dump(mode="json") for s in schemas]
    return ResponseHelper.success(data=response_data, message="Event schemas retrieved successfully")

@router.post("/schemas")
def create_event_schema(
    schema_data: EventSchemaRegistryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("MANAGE_EVENT_SCHEMA"))
):
    new_schema = EventSchemaRegistry(**schema_data.model_dump(), created_by=current_user.id)
    db.add(new_schema)
    db.commit()
    db.refresh(new_schema)
    response_data = EventSchemaRegistryResponse.model_validate(new_schema).model_dump(mode="json")
    return ResponseHelper.success(data=response_data, message="Event schema created successfully", status_code=201)

@router.put("/schemas/{schema_id}")
def update_event_schema(
    schema_id: UUID,
    schema_data: EventSchemaRegistryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("MANAGE_EVENT_SCHEMA"))
):
    schema_record = db.query(EventSchemaRegistry).filter(EventSchemaRegistry.id == schema_id).first()
    if not schema_record:
        raise HTTPException(status_code=404, detail="Event schema not found")
    
    update_data = schema_data.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(schema_record, k, v)
    
    db.commit()
    db.refresh(schema_record)
    response_data = EventSchemaRegistryResponse.model_validate(schema_record).model_dump(mode="json")
    return ResponseHelper.success(data=response_data, message="Event schema updated successfully")

@router.delete("/schemas/{schema_id}")
def delete_event_schema(
    schema_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("MANAGE_EVENT_SCHEMA"))
):
    schema_record = db.query(EventSchemaRegistry).filter(EventSchemaRegistry.id == schema_id).first()
    if not schema_record:
        raise HTTPException(status_code=404, detail="Event schema not found")
    db.delete(schema_record)
    db.commit()
    return ResponseHelper.success(message="Event schema deleted successfully")


@router.get("/retention-rules")
def list_retention_rules(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("VIEW_REFERENCE_DATA"))
):
    tenant_id = current_user.id
    rules = db.query(EventRetentionRule).filter(EventRetentionRule.tenant_id == tenant_id).order_by(EventRetentionRule.created_at.desc()).all()
    response_data = [EventRetentionRuleResponse.model_validate(r).model_dump(mode="json") for r in rules]
    return ResponseHelper.success(data=response_data, message="Retention rules retrieved successfully")

@router.post("/retention-rules")
def create_retention_rule(
    rule_data: EventRetentionRuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("MANAGE_RETENTION_RULES"))
):
    tenant_id = current_user.id
    new_rule = EventRetentionRule(**rule_data.model_dump(), tenant_id=tenant_id)
    db.add(new_rule)
    db.commit()
    db.refresh(new_rule)
    response_data = EventRetentionRuleResponse.model_validate(new_rule).model_dump(mode="json")
    return ResponseHelper.success(data=response_data, message="Retention rule created successfully", status_code=201)

@router.put("/retention-rules/{rule_id}")
def update_retention_rule(
    rule_id: UUID,
    rule_data: EventRetentionRuleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("MANAGE_RETENTION_RULES"))
):
    tenant_id = current_user.id
    rule_record = db.query(EventRetentionRule).filter(
        EventRetentionRule.id == rule_id, 
        EventRetentionRule.tenant_id == tenant_id
    ).first()
    
    if not rule_record:
        raise HTTPException(status_code=404, detail="Retention rule not found")
        
    update_data = rule_data.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(rule_record, k, v)
        
    now = datetime.now(timezone.utc)
    
    audit_event_create = GovernanceEventCreate(
        event_type="EVENT_CORRECTION_RECORDED",
        event_category="Audit",
        event_version="1.0",
        occurred_at=now,
        source_service="event_management",
        actor_json={"user_id": str(current_user.id)},
        subject_json={"entity_type": "event_retention_rule", "entity_id": str(rule_record.id)},
        payload_json={"updated_fields": update_data},
        classification="INTERNAL",
        retention_class="STANDARD_90_DAYS"
    )
    publisher_service.publish_event(db, audit_event_create, tenant_id)
    
    db.commit()
    db.refresh(rule_record)
    response_data = EventRetentionRuleResponse.model_validate(rule_record).model_dump(mode="json")
    return ResponseHelper.success(data=response_data, message="Retention rule updated successfully")

@router.delete("/retention-rules/{rule_id}")
def delete_retention_rule(
    rule_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("MANAGE_RETENTION_RULES"))
):
    tenant_id = current_user.id
    rule_record = db.query(EventRetentionRule).filter(
        EventRetentionRule.id == rule_id, 
        EventRetentionRule.tenant_id == tenant_id
    ).first()
    if not rule_record:
        raise HTTPException(status_code=404, detail="Retention rule not found")
    db.delete(rule_record)
    db.commit()
    return ResponseHelper.success(message="Retention rule deleted successfully")


# -----------------------------------------------------------------------------
# Dynamic Event Endpoint (Must remain at the bottom to prevent route shadowing)
# -----------------------------------------------------------------------------
@router.get("/{event_id}")
def get_governance_event_by_id(
    event_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("VIEW_EVENTS"))
):
    """
    Fetch single canonical event by UUID with tenant isolation.
    """
    tenant_id = current_user.id
    event = EventRepository.get_event_by_id(db, tenant_id, event_id)
    if not event:
        raise HTTPException(status_code=404, detail=f"Governance event '{event_id}' not found")

    response_data = GovernanceEventResponse.model_validate(event)
    return ResponseHelper.success(
        data=response_data.model_dump(mode="json"),
        message="Governance event details retrieved successfully"
    )

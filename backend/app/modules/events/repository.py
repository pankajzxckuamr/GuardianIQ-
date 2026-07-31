"""
EventRepository Implementation for Phase 4 Governance Event Store
WBS Reference: 4.3.2
Immutability & Mandatory Fail-Closed Tenant Isolation Enforced
"""
from typing import List, Tuple, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.modules.events.models import GovernanceEvent
from app.modules.events.schemas import GovernanceEventSearchFilter

class EventRepository:
    """
    Repository providing append-only persistence and tenant-isolated querying for governance events.
    Intentional design: No update or delete methods exist to guarantee audit log immutability.
    """

    @staticmethod
    def insert_event(db: Session, event: GovernanceEvent) -> GovernanceEvent:
        """Append-only event insertion."""
        if not event.tenant_id:
            raise ValueError("tenant_id is mandatory for tenant isolation")
        db.add(event)
        db.flush()
        return event

    @staticmethod
    def get_event_by_id(db: Session, tenant_id: UUID, event_id: UUID) -> Optional[GovernanceEvent]:
        """Fetch single event by ID with mandatory tenant isolation."""
        if not tenant_id:
            raise ValueError("tenant_id is mandatory for tenant isolation")
        return db.query(GovernanceEvent).filter(
            GovernanceEvent.tenant_id == tenant_id,
            GovernanceEvent.event_id == event_id
        ).first()

    @staticmethod
    def search_events(
        db: Session, 
        tenant_id: UUID, 
        filters: GovernanceEventSearchFilter
    ) -> Tuple[List[GovernanceEvent], int]:
        """Paginated search with mandatory tenant isolation and JSONB filters."""
        if not tenant_id:
            raise ValueError("tenant_id is mandatory for tenant isolation")

        query = db.query(GovernanceEvent).filter(GovernanceEvent.tenant_id == tenant_id)

        if filters.start_date:
            query = query.filter(GovernanceEvent.occurred_at >= filters.start_date)
        if filters.end_date:
            query = query.filter(GovernanceEvent.occurred_at <= filters.end_date)
        if filters.event_type:
            query = query.filter(GovernanceEvent.event_type == filters.event_type)
        if filters.event_category:
            query = query.filter(GovernanceEvent.event_category == filters.event_category)
        if filters.subject_type:
            query = query.filter(GovernanceEvent.subject_json["entity_type"].astext == filters.subject_type)
        if filters.subject_id:
            query = query.filter(GovernanceEvent.subject_json["entity_id"].astext == str(filters.subject_id))
        if filters.actor_id:
            query = query.filter(GovernanceEvent.actor_json["user_id"].astext == str(filters.actor_id))
        if filters.correlation_id:
            query = query.filter(GovernanceEvent.correlation_id == filters.correlation_id)
        if filters.risk_level:
            query = query.filter(GovernanceEvent.risk_context_json["risk_level"].astext == filters.risk_level)
        if filters.source_service:
            query = query.filter(GovernanceEvent.source_service == filters.source_service)
        if filters.classification:
            query = query.filter(GovernanceEvent.classification == filters.classification)

        total_count = query.count()
        offset = (filters.page - 1) * filters.page_size
        events = query.order_by(GovernanceEvent.occurred_at.desc()).offset(offset).limit(filters.page_size).all()

        return events, total_count

    @staticmethod
    def get_subject_events(
        db: Session, 
        tenant_id: UUID, 
        entity_type: str, 
        entity_id: str, 
        limit: int = 100
    ) -> List[GovernanceEvent]:
        """Fetch subject event history for query-time timeline reconstruction."""
        if not tenant_id:
            raise ValueError("tenant_id is mandatory for tenant isolation")
        return db.query(GovernanceEvent).filter(
            GovernanceEvent.tenant_id == tenant_id,
            GovernanceEvent.subject_json["entity_type"].astext == entity_type,
            GovernanceEvent.subject_json["entity_id"].astext == str(entity_id)
        ).order_by(GovernanceEvent.occurred_at.asc()).limit(limit).all()

    @staticmethod
    def get_correlation_events(
        db: Session, 
        tenant_id: UUID, 
        correlation_id: UUID, 
        limit: int = 100
    ) -> List[GovernanceEvent]:
        """Fetch correlated event stream trace."""
        if not tenant_id:
            raise ValueError("tenant_id is mandatory for tenant isolation")
        return db.query(GovernanceEvent).filter(
            GovernanceEvent.tenant_id == tenant_id,
            GovernanceEvent.correlation_id == correlation_id
        ).order_by(GovernanceEvent.occurred_at.asc()).limit(limit).all()

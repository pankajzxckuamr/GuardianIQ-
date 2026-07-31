"""
AuditTimelineService Implementation for Phase 4
WBS Reference: 4.4.3
Query-time reconstruction of subject entity and correlation stream timelines over governance_events
"""
from uuid import UUID
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.modules.events.repository import EventRepository
from app.modules.events.schemas import GovernanceEventResponse

class AuditTimelineService:
    """
    Service responsible for query-time reconstruction of governance event timelines.
    No derived audit_timelines table is written (MVP query-time reconstruction only).
    """

    @staticmethod
    def build_subject_timeline(
        db: Session, 
        tenant_id: UUID, 
        entity_type: str, 
        entity_id: str, 
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Reconstructs chronological event timeline for a specific subject entity from governance_events.
        Enforces tenant_id isolation.
        """
        events = EventRepository.get_subject_events(
            db=db, 
            tenant_id=tenant_id, 
            entity_type=entity_type, 
            entity_id=entity_id, 
            limit=limit
        )

        event_responses = [GovernanceEventResponse.model_validate(e).model_dump(mode="json") for e in events]
        
        first_event_at = events[0].occurred_at.isoformat() if events else None
        last_event_at = events[-1].occurred_at.isoformat() if events else None

        return {
            "subject_type": entity_type,
            "subject_id": entity_id,
            "total_events": len(events),
            "first_event_at": first_event_at,
            "last_event_at": last_event_at,
            "events": event_responses
        }

    @staticmethod
    def build_correlation_timeline(
        db: Session, 
        tenant_id: UUID, 
        correlation_id: UUID, 
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Reconstructs multi-step execution correlation stream trace from governance_events.
        Enforces tenant_id isolation.
        """
        events = EventRepository.get_correlation_events(
            db=db, 
            tenant_id=tenant_id, 
            correlation_id=correlation_id, 
            limit=limit
        )

        event_responses = [GovernanceEventResponse.model_validate(e).model_dump(mode="json") for e in events]

        first_event_at = events[0].occurred_at.isoformat() if events else None
        last_event_at = events[-1].occurred_at.isoformat() if events else None

        # Build causation chain trace
        causation_chain = [
            {"event_id": str(e.event_id), "event_type": e.event_type, "causation_id": str(e.causation_id) if e.causation_id else None}
            for e in events
        ]

        return {
            "correlation_id": str(correlation_id),
            "total_events": len(events),
            "first_event_at": first_event_at,
            "last_event_at": last_event_at,
            "causation_chain": causation_chain,
            "events": event_responses
        }

"""
EventPublisherService Implementation for Phase 4 Governance Event Store
WBS Reference: 4.3.3
Transactional Outbox Pattern, Actor Enrichment & Business Correlation Tracing
"""
from typing import Dict, Any, Optional
from uuid import UUID, uuid4
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.shared.audit_listeners import get_current_actor_id
from app.core.middleware import get_user_context
from app.shared.hashing import compute_canonical_event_hash
from app.modules.events.models import GovernanceEvent, EventOutbox
from app.modules.events.repository import EventRepository
from app.modules.events.schemas import GovernanceEventCreate

from app.modules.events.validators import EventValidator

class EventPublisherService:
    """
    Central service interface for publishing, enriching, validating, and persisting governance events.
    Guarantees transactional outbox creation in the exact same database transaction.
    """

    def __init__(self):
        self.repository = EventRepository()
        self.validator = EventValidator()

    def enrich_event(
        self, 
        event_data: GovernanceEventCreate, 
        tenant_id: UUID
    ) -> Dict[str, Any]:
        """
        Enriches incoming event with actor details, tenant context, business correlation ID,
        causation ID, and SHA-256 canonical event hash.
        """
        if not tenant_id:
            raise ValueError("tenant_id is mandatory for event publishing")

        # 1. Resolve Actor Context
        current_actor_id = get_current_actor_id()
        user_ctx = get_user_context() or {}
        
        actor_json = dict(event_data.actor_json or {})
        if "user_id" not in actor_json or not actor_json["user_id"]:
            actor_json["user_id"] = str(current_actor_id or tenant_id)
        else:
            actor_json["user_id"] = str(actor_json["user_id"])
            
        if "roles" not in actor_json:
            actor_json["roles"] = user_ctx.get("roles", [])
        if "ip_address" not in actor_json:
            actor_json["ip_address"] = user_ctx.get("ip_address", "127.0.0.1")

        # 2. Resolve Business Correlation & Causation IDs
        # Business flow correlation ID distinct from transient HTTP request ID
        correlation_id = event_data.correlation_id or uuid4()
        causation_id = event_data.causation_id

        # 3. Format Subject Context
        subject_json = dict(event_data.subject_json or {})
        if "entity_id" in subject_json:
            subject_json["entity_id"] = str(subject_json["entity_id"])

        # 4. Compute SHA-256 Canonical Event Hash
        hash_payload = {
            "tenant_id": str(tenant_id),
            "event_type": event_data.event_type,
            "event_category": event_data.event_category,
            "occurred_at": event_data.occurred_at.isoformat() if isinstance(event_data.occurred_at, datetime) else str(event_data.occurred_at),
            "source_service": event_data.source_service,
            "actor": actor_json,
            "subject": subject_json,
            "payload": event_data.payload_json
        }
        event_hash = compute_canonical_event_hash(hash_payload, event_data.previous_event_hash)

        return {
            "tenant_id": tenant_id,
            "event_type": event_data.event_type,
            "event_category": event_data.event_category,
            "event_version": event_data.event_version or "1.0",
            "occurred_at": event_data.occurred_at,
            "source_service": event_data.source_service,
            "source_system": event_data.source_system or "guardianiq-backend",
            "actor_json": actor_json,
            "subject_json": subject_json,
            "correlation_id": correlation_id,
            "causation_id": causation_id,
            "risk_context_json": event_data.risk_context_json or {},
            "policy_context_json": event_data.policy_context_json or {},
            "payload_json": event_data.payload_json,
            "classification": event_data.classification or "INTERNAL",
            "retention_class": event_data.retention_class or "STANDARD_90_DAYS",
            "event_hash": event_hash,
            "previous_event_hash": event_data.previous_event_hash
        }

    def validate_event(self, db: Optional[Session], enriched_data: Dict[str, Any]) -> bool:
        """Validates enriched event dictionary properties, schema registry active state, and secret key rules."""
        return self.validator.validate_event(db, enriched_data)

    def append_event(self, db: Session, enriched_data: Dict[str, Any]) -> GovernanceEvent:
        """Instantiates and appends GovernanceEvent model into database transaction."""
        event_model = GovernanceEvent(
            tenant_id=enriched_data["tenant_id"],
            event_type=enriched_data["event_type"],
            event_category=enriched_data["event_category"],
            event_version=enriched_data["event_version"],
            occurred_at=enriched_data["occurred_at"],
            source_service=enriched_data["source_service"],
            source_system=enriched_data["source_system"],
            actor_json=enriched_data["actor_json"],
            subject_json=enriched_data["subject_json"],
            correlation_id=enriched_data["correlation_id"],
            causation_id=enriched_data["causation_id"],
            risk_context_json=enriched_data["risk_context_json"],
            policy_context_json=enriched_data["policy_context_json"],
            payload_json=enriched_data["payload_json"],
            classification=enriched_data["classification"],
            retention_class=enriched_data["retention_class"],
            event_hash=enriched_data["event_hash"],
            previous_event_hash=enriched_data["previous_event_hash"]
        )
        return self.repository.insert_event(db, event_model)

    def publish_event(
        self, 
        db: Session, 
        event_data: GovernanceEventCreate, 
        tenant_id: UUID
    ) -> GovernanceEvent:
        """
        Main entry point for publishing a governance event.
        Persists GovernanceEvent AND creates corresponding EventOutbox entry in the SAME transaction.
        """
        # 1. Enrich & Validate (Pre-persistance fail-fast rejection)
        enriched_data = self.enrich_event(event_data, tenant_id)
        self.validate_event(db, enriched_data)

        # 2. Append Governance Event
        event = self.append_event(db, enriched_data)

        # 3. Transactional Outbox Pattern Write (Same DB session transaction)
        outbox_entry = EventOutbox(
            event_id=event.event_id,
            tenant_id=event.tenant_id,
            destination="internal_bus",
            payload_json=event.payload_json,
            status="PENDING",
            retry_count=0,
            max_retries=5
        )
        db.add(outbox_entry)
        db.flush()
        return event


class EventMetricsService:
    @staticmethod
    def get_dashboard_metrics(db: Session, tenant_id: UUID) -> Dict[str, Any]:
        """
        Calculates aggregated governance event metrics with explicit manual tenant filtering on every query.
        """
        from sqlalchemy import func
        from app.modules.events.models import EventDeadLetter

        # 1. Total Governance Events
        total_events = db.query(func.count(GovernanceEvent.event_id)).filter(
            GovernanceEvent.tenant_id == tenant_id
        ).scalar() or 0

        # 2. Events by Category
        cat_query = db.query(
            GovernanceEvent.event_category,
            func.count(GovernanceEvent.event_id)
        ).filter(
            GovernanceEvent.tenant_id == tenant_id
        ).group_by(GovernanceEvent.event_category).all()
        events_by_category = {cat: count for cat, count in cat_query if cat}

        # 3. Events by Type
        type_query = db.query(
            GovernanceEvent.event_type,
            func.count(GovernanceEvent.event_id)
        ).filter(
            GovernanceEvent.tenant_id == tenant_id
        ).group_by(GovernanceEvent.event_type).all()
        events_by_type = {etype: count for etype, count in type_query if etype}

        # 4. Policy Violations
        policy_violations_count = db.query(func.count(GovernanceEvent.event_id)).filter(
            GovernanceEvent.tenant_id == tenant_id,
            GovernanceEvent.event_category == "Violation"
        ).scalar() or 0

        # 5. SLA Breaches Count
        sla_breaches_count = db.query(func.count(GovernanceEvent.event_id)).filter(
            GovernanceEvent.tenant_id == tenant_id,
            GovernanceEvent.event_type.in_(["SLA_BREACHED", "SLA_VIOLATED"])
        ).scalar() or 0

        # 6. Blocked Agent Actions
        blocked_agent_actions_count = db.query(func.count(GovernanceEvent.event_id)).filter(
            GovernanceEvent.tenant_id == tenant_id,
            GovernanceEvent.event_type.in_(["UNAUTHORIZED_ACCESS_BLOCKED", "AGENT_ACTION_BLOCKED", "BOUNDARY_BREACH_ATTEMPTED"])
        ).scalar() or 0

        # 7. Outbox Lag Seconds
        min_pending_created = db.query(func.min(EventOutbox.created_at)).filter(
            EventOutbox.tenant_id == tenant_id,
            EventOutbox.status == "PENDING"
        ).scalar()

        outbox_lag_seconds = 0.0
        if min_pending_created:
            now = datetime.now(timezone.utc)
            if min_pending_created.tzinfo is None:
                min_pending_created = min_pending_created.replace(tzinfo=timezone.utc)
            outbox_lag_seconds = max(0.0, (now - min_pending_created).total_seconds())

        # 8. Unresolved Dead Letter Count
        dead_letter_count = db.query(func.count(EventDeadLetter.id)).filter(
            EventDeadLetter.tenant_id == tenant_id,
            EventDeadLetter.status == "UNRESOLVED"
        ).scalar() or 0

        return {
            "tenant_id": str(tenant_id),
            "total_events_count": total_events,
            "events_by_category": events_by_category,
            "events_by_type": events_by_type,
            "policy_violations_count": policy_violations_count,
            "sla_breaches_count": sla_breaches_count,
            "blocked_agent_actions_count": blocked_agent_actions_count,
            "outbox_lag_seconds": round(outbox_lag_seconds, 2),
            "dead_letter_count": dead_letter_count,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }

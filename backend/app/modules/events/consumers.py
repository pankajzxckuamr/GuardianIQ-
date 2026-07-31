"""
Event Consumers & Idempotent Handler Subscriptions
WBS Reference: 4.4.2
Guarantees Idempotent Processing & Audit Logging in event_processing_log
"""
import time
from uuid import UUID
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Callable
from sqlalchemy.orm import Session

from app.modules.events.models import EventProcessingLog, GovernanceEvent

class BaseEventConsumer:
    """
    Base consumer class enforcing handler idempotency via event_processing_log checks.
    """

    def __init__(self, consumer_id: str):
        self.consumer_id = consumer_id

    def is_already_processed(self, db: Session, event_id: UUID) -> bool:
        """Checks if event has already been processed by this consumer."""
        existing = db.query(EventProcessingLog).filter_by(
            event_id=event_id,
            consumer_id=self.consumer_id
        ).first()
        return existing is not None and existing.status in ["PROCESSED", "SUCCESS"]

    def log_processing(
        self, 
        db: Session, 
        event_id: UUID, 
        status: str, 
        execution_time_ms: int, 
        error_message: Optional[str] = None
    ) -> EventProcessingLog:
        """Persists consumer execution outcome to event_processing_log."""
        log_entry = EventProcessingLog(
            event_id=event_id,
            consumer_id=self.consumer_id,
            status=status,
            processed_at=datetime.now(timezone.utc),
            execution_time_ms=execution_time_ms,
            error_message=error_message
        )
        db.add(log_entry)
        db.flush()
        return log_entry

    def process_event(
        self, 
        db: Session, 
        event: GovernanceEvent, 
        handler_fn: Callable[[GovernanceEvent], Any]
    ) -> Dict[str, Any]:
        """
        Executes handler_fn idempotently.
        If event was already processed, returns status SKIPPED without duplicate handler execution.
        """
        if self.is_already_processed(db, event.event_id):
            return {"status": "SKIPPED", "message": f"Event {event.event_id} already processed by consumer {self.consumer_id}"}

        start_time = time.time()
        try:
            handler_fn(event)
            duration_ms = int((time.time() - start_time) * 1000)
            self.log_processing(db, event.event_id, "PROCESSED", duration_ms)
            return {"status": "PROCESSED", "execution_time_ms": duration_ms}
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            self.log_processing(db, event.event_id, "FAILED", duration_ms, error_message=str(e))
            raise e

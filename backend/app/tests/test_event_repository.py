"""
Unit tests for EventRepository (WBS 4.3.2)
Verifies immutability (no update/delete methods) and mandatory fail-closed tenant isolation.
"""
import pytest
from uuid import uuid4
from datetime import datetime, timezone
from app.db.session import SessionLocal
from app.modules.events.models import GovernanceEvent
from app.modules.events.repository import EventRepository
from app.modules.events.schemas import GovernanceEventSearchFilter

def test_event_repository_immutability():
    """Verify that EventRepository exposes ZERO update or delete methods."""
    repo_methods = [method for method in dir(EventRepository) if not method.startswith("__")]
    
    # Assert no update or delete pathways exist
    for method in repo_methods:
        assert "update" not in method.lower(), f"Forbidden update method found: {method}"
        assert "delete" not in method.lower(), f"Forbidden delete method found: {method}"
        assert "remove" not in method.lower(), f"Forbidden remove method found: {method}"

def test_tenant_id_fail_closed_validation():
    """Verify that all EventRepository query methods fail closed if tenant_id is missing or None."""
    db = SessionLocal()
    try:
        dummy_uuid = uuid4()
        dummy_filter = GovernanceEventSearchFilter()

        with pytest.raises(ValueError, match="tenant_id is mandatory"):
            EventRepository.insert_event(db, GovernanceEvent(tenant_id=None))

        with pytest.raises(ValueError, match="tenant_id is mandatory"):
            EventRepository.get_event_by_id(db, tenant_id=None, event_id=dummy_uuid)

        with pytest.raises(ValueError, match="tenant_id is mandatory"):
            EventRepository.search_events(db, tenant_id=None, filters=dummy_filter)

        with pytest.raises(ValueError, match="tenant_id is mandatory"):
            EventRepository.get_subject_events(db, tenant_id=None, entity_type="Agent", entity_id=str(dummy_uuid))

        with pytest.raises(ValueError, match="tenant_id is mandatory"):
            EventRepository.get_correlation_events(db, tenant_id=None, correlation_id=dummy_uuid)
    finally:
        db.close()

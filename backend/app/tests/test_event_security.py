"""
Unit Tests for Retention and Classification Controls (WBS 4.5.2)
Tests EventSecurityService and PayloadRedactorService.
"""
import pytest
import uuid
from types import SimpleNamespace
from app.modules.registry.constants import DataClassification
from app.shared.redaction import PayloadRedactorService
from app.modules.events.security import EventSecurityService


def test_payload_redactor_secrets():
    """Verify secret keys (passwords, tokens, api keys) are automatically redacted."""
    raw_payload = {
        "user": "alice",
        "password": "SuperSecretPassword123!",
        "api_key": "sk_live_123456789",
        "nested": {
            "access_token": "bearer_abc_xyz",
            "normal_field": "visible"
        }
    }

    redacted = PayloadRedactorService.redact_secrets(raw_payload)

    assert redacted["user"] == "alice"
    assert redacted["password"] == "[REDACTED]"
    assert redacted["api_key"] == "[REDACTED]"
    assert redacted["nested"]["access_token"] == "[REDACTED]"
    assert redacted["nested"]["normal_field"] == "visible"


def test_payload_redactor_clearance_restriction():
    """Verify payload is masked when user clearance rank is below event classification rank."""
    raw_payload = {"sensitive_data": "top_secret_value"}

    # User with INTERNAL clearance attempting to view RESTRICTED event payload
    masked = PayloadRedactorService.redact_by_clearance(
        raw_payload,
        user_clearance="INTERNAL",
        event_classification="RESTRICTED"
    )

    assert masked["masked"] is True
    assert masked["data"] == "[REDACTED]"

    # User with RESTRICTED clearance viewing RESTRICTED event payload
    unmasked = PayloadRedactorService.redact_by_clearance(
        raw_payload,
        user_clearance="RESTRICTED",
        event_classification="RESTRICTED"
    )

    assert unmasked["sensitive_data"] == "top_secret_value"


def test_event_security_can_view_event():
    """Verify tenant isolation and classification clearance check."""
    tenant_a = uuid.uuid4()
    tenant_b = uuid.uuid4()

    user_admin = SimpleNamespace(id=tenant_a, tenant_id=tenant_a, role="ADMIN")
    user_business = SimpleNamespace(id=tenant_a, tenant_id=tenant_a, role="BUSINESS_USER")

    event_internal = SimpleNamespace(tenant_id=tenant_a, classification="INTERNAL")
    event_restricted = SimpleNamespace(tenant_id=tenant_a, classification="RESTRICTED")
    event_other_tenant = SimpleNamespace(tenant_id=tenant_b, classification="INTERNAL")

    # 1. Admin can view internal & restricted
    assert EventSecurityService.can_view_event(user_admin, event_internal) is True
    assert EventSecurityService.can_view_event(user_admin, event_restricted) is True

    # 2. Business user can view internal, but NOT restricted
    assert EventSecurityService.can_view_event(user_business, event_internal) is True
    assert EventSecurityService.can_view_event(user_business, event_restricted) is False

    # 3. Tenant isolation prevents viewing other tenant's events
    assert EventSecurityService.can_view_event(user_admin, event_other_tenant) is False


def test_event_security_filter_events_by_scope():
    """Verify batch filtering and payload masking for scoped events."""
    tenant_id = uuid.uuid4()
    user = SimpleNamespace(id=tenant_id, tenant_id=tenant_id, role="BUSINESS_USER")

    events = [
        SimpleNamespace(
            event_id="e1",
            tenant_id=tenant_id,
            classification="INTERNAL",
            payload_json={"action": "RUN", "secret": "12345"}
        ),
        SimpleNamespace(
            event_id="e2",
            tenant_id=tenant_id,
            classification="RESTRICTED",
            payload_json={"high_risk_data": "secret"}
        )
    ]

    filtered = EventSecurityService.filter_events_by_scope(user, events)

    # Only e1 should be included since business user lacks RESTRICTED clearance
    assert len(filtered) == 1
    assert filtered[0]["event_id"] == "e1"
    # Secret key should be redacted
    assert filtered[0]["payload_json"]["secret"] == "[REDACTED]"
    assert filtered[0]["payload_json"]["action"] == "RUN"

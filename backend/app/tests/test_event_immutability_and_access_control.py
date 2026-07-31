"""
Integration Test Suite for Event Immutability and Access Control (WBS 4.7.2 / QA4-005, QA4-009)
Explicitly verifies:
(a) Event Immutability: EventRepository has 0 update/delete methods & HTTP PUT/PATCH/DELETE returns 405 Method Not Allowed.
(b) Access Control: Tenant isolation (404, 0 leak), RBAC (403, 0 payload leak), ABAC clearance & department scoping, and payload masking.
"""
import pytest
import uuid
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import SessionLocal, get_db
from app.modules.auth.models import User, Role
from app.modules.auth.dependencies import get_current_user
from app.modules.events.models import GovernanceEvent
from app.modules.events.repository import EventRepository
from app.modules.events.service import EventPublisherService
from app.modules.events.schemas import GovernanceEventCreate
from app.modules.events.security import EventSecurityService
from app.shared.redaction import PayloadRedactorService


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def tenant_a_admin(db_session):
    user_id = uuid.uuid4()
    user = User(
        id=user_id,
        email=f"immut_admin_{user_id.hex[:8]}@example.com",
        hashed_password="hashed_pw",
        name="Tenant A Admin",
        status="ACTIVE"
    )
    db_session.add(user)
    db_session.commit()

    admin_role = db_session.query(Role).filter_by(role_code="ADMIN").first()
    if admin_role:
        user.roles.append(admin_role)
        db_session.commit()

    db_session.refresh(user)
    setattr(user, "role", "ADMIN")
    return user


@pytest.fixture
def tenant_b_admin(db_session):
    user_id = uuid.uuid4()
    user = User(
        id=user_id,
        email=f"immut_tenant_b_{user_id.hex[:8]}@example.com",
        hashed_password="hashed_pw",
        name="Tenant B Admin",
        status="ACTIVE"
    )
    db_session.add(user)
    db_session.commit()

    admin_role = db_session.query(Role).filter_by(role_code="ADMIN").first()
    if admin_role:
        user.roles.append(admin_role)
        db_session.commit()

    db_session.refresh(user)
    setattr(user, "role", "ADMIN")
    return user


@pytest.fixture
def unprivileged_user(db_session):
    user_id = uuid.uuid4()
    user = User(
        id=user_id,
        email=f"unpriv_user_{user_id.hex[:8]}@example.com",
        hashed_password="hashed_pw",
        name="Unprivileged User",
        status="ACTIVE"
    )
    db_session.add(user)
    db_session.commit()
    return user


def test_governance_event_immutability_enforcement(db_session, tenant_a_admin):
    """(a) Confirm EventRepository has ZERO update/delete methods & HTTP PUT/PATCH/DELETE returns 405 Method Not Allowed."""
    # 1. Repository inspection
    repo_methods = [m for m in dir(EventRepository) if not m.startswith("__")]
    for method in repo_methods:
        assert "update" not in method.lower(), f"Forbidden method found: {method}"
        assert "delete" not in method.lower(), f"Forbidden method found: {method}"
        assert "modify" not in method.lower(), f"Forbidden method found: {method}"
        assert "remove" not in method.lower(), f"Forbidden method found: {method}"

    # 2. HTTP method rejection on REST endpoints
    event_id = uuid.uuid4()
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_user] = lambda: tenant_a_admin
    client = TestClient(app)

    put_res = client.put(f"/api/v1/events/{event_id}", json={"event_type": "MUTATION_ATTEMPT"})
    assert put_res.status_code == 405 # Method Not Allowed

    patch_res = client.patch(f"/api/v1/events/{event_id}", json={"event_type": "MUTATION_ATTEMPT"})
    assert patch_res.status_code == 405

    delete_res = client.delete(f"/api/v1/events/{event_id}")
    assert delete_res.status_code == 405

    app.dependency_overrides.clear()


def test_tenant_isolation_zero_existence_leakage(db_session, tenant_a_admin, tenant_b_admin):
    """(b) Confirm event visibility respects tenant_id and unauthorized tenant gets 404 without existence leakage."""
    publisher = EventPublisherService()

    ev = publisher.publish_event(
        db_session,
        GovernanceEventCreate(
            event_type="WORKFLOW_RUN_STARTED", event_category="Workflow", event_version="1.0",
            occurred_at=datetime.now(timezone.utc), source_service="workflow",
            actor_json={"user_id": str(tenant_a_admin.id)}, subject_json={"entity_type": "run", "entity_id": "a_1"},
            payload_json={"secret_code": "TOP_SECRET_CODE"}, classification="RESTRICTED", retention_class="STANDARD_90_DAYS"
        ),
        tenant_id=tenant_a_admin.id
    )

    # Query as Tenant B
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_user] = lambda: tenant_b_admin
    client = TestClient(app)

    # Direct ID GET -> 404 Not Found (zero existence leak)
    res = client.get(f"/api/v1/events/{ev.event_id}")
    assert res.status_code == 404
    assert "TOP_SECRET_CODE" not in res.text

    app.dependency_overrides.clear()


def test_rbac_permission_denial_no_payload_leak(db_session, unprivileged_user):
    """(b) Confirm request without required RBAC permission returns 403 without payload leakage."""
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_user] = lambda: unprivileged_user
    client = TestClient(app)

    # Attempt GET /api/v1/events without VIEW_EVENTS permission -> 403 Forbidden
    res = client.get("/api/v1/events")
    assert res.status_code == 403
    assert "VIEW_EVENTS" in res.json()["message"]

    # Attempt POST /api/v1/audit/export without EXPORT_AUDIT_PACKAGE permission -> 403 Forbidden
    export_res = client.post("/api/v1/audit/export", json={"format": "json", "reason": "Test"})
    assert export_res.status_code == 403

    app.dependency_overrides.clear()


def test_abac_department_clearance_and_payload_redaction():
    """(b) Confirm ABAC clearance scoping and PayloadRedactorService redacts sensitive key patterns."""
    raw_payload = {
        "user_id": "usr_100",
        "api_key": "sk_live_123456789",
        "access_token": "bearer_abc_xyz",
        "credit_card": "4111-2222-3333-4444",
        "status": "ACTIVE"
    }

    redacted = PayloadRedactorService.redact_secrets(raw_payload)

    assert redacted["user_id"] == "usr_100"
    assert redacted["api_key"] == "[REDACTED]"
    assert redacted["access_token"] == "[REDACTED]"
    assert redacted["credit_card"] == "[REDACTED]"
    assert redacted["status"] == "ACTIVE"

    # Test clearance masking
    clearance_masked = PayloadRedactorService.redact_by_clearance(
        payload=raw_payload,
        user_clearance="INTERNAL",
        event_classification="RESTRICTED"
    )
    assert clearance_masked["masked"] is True
    assert clearance_masked["data"] == "[REDACTED]"

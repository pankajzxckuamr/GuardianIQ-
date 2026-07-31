"""
API Test Suite for Phase 4 Governance Event Endpoints (WBS 4.3.5)
Verifies POST /api/v1/events, GET search, GET by ID, GET subject timeline, and GET correlation trace.
"""
import pytest
from uuid import uuid4
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import SessionLocal
from app.modules.auth.models import User
from app.modules.auth.dependencies import get_current_user

from types import SimpleNamespace

def get_test_user_override():
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(email="test_api@guardianiq.demo").first()
        if not user:
            user = User(
                id=uuid4(),
                email="test_api@guardianiq.demo",
                name="Test API User",
                hashed_password="hashed_pwd_stub"
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        return SimpleNamespace(
            id=user.id,
            email=user.email,
            role="ADMIN",
            roles=[]
        )
    finally:
        db.close()

@pytest.fixture
def client():
    app.dependency_overrides[get_current_user] = get_test_user_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

def test_event_api_full_lifecycle(client):
    """Test full event creation, search, single event fetch, subject timeline, and correlation trace via REST API."""
    user = get_test_user_override()
    tenant_id = str(user.id)
    correlation_id = str(uuid4())
    entity_id = str(uuid4())

    # 1. POST /api/v1/events (Publish Event)
    create_payload = {
        "event_type": "WORKFLOW_RUN_STARTED",
        "event_category": "Workflow",
        "occurred_at": datetime.now(timezone.utc).isoformat(),
        "source_service": "workflow_execution",
        "actor_json": {"user_id": tenant_id, "roles": ["ADMIN"]},
        "subject_json": {"entity_type": "workflows", "entity_id": entity_id},
        "correlation_id": correlation_id,
        "payload_json": {"mode": "AUTOMATED", "run_id": str(uuid4())}
    }

    response = client.post("/api/v1/events", json=create_payload)
    assert response.status_code == 201, f"Create event failed: {response.text}"
    data = response.json()
    assert data["status"] == "success"
    assert "request_id" in data
    event_id = data["data"]["event_id"]
    assert event_id is not None

    # 2. GET /api/v1/events (Search Events)
    search_res = client.get("/api/v1/events", params={"event_category": "Workflow", "page": 1, "page_size": 10})
    assert search_res.status_code == 200
    search_data = search_res.json()
    assert search_data["status"] == "success"
    assert search_data["data"]["total"] >= 1

    # 3. GET /api/v1/events/{event_id} (Fetch Single Event)
    get_res = client.get(f"/api/v1/events/{event_id}")
    assert get_res.status_code == 200
    get_data = get_res.json()
    assert get_data["data"]["event_id"] == event_id

    # 4. GET /api/v1/events/subject/{entity_type}/{entity_id} (Subject Timeline)
    timeline_res = client.get(f"/api/v1/events/subject/workflows/{entity_id}")
    assert timeline_res.status_code == 200
    timeline_data = timeline_res.json()
    assert timeline_data["data"]["total_events"] >= 1

    # 5. GET /api/v1/events/correlation/{correlation_id} (Correlation Trace)
    corr_res = client.get(f"/api/v1/events/correlation/{correlation_id}")
    assert corr_res.status_code == 200
    corr_data = corr_res.json()
    assert corr_data["data"]["total_events"] >= 1

def test_event_api_404_not_found(client):
    """Verify 404 response for non-existent event ID."""
    non_existent_id = str(uuid4())
    res = client.get(f"/api/v1/events/{non_existent_id}")
    assert res.status_code == 404

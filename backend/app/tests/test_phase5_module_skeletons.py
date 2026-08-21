from uuid import uuid4
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import SessionLocal
from app.modules.auth.models import User
from app.modules.enforcement import (
    GovernedRuntimeContextBuilder,
    EnforcementDecisionCombiner,
    RuntimeAuthorizationService,
    RuntimeEnforcementEngine,
)
from app.modules.policy_engine.enums import Decision, EnforcementMode
from app.modules.policy_engine.schemas import PolicyEvaluationResult


@pytest.fixture
def auth_client():
    client = TestClient(app)
    # Login to obtain real JWT token
    login_resp = client.post(
        "/api/auth/login",
        data={"username": "admin@guardianiq.com", "password": "Admin@1234!"}
    )
    if login_resp.status_code == 200:
        token = login_resp.json()["access_token"]
        client.headers.update({"Authorization": f"Bearer {token}"})
    return client


def test_app_starts_and_routes_registered():
    client = TestClient(app)
    # Test health check route to prove app starts
    resp = client.get("/api/health")
    assert resp.status_code == 200
    res_data = resp.json()
    assert res_data["data"]["status"] == "healthy"


def test_public_policy_engine_routes(auth_client: TestClient):
    resp = auth_client.get("/api/v1/policies")
    assert resp.status_code == 200
    res_data = resp.json()
    assert res_data["success"] is True
    assert isinstance(res_data["data"], list)
    # Ensure seeded policies are present
    codes = [p["policy_code"] for p in res_data["data"]]
    assert "POL-DLP-001" in codes

    # Test GET /api/v1/policy-bindings
    bind_resp = auth_client.get("/api/v1/policy-bindings")
    assert bind_resp.status_code == 200
    bind_data = bind_resp.json()
    assert bind_data["success"] is True
    assert isinstance(bind_data["data"], list)


def test_public_agent_boundary_routes(auth_client: TestClient):
    resp = auth_client.get("/api/v1/agent-boundaries")
    assert resp.status_code == 200
    res_data = resp.json()
    assert res_data["success"] is True
    assert isinstance(res_data["data"], list)


def test_public_tool_governance_routes(auth_client: TestClient):
    db = SessionLocal()
    try:
        from app.modules.registry.models import Tool
        tool = db.query(Tool).first()
        if tool:
            resp = auth_client.get(f"/api/v1/tool-governance/tools/{tool.id}/capabilities")
            assert resp.status_code == 200
            res_data = resp.json()
            assert res_data["success"] is True
            assert isinstance(res_data["data"], list)
    finally:
        db.close()


def test_public_data_governance_routes(auth_client: TestClient):
    db = SessionLocal()
    try:
        from app.modules.datasource.models import DataSource
        ds = db.query(DataSource).first()
        if ds:
            resp = auth_client.get(f"/api/v1/data-governance/datasources/{ds.id}/fields")
            assert resp.status_code == 200
            res_data = resp.json()
            assert res_data["success"] is True
            assert isinstance(res_data["data"], list)
    finally:
        db.close()


def test_internal_enforcement_engine_pipeline():
    db = SessionLocal()
    try:
        # 1. Build context via GovernedRuntimeContextBuilder
        req = GovernedRuntimeContextBuilder.build_request(
            actor_id="usr_tester",
            role="Analyst",
            agent_id="agt_audit_01",
            tool_id=str(uuid4()),
            tool_name="DatabaseQueryTool",
            tool_parameters={"query": "SELECT * FROM logs"},
            enforcement_mode=EnforcementMode.BLOCKING,
        )
        assert req.request_id is not None
        assert req.correlation_id is not None
        assert req.agent.agent_id == "agt_audit_01"

        # 2. Test Decision Combiner
        eval1 = PolicyEvaluationResult(
            policy_id="pol_1", policy_name="DLP", decision=Decision.ALLOW
        )
        eval2 = PolicyEvaluationResult(
            policy_id="pol_2", policy_name="Approval", decision=Decision.REQUIRE_APPROVAL
        )
        combined = EnforcementDecisionCombiner.combine([eval1, eval2])
        assert combined == Decision.REQUIRE_APPROVAL

        # 3. Test RuntimeEnforcementEngine execution
        engine = RuntimeEnforcementEngine(db)
        resp = engine.enforce(req, tenant_id=uuid4())
        assert resp.request_id == req.request_id
        assert resp.decision in [Decision.ALLOW, Decision.DENY, Decision.REQUIRE_APPROVAL, Decision.MODIFY]
    finally:
        db.close()

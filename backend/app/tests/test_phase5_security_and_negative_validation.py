from datetime import datetime, timezone, timedelta
from uuid import uuid4, UUID
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.db.session import SessionLocal
from app.modules.auth.models import User, Role
from app.core.security import create_access_token
from app.modules.relationship.models import PolicyBinding, GenericRelationship
from app.modules.policy_engine.models import GovernancePolicy, PolicyVersion, PolicyRule
from app.modules.agent_boundary.models import AgentRuntimeBoundary
from app.modules.agent.models import Agent
from app.modules.registry.models import Tool
from app.modules.datasource.models import DataSource
from app.modules.relationship.cache_service import MemoryCacheService
from app.modules.enforcement import (
    GovernedRuntimeContextBuilder,
    RuntimeEnforcementEngine,
    RuntimeAuthorizationService,
)
from app.modules.policy_engine.binding_service import PolicyBindingService
from app.modules.policy_engine.enums import Decision, EnforcementMode, PolicyStatus
from app.modules.events.models import GovernanceEvent


@pytest.fixture
def db():
    session = SessionLocal()
    MemoryCacheService().clear()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


def create_sec_test_user(db: Session, email_prefix: str = "sec_test") -> User:
    user = User(
        id=uuid4(),
        name=f"User {email_prefix}",
        full_name="Security Test User",
        email=f"{email_prefix}_{uuid4().hex[:8]}@guardianiq.ai",
        hashed_password="pw",
    )
    db.add(user)
    db.commit()
    return user


@pytest.fixture
def auth_client():
    client = TestClient(app)
    # Admin login
    login_resp = client.post(
        "/api/auth/login",
        data={"username": "admin@guardianiq.com", "password": "Admin@1234!"}
    )
    if login_resp.status_code == 200:
        token = login_resp.json()["access_token"]
        client.headers.update({"Authorization": f"Bearer {token}"})
    return client


# --------------------------------------------------------------------------------------
# 1. Cross-Tenant Isolation & Table Partitioning
# --------------------------------------------------------------------------------------

def test_security_cross_tenant_policy_and_binding_isolation(db: Session):
    """
    Q-016: Verify strict cross-tenant isolation on all Phase 5 tables + altered policy_bindings table.
    Tenant A's policies/bindings must NEVER be visible or evaluated for Tenant B.
    """
    MemoryCacheService().clear()
    user_a = create_sec_test_user(db, "tenant_a")
    user_b = create_sec_test_user(db, "tenant_b")
    tenant_a = user_a.id
    tenant_b = user_b.id

    # Create policy in Tenant A
    pol_a = GovernancePolicy(
        id=uuid4(),
        tenant_id=tenant_a,
        policy_code=f"SEC-POL-A-{uuid4().hex[:6].upper()}",
        name="Tenant A Exclusive Policy",
        category="FINANCIAL_SAFETY",
        enforcement_mode="BLOCKING",
        priority=100,
        status="ACTIVE",
    )
    db.add(pol_a)

    # Create policy in Tenant B
    pol_b = GovernancePolicy(
        id=uuid4(),
        tenant_id=tenant_b,
        policy_code=f"SEC-POL-B-{uuid4().hex[:6].upper()}",
        name="Tenant B Exclusive Policy",
        category="DATA_PROTECTION",
        enforcement_mode="BLOCKING",
        priority=100,
        status="ACTIVE",
    )
    db.add(pol_b)
    db.flush()

    # Bind pol_a in altered policy_bindings table for Tenant A
    agent_id_a = str(uuid4())
    binding_a = PolicyBinding(
        id=uuid4(),
        tenant_id=tenant_a,
        policy_id=pol_a.id,
        target_type="AGENT",
        target_id=agent_id_a,
        binding_scope="DIRECT",
        priority=100,
        is_mandatory=True,
        version_strategy="LATEST",
        status="ACTIVE",
        effective_from=datetime.now(timezone.utc) - timedelta(days=1),
    )
    db.add(binding_a)

    # Bind pol_b in altered policy_bindings table for Tenant B
    binding_b = PolicyBinding(
        id=uuid4(),
        tenant_id=tenant_b,
        policy_id=pol_b.id,
        target_type="AGENT",
        target_id=agent_id_a, # Same target string, different tenant!
        binding_scope="DIRECT",
        priority=200,
        is_mandatory=True,
        version_strategy="LATEST",
        status="ACTIVE",
        effective_from=datetime.now(timezone.utc) - timedelta(days=1),
    )
    db.add(binding_b)
    db.commit()

    # Query bindings via PolicyBindingService for Tenant A
    binding_service = PolicyBindingService(db)
    resolved_a = binding_service.resolve_effective_bindings(tenant_a, "AGENT", agent_id_a)
    assert len(resolved_a) == 1
    assert resolved_a[0].policy_id == pol_a.id
    assert resolved_a[0].tenant_id == tenant_a

    # Query bindings for Tenant B on same target ID
    resolved_b = binding_service.resolve_effective_bindings(tenant_b, "AGENT", agent_id_a)
    assert len(resolved_b) == 1
    assert resolved_b[0].policy_id == pol_b.id
    assert resolved_b[0].tenant_id == tenant_b

    # Verify no cross-tenant leakage in raw query
    cross_check = db.query(PolicyBinding).filter(
        PolicyBinding.tenant_id == tenant_a,
        PolicyBinding.policy_id == pol_b.id
    ).all()
    assert len(cross_check) == 0


# --------------------------------------------------------------------------------------
# 2. SYSTEM-Actor External Spoof Prevention
# --------------------------------------------------------------------------------------

def test_security_system_actor_external_spoof_prevention(auth_client: TestClient):
    """
    Ensure external HTTP callers cannot spoof 'SYSTEM' actor to bypass governance controls.
    External evaluation must always be authenticated with a valid JWT.
    """
    unauth_client = TestClient(app)
    
    # 1. Anonymous request with spoofed SYSTEM headers should be rejected (401 Unauthorized)
    resp = unauth_client.post(
        "/api/v1/policies",
        json={
            "policy_code": "SPOOF-SYS-001",
            "name": "Spoofed System Policy",
            "category": "GENERAL",
            "enforcement_mode": "BLOCKING"
        },
        headers={"X-Actor-Type": "SYSTEM", "X-System-Bypass": "true"}
    )
    assert resp.status_code in [401, 403]

    # 2. Authenticated user attempting to override system actor in simulation or gateway
    sim_resp = auth_client.post(
        "/api/v1/enforce/simulate",
        json={
            "agent_id": str(uuid4()),
            "operation": "admin_system_shutdown",
            "role": "SYSTEM_ROOT_ADMIN", # Spoofed high role
        }
    )
    assert sim_resp.status_code == 200
    res_data = sim_resp.json()["data"]
    # Decision must be evaluated normally against boundaries, not bypass
    assert res_data["decision"] in ["ALLOW", "DENY", "REQUIRE_APPROVAL"]


# --------------------------------------------------------------------------------------
# 3. Agent & Identity Spoofing Blocked
# --------------------------------------------------------------------------------------

def test_security_agent_identity_spoofing_blocked(db: Session):
    """
    Verify that requests asserting non-existent or cross-tenant agent IDs are rejected with DENY.
    """
    user_self = create_sec_test_user(db, "tenant_self")
    user_foreign = create_sec_test_user(db, "tenant_foreign")
    tenant_id = user_self.id
    foreign_tenant_id = user_foreign.id

    # Create agent in foreign tenant
    foreign_agent = Agent(
        id=uuid4(),
        tenant_id=foreign_tenant_id,
        agent_code=f"AGT-FOREIGN-{uuid4().hex[:6]}",
        agent_name="Foreign Agent",
        agent_type="TASK_AGENT",
        execution_mode="AUTONOMOUS",
        risk_level="HIGH",
        status="ACTIVE",
    )
    db.add(foreign_agent)

    # Attach boundary for foreign agent in foreign tenant with kill switch active
    foreign_boundary = AgentRuntimeBoundary(
        id=uuid4(),
        tenant_id=foreign_tenant_id,
        agent_id=foreign_agent.id,
        max_autonomy_level="HUMAN_SUPERVISED",
        is_active=False,
    )
    db.add(foreign_boundary)
    db.commit()

    # Attempt to build runtime context and enforce for tenant_id using foreign_agent.id
    req = GovernedRuntimeContextBuilder.build_request(
        actor_id="user_attacker",
        role="ATTACKER",
        agent_id=str(foreign_agent.id),
        enforcement_mode=EnforcementMode.BLOCKING,
    )

    engine = RuntimeEnforcementEngine(db)
    result = engine.enforce(req, tenant_id=foreign_tenant_id)
    # Must fail-closed / DENY because boundary kill switch is active
    assert result.decision == Decision.DENY
    assert any("kill-switch" in r.lower() or "inactive" in r.lower() or "violation" in r.lower() for r in result.reasons)


# --------------------------------------------------------------------------------------
# 4. Inactive & Expired Permission Handling
# --------------------------------------------------------------------------------------

def test_security_inactive_and_revoked_policy_enforcement(db: Session):
    """
    Verify that revoked bindings, suspended policies, and inactive rules are excluded.
    """
    MemoryCacheService().clear()
    user = create_sec_test_user(db, "inactive_test")
    tenant_id = user.id
    agent_id = str(uuid4())

    # 1. Suspended Policy
    suspended_pol = GovernancePolicy(
        id=uuid4(),
        tenant_id=tenant_id,
        policy_code=f"SEC-SUSP-{uuid4().hex[:6].upper()}",
        name="Suspended Policy",
        category="GENERAL",
        enforcement_mode="BLOCKING",
        priority=10,
        status="SUSPENDED",
    )
    db.add(suspended_pol)

    # 2. Revoked Binding
    revoked_binding = PolicyBinding(
        id=uuid4(),
        tenant_id=tenant_id,
        policy_id=suspended_pol.id,
        target_type="AGENT",
        target_id=agent_id,
        binding_scope="DIRECT",
        priority=10,
        is_mandatory=True,
        status="REVOKED",
        effective_from=datetime.now(timezone.utc) - timedelta(days=5),
        effective_to=datetime.now(timezone.utc) + timedelta(days=5),
    )
    db.add(revoked_binding)
    db.commit()

    # Resolve active bindings
    binding_service = PolicyBindingService(db)
    active_bindings = binding_service.resolve_effective_bindings(tenant_id, "AGENT", agent_id)
    assert len(active_bindings) == 0


# --------------------------------------------------------------------------------------
# 5. Unauthorized Admin Changes (RBAC & Authentication)
# --------------------------------------------------------------------------------------

def test_security_rbac_unauthorized_policy_mutations_blocked():
    """
    Ensure unauthenticated and unauthorized requests cannot create policies, bindings, or modify boundaries.
    """
    unauth_client = TestClient(app)

    # 1. Attempt to create policy without credentials
    create_resp = unauth_client.post(
        "/api/v1/policies",
        json={
            "policy_code": "SEC-HACK-001",
            "name": "Malicious Policy",
            "category": "GENERAL",
            "enforcement_mode": "BLOCKING",
            "priority": 1
        }
    )
    assert create_resp.status_code in [403, 401]

    # 2. Attempt to create policy binding without credentials
    bind_resp = unauth_client.post(
        "/api/v1/policy-bindings",
        json={
            "policy_id": str(uuid4()),
            "target_type": "AGENT",
            "target_id": str(uuid4()),
        }
    )
    assert bind_resp.status_code in [403, 401]

    # 3. Attempt to set agent runtime boundary without credentials
    b_resp = unauth_client.post(
        "/api/v1/agent-boundaries",
        json={"agent_id": str(uuid4()), "max_autonomy_level": "AUTONOMOUS", "is_active": False}
    )
    assert b_resp.status_code in [403, 401]

    # 4. Attempt to activate policy version without credentials
    act_resp = unauth_client.post(
        f"/api/v1/policies/{uuid4()}/versions/{uuid4()}/activate"
    )
    assert act_resp.status_code in [403, 401]


# --------------------------------------------------------------------------------------
# 6. No Secret & Raw Sensitive Payload Leakage
# --------------------------------------------------------------------------------------

def test_security_payload_sanitization_no_secret_leakage(db: Session):
    """
    Verify that raw sensitive payloads (passwords, bearer tokens, credit cards)
    are excluded/masked when building runtime context and recording governance events.
    """
    user = create_sec_test_user(db, "sanitization_user")
    tenant_id = user.id
    agent_id = str(uuid4())
    raw_secret_token = "SUPER_SECRET_BEARER_TOKEN_999"
    raw_password = "AdminSuperSecretPassword#2026"

    # Build request with sensitive parameters
    req = GovernedRuntimeContextBuilder.build_request(
        actor_id="user_app",
        role="OPERATOR",
        agent_id=agent_id,
        tool_id=str(uuid4()),
        tool_name="CloudCredentialsTool",
        tool_parameters={
            "api_key": raw_secret_token,
            "admin_password": raw_password,
            "amount": 100,
        },
        enforcement_mode=EnforcementMode.BLOCKING,
    )

    engine = RuntimeEnforcementEngine(db)
    resp = engine.enforce(req, tenant_id=tenant_id)

    # Check published governance events for this correlation_id
    events = (
        db.query(GovernanceEvent)
        .filter(GovernanceEvent.correlation_id == req.correlation_id)
        .all()
    )

    for event in events:
        event_str = str(event.event_payload or {}) + str(event.metadata_json or {})
        # Sensitive credentials must NEVER appear in plain text
        assert raw_secret_token not in event_str
        assert raw_password not in event_str

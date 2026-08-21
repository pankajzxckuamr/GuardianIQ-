from datetime import datetime, timezone, timedelta
from uuid import uuid4
import pytest
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
import app.db.base
from app.modules.auth.models import User
from app.modules.agent.models import Agent
from app.modules.registry.models import Tool, Workflow
from app.modules.datasource.models import DataSource
from app.modules.ai_model.models import AIModel
from app.modules.policy_engine.models import GovernancePolicy, PolicyVersion
from app.modules.relationship.models import PolicyBinding
from app.modules.relationship.cache_service import MemoryCacheService
from app.modules.policy_engine.binding_service import PolicyBindingService
from app.modules.events.models import GovernanceEvent


def create_test_user(db: Session, email_prefix: str = "user") -> User:
    user = User(
        id=uuid4(),
        name=f"User {email_prefix}",
        full_name="Binding Test User",
        email=f"{email_prefix}_{uuid4().hex[:8]}@guardianiq.ai",
        hashed_password="pw",
    )
    db.add(user)
    db.commit()
    return user


@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    session.rollback()
    session.close()


def test_multi_target_policy_bindings(db: Session):
    user = create_test_user(db, "binding_admin")
    tenant_id = user.id
    service = PolicyBindingService(db)

    # 1. Create a Policy
    policy = GovernancePolicy(
        tenant_id=tenant_id,
        owner_user_id=user.id,
        policy_code=f"POL-BIND-{uuid4().hex[:6]}",
        name="Multi Target Policy",
        status="ACTIVE",
    )
    db.add(policy)

    # 2. Create Target Entities for this tenant
    agent = Agent(
        id=uuid4(),
        tenant_id=tenant_id,
        agent_code=f"AGT-{uuid4().hex[:6]}",
        agent_name="Binding Agent",
        agent_type="AUTONOMOUS",
        execution_mode="AUTONOMOUS",
        risk_level="LOW",
        status="ACTIVE",
    )
    tool = Tool(
        id=uuid4(),
        tenant_id=tenant_id,
        tool_code=f"TL-{uuid4().hex[:6]}",
        tool_name="Binding Tool",
        tool_category="DATABASE",
        access_mode="READ_ONLY",
        sensitivity_level="LOW",
        allowed_operations_json=["get_data"],
        status="ACTIVE",
    )
    ds = DataSource(
        id=uuid4(),
        tenant_id=tenant_id,
        source_code=f"DS-{uuid4().hex[:6]}",
        source_name="Binding DB",
        source_type="POSTGRESQL",
        classification="CONFIDENTIAL",
        sensitivity_level="HIGH",
        status="ACTIVE",
    )
    db.add_all([agent, tool, ds])
    db.commit()

    # 3. Create Bindings across AGENT, TOOL, DATA_SOURCE
    b_agent = service.create_binding(
        tenant_id=tenant_id,
        user_id=user.id,
        binding_data={
            "policy_id": policy.id,
            "target_type": "AGENT",
            "target_id": str(agent.id),
            "version_strategy": "LATEST",
        },
    )
    assert b_agent.id is not None
    assert b_agent.target_type == "AGENT"

    b_tool = service.create_binding(
        tenant_id=tenant_id,
        user_id=user.id,
        binding_data={
            "policy_id": policy.id,
            "target_type": "TOOL",
            "target_id": str(tool.id),
            "version_strategy": "LATEST",
        },
    )
    assert b_tool.id is not None
    assert b_tool.target_type == "TOOL"

    b_ds = service.create_binding(
        tenant_id=tenant_id,
        user_id=user.id,
        binding_data={
            "policy_id": policy.id,
            "target_type": "DATA_SOURCE",
            "target_id": str(ds.id),
            "version_strategy": "LATEST",
        },
    )
    assert b_ds.id is not None
    assert b_ds.target_type == "DATA_SOURCE"


def test_cross_tenant_target_binding_blocked(db: Session):
    user_a = create_test_user(db, "tenant_a")
    user_b = create_test_user(db, "tenant_b")
    service = PolicyBindingService(db)

    # Policy in Tenant A
    pol_a = GovernancePolicy(
        tenant_id=user_a.id,
        owner_user_id=user_a.id,
        policy_code=f"POL-A-{uuid4().hex[:6]}",
        name="Tenant A Policy",
        status="ACTIVE",
    )
    # Agent in Tenant B
    agt_b = Agent(
        id=uuid4(),
        tenant_id=user_b.id,
        agent_code=f"AGT-B-{uuid4().hex[:6]}",
        agent_name="Tenant B Agent",
        agent_type="AUTONOMOUS",
        execution_mode="AUTONOMOUS",
        risk_level="LOW",
        status="ACTIVE",
    )
    db.add_all([pol_a, agt_b])
    db.commit()

    # Attempt to bind Tenant A's policy to Tenant B's agent from Tenant A context -> must raise ValueError
    with pytest.raises(ValueError) as excinfo:
        service.create_binding(
            tenant_id=user_a.id,
            user_id=user_a.id,
            binding_data={
                "policy_id": pol_a.id,
                "target_type": "AGENT",
                "target_id": str(agt_b.id),
            },
        )
    assert "not found for tenant" in str(excinfo.value).lower()


def test_duplicate_date_overlap_rejection(db: Session):
    user = create_test_user(db, "overlap_user")
    service = PolicyBindingService(db)
    now = datetime.now(timezone.utc)

    policy = GovernancePolicy(
        tenant_id=user.id,
        owner_user_id=user.id,
        policy_code=f"POL-OV-{uuid4().hex[:6]}",
        name="Overlap Policy",
        status="ACTIVE",
    )
    agent = Agent(
        id=uuid4(),
        tenant_id=user.id,
        agent_code=f"AGT-OV-{uuid4().hex[:6]}",
        agent_name="Overlap Agent",
        agent_type="AUTONOMOUS",
        execution_mode="AUTONOMOUS",
        risk_level="LOW",
        status="ACTIVE",
    )
    db.add_all([policy, agent])
    db.commit()

    # 1. Create initial active binding (day 0 to day 10)
    service.create_binding(
        tenant_id=user.id,
        user_id=user.id,
        binding_data={
            "policy_id": policy.id,
            "target_type": "AGENT",
            "target_id": str(agent.id),
            "effective_from": now,
            "effective_to": now + timedelta(days=10),
        },
    )

    # 2. Attempt overlapping binding (day 5 to day 15) -> must raise ValueError
    with pytest.raises(ValueError) as excinfo:
        service.create_binding(
            tenant_id=user.id,
            user_id=user.id,
            binding_data={
                "policy_id": policy.id,
                "target_type": "AGENT",
                "target_id": str(agent.id),
                "effective_from": now + timedelta(days=5),
                "effective_to": now + timedelta(days=15),
            },
        )
    assert "conflicting active binding already exists" in str(excinfo.value).lower()


def test_pinned_version_strategy_validation(db: Session):
    user = create_test_user(db, "pinned_user")
    service = PolicyBindingService(db)

    policy = GovernancePolicy(
        tenant_id=user.id,
        owner_user_id=user.id,
        policy_code=f"POL-PIN-{uuid4().hex[:6]}",
        name="Pinned Policy",
        status="ACTIVE",
    )
    db.add(policy)
    db.flush()

    v1 = PolicyVersion(
        tenant_id=user.id,
        policy_id=policy.id,
        version_number=1,
        status="ACTIVE",
    )
    agent = Agent(
        id=uuid4(),
        tenant_id=user.id,
        agent_code=f"AGT-PIN-{uuid4().hex[:6]}",
        agent_name="Pinned Agent",
        agent_type="AUTONOMOUS",
        execution_mode="AUTONOMOUS",
        risk_level="LOW",
        status="ACTIVE",
    )
    db.add_all([v1, agent])
    db.commit()

    # 1. PINNED without version ID -> fails
    with pytest.raises(ValueError) as excinfo:
        service.create_binding(
            tenant_id=user.id,
            user_id=user.id,
            binding_data={
                "policy_id": policy.id,
                "target_type": "AGENT",
                "target_id": str(agent.id),
                "version_strategy": "PINNED",
                "pinned_policy_version_id": None,
            },
        )
    assert "pinned_policy_version_id is required" in str(excinfo.value).lower()

    # 2. PINNED with valid version ID -> succeeds
    binding = service.create_binding(
        tenant_id=user.id,
        user_id=user.id,
        binding_data={
            "policy_id": policy.id,
            "target_type": "AGENT",
            "target_id": str(agent.id),
            "version_strategy": "PINNED",
            "pinned_policy_version_id": v1.id,
        },
    )
    assert binding.version_strategy == "PINNED"
    assert binding.pinned_policy_version_id == v1.id


def test_binding_lifecycle_cache_and_events(db: Session):
    user = create_test_user(db, "bind_evt_user")
    service = PolicyBindingService(db)
    cache = MemoryCacheService()
    correlation_id = uuid4()

    policy = GovernancePolicy(
        tenant_id=user.id,
        owner_user_id=user.id,
        policy_code=f"POL-EVT-{uuid4().hex[:6]}",
        name="Event Policy",
        status="ACTIVE",
    )
    agent = Agent(
        id=uuid4(),
        tenant_id=user.id,
        agent_code=f"AGT-EVT-{uuid4().hex[:6]}",
        agent_name="Event Agent",
        agent_type="AUTONOMOUS",
        execution_mode="AUTONOMOUS",
        risk_level="LOW",
        status="ACTIVE",
    )
    db.add_all([policy, agent])
    db.commit()

    # 1. Create binding
    binding = service.create_binding(
        tenant_id=user.id,
        user_id=user.id,
        binding_data={
            "policy_id": policy.id,
            "target_type": "AGENT",
            "target_id": str(agent.id),
        },
        correlation_id=correlation_id,
    )
    assert binding.status == "ACTIVE"

    # 2. Test cached retrieval
    resolved = service.resolve_effective_bindings(user.id, "AGENT", str(agent.id))
    assert len(resolved) == 1
    # Check item is in MemoryCache
    cache_key = f"bindings:{user.id}:AGENT:{agent.id}"
    assert cache.get(cache_key) is not None

    # 3. Revoke binding -> cache must be invalidated
    service.revoke_binding(user.id, binding.id, user.id, reason="Testing revocation", correlation_id=correlation_id)
    assert cache.get(cache_key) is None
    assert binding.status == "DEACTIVATED"

    # 4. Check audit events emitted
    events = (
        db.query(GovernanceEvent)
        .filter(GovernanceEvent.tenant_id == user.id, GovernanceEvent.correlation_id == correlation_id)
        .all()
    )
    event_types = [e.event_type for e in events]
    assert "POLICY_BINDING_CREATED" in event_types
    assert "POLICY_BINDING_DEACTIVATED" in event_types

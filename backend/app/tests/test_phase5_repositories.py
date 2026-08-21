from datetime import datetime, timezone, timedelta
from uuid import uuid4
import pytest
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
import app.db.base
from app.modules.auth.models import User
from app.modules.policy_engine.models import (
    GovernancePolicy,
    PolicyVersion,
    PolicyRule,
    PolicyException,
)
from app.modules.agent_boundary.models import (
    AgentRuntimeBoundary,
    ToolCapability,
    AgentToolPermission,
    DataSourceField,
    AgentDataPermission,
)
from app.modules.relationship.models import PolicyBinding, GenericRelationship
from app.modules.relationship.repository import RelationshipRepository
from app.modules.policy_engine.repository import (
    PolicyRepository,
    PolicyVersionRepository,
    PolicyRuleRepository,
    PolicyBindingRepository,
    PolicyExceptionRepository,
)
from app.modules.agent_boundary.repository import AgentBoundaryRepository
from app.modules.tool_governance.repository import ToolGovernanceRepository
from app.modules.data_governance.repository import DataGovernanceRepository


def create_test_user(db: Session, email_prefix: str = "user") -> User:
    user = User(
        id=uuid4(),
        name=f"User {email_prefix}",
        full_name="Repository Test User",
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


def test_repository_strict_tenant_isolation(db: Session):
    user_a = create_test_user(db, "tenant_a")
    user_b = create_test_user(db, "tenant_b")
    tenant_a = user_a.id
    tenant_b = user_b.id

    # Create Policy for Tenant A
    pol_a = GovernancePolicy(
        tenant_id=tenant_a,
        owner_user_id=user_a.id,
        policy_code=f"POL-TENANT-A-{uuid4().hex[:6]}",
        name="Tenant A Policy",
        status="ACTIVE",
    )
    PolicyRepository.create(db, pol_a)
    db.commit()

    # Query with Tenant B ID -> must be isolated (empty / not found)
    pol_from_b = PolicyRepository.get_by_id(db, pol_a.id, tenant_b)
    assert pol_from_b is None

    list_b = PolicyRepository.list_policies(db, tenant_b)
    assert not any(p.id == pol_a.id for p in list_b)

    # Query with Tenant A ID -> found
    pol_from_a = PolicyRepository.get_by_id(db, pol_a.id, tenant_a)
    assert pol_from_a is not None
    assert pol_from_a.id == pol_a.id


def test_effective_date_temporal_filtering(db: Session):
    user = create_test_user(db, "tenant_tempo")
    tenant_id = user.id
    now = datetime.now(timezone.utc)

    # 1. Expired Policy (ended yesterday)
    pol_expired = GovernancePolicy(
        tenant_id=tenant_id,
        owner_user_id=user.id,
        policy_code=f"POL-EXP-{uuid4().hex[:6]}",
        name="Expired Policy",
        status="ACTIVE",
        effective_from=now - timedelta(days=30),
        effective_to=now - timedelta(days=1),
    )
    # 2. Future Policy (starts tomorrow)
    pol_future = GovernancePolicy(
        tenant_id=tenant_id,
        owner_user_id=user.id,
        policy_code=f"POL-FUT-{uuid4().hex[:6]}",
        name="Future Policy",
        status="ACTIVE",
        effective_from=now + timedelta(days=1),
        effective_to=now + timedelta(days=30),
    )
    # 3. Active Policy (started last week, ends next week)
    pol_active = GovernancePolicy(
        tenant_id=tenant_id,
        owner_user_id=user.id,
        policy_code=f"POL-ACT-{uuid4().hex[:6]}",
        name="Active Policy",
        status="ACTIVE",
        effective_from=now - timedelta(days=7),
        effective_to=now + timedelta(days=7),
    )
    PolicyRepository.create(db, pol_expired)
    PolicyRepository.create(db, pol_future)
    PolicyRepository.create(db, pol_active)
    db.commit()

    # Query as of now
    active_policies = PolicyRepository.list_policies(db, tenant_id, as_of=now)
    active_ids = [p.id for p in active_policies]

    assert pol_active.id in active_ids
    assert pol_expired.id not in active_ids
    assert pol_future.id not in active_ids


def test_policy_version_immutability(db: Session):
    user = create_test_user(db, "tenant_ver")
    tenant_id = user.id

    pol = GovernancePolicy(
        tenant_id=tenant_id,
        owner_user_id=user.id,
        policy_code=f"POL-VER-{uuid4().hex[:6]}",
        name="Versioned Policy",
        status="ACTIVE",
    )
    PolicyRepository.create(db, pol)
    db.commit()

    # Create active version
    v_active = PolicyVersion(
        tenant_id=tenant_id,
        policy_id=pol.id,
        version_number=1,
        status="ACTIVE",
        changelog="Active version",
    )
    db.add(v_active)
    db.commit()

    # Attempt to modify active version via update_draft -> should raise ValueError
    v_active.changelog = "Tampered changelog"
    with pytest.raises(ValueError) as excinfo:
        PolicyVersionRepository.update_draft(db, v_active)
    assert "cannot modify immutable policy version" in str(excinfo.value).lower()

    # Create draft version -> should succeed
    v_draft = PolicyVersion(
        tenant_id=tenant_id,
        policy_id=pol.id,
        version_number=2,
        status="DRAFT",
        changelog="Draft v2",
    )
    PolicyVersionRepository.create_draft(db, v_draft)
    v_draft.changelog = "Updated Draft v2"
    updated = PolicyVersionRepository.update_draft(db, v_draft)
    assert updated.changelog == "Updated Draft v2"


def test_transitive_relationship_resolution(db: Session):
    user = create_test_user(db, "tenant_rel")
    tenant_id = user.id
    agent_id = str(uuid4())
    workflow_id = str(uuid4())
    policy_id = uuid4()
    now = datetime.now(timezone.utc)

    # 1. Create a policy
    pol = GovernancePolicy(
        id=policy_id,
        tenant_id=tenant_id,
        owner_user_id=user.id,
        policy_code=f"POL-WF-{uuid4().hex[:6]}",
        name="Workflow Inherited Policy",
        status="ACTIVE",
    )
    PolicyRepository.create(db, pol)

    # 2. Bind Policy to Workflow
    wf_binding = PolicyBinding(
        tenant_id=tenant_id,
        policy_id=policy_id,
        target_type="WORKFLOW",
        target_id=workflow_id,
        status="ACTIVE",
        effective_from=now - timedelta(days=1),
        effective_to=now + timedelta(days=10),
    )
    PolicyBindingRepository.create(db, wf_binding)

    # 3. Create active relationship: Agent GOVERNED_BY Workflow
    rel = GenericRelationship(
        tenant_id=tenant_id,
        source_type="AGENT",
        source_id=agent_id,
        relationship_type="GOVERNED_BY",
        target_type="WORKFLOW",
        target_id=workflow_id,
        relationship_scope="HIERARCHICAL",
        status="ACTIVE",
        effective_from=now - timedelta(days=1),
        effective_to=now + timedelta(days=10),
    )
    RelationshipRepository.create(db, rel)
    db.commit()

    # 4. Resolve effective bindings for agent -> should resolve inherited workflow policy
    effective_bindings = PolicyBindingRepository.resolve_effective_bindings_for_agent(
        db, tenant_id, agent_id, as_of=now
    )
    assert len(effective_bindings) > 0
    resolved_policy_ids = [b.policy_id for b in effective_bindings]
    assert policy_id in resolved_policy_ids


def test_expired_relationship_ignored_in_resolution(db: Session):
    user = create_test_user(db, "tenant_exp_rel")
    tenant_id = user.id
    agent_id = str(uuid4())
    workflow_id = str(uuid4())
    policy_id = uuid4()
    now = datetime.now(timezone.utc)

    # 1. Create Policy
    pol = GovernancePolicy(
        id=policy_id,
        tenant_id=tenant_id,
        owner_user_id=user.id,
        policy_code=f"POL-EXP-REL-{uuid4().hex[:6]}",
        name="Workflow Policy",
        status="ACTIVE",
    )
    PolicyRepository.create(db, pol)

    # 2. Bind Policy to Workflow
    wf_binding = PolicyBinding(
        tenant_id=tenant_id,
        policy_id=policy_id,
        target_type="WORKFLOW",
        target_id=workflow_id,
        status="ACTIVE",
    )
    PolicyBindingRepository.create(db, wf_binding)

    # 3. Create EXPIRED relationship: Agent GOVERNED_BY Workflow (expired yesterday)
    rel = GenericRelationship(
        tenant_id=tenant_id,
        source_type="AGENT",
        source_id=agent_id,
        relationship_type="GOVERNED_BY",
        target_type="WORKFLOW",
        target_id=workflow_id,
        relationship_scope="HIERARCHICAL",
        status="ACTIVE",
        effective_from=now - timedelta(days=30),
        effective_to=now - timedelta(days=1),  # Expired
    )
    RelationshipRepository.create(db, rel)
    db.commit()

    # 4. Resolve effective bindings for agent as of now -> should NOT resolve expired workflow binding
    effective_bindings = PolicyBindingRepository.resolve_effective_bindings_for_agent(
        db, tenant_id, agent_id, as_of=now
    )
    resolved_policy_ids = [b.policy_id for b in effective_bindings]
    assert policy_id not in resolved_policy_ids

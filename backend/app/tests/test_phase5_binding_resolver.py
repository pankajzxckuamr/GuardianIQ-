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
from app.modules.policy_engine.models import GovernancePolicy, PolicyVersion, PolicyRule
from app.modules.relationship.models import PolicyBinding, GenericRelationship
from app.modules.policy_engine.resolver import BindingResolver, ResolvedPolicySet


def create_test_user(db: Session, email_prefix: str = "resolver") -> User:
    user = User(
        id=uuid4(),
        name=f"User {email_prefix}",
        full_name="Resolver Test User",
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


def test_hierarchical_scope_precedence(db: Session):
    user = create_test_user(db, "scope_precedence")
    tenant_id = user.id
    resolver = BindingResolver(db)
    now = datetime.now(timezone.utc)

    # 1. Create a Policy with 2 versions
    policy = GovernancePolicy(
        tenant_id=tenant_id,
        owner_user_id=user.id,
        policy_code=f"POL-SCOPE-{uuid4().hex[:6]}",
        name="Scope Override Policy",
        status="ACTIVE",
    )
    db.add(policy)
    db.flush()

    v1 = PolicyVersion(
        tenant_id=tenant_id,
        policy_id=policy.id,
        version_number=1,
        status="SUPERSEDED",
    )
    v2 = PolicyVersion(
        tenant_id=tenant_id,
        policy_id=policy.id,
        version_number=2,
        status="ACTIVE",
    )
    db.add_all([v1, v2])

    agent = Agent(
        id=uuid4(),
        tenant_id=tenant_id,
        agent_code=f"AGT-SCOPE-{uuid4().hex[:6]}",
        agent_name="Scope Agent",
        agent_type="AUTONOMOUS",
        execution_mode="AUTONOMOUS",
        risk_level="LOW",
        status="ACTIVE",
    )
    workflow = Workflow(
        id=uuid4(),
        tenant_id=tenant_id,
        workflow_code=f"WF-SCOPE-{uuid4().hex[:6]}",
        workflow_name="Scope Workflow",
        workflow_type="AUTOMATION",
        business_criticality="HIGH",
        status="ACTIVE",
    )
    db.add_all([agent, workflow])
    db.commit()

    # 2. Workflow Binding (pinned to V1, priority 100)
    wf_binding = PolicyBinding(
        tenant_id=tenant_id,
        policy_id=policy.id,
        target_type="WORKFLOW",
        target_id=str(workflow.id),
        status="ACTIVE",
        version_strategy="PINNED",
        pinned_policy_version_id=v1.id,
        priority=100,
        effective_from=now,
    )
    # 3. Direct Agent Binding (LATEST, priority 50)
    agent_binding = PolicyBinding(
        tenant_id=tenant_id,
        policy_id=policy.id,
        target_type="AGENT",
        target_id=str(agent.id),
        status="ACTIVE",
        version_strategy="LATEST",
        priority=50,
        effective_from=now,
    )
    db.add_all([wf_binding, agent_binding])

    # 4. Agent PARTICIPATES_IN_WORKFLOW Workflow
    rel = GenericRelationship(
        tenant_id=tenant_id,
        source_type="AGENT",
        source_id=str(agent.id),
        relationship_type="PARTICIPATES_IN_WORKFLOW",
        target_type="WORKFLOW",
        target_id=str(workflow.id),
        relationship_scope="HIERARCHICAL",
        effective_from=now,
        status="ACTIVE",
    )
    db.add(rel)
    db.commit()

    # 5. Resolve Runtime Policies for Agent -> DIRECT scope MUST win over WORKFLOW scope
    res: ResolvedPolicySet = resolver.resolve_runtime_policies(
        tenant_id=tenant_id,
        agent_id=str(agent.id),
        as_of=now,
    )
    assert len(res.resolved_policies) == 1
    resolved = res.resolved_policies[0]
    assert resolved.resolved_scope == "DIRECT"
    assert resolved.version.version_number == 2  # LATEST version selected by Direct binding
    assert resolved.binding.id == agent_binding.id


def test_relationship_literal_normalization(db: Session):
    user = create_test_user(db, "rel_literal")
    tenant_id = user.id
    resolver = BindingResolver(db)
    now = datetime.now(timezone.utc)

    # Create Policy for Tool
    pol_tool = GovernancePolicy(
        tenant_id=tenant_id,
        owner_user_id=user.id,
        policy_code=f"POL-TL-{uuid4().hex[:6]}",
        name="Tool Policy",
        status="ACTIVE",
    )
    # Create Policy for DataSource
    pol_ds = GovernancePolicy(
        tenant_id=tenant_id,
        owner_user_id=user.id,
        policy_code=f"POL-DS-{uuid4().hex[:6]}",
        name="DS Policy",
        status="ACTIVE",
    )
    db.add_all([pol_tool, pol_ds])
    db.flush()

    v_tl = PolicyVersion(tenant_id=tenant_id, policy_id=pol_tool.id, version_number=1, status="ACTIVE")
    v_ds = PolicyVersion(tenant_id=tenant_id, policy_id=pol_ds.id, version_number=1, status="ACTIVE")
    db.add_all([v_tl, v_ds])

    agent = Agent(
        id=uuid4(),
        tenant_id=tenant_id,
        agent_code=f"AGT-LIT-{uuid4().hex[:6]}",
        agent_name="Lit Agent",
        agent_type="AUTONOMOUS",
        execution_mode="AUTONOMOUS",
        risk_level="LOW",
        status="ACTIVE",
    )
    tool = Tool(
        id=uuid4(),
        tenant_id=tenant_id,
        tool_code=f"TL-LIT-{uuid4().hex[:6]}",
        tool_name="Lit Tool",
        tool_category="API",
        access_mode="EXECUTE",
        sensitivity_level="LOW",
        allowed_operations_json=["invoke"],
        status="ACTIVE",
    )
    ds = DataSource(
        id=uuid4(),
        tenant_id=tenant_id,
        source_code=f"DS-LIT-{uuid4().hex[:6]}",
        source_name="Lit DB",
        source_type="SQL",
        classification="CONFIDENTIAL",
        sensitivity_level="HIGH",
        status="ACTIVE",
    )
    db.add_all([agent, tool, ds])
    db.flush()

    # Bindings
    b_tool = PolicyBinding(
        tenant_id=tenant_id,
        policy_id=pol_tool.id,
        target_type="TOOL",
        target_id=str(tool.id),
        status="ACTIVE",
        version_strategy="LATEST",
        effective_from=now,
    )
    b_ds = PolicyBinding(
        tenant_id=tenant_id,
        policy_id=pol_ds.id,
        target_type="DATA_SOURCE",
        target_id=str(ds.id),
        status="ACTIVE",
        version_strategy="LATEST",
        effective_from=now,
    )
    db.add_all([b_tool, b_ds])

    # Relationships: one using explicit USES_TOOL, one using generic USES with DATA_SOURCE target
    rel1 = GenericRelationship(
        tenant_id=tenant_id,
        source_type="AGENT",
        source_id=str(agent.id),
        relationship_type="USES_TOOL",
        target_type="TOOL",
        target_id=str(tool.id),
        effective_from=now,
        status="ACTIVE",
    )
    rel2 = GenericRelationship(
        tenant_id=tenant_id,
        source_type="AGENT",
        source_id=str(agent.id),
        relationship_type="USES",
        target_type="DATA_SOURCE",
        target_id=str(ds.id),
        effective_from=now,
        status="ACTIVE",
    )
    db.add_all([rel1, rel2])
    db.commit()

    # Resolve policies via agent graph lookup
    res: ResolvedPolicySet = resolver.resolve_runtime_policies(
        tenant_id=tenant_id,
        agent_id=str(agent.id),
        as_of=now,
    )
    assert len(res.resolved_policies) == 2
    policy_ids = [rp.policy.id for rp in res.resolved_policies]
    assert pol_tool.id in policy_ids
    assert pol_ds.id in policy_ids


def test_deterministic_resolution_hash_and_trace(db: Session):
    user = create_test_user(db, "hash_trace")
    tenant_id = user.id
    resolver = BindingResolver(db)
    now = datetime.now(timezone.utc)

    policy = GovernancePolicy(
        tenant_id=tenant_id,
        owner_user_id=user.id,
        policy_code=f"POL-HT-{uuid4().hex[:6]}",
        name="Hash Trace Policy",
        status="ACTIVE",
        effective_from=now,
    )
    db.add(policy)
    db.flush()

    v1 = PolicyVersion(tenant_id=tenant_id, policy_id=policy.id, version_number=1, status="ACTIVE")
    db.add(v1)
    db.flush()

    r1 = PolicyRule(
        tenant_id=tenant_id,
        policy_version_id=v1.id,
        rule_code="RULE-HT-01",
        name="Hash Rule 1",
        rule_type="GENERAL",
        target_type="AGENT",
        target_id="*",
        condition_expression="true",
        condition_json={},
        action="DENY",
        severity="HIGH",
        execution_order=1,
        is_active=True,
    )
    db.add(r1)

    agent = Agent(
        id=uuid4(),
        tenant_id=tenant_id,
        agent_code=f"AGT-HT-{uuid4().hex[:6]}",
        agent_name="Hash Agent",
        agent_type="AUTONOMOUS",
        execution_mode="AUTONOMOUS",
        risk_level="LOW",
        status="ACTIVE",
    )
    db.add(agent)
    db.flush()

    binding = PolicyBinding(
        tenant_id=tenant_id,
        policy_id=policy.id,
        target_type="AGENT",
        target_id=str(agent.id),
        status="ACTIVE",
        version_strategy="LATEST",
        effective_from=now,
    )
    db.add(binding)
    db.commit()

    # Resolution 1
    res1 = resolver.resolve_runtime_policies(tenant_id, agent_id=str(agent.id), as_of=now)
    # Resolution 2
    res2 = resolver.resolve_runtime_policies(tenant_id, agent_id=str(agent.id), as_of=now)

    # Hashes must be identical and 64 hex characters
    assert res1.resolution_hash == res2.resolution_hash
    assert len(res1.resolution_hash) == 64

    # Check trace content
    assert len(res1.resolution_trace) == 1
    trace = res1.resolution_trace[0]
    assert trace["policy_code"] == policy.policy_code
    assert trace["version_number"] == 1
    assert trace["resolved_scope"] == "DIRECT"
    assert trace["rules_count"] == 1


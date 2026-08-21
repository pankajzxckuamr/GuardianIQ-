from uuid import uuid4
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import pytest
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
import app.db.base
from app.modules.auth.models import User
from app.modules.agent.models import Agent
from app.modules.registry.models import Tool
from app.modules.datasource.models import DataSource
from app.modules.ai_model.models import AIModel, AIModelProvider
from app.modules.agent_boundary.models import AgentRuntimeBoundary, ToolCapability, DataSourceField, AgentDataPermission
from app.modules.relationship.models import GenericRelationship
from app.modules.policy_engine.models import GovernancePolicy, PolicyVersion, PolicyRule
from app.modules.relationship.models import PolicyBinding
from app.modules.enforcement.context_builder import GovernedRuntimeContextBuilder
from app.modules.enforcement.engine import RuntimeEnforcementEngine
from app.modules.policy_engine.enums import Decision, EnforcementMode


def create_test_user(db: Session, email_prefix: str = "enforce") -> User:
    user = User(
        id=uuid4(),
        name=f"User {email_prefix}",
        full_name="Enforcement Engine User",
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


def test_full_multi_layered_governance_pass(db: Session):
    user = create_test_user(db, "full_pass")
    tenant_id = user.id
    engine = RuntimeEnforcementEngine(db)
    now = datetime.now(timezone.utc)

    # 1. Setup Base Entities
    agent = Agent(
        id=uuid4(),
        tenant_id=tenant_id,
        agent_code=f"AGT-EP-{uuid4().hex[:6]}",
        agent_name="Enforce Pass Agent",
        agent_type="AUTONOMOUS",
        execution_mode="AUTONOMOUS",
        risk_level="LOW",
        status="ACTIVE",
    )
    tool = Tool(
        id=uuid4(),
        tenant_id=tenant_id,
        tool_code=f"TL-EP-{uuid4().hex[:6]}",
        tool_name="Search Tool",
        tool_category="SEARCH",
        access_mode="READ",
        sensitivity_level="LOW",
        allowed_operations_json=["search_docs"],
        status="ACTIVE",
    )
    model = AIModel(
        id=uuid4(),
        tenant_id=tenant_id,
        model_code=f"MDL-EP-{uuid4().hex[:6]}",
        model_name="GPT-4o Pass",
        model_type="LLM",
        purpose="General Search",
        deployment_environment="PRODUCTION",
        version="v1.0",
        status="ACTIVE",
    )
    db.add_all([agent, tool, model])
    db.flush()

    # 2. Setup Dependent Boundaries & Relationships
    boundary = AgentRuntimeBoundary(
        id=uuid4(),
        tenant_id=tenant_id,
        agent_id=agent.id,
        max_autonomy_level="AUTONOMOUS",
        allowed_access_modes_json=["READ_ONLY", "EXECUTE", "WRITE"],
        is_active=True,
    )
    cap = ToolCapability(
        id=uuid4(),
        tenant_id=tenant_id,
        tool_id=tool.id,
        capability_name="search_docs",
        access_mode="READ",
    )
    rel_tool = GenericRelationship(
        tenant_id=tenant_id,
        source_type="AGENT",
        source_id=str(agent.id),
        relationship_type="USES_TOOL",
        target_type="TOOL",
        target_id=str(tool.id),
        effective_from=now,
        status="ACTIVE",
    )
    rel_model = GenericRelationship(
        tenant_id=tenant_id,
        source_type="AGENT",
        source_id=str(agent.id),
        relationship_type="USES_MODEL",
        target_type="MODEL",
        target_id=str(model.id),
        effective_from=now,
        status="ACTIVE",
    )
    db.add_all([boundary, cap, rel_tool, rel_model])
    db.commit()

    # Build canonical request
    req = GovernedRuntimeContextBuilder.build_request(
        tenant_id=tenant_id,
        agent_id=str(agent.id),
        tool_id=str(tool.id),
        tool_name="search_docs",
        operation="search_docs",
        model_id=str(model.id),
        environment="PRODUCTION",
    )

    resp = engine.enforce(req, tenant_id=tenant_id)
    assert resp.decision == Decision.ALLOW
    assert resp.execution_permitted is True
    assert resp.trace is not None
    assert len(resp.trace["steps"]) >= 3


def test_agent_boundary_and_tool_guard_interception(db: Session):
    user = create_test_user(db, "boundary_block")
    tenant_id = user.id
    engine = RuntimeEnforcementEngine(db)
    now = datetime.now(timezone.utc)

    # Inactive agent boundary kill-switch
    agent = Agent(
        id=uuid4(),
        tenant_id=tenant_id,
        agent_code=f"AGT-BLK-{uuid4().hex[:6]}",
        agent_name="Blocked Agent",
        agent_type="AUTONOMOUS",
        execution_mode="AUTONOMOUS",
        risk_level="LOW",
        status="ACTIVE",
    )
    db.add(agent)
    db.flush()

    boundary = AgentRuntimeBoundary(
        id=uuid4(),
        tenant_id=tenant_id,
        agent_id=agent.id,
        max_autonomy_level="AUTONOMOUS",
        allowed_access_modes_json=["READ_ONLY"],
        is_active=False,  # KILL-SWITCH ACTIVE
    )
    db.add(boundary)
    db.commit()

    req = GovernedRuntimeContextBuilder.build_request(
        tenant_id=tenant_id,
        agent_id=str(agent.id),
        autonomy_level="AUTONOMOUS",
    )

    resp = engine.enforce(req, tenant_id=tenant_id)
    assert resp.decision == Decision.DENY
    assert resp.execution_permitted is False
    assert any("kill-switch" in r.lower() for r in resp.reasons)


def test_dynamic_policy_engine_rule_combining(db: Session):
    user = create_test_user(db, "policy_eval")
    tenant_id = user.id
    engine = RuntimeEnforcementEngine(db)
    now = datetime.now(timezone.utc)

    agent = Agent(
        id=uuid4(),
        tenant_id=tenant_id,
        agent_code=f"AGT-POL-{uuid4().hex[:6]}",
        agent_name="Policy Governed Agent",
        agent_type="AUTONOMOUS",
        execution_mode="AUTONOMOUS",
        risk_level="LOW",
        status="ACTIVE",
    )
    db.add(agent)
    db.flush()

    boundary = AgentRuntimeBoundary(
        id=uuid4(),
        tenant_id=tenant_id,
        agent_id=agent.id,
        max_autonomy_level="AUTONOMOUS",
        allowed_access_modes_json=["READ_ONLY", "EXECUTE", "WRITE"],
        is_active=True,
    )
    # Dynamic Policy with DENY Rule
    pol = GovernancePolicy(
        id=uuid4(),
        tenant_id=tenant_id,
        policy_code=f"POL-GOV-{uuid4().hex[:6]}",
        name="Production Safety Policy",
        category="AGENT_BOUNDARY",
        status="ACTIVE",
    )
    db.add_all([boundary, pol])
    db.flush()

    v1 = PolicyVersion(
        id=uuid4(),
        tenant_id=tenant_id,
        policy_id=pol.id,
        version_number=1,
        status="ACTIVE",
    )
    db.add(v1)
    db.flush()

    rule = PolicyRule(
        id=uuid4(),
        tenant_id=tenant_id,
        policy_version_id=v1.id,
        rule_code="RULE-PROD-DENY",
        name="Deny Unsupervised Destructive Ops",
        rule_type="EXECUTION",
        target_type="AGENT",
        target_id=str(agent.id),
        condition_json={
            "field": "facts.operation",
            "operator": "EQ",
            "value": "delete_database",
        },
        action="DENY",
        severity="CRITICAL",
        execution_order=1,
    )
    binding = PolicyBinding(
        id=uuid4(),
        tenant_id=tenant_id,
        policy_id=pol.id,
        target_type="AGENT",
        target_id=str(agent.id),
        binding_scope="DIRECT",
        priority=100,
        status="ACTIVE",
    )
    db.add_all([rule, binding])
    db.commit()

    # Request with facts.operation == "delete_database" -> DENIED by Layer 3 Policy Rule
    req = GovernedRuntimeContextBuilder.build_request(
        tenant_id=tenant_id,
        agent_id=str(agent.id),
        operation="delete_database",
    )

    resp = engine.enforce(req, tenant_id=tenant_id)
    assert resp.decision == Decision.DENY
    assert resp.execution_permitted is False
    assert any("RULE-PROD-DENY" in v for v in resp.violations)

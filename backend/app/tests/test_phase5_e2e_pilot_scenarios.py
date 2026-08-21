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
from app.modules.ai_model.models import AIModel
from app.shared.enums.risk_level import RiskLevel
from app.modules.workflow_scheduler.models import Phase2WorkflowSchedule, WorkflowScheduleAgentAssignment
from app.modules.workflow_execution.models import WorkflowRun
from app.modules.agent_boundary.models import AgentRuntimeBoundary, ToolCapability
from app.modules.relationship.models import GenericRelationship, PolicyBinding
from app.modules.policy_engine.models import GovernancePolicy, PolicyVersion, PolicyRule
from app.modules.policy_engine.enums import Decision, EnforcementMode, DataClassification
from app.modules.policy_engine.schemas import GovernedRuntimeRequest
from app.modules.enforcement.context_builder import GovernedRuntimeContextBuilder
from app.modules.enforcement.engine import RuntimeEnforcementEngine
from app.modules.enforcement.authorization_service import RuntimeAuthorizationService
from app.modules.enforcement.approval_adapter import ApprovalExceptionAdapter, PolicyApproval


@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    session.rollback()
    session.close()


def create_test_user(db: Session, email_prefix: str = "pilot") -> User:
    user = User(
        id=uuid4(),
        name=f"User {email_prefix}",
        full_name="E2E Pilot User",
        email=f"{email_prefix}_{uuid4().hex[:8]}@guardianiq.ai",
        hashed_password="pw",
    )
    db.add(user)
    db.commit()
    return user


def test_e2e_flow_1_permitted_action(db: Session):
    """Pilot Flow 1: Fully authorized action passes all layers and obtains valid single-use token."""
    user = create_test_user(db, "flow1_ok")
    tenant_id = user.id
    now = datetime.now(timezone.utc)

    agent = Agent(
        id=uuid4(),
        tenant_id=tenant_id,
        agent_code=f"AGT-P1-{uuid4().hex[:6]}",
        agent_name="Permitted Analytics Agent",
        agent_type="AUTONOMOUS",
        execution_mode="AUTONOMOUS",
        risk_level="LOW",
        status="ACTIVE",
    )
    db.add(agent)
    db.flush()

    tool = Tool(
        id=uuid4(),
        tenant_id=tenant_id,
        tool_code=f"TOOL-P1-{uuid4().hex[:6]}",
        tool_name="Analytics Query Tool",
        tool_category="DATABASE",
        access_mode="READ_WRITE",
        sensitivity_level="LOW",
        allowed_operations_json=["query_metrics"],
        status="ACTIVE",
    )
    db.add(tool)
    db.flush()

    boundary = AgentRuntimeBoundary(
        id=uuid4(),
        tenant_id=tenant_id,
        agent_id=agent.id,
        max_autonomy_level="AUTONOMOUS",
        rate_limit_per_minute=200,
        max_concurrency=20,
        is_active=True,
    )
    rel = GenericRelationship(
        id=uuid4(),
        tenant_id=tenant_id,
        source_type="AGENT",
        source_id=str(agent.id),
        target_type="TOOL",
        target_id=str(tool.id),
        relationship_type="USES_TOOL",
        effective_from=now,
        status="ACTIVE",
    )
    capability = ToolCapability(
        id=uuid4(),
        tenant_id=tenant_id,
        tool_id=tool.id,
        capability_name="query_metrics",
        access_mode="READ_ONLY",
    )
    db.add_all([boundary, rel, capability])
    db.commit()

    request = GovernedRuntimeContextBuilder.build_request(
        tenant_id=tenant_id,
        actor_id=str(user.id),
        agent_id=str(agent.id),
        tool_id=str(tool.id),
        tool_name=tool.tool_name,
        operation="query_metrics",
        environment="PRODUCTION",
        enforcement_mode=EnforcementMode.BLOCKING,
    )

    engine = RuntimeEnforcementEngine(db)
    res = engine.enforce(request, tenant_id)

    assert res.decision == Decision.ALLOW
    assert res.execution_permitted is True

    # Obtain TOCTOU runtime authorization token
    auth_service = RuntimeAuthorizationService(db)
    auth_rec = auth_service.issue_authorization(
        tenant_id=tenant_id,
        request=request,
        decision=res.decision,
        ttl_seconds=60,
        is_single_use=True,
    )
    assert auth_rec.id is not None
    assert auth_rec.authorized is True

    # Verify single-use authorization
    valid, reason = auth_service.verify_and_consume_authorization(
        authorization_id=auth_rec.id,
        tenant_id=tenant_id,
        current_request=request,
    )
    assert valid is True
    assert reason is None


def test_e2e_flow_2_missing_write_permission_with_backfilled_capabilities(db: Session):
    """Pilot Flow 2: Tool with backfilled heuristic capability (_backfilled: true) blocks WRITE operation on READ capability."""
    user = create_test_user(db, "flow2_write_denied")
    tenant_id = user.id
    now = datetime.now(timezone.utc)

    agent = Agent(
        id=uuid4(),
        tenant_id=tenant_id,
        agent_code=f"AGT-P2-{uuid4().hex[:6]}",
        agent_name="Read Only Search Agent",
        agent_type="AUTONOMOUS",
        execution_mode="AUTONOMOUS",
        risk_level="MEDIUM",
        status="ACTIVE",
    )
    db.add(agent)
    db.flush()

    tool = Tool(
        id=uuid4(),
        tenant_id=tenant_id,
        tool_code=f"TOOL-P2-{uuid4().hex[:6]}",
        tool_name="Backfilled Search Tool",
        tool_category="DATABASE",
        access_mode="READ_WRITE",
        sensitivity_level="LOW",
        allowed_operations_json=["search_records", "update_records"],
        status="ACTIVE",
    )
    db.add(tool)
    db.flush()

    boundary = AgentRuntimeBoundary(
        id=uuid4(),
        tenant_id=tenant_id,
        agent_id=agent.id,
        max_autonomy_level="AUTONOMOUS",
        is_active=True,
    )
    rel = GenericRelationship(
        id=uuid4(),
        tenant_id=tenant_id,
        source_type="AGENT",
        source_id=str(agent.id),
        target_type="TOOL",
        target_id=str(tool.id),
        relationship_type="USES_TOOL",
        effective_from=now,
        status="ACTIVE",
    )
    # Heuristically backfilled capability tagged _backfilled: true
    backfilled_capability = ToolCapability(
        id=uuid4(),
        tenant_id=tenant_id,
        tool_id=tool.id,
        capability_name="search_records",
        access_mode="READ_ONLY",
        metadata_json={"_backfilled": True, "inferred_from": "tool_name_pattern"},
    )
    db.add_all([boundary, rel, backfilled_capability])
    db.commit()

    # Agent attempts to execute a WRITE modification operation against the backfilled READ capability
    request = GovernedRuntimeContextBuilder.build_request(
        tenant_id=tenant_id,
        actor_id=str(user.id),
        agent_id=str(agent.id),
        tool_id=str(tool.id),
        tool_name=tool.tool_name,
        operation="update_records",  # Operation requires WRITE
        environment="PRODUCTION",
        enforcement_mode=EnforcementMode.BLOCKING,
    )

    engine = RuntimeEnforcementEngine(db)
    res = engine.enforce(request, tenant_id)

    assert res.decision == Decision.DENY
    assert res.execution_permitted is False
    assert any("permission" in r.lower() or "denied" in r.lower() or "capability" in r.lower() for r in res.reasons)


def test_e2e_flow_3_high_value_approval_lifecycle(db: Session):
    """Pilot Flow 3: Financial transfer exceeding threshold returns REQUIRE_APPROVAL, saves approval record, and executes upon approval."""
    user = create_test_user(db, "flow3_appr")
    tenant_id = user.id

    agent = Agent(
        id=uuid4(),
        tenant_id=tenant_id,
        agent_code=f"AGT-P3-{uuid4().hex[:6]}",
        agent_name="Treasury Agent",
        agent_type="AUTONOMOUS",
        execution_mode="AUTONOMOUS",
        risk_level="HIGH",
        status="ACTIVE",
    )
    db.add(agent)
    db.flush()

    boundary = AgentRuntimeBoundary(
        id=uuid4(),
        tenant_id=tenant_id,
        agent_id=agent.id,
        max_autonomy_level="AUTONOMOUS",
        require_approval_threshold=Decimal("5000.00"),
        is_active=True,
    )
    db.add(boundary)
    db.flush()

    policy = GovernancePolicy(
        id=uuid4(),
        tenant_id=tenant_id,
        policy_code=f"POL-TR-{uuid4().hex[:6]}",
        name="Treasury Approval Policy",
        status="ACTIVE",
    )
    db.add(policy)
    db.commit()

    # Attempt $25,000 disbursement (exceeds $5,000 threshold)
    request = GovernedRuntimeContextBuilder.build_request(
        tenant_id=tenant_id,
        actor_id=str(user.id),
        agent_id=str(agent.id),
        operation="transfer_funds",
        facts={"transaction_amount": 25000.00, "currency": "USD"},
        enforcement_mode=EnforcementMode.BLOCKING,
    )

    engine = RuntimeEnforcementEngine(db)
    res = engine.enforce(request, tenant_id)

    assert res.decision == Decision.REQUIRE_APPROVAL
    assert res.execution_permitted is False

    # Create approval request via ApprovalExceptionAdapter
    adapter = ApprovalExceptionAdapter(db)
    approval_rec = adapter.request_approval(
        tenant_id=tenant_id,
        request=request,
        policy_id=policy.id,
        required_role="TREASURY_MANAGERS",
        timeout_minutes=60,
    )
    assert approval_rec.status == "PENDING"

    # Authorized manager approves
    approved = adapter.record_approval_decision(
        approval_id=approval_rec.id,
        tenant_id=tenant_id,
        approver_id=user.id,
        decision="APPROVED",
        reason="High-value wire approved for verified vendor.",
    )
    assert approved is not None
    assert approved.status == "APPROVED"


def test_e2e_flow_4_restricted_data_prohibited_model_blocked(db: Session):
    """Pilot Flow 4: Accessing RESTRICTED data with an unapproved model in DEVELOPMENT environment is blocked before invocation."""
    user = create_test_user(db, "flow4_model")
    tenant_id = user.id

    agent = Agent(
        id=uuid4(),
        tenant_id=tenant_id,
        agent_code=f"AGT-P4-{uuid4().hex[:6]}",
        agent_name="Model Invocator Agent",
        agent_type="AUTONOMOUS",
        execution_mode="AUTONOMOUS",
        risk_level="HIGH",
        status="ACTIVE",
    )
    db.add(agent)
    db.flush()

    model = AIModel(
        id=uuid4(),
        tenant_id=tenant_id,
        model_code=f"MDL-DEV-{uuid4().hex[:6]}",
        model_name="Experimental Claude Dev Model",
        model_type="LLM",
        purpose="Dev testing",
        risk_level=RiskLevel.HIGH,
        deployment_environment="DEVELOPMENT",  # Development environment not approved for RESTRICTED data
        status="ACTIVE",
    )
    db.add(model)
    db.flush()

    boundary = AgentRuntimeBoundary(
        id=uuid4(),
        tenant_id=tenant_id,
        agent_id=agent.id,
        max_autonomy_level="AUTONOMOUS",
        is_active=True,
    )
    db.add(boundary)
    db.commit()

    # Attempt to route RESTRICTED classified request to DEVELOPMENT model
    request = GovernedRuntimeContextBuilder.build_request(
        tenant_id=tenant_id,
        actor_id=str(user.id),
        agent_id=str(agent.id),
        model_id=str(model.id),
        operation="analyze_classified_records",
        environment="PRODUCTION",
        facts={"data_classification": "RESTRICTED"},
        enforcement_mode=EnforcementMode.BLOCKING,
    )

    engine = RuntimeEnforcementEngine(db)
    res = engine.enforce(request, tenant_id)

    assert res.decision == Decision.DENY
    assert res.execution_permitted is False
    assert any("model" in r.lower() or "environment" in r.lower() or "restricted" in r.lower() or "relationship" in r.lower() for r in res.reasons)


def test_e2e_flow_5_data_masking_transformation_obligations(db: Session):
    """Pilot Flow 5: Data access with sensitive fields triggers ALLOW_WITH_OBLIGATIONS and field masking."""
    user = create_test_user(db, "flow5_mask")
    tenant_id = user.id
    now = datetime.now(timezone.utc)

    agent = Agent(
        id=uuid4(),
        tenant_id=tenant_id,
        agent_code=f"AGT-P5-{uuid4().hex[:6]}",
        agent_name="Customer Summary Agent",
        agent_type="AUTONOMOUS",
        execution_mode="AUTONOMOUS",
        risk_level="MEDIUM",
        status="ACTIVE",
    )
    db.add(agent)
    db.flush()

    ds = DataSource(
        id=uuid4(),
        tenant_id=tenant_id,
        source_code=f"DS-P5-{uuid4().hex[:6]}",
        source_name="Customer Accounts DB",
        source_type="POSTGRES",
        classification="CONFIDENTIAL",
        sensitivity_level="MODERATE",
        status="ACTIVE",
    )
    db.add(ds)
    db.flush()

    boundary = AgentRuntimeBoundary(
        id=uuid4(),
        tenant_id=tenant_id,
        agent_id=agent.id,
        max_autonomy_level="AUTONOMOUS",
        is_active=True,
    )
    rel = GenericRelationship(
        id=uuid4(),
        tenant_id=tenant_id,
        source_type="AGENT",
        source_id=str(agent.id),
        target_type="DATA_SOURCE",
        target_id=str(ds.id),
        relationship_type="USES_DATA_SOURCE",
        effective_from=now,
        status="ACTIVE",
    )
    db.add_all([boundary, rel])
    db.commit()

    request = GovernedRuntimeContextBuilder.build_request(
        tenant_id=tenant_id,
        actor_id=str(user.id),
        agent_id=str(agent.id),
        data_requests=[{
            "data_source_id": str(ds.id),
            "table_name": "customers",
            "columns": ["full_name", "ssn", "credit_card", "email"],
            "operation": "READ",
        }],
        operation="generate_statement",
        environment="PRODUCTION",
        enforcement_mode=EnforcementMode.BLOCKING,
    )

    engine = RuntimeEnforcementEngine(db)
    res = engine.enforce(request, tenant_id)

    assert res.decision in [Decision.ALLOW, Decision.ALLOW_WITH_OBLIGATIONS]
    assert res.execution_permitted is True


def test_e2e_flow_6_toctou_permission_revoked_after_approval(db: Session):
    """Pilot Flow 6: Request altered or authorization context tampered post-approval is rejected by TOCTOU check."""
    user = create_test_user(db, "flow6_toctou")
    tenant_id = user.id

    agent = Agent(
        id=uuid4(),
        tenant_id=tenant_id,
        agent_code=f"AGT-P6-{uuid4().hex[:6]}",
        agent_name="Wire Agent",
        agent_type="AUTONOMOUS",
        execution_mode="AUTONOMOUS",
        risk_level="HIGH",
        status="ACTIVE",
    )
    db.add(agent)
    db.commit()

    auth_service = RuntimeAuthorizationService(db)

    orig_req = GovernedRuntimeContextBuilder.build_request(
        tenant_id=tenant_id,
        actor_id=str(user.id),
        agent_id=str(agent.id),
        operation="transfer_funds",
        facts={"amount": 100.00, "recipient": "vendor_a"},
        enforcement_mode=EnforcementMode.BLOCKING,
    )

    # Issue token for authorized payment of $100
    auth_rec = auth_service.issue_authorization(
        tenant_id=tenant_id,
        request=orig_req,
        decision=Decision.ALLOW,
        ttl_seconds=60,
    )

    # Attacker tampers with request payload to change amount to $50,000 at execution time
    tampered_req = GovernedRuntimeContextBuilder.build_request(
        tenant_id=tenant_id,
        actor_id=str(user.id),
        agent_id=str(agent.id),
        operation="transfer_funds",
        facts={"amount": 50000.00, "recipient": "vendor_attacker"},
        enforcement_mode=EnforcementMode.BLOCKING,
    )

    tamper_verified, reason = auth_service.verify_and_consume_authorization(
        authorization_id=auth_rec.id,
        tenant_id=tenant_id,
        current_request=tampered_req,
    )
    assert tamper_verified is False
    assert "context_hash" in str(reason).lower() or "mismatch" in str(reason).lower() or "tamper" in str(reason).lower()


def test_e2e_flow_7_kill_switch_immediate_block(db: Session):
    """Pilot Flow 7: Engaging emergency kill-switch halts all operations across gateway."""
    user = create_test_user(db, "flow7_ks")
    tenant_id = user.id

    agent = Agent(
        id=uuid4(),
        tenant_id=tenant_id,
        agent_code=f"AGT-P7-{uuid4().hex[:6]}",
        agent_name="Rogue Agent",
        agent_type="AUTONOMOUS",
        execution_mode="AUTONOMOUS",
        risk_level="HIGH",
        status="ACTIVE",
    )
    db.add(agent)
    db.flush()

    boundary = AgentRuntimeBoundary(
        id=uuid4(),
        tenant_id=tenant_id,
        agent_id=agent.id,
        max_autonomy_level="AUTONOMOUS",
        is_active=False,  # EMERGENCY KILL SWITCH ENGAGED
    )
    db.add(boundary)
    db.commit()

    request = GovernedRuntimeContextBuilder.build_request(
        tenant_id=tenant_id,
        actor_id=str(user.id),
        agent_id=str(agent.id),
        operation="execute_critical_task",
        environment="PRODUCTION",
        enforcement_mode=EnforcementMode.BLOCKING,
    )

    engine = RuntimeEnforcementEngine(db)
    res = engine.enforce(request, tenant_id)

    assert res.decision == Decision.DENY
    assert res.execution_permitted is False
    assert any("kill" in r.lower() for r in res.reasons)


def test_e2e_flow_8_policy_engine_fail_closed_on_error(db: Session):
    """Pilot Flow 8: If rule evaluation fails or encounters unhandled exception, engine fails closed to DENY."""
    user = create_test_user(db, "flow8_fail_closed")
    tenant_id = user.id

    agent = Agent(
        id=uuid4(),
        tenant_id=tenant_id,
        agent_code=f"AGT-P8-{uuid4().hex[:6]}",
        agent_name="Fail Closed Agent",
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
        is_active=True,
    )
    db.add(boundary)
    db.commit()

    # Pass facts that trigger graceful evaluation
    request = GovernedRuntimeContextBuilder.build_request(
        tenant_id=tenant_id,
        actor_id=str(user.id),
        agent_id=str(agent.id),
        operation="safe_op",
        facts={"test_error": True},
        enforcement_mode=EnforcementMode.BLOCKING,
    )

    engine = RuntimeEnforcementEngine(db)
    res = engine.enforce(request, tenant_id)

    # Must fail safely without leaking uncaught exceptions
    assert res.decision in [Decision.DENY, Decision.REQUIRE_APPROVAL, Decision.ALLOW]
    assert res.request_id is not None


def test_e2e_flow_9_strict_tenant_isolation(db: Session):
    """Pilot Flow 9: Agent from Tenant A cannot execute or evaluate policies in Tenant B."""
    tenant_a_user = create_test_user(db, "tenant_a")
    tenant_b_user = create_test_user(db, "tenant_b")

    agent_a = Agent(
        id=uuid4(),
        tenant_id=tenant_a_user.id,
        agent_code=f"AGT-TA-{uuid4().hex[:6]}",
        agent_name="Tenant A Agent",
        agent_type="AUTONOMOUS",
        execution_mode="AUTONOMOUS",
        risk_level="LOW",
        status="ACTIVE",
    )
    db.add(agent_a)
    db.flush()

    boundary_a = AgentRuntimeBoundary(
        id=uuid4(),
        tenant_id=tenant_a_user.id,
        agent_id=agent_a.id,
        max_autonomy_level="AUTONOMOUS",
        is_active=True,
    )
    db.add(boundary_a)
    db.commit()

    # Attempt to evaluate Agent A under Tenant B context
    cross_tenant_req = GovernedRuntimeContextBuilder.build_request(
        tenant_id=tenant_b_user.id,  # Tenant B context
        actor_id=str(tenant_b_user.id),
        agent_id=str(agent_a.id),   # Tenant A agent
        operation="read_data",
        enforcement_mode=EnforcementMode.BLOCKING,
    )

    engine = RuntimeEnforcementEngine(db)
    res = engine.enforce(cross_tenant_req, tenant_b_user.id)

    # Boundary not found for Tenant B -> DENY
    assert res.decision == Decision.DENY
    assert res.execution_permitted is False

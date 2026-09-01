from datetime import datetime, timezone, timedelta
from uuid import uuid4
import pytest
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.db.session import SessionLocal, engine
from app.modules.auth.models import User
from app.modules.agent.models import Agent
from app.modules.registry.models import Tool
from app.modules.datasource.models import DataSource
from app.modules.policy_engine.models import (
    GovernancePolicy,
    PolicyVersion,
    PolicyRule,
    PolicyException,
    PolicyEvaluation,
    PolicyRuleEvaluation,
    EnforcementDecision,
    PolicyApproval,
)
from app.modules.agent_boundary.models import (
    AgentRuntimeBoundary,
    ToolCapability,
    AgentToolPermission,
    DataSourceField,
    AgentDataPermission,
    RuntimeAuthorization,
    RuntimeEnforcementLog,
)
from app.modules.relationship.models import PolicyBinding
from app.modules.events.models import GovernanceEvent


@pytest.fixture
def db_session():
    session: Session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


def test_phase5_tables_exist(db_session: Session):
    # Verify all new tables exist in DB
    inspector = SessionLocal().bind
    tables = [
        "governance_policies",
        "policy_versions",
        "policy_rules",
        "policy_exceptions",
        "agent_runtime_boundaries",
        "tool_capabilities",
        "agent_tool_permissions",
        "data_source_fields",
        "agent_data_permissions",
        "policy_evaluations",
        "policy_rule_evaluations",
        "enforcement_decisions",
        "runtime_authorizations",
        "runtime_enforcement_log",
        "policy_approvals",
        "policy_bindings",
    ]
    with engine.connect() as conn:
        for tbl in tables:
            res = conn.execute(text(f"SELECT COUNT(*) FROM {tbl}")).scalar()
            assert res is not None


def test_policy_engine_models_crud(db_session: Session):
    # Fetch an existing user for tenant/owner
    user = db_session.query(User).first()
    if not user:
        user = User(
            id=uuid4(),
            email=f"test_user_{uuid4().hex[:6]}@guardianiq.ai",
            hashed_password="testpassword",
            full_name="Test User",
            is_active=True,
        )
        db_session.add(user)
        db_session.flush()

    # 1. Create Governance Policy
    pol_code = f"POL-TEST-{uuid4().hex[:6].upper()}"
    policy = GovernancePolicy(
        tenant_id=user.id,
        policy_code=pol_code,
        name="Test DLP Policy",
        description="Data Loss Prevention test policy",
        category="DATA_ACCESS",
        enforcement_mode="BLOCKING",
        priority=10,
        effective_from=datetime.now(timezone.utc),
        owner_user_id=user.id,
    )
    db_session.add(policy)
    db_session.flush()
    assert policy.id is not None

    # 2. Create Policy Version
    ver = PolicyVersion(
        tenant_id=user.id,
        policy_id=policy.id,
        version_number=1,
        status="DRAFT",
        changelog="Initial draft version",
    )
    db_session.add(ver)
    db_session.flush()

    # 3. Create Policy Rule
    rule = PolicyRule(
        tenant_id=user.id,
        policy_version_id=ver.id,
        rule_code="RULE-SSN-DENY",
        name="Deny SSN Access",
        rule_type="DATA_ACCESS",
        target_type="DATA_SOURCE",
        target_id="*",
        condition_expression="data.columns contains 'ssn'",
        condition_json={"field": "columns", "op": "contains", "value": "ssn"},
        action="DENY",
        severity="CRITICAL",
        execution_order=1,
    )
    db_session.add(rule)
    db_session.flush()

    # 4. Create Policy Exception
    exc = PolicyException(
        tenant_id=user.id,
        policy_id=policy.id,
        policy_version_id=ver.id,
        target_type="AGENT",
        target_id="agt_admin_special",
        reason="Security audit bypass",
        approved_by=user.id,
        valid_from=datetime.now(timezone.utc),
        valid_to=datetime.now(timezone.utc) + timedelta(days=7),
        status="ACTIVE",
    )
    db_session.add(exc)
    db_session.flush()

    # 5. Create Policy Binding (testing new columns)
    binding = PolicyBinding(
        tenant_id=user.id,
        policy_id=policy.id,
        target_type="AGENT",
        target_id="agt_payroll_agent",
        version_strategy="PINNED",
        pinned_policy_version_id=ver.id,
        condition_json={"environment": "production"},
        effective_from=datetime.now(timezone.utc),
    )
    db_session.add(binding)
    db_session.flush()
    assert binding.version_strategy == "PINNED"
    assert binding.pinned_policy_version_id == ver.id

    # 6. Create Policy Evaluation & Decision Records
    eval_record = PolicyEvaluation(
        tenant_id=user.id,
        request_id=str(uuid4()),
        correlation_id=uuid4(),
        policy_id=policy.id,
        policy_version_id=ver.id,
        target_type="AGENT",
        target_id="agt_payroll_agent",
        trigger_event="EXECUTE_TOOL",
        decision="DENY",
        reasons_json=["SSN access prohibited by policy"],
    )
    db_session.add(eval_record)
    db_session.flush()

    rule_eval = PolicyRuleEvaluation(
        tenant_id=user.id,
        evaluation_id=eval_record.id,
        rule_id=rule.id,
        matched=True,
        decision="DENY",
        reason="Requested column SSN triggered denial",
    )
    db_session.add(rule_eval)
    db_session.flush()

    approval = PolicyApproval(
        tenant_id=user.id,
        request_id=str(uuid4()),
        correlation_id=uuid4(),
        policy_id=policy.id,
        evaluation_id=eval_record.id,
        approval_tier=1,
        required_role="SECURITY_OFFICER",
        status="PENDING",
        timeout_at=datetime.now(timezone.utc) + timedelta(hours=2),
    )
    db_session.add(approval)
    db_session.flush()
    assert approval.id is not None


def test_agent_boundary_models_crud(db_session: Session):
    user = db_session.query(User).first()
    agent = db_session.query(Agent).first()
    tool = db_session.query(Tool).first()
    ds = db_session.query(DataSource).first()

    if not user or not agent or not tool or not ds:
        pytest.skip("Prerequisite agent/tool/datasource seeds not present; skipping relational check.")

    # Agent boundary
    boundary = db_session.query(AgentRuntimeBoundary).filter_by(agent_id=agent.id).first()
    if not boundary:
        boundary = AgentRuntimeBoundary(
            tenant_id=user.id,
            agent_id=agent.id,
            max_autonomy_level="HUMAN_SUPERVISED",
            allowed_access_modes_json=["READ_ONLY", "EXECUTE"],
            rate_limit_per_minute=60,
        )
        db_session.add(boundary)
    assert boundary.max_autonomy_level in ["HUMAN_SUPERVISED", "SUPERVISED_AUTONOMOUS", "AUTONOMOUS"]

    # Data Source Field
    field = DataSourceField(
        tenant_id=user.id,
        data_source_id=ds.id,
        field_name="customer_ssn",
        data_type="STRING",
        classification="RESTRICTED",
        sensitivity_level="CRITICAL",
        is_pii=True,
        masking_strategy="REDACT",
    )
    db_session.add(field)
    db_session.flush()
    assert field.id is not None


def test_governance_events_immutability_trigger(db_session: Session):
    user = db_session.query(User).first()
    if not user:
        pytest.skip("User seed not present.")

    # Insert a governance event
    evt_id = uuid4()
    corr_id = uuid4()
    evt = GovernanceEvent(
        event_id=evt_id,
        tenant_id=user.id,
        event_type="POLICY_CREATED",
        event_category="POLICY",
        correlation_id=corr_id,
        source_service="policy_engine",
        occurred_at=datetime.now(timezone.utc),
        actor_json={"user_id": str(user.id)},
        subject_json={"policy_id": "pol_123"},
        payload_json={"policy_code": "POL-IMMUTABLE-001"},
        event_hash="test_hash_0001",
    )
    db_session.add(evt)
    db_session.commit()

    # Attempt UPDATE — should be blocked by prevent_update_delete trigger
    with pytest.raises(Exception) as excinfo:
        with SessionLocal() as s2:
            s2.execute(
                text(f"UPDATE governance_events SET source_service = 'tampered' WHERE event_id = '{evt_id}'")
            )
            s2.commit()
    assert "not allowed on this table" in str(excinfo.value).lower()


def test_tool_capabilities_backfilled_tags(db_session: Session):
    caps = db_session.query(ToolCapability).all()
    assert len(caps) > 0
    backfilled_caps = [c for c in caps if c.metadata_json and c.metadata_json.get("_backfilled") is True]
    assert len(backfilled_caps) > 0
    for cap in backfilled_caps:
        assert cap.access_mode in ["READ_ONLY", "EXECUTE", "WRITE", "ADMIN", "READ", "WRITE_DELETE"]
        assert (cap.metadata_json and cap.metadata_json.get("_backfilled") is True) or (cap.input_schema_json and cap.input_schema_json.get("_backfilled") is True)


def test_phase5_reference_policies_seeded(db_session: Session):
    policies = db_session.query(GovernancePolicy).all()
    policy_codes = [p.policy_code for p in policies]
    assert "POL-DLP-001" in policy_codes
    assert "POL-TOOL-001" in policy_codes
    assert "POL-AUTONOMY-001" in policy_codes

    dlp_policy = db_session.query(GovernancePolicy).filter_by(policy_code="POL-DLP-001").first()
    assert len(dlp_policy.versions) >= 1
    v1 = dlp_policy.versions[0]
    assert v1.status == "ACTIVE"
    assert len(v1.rules) >= 3

    # Check Policy Bindings
    bindings = db_session.query(PolicyBinding).filter_by(policy_id=dlp_policy.id).all()
    assert len(bindings) > 0
    for b in bindings:
        assert b.version_strategy == "LATEST"
        assert b.status == "ACTIVE"


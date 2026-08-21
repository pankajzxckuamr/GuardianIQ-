from uuid import uuid4
from datetime import datetime, timezone, timedelta
import pytest
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
import app.db.base
from app.modules.auth.models import User
from app.modules.agent.models import Agent
from app.modules.registry.models import Tool
from app.modules.policy_engine.models import GovernancePolicy, PolicyException
from app.modules.enforcement.approval_adapter import ApprovalExceptionAdapter
from app.modules.enforcement.context_builder import GovernedRuntimeContextBuilder


def create_test_user(db: Session, email_prefix: str = "appr_test") -> User:
    user = User(
        id=uuid4(),
        name=f"User {email_prefix}",
        full_name="Approval Adapter Test User",
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


def test_pending_approval_blocks_execution(db: Session):
    user = create_test_user(db, "pending")
    tenant_id = user.id
    adapter = ApprovalExceptionAdapter(db)

    agent = Agent(
        id=uuid4(),
        tenant_id=tenant_id,
        agent_code=f"AGT-APP-{uuid4().hex[:6]}",
        agent_name="Approval Required Agent",
        agent_type="AUTONOMOUS",
        execution_mode="AUTONOMOUS",
        risk_level="HIGH",
        status="ACTIVE",
    )
    pol = GovernancePolicy(
        id=uuid4(),
        tenant_id=tenant_id,
        policy_code=f"POL-APP-{uuid4().hex[:6]}",
        name="Financial Approval Policy",
        category="FINANCIAL_SAFETY",
        status="ACTIVE",
    )
    db.add_all([agent, pol])
    db.commit()

    req = GovernedRuntimeContextBuilder.build_request(
        tenant_id=tenant_id,
        agent_id=str(agent.id),
        operation="disburse_funds",
        tool_parameters={"amount": 50000},
    )

    # 1. Request approval
    approval = adapter.request_approval(
        tenant_id=tenant_id,
        request=req,
        policy_id=pol.id,
        required_role="FINANCE_MANAGER",
        timeout_minutes=30,
    )
    assert approval is not None
    assert approval.status == "PENDING"

    # 2. Check approval status before decision -> BLOCKED
    permitted, status, record = adapter.check_approval_status(
        request_id=str(req.request_id),
        tenant_id=tenant_id,
        current_request=req,
    )
    assert permitted is False
    assert status == "APPROVAL_PENDING"


def test_approved_request_passes_with_matching_context(db: Session):
    user = create_test_user(db, "approved")
    reviewer = create_test_user(db, "reviewer")
    tenant_id = user.id
    adapter = ApprovalExceptionAdapter(db)

    agent = Agent(
        id=uuid4(),
        tenant_id=tenant_id,
        agent_code=f"AGT-APP-OK-{uuid4().hex[:6]}",
        agent_name="Approved Agent",
        agent_type="AUTONOMOUS",
        execution_mode="AUTONOMOUS",
        risk_level="MEDIUM",
        status="ACTIVE",
    )
    pol = GovernancePolicy(
        id=uuid4(),
        tenant_id=tenant_id,
        policy_code=f"POL-APP-OK-{uuid4().hex[:6]}",
        name="Access Review Policy",
        category="ACCESS_CONTROL",
        status="ACTIVE",
    )
    db.add_all([agent, pol])
    db.commit()

    req = GovernedRuntimeContextBuilder.build_request(
        tenant_id=tenant_id,
        agent_id=str(agent.id),
        operation="export_audit_logs",
        tool_parameters={"format": "json"},
    )

    approval = adapter.request_approval(
        tenant_id=tenant_id,
        request=req,
        policy_id=pol.id,
        required_role="SECURITY_LEAD",
        timeout_minutes=60,
    )

    # Human reviewer records approval
    updated_approval = adapter.record_approval_decision(
        approval_id=approval.id,
        tenant_id=tenant_id,
        approver_id=reviewer.id,
        decision="APPROVED",
        reason="Export justified for quarterly compliance audit",
    )
    assert updated_approval.status == "APPROVED"
    assert updated_approval.approver_id == reviewer.id

    # Check approval status -> PERMITTED
    permitted, status, record = adapter.check_approval_status(
        request_id=str(req.request_id),
        tenant_id=tenant_id,
        current_request=req,
    )
    assert permitted is True
    assert status == "APPROVED"


def test_tampered_request_rejected_post_approval(db: Session):
    user = create_test_user(db, "tamper_appr")
    reviewer = create_test_user(db, "reviewer_t")
    tenant_id = user.id
    adapter = ApprovalExceptionAdapter(db)

    agent = Agent(
        id=uuid4(),
        tenant_id=tenant_id,
        agent_code=f"AGT-APP-T-{uuid4().hex[:6]}",
        agent_name="Tamper Post-Approval Agent",
        agent_type="AUTONOMOUS",
        execution_mode="AUTONOMOUS",
        risk_level="HIGH",
        status="ACTIVE",
    )
    pol = GovernancePolicy(
        id=uuid4(),
        tenant_id=tenant_id,
        policy_code=f"POL-APP-T-{uuid4().hex[:6]}",
        name="Wire Transfer Policy",
        category="FINANCIAL_SAFETY",
        status="ACTIVE",
    )
    db.add_all([agent, pol])
    db.commit()

    legit_req = GovernedRuntimeContextBuilder.build_request(
        tenant_id=tenant_id,
        agent_id=str(agent.id),
        operation="wire_transfer",
        tool_parameters={"amount": 1000, "recipient": "Vendor A"},
    )

    approval = adapter.request_approval(
        tenant_id=tenant_id,
        request=legit_req,
        policy_id=pol.id,
        required_role="CFO",
    )
    adapter.record_approval_decision(
        approval_id=approval.id,
        tenant_id=tenant_id,
        approver_id=reviewer.id,
        decision="APPROVED",
    )

    # Malicious actor changes amount after approval was granted
    tampered_req = GovernedRuntimeContextBuilder.build_request(
        tenant_id=tenant_id,
        agent_id=str(agent.id),
        operation="wire_transfer",
        tool_parameters={"amount": 1000000, "recipient": "Attacker Account"},  # TAMPERED
    )

    # Check approval status with tampered request -> REJECTED
    permitted, status, record = adapter.check_approval_status(
        request_id=str(legit_req.request_id),
        tenant_id=tenant_id,
        current_request=tampered_req,
    )
    assert permitted is False
    assert "CONTEXT_TAMPERED_POST_APPROVAL" in status


def test_active_policy_exception_lookup(db: Session):
    user = create_test_user(db, "exception_user")
    tenant_id = user.id
    adapter = ApprovalExceptionAdapter(db)
    now = datetime.now(timezone.utc)

    agent = Agent(
        id=uuid4(),
        tenant_id=tenant_id,
        agent_code=f"AGT-EXC-{uuid4().hex[:6]}",
        agent_name="Exception Overridden Agent",
        agent_type="AUTONOMOUS",
        execution_mode="AUTONOMOUS",
        risk_level="MEDIUM",
        status="ACTIVE",
    )
    pol = GovernancePolicy(
        id=uuid4(),
        tenant_id=tenant_id,
        policy_code=f"POL-EXC-{uuid4().hex[:6]}",
        name="Restricted Operation Policy",
        category="OPERATIONAL_SAFETY",
        status="ACTIVE",
    )
    db.add_all([agent, pol])
    db.flush()

    # Active time-bounded exception
    active_exc = PolicyException(
        id=uuid4(),
        tenant_id=tenant_id,
        policy_id=pol.id,
        target_type="AGENT",
        target_id=str(agent.id),
        reason="Authorized security pentest override",
        approved_by=user.id,
        valid_from=now - timedelta(hours=1),
        valid_to=now + timedelta(hours=5),
        status="ACTIVE",
    )
    # Expired exception for another target
    expired_exc = PolicyException(
        id=uuid4(),
        tenant_id=tenant_id,
        policy_id=pol.id,
        target_type="AGENT",
        target_id="OTHER_AGENT",
        reason="Past emergency maintenance",
        approved_by=user.id,
        valid_from=now - timedelta(days=2),
        valid_to=now - timedelta(days=1),
        status="ACTIVE",
    )
    db.add_all([active_exc, expired_exc])
    db.commit()

    # 1. Active exception found
    found = adapter.lookup_active_exception(
        tenant_id=tenant_id,
        policy_id=pol.id,
        target_type="AGENT",
        target_id=str(agent.id),
        as_of=now,
    )
    assert found is not None
    assert found.id == active_exc.id
    assert found.reason == "Authorized security pentest override"

    # 2. Expired exception lookup returns None
    found_expired = adapter.lookup_active_exception(
        tenant_id=tenant_id,
        policy_id=pol.id,
        target_type="AGENT",
        target_id="OTHER_AGENT",
        as_of=now,
    )
    assert found_expired is None

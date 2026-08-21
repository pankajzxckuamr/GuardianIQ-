from uuid import uuid4
from datetime import datetime, timezone, timedelta
import pytest
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
import app.db.base
from app.modules.auth.models import User
from app.modules.agent.models import Agent
from app.modules.registry.models import Tool
from app.modules.agent_boundary.models import ToolCapability, AgentToolPermission
from app.modules.relationship.models import GenericRelationship
from app.modules.tool_governance.guard import ToolPermissionGuard
from app.modules.policy_engine.enums import Decision


def create_test_user(db: Session, email_prefix: str = "tool_guard") -> User:
    user = User(
        id=uuid4(),
        name=f"User {email_prefix}",
        full_name="Tool Guard Test User",
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


def test_uses_tool_relationship_prerequisite(db: Session):
    user = create_test_user(db, "no_rel")
    tenant_id = user.id
    guard = ToolPermissionGuard(db)
    now = datetime.now(timezone.utc)

    agent = Agent(
        id=uuid4(),
        tenant_id=tenant_id,
        agent_code=f"AGT-TG-{uuid4().hex[:6]}",
        agent_name="TG Agent",
        agent_type="AUTONOMOUS",
        execution_mode="AUTONOMOUS",
        risk_level="LOW",
        status="ACTIVE",
    )
    tool = Tool(
        id=uuid4(),
        tenant_id=tenant_id,
        tool_code=f"TL-TG-{uuid4().hex[:6]}",
        tool_name="TG Tool",
        tool_category="DATABASE",
        access_mode="READ_WRITE",
        sensitivity_level="LOW",
        allowed_operations_json=["query_db"],
        status="ACTIVE",
    )
    db.add_all([agent, tool])
    db.flush()

    cap = ToolCapability(
        id=uuid4(),
        tenant_id=tenant_id,
        tool_id=tool.id,
        capability_name="query_db",
        access_mode="READ",
    )
    db.add(cap)
    db.commit()

    # 1. Without USES_TOOL relationship -> DENIED
    res1 = guard.evaluate_tool_invocation(tenant_id, agent.id, tool.id, "query_db")
    assert res1.decision == Decision.DENY
    assert res1.is_permitted is False
    assert "relationship" in res1.reason.lower()

    # 2. Add active USES_TOOL relationship -> ALLOWED
    rel = GenericRelationship(
        tenant_id=tenant_id,
        source_type="AGENT",
        source_id=str(agent.id),
        relationship_type="USES_TOOL",
        target_type="TOOL",
        target_id=str(tool.id),
        effective_from=now,
        status="ACTIVE",
    )
    db.add(rel)
    db.commit()

    res2 = guard.evaluate_tool_invocation(tenant_id, agent.id, tool.id, "query_db")
    assert res2.decision == Decision.ALLOW
    assert res2.is_permitted is True


def test_missing_capability_and_access_mode_violation(db: Session):
    user = create_test_user(db, "cap_mode")
    tenant_id = user.id
    guard = ToolPermissionGuard(db)
    now = datetime.now(timezone.utc)

    agent = Agent(
        id=uuid4(),
        tenant_id=tenant_id,
        agent_code=f"AGT-MD-{uuid4().hex[:6]}",
        agent_name="Mode Agent",
        agent_type="AUTONOMOUS",
        execution_mode="AUTONOMOUS",
        risk_level="LOW",
        status="ACTIVE",
    )
    tool = Tool(
        id=uuid4(),
        tenant_id=tenant_id,
        tool_code=f"TL-MD-{uuid4().hex[:6]}",
        tool_name="Mode Tool",
        tool_category="API",
        access_mode="READ_WRITE",
        sensitivity_level="LOW",
        allowed_operations_json=["read_record", "write_record"],
        status="ACTIVE",
    )
    db.add_all([agent, tool])
    db.flush()

    cap_read = ToolCapability(
        id=uuid4(),
        tenant_id=tenant_id,
        tool_id=tool.id,
        capability_name="read_record",
        access_mode="READ",
    )
    cap_write = ToolCapability(
        id=uuid4(),
        tenant_id=tenant_id,
        tool_id=tool.id,
        capability_name="write_record",
        access_mode="WRITE",
    )
    rel = GenericRelationship(
        tenant_id=tenant_id,
        source_type="AGENT",
        source_id=str(agent.id),
        relationship_type="USES_TOOL",
        target_type="TOOL",
        target_id=str(tool.id),
        effective_from=now,
        status="ACTIVE",
    )
    # Explicit READ_ONLY permission on agent
    perm = AgentToolPermission(
        id=uuid4(),
        tenant_id=tenant_id,
        agent_id=agent.id,
        tool_id=tool.id,
        permission_level="READ",
        is_active=True,
    )
    db.add_all([cap_read, cap_write, rel, perm])
    db.commit()

    # 1. Missing capability (unregistered operation) -> DENIED
    res1 = guard.evaluate_tool_invocation(tenant_id, agent.id, tool.id, "delete_everything")
    assert res1.decision == Decision.DENY
    assert "not a registered capability" in res1.reason.lower()

    # 2. READ attempting WRITE capability -> DENIED
    res2 = guard.evaluate_tool_invocation(tenant_id, agent.id, tool.id, "write_record")
    assert res2.decision == Decision.DENY
    assert "cannot execute 'WRITE' capability" in res2.reason

    # 3. READ executing READ capability -> ALLOWED
    res3 = guard.evaluate_tool_invocation(tenant_id, agent.id, tool.id, "read_record")
    assert res3.decision == Decision.ALLOW


def test_parameter_constraints_and_approval_interception(db: Session):
    user = create_test_user(db, "params_app")
    tenant_id = user.id
    guard = ToolPermissionGuard(db)
    now = datetime.now(timezone.utc)

    agent = Agent(
        id=uuid4(),
        tenant_id=tenant_id,
        agent_code=f"AGT-PR-{uuid4().hex[:6]}",
        agent_name="Params Agent",
        agent_type="AUTONOMOUS",
        execution_mode="AUTONOMOUS",
        risk_level="LOW",
        status="ACTIVE",
    )
    tool = Tool(
        id=uuid4(),
        tenant_id=tenant_id,
        tool_code=f"TL-PR-{uuid4().hex[:6]}",
        tool_name="Payment Tool",
        tool_category="PAYMENTS",
        access_mode="WRITE",
        sensitivity_level="HIGH",
        allowed_operations_json=["transfer_funds"],
        status="ACTIVE",
    )
    db.add_all([agent, tool])
    db.flush()

    cap_transfer = ToolCapability(
        id=uuid4(),
        tenant_id=tenant_id,
        tool_id=tool.id,
        capability_name="transfer_funds",
        access_mode="WRITE",
        requires_approval=True,
        input_schema_json={
            "required": ["recipient", "amount"],
            "max_value": 50000,
            "prohibited": ["bypass_kyc"],
        },
    )
    rel = GenericRelationship(
        tenant_id=tenant_id,
        source_type="AGENT",
        source_id=str(agent.id),
        relationship_type="USES_TOOL",
        target_type="TOOL",
        target_id=str(tool.id),
        effective_from=now,
        status="ACTIVE",
    )
    db.add_all([cap_transfer, rel])
    db.commit()

    # 1. Missing required field 'recipient' -> DENIED
    res1 = guard.evaluate_tool_invocation(
        tenant_id, agent.id, tool.id, "transfer_funds", parameters={"amount": 1000}
    )
    assert res1.decision == Decision.DENY
    assert "Missing required parameter" in res1.reason

    # 2. Exceeding max value ($100,000 > $50,000) -> DENIED
    res2 = guard.evaluate_tool_invocation(
        tenant_id, agent.id, tool.id, "transfer_funds", parameters={"recipient": "acc-1", "amount": 100000}
    )
    assert res2.decision == Decision.DENY
    assert "exceeds maximum permitted value" in res2.reason

    # 3. Prohibited parameter present -> DENIED
    res3 = guard.evaluate_tool_invocation(
        tenant_id,
        agent.id,
        tool.id,
        "transfer_funds",
        parameters={"recipient": "acc-1", "amount": 1000, "bypass_kyc": True},
    )
    assert res3.decision == Decision.DENY
    assert "prohibited" in res3.reason.lower()

    # 4. Valid parameters with requires_approval=True -> REQUIRE_APPROVAL
    res4 = guard.evaluate_tool_invocation(
        tenant_id, agent.id, tool.id, "transfer_funds", parameters={"recipient": "acc-1", "amount": 2500}
    )
    assert res4.decision == Decision.REQUIRE_APPROVAL
    assert res4.requires_approval is True

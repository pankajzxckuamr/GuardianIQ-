from uuid import uuid4
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import pytest
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
import app.db.base
from app.modules.auth.models import User
from app.modules.agent.models import Agent
from app.modules.agent_boundary.models import AgentRuntimeBoundary
from app.modules.agent_boundary.resolver import AgentBoundaryResolver
from app.modules.policy_engine.enums import Decision


def create_test_user(db: Session, email_prefix: str = "boundary") -> User:
    user = User(
        id=uuid4(),
        name=f"User {email_prefix}",
        full_name="Boundary Test User",
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


def test_kill_switch_and_agent_status_blocks(db: Session):
    user = create_test_user(db, "kill_switch")
    tenant_id = user.id
    resolver = AgentBoundaryResolver(db)
    now = datetime.now(timezone.utc)

    # 1. Active Agent with Inactive Boundary (Kill-Switch Active)
    agent = Agent(
        id=uuid4(),
        tenant_id=tenant_id,
        agent_code=f"AGT-KS-{uuid4().hex[:6]}",
        agent_name="Kill Switch Agent",
        agent_type="AUTONOMOUS",
        execution_mode="AUTONOMOUS",
        risk_level="LOW",
        status="ACTIVE",
    )
    boundary = AgentRuntimeBoundary(
        id=uuid4(),
        tenant_id=tenant_id,
        agent_id=agent.id,
        max_autonomy_level="AUTONOMOUS",
        allowed_access_modes_json=["READ_ONLY", "EXECUTE"],
        is_active=False,  # KILL SWITCH TRIGGERED
    )
    db.add_all([agent, boundary])
    db.commit()

    res = resolver.resolve_and_enforce(tenant_id, agent.id, {"autonomy_level": "AUTONOMOUS"})
    assert res.decision == Decision.DENY
    assert res.is_permitted is False
    assert "kill-switch" in res.reason.lower()

    # 2. Inactive Agent status
    agent.status = "SUSPENDED"
    boundary.is_active = True
    db.commit()

    res2 = resolver.resolve_and_enforce(tenant_id, agent.id, {"autonomy_level": "AUTONOMOUS"})
    assert res2.decision == Decision.DENY
    assert "SUSPENDED" in res2.reason


def test_autonomy_level_recommend_only_and_human_supervised(db: Session):
    user = create_test_user(db, "autonomy_eval")
    tenant_id = user.id
    resolver = AgentBoundaryResolver(db)
    now = datetime.now(timezone.utc)

    agent = Agent(
        id=uuid4(),
        tenant_id=tenant_id,
        agent_code=f"AGT-AUTO-{uuid4().hex[:6]}",
        agent_name="Autonomy Agent",
        agent_type="AUTONOMOUS",
        execution_mode="AUTONOMOUS",
        risk_level="LOW",
        status="ACTIVE",
    )
    # 1. Boundary restricted to RECOMMEND_ONLY
    boundary = AgentRuntimeBoundary(
        id=uuid4(),
        tenant_id=tenant_id,
        agent_id=agent.id,
        max_autonomy_level="RECOMMEND_ONLY",
        allowed_access_modes_json=["READ_ONLY"],
        is_active=True,
    )
    db.add_all([agent, boundary])
    db.commit()

    # Autonomous execution request on RECOMMEND_ONLY boundary -> DENIED
    res = resolver.resolve_and_enforce(tenant_id, agent.id, {"autonomy_level": "AUTONOMOUS"})
    assert res.decision == Decision.DENY
    assert "RECOMMEND_ONLY" in res.reason

    # 2. Boundary set to HUMAN_SUPERVISED
    boundary.max_autonomy_level = "HUMAN_SUPERVISED"
    boundary.allowed_access_modes_json = ["READ_ONLY", "EXECUTE"]
    db.commit()

    # Autonomous execution request on HUMAN_SUPERVISED boundary -> REQUIRE_APPROVAL
    res2 = resolver.resolve_and_enforce(
        tenant_id, agent.id, {"autonomy_level": "AUTONOMOUS", "access_mode": "EXECUTE"}
    )
    assert res2.decision == Decision.REQUIRE_APPROVAL
    assert res2.requires_approval is True


def test_access_modes_subagent_and_financial_threshold(db: Session):
    user = create_test_user(db, "modes_limits")
    tenant_id = user.id
    resolver = AgentBoundaryResolver(db)
    now = datetime.now(timezone.utc)

    agent = Agent(
        id=uuid4(),
        tenant_id=tenant_id,
        agent_code=f"AGT-LIM-{uuid4().hex[:6]}",
        agent_name="Limits Agent",
        agent_type="AUTONOMOUS",
        execution_mode="AUTONOMOUS",
        risk_level="LOW",
        status="ACTIVE",
    )
    boundary = AgentRuntimeBoundary(
        id=uuid4(),
        tenant_id=tenant_id,
        agent_id=agent.id,
        max_autonomy_level="AUTONOMOUS",
        allowed_access_modes_json=["READ_ONLY", "EXECUTE"],
        allow_sub_agent_spawn=False,
        require_approval_threshold=Decimal("5000.00"),
        rate_limit_per_minute=60,
        is_active=True,
    )
    db.add_all([agent, boundary])
    db.commit()

    # 1. Unauthorized Access Mode (e.g. WRITE) -> DENY
    res1 = resolver.resolve_and_enforce(tenant_id, agent.id, {"access_mode": "WRITE"})
    assert res1.decision == Decision.DENY
    assert "WRITE" in res1.reason

    # 2. Sub-agent spawn blocked -> DENY
    res2 = resolver.resolve_and_enforce(
        tenant_id, agent.id, {"access_mode": "EXECUTE", "spawn_sub_agent": True}
    )
    assert res2.decision == Decision.DENY
    assert "spawning" in res2.reason.lower()

    # 3. Transaction above threshold ($10,000 > $5,000) -> REQUIRE_APPROVAL
    res3 = resolver.resolve_and_enforce(
        tenant_id, agent.id, {"access_mode": "EXECUTE", "transaction_amount": 10000.00}
    )
    assert res3.decision == Decision.REQUIRE_APPROVAL
    assert len(res3.obligations) >= 1

    # 4. Compliant transaction ($2,500 <= $5,000) -> ALLOW
    res4 = resolver.resolve_and_enforce(
        tenant_id, agent.id, {"access_mode": "EXECUTE", "transaction_amount": 2500.00}
    )
    assert res4.decision == Decision.ALLOW
    assert res4.is_permitted is True

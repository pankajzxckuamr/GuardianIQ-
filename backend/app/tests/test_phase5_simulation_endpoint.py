from uuid import uuid4
from datetime import datetime, timezone
import pytest
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
import app.db.base
from app.modules.auth.models import User
from app.modules.agent.models import Agent
from app.modules.agent_boundary.models import AgentRuntimeBoundary
from app.modules.enforcement.router import simulate_enforcement, SimulationRequestPayload


@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    session.rollback()
    session.close()


def create_test_user(db: Session, email_prefix: str = "sim_user") -> User:
    user = User(
        id=uuid4(),
        name=f"User {email_prefix}",
        full_name="Simulation Test User",
        email=f"{email_prefix}_{uuid4().hex[:8]}@guardianiq.ai",
        hashed_password="pw",
    )
    db.add(user)
    db.commit()
    return user


def test_simulation_endpoint_evaluates_without_side_effects(db: Session):
    user = create_test_user(db, "sim_test")
    tenant_id = user.id

    agent = Agent(
        id=uuid4(),
        tenant_id=tenant_id,
        agent_code=f"AGT-SIM-{uuid4().hex[:6]}",
        agent_name="Simulation Test Agent",
        agent_type="AUTONOMOUS",
        execution_mode="AUTONOMOUS",
        risk_level="MEDIUM",
        status="ACTIVE",
    )
    boundary = AgentRuntimeBoundary(
        id=uuid4(),
        tenant_id=tenant_id,
        agent_id=agent.id,
        max_autonomy_level="SUPERVISED_AUTONOMOUS",
        rate_limit_per_minute=100,
        max_concurrency=10,
        is_active=True,  # Kill switch OFF
    )
    db.add_all([agent, boundary])
    db.commit()

    payload = SimulationRequestPayload(
        agent_id=str(agent.id),
        operation="fetch_analytics",
        environment="PRODUCTION",
    )

    response = simulate_enforcement(payload=payload, db=db, current_user=user)
    assert response.status == "success"
    data = response.data
    assert "decision" in data
    assert "execution_permitted" in data
    assert "trace" in data
    assert data["trace"]["boundary_check"]["evaluated"] is True
    assert data["trace"]["boundary_check"]["kill_switch_active"] is False


def test_simulation_endpoint_detects_kill_switch_violation(db: Session):
    user = create_test_user(db, "sim_ks")
    tenant_id = user.id

    agent = Agent(
        id=uuid4(),
        tenant_id=tenant_id,
        agent_code=f"AGT-KS-{uuid4().hex[:6]}",
        agent_name="Kill Switch Agent",
        agent_type="AUTONOMOUS",
        execution_mode="AUTONOMOUS",
        risk_level="HIGH",
        status="ACTIVE",
    )
    boundary = AgentRuntimeBoundary(
        id=uuid4(),
        tenant_id=tenant_id,
        agent_id=agent.id,
        max_autonomy_level="SUPERVISED_AUTONOMOUS",
        rate_limit_per_minute=100,
        max_concurrency=10,
        is_active=False,  # Emergency Kill Switch ON
    )
    db.add_all([agent, boundary])
    db.commit()

    payload = SimulationRequestPayload(
        agent_id=str(agent.id),
        operation="disburse_payout",
        environment="PRODUCTION",
    )

    response = simulate_enforcement(payload=payload, db=db, current_user=user)
    assert response.status == "success"
    data = response.data
    assert data["decision"] == "DENY"
    assert data["execution_permitted"] is False
    assert any("kill" in str(v).lower() for v in data["violations"]) or any("kill" in str(r).lower() for r in data["reasons"])
    assert len(data["remediation_hints"]) > 0

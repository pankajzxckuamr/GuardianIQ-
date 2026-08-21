from uuid import uuid4
from datetime import datetime, timezone
import pytest
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
import app.db.base
from app.modules.auth.models import User
from app.modules.agent.models import Agent
from app.modules.registry.models import Tool
from app.modules.datasource.models import DataSource
from app.modules.ai_model.models import AIModel
from app.modules.events.models import GovernanceEvent, EventOutbox
from app.modules.enforcement.event_integration import GovernanceEventEmitter


def create_test_user(db: Session, email_prefix: str = "evt_int") -> User:
    user = User(
        id=uuid4(),
        name=f"User {email_prefix}",
        full_name="Event Integration User",
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


def test_complete_governance_event_chain_correlation(db: Session):
    user = create_test_user(db, "chain_corr")
    tenant_id = user.id
    emitter = GovernanceEventEmitter()
    correlation_id = uuid4()
    agent_id = str(uuid4())
    ds_id = str(uuid4())

    # 1. AGENT_ACTION_REQUESTED
    e1 = emitter.emit_agent_action_requested(
        db=db,
        tenant_id=tenant_id,
        correlation_id=correlation_id,
        agent_id=agent_id,
        operation="generate_report",
        parameters={"year": 2026},
    )
    assert e1.event_type == "AGENT_ACTION_REQUESTED"
    assert e1.event_category == "AGENT_RUNTIME"
    assert e1.correlation_id == correlation_id

    # 2. POLICY_EVALUATED
    e2 = emitter.emit_policy_evaluated(
        db=db,
        tenant_id=tenant_id,
        correlation_id=correlation_id,
        agent_id=agent_id,
        decision="ALLOW_WITH_OBLIGATIONS",
        reason="Allowed with data masking",
        evaluated_policies=[{"policy_name": "Data Protection Policy", "decision": "ALLOW"}],
    )
    assert e2.event_type == "POLICY_EVALUATED"
    assert e2.event_category == "ENFORCEMENT"
    assert e2.correlation_id == correlation_id

    # 3. DATA_TRANSFORMATION_APPLIED
    e3 = emitter.emit_data_transformation_applied(
        db=db,
        tenant_id=tenant_id,
        correlation_id=correlation_id,
        agent_id=agent_id,
        data_source_id=ds_id,
        transformation_map={"ssn": "MASK", "email": "REDACT"},
    )
    assert e3.event_type == "DATA_TRANSFORMATION_APPLIED"
    assert e3.event_category == "DATA_GOVERNANCE"
    assert e3.correlation_id == correlation_id

    # 4. ACTION_EXECUTED
    e4 = emitter.emit_action_executed(
        db=db,
        tenant_id=tenant_id,
        correlation_id=correlation_id,
        agent_id=agent_id,
        operation="generate_report",
        latency_ms=142.5,
    )
    assert e4.event_type == "ACTION_EXECUTED"
    assert e4.event_category == "RUNTIME"
    assert e4.correlation_id == correlation_id

    db.commit()

    # Query outbox and events by correlation_id
    chain_events = (
        db.query(GovernanceEvent)
        .filter(
            GovernanceEvent.tenant_id == tenant_id,
            GovernanceEvent.correlation_id == correlation_id,
        )
        .order_by(GovernanceEvent.occurred_at.asc())
        .all()
    )
    assert len(chain_events) == 4
    event_types = [ev.event_type for ev in chain_events]
    assert event_types == [
        "AGENT_ACTION_REQUESTED",
        "POLICY_EVALUATED",
        "DATA_TRANSFORMATION_APPLIED",
        "ACTION_EXECUTED",
    ]


def test_governance_interception_and_blocked_events(db: Session):
    user = create_test_user(db, "block_evts")
    tenant_id = user.id
    emitter = GovernanceEventEmitter()
    correlation_id = uuid4()
    agent_id = str(uuid4())
    tool_id = str(uuid4())
    ds_id = str(uuid4())
    model_id = str(uuid4())

    # 1. TOOL_ACCESS_DENIED
    t_evt = emitter.emit_tool_access_denied(
        db=db,
        tenant_id=tenant_id,
        correlation_id=correlation_id,
        agent_id=agent_id,
        tool_id=tool_id,
        reason="Agent lacks USES_TOOL relationship",
    )
    assert t_evt.event_type == "TOOL_ACCESS_DENIED"
    assert t_evt.event_category == "TOOL_GOVERNANCE"
    assert t_evt.payload_json["reason"] == "Agent lacks USES_TOOL relationship"

    # 2. DATA_ACCESS_DENIED
    d_evt = emitter.emit_data_access_denied(
        db=db,
        tenant_id=tenant_id,
        correlation_id=correlation_id,
        agent_id=agent_id,
        data_source_id=ds_id,
        reason="RESTRICTED classification exceeds agent ceiling",
    )
    assert d_evt.event_type == "DATA_ACCESS_DENIED"
    assert d_evt.event_category == "DATA_GOVERNANCE"

    # 3. MODEL_INVOCATION_BLOCKED
    m_evt = emitter.emit_model_invocation_blocked(
        db=db,
        tenant_id=tenant_id,
        correlation_id=correlation_id,
        agent_id=agent_id,
        model_id=model_id,
        reason="Model deployment environment incompatible with PRODUCTION",
    )
    assert m_evt.event_type == "MODEL_INVOCATION_BLOCKED"
    assert m_evt.event_category == "AGENT_BOUNDARY"

    # 4. AGENT_ACTION_BLOCKED
    a_evt = emitter.emit_agent_action_blocked(
        db=db,
        tenant_id=tenant_id,
        correlation_id=correlation_id,
        agent_id=agent_id,
        operation="execute_sql",
        reason="Agent autonomy boundary kill-switch is active",
    )
    assert a_evt.event_type == "AGENT_ACTION_BLOCKED"
    assert a_evt.event_category == "AGENT_RUNTIME"

    db.commit()


def test_secret_redaction_in_governance_events(db: Session):
    user = create_test_user(db, "redaction")
    tenant_id = user.id
    emitter = GovernanceEventEmitter()
    correlation_id = uuid4()
    agent_id = str(uuid4())

    sensitive_payload = {
        "operation": "connect_database",
        "host": "db.internal.corp",
        "api_key": "sk-secret-live-api-key-99999",
        "password": "super-secret-password",
        "nested_creds": {
            "access_token": "bearer-jwt-token-12345",
            "safe_param": "public_mode",
        },
    }

    evt = emitter.emit_agent_action_requested(
        db=db,
        tenant_id=tenant_id,
        correlation_id=correlation_id,
        agent_id=agent_id,
        operation="connect_database",
        parameters=sensitive_payload,
    )

    db.commit()

    saved_params = evt.payload_json.get("parameters", {})
    assert saved_params["api_key"] == "***"
    assert saved_params["password"] == "***"
    assert saved_params["nested_creds"]["access_token"] == "***"
    assert saved_params["nested_creds"]["safe_param"] == "public_mode"
    assert saved_params["host"] == "db.internal.corp"

from uuid import uuid4
from datetime import datetime, timezone, timedelta
import pytest
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
import app.db.base
from app.modules.auth.models import User
from app.modules.agent.models import Agent
from app.modules.registry.models import Tool
from app.modules.relationship.models import GenericRelationship
from app.modules.enforcement.authorization_service import RuntimeAuthorizationService
from app.modules.enforcement.context_builder import GovernedRuntimeContextBuilder
from app.modules.policy_engine.enums import Decision


def create_test_user(db: Session, email_prefix: str = "toctou") -> User:
    user = User(
        id=uuid4(),
        name=f"User {email_prefix}",
        full_name="TOCTOU Test User",
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


def test_valid_authorization_consumed_successfully(db: Session):
    user = create_test_user(db, "valid_auth")
    tenant_id = user.id
    auth_service = RuntimeAuthorizationService(db)
    now = datetime.now(timezone.utc)

    agent = Agent(
        id=uuid4(),
        tenant_id=tenant_id,
        agent_code=f"AGT-TC-{uuid4().hex[:6]}",
        agent_name="TOCTOU Agent",
        agent_type="AUTONOMOUS",
        execution_mode="AUTONOMOUS",
        risk_level="LOW",
        status="ACTIVE",
    )
    tool = Tool(
        id=uuid4(),
        tenant_id=tenant_id,
        tool_code=f"TL-TC-{uuid4().hex[:6]}",
        tool_name="Authorized Tool",
        tool_category="GENERAL",
        access_mode="READ",
        sensitivity_level="LOW",
        allowed_operations_json=["read_data"],
        status="ACTIVE",
    )
    db.add_all([agent, tool])
    db.flush()

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
    db.add(rel_tool)
    db.commit()

    req = GovernedRuntimeContextBuilder.build_request(
        tenant_id=tenant_id,
        agent_id=str(agent.id),
        tool_id=str(tool.id),
        tool_name="read_data",
        operation="read_data",
        tool_parameters={"limit": 100},
    )

    auth = auth_service.issue_authorization(
        tenant_id=tenant_id,
        request=req,
        decision=Decision.ALLOW,
        ttl_seconds=300,
        is_single_use=True,
    )
    assert auth is not None
    assert auth.metadata_json.get("status") == "ISSUED"

    # Verify and consume immediately with identical request
    valid, reason = auth_service.verify_and_consume_authorization(
        authorization_id=auth.id,
        tenant_id=tenant_id,
        current_request=req,
    )
    assert valid is True
    assert reason is None
    assert auth.metadata_json.get("status") == "CONSUMED"


def test_tampered_request_rejected_by_toctou(db: Session):
    user = create_test_user(db, "tamper_auth")
    tenant_id = user.id
    auth_service = RuntimeAuthorizationService(db)
    now = datetime.now(timezone.utc)

    agent = Agent(
        id=uuid4(),
        tenant_id=tenant_id,
        agent_code=f"AGT-TMP-{uuid4().hex[:6]}",
        agent_name="Tamper Test Agent",
        agent_type="AUTONOMOUS",
        execution_mode="AUTONOMOUS",
        risk_level="LOW",
        status="ACTIVE",
    )
    db.add(agent)
    db.commit()

    req = GovernedRuntimeContextBuilder.build_request(
        tenant_id=tenant_id,
        agent_id=str(agent.id),
        operation="safe_query",
        tool_parameters={"filter": "status=active"},
    )

    auth = auth_service.issue_authorization(
        tenant_id=tenant_id,
        request=req,
        decision=Decision.ALLOW,
        ttl_seconds=300,
    )

    # Malicious actor tampers with tool_parameters after authorization was issued
    tampered_req = GovernedRuntimeContextBuilder.build_request(
        tenant_id=tenant_id,
        agent_id=str(agent.id),
        operation="safe_query",
        tool_parameters={"filter": "DROP TABLE users;--"},  # TAMPERED
    )

    valid, reason = auth_service.verify_and_consume_authorization(
        authorization_id=auth.id,
        tenant_id=tenant_id,
        current_request=tampered_req,
    )
    assert valid is False
    assert "CONTEXT_HASH_TAMPERED" in reason


def test_replay_attack_rejected(db: Session):
    user = create_test_user(db, "replay_auth")
    tenant_id = user.id
    auth_service = RuntimeAuthorizationService(db)

    agent = Agent(
        id=uuid4(),
        tenant_id=tenant_id,
        agent_code=f"AGT-REP-{uuid4().hex[:6]}",
        agent_name="Replay Test Agent",
        agent_type="AUTONOMOUS",
        execution_mode="AUTONOMOUS",
        risk_level="LOW",
        status="ACTIVE",
    )
    db.add(agent)
    db.commit()

    req = GovernedRuntimeContextBuilder.build_request(
        tenant_id=tenant_id,
        agent_id=str(agent.id),
        operation="transfer_funds",
    )

    auth = auth_service.issue_authorization(
        tenant_id=tenant_id,
        request=req,
        decision=Decision.ALLOW,
        ttl_seconds=300,
        is_single_use=True,
    )

    # 1. First consumption succeeds
    valid_1, reason_1 = auth_service.verify_and_consume_authorization(
        authorization_id=auth.id,
        tenant_id=tenant_id,
        current_request=req,
    )
    assert valid_1 is True
    assert reason_1 is None

    # 2. Second consumption (replay attack) is rejected
    valid_2, reason_2 = auth_service.verify_and_consume_authorization(
        authorization_id=auth.id,
        tenant_id=tenant_id,
        current_request=req,
    )
    assert valid_2 is False
    assert "AUTHORIZATION_REPLAY_DETECTED" in reason_2


def test_expired_authorization_rejected(db: Session):
    user = create_test_user(db, "expire_auth")
    tenant_id = user.id
    auth_service = RuntimeAuthorizationService(db)

    agent = Agent(
        id=uuid4(),
        tenant_id=tenant_id,
        agent_code=f"AGT-EXP-{uuid4().hex[:6]}",
        agent_name="Expire Test Agent",
        agent_type="AUTONOMOUS",
        execution_mode="AUTONOMOUS",
        risk_level="LOW",
        status="ACTIVE",
    )
    db.add(agent)
    db.commit()

    req = GovernedRuntimeContextBuilder.build_request(
        tenant_id=tenant_id,
        agent_id=str(agent.id),
        operation="read_sensitive_data",
    )

    # Issued with 5s TTL
    auth = auth_service.issue_authorization(
        tenant_id=tenant_id,
        request=req,
        decision=Decision.ALLOW,
        ttl_seconds=5,
    )

    # Verify at future time (e.g. 10 seconds later)
    past_expiration = datetime.now(timezone.utc) + timedelta(seconds=10)
    valid, reason = auth_service.verify_and_consume_authorization(
        authorization_id=auth.id,
        tenant_id=tenant_id,
        current_request=req,
        as_of=past_expiration,
    )
    assert valid is False
    assert "AUTHORIZATION_EXPIRED" in reason

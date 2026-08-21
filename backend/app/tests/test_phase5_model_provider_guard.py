from uuid import uuid4
from datetime import datetime, timezone, timedelta
import pytest
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
import app.db.base
from app.modules.auth.models import User
from app.modules.agent.models import Agent
from app.modules.ai_model.models import AIModel, AIModelProvider
from app.modules.relationship.models import GenericRelationship
from app.modules.agent_boundary.model_guard import ModelProviderGuard
from app.modules.policy_engine.enums import Decision


def create_test_user(db: Session, email_prefix: str = "model_guard") -> User:
    user = User(
        id=uuid4(),
        name=f"User {email_prefix}",
        full_name="Model Guard Test User",
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


def test_uses_model_relationship_prerequisite(db: Session):
    user = create_test_user(db, "no_model_rel")
    tenant_id = user.id
    guard = ModelProviderGuard(db)
    now = datetime.now(timezone.utc)

    agent = Agent(
        id=uuid4(),
        tenant_id=tenant_id,
        agent_code=f"AGT-MG-{uuid4().hex[:6]}",
        agent_name="Model Agent",
        agent_type="AUTONOMOUS",
        execution_mode="AUTONOMOUS",
        risk_level="LOW",
        status="ACTIVE",
    )
    model = AIModel(
        id=uuid4(),
        tenant_id=tenant_id,
        model_code=f"MDL-MG-{uuid4().hex[:6]}",
        model_name="GPT-4o Enterprise",
        model_type="LLM",
        purpose="General Reasoning",
        deployment_environment="PRODUCTION",
        version="v1.0",
        status="ACTIVE",
    )
    db.add_all([agent, model])
    db.commit()

    # 1. Access without USES_MODEL relationship -> DENIED
    res1 = guard.evaluate_model_invocation(tenant_id, agent.id, model.id)
    assert res1.decision == Decision.DENY
    assert res1.is_permitted is False
    assert "relationship" in res1.reason.lower()

    # 2. Add active USES_MODEL relationship -> ALLOWED
    rel = GenericRelationship(
        tenant_id=tenant_id,
        source_type="AGENT",
        source_id=str(agent.id),
        relationship_type="USES_MODEL",
        target_type="MODEL",
        target_id=str(model.id),
        effective_from=now,
        status="ACTIVE",
    )
    db.add(rel)
    db.commit()

    res2 = guard.evaluate_model_invocation(tenant_id, agent.id, model.id)
    assert res2.decision == Decision.ALLOW
    assert res2.is_permitted is True


def test_environment_and_version_incompatibility(db: Session):
    user = create_test_user(db, "env_ver")
    tenant_id = user.id
    guard = ModelProviderGuard(db)
    now = datetime.now(timezone.utc)

    agent = Agent(
        id=uuid4(),
        tenant_id=tenant_id,
        agent_code=f"AGT-EV-{uuid4().hex[:6]}",
        agent_name="Env Agent",
        agent_type="AUTONOMOUS",
        execution_mode="AUTONOMOUS",
        risk_level="LOW",
        status="ACTIVE",
    )
    dev_model = AIModel(
        id=uuid4(),
        tenant_id=tenant_id,
        model_code=f"MDL-DEV-{uuid4().hex[:6]}",
        model_name="Llama-3-Dev",
        model_type="LLM",
        purpose="Experimentation",
        deployment_environment="DEVELOPMENT",
        version="2.0-beta",
        status="ACTIVE",
    )
    rel = GenericRelationship(
        tenant_id=tenant_id,
        source_type="AGENT",
        source_id=str(agent.id),
        relationship_type="USES_MODEL",
        target_type="MODEL",
        target_id=str(dev_model.id),
        effective_from=now,
        status="ACTIVE",
    )
    db.add_all([agent, dev_model, rel])
    db.commit()

    # 1. Invoking DEVELOPMENT model in PRODUCTION -> DENIED
    res1 = guard.evaluate_model_invocation(
        tenant_id=tenant_id,
        agent_id=agent.id,
        model_id=dev_model.id,
        environment="PRODUCTION",
    )
    assert res1.decision == Decision.DENY
    assert "PRODUCTION" in res1.reason

    # 2. Invoking with invalid version -> DENIED
    res2 = guard.evaluate_model_invocation(
        tenant_id=tenant_id,
        agent_id=agent.id,
        model_id=dev_model.id,
        requested_version="1.0-deprecated",
        environment="DEVELOPMENT",
    )
    assert res2.decision == Decision.DENY
    assert "version mismatch" in res2.reason.lower()

    # 3. Invoking with correct environment and version -> ALLOWED
    res3 = guard.evaluate_model_invocation(
        tenant_id=tenant_id,
        agent_id=agent.id,
        model_id=dev_model.id,
        requested_version="2.0-beta",
        environment="DEVELOPMENT",
    )
    assert res3.decision == Decision.ALLOW


def test_provider_data_classification_and_fallback_guard(db: Session):
    user = create_test_user(db, "provider_data")
    tenant_id = user.id
    guard = ModelProviderGuard(db)
    now = datetime.now(timezone.utc)

    agent = Agent(
        id=uuid4(),
        tenant_id=tenant_id,
        agent_code=f"AGT-PRV-{uuid4().hex[:6]}",
        agent_name="Provider Agent",
        agent_type="AUTONOMOUS",
        execution_mode="AUTONOMOUS",
        risk_level="LOW",
        status="ACTIVE",
    )
    public_provider = AIModelProvider(
        id=uuid4(),
        tenant_id=tenant_id,
        provider_name="Public Community LLM API",
        provider_type="EXTERNAL",
        hosting_type="PUBLIC",
        risk_classification="HIGH",
    )
    db.add_all([agent, public_provider])
    db.flush()

    public_model = AIModel(
        id=uuid4(),
        tenant_id=tenant_id,
        model_code=f"MDL-PUB-{uuid4().hex[:6]}",
        model_name="Open-Mistral-Public",
        model_type="LLM",
        provider_id=public_provider.id,
        purpose="Public Summarization",
        deployment_environment="PRODUCTION",
        version="1.0",
        status="ACTIVE",
    )
    rel = GenericRelationship(
        tenant_id=tenant_id,
        source_type="AGENT",
        source_id=str(agent.id),
        relationship_type="USES_MODEL",
        target_type="MODEL",
        target_id=str(public_model.id),
        effective_from=now,
        status="ACTIVE",
    )
    db.add_all([public_model, rel])
    db.commit()

    # 1. Routing RESTRICTED data to public/high-risk provider -> DENIED
    res1 = guard.evaluate_model_invocation(
        tenant_id=tenant_id,
        agent_id=agent.id,
        model_id=public_model.id,
        data_classification="RESTRICTED",
    )
    assert res1.decision == Decision.DENY
    assert "RESTRICTED" in res1.reason

    # 2. Routing PUBLIC data to public provider -> ALLOWED
    res2 = guard.evaluate_model_invocation(
        tenant_id=tenant_id,
        agent_id=agent.id,
        model_id=public_model.id,
        data_classification="PUBLIC",
    )
    assert res2.decision == Decision.ALLOW

    # 3. Unauthorized fallback model (no USES_MODEL relationship) -> DENIED
    unlinked_fallback_id = uuid4()
    res3 = guard.evaluate_model_invocation(
        tenant_id=tenant_id,
        agent_id=agent.id,
        model_id=unlinked_fallback_id,
        is_fallback=True,
    )
    assert res3.decision == Decision.DENY
    assert "fallback model" in res3.reason.lower()

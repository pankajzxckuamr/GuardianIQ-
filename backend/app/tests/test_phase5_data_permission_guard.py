from uuid import uuid4
from datetime import datetime, timezone, timedelta
import pytest
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
import app.db.base
from app.modules.auth.models import User
from app.modules.agent.models import Agent
from app.modules.datasource.models import DataSource
from app.modules.agent_boundary.models import DataSourceField, AgentDataPermission
from app.modules.relationship.models import GenericRelationship
from app.modules.data_governance.guard import DataPermissionGuard, DataTransformer
from app.modules.policy_engine.enums import Decision


def create_test_user(db: Session, email_prefix: str = "data_guard") -> User:
    user = User(
        id=uuid4(),
        name=f"User {email_prefix}",
        full_name="Data Guard Test User",
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


def test_data_transformer_pipeline():
    # 1. Masking email, phone, and strings
    assert DataTransformer.transform_value("john.doe@company.com", "MASK") == "j***@company.com"
    assert DataTransformer.transform_value("+1-555-123-4567", "MASK") == "***-***-4567"
    assert DataTransformer.transform_value("SecretValue", "MASK") == "Se***ue"

    # 2. Redacting
    assert DataTransformer.transform_value("HighlySensitiveSSN", "REDACT") == "[REDACTED]"

    # 3. Tokenizing
    tok = DataTransformer.transform_value("Cust-12345", "TOKENIZE")
    assert tok.startswith("tok_")
    assert len(tok) == 16

    # 4. Hashing
    h = DataTransformer.transform_value("RawPassword123", "HASH")
    assert len(h) == 64

    # 5. Transform dataset with multiple field strategies and stripped fields
    raw_dataset = [
        {"id": 1, "email": "alice@guardianiq.ai", "salary": 150000, "ssn": "123-45-6789", "public_name": "Alice"},
        {"id": 2, "email": "bob@guardianiq.ai", "salary": 120000, "ssn": "987-65-4321", "public_name": "Bob"},
    ]
    strategies = {
        "email": "MASK",
        "ssn": "REDACT",
        "salary": "TOKENIZE",
    }
    allowed_fields = ["id", "email", "salary", "ssn", "public_name"]

    transformed = DataTransformer.transform_dataset(raw_dataset, strategies, allowed_fields)
    assert len(transformed) == 2
    assert transformed[0]["email"] == "a***@guardianiq.ai"
    assert transformed[0]["ssn"] == "[REDACTED]"
    assert str(transformed[0]["salary"]).startswith("tok_")
    assert transformed[0]["public_name"] == "Alice"


def test_uses_data_source_relationship_prerequisite(db: Session):
    user = create_test_user(db, "no_ds_rel")
    tenant_id = user.id
    guard = DataPermissionGuard(db)
    now = datetime.now(timezone.utc)

    agent = Agent(
        id=uuid4(),
        tenant_id=tenant_id,
        agent_code=f"AGT-DS-{uuid4().hex[:6]}",
        agent_name="DS Agent",
        agent_type="AUTONOMOUS",
        execution_mode="AUTONOMOUS",
        risk_level="LOW",
        status="ACTIVE",
    )
    ds = DataSource(
        id=uuid4(),
        tenant_id=tenant_id,
        source_code=f"DS-GUARD-{uuid4().hex[:6]}",
        source_name="Guard DB",
        source_type="POSTGRESQL",
        classification="INTERNAL",
        sensitivity_level="LOW",
        status="ACTIVE",
    )
    db.add_all([agent, ds])
    db.commit()

    # 1. Access without USES_DATA_SOURCE relationship -> DENIED
    res1 = guard.evaluate_data_access(tenant_id, agent.id, ds.id, "READ")
    assert res1.decision == Decision.DENY
    assert "relationship" in res1.reason.lower()

    # 2. Add active relationship -> ALLOWED
    rel = GenericRelationship(
        tenant_id=tenant_id,
        source_type="AGENT",
        source_id=str(agent.id),
        relationship_type="USES_DATA_SOURCE",
        target_type="DATA_SOURCE",
        target_id=str(ds.id),
        effective_from=now,
        status="ACTIVE",
    )
    db.add(rel)
    db.commit()

    res2 = guard.evaluate_data_access(tenant_id, agent.id, ds.id, "READ")
    assert res2.decision == Decision.ALLOW
    assert res2.is_permitted is True


def test_field_classification_ceilings_and_masking(db: Session):
    user = create_test_user(db, "field_class")
    tenant_id = user.id
    guard = DataPermissionGuard(db)
    now = datetime.now(timezone.utc)

    agent = Agent(
        id=uuid4(),
        tenant_id=tenant_id,
        agent_code=f"AGT-FC-{uuid4().hex[:6]}",
        agent_name="Field Class Agent",
        agent_type="AUTONOMOUS",
        execution_mode="AUTONOMOUS",
        risk_level="LOW",
        status="ACTIVE",
    )
    ds = DataSource(
        id=uuid4(),
        tenant_id=tenant_id,
        source_code=f"DS-FC-{uuid4().hex[:6]}",
        source_name="Customer DB",
        source_type="POSTGRESQL",
        classification="CONFIDENTIAL",
        sensitivity_level="HIGH",
        status="ACTIVE",
    )
    db.add_all([agent, ds])
    db.flush()

    # Fields: name (INTERNAL), email (CONFIDENTIAL + MASK), credit_card (RESTRICTED + REDACT)
    f_name = DataSourceField(
        id=uuid4(),
        tenant_id=tenant_id,
        data_source_id=ds.id,
        field_name="name",
        classification="INTERNAL",
        sensitivity_level="LOW",
    )
    f_email = DataSourceField(
        id=uuid4(),
        tenant_id=tenant_id,
        data_source_id=ds.id,
        field_name="email",
        classification="CONFIDENTIAL",
        sensitivity_level="MEDIUM",
        masking_strategy="MASK",
    )
    f_card = DataSourceField(
        id=uuid4(),
        tenant_id=tenant_id,
        data_source_id=ds.id,
        field_name="credit_card",
        classification="RESTRICTED",
        sensitivity_level="CRITICAL",
        masking_strategy="REDACT",
    )
    rel = GenericRelationship(
        tenant_id=tenant_id,
        source_type="AGENT",
        source_id=str(agent.id),
        relationship_type="USES_DATA_SOURCE",
        target_type="DATA_SOURCE",
        target_id=str(ds.id),
        effective_from=now,
        status="ACTIVE",
    )
    # Agent permission allows up to CONFIDENTIAL, max sensitivity HIGH
    perm = AgentDataPermission(
        id=uuid4(),
        tenant_id=tenant_id,
        agent_id=agent.id,
        data_source_id=ds.id,
        max_classification="CONFIDENTIAL",
        max_sensitivity="HIGH",
        allowed_operations_json=["READ", "QUERY"],
        is_active=True,
    )
    db.add_all([f_name, f_email, f_card, rel, perm])
    db.commit()

    sample_records = [
        {"name": "John Doe", "email": "john.doe@guardianiq.ai", "credit_card": "4111-2222-3333-4444"},
    ]

    # 1. Requesting all fields including RESTRICTED credit_card explicitly -> DENIED
    res1 = guard.evaluate_data_access(
        tenant_id=tenant_id,
        agent_id=agent.id,
        data_source_id=ds.id,
        operation="READ",
        requested_fields=["name", "email", "credit_card"],
        records=sample_records,
    )
    assert res1.decision == Decision.DENY
    assert "credit_card" in res1.denied_fields

    # 2. Requesting allowed fields (name, email) -> ALLOW_WITH_OBLIGATIONS (due to email MASK)
    res2 = guard.evaluate_data_access(
        tenant_id=tenant_id,
        agent_id=agent.id,
        data_source_id=ds.id,
        operation="READ",
        requested_fields=["name", "email"],
        records=sample_records,
    )
    assert res2.decision == Decision.ALLOW_WITH_OBLIGATIONS
    assert res2.is_permitted is True
    assert res2.transformed_data[0]["email"] == "j***@guardianiq.ai"
    assert res2.transformed_data[0]["name"] == "John Doe"
    assert "credit_card" not in res2.transformed_data[0]


def test_bulk_export_record_limit(db: Session):
    user = create_test_user(db, "bulk_export")
    tenant_id = user.id
    guard = DataPermissionGuard(db)
    now = datetime.now(timezone.utc)

    agent = Agent(
        id=uuid4(),
        tenant_id=tenant_id,
        agent_code=f"AGT-EXP-{uuid4().hex[:6]}",
        agent_name="Export Agent",
        agent_type="AUTONOMOUS",
        execution_mode="AUTONOMOUS",
        risk_level="LOW",
        status="ACTIVE",
    )
    ds = DataSource(
        id=uuid4(),
        tenant_id=tenant_id,
        source_code=f"DS-EXP-{uuid4().hex[:6]}",
        source_name="Large DB",
        source_type="POSTGRESQL",
        classification="INTERNAL",
        sensitivity_level="LOW",
        status="ACTIVE",
    )
    db.add_all([agent, ds])
    db.flush()

    rel = GenericRelationship(
        tenant_id=tenant_id,
        source_type="AGENT",
        source_id=str(agent.id),
        relationship_type="USES_DATA_SOURCE",
        target_type="DATA_SOURCE",
        target_id=str(ds.id),
        effective_from=now,
        status="ACTIVE",
    )
    perm = AgentDataPermission(
        id=uuid4(),
        tenant_id=tenant_id,
        agent_id=agent.id,
        data_source_id=ds.id,
        max_classification="CONFIDENTIAL",
        max_sensitivity="HIGH",
        allowed_operations_json=["READ", "EXPORT"],
        is_active=True,
    )
    db.add_all([rel, perm])
    db.commit()

    # Bulk export of 10,000 records (exceeding 5,000 limit) -> DENIED
    res = guard.evaluate_data_access(
        tenant_id=tenant_id,
        agent_id=agent.id,
        data_source_id=ds.id,
        operation="EXPORT",
        record_count=10000,
    )
    assert res.decision == Decision.DENY
    assert "limit" in res.reason.lower()

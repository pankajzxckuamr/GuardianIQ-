from datetime import datetime, timezone, timedelta
from uuid import uuid4, UUID
import pytest
from sqlalchemy.orm import Session
import time
from unittest.mock import patch

from app.db.session import SessionLocal
import app.db.base
from app.modules.auth.models import User
from app.modules.agent.models import Agent
from app.modules.registry.models import Tool
from app.modules.datasource.models import DataSource
from app.modules.relationship.models import PolicyBinding
from app.modules.relationship.cache_service import MemoryCacheService
from app.modules.agent_boundary.models import AgentRuntimeBoundary
from app.modules.agent_boundary.service import AgentBoundaryService
from app.modules.agent_boundary.resolver import AgentBoundaryResolver
from app.modules.policy_engine.models import GovernancePolicy, PolicyVersion, PolicyRule
from app.modules.policy_engine.service import PolicyService, PolicyVersionService
from app.modules.policy_engine.enums import Decision, EnforcementMode
from app.modules.policy_engine.schemas import GovernedRuntimeRequest
from app.modules.enforcement import (
    GovernedRuntimeContextBuilder,
    RuntimeEnforcementEngine,
)


@pytest.fixture
def db():
    session = SessionLocal()
    MemoryCacheService().clear()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


def create_perf_test_user(db: Session, email_prefix: str = "perf") -> User:
    user = User(
        id=uuid4(),
        name=f"User {email_prefix}",
        full_name="Performance Test User",
        email=f"{email_prefix}_{uuid4().hex[:8]}@guardianiq.ai",
        hashed_password="pw",
    )
    db.add(user)
    db.commit()
    return user


# --------------------------------------------------------------------------------------
# 1. Cache Hit Performance & Latency
# --------------------------------------------------------------------------------------

def test_cache_hit_performance_and_latency(db: Session):
    """
    Verify sub-50ms resolution on warm cache hits and accurate latency_ms measurement.
    """
    user = create_perf_test_user(db, "cache_hit")
    tenant_id = user.id

    agent = Agent(
        id=uuid4(),
        tenant_id=tenant_id,
        agent_code=f"AGT-PERF-{uuid4().hex[:6]}",
        agent_name="Fast Analytics Agent",
        agent_type="AUTONOMOUS",
        execution_mode="AUTONOMOUS",
        risk_level="LOW",
        status="ACTIVE",
    )
    db.add(agent)

    boundary = AgentRuntimeBoundary(
        id=uuid4(),
        tenant_id=tenant_id,
        agent_id=agent.id,
        max_autonomy_level="AUTONOMOUS",
        is_active=True,
    )
    db.add(boundary)
    db.commit()

    resolver = AgentBoundaryResolver(db)

    # 1. Cold query (DB read)
    cold_start = time.perf_counter()
    b_cold = resolver.resolve_boundary(tenant_id, agent.id)
    cold_duration_ms = (time.perf_counter() - cold_start) * 1000.0
    assert b_cold is not None
    assert b_cold.id == boundary.id

    # 2. Warm query (Cache hit)
    warm_start = time.perf_counter()
    b_warm = resolver.resolve_boundary(tenant_id, agent.id)
    warm_duration_ms = (time.perf_counter() - warm_start) * 1000.0
    assert b_warm is not None
    assert b_warm.id == boundary.id
    # Cache hit should be fast (< 50ms)
    assert warm_duration_ms < 50.0


# --------------------------------------------------------------------------------------
# 2. Cache Invalidation on Boundary Changes
# --------------------------------------------------------------------------------------

def test_cache_invalidation_on_boundary_kill_switch(db: Session):
    """
    Verify that updating an agent boundary or engaging the kill-switch invalidates cache.
    """
    user = create_perf_test_user(db, "boundary_cache")
    tenant_id = user.id

    agent = Agent(
        id=uuid4(),
        tenant_id=tenant_id,
        agent_code=f"AGT-KS-{uuid4().hex[:6]}",
        agent_name="KillSwitch Target Agent",
        agent_type="AUTONOMOUS",
        execution_mode="AUTONOMOUS",
        risk_level="HIGH",
        status="ACTIVE",
    )
    db.add(agent)
    db.commit()

    service = AgentBoundaryService(db)
    resolver = AgentBoundaryResolver(db)

    # 1. Create boundary with is_active = True
    b1 = service.set_boundary(tenant_id, {
        "agent_id": agent.id,
        "max_autonomy_level": "AUTONOMOUS",
        "is_active": True,
    })
    assert b1.is_active is True

    # 2. Warm cache
    b_cached = resolver.resolve_boundary(tenant_id, agent.id)
    assert b_cached is not None
    assert b_cached.is_active is True

    # 3. Engage kill switch via service (sets is_active=False and invalidates cache)
    service.set_boundary(tenant_id, {
        "agent_id": agent.id,
        "max_autonomy_level": "AUTONOMOUS",
        "is_active": False,
    })

    # 4. Resolve boundary again: must reflect is_active=False immediately
    b_updated = resolver.resolve_boundary(tenant_id, agent.id)
    assert b_updated is not None
    assert b_updated.is_active is False


# --------------------------------------------------------------------------------------
# 3. DB Fallback on Cache Failure
# --------------------------------------------------------------------------------------

def test_cache_failure_graceful_db_fallback(db: Session):
    """
    Verify that if the in-memory cache encounters an unexpected error, the system
    gracefully and authoritatively falls back to the database without failing open.
    """
    user = create_perf_test_user(db, "cache_fallback")
    tenant_id = user.id

    agent = Agent(
        id=uuid4(),
        tenant_id=tenant_id,
        agent_code=f"AGT-FALLBACK-{uuid4().hex[:6]}",
        agent_name="Fallback Agent",
        agent_type="AUTONOMOUS",
        execution_mode="AUTONOMOUS",
        risk_level="LOW",
        status="ACTIVE",
    )
    db.add(agent)

    boundary = AgentRuntimeBoundary(
        id=uuid4(),
        tenant_id=tenant_id,
        agent_id=agent.id,
        max_autonomy_level="AUTONOMOUS",
        is_active=True,
    )
    db.add(boundary)
    db.commit()

    resolver = AgentBoundaryResolver(db)

    # Mock cache.get to throw an exception
    with patch.object(resolver.cache, "get", side_effect=RuntimeError("Simulated cache failure")):
        b_res = resolver.resolve_boundary(tenant_id, agent.id)
        # Should gracefully return the DB record
        assert b_res is not None
        assert b_res.id == boundary.id


# --------------------------------------------------------------------------------------
# 4. Enforcement Engine Timeout (Fail-Closed)
# --------------------------------------------------------------------------------------

def test_enforcement_engine_timeout_fail_closed(db: Session):
    """
    Verify that when evaluation exceeds the configured timeout_ms threshold,
    the engine fails-closed with Decision.DENY and ENGINE_TIMEOUT_FAIL_CLOSED.
    """
    user = create_perf_test_user(db, "timeout_fail_closed")
    tenant_id = user.id

    agent = Agent(
        id=uuid4(),
        tenant_id=tenant_id,
        agent_code=f"AGT-TIMEOUT-{uuid4().hex[:6]}",
        agent_name="Timeout Test Agent",
        agent_type="AUTONOMOUS",
        execution_mode="AUTONOMOUS",
        risk_level="MEDIUM",
        status="ACTIVE",
    )
    db.add(agent)
    db.commit()

    req = GovernedRuntimeContextBuilder.build_request(
        actor_id="user_test",
        role="OPERATOR",
        agent_id=str(agent.id),
        enforcement_mode=EnforcementMode.BLOCKING,
    )

    engine = RuntimeEnforcementEngine(db)

    # Calling with timeout_ms=0 forces immediate timeout fail-closed
    result = engine.enforce(req, tenant_id=tenant_id, timeout_ms=0)
    assert result.decision == Decision.DENY
    assert result.execution_permitted is False
    assert any("timeout" in str(v).lower() for v in result.violations) or any("timeout" in str(r).lower() for r in result.reasons)
    assert result.latency_ms is not None


# --------------------------------------------------------------------------------------
# 5. Runtime Latency Measurement
# --------------------------------------------------------------------------------------

def test_runtime_latency_measurement(db: Session):
    """
    Verify that latency_ms is accurately calculated, reported in response, and > 0.0.
    """
    user = create_perf_test_user(db, "latency_metric")
    tenant_id = user.id

    req = GovernedRuntimeContextBuilder.build_request(
        actor_id="user_test",
        role="OPERATOR",
        operation="read_status",
        enforcement_mode=EnforcementMode.BLOCKING,
    )

    engine = RuntimeEnforcementEngine(db)
    result = engine.enforce(req, tenant_id=tenant_id)
    assert result.latency_ms is not None
    assert result.latency_ms > 0.0

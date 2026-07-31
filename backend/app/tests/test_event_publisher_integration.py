"""
Integration test suite for Phase 4 EventPublisherService across 5 operational flows (WBS 4.4.4)
"""
import pytest
from uuid import uuid4
from datetime import datetime, timezone
from types import SimpleNamespace
from sqlalchemy import text

from app.db.session import SessionLocal
from app.modules.auth.models import User
from app.modules.events.models import GovernanceEvent, EventOutbox
from app.modules.relationship.audit_service import RelationshipAuditService
from app.modules.workflow_execution.service import WorkflowRunService
from app.modules.workflow_execution.models import WorkflowRun
from app.modules.workflow_scheduler.models import Phase2WorkflowSchedule
from app.modules.agent_runtime.boundary_checker import BoundaryChecker

def seed_test_schema_registry(db):
    event_types = [
        "RELATIONSHIP_CREATED", 
        "RELATIONSHIP_REVOKED", 
        "WORKFLOW_RUN_STARTED", 
        "WORKFLOW_RUN_COMPLETED", 
        "UNAUTHORIZED_ACCESS_BLOCKED"
    ]
    for et in event_types:
        existing = db.execute(
            text("SELECT 1 FROM event_schema_registry WHERE event_type = :type AND version = '1.0'"),
            {"type": et}
        ).fetchone()
        if not existing:
            db.execute(
                text("""
                    INSERT INTO event_schema_registry 
                    (id, event_type, version, json_schema, is_active, created_at) 
                    VALUES (:id, :type, '1.0', '{}', true, CURRENT_TIMESTAMP)
                """),
                {"id": str(uuid4()), "type": et}
            )
    db.commit()

def get_test_user():
    db = SessionLocal()
    try:
        seed_test_schema_registry(db)
        user = db.query(User).filter_by(email="test_integration@guardianiq.demo").first()
        if not user:
            user = User(
                id=uuid4(),
                email="test_integration@guardianiq.demo",
                name="Test Integration User",
                hashed_password="hashed_pwd_stub"
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        return user.id
    finally:
        db.close()

@pytest.mark.asyncio
async def test_relationship_created_publishes_governance_event():
    """Flow 1: Verify RELATIONSHIP_CREATED emits GovernanceEvent and EventOutbox."""
    db = SessionLocal()
    try:
        tenant_id = get_test_user()
        rel_audit = RelationshipAuditService(db=db, current_user_id=tenant_id)
        rel_id = uuid4()
        
        await rel_audit.publish_relationship_created(rel_id, {"source": "unit_test"})
        db.commit()

        evt = db.query(GovernanceEvent).filter_by(event_type="RELATIONSHIP_CREATED", tenant_id=tenant_id).order_by(GovernanceEvent.recorded_at.desc()).first()
        assert evt is not None
        assert evt.subject_json["entity_id"] == str(rel_id)

        outbox = db.query(EventOutbox).filter_by(event_id=evt.event_id).first()
        assert outbox is not None
        assert outbox.status == "PENDING"
    finally:
        db.close()

@pytest.mark.asyncio
async def test_relationship_revoked_publishes_governance_event():
    """Flow 2: Verify RELATIONSHIP_REVOKED emits GovernanceEvent."""
    db = SessionLocal()
    try:
        tenant_id = get_test_user()
        rel_audit = RelationshipAuditService(db=db, current_user_id=tenant_id)
        rel_id = uuid4()

        await rel_audit.publish_relationship_revoked(rel_id, reason="Security policy update")
        db.commit()

        evt = db.query(GovernanceEvent).filter_by(event_type="RELATIONSHIP_REVOKED", tenant_id=tenant_id).order_by(GovernanceEvent.recorded_at.desc()).first()
        assert evt is not None
        assert evt.subject_json["entity_id"] == str(rel_id)
        assert evt.payload_json["reason"] == "Security policy update"
    finally:
        db.close()

def create_test_schedule(db, tenant_id, sched_id, wf_id):
    from app.modules.registry.models import RegistryWorkflow
    wf = db.query(RegistryWorkflow).filter_by(id=wf_id).first()
    if not wf:
        wf = RegistryWorkflow(
            id=wf_id,
            tenant_id=tenant_id,
            workflow_name="Test Workflow",
            workflow_code="WF_TEST_" + str(wf_id)[:6],
            workflow_type="AUTOMATED",
            business_criticality="LOW",
            created_by=tenant_id,
            updated_by=tenant_id
        )
        db.add(wf)
        db.commit()

    sched = db.query(Phase2WorkflowSchedule).filter_by(id=sched_id).first()
    if not sched:
        sched = Phase2WorkflowSchedule(
            id=sched_id,
            tenant_id=tenant_id,
            workflow_id=wf_id,
            schedule_name="Test Schedule " + str(sched_id)[:6],
            schedule_code="SCHED_TEST_" + str(sched_id)[:6],
            schedule_type="MANUAL",
            schedule_status="ACTIVE",
            risk_level="LOW",
            owner_user_id=tenant_id,
            created_by=tenant_id,
            updated_by=tenant_id
        )
        db.add(sched)
        db.commit()

@pytest.mark.asyncio
async def test_workflow_run_started_publishes_governance_event():
    """Flow 3: Verify WORKFLOW_RUN_STARTED emits GovernanceEvent."""
    db = SessionLocal()
    try:
        tenant_id = get_test_user()
        sched_id = uuid4()
        wf_id = uuid4()
        run_id = uuid4()

        create_test_schedule(db, tenant_id, sched_id, wf_id)

        run = WorkflowRun(
            id=run_id,
            tenant_id=tenant_id,
            schedule_id=sched_id,
            workflow_id=wf_id,
            run_code="RUN-TEST-001",
            trigger_type="MANUAL",
            triggered_by_user_id=tenant_id,
            run_status="QUEUED",
            risk_level="LOW",
            created_by=tenant_id,
            updated_by=tenant_id
        )
        db.add(run)
        db.commit()

        wf_service = WorkflowRunService()
        await wf_service.start_run(run_id, db)
        db.commit()

        evt = db.query(GovernanceEvent).filter_by(event_type="WORKFLOW_RUN_STARTED", tenant_id=tenant_id).order_by(GovernanceEvent.recorded_at.desc()).first()
        assert evt is not None
        assert evt.subject_json["entity_id"] == str(run_id)
    finally:
        db.close()

@pytest.mark.asyncio
async def test_workflow_run_completed_publishes_governance_event():
    """Flow 4: Verify WORKFLOW_RUN_COMPLETED emits GovernanceEvent resolving agent_id."""
    db = SessionLocal()
    try:
        tenant_id = get_test_user()
        sched_id = uuid4()
        wf_id = uuid4()
        run_id = uuid4()
        agent_id = uuid4()

        create_test_schedule(db, tenant_id, sched_id, wf_id)

        run = WorkflowRun(
            id=run_id,
            tenant_id=tenant_id,
            schedule_id=sched_id,
            workflow_id=wf_id,
            run_code="RUN-TEST-002",
            trigger_type="MANUAL",
            triggered_by_user_id=tenant_id,
            run_status="RUNNING",
            started_at=datetime.now(timezone.utc),
            risk_level="LOW",
            created_by=tenant_id,
            updated_by=tenant_id
        )
        db.add(run)
        db.commit()

        assignment_mock = SimpleNamespace(agent_id=agent_id)
        wf_service = WorkflowRunService()
        await wf_service.complete_run(run_id, db, primary_assignment=assignment_mock)
        db.commit()

        evt = db.query(GovernanceEvent).filter_by(event_type="WORKFLOW_RUN_COMPLETED", tenant_id=tenant_id).order_by(GovernanceEvent.recorded_at.desc()).first()
        assert evt is not None
        assert evt.payload_json["agent_id"] == str(agent_id)
    finally:
        db.close()

@pytest.mark.asyncio
async def test_agent_boundary_blocked_publishes_governance_event():
    """Flow 5: Verify UNAUTHORIZED_ACCESS_BLOCKED emits GovernanceEvent on boundary failure."""
    db = SessionLocal()
    try:
        tenant_id = get_test_user()
        agent_id = uuid4()
        sched_id = uuid4()
        assignment_mock = SimpleNamespace(agent_id=agent_id, schedule_id=sched_id, tenant_id=tenant_id)

        checker = BoundaryChecker()
        await checker._publish_failure(assignment_mock, "Unauthorized write operation blocked", db)
        db.commit()

        evt = db.query(GovernanceEvent).filter_by(event_type="UNAUTHORIZED_ACCESS_BLOCKED", tenant_id=tenant_id).order_by(GovernanceEvent.recorded_at.desc()).first()
        assert evt is not None
        assert evt.event_category == "Violation"
        assert evt.payload_json["reason"] == "Unauthorized write operation blocked"
    finally:
        db.close()

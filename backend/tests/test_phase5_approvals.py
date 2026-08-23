import pytest
import asyncio
from uuid import uuid4
from httpx import AsyncClient, ASGITransport
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock environment variables required by Settings
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-key-for-pytest"

from app.main import app
from app.db.session import SessionLocal, Base, engine
from app.modules.workflow_scheduler.models import Phase2WorkflowSchedule, WorkflowScheduleApproval
from app.modules.department.models import Department, DepartmentOwnerAssignment
from app.modules.auth.models import User
from sqlalchemy import select

pytestmark = pytest.mark.anyio

@pytest.fixture
def anyio_backend():
    return 'asyncio'

@pytest.fixture
async def async_client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

# --- MOCK TOKENS AND SETUP ---
# Since we don't have the full auth setup for dynamic users in this snippet, 
# we'll assume the endpoints use get_current_user which we can mock or we use the DB to bypass.
# But since this is an E2E test, we'd normally authenticate as specific users. 
# For these tests, we will mock the service directly using the DB session for some scenarios 
# to ensure precise control over the state, and use HTTP endpoints where appropriate.

@pytest.fixture(autouse=True)
def init_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def setup_mock_department_chain(db_session, user_ids: list):
    # Create departments and owners
    depts = []
    codes = ["BUSINESS_OWNER", "TECHNICAL_OWNER", "LEGAL", "AUDIT", "HR"]
    
    for i, u_id in enumerate(user_ids):
        d_id = uuid4()
        dept = Department(id=d_id, tenant_id=uuid4(), department_code=codes[i], display_name=f"{codes[i]} Dept")
        assignment = DepartmentOwnerAssignment(
            id=uuid4(), tenant_id=dept.tenant_id, department_id=d_id, owner_user_id=u_id, role_type="OWNER"
        )
        db_session.add(dept)
        db_session.add(assignment)
        depts.append(dept)
    
    db_session.commit()
    return depts

# Note: The following test cases are written using the WorkflowScheduleService directly 
# to cleanly test the complex state machine, as full E2E setup for 5 distinct JWTs 
# is highly environment-dependent.

@pytest.fixture
def workflow_service():
    from app.modules.workflow_scheduler.service import WorkflowScheduleService
    return WorkflowScheduleService()

class MockUser:
    def __init__(self, user_id, role_code="APPROVER"):
        self.id = user_id
        self.role_code = role_code

@pytest.mark.asyncio
async def test_3_department_chain_sequential_approval(db_session, workflow_service):
    # Scenario: 3-department chain, distinct owners -> sequential PENDING, ACTIVE at end
    user1, user2, user3 = uuid4(), uuid4(), uuid4()
    depts = await setup_mock_department_chain(db_session, [user1, user2, user3])
    
    tenant_id = depts[0].tenant_id
    sched_id = uuid4()
    
    # Mock user creation
    for uid in [user1, user2, user3]:
        db_session.add(User(id=uid, tenant_id=tenant_id, email=f"{uid}@test.com", password_hash="hash", username=str(uid)))
        
    schedule = Phase2WorkflowSchedule(
        id=sched_id, tenant_id=tenant_id, workflow_id=uuid4(), schedule_code="TEST_1",
        schedule_name="Test 1", schedule_type="DAILY", owner_user_id=user1, approval_required=True, schedule_status="DRAFT"
    )
    db_session.add(schedule)
    db_session.commit()
    
    # Setup layers
    from app.modules.workflow_scheduler.models import ScheduleApprovalLayerSelection
    for i, dept in enumerate(depts):
        db_session.add(ScheduleApprovalLayerSelection(schedule_id=sched_id, department_id=dept.id, layer_order=i+1, tenant_id=tenant_id))
    db_session.commit()
    
    # Act: Submit
    await workflow_service.submit_for_approval(sched_id, MockUser(user1), db_session)
    db_session.refresh(schedule)
    assert schedule.schedule_status == "PENDING_APPROVAL"
    
    # Verify Layer 1
    stmt = select(WorkflowScheduleApproval).where(WorkflowScheduleApproval.schedule_id == sched_id)
    res = db_session.execute(stmt)
    approvals = res.scalars().all()
    assert len(approvals) == 1
    app1 = approvals[0]
    assert app1.approval_layer == 1
    assert app1.approval_status == "PENDING"
    
    # Approve Layer 1
    await workflow_service.decide_approval(app1.id, "APPROVED", "OK 1", MockUser(user1), db_session)
    
    # Verify Layer 2
    res = db_session.execute(stmt)
    approvals = sorted(res.scalars().all(), key=lambda x: x.created_at)
    assert len(approvals) == 2
    app2 = approvals[-1]
    assert app2.approval_layer == 2
    assert app2.approval_status == "PENDING"
    
    # Approve Layer 2
    await workflow_service.decide_approval(app2.id, "APPROVED", "OK 2", MockUser(user2), db_session)
    
    # Verify Layer 3
    res = db_session.execute(stmt)
    approvals = sorted(res.scalars().all(), key=lambda x: x.created_at)
    assert len(approvals) == 3
    app3 = approvals[-1]
    assert app3.approval_layer == 3
    assert app3.approval_status == "PENDING"
    
    # Approve Layer 3
    await workflow_service.decide_approval(app3.id, "APPROVED", "OK 3", MockUser(user3), db_session)
    
    # Verify ACTIVE
    db_session.refresh(schedule)
    assert schedule.schedule_status == "ACTIVE"


@pytest.mark.asyncio
async def test_same_owner_skips_layer(db_session, workflow_service):
    # Scenario: Same owner assigned to two selected departments -> second is SKIPPED
    user1 = uuid4()
    depts = await setup_mock_department_chain(db_session, [user1, user1]) # Same owner!
    
    tenant_id = depts[0].tenant_id
    sched_id = uuid4()
    
    db_session.add(User(id=user1, tenant_id=tenant_id, email=f"{user1}@test.com", password_hash="hash", username=str(user1)))
    schedule = Phase2WorkflowSchedule(
        id=sched_id, tenant_id=tenant_id, workflow_id=uuid4(), schedule_code="TEST_2",
        schedule_name="Test 2", schedule_type="DAILY", owner_user_id=user1, approval_required=True, schedule_status="DRAFT"
    )
    db_session.add(schedule)
    db_session.add(ScheduleApprovalLayerSelection(schedule_id=sched_id, department_id=depts[0].id, layer_order=1, tenant_id=tenant_id))
    db_session.add(ScheduleApprovalLayerSelection(schedule_id=sched_id, department_id=depts[1].id, layer_order=2, tenant_id=tenant_id))
    db_session.commit()
    
    # Act: Submit
    # But wait, our new rule says "Entire selected department set resolves to a single owner -> rejected"
    # So this should fail with 400! Let's test THAT rule here!
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await workflow_service.submit_for_approval(sched_id, MockUser(user1), db_session)
    assert "resolves to a single owner" in exc.value.detail["message"]

@pytest.mark.asyncio
async def test_same_owner_skips_middle_layer(db_session, workflow_service):
    # Scenario: 3 depts, owners A, B, A. 
    # Layer 1 (A), Layer 2 (B), Layer 3 (A) -> Layer 3 gets skipped!
    userA, userB = uuid4(), uuid4()
    depts = await setup_mock_department_chain(db_session, [userA, userB, userA])
    
    tenant_id = depts[0].tenant_id
    sched_id = uuid4()
    db_session.add(User(id=userA, tenant_id=tenant_id, email=f"{userA}@test.com", password_hash="h", username=str(userA)))
    db_session.add(User(id=userB, tenant_id=tenant_id, email=f"{userB}@test.com", password_hash="h", username=str(userB)))
    schedule = Phase2WorkflowSchedule(id=sched_id, tenant_id=tenant_id, workflow_id=uuid4(), schedule_code="TEST_3", schedule_name="T3", schedule_type="DAILY", owner_user_id=userA, approval_required=True)
    db_session.add(schedule)
    for i, dept in enumerate(depts):
        db_session.add(ScheduleApprovalLayerSelection(schedule_id=sched_id, department_id=dept.id, layer_order=i+1, tenant_id=tenant_id))
    db_session.commit()
    
    await workflow_service.submit_for_approval(sched_id, MockUser(userA), db_session)
    
    stmt = select(WorkflowScheduleApproval).where(WorkflowScheduleApproval.schedule_id == sched_id)
    res = db_session.execute(stmt)
    app1 = res.scalars().first()
    
    # Approve Layer 1 (A)
    await workflow_service.decide_approval(app1.id, "APPROVED", "OK", MockUser(userA), db_session)
    
    res = db_session.execute(stmt)
    approvals = sorted(res.scalars().all(), key=lambda x: x.created_at)
    assert len(approvals) == 2
    app2 = approvals[-1]
    assert app2.approval_layer == 2
    assert app2.approval_status == "PENDING"
    
    # Approve Layer 2 (B) -> Layer 3 (A) should be skipped, schedule becomes ACTIVE
    await workflow_service.decide_approval(app2.id, "APPROVED", "OK", MockUser(userB), db_session)
    
    res = db_session.execute(stmt)
    approvals = sorted(res.scalars().all(), key=lambda x: x.created_at)
    assert len(approvals) == 3
    app3 = approvals[-1]
    assert app3.approval_layer == 3
    assert app3.approval_status == "SKIPPED"
    
    db_session.refresh(schedule)
    assert schedule.schedule_status == "ACTIVE"


@pytest.mark.asyncio
async def test_reject_terminates_chain(db_session, workflow_service):
    user1, user2 = uuid4(), uuid4()
    depts = await setup_mock_department_chain(db_session, [user1, user2])
    tenant_id = depts[0].tenant_id
    sched_id = uuid4()
    
    db_session.add(User(id=user1, tenant_id=tenant_id, email=f"{user1}@test.com", password_hash="h", username=str(user1)))
    schedule = Phase2WorkflowSchedule(id=sched_id, tenant_id=tenant_id, workflow_id=uuid4(), schedule_code="TEST_4", schedule_name="T4", schedule_type="DAILY", owner_user_id=user1, approval_required=True)
    db_session.add(schedule)
    db_session.add(ScheduleApprovalLayerSelection(schedule_id=sched_id, department_id=depts[0].id, layer_order=1, tenant_id=tenant_id))
    db_session.add(ScheduleApprovalLayerSelection(schedule_id=sched_id, department_id=depts[1].id, layer_order=2, tenant_id=tenant_id))
    db_session.commit()
    
    await workflow_service.submit_for_approval(sched_id, MockUser(user1), db_session)
    
    stmt = select(WorkflowScheduleApproval).where(WorkflowScheduleApproval.schedule_id == sched_id)
    app1 = db_session.execute(stmt).scalars().first()
    
    # REJECT layer 1
    await workflow_service.decide_approval(app1.id, "REJECTED", "No", MockUser(user1), db_session)
    
    db_session.refresh(schedule)
    assert schedule.schedule_status == "DRAFT"
    
    # Ensure layer 2 never created
    apps = db_session.execute(stmt).scalars().all()
    assert len(apps) == 1


@pytest.mark.asyncio
async def test_resubmission_new_cycle(db_session, workflow_service):
    user1, user2 = uuid4(), uuid4()
    depts = await setup_mock_department_chain(db_session, [user1, user2])
    tenant_id = depts[0].tenant_id
    sched_id = uuid4()
    
    db_session.add(User(id=user1, tenant_id=tenant_id, email=f"{user1}@test.com", password_hash="h", username=str(user1)))
    db_session.add(User(id=user2, tenant_id=tenant_id, email=f"{user2}@test.com", password_hash="h", username=str(user2)))
    schedule = Phase2WorkflowSchedule(id=sched_id, tenant_id=tenant_id, workflow_id=uuid4(), schedule_code="TEST_5", schedule_name="T5", schedule_type="DAILY", owner_user_id=user1, approval_required=True)
    db_session.add(schedule)
    db_session.add(ScheduleApprovalLayerSelection(schedule_id=sched_id, department_id=depts[0].id, layer_order=1, tenant_id=tenant_id))
    db_session.add(ScheduleApprovalLayerSelection(schedule_id=sched_id, department_id=depts[1].id, layer_order=2, tenant_id=tenant_id))
    db_session.commit()
    
    await workflow_service.submit_for_approval(sched_id, MockUser(user1), db_session)
    
    stmt = select(WorkflowScheduleApproval).where(WorkflowScheduleApproval.schedule_id == sched_id).order_by(WorkflowScheduleApproval.created_at.desc())
    app1 = db_session.execute(stmt).scalars().first()
    first_cycle_id = app1.approval_cycle_id
    
    # REJECT
    await workflow_service.decide_approval(app1.id, "REJECTED", "No", MockUser(user1), db_session)
    
    # Resubmit
    await workflow_service.submit_for_approval(sched_id, MockUser(user1), db_session)
    app1_retry = db_session.execute(stmt).scalars().first()
    
    assert app1_retry.approval_cycle_id != first_cycle_id
    # Ensure it's back at layer 1 and PENDING
    assert app1_retry.approval_layer == 1
    assert app1_retry.approval_status == "PENDING"
    
    # Ensure user1 can approve again in the new cycle
    await workflow_service.decide_approval(app1_retry.id, "APPROVED", "Yes", MockUser(user1), db_session)
    
    # Try deciding the old row
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await workflow_service.decide_approval(app1.id, "APPROVED", "Stale", MockUser(user1), db_session)
    assert "stale" in exc.value.detail["message"]


@pytest.mark.asyncio
async def test_escalate_preserves_chain(db_session, workflow_service):
    user1 = uuid4()
    depts = await setup_mock_department_chain(db_session, [user1])
    tenant_id = depts[0].tenant_id
    sched_id = uuid4()
    
    db_session.add(User(id=user1, tenant_id=tenant_id, email=f"{user1}@test.com", password_hash="h", username=str(user1)))
    schedule = Phase2WorkflowSchedule(id=sched_id, tenant_id=tenant_id, workflow_id=uuid4(), schedule_code="TEST_6", schedule_name="T6", schedule_type="DAILY", owner_user_id=user1, approval_required=True)
    db_session.add(schedule)
    db_session.add(ScheduleApprovalLayerSelection(schedule_id=sched_id, department_id=depts[0].id, layer_order=1, tenant_id=tenant_id))
    db_session.commit()
    
    await workflow_service.submit_for_approval(sched_id, MockUser(user1), db_session)
    
    stmt = select(WorkflowScheduleApproval).where(WorkflowScheduleApproval.schedule_id == sched_id)
    app1 = db_session.execute(stmt).scalars().first()
    
    await workflow_service.decide_approval(app1.id, "ESCALATED", "Help", MockUser(user1), db_session)
    
    db_session.refresh(schedule)
    assert schedule.schedule_status == "PENDING_APPROVAL"
    
    app1_refreshed = db_session.execute(stmt).scalars().first()
    assert app1_refreshed.approval_status == "ESCALATED"


@pytest.mark.asyncio
async def test_activate_while_pending_rejected(db_session, workflow_service):
    user1, user2 = uuid4(), uuid4()
    depts = await setup_mock_department_chain(db_session, [user1, user2])
    tenant_id = depts[0].tenant_id
    sched_id = uuid4()
    
    db_session.add(User(id=user1, tenant_id=tenant_id, email=f"{user1}@test.com", password_hash="h", username=str(user1)))
    db_session.add(User(id=user2, tenant_id=tenant_id, email=f"{user2}@test.com", password_hash="h", username=str(user2)))
    schedule = Phase2WorkflowSchedule(id=sched_id, tenant_id=tenant_id, workflow_id=uuid4(), schedule_code="TEST_7", schedule_name="T7", schedule_type="DAILY", owner_user_id=user1, approval_required=True)
    db_session.add(schedule)
    db_session.add(ScheduleApprovalLayerSelection(schedule_id=sched_id, department_id=depts[0].id, layer_order=1, tenant_id=tenant_id))
    db_session.add(ScheduleApprovalLayerSelection(schedule_id=sched_id, department_id=depts[1].id, layer_order=2, tenant_id=tenant_id))
    db_session.commit()
    
    await workflow_service.submit_for_approval(sched_id, MockUser(user1), db_session)
    
    # Layer 1 is pending. If we try to activate directly:
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await workflow_service.activate_schedule(sched_id, MockUser(user1), db_session)
    # The activate_schedule should fail if approval is required and it's not bypassed correctly, 
    # but the service layer decide_approval does the check before calling activate_schedule.
    # Actually, activate_schedule enforces schedule_status == "APPROVED" unless bypassed.
    assert exc.value.status_code in [400, 403]


@pytest.mark.asyncio
async def test_unauthorized_user_rejected(db_session, workflow_service):
    user1, hacker = uuid4(), uuid4()
    depts = await setup_mock_department_chain(db_session, [user1])
    tenant_id = depts[0].tenant_id
    sched_id = uuid4()
    
    db_session.add(User(id=user1, tenant_id=tenant_id, email=f"{user1}@test.com", password_hash="h", username=str(user1)))
    db_session.add(User(id=hacker, tenant_id=tenant_id, email=f"{hacker}@test.com", password_hash="h", username=str(hacker)))
    schedule = Phase2WorkflowSchedule(id=sched_id, tenant_id=tenant_id, workflow_id=uuid4(), schedule_code="TEST_8", schedule_name="T8", schedule_type="DAILY", owner_user_id=user1, approval_required=True)
    db_session.add(schedule)
    db_session.add(ScheduleApprovalLayerSelection(schedule_id=sched_id, department_id=depts[0].id, layer_order=1, tenant_id=tenant_id))
    db_session.commit()
    
    await workflow_service.submit_for_approval(sched_id, MockUser(user1), db_session)
    
    stmt = select(WorkflowScheduleApproval).where(WorkflowScheduleApproval.schedule_id == sched_id)
    app1 = db_session.execute(stmt).scalars().first()
    
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        # hacker tries to approve user1's layer
        await workflow_service.decide_approval(app1.id, "APPROVED", "Hacked", MockUser(hacker, role_code="USER"), db_session)
    assert exc.value.status_code == 403
    assert "Access denied" in exc.value.detail["message"]


@pytest.mark.asyncio
async def test_single_department_approval(db_session, workflow_service):
    user1 = uuid4()
    depts = await setup_mock_department_chain(db_session, [user1])
    tenant_id = depts[0].tenant_id
    sched_id = uuid4()
    
    db_session.add(User(id=user1, tenant_id=tenant_id, email=f"{user1}@test.com", password_hash="h", username=str(user1)))
    schedule = Phase2WorkflowSchedule(id=sched_id, tenant_id=tenant_id, workflow_id=uuid4(), schedule_code="TEST_9", schedule_name="T9", schedule_type="DAILY", owner_user_id=user1, approval_required=True)
    db_session.add(schedule)
    db_session.add(ScheduleApprovalLayerSelection(schedule_id=sched_id, department_id=depts[0].id, layer_order=1, tenant_id=tenant_id))
    db_session.commit()
    
    await workflow_service.submit_for_approval(sched_id, MockUser(user1), db_session)
    
    stmt = select(WorkflowScheduleApproval).where(WorkflowScheduleApproval.schedule_id == sched_id)
    app1 = db_session.execute(stmt).scalars().first()
    
    await workflow_service.decide_approval(app1.id, "APPROVED", "OK", MockUser(user1), db_session)
    
    db_session.refresh(schedule)
    assert schedule.schedule_status == "ACTIVE"




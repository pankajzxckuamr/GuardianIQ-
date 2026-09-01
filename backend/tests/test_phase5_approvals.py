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
import app.db.base
from app.modules.workflow_scheduler.models import Phase2WorkflowSchedule, WorkflowScheduleApproval, WorkflowScheduleAgentAssignment, ScheduleApprovalLayerSelection
from app.modules.department.models import Department, DepartmentOwnerAssignment
from app.modules.auth.models import User
from sqlalchemy import select
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import JSONB

@compiles(JSONB, "sqlite")
def compile_jsonb_sqlite(type_, compiler, **kw):
    return "JSON"

pytestmark = pytest.mark.anyio

@pytest.fixture
def anyio_backend():
    return 'asyncio'

@pytest.fixture
async def async_client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

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
    depts = []
    codes = ["BUSINESS_OWNER", "TECHNICAL_OWNER", "LEGAL", "AUDIT", "HR"]
    prefix = uuid4().hex[:6].upper()
    
    for i, u_id in enumerate(user_ids):
        d_id = uuid4()
        code = f"{codes[i % len(codes)]}_{prefix}_{i}"
        dept = Department(id=d_id, tenant_id=uuid4(), department_code=code, department_name=f"{code} Dept")
        assignment = DepartmentOwnerAssignment(
            id=uuid4(), tenant_id=dept.tenant_id, department_id=d_id, owner_user_id=u_id
        )
        db_session.add(dept)
        db_session.add(assignment)
        depts.append(dept)
    
    db_session.commit()
    return depts

@pytest.fixture
def workflow_service():
    from app.modules.workflow_scheduler.service import WorkflowScheduleService
    return WorkflowScheduleService()

class MockUser:
    def __init__(self, user_id, role_code="APPROVER", is_superuser=False):
        self.id = user_id
        self.role_code = role_code
        self.is_superuser = is_superuser


@pytest.mark.asyncio
async def test_3_department_chain_sequential_approval(db_session, workflow_service):
    creator = uuid4()
    user1, user2, user3 = uuid4(), uuid4(), uuid4()
    depts = await setup_mock_department_chain(db_session, [user1, user2, user3])
    
    tenant_id = depts[0].tenant_id
    sched_id = uuid4()
    
    for uid in [creator, user1, user2, user3]:
        db_session.add(User(id=uid, name=str(uid), email=f"{uid}@test.com", hashed_password="hash"))
        
    schedule = Phase2WorkflowSchedule(
        id=sched_id, tenant_id=tenant_id, workflow_id=uuid4(), schedule_code="TEST_1",
        schedule_name="Test 1", schedule_type="DAILY", owner_user_id=creator, approval_required=True, schedule_status="DRAFT"
    )
    db_session.add(schedule)
    db_session.add(WorkflowScheduleAgentAssignment(schedule_id=sched_id, agent_id=uuid4(), assignment_role="PRIMARY", tenant_id=tenant_id))
    db_session.commit()
    
    # Setup layers with approver_user_ids
    for i, dept in enumerate(depts):
        approver = [user1, user2, user3][i]
        db_session.add(ScheduleApprovalLayerSelection(
            schedule_id=sched_id, department_id=dept.id, layer_order=i+1, 
            approver_user_ids=[str(approver)], require_all_approvers=True, tenant_id=tenant_id
        ))
    db_session.commit()
    
    # Submit
    await workflow_service.submit_for_approval(sched_id, MockUser(creator), db_session)
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
    assert app1.approver_user_id == user1
    
    # Approve Layer 1
    await workflow_service.decide_approval(app1.id, "APPROVED", "OK 1", MockUser(user1), db_session)
    
    # Verify Layer 2
    res = db_session.execute(stmt)
    approvals = sorted(res.scalars().all(), key=lambda x: x.created_at)
    assert len(approvals) == 2
    app2 = approvals[-1]
    assert app2.approval_layer == 2
    assert app2.approval_status == "PENDING"
    assert app2.approver_user_id == user2
    
    # Approve Layer 2
    await workflow_service.decide_approval(app2.id, "APPROVED", "OK 2", MockUser(user2), db_session)
    
    # Verify Layer 3
    res = db_session.execute(stmt)
    approvals = sorted(res.scalars().all(), key=lambda x: x.created_at)
    assert len(approvals) == 3
    app3 = approvals[-1]
    assert app3.approval_layer == 3
    assert app3.approval_status == "PENDING"
    assert app3.approver_user_id == user3
    
    # Approve Layer 3
    await workflow_service.decide_approval(app3.id, "APPROVED", "OK 3", MockUser(user3), db_session)
    
    # Verify ACTIVE
    db_session.refresh(schedule)
    assert schedule.schedule_status == "ACTIVE"


@pytest.mark.asyncio
async def test_self_approval_guard_rejection(db_session, workflow_service):
    # Scenario: Creator assigns only themselves as the approver for a department layer
    creator = uuid4()
    depts = await setup_mock_department_chain(db_session, [creator])
    
    tenant_id = depts[0].tenant_id
    sched_id = uuid4()
    
    db_session.add(User(id=creator, name=str(creator), email=f"{creator}@test.com", hashed_password="hash"))
    schedule = Phase2WorkflowSchedule(
        id=sched_id, tenant_id=tenant_id, workflow_id=uuid4(), schedule_code="TEST_SELF",
        schedule_name="Test Self Approval", schedule_type="DAILY", owner_user_id=creator, approval_required=True, schedule_status="DRAFT"
    )
    db_session.add(schedule)
    db_session.add(WorkflowScheduleAgentAssignment(schedule_id=sched_id, agent_id=uuid4(), assignment_role="PRIMARY", tenant_id=tenant_id))
    db_session.add(ScheduleApprovalLayerSelection(
        schedule_id=sched_id, department_id=depts[0].id, layer_order=1, 
        approver_user_ids=[str(creator)], require_all_approvers=True, tenant_id=tenant_id
    ))
    db_session.commit()
    
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await workflow_service.submit_for_approval(sched_id, MockUser(creator), db_session)
    assert "Self-approval violation" in exc.value.detail["message"]


@pytest.mark.asyncio
async def test_intra_layer_unanimous_quorum(db_session, workflow_service):
    # Scenario: 1 Department with 2 approvers (userA and userB), require_all_approvers = True
    creator = uuid4()
    userA, userB = uuid4(), uuid4()
    depts = await setup_mock_department_chain(db_session, [userA])
    
    tenant_id = depts[0].tenant_id
    sched_id = uuid4()
    
    for uid in [creator, userA, userB]:
        db_session.add(User(id=uid, name=str(uid), email=f"{uid}@test.com", hashed_password="hash"))
        
    schedule = Phase2WorkflowSchedule(
        id=sched_id, tenant_id=tenant_id, workflow_id=uuid4(), schedule_code="TEST_UNANIMOUS",
        schedule_name="Test Unanimous", schedule_type="DAILY", owner_user_id=creator, approval_required=True, schedule_status="DRAFT"
    )
    db_session.add(schedule)
    db_session.add(WorkflowScheduleAgentAssignment(schedule_id=sched_id, agent_id=uuid4(), assignment_role="PRIMARY", tenant_id=tenant_id))
    db_session.add(ScheduleApprovalLayerSelection(
        schedule_id=sched_id, department_id=depts[0].id, layer_order=1, 
        approver_user_ids=[str(userA), str(userB)], require_all_approvers=True, tenant_id=tenant_id
    ))
    db_session.commit()
    
    # Submit
    await workflow_service.submit_for_approval(sched_id, MockUser(creator), db_session)
    db_session.refresh(schedule)
    assert schedule.schedule_status == "PENDING_APPROVAL"
    
    # Check 2 pending rows generated for layer 1
    stmt = select(WorkflowScheduleApproval).where(WorkflowScheduleApproval.schedule_id == sched_id)
    approvals = db_session.execute(stmt).scalars().all()
    assert len(approvals) == 2
    appA = next(a for a in approvals if a.approver_user_id == userA)
    appB = next(a for a in approvals if a.approver_user_id == userB)
    assert appA.approval_status == "PENDING"
    assert appB.approval_status == "PENDING"
    
    # userA approves -> schedule stays PENDING_APPROVAL because userB has not approved
    await workflow_service.decide_approval(appA.id, "APPROVED", "Approved by A", MockUser(userA), db_session)
    db_session.refresh(schedule)
    assert schedule.schedule_status == "PENDING_APPROVAL"
    
    # userB approves -> all satisfied -> schedule becomes ACTIVE
    await workflow_service.decide_approval(appB.id, "APPROVED", "Approved by B", MockUser(userB), db_session)
    db_session.refresh(schedule)
    assert schedule.schedule_status == "ACTIVE"


@pytest.mark.asyncio
async def test_intra_layer_first_responder_supersedes_sibling(db_session, workflow_service):
    # Scenario: 1 Department with 2 approvers (userA and userB), require_all_approvers = False (ANY)
    creator = uuid4()
    userA, userB = uuid4(), uuid4()
    depts = await setup_mock_department_chain(db_session, [userA])
    
    tenant_id = depts[0].tenant_id
    sched_id = uuid4()
    
    for uid in [creator, userA, userB]:
        db_session.add(User(id=uid, name=str(uid), email=f"{uid}@test.com", hashed_password="hash"))
        
    schedule = Phase2WorkflowSchedule(
        id=sched_id, tenant_id=tenant_id, workflow_id=uuid4(), schedule_code="TEST_FIRST_RESP",
        schedule_name="Test First Responder", schedule_type="DAILY", owner_user_id=creator, approval_required=True, schedule_status="DRAFT"
    )
    db_session.add(schedule)
    db_session.add(WorkflowScheduleAgentAssignment(schedule_id=sched_id, agent_id=uuid4(), assignment_role="PRIMARY", tenant_id=tenant_id))
    db_session.add(ScheduleApprovalLayerSelection(
        schedule_id=sched_id, department_id=depts[0].id, layer_order=1, 
        approver_user_ids=[str(userA), str(userB)], require_all_approvers=False, tenant_id=tenant_id
    ))
    db_session.commit()
    
    # Submit
    await workflow_service.submit_for_approval(sched_id, MockUser(creator), db_session)
    
    stmt = select(WorkflowScheduleApproval).where(WorkflowScheduleApproval.schedule_id == sched_id)
    approvals = db_session.execute(stmt).scalars().all()
    assert len(approvals) == 2
    appA = next(a for a in approvals if a.approver_user_id == userA)
    appB = next(a for a in approvals if a.approver_user_id == userB)
    
    # userA approves -> userB's pending row must transition to SUPERSEDED and schedule becomes ACTIVE
    await workflow_service.decide_approval(appA.id, "APPROVED", "First responder approval", MockUser(userA), db_session)
    
    db_session.refresh(appB)
    db_session.refresh(schedule)
    assert appB.approval_status == "SUPERSEDED"
    assert "Layer satisfied" in appB.skip_reason
    assert schedule.schedule_status == "ACTIVE"


@pytest.mark.asyncio
async def test_rejection_fail_fast_supersedes_siblings(db_session, workflow_service):
    # Scenario: 2 approvers in Layer 1, userA REJECTS -> userB superseded and schedule becomes DRAFT
    creator = uuid4()
    userA, userB = uuid4(), uuid4()
    depts = await setup_mock_department_chain(db_session, [userA])
    
    tenant_id = depts[0].tenant_id
    sched_id = uuid4()
    
    for uid in [creator, userA, userB]:
        db_session.add(User(id=uid, name=str(uid), email=f"{uid}@test.com", hashed_password="hash"))
        
    schedule = Phase2WorkflowSchedule(
        id=sched_id, tenant_id=tenant_id, workflow_id=uuid4(), schedule_code="TEST_REJECT_FAST",
        schedule_name="Test Reject Fast", schedule_type="DAILY", owner_user_id=creator, approval_required=True, schedule_status="DRAFT"
    )
    db_session.add(schedule)
    db_session.add(WorkflowScheduleAgentAssignment(schedule_id=sched_id, agent_id=uuid4(), assignment_role="PRIMARY", tenant_id=tenant_id))
    db_session.add(ScheduleApprovalLayerSelection(
        schedule_id=sched_id, department_id=depts[0].id, layer_order=1, 
        approver_user_ids=[str(userA), str(userB)], require_all_approvers=True, tenant_id=tenant_id
    ))
    db_session.commit()
    
    await workflow_service.submit_for_approval(sched_id, MockUser(creator), db_session)
    
    stmt = select(WorkflowScheduleApproval).where(WorkflowScheduleApproval.schedule_id == sched_id)
    approvals = db_session.execute(stmt).scalars().all()
    appA = next(a for a in approvals if a.approver_user_id == userA)
    appB = next(a for a in approvals if a.approver_user_id == userB)
    
    # userA rejects
    await workflow_service.decide_approval(appA.id, "REJECTED", "Rejection note", MockUser(userA), db_session)
    
    db_session.refresh(appB)
    db_session.refresh(schedule)
    assert appB.approval_status == "SUPERSEDED"
    assert schedule.schedule_status == "DRAFT"


@pytest.mark.asyncio
async def test_reassign_approver(db_session, workflow_service):
    # Scenario: Admin reassigns a pending approval from userA to replacementUser
    creator = uuid4()
    userA, replacementUser = uuid4(), uuid4()
    adminUser = uuid4()
    depts = await setup_mock_department_chain(db_session, [userA])
    
    tenant_id = depts[0].tenant_id
    sched_id = uuid4()
    
    for uid in [creator, userA, replacementUser, adminUser]:
        db_session.add(User(id=uid, name=str(uid), email=f"{uid}@test.com", hashed_password="hash"))
        
    schedule = Phase2WorkflowSchedule(
        id=sched_id, tenant_id=tenant_id, workflow_id=uuid4(), schedule_code="TEST_REASSIGN",
        schedule_name="Test Reassign", schedule_type="DAILY", owner_user_id=creator, approval_required=True, schedule_status="DRAFT"
    )
    db_session.add(schedule)
    db_session.add(WorkflowScheduleAgentAssignment(schedule_id=sched_id, agent_id=uuid4(), assignment_role="PRIMARY", tenant_id=tenant_id))
    db_session.add(ScheduleApprovalLayerSelection(
        schedule_id=sched_id, department_id=depts[0].id, layer_order=1, 
        approver_user_ids=[str(userA)], require_all_approvers=True, tenant_id=tenant_id
    ))
    db_session.commit()
    
    await workflow_service.submit_for_approval(sched_id, MockUser(creator), db_session)
    
    # Admin reassigns
    app = await workflow_service.reassign_approver(
        sched_id, userA, replacementUser, MockUser(adminUser, is_superuser=True), db_session
    )
    
    assert app.approver_user_id == replacementUser
    assert app.approval_status == "PENDING"
    
    # replacementUser can now approve
    await workflow_service.decide_approval(app.id, "APPROVED", "Approved by replacement", MockUser(replacementUser), db_session)
    db_session.refresh(schedule)
    assert schedule.schedule_status == "ACTIVE"

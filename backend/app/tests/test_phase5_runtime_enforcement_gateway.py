from uuid import uuid4
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import pytest
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
import app.db.base
from app.modules.auth.models import User
from app.modules.agent.models import Agent
from app.modules.registry.models import Tool, Workflow
from app.modules.ai_model.models import AIModel
from app.modules.workflow_scheduler.models import Phase2WorkflowSchedule, WorkflowScheduleAgentAssignment
from app.modules.workflow_execution.models import WorkflowRun, WorkflowRunStep
from app.modules.agent_boundary.models import AgentRuntimeBoundary, ToolCapability
from app.modules.relationship.models import GenericRelationship
from app.modules.agent_runtime.service import AgentRuntimeService, BoundaryViolationError


def create_test_user(db: Session, email_prefix: str = "gateway") -> User:
    user = User(
        id=uuid4(),
        name=f"User {email_prefix}",
        full_name="Gateway Test User",
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


@pytest.mark.asyncio
async def test_runtime_enforcement_gateway_deny_blocks_execution(db: Session):
    user = create_test_user(db, "gw_deny")
    tenant_id = user.id
    service = AgentRuntimeService()
    now = datetime.now(timezone.utc)

    agent = Agent(
        id=uuid4(),
        tenant_id=tenant_id,
        agent_code=f"AGT-GW-D-{uuid4().hex[:6]}",
        agent_name="Gateway Deny Agent",
        agent_type="AUTONOMOUS",
        execution_mode="AUTONOMOUS",
        risk_level="LOW",
        status="ACTIVE",
    )
    wf = Workflow(
        id=uuid4(),
        tenant_id=tenant_id,
        workflow_code=f"WF-GW-{uuid4().hex[:6]}",
        workflow_name="Gateway Workflow",
        workflow_type="AUTOMATED",
        business_criticality="MEDIUM",
        status="ACTIVE",
    )
    db.add_all([agent, wf])
    db.flush()

    boundary = AgentRuntimeBoundary(
        id=uuid4(),
        tenant_id=tenant_id,
        agent_id=agent.id,
        max_autonomy_level="AUTONOMOUS",
        allowed_access_modes_json=["READ_ONLY"],
        is_active=False,  # KILL-SWITCH ACTIVE
    )
    schedule = Phase2WorkflowSchedule(
        id=uuid4(),
        tenant_id=tenant_id,
        workflow_id=wf.id,
        schedule_code=f"SCH-GW-{uuid4().hex[:6]}",
        schedule_name="Deny Schedule",
        schedule_type="MANUAL",
        owner_user_id=user.id,
        cron_expression="0 0 * * *",
        schedule_status="ACTIVE",
    )
    db.add_all([boundary, schedule])
    db.flush()

    assignment = WorkflowScheduleAgentAssignment(
        id=uuid4(),
        tenant_id=tenant_id,
        schedule_id=schedule.id,
        agent_id=agent.id,
        assignment_role="PRIMARY",
        execution_mode="AUTONOMOUS",
    )
    run = WorkflowRun(
        id=uuid4(),
        tenant_id=tenant_id,
        schedule_id=schedule.id,
        workflow_id=wf.id,
        run_code=f"RUN-GW-{uuid4().hex[:6]}",
        trigger_type="MANUAL",
        run_status="RUNNING",
        started_at=now,
    )
    db.add_all([assignment, run])
    db.commit()

    # Execution with kill switch triggered -> MUST raise BoundaryViolationError
    with pytest.raises(BoundaryViolationError) as exc_info:
        await service.invoke_agent(
            run_id=run.id,
            assignment=assignment,
            context={"facts": {"autonomy_level": "AUTONOMOUS"}},
            db=db,
        )

    assert "kill_switch" in str(exc_info.value).lower() or "kill-switch" in str(exc_info.value).lower() or "denied" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_runtime_enforcement_gateway_approval_interception(db: Session):
    user = create_test_user(db, "gw_appr")
    tenant_id = user.id
    service = AgentRuntimeService()
    now = datetime.now(timezone.utc)

    agent = Agent(
        id=uuid4(),
        tenant_id=tenant_id,
        agent_code=f"AGT-GW-A-{uuid4().hex[:6]}",
        agent_name="Gateway Approval Agent",
        agent_type="AUTONOMOUS",
        execution_mode="AUTONOMOUS",
        risk_level="LOW",
        status="ACTIVE",
    )
    tool = Tool(
        id=uuid4(),
        tenant_id=tenant_id,
        tool_code=f"TL-GW-A-{uuid4().hex[:6]}",
        tool_name="Approval Tool",
        tool_category="FINANCE",
        access_mode="WRITE",
        sensitivity_level="HIGH",
        allowed_operations_json=["disburse_funds"],
        status="ACTIVE",
    )
    wf = Workflow(
        id=uuid4(),
        tenant_id=tenant_id,
        workflow_code=f"WF-GW-A-{uuid4().hex[:6]}",
        workflow_name="Gateway Approval Workflow",
        workflow_type="AUTOMATED",
        business_criticality="MEDIUM",
        status="ACTIVE",
    )
    db.add_all([agent, tool, wf])
    db.flush()

    boundary = AgentRuntimeBoundary(
        id=uuid4(),
        tenant_id=tenant_id,
        agent_id=agent.id,
        max_autonomy_level="AUTONOMOUS",
        allowed_access_modes_json=["READ_ONLY", "EXECUTE", "WRITE"],
        is_active=True,
    )
    cap = ToolCapability(
        id=uuid4(),
        tenant_id=tenant_id,
        tool_id=tool.id,
        capability_name="disburse_funds",
        access_mode="WRITE",
        requires_approval=True,  # APPROVAL MANDATED
    )
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
    schedule = Phase2WorkflowSchedule(
        id=uuid4(),
        tenant_id=tenant_id,
        workflow_id=wf.id,
        schedule_code=f"SCH-GW-A-{uuid4().hex[:6]}",
        schedule_name="Approval Schedule",
        schedule_type="MANUAL",
        owner_user_id=user.id,
        cron_expression="0 0 * * *",
        schedule_status="ACTIVE",
    )
    db.add_all([boundary, cap, rel_tool, schedule])
    db.flush()

    assignment = WorkflowScheduleAgentAssignment(
        id=uuid4(),
        tenant_id=tenant_id,
        schedule_id=schedule.id,
        agent_id=agent.id,
        assignment_role="PRIMARY",
        execution_mode="AUTONOMOUS",
    )
    run = WorkflowRun(
        id=uuid4(),
        tenant_id=tenant_id,
        schedule_id=schedule.id,
        workflow_id=wf.id,
        run_code=f"RUN-GW-A-{uuid4().hex[:6]}",
        trigger_type="MANUAL",
        run_status="RUNNING",
        started_at=now,
    )
    db.add_all([assignment, run])
    db.commit()

    # Tool invocation requiring approval -> Intercepted as APPROVAL_REQUIRED without executing mock
    result = await service.invoke_agent(
        run_id=run.id,
        assignment=assignment,
        context={
            "tool_id": str(tool.id),
            "requested_tool": "disburse_funds",
            "operation": "disburse_funds",
        },
        db=db,
    )

    assert result["status"] == "APPROVAL_REQUIRED"
    assert result["execution_permitted"] is False
    assert len(result["approval_requirements"]) >= 1


@pytest.mark.asyncio
async def test_runtime_enforcement_gateway_allow_passes_through(db: Session):
    user = create_test_user(db, "gw_allow")
    tenant_id = user.id
    service = AgentRuntimeService()
    now = datetime.now(timezone.utc)

    agent = Agent(
        id=uuid4(),
        tenant_id=tenant_id,
        agent_code=f"AGT-GW-P-{uuid4().hex[:6]}",
        agent_name="Gateway Pass Agent",
        agent_type="AUTONOMOUS",
        execution_mode="AUTONOMOUS",
        risk_level="LOW",
        status="ACTIVE",
    )
    tool = Tool(
        id=uuid4(),
        tenant_id=tenant_id,
        tool_code=f"TL-GW-P-{uuid4().hex[:6]}",
        tool_name="Read Tool",
        tool_category="GENERAL",
        access_mode="READ",
        sensitivity_level="LOW",
        allowed_operations_json=["read_info"],
        status="ACTIVE",
    )
    wf = Workflow(
        id=uuid4(),
        tenant_id=tenant_id,
        workflow_code=f"WF-GW-P-{uuid4().hex[:6]}",
        workflow_name="Gateway Pass Workflow",
        workflow_type="AUTOMATED",
        business_criticality="MEDIUM",
        status="ACTIVE",
    )
    db.add_all([agent, tool, wf])
    db.flush()

    boundary = AgentRuntimeBoundary(
        id=uuid4(),
        tenant_id=tenant_id,
        agent_id=agent.id,
        max_autonomy_level="AUTONOMOUS",
        allowed_access_modes_json=["READ_ONLY", "EXECUTE"],
        is_active=True,
    )
    cap = ToolCapability(
        id=uuid4(),
        tenant_id=tenant_id,
        tool_id=tool.id,
        capability_name="read_info",
        access_mode="READ",
        requires_approval=False,
    )
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
    schedule = Phase2WorkflowSchedule(
        id=uuid4(),
        tenant_id=tenant_id,
        workflow_id=wf.id,
        schedule_code=f"SCH-GW-P-{uuid4().hex[:6]}",
        schedule_name="Pass Schedule",
        schedule_type="MANUAL",
        owner_user_id=user.id,
        cron_expression="0 0 * * *",
        schedule_status="ACTIVE",
    )
    db.add_all([boundary, cap, rel_tool, schedule])
    db.flush()

    assignment = WorkflowScheduleAgentAssignment(
        id=uuid4(),
        tenant_id=tenant_id,
        schedule_id=schedule.id,
        agent_id=agent.id,
        assignment_role="PRIMARY",
        execution_mode="AUTONOMOUS",
    )
    run = WorkflowRun(
        id=uuid4(),
        tenant_id=tenant_id,
        schedule_id=schedule.id,
        workflow_id=wf.id,
        run_code=f"RUN-GW-P-{uuid4().hex[:6]}",
        trigger_type="MANUAL",
        run_status="RUNNING",
        started_at=now,
    )
    db.add_all([assignment, run])
    db.commit()

    result = await service.invoke_agent(
        run_id=run.id,
        assignment=assignment,
        context={
            "tool_id": str(tool.id),
            "requested_tool": "read_info",
            "operation": "read_info",
        },
        db=db,
    )

    assert "findings" in result
    assert "risk_score" in result

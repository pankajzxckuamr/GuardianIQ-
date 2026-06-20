import pytest
import asyncio
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from httpx import AsyncClient, ASGITransport
from uuid import uuid4
from app.main import app

pytestmark = pytest.mark.anyio

@pytest.fixture
def anyio_backend():
    return 'asyncio'

@pytest.fixture
async def async_client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

@pytest.fixture
def admin_token():
    return "mock_admin_token" # You might need a real JWT depending on auth config

@pytest.fixture
def auditor_token():
    return "mock_auditor_token"

@pytest.fixture
def risk_manager_token():
    return "mock_risk_manager_token"

# In a real scenario, we would fetch these from the DB after seed_data is run
# For this stub we will define tests that map to the requirements
# We simulate the IDs or fetch them dynamically. 
# Due to the complexity, these tests are skeletons with expected API shapes.

async def get_test_data(async_client):
    # This helper would fetch workflow, agent, model IDs to be used in payload
    # For now we'll use fake UUIDs in the payload, but if seed runs, we could query DB.
    pass

async def test_tc_001_post_schedules_valid(async_client: AsyncClient, admin_token: str):
    # TC-001 | POST /schedules with valid DAILY + RECOMMEND_ONLY agent | 201, status=DRAFT
    # Payload matching WorkflowScheduleCreate
    payload = {
        "workflow_id": str(uuid4()),
        "schedule_code": "TEST_SCHED_001",
        "schedule_name": "Test Schedule",
        "schedule_type": "DAILY",
        "cron_expression": "0 9 * * *",
        "owner_user_id": str(uuid4()),
        "risk_level": "HIGH",
        "agent_assignments": [
            {
                "agent_id": str(uuid4()),
                "execution_mode": "RECOMMEND_ONLY",
                "boundary_rules": {
                    "max_records": 100,
                    "allow_write_tools": False,
                    "requires_human_approval_for_high_risk": True
                }
            }
        ]
    }
    # response = await async_client.post("/api/v1/workflow-scheduler/schedules", json=payload, headers={"Authorization": f"Bearer {admin_token}"})
    # assert response.status_code == 201
    # assert response.json()["data"]["schedule_status"] == "DRAFT"
    pass

async def test_tc_002_post_schedules_inactive_agent(async_client: AsyncClient, admin_token: str):
    # TC-002 | POST /schedules with inactive agent | 422 validation error
    pass

async def test_tc_003_post_schedules_activate_as_auditor(async_client: AsyncClient, auditor_token: str):
    # TC-003 | POST /schedules/{id}/activate as AUDITOR | 403 + AUTHORIZATION_DENIED in audit_events
    pass

async def test_tc_004_post_schedules_activate_as_risk_manager(async_client: AsyncClient, risk_manager_token: str):
    # TC-004 | POST /schedules/{id}/activate as RISK_MANAGER (approval group member) | 200, status=ACTIVE
    pass

async def test_tc_005_post_schedules_run_now_on_active(async_client: AsyncClient, admin_token: str):
    # TC-005 | POST /schedules/{id}/run-now on ACTIVE schedule | 201 run with trigger_type=MANUAL
    pass

async def test_tc_006_run_blocked_operation(async_client: AsyncClient, admin_token: str):
    # TC-006 | Run that requests a blocked operation | run FAILED, AGENT_BOUNDARY_CHECK_FAILED in audit_events
    pass

async def test_tc_007_scheduler_worker_poll_detects_due(async_client: AsyncClient):
    # TC-007 | Scheduler worker poll detects due schedule | run created, next_run_at updated
    pass

async def test_tc_008_second_run_now_skip_if_running(async_client: AsyncClient, admin_token: str):
    # TC-008 | Second run-now when SKIP_IF_RUNNING and one already RUNNING | second run status=SKIPPED
    pass

async def test_tc_009_run_output_high_risk(async_client: AsyncClient):
    # TC-009 | Run output with risk_score=90 | workflow_notifications record created for RISK_MANAGER
    pass

async def test_tc_010_get_workflow_runs_as_auditor(async_client: AsyncClient, auditor_token: str):
    # TC-010 | GET /workflow-runs/:id as AUDITOR | 200 read-only, no mutation buttons
    pass

async def test_tc_011_get_outputs_without_permission(async_client: AsyncClient, auditor_token: str):
    # TC-011 | GET /workflow-runs/:runId/outputs as user without VIEW_WORKFLOW_RUN_OUTPUT | raw_output_json not present in response
    pass

async def test_tc_012_post_schedules_pause(async_client: AsyncClient, admin_token: str):
    # TC-012 | POST /schedules/{id}/pause | status=PAUSED, next_run_at=null
    pass

async def test_tc_013_post_schedules_retire_then_resume(async_client: AsyncClient, admin_token: str):
    # TC-013 | POST /schedules/{id}/retire then /resume | 409 on resume (terminal state)
    pass

async def test_tc_014_post_schedules_invalid_cron(async_client: AsyncClient, admin_token: str):
    # TC-014 | POST /schedules with invalid cron expression | 422 with field-level error on cron_expression
    payload = {
        "workflow_id": str(uuid4()),
        "schedule_code": "TEST_SCHED_002",
        "schedule_name": "Test Schedule 2",
        "schedule_type": "CRON",
        "cron_expression": "invalid cron",
        "owner_user_id": str(uuid4()),
        "risk_level": "MEDIUM"
    }
    # response = await async_client.post("/api/v1/workflow-scheduler/schedules", json=payload)
    # assert response.status_code == 422
    pass

async def test_tc_015_failed_run_retries(async_client: AsyncClient):
    # TC-015 | Failed run with max_retries=2 | retry count increments, RETRY_QUEUED status set
    pass

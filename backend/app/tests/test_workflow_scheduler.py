import unittest
import sqlalchemy as sa
from datetime import datetime, timezone, timedelta
from uuid import uuid4, UUID
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import SessionLocal
from app.modules.auth.models import User, Role
from app.modules.registry.models import (
    GuardianUser,
    RegistryWorkflow,
    RegistryAIAgent,
    RegistryAIModel,
    RegistryTool,
    RegistryDepartment
)
from app.modules.workflow_scheduler.models import (
    ApprovalGroup,
    Phase2WorkflowSchedule,
    WorkflowScheduleAgentAssignment,
    WorkflowScheduleApproval,
    WorkflowScheduleHistory,
    ApprovalGroupMember
)
from app.modules.workflow_execution.models import WorkflowRun
from app.modules.workflow_notifications.models import WorkflowNotification
from app.modules.workflow_scheduler.validators import WorkflowScheduleValidationService, ValidationError
from app.modules.workflow_scheduler.service import WorkflowScheduleService, WorkflowScheduleStateError

class WorkflowSchedulerTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.db = SessionLocal()

        # Seed basic registry roles, departments, users
        from app.modules.registry.seed import seed_registry_data
        seed_registry_data(self.db)

        # Login as admin to get auth token
        login_response = self.client.post(
            "/api/auth/login",
            data={"username": "admin@guardianiq.com", "password": "Admin@1234!"}
        )
        self.assertEqual(login_response.status_code, 200)
        login_data = login_response.json()
        self.access_token = login_data["access_token"]
        self.headers = {"Authorization": f"Bearer {self.access_token}"}

        # Setup standard User roles
        admin_user = self.db.query(User).filter(User.email == "admin@guardianiq.com").first()
        gov_role = self.db.query(Role).filter(Role.role_code == "ADMIN").first()
        if admin_user and gov_role and gov_role not in admin_user.roles:
            admin_user.roles.append(gov_role)
            self.db.commit()

        # Get Admin Guardian User
        admin_guardian = self.db.query(GuardianUser).filter(GuardianUser.email == "admin@guardianiq.com").first()
        self.assertIsNotNone(admin_guardian)
        self.admin_uuid = admin_guardian.id

        # Get department
        dept = self.db.query(RegistryDepartment).filter(RegistryDepartment.department_code == "COMPLIANCE").first()
        self.assertIsNotNone(dept)
        self.department_id = dept.id

        # Setup workflow
        self.workflow = RegistryWorkflow(
            id=uuid4(),
            workflow_code="WF-SCHED-TEST",
            workflow_name="Scheduler Test Workflow",
            workflow_type="TEST",
            department_id=self.department_id,
            owner_user_id=self.admin_uuid,
            business_criticality="MEDIUM",
            status="ACTIVE"
        )
        self.db.add(self.workflow)

        # Setup AI Agent
        self.agent = RegistryAIAgent(
            id=uuid4(),
            agent_code="AG-SCHED-TEST",
            agent_name="Scheduler Test Agent",
            agent_type="TEST",
            owner_user_id=self.admin_uuid,
            department_id=self.department_id,
            execution_mode="LIMITED_EXECUTION",
            risk_level="MEDIUM",
            status="ACTIVE"
        )
        self.db.add(self.agent)

        # Setup AI Model
        self.model = RegistryAIModel(
            id=uuid4(),
            model_code="MOD-SCHED-TEST",
            model_name="Scheduler Test Model",
            model_type="TEST",
            purpose="Testing",
            owner_user_id=self.admin_uuid,
            department_id=self.department_id,
            risk_level="MEDIUM",
            status="ACTIVE"
        )
        self.db.add(self.model)

        # Setup Tools
        self.read_tool = RegistryTool(
            id=uuid4(),
            tool_code="TL-READ",
            tool_name="Read Tool",
            tool_category="TEST",
            access_mode="READ_ONLY",
            owner_user_id=self.admin_uuid,
            sensitivity_level="LOW",
            status="ACTIVE"
        )
        self.write_tool = RegistryTool(
            id=uuid4(),
            tool_code="TL-WRITE",
            tool_name="Write Tool",
            tool_category="TEST",
            access_mode="WRITE",
            owner_user_id=self.admin_uuid,
            sensitivity_level="MEDIUM",
            status="ACTIVE"
        )
        self.db.add(self.read_tool)
        self.db.add(self.write_tool)

        # Setup Approval Group
        self.group = ApprovalGroup(
            id=uuid4(),
            name="Sched Test Group",
            tenant_id=self.admin_uuid
        )
        self.db.add(self.group)
        self.db.flush()

        # Add member to approval group
        self.member = ApprovalGroupMember(
            approval_group_id=self.group.id,
            user_id=self.admin_uuid
        )
        self.db.add(self.member)

        self.db.commit()

        # Tracking for cleanup
        self.schedules_to_cleanup = []
        self.runs_to_cleanup = []
        self.notifications_to_cleanup = []

    def tearDown(self):
        try:
            # Delete notifications
            for nid in self.notifications_to_cleanup:
                self.db.query(WorkflowNotification).filter(WorkflowNotification.id == nid).delete()
            
            # Delete runs
            for rid in self.runs_to_cleanup:
                self.db.query(WorkflowRun).filter(WorkflowRun.id == rid).delete()

            # Delete assignments & schedule approvals & history
            for sid in self.schedules_to_cleanup:
                self.db.query(WorkflowScheduleAgentAssignment).filter(WorkflowScheduleAgentAssignment.schedule_id == sid).delete()
                self.db.query(WorkflowScheduleApproval).filter(WorkflowScheduleApproval.schedule_id == sid).delete()
                self.db.query(WorkflowScheduleHistory).filter(WorkflowScheduleHistory.schedule_id == sid).delete()
                self.db.query(Phase2WorkflowSchedule).filter(Phase2WorkflowSchedule.id == sid).delete()

            # Delete seed objects
            self.db.query(ApprovalGroupMember).filter(ApprovalGroupMember.approval_group_id == self.group.id).delete()
            self.db.query(ApprovalGroup).filter(ApprovalGroup.id == self.group.id).delete()
            self.db.query(RegistryTool).filter(RegistryTool.id.in_([self.read_tool.id, self.write_tool.id])).delete()
            self.db.query(RegistryAIModel).filter(RegistryAIModel.id == self.model.id).delete()
            self.db.query(RegistryAIAgent).filter(RegistryAIAgent.id == self.agent.id).delete()
            self.db.query(RegistryWorkflow).filter(RegistryWorkflow.id == self.workflow.id).delete()

            self.db.commit()
        except Exception as e:
            self.db.rollback()
            print(f"Cleanup error: {e}")
        self.db.close()

    def test_validation_errors(self):
        # 1. Test inactive workflow
        self.workflow.status = "DRAFT"
        self.db.commit()
        
        payload = {
            "workflow_id": str(self.workflow.id),
            "schedule_code": "SCH-TEST-001",
            "schedule_name": "Test Schedule",
            "schedule_type": "CRON",
            "cron_expression": "0 0 * * *",
            "timezone": "Asia/Kolkata",
            "owner_user_id": str(self.admin_uuid),
            "risk_level": "LOW",
            "agent_assignments": [
                {
                    "agent_id": str(self.agent.id),
                    "model_id": str(self.model.id),
                    "execution_mode": "READ_ONLY",
                    "allowed_tools": ["TL-READ"],
                    "boundary_rules": {"max_records": 10, "allow_write_tools": False, "requires_human_approval_for_high_risk": False}
                }
            ]
        }
        
        import asyncio
        errors = asyncio.run(WorkflowScheduleValidationService.validate_create(payload, self.db))
        self.assertTrue(any("is not ACTIVE" in e.message for e in errors))

        # Revert status
        self.workflow.status = "ACTIVE"
        self.db.commit()

        # 2. Test invalid cron expression
        payload["cron_expression"] = "invalid_cron"
        errors = asyncio.run(WorkflowScheduleValidationService.validate_create(payload, self.db))
        self.assertTrue(any("Invalid cron expression" in e.message for e in errors))
        
        payload["cron_expression"] = "0 0 * * *"

        # 3. Test invalid timezone
        payload["timezone"] = "Invalid/Timezone"
        errors = asyncio.run(WorkflowScheduleValidationService.validate_create(payload, self.db))
        self.assertTrue(any("Invalid timezone" in e.message for e in errors))
        
        payload["timezone"] = "Asia/Kolkata"

        # 4. Test exceeding agent registered max execution mode
        # Agent execution mode is LIMITED_EXECUTION (rank 4). Let's change assignment mode to FULLY_BLOCKED (rank 5)
        payload["agent_assignments"][0]["execution_mode"] = "FULLY_BLOCKED"
        errors = asyncio.run(WorkflowScheduleValidationService.validate_create(payload, self.db))
        self.assertTrue(any("exceeds agent's max registered mode" in e.message for e in errors))

    def test_validation_auto_approval(self):
        # 1. Test auto-set approval_required=True for CRITICAL risk
        payload = {
            "workflow_id": str(self.workflow.id),
            "schedule_code": "SCH-TEST-AUTO",
            "schedule_name": "Auto Approval Schedule",
            "schedule_type": "DAILY",
            "owner_user_id": str(self.admin_uuid),
            "risk_level": "CRITICAL",
            "approval_required": False,
            "agent_assignments": [
                {
                    "agent_id": str(self.agent.id),
                    "model_id": str(self.model.id),
                    "execution_mode": "READ_ONLY",
                    "allowed_tools": ["TL-READ"],
                    "boundary_rules": {"max_records": 10, "allow_write_tools": False, "requires_human_approval_for_high_risk": False}
                }
            ]
        }
        
        import asyncio
        errors = asyncio.run(WorkflowScheduleValidationService.validate_create(payload, self.db))
        # approval_required should have been set to True, and since approval_group_id is None, it should trigger ValidationError
        self.assertTrue(payload["approval_required"])
        self.assertTrue(any("approval_group_id is required" in e.message for e in errors))

        # 2. Test auto-set approval_required=True for WRITE tool
        payload["risk_level"] = "LOW"
        payload["agent_assignments"][0]["allowed_tools"] = ["TL-WRITE"]
        errors = asyncio.run(WorkflowScheduleValidationService.validate_create(payload, self.db))
        self.assertTrue(payload["approval_required"])
        self.assertTrue(any("approval_group_id is required" in e.message for e in errors))

        # 3. Test auto-set approval_required=True for LIMITED_EXECUTION mode
        payload["agent_assignments"][0]["allowed_tools"] = ["TL-READ"]
        payload["agent_assignments"][0]["execution_mode"] = "LIMITED_EXECUTION"
        errors = asyncio.run(WorkflowScheduleValidationService.validate_create(payload, self.db))
        self.assertTrue(payload["approval_required"])
        self.assertTrue(any("approval_group_id is required" in e.message for e in errors))

    def test_schedule_lifecycle_endpoints(self):
        # 1. Create a schedule (requires approval since risk is LOW, but tool is TL-WRITE)
        payload = {
            "workflow_id": str(self.workflow.id),
            "schedule_code": "SCH-API-001",
            "schedule_name": "API Test Schedule",
            "schedule_type": "CRON",
            "cron_expression": "*/5 * * * *",
            "timezone": "Asia/Kolkata",
            "owner_user_id": str(self.admin_uuid),
            "approval_group_id": str(self.group.id),
            "risk_level": "LOW",
            "agent_assignments": [
                {
                    "agent_id": str(self.agent.id),
                    "model_id": str(self.model.id),
                    "execution_mode": "RECOMMEND_ONLY",
                    "allowed_tools": ["TL-WRITE"],
                    "boundary_rules": {"max_records": 10, "allow_write_tools": True, "requires_human_approval_for_high_risk": False}
                }
            ]
        }
        
        response = self.client.post("/api/v1/workflow-scheduler/schedules", json=payload, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        res_env = response.json()
        self.assertTrue(res_env["success"], f"Error: {res_env.get('error')}")
        self.assertIsNotNone(res_env["request_id"])
        
        sched_data = res_env["data"]
        self.assertEqual(sched_data["schedule_status"], "DRAFT")
        self.assertTrue(sched_data["approval_required"])
        schedule_id = UUID(sched_data["id"])
        self.schedules_to_cleanup.append(schedule_id)

        # 2. Get Detail
        detail_response = self.client.get(f"/api/v1/workflow-scheduler/schedules/{schedule_id}", headers=self.headers)
        self.assertEqual(detail_response.status_code, 200)
        detail_env = detail_response.json()
        self.assertTrue(detail_env["success"])
        self.assertIn("schedule", detail_env["data"])
        self.assertIn("latest_approval", detail_env["data"])
        self.assertIn("last_runs_summary", detail_env["data"])

        # 2.5 Update Schedule (transitions DRAFT or PAUSED)
        update_payload = {
            "schedule_name": "API Test Schedule Updated"
        }
        update_response = self.client.put(f"/api/v1/workflow-scheduler/schedules/{schedule_id}", json=update_payload, headers=self.headers)
        self.assertEqual(update_response.status_code, 200)
        update_env = update_response.json()
        self.assertTrue(update_env["success"], f"Update failed: {update_env.get('error')}")
        self.assertEqual(update_env["data"]["schedule_name"], "API Test Schedule Updated")

        # 3. Submit for approval (transitions DRAFT -> PENDING_APPROVAL)
        submit_response = self.client.post(f"/api/v1/workflow-scheduler/schedules/{schedule_id}/submit", headers=self.headers)
        self.assertEqual(submit_response.status_code, 200)
        submit_env = submit_response.json()
        self.assertTrue(submit_env["success"])
        self.assertEqual(submit_env["data"]["schedule_status"], "PENDING_APPROVAL")

        # Verify notification created
        notifs = self.db.query(WorkflowNotification).filter(WorkflowNotification.entity_id == schedule_id).all()
        self.assertTrue(len(notifs) > 0)
        for n in notifs:
            self.notifications_to_cleanup.append(n.id)

        # Get latest approval record
        app_stmt = sa.select(WorkflowScheduleApproval).where(WorkflowScheduleApproval.schedule_id == schedule_id)
        app_res = self.db.execute(app_stmt)
        approval_rec = app_res.scalar()
        self.assertIsNotNone(approval_rec)
        self.assertEqual(approval_rec.approval_status, "PENDING")

        # 4. Try to activate directly when in PENDING_APPROVAL without approval decision (should raise state error or abac deny if not approved)
        # Note: activate_schedule directly transitions PENDING_APPROVAL -> ACTIVE, which is allowed in transition validation, but requires approval group permission
        # Let's test decide_approval REJECTED
        decide_payload = {
            "decision": "REJECTED",
            "reason": "Wrong cron expression"
        }
        decide_response = self.client.post(
            f"/api/v1/schedule-approvals/{approval_rec.id}/decide",
            json=decide_payload,
            headers=self.headers
        )
        self.assertEqual(decide_response.status_code, 200)
        decide_env = decide_response.json()
        self.assertEqual(decide_env["data"]["schedule_status"], "DRAFT") # transitions back to DRAFT

        # Submit again for approval
        self.client.post(f"/api/v1/workflow-scheduler/schedules/{schedule_id}/submit", headers=self.headers)
        
        # Get new approval record
        app_res2 = self.db.execute(sa.select(WorkflowScheduleApproval).where(
            WorkflowScheduleApproval.schedule_id == schedule_id,
            WorkflowScheduleApproval.approval_status == "PENDING"
        ))
        approval_rec2 = app_res2.scalar()

        # Decide approval APPROVED (should transition to ACTIVE and compute next_run_at)
        decide_payload["decision"] = "APPROVED"
        decide_payload["reason"] = "Looks good"
        decide_response2 = self.client.post(
            f"/api/v1/schedule-approvals/{approval_rec2.id}/decide",
            json=decide_payload,
            headers=self.headers
        )
        self.assertEqual(decide_response2.status_code, 200)
        decide_env2 = decide_response2.json()
        self.assertEqual(decide_env2["data"]["schedule_status"], "ACTIVE")
        self.assertIsNotNone(decide_env2["data"]["next_run_at"])

        # 5. Pause Schedule (ACTIVE -> PAUSED)
        pause_response = self.client.post(f"/api/v1/workflow-scheduler/schedules/{schedule_id}/pause", headers=self.headers)
        self.assertEqual(pause_response.status_code, 200)
        pause_env = pause_response.json()
        self.assertEqual(pause_env["data"]["schedule_status"], "PAUSED")
        self.assertIsNone(pause_env["data"]["next_run_at"])

        # 6. Resume Schedule (PAUSED -> ACTIVE)
        resume_response = self.client.post(f"/api/v1/workflow-scheduler/schedules/{schedule_id}/resume", headers=self.headers)
        self.assertEqual(resume_response.status_code, 200)
        resume_env = resume_response.json()
        self.assertEqual(resume_env["data"]["schedule_status"], "ACTIVE")
        self.assertIsNotNone(resume_env["data"]["next_run_at"])

        # 7. Run Now (trigger manual run)
        run_response = self.client.post(f"/api/v1/workflow-scheduler/schedules/{schedule_id}/run-now", headers=self.headers)
        self.assertEqual(run_response.status_code, 200)
        run_env = run_response.json()
        self.assertTrue(run_env["success"])
        self.assertEqual(run_env["data"]["run_status"], "QUEUED")
        self.assertEqual(run_env["data"]["trigger_type"], "MANUAL")
        run_id = UUID(run_env["data"]["id"])
        self.runs_to_cleanup.append(run_id)

        # 8. Retire Schedule (ACTIVE -> RETIRED)
        retire_response = self.client.post(f"/api/v1/workflow-scheduler/schedules/{schedule_id}/retire", headers=self.headers)
        self.assertEqual(retire_response.status_code, 200)
        retire_env = retire_response.json()
        self.assertEqual(retire_env["data"]["schedule_status"], "RETIRED")
        self.assertIsNone(retire_env["data"]["next_run_at"])

        # 9. Try invalid transition from RETIRED (should raise error)
        pause_response_ret = self.client.post(f"/api/v1/workflow-scheduler/schedules/{schedule_id}/pause", headers=self.headers)
        # should fail as RETIRED is terminal
        self.assertFalse(pause_response_ret.json()["success"])

        # 10. Fetch history and approvals
        hist_res = self.client.get(f"/api/v1/workflow-scheduler/schedules/{schedule_id}/history", headers=self.headers)
        self.assertEqual(hist_res.status_code, 200)
        self.assertTrue(len(hist_res.json()["data"]) > 0)

        app_res = self.client.get(f"/api/v1/workflow-scheduler/schedules/{schedule_id}/approvals", headers=self.headers)
        self.assertEqual(app_res.status_code, 200)
        self.assertTrue(len(app_res.json()["data"]) > 0)

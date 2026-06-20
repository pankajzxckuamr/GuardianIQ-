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
from app.modules.audit.models import AuditEvent
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
        gov_admin_role = self.db.query(Role).filter(Role.role_code == "GOVERNANCE_ADMIN").first()
        if admin_user:
            if gov_role and gov_role not in admin_user.roles:
                admin_user.roles.append(gov_role)
            if gov_admin_role and gov_admin_role not in admin_user.roles:
                admin_user.roles.append(gov_admin_role)
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
            workflow_code="WF-SCHED-TEST-2",
            workflow_name="Scheduler Test Workflow 2",
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
            agent_code="AG-SCHED-TEST-2",
            agent_name="Scheduler Test Agent 2",
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
            model_code="MOD-SCHED-TEST-2",
            model_name="Scheduler Test Model 2",
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
            tool_code="TL-READ-2",
            tool_name="Read Tool 2",
            tool_category="TEST",
            access_mode="READ_ONLY",
            owner_user_id=self.admin_uuid,
            sensitivity_level="LOW",
            status="ACTIVE"
        )
        self.write_tool = RegistryTool(
            id=uuid4(),
            tool_code="TL-WRITE-2",
            tool_name="Write Tool 2",
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
                    "allowed_tools": ["TL-WRITE-2"],
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

    def test_api_integration_scenarios(self):
        valid_payload = {
            "workflow_id": str(self.workflow.id),
            "schedule_code": "VERIFY_DAILY_002",
            "schedule_name": "Verify Daily Schedule",
            "schedule_type": "DAILY",
            "timezone": "Asia/Kolkata",
            "owner_user_id": str(self.admin_uuid),
            "risk_level": "LOW",
            "approval_required": False,
            "agent_assignments": [{
                "agent_id": str(self.agent.id),
                "model_id": str(self.model.id),
                "execution_mode": "RECOMMEND_ONLY",
                "allowed_tools": ["TL-READ-2"],
                "boundary_rules": {"max_records": 100, "allow_write_tools": False, "requires_human_approval_for_high_risk": True}
            }]
        }

        # Test 1: Create valid schedule
        r1 = self.client.post("/api/v1/workflow-scheduler/schedules", json=valid_payload, headers=self.headers)
        self.assertEqual(r1.status_code, 200)
        self.assertTrue(r1.json().get("success"), f"Create schedule failed: {r1.json().get('error')}")
        r1_data = r1.json()["data"]
        from uuid import UUID
        self.schedules_to_cleanup.append(UUID(r1_data["id"]))
        self.assertIn(r1_data["schedule_status"], ["DRAFT", "ACTIVE"])
        self.assertEqual(r1_data["schedule_code"], "VERIFY_DAILY_002")
        schedule_id = r1_data["id"]
        self.schedules_to_cleanup.append(UUID(schedule_id))
        print("PASS: Create schedule returns 200 (Success envelope)")

        # Test 2: Create with inactive agent
        self.agent.status = "INACTIVE"
        self.db.commit()
        r2 = self.client.post("/api/v1/workflow-scheduler/schedules", json=valid_payload, headers=self.headers)
        if r2.status_code == 422:
            self.assertIn("agent", r2.text.lower())
        else:
            self.assertEqual(r2.status_code, 200)
            self.assertFalse(r2.json().get("success"))
            self.assertIn("agent", (r2.json().get("error") or "").lower())
        print("PASS: Inactive agent rejected")

        self.agent.status = "ACTIVE"
        self.db.commit()

        # Test 3: HIGH risk + no approval_group_id
        high_risk_payload = valid_payload.copy()
        high_risk_payload["risk_level"] = "HIGH"
        high_risk_payload["approval_required"] = True
        r3 = self.client.post("/api/v1/workflow-scheduler/schedules", json=high_risk_payload, headers=self.headers)
        if r3.status_code == 422:
            self.assertIn("approval_group", r3.text.lower())
        else:
            self.assertEqual(r3.status_code, 200)
            self.assertFalse(r3.json().get("success"))
            self.assertIn("approval_group", (r3.json().get("error") or "").lower())
        print("PASS: HIGH risk without approval_group_id rejected")

        # Test 4: CRON type without cron_expression
        cron_payload = valid_payload.copy()
        cron_payload["schedule_type"] = "CRON"
        r4 = self.client.post("/api/v1/workflow-scheduler/schedules", json=cron_payload, headers=self.headers)
        if r4.status_code == 422:
            pass 
        else:
            self.assertEqual(r4.status_code, 200)
            self.assertFalse(r4.json().get("success"))
        print("PASS: CRON without cron_expression rejected")

        # Test 5: Activate as AUDITOR → 403
        auditor_user = self.db.query(User).filter(User.email == "auditor@guardianiq.com").first()
        if auditor_user:
            auditor_login = self.client.post("/api/auth/login", data={"username": "auditor@guardianiq.com", "password": "Auditor@1234!"})
            if auditor_login.status_code == 200:
                auditor_token = auditor_login.json()["access_token"]
                auditor_headers = {"Authorization": f"Bearer {auditor_token}"}
                r5 = self.client.post(f"/api/v1/workflow-scheduler/schedules/{schedule_id}/activate", headers=auditor_headers)
                self.assertEqual(r5.status_code, 403)
                
                # Check AUTHORIZATION_DENIED event logged
                audit_event = self.db.query(AuditEvent).filter(
                    AuditEvent.entity_id == schedule_id,
                    AuditEvent.event_code == "AUTHORIZATION_DENIED"
                ).first()
                self.assertIsNotNone(audit_event)
                
                print("PASS: Auditor cannot activate, 403 returned and AUTHORIZATION_DENIED logged")

        # Test 6: Submit → PENDING_APPROVAL
        hr_payload = high_risk_payload.copy()
        hr_payload["schedule_code"] = "VERIFY_HIGH_001"
        hr_payload["approval_group_id"] = str(self.group.id)
        r6_1 = self.client.post("/api/v1/workflow-scheduler/schedules", json=hr_payload, headers=self.headers)
        self.assertTrue(r6_1.json().get("success"))
        schedule_id_hr = r6_1.json()["data"]["id"]
        self.schedules_to_cleanup.append(UUID(schedule_id_hr))
        
        r6_2 = self.client.post(f"/api/v1/workflow-scheduler/schedules/{schedule_id_hr}/submit", headers=self.headers)
        self.assertEqual(r6_2.json()["data"]["schedule_status"], "PENDING_APPROVAL")
        app_count = self.db.query(WorkflowScheduleApproval).filter(
            WorkflowScheduleApproval.schedule_id == schedule_id_hr,
            WorkflowScheduleApproval.approval_status == "PENDING"
        ).count()
        self.assertEqual(app_count, 1)
        print("PASS: Submit transitions to PENDING_APPROVAL")

        # Test 7: Retire → terminal
        # First activate it so it can be retired (DRAFT -> ACTIVE)
        r7_activate = self.client.post(f"/api/v1/workflow-scheduler/schedules/{schedule_id}/activate", headers=self.headers)
        self.assertTrue(r7_activate.json().get("success"), f"Activation failed: {r7_activate.json().get('error')}")
        
        # Now retire it (ACTIVE -> RETIRED)
        r7 = self.client.post(f"/api/v1/workflow-scheduler/schedules/{schedule_id}/retire", headers=self.headers)
        self.assertTrue(r7.json().get("success"), f"Retire failed: {r7.json().get('error')}")
        self.assertEqual(r7.json()["data"]["schedule_status"], "RETIRED")
        print("PASS: Schedule retired successfully")
        r7_resume = self.client.post(f"/api/v1/workflow-scheduler/schedules/{schedule_id}/resume", headers=self.headers)
        if r7_resume.status_code == 409:
            pass
        else:
            self.assertEqual(r7_resume.status_code, 200)
            self.assertFalse(r7_resume.json().get("success"))
        print("PASS: RETIRED is terminal")

        # Test 8: Pagination works
        r8 = self.client.get("/api/v1/workflow-scheduler/schedules?page=1&per_page=5&status=DRAFT", headers=self.headers)
        self.assertEqual(r8.status_code, 200)
        self.assertIsInstance(r8.json()["data"]["items"], list)
        self.assertTrue(len(r8.json()["data"]["items"]) <= 5)
        self.assertIsInstance(r8.json()["data"]["total"], int)
        self.assertEqual(r8.json()["data"]["page"], 1)
        print("PASS: Pagination fields present in list response")

        # Test 9: WORKFLOW_SCHEDULE_CREATED audit event exists
        create_audit_event = self.db.query(AuditEvent).filter(
            AuditEvent.entity_id == UUID(schedule_id),
            AuditEvent.event_code == "WORKFLOW_SCHEDULE_CREATED"
        ).first()
        self.assertIsNotNone(create_audit_event)
        print("PASS: WORKFLOW_SCHEDULE_CREATED audit event logged")

        # Test 10: workflow_schedule_history written on update
        app_record = self.db.query(WorkflowScheduleApproval).filter(WorkflowScheduleApproval.schedule_id == schedule_id_hr).first()
        r10_reject = self.client.post(f"/api/v1/workflow-scheduler/approvals/{app_record.id}/decide", json={"decision": "REJECTED", "reason": "Test reject"}, headers=self.headers)
        self.assertTrue(r10_reject.json().get("success"))

        r10_hr = self.client.put(f"/api/v1/workflow-scheduler/schedules/{schedule_id_hr}", json={"schedule_name": "Updated Name HR"}, headers=self.headers)
        self.assertEqual(r10_hr.status_code, 200)
        self.assertTrue(r10_hr.json().get("success"))
        hist_count = self.db.query(WorkflowScheduleHistory).filter(WorkflowScheduleHistory.schedule_id == schedule_id_hr).count()
        self.assertGreater(hist_count, 0)
        print("PASS: Update writes workflow_schedule_history row")

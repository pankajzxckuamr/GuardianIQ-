import unittest
import asyncio
import os
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
    ApprovalGroupMember
)
from app.modules.workflow_execution.models import WorkflowRun, WorkflowRunStep, WorkflowRunOutput, WorkflowRunFailure
from app.modules.workflow_execution.service import WorkflowRunService, WorkflowRunStateError
from app.modules.agent_runtime.boundary_checker import BoundaryChecker
from app.modules.agent_runtime.service import AgentRuntimeService
from app.modules.audit.models import AuditEvent

class WorkflowRunTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.db = SessionLocal()

        # Clean up existing test records to prevent UniqueViolation from previous failed runs
        try:
            aud_guardian = self.db.query(GuardianUser).filter(GuardianUser.email == "auditor@guardianiq.com").first()
            if aud_guardian:
                from app.modules.authorization.models import WorkflowAuthorizationDecision
                self.db.query(WorkflowAuthorizationDecision).filter(
                    sa.or_(
                        WorkflowAuthorizationDecision.subject_user_id == aud_guardian.id,
                        WorkflowAuthorizationDecision.tenant_id == aud_guardian.id
                    )
                ).delete()
                self.db.query(GuardianUser).filter(GuardianUser.id == aud_guardian.id).delete()

            aud_user = self.db.query(User).filter(User.email == "auditor@guardianiq.com").first()
            if aud_user:
                from app.modules.auth.models import user_roles
                self.db.execute(user_roles.delete().where(user_roles.c.user_id == aud_user.id))
                self.db.query(User).filter(User.id == aud_user.id).delete()

            old_schedules = self.db.query(Phase2WorkflowSchedule).filter(Phase2WorkflowSchedule.schedule_code == "SCH-RUN-TEST").all()
            for old_sched in old_schedules:
                runs = self.db.query(WorkflowRun).filter(WorkflowRun.schedule_id == old_sched.id).all()
                for r in runs:
                    self.db.query(WorkflowRunFailure).filter(WorkflowRunFailure.run_id == r.id).delete()
                    self.db.query(WorkflowRunOutput).filter(WorkflowRunOutput.run_id == r.id).delete()
                    self.db.query(WorkflowRunStep).filter(WorkflowRunStep.run_id == r.id).delete()
                    self.db.query(WorkflowRun).filter(WorkflowRun.id == r.id).delete()
                self.db.query(WorkflowScheduleAgentAssignment).filter(WorkflowScheduleAgentAssignment.schedule_id == old_sched.id).delete()
                self.db.query(Phase2WorkflowSchedule).filter(Phase2WorkflowSchedule.id == old_sched.id).delete()

            old_group = self.db.query(ApprovalGroup).filter(ApprovalGroup.name == "Run Test Group").first()
            if old_group:
                self.db.query(ApprovalGroupMember).filter(ApprovalGroupMember.approval_group_id == old_group.id).delete()
                self.db.query(ApprovalGroup).filter(ApprovalGroup.id == old_group.id).delete()

            self.db.query(RegistryTool).filter(RegistryTool.tool_code == "TL-WRITE").delete()
            self.db.query(RegistryAIModel).filter(RegistryAIModel.model_code == "MOD-RUN-TEST").delete()
            self.db.query(RegistryAIAgent).filter(RegistryAIAgent.agent_code == "AG-RUN-TEST").delete()
            self.db.query(RegistryWorkflow).filter(RegistryWorkflow.workflow_code == "WF-RUN-TEST").delete()
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            print(f"SetUp initial cleanup error: {e}")

        # Seed registry data
        from app.modules.registry.seed import seed_registry_data
        seed_registry_data(self.db)

        # Login as admin
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

        # Setup active entities for test schedule
        self.workflow = RegistryWorkflow(
            id=uuid4(),
            workflow_code="WF-RUN-TEST",
            workflow_name="Execution Run Test Workflow",
            workflow_type="TEST",
            department_id=self.department_id,
            owner_user_id=self.admin_uuid,
            business_criticality="MEDIUM",
            status="ACTIVE"
        )
        self.db.add(self.workflow)

        self.agent = RegistryAIAgent(
            id=uuid4(),
            agent_code="AG-RUN-TEST",
            agent_name="Execution Run Test Agent",
            agent_type="TEST",
            owner_user_id=self.admin_uuid,
            department_id=self.department_id,
            execution_mode="LIMITED_EXECUTION",
            risk_level="MEDIUM",
            status="ACTIVE"
        )
        self.db.add(self.agent)

        self.model = RegistryAIModel(
            id=uuid4(),
            model_code="MOD-RUN-TEST",
            model_name="Execution Run Test Model",
            model_type="TEST",
            purpose="Testing",
            owner_user_id=self.admin_uuid,
            department_id=self.department_id,
            risk_level="MEDIUM",
            status="ACTIVE"
        )
        self.db.add(self.model)

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
        self.db.add(self.write_tool)

        self.group = ApprovalGroup(
            id=uuid4(),
            name="Run Test Group",
            tenant_id=self.admin_uuid
        )
        self.db.add(self.group)
        self.db.flush()

        self.member = ApprovalGroupMember(
            approval_group_id=self.group.id,
            user_id=self.admin_uuid
        )
        self.db.add(self.member)

        # Create standard test schedule (ACTIVE)
        self.schedule = Phase2WorkflowSchedule(
            id=uuid4(),
            tenant_id=self.admin_uuid,
            workflow_id=self.workflow.id,
            schedule_code="SCH-RUN-TEST",
            schedule_name="Execution Run Test Schedule",
            schedule_type="CRON",
            cron_expression="*/5 * * * *",
            timezone="Asia/Kolkata",
            start_at=datetime.now(timezone.utc) - timedelta(hours=1),
            concurrency_policy="SKIP_IF_RUNNING",
            max_runtime_seconds=600,
            retry_policy_json={"max_retries": 2, "retry_delay_seconds": 60},
            owner_user_id=self.admin_uuid,
            owner_department_id=self.department_id,
            approval_required=False,
            risk_level="LOW",
            schedule_status="ACTIVE"
        )
        self.db.add(self.schedule)
        self.db.flush()

        # Create Agent Assignment
        self.assignment = WorkflowScheduleAgentAssignment(
            id=uuid4(),
            tenant_id=self.admin_uuid,
            schedule_id=self.schedule.id,
            agent_id=self.agent.id,
            model_id=self.model.id,
            assignment_role="PRIMARY",
            execution_mode="RECOMMEND_ONLY",
            confidence_threshold=85.0,
            allowed_tools_json=["TL-WRITE"],
            allowed_data_sources_json=[],
            blocked_operations_json=[],
            boundary_rules_json={"max_records": 10, "allow_write_tools": True, "requires_human_approval_for_high_risk": False},
            status="ACTIVE"
        )
        self.db.add(self.assignment)
        self.db.commit()

        self.runs_to_cleanup = []

    def tearDown(self):
        try:
            # Delete steps, outputs, failures and runs for this schedule
            runs = self.db.query(WorkflowRun).filter(WorkflowRun.schedule_id == self.schedule.id).all()
            for r in runs:
                self.db.query(WorkflowRunFailure).filter(WorkflowRunFailure.run_id == r.id).delete()
                self.db.query(WorkflowRunOutput).filter(WorkflowRunOutput.run_id == r.id).delete()
                self.db.query(WorkflowRunStep).filter(WorkflowRunStep.run_id == r.id).delete()
                self.db.query(WorkflowRun).filter(WorkflowRun.id == r.id).delete()

            for rid in self.runs_to_cleanup:
                self.db.query(WorkflowRunFailure).filter(WorkflowRunFailure.run_id == rid).delete()
                self.db.query(WorkflowRunOutput).filter(WorkflowRunOutput.run_id == rid).delete()
                self.db.query(WorkflowRunStep).filter(WorkflowRunStep.run_id == rid).delete()
                self.db.query(WorkflowRun).filter(WorkflowRun.id == rid).delete()

            # Delete schedule related structures
            self.db.query(WorkflowScheduleAgentAssignment).filter(WorkflowScheduleAgentAssignment.schedule_id == self.schedule.id).delete()
            self.db.query(Phase2WorkflowSchedule).filter(Phase2WorkflowSchedule.id == self.schedule.id).delete()
            self.db.query(ApprovalGroupMember).filter(ApprovalGroupMember.approval_group_id == self.group.id).delete()
            self.db.query(ApprovalGroup).filter(ApprovalGroup.id == self.group.id).delete()
            self.db.query(RegistryTool).filter(RegistryTool.id == self.write_tool.id).delete()
            self.db.query(RegistryAIModel).filter(RegistryAIModel.id == self.model.id).delete()
            self.db.query(RegistryAIAgent).filter(RegistryAIAgent.id == self.agent.id).delete()
            self.db.query(RegistryWorkflow).filter(RegistryWorkflow.id == self.workflow.id).delete()

            # Clean up auditor user and guardian user
            aud_guardian = self.db.query(GuardianUser).filter(GuardianUser.email == "auditor@guardianiq.com").first()
            if aud_guardian:
                from app.modules.authorization.models import WorkflowAuthorizationDecision
                self.db.query(WorkflowAuthorizationDecision).filter(
                    sa.or_(
                        WorkflowAuthorizationDecision.subject_user_id == aud_guardian.id,
                        WorkflowAuthorizationDecision.tenant_id == aud_guardian.id
                    )
                ).delete()
                self.db.query(GuardianUser).filter(GuardianUser.id == aud_guardian.id).delete()

            aud_user = self.db.query(User).filter(User.email == "auditor@guardianiq.com").first()
            if aud_user:
                from app.modules.auth.models import user_roles
                self.db.execute(user_roles.delete().where(user_roles.c.user_id == aud_user.id))
                self.db.query(User).filter(User.id == aud_user.id).delete()

            self.db.commit()
        except Exception as e:
            self.db.rollback()
            print(f"TearDown cleanup error: {e}")
        self.db.close()

    def test_run_transitions_and_concurrency(self):
        # 1. Create a run when no other runs exist
        run1 = asyncio.run(WorkflowRunService.create_run(self.db, self.schedule.id, "MANUAL", self.admin_uuid))
        self.assertIsNotNone(run1)
        self.assertEqual(run1.run_status, "QUEUED")
        self.runs_to_cleanup.append(run1.id)

        # 2. Concurrency Conflict path: create another run while run1 is active and policy is SKIP_IF_RUNNING
        run2 = asyncio.run(WorkflowRunService.create_run(self.db, self.schedule.id, "MANUAL", self.admin_uuid))
        self.assertEqual(run2.run_status, "SKIPPED")
        self.runs_to_cleanup.append(run2.id)

        # 3. Verify transition rules: QUEUED -> RUNNING
        service = WorkflowRunService()
        run1 = asyncio.run(service.start_run(run1.id, self.db))
        self.assertEqual(run1.run_status, "RUNNING")
        self.assertIsNotNone(run1.started_at)

        # 4. Verify invalid transitions: COMPLETED is not allowed from QUEUED
        with self.assertRaises(WorkflowRunStateError):
            asyncio.run(service.complete_run(run2.id, self.db)) # run2 is SKIPPED (terminal)

    def test_boundary_checker_rules(self):
        checker = BoundaryChecker()

        # 1. Check PASS path
        passed, reason = asyncio.run(checker.check(self.assignment, "TL-WRITE", self.db))
        self.assertTrue(passed)
        self.assertIsNone(reason)

        # 2. Check tool mismatch boundary failure
        passed, reason = asyncio.run(checker.check(self.assignment, "TL-UNKNOWN", self.db))
        self.assertFalse(passed)
        self.assertIn("not allowed by assignment policy", reason)

        # 3. Check inactive agent boundary failure
        self.agent.status = "DRAFT"
        self.db.commit()
        passed, reason = asyncio.run(checker.check(self.assignment, None, self.db))
        self.assertFalse(passed)
        self.assertIn("is not ACTIVE", reason)

        # Revert agent status
        self.agent.status = "ACTIVE"
        self.db.commit()

    def test_run_execution_and_sla_breach(self):
        service = WorkflowRunService()
        
        # Create a run
        run = asyncio.run(WorkflowRunService.create_run(self.db, self.schedule.id, "MANUAL", self.admin_uuid))
        self.runs_to_cleanup.append(run.id)

        # Execute run (simulates Claude invoke, output parsing, completion steps)
        asyncio.run(service.execute_run(run.id, self.db))
        
        # Verify run completed successfully
        self.db.refresh(run)
        self.assertEqual(run.run_status, "COMPLETED")
        self.assertIsNotNone(run.completed_at)
        self.assertTrue(len(run.steps) == 6) # Validation, Boundary, Invocation, Parsing, Audit, Notification

        # Verify output parsed successfully
        self.assertTrue(len(run.outputs) == 1)
        self.assertEqual(run.outputs[0].parse_status, "PARSED")

        # Verify Audit Events (QUEUED -> RUNNING -> COMPLETED)
        from app.modules.audit.event_service import GovernanceEventService
        audit_events = asyncio.run(GovernanceEventService().get_timeline("workflow_runs", run.id, self.db))
        event_codes = [e.event_type for e in audit_events]
        self.assertIn("WORKFLOW_RUN_QUEUED", event_codes)
        self.assertIn("WORKFLOW_RUN_COMPLETED", event_codes)

        # Test SLA Breach
        run_sla = asyncio.run(WorkflowRunService.create_run(self.db, self.schedule.id, "MANUAL", self.admin_uuid))
        self.runs_to_cleanup.append(run_sla.id)
        
        # Fake started_at to be way in the past
        run_sla.run_status = "RUNNING"
        run_sla.started_at = datetime.now(timezone.utc) - timedelta(hours=2)
        self.db.commit()

        # Run execute - should trigger SLA fail path
        asyncio.run(service.execute_run(run_sla.id, self.db))
        self.db.refresh(run_sla)
        self.assertEqual(run_sla.run_status, "FAILED")
        self.assertTrue(len(run_sla.failures) > 0)
        self.assertEqual(run_sla.failures[0].failure_type, "SLA_BREACH")

    def test_run_rest_routes(self):
        # 1. Create a run to list/get
        run = asyncio.run(WorkflowRunService.create_run(self.db, self.schedule.id, "MANUAL", self.admin_uuid))
        self.runs_to_cleanup.append(run.id)
        
        # Fetch output generation mock
        service = WorkflowRunService()
        asyncio.run(service.execute_run(run.id, self.db))

        # 2. Get Detail REST route
        detail_response = self.client.get(f"/api/v1/workflow-runs/{run.id}", headers=self.headers)
        self.assertEqual(detail_response.status_code, 200)
        detail_data = detail_response.json()
        self.assertTrue(detail_data["success"])
        self.assertEqual(detail_data["data"]["run_code"], run.run_code)

        # 3. List REST route
        list_response = self.client.get("/api/v1/workflow-runs", headers=self.headers)
        self.assertEqual(list_response.status_code, 200)
        list_data = list_response.json()
        self.assertTrue(list_data["success"])
        self.assertTrue(list_data["data"]["total"] > 0)

        # 4. Steps REST route
        steps_response = self.client.get(f"/api/v1/workflow-runs/{run.id}/steps", headers=self.headers)
        self.assertEqual(steps_response.status_code, 200)
        steps_data = steps_response.json()
        self.assertTrue(steps_data["success"])
        self.assertEqual(len(steps_data["data"]), 6)

        # 5. Outputs REST route (Test permission masking)
        # Note: Admin should have VIEW_WORKFLOW_RUN_OUTPUT permission (allow path)
        outputs_response = self.client.get(f"/api/v1/workflow-runs/{run.id}/outputs", headers=self.headers)
        self.assertEqual(outputs_response.status_code, 200)
        outputs_data = outputs_response.json()
        self.assertTrue(outputs_data["success"])
        self.assertIsNotNone(outputs_data["data"][0]["raw_output_json"])

        # Create a user with zero permissions
        # Mask test: if headers contain invalid or low privilege token, raw_output_json is masked
        # Login as non-permission auditor
        non_perm_headers = {}
        auditor_user = self.db.query(User).filter(User.email == "auditor@guardianiq.com").first()
        if not auditor_user:
            admin_user = self.db.query(User).filter(User.email == "admin@guardianiq.com").first()
            auditor_user = User(
                email="auditor@guardianiq.com",
                name="auditor",
                full_name="Compliance Auditor",
                hashed_password=admin_user.hashed_password
            )
            self.db.add(auditor_user)
            self.db.commit()

        auditor_guardian = self.db.query(GuardianUser).filter(GuardianUser.email == "auditor@guardianiq.com").first()
        if not auditor_guardian:
            admin_guardian = self.db.query(GuardianUser).filter(GuardianUser.email == "admin@guardianiq.com").first()
            auditor_guardian = GuardianUser(
                id=uuid4(),
                email="auditor@guardianiq.com",
                full_name="Compliance Auditor",
                department_id=admin_guardian.department_id,
                role_id=admin_guardian.role_id,
                status="ACTIVE"
            )
            self.db.add(auditor_guardian)
            self.db.commit()

        login_response_aud = self.client.post(
            "/api/auth/login",
            data={"username": "auditor@guardianiq.com", "password": "Admin@1234!"}
        )
        if login_response_aud.status_code == 200:
            token = login_response_aud.json()["access_token"]
            non_perm_headers = {"Authorization": f"Bearer {token}"}
            
            outputs_masked_resp = self.client.get(f"/api/v1/workflow-runs/{run.id}/outputs", headers=non_perm_headers)
            self.assertEqual(outputs_masked_resp.status_code, 200)
            masked_data = outputs_masked_resp.json()
            self.assertIsNone(masked_data["data"][0]["raw_output_json"])

        # 6. Cancel REST route
        # Cancel requires CANCEL_WORKFLOW_RUN
        run_to_cancel = asyncio.run(WorkflowRunService.create_run(self.db, self.schedule.id, "MANUAL", self.admin_uuid))
        self.runs_to_cleanup.append(run_to_cancel.id)
        
        # Must be RUNNING to be cancelled
        asyncio.run(service.start_run(run_to_cancel.id, self.db))

        cancel_resp = self.client.post(f"/api/v1/workflow-runs/{run_to_cancel.id}/cancel", headers=self.headers)
        self.assertEqual(cancel_resp.status_code, 200)
        self.assertEqual(cancel_resp.json()["data"]["run_status"], "CANCELLED")

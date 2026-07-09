import unittest
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import SessionLocal
from app.modules.auth.models import User, Role
from app.modules.registry.models import GuardianUser, RegistryWorkflow, RegistryAuditEvent
from app.modules.workflow_scheduler.models import ApprovalGroup, Phase2WorkflowSchedule, ApprovalGroupMember
from app.modules.authorization.models import WorkflowAuthorizationDecision, WorkflowDelegation


class AuthorizationIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.db = SessionLocal()
        
        # Ensure registry seed is run
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

        # Retrieve admin user UUID from guardian_users
        admin_guardian = self.db.query(GuardianUser).filter(GuardianUser.email == "admin@guardianiq.com").first()
        self.assertIsNotNone(admin_guardian, "Admin user not found in guardian_users")
        self.admin_uuid = admin_guardian.id

        # Assign GOVERNANCE_ADMIN role to admin in user_roles table so they have permissions
        admin_user = self.db.query(User).filter(User.email == "admin@guardianiq.com").first()
        gov_role = self.db.query(Role).filter(Role.role_code == "GOVERNANCE_ADMIN").first()
        if admin_user and gov_role and gov_role not in admin_user.roles:
            admin_user.roles.append(gov_role)
            self.db.commit()

        # Retrieve auditor user UUID from guardian_users
        auditor_guardian = self.db.query(GuardianUser).filter(GuardianUser.email == "auditor@guardianiq.com").first()
        self.assertIsNotNone(auditor_guardian, "Auditor user not found in guardian_users")
        self.auditor_uuid = auditor_guardian.id

        # Retrieve department and workflow
        from app.modules.registry.models import RegistryDepartment
        dept = self.db.query(RegistryDepartment).first()
        self.assertIsNotNone(dept, "No department found in database")
        self.department_id = dept.id

        workflow = self.db.query(RegistryWorkflow).first()
        if not workflow:
            workflow = RegistryWorkflow(
                id=uuid4(),
                workflow_code="WF-AUTH-TEST",
                workflow_name="Auth Test Workflow",
                workflow_type="TEST",
                department_id=self.department_id,
                owner_user_id=self.admin_uuid,
                business_criticality="LOW",
                status="ACTIVE"
            )
            self.db.add(workflow)
            self.db.commit()
        self.workflow_id = workflow.id

        # List of created entities for cleanup
        self.schedules_to_cleanup = []
        self.groups_to_cleanup = []
        self.members_to_cleanup = []
        self.delegations_to_cleanup = []
        self.decisions_to_cleanup = []
        self.audits_to_cleanup = []

    def tearDown(self):
        try:
            # Delete created decisions
            for dec_id in self.decisions_to_cleanup:
                self.db.query(WorkflowAuthorizationDecision).filter(WorkflowAuthorizationDecision.id == dec_id).delete()
            
            # Delete delegations
            for del_id in self.delegations_to_cleanup:
                self.db.query(WorkflowDelegation).filter(WorkflowDelegation.id == del_id).delete()
                
            # Delete members
            for gid, uid in self.members_to_cleanup:
                self.db.query(ApprovalGroupMember).filter(
                    ApprovalGroupMember.approval_group_id == gid,
                    ApprovalGroupMember.user_id == uid
                ).delete()
                
            # Delete schedules
            for sid in self.schedules_to_cleanup:
                self.db.query(Phase2WorkflowSchedule).filter(Phase2WorkflowSchedule.id == sid).delete()
                
            # Delete groups
            for gid in self.groups_to_cleanup:
                self.db.query(ApprovalGroup).filter(ApprovalGroup.id == gid).delete()

            # Delete audit events
            for aid in self.audits_to_cleanup:
                self.db.query(RegistryAuditEvent).filter(RegistryAuditEvent.id == aid).delete()

            self.db.commit()
        except Exception as e:
            self.db.rollback()
            print(f"Cleanup failed: {e}")
        self.db.close()

    def test_allow_path_governance_admin_low_risk(self):
        # 1. Create a LOW risk schedule
        group = ApprovalGroup(id=uuid4(), name="Low Risk Group", tenant_id=self.admin_uuid)
        self.db.add(group)
        self.db.commit()
        self.groups_to_cleanup.append(group.id)

        schedule = Phase2WorkflowSchedule(
            id=uuid4(),
            workflow_id=self.workflow_id,
            schedule_code="SCH-LOW-001",
            schedule_name="Low Risk Schedule",
            schedule_type="DAILY",
            owner_user_id=self.admin_uuid,
            tenant_id=self.admin_uuid,
            risk_level="LOW",
            schedule_status="DRAFT",
            approval_group_id=group.id
        )
        self.db.add(schedule)
        self.db.commit()
        self.schedules_to_cleanup.append(schedule.id)

        # 2. Evaluate ALLOW path
        payload = {
            "subject_user_id": str(self.admin_uuid),
            "object_type": "workflow_schedules",
            "object_id": str(schedule.id),
            "action": "ACTIVATE_WORKFLOW_SCHEDULE",
            "context_json": {}
        }
        response = self.client.post("/api/v1/authorization/evaluate", json=payload, headers=self.headers)
        self.assertEqual(response.status_code, 200, response.text)
        
        res_data = response.json()["data"]
        self.assertTrue(res_data["allowed"])
        self.assertEqual(res_data["decision"], "ALLOW")
        self.assertTrue(res_data["rbac_result"]["allowed"])
        self.assertTrue(res_data["abac_result"]["allowed"])

    def test_deny_missing_permission_rbac_fail(self):
        # 1. Create a schedule
        group = ApprovalGroup(id=uuid4(), name="RBAC Group", tenant_id=self.admin_uuid)
        self.db.add(group)
        self.db.commit()
        self.groups_to_cleanup.append(group.id)

        schedule = Phase2WorkflowSchedule(
            id=uuid4(),
            workflow_id=self.workflow_id,
            schedule_code="SCH-RBAC-001",
            schedule_name="RBAC Fail Schedule",
            schedule_type="DAILY",
            owner_user_id=self.admin_uuid,
            tenant_id=self.admin_uuid,
            risk_level="LOW",
            schedule_status="DRAFT",
            approval_group_id=group.id
        )
        self.db.add(schedule)
        self.db.commit()
        self.schedules_to_cleanup.append(schedule.id)

        # 2. Evaluate with Auditor (should fail because Auditor doesn't have ACTIVATE_WORKFLOW_SCHEDULE)
        payload = {
            "subject_user_id": str(self.auditor_uuid),
            "object_type": "workflow_schedules",
            "object_id": str(schedule.id),
            "action": "ACTIVATE_WORKFLOW_SCHEDULE",
            "context_json": {}
        }
        response = self.client.post("/api/v1/authorization/evaluate", json=payload, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        
        res_data = response.json()["data"]
        self.assertFalse(res_data["allowed"])
        self.assertEqual(res_data["decision"], "DENY")
        self.assertFalse(res_data["rbac_result"]["allowed"])
        self.assertIn("Failed RBAC check", res_data["deny_reasons"][0])

    def test_deny_non_approval_group_member_high_risk_abac_fail(self):
        # 1. Create a HIGH risk schedule
        group = ApprovalGroup(id=uuid4(), name="High Risk Group", tenant_id=self.admin_uuid)
        self.db.add(group)
        self.db.commit()
        self.groups_to_cleanup.append(group.id)

        schedule = Phase2WorkflowSchedule(
            id=uuid4(),
            workflow_id=self.workflow_id,
            schedule_code="SCH-HIGH-001",
            schedule_name="High Risk Schedule",
            schedule_type="DAILY",
            owner_user_id=self.admin_uuid,
            tenant_id=self.admin_uuid,
            risk_level="HIGH",
            schedule_status="DRAFT",
            approval_group_id=group.id
        )
        self.db.add(schedule)
        self.db.commit()
        self.schedules_to_cleanup.append(schedule.id)

        # Temporarily remove SUPER_ADMIN role so we can test the restricted GOVERNANCE_ADMIN constraints
        admin_user = self.db.query(User).filter(User.email == "admin@guardianiq.com").first()
        super_role = self.db.query(Role).filter(Role.role_code == "SUPER_ADMIN").first()
        removed_super = False
        if admin_user and super_role and super_role in admin_user.roles:
            admin_user.roles.remove(super_role)
            self.db.commit()
            removed_super = True

        try:
            # 2. Evaluate with admin (RBAC passes, but admin is NOT in the approval group, and no active delegation)
            payload = {
                "subject_user_id": str(self.admin_uuid),
                "object_type": "workflow_schedules",
                "object_id": str(schedule.id),
                "action": "ACTIVATE_WORKFLOW_SCHEDULE",
                "context_json": {}
            }
            response = self.client.post("/api/v1/authorization/evaluate", json=payload, headers=self.headers)
            self.assertEqual(response.status_code, 200)
            
            res_data = response.json()["data"]
            self.assertFalse(res_data["allowed"])
            self.assertEqual(res_data["decision"], "DENY")
            self.assertTrue(res_data["rbac_result"]["allowed"])
            self.assertFalse(res_data["abac_result"]["allowed"])
            self.assertIn("High risk schedules require approval group membership", res_data["deny_reasons"][0])
        finally:
            # Restore SUPER_ADMIN role
            if removed_super and admin_user and super_role and super_role not in admin_user.roles:
                admin_user.roles.append(super_role)
                self.db.commit()

    def test_decision_persisted_to_workflow_authorization_decisions(self):
        # 1. Create schedule
        group = ApprovalGroup(id=uuid4(), name="Persist Group", tenant_id=self.admin_uuid)
        self.db.add(group)
        self.db.commit()
        self.groups_to_cleanup.append(group.id)

        schedule = Phase2WorkflowSchedule(
            id=uuid4(),
            workflow_id=self.workflow_id,
            schedule_code="SCH-PERSIST-001",
            schedule_name="Persist Test Schedule",
            schedule_type="DAILY",
            owner_user_id=self.admin_uuid,
            tenant_id=self.admin_uuid,
            risk_level="LOW",
            schedule_status="DRAFT",
            approval_group_id=group.id
        )
        self.db.add(schedule)
        self.db.commit()
        self.schedules_to_cleanup.append(schedule.id)

        # 2. Call evaluate via client (which sets persist=True in implementation)
        payload = {
            "subject_user_id": str(self.admin_uuid),
            "object_type": "workflow_schedules",
            "object_id": str(schedule.id),
            "action": "ACTIVATE_WORKFLOW_SCHEDULE",
            "context_json": {}
        }
        response = self.client.post("/api/v1/authorization/evaluate", json=payload, headers=self.headers)
        self.assertEqual(response.status_code, 200)

        # 3. Query DB to verify the decision record was persisted
        decision_rec = (
            self.db.query(WorkflowAuthorizationDecision)
            .filter(
                WorkflowAuthorizationDecision.subject_user_id == self.admin_uuid,
                WorkflowAuthorizationDecision.action == "ACTIVATE_WORKFLOW_SCHEDULE",
                WorkflowAuthorizationDecision.object_id == schedule.id
            )
            .order_by(WorkflowAuthorizationDecision.evaluated_at.desc())
            .first()
        )
        self.assertIsNotNone(decision_rec)
        self.assertEqual(decision_rec.decision, "ALLOW")
        self.decisions_to_cleanup.append(decision_rec.id)

    def test_authorization_denied_audit_event_published_on_deny(self):
        # 1. Create a schedule
        group = ApprovalGroup(id=uuid4(), name="Audit Group", tenant_id=self.admin_uuid)
        self.db.add(group)
        self.db.commit()
        self.groups_to_cleanup.append(group.id)

        schedule = Phase2WorkflowSchedule(
            id=uuid4(),
            workflow_id=self.workflow_id,
            schedule_code="SCH-AUDIT-001",
            schedule_name="Audit Denied Schedule",
            schedule_type="DAILY",
            owner_user_id=self.admin_uuid,
            tenant_id=self.admin_uuid,
            risk_level="LOW",
            schedule_status="DRAFT",
            approval_group_id=group.id
        )
        self.db.add(schedule)
        self.db.commit()
        self.schedules_to_cleanup.append(schedule.id)

        # 2. Evaluate with Auditor user (triggers DENY due to RBAC failure)
        payload = {
            "subject_user_id": str(self.auditor_uuid),
            "object_type": "workflow_schedules",
            "object_id": str(schedule.id),
            "action": "ACTIVATE_WORKFLOW_SCHEDULE",
            "context_json": {}
        }
        response = self.client.post("/api/v1/authorization/evaluate", json=payload, headers=self.headers)
        self.assertEqual(response.status_code, 200)

        # 3. Verify audit event is logged in registry_audit_events table
        audit_rec = (
            self.db.query(RegistryAuditEvent)
            .filter(
                RegistryAuditEvent.event_type == "AUTHORIZATION_DENIED",
                RegistryAuditEvent.actor_user_id == self.auditor_uuid
            )
            .order_by(RegistryAuditEvent.created_at.desc())
            .first()
        )
        self.assertIsNotNone(audit_rec)
        self.assertIn("Authorization denied", audit_rec.event_metadata.get("change_summary", ""))
        self.audits_to_cleanup.append(audit_rec.id)

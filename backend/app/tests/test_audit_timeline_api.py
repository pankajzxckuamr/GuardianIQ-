import unittest
from uuid import uuid4
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal
from app.modules.registry.models import GuardianUser
from app.modules.audit.event_codes import WorkflowEventCode
from app.modules.audit.event_service import GovernanceEventService

class AuditTimelineApiTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.db = SessionLocal()

        # Seed data
        from app.modules.registry.seed import seed_registry_data
        seed_registry_data(self.db)

        # Login as admin to get token
        login_response = self.client.post(
            "/api/auth/login",
            data={"username": "admin@guardianiq.com", "password": "Admin@1234!"}
        )
        self.assertEqual(login_response.status_code, 200)
        login_data = login_response.json()
        self.access_token = login_data["access_token"]
        self.headers = {"Authorization": f"Bearer {self.access_token}"}

        # Get Admin Guardian User ID
        admin_guardian = self.db.query(GuardianUser).filter(GuardianUser.email == "admin@guardianiq.com").first()
        self.assertIsNotNone(admin_guardian)
        self.admin_uuid = admin_guardian.id

    def tearDown(self):
        self.db.close()

    async def test_get_audit_events_timeline_auth_and_actor_resolution(self):
        # 1. Test unauthenticated request
        response = self.client.get(
            f"/api/v1/audit/events?entity_type=WORKFLOW_SCHEDULE&entity_id={uuid4()}"
        )
        self.assertEqual(response.status_code, 401)

        # 2. Publish an event using GovernanceEventService
        entity_id = uuid4()
        service = GovernanceEventService()
        await service.publish_event(
            event_code=WorkflowEventCode.WORKFLOW_SCHEDULE_CREATED,
            entity_type="workflow_schedules",
            entity_id=entity_id,
            actor_type="USER",
            actor_id=self.admin_uuid,
            action_type="CREATE",
            event_summary="Test schedule created by admin user",
            event_payload={},
            db=self.db
        )

        # 3. Test authenticated request and verify actor_name
        response = self.client.get(
            f"/api/v1/audit/events?entity_type=WORKFLOW_SCHEDULE&entity_id={entity_id}",
            headers=self.headers
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        items = data["data"]["items"]
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["action_type"], "CREATE")
        self.assertEqual(items[0]["event_summary"], "Test schedule created by admin user")
        self.assertIn("actor_name", items[0])
        # It should resolve to the admin user's name or email
        self.assertIn("admin", items[0]["actor_name"].lower())

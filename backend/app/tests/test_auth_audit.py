import unittest
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal
from app.modules.audit.models import AuditEvent

class AuthAuditIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.db = SessionLocal()

    def tearDown(self):
        try:
            events = self.db.query(AuditEvent).all()
            for event in events:
                meta = event.event_metadata or {}
                if meta.get("ip_address") == "testclient" or meta.get("ip") == "testclient":
                    self.db.delete(event)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            print(f"Failed to clean up test audit events: {e}")
        self.db.close()

    def test_failed_login_records_audit_event(self):
        # 1. Capture initial count of audit events
        initial_count = self.db.query(AuditEvent).filter(AuditEvent.action == "login").count()

        # 2. Attempt failed login with non-existent user
        response = self.client.post(
            "/api/auth/login",
            data={"username": "nonexistent@guardianiq.com", "password": "WrongPassword123!"}
        )
        self.assertEqual(response.status_code, 401)

        # 3. Assert a new audit event was written
        new_count = self.db.query(AuditEvent).filter(AuditEvent.action == "login").count()
        self.assertEqual(new_count, initial_count + 1)

        # 4. Verify event details
        latest_event = self.db.query(AuditEvent).filter(AuditEvent.action == "login").order_by(AuditEvent.created_at.desc()).first()
        self.assertEqual(latest_event.event_type, "auth.login_failure")
        self.assertEqual(latest_event.entity_type, "user")
        self.assertEqual(latest_event.action, "login")
        self.assertEqual(latest_event.event_metadata["status"], "failure")
        self.assertIn("User not found", latest_event.event_metadata["detail"])

    def test_failed_password_records_audit_event(self):
        initial_count = self.db.query(AuditEvent).filter(AuditEvent.action == "login").count()

        # Attempt failed login with correct username (admin) but incorrect password
        response = self.client.post(
            "/api/auth/login",
            data={"username": "admin@guardianiq.com", "password": "WrongPassword123!"}
        )
        self.assertEqual(response.status_code, 401)

        new_count = self.db.query(AuditEvent).filter(AuditEvent.action == "login").count()
        self.assertEqual(new_count, initial_count + 1)

        latest_event = self.db.query(AuditEvent).filter(AuditEvent.action == "login").order_by(AuditEvent.created_at.desc()).first()
        self.assertEqual(latest_event.event_type, "auth.login_failure")
        self.assertEqual(latest_event.entity_type, "user")
        self.assertEqual(latest_event.action, "login")
        self.assertEqual(latest_event.event_metadata["status"], "failure")
        self.assertIn("Invalid password", latest_event.event_metadata["detail"])

    def test_successful_login_records_audit_event(self):
        initial_count = self.db.query(AuditEvent).filter(AuditEvent.action == "login").count()

        # Attempt successful login with seeded admin user
        response = self.client.post(
            "/api/auth/login",
            data={"username": "admin@guardianiq.com", "password": "Admin@1234!"}
        )
        self.assertEqual(response.status_code, 200)

        new_count = self.db.query(AuditEvent).filter(AuditEvent.action == "login").count()
        self.assertEqual(new_count, initial_count + 1)

        latest_event = self.db.query(AuditEvent).filter(AuditEvent.action == "login").order_by(AuditEvent.created_at.desc()).first()
        self.assertEqual(latest_event.event_type, "auth.login_success")
        self.assertEqual(latest_event.entity_type, "user")
        self.assertEqual(latest_event.action, "login")
        self.assertEqual(latest_event.event_metadata["status"], "success")
        self.assertIn("Login successful", latest_event.event_metadata["detail"])

if __name__ == "__main__":
    unittest.main()

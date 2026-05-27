import unittest

from fastapi.testclient import TestClient

from app.main import app


class RBACRouteProtectionTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_module_routes_require_authentication(self):
        protected_routes = [
            ("get", "/api/policies"),
            ("get", "/api/audit"),
            ("get", "/api/data-sources"),
            ("get", "/api/departments"),
            ("get", "/api/approvals"),
            ("get", "/api/approvals/1"),
            ("get", "/api/recommendations"),
            ("get", "/api/recommendations/1"),
            ("get", "/api/ai-models"),
            ("get", "/api/ai-models/1"),
            ("get", "/api/agents"),
            ("get", "/api/agents/1"),
        ]

        for method, path in protected_routes:
            response = getattr(self.client, method)(path)
            self.assertEqual(
                response.status_code,
                401,
                msg=f"{method.upper()} {path} should require authentication, got {response.status_code}",
            )


if __name__ == "__main__":
    unittest.main()

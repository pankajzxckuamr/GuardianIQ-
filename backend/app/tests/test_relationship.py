import unittest
from uuid import uuid4
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal
from app.modules.auth.models import User, Role
from app.modules.ai_model.models import AIModel
from app.modules.agent.models import Agent
from app.modules.relationship.models import GenericRelationship, ObjectResponsibility, RelationshipValidationResult

class RelationshipIntegrationTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.db = SessionLocal()

        # Seed registry data if not already present
        from app.modules.registry.seed import seed_registry_data
        seed_registry_data(self.db)

        # Login to get authorization token
        login_response = self.client.post(
            "/api/auth/login",
            data={"username": "admin@guardianiq.com", "password": "Admin@1234!"}
        )
        self.assertEqual(login_response.status_code, 200)
        login_data = login_response.json()
        self.access_token = login_data["access_token"]
        self.headers = {"Authorization": f"Bearer {self.access_token}"}

        # Get admin user and tenant details
        admin = self.db.query(User).filter(User.email == "admin@guardianiq.com").first()
        self.assertIsNotNone(admin)
        self.admin_id = admin.id
        self.tenant_id = admin.id

        # Add GOVERNANCE_ADMIN role to admin user to ensure ABAC write access passes
        gov_admin_role = self.db.query(Role).filter(Role.role_code == "GOVERNANCE_ADMIN").first()
        if gov_admin_role and gov_admin_role not in admin.roles:
            admin.roles.append(gov_admin_role)
            self.db.commit()

        # Setup test model and agent in registry
        self.model_code = f"test-model-{uuid4().hex[:6]}"
        self.test_model = AIModel(
            id=uuid4(),
            tenant_id=self.tenant_id,
            model_code=self.model_code,
            model_name="Test Model for Relationship",
            model_type="LLM",
            purpose="Testing relationships",
            risk_level="LOW",
            status="ACTIVE"
        )
        self.db.add(self.test_model)

        self.agent_code = f"test-agent-{uuid4().hex[:6]}"
        self.test_agent = Agent(
            id=uuid4(),
            tenant_id=self.tenant_id,
            agent_code=self.agent_code,
            agent_name="Test Agent for Relationship",
            agent_type="ROUTING",
            execution_mode="RECOMMEND_ONLY",
            risk_level="LOW",
            status="ACTIVE"
        )
        self.db.add(self.test_agent)
        self.db.commit()

        self.created_relationship_ids = []
        self.created_responsibility_ids = []

    def tearDown(self):
        # Clean up any created objects to keep the test db clean
        for rel_id in self.created_relationship_ids:
            self.db.query(GenericRelationship).filter(GenericRelationship.id == rel_id).delete()
        for resp_id in self.created_responsibility_ids:
            self.db.query(ObjectResponsibility).filter(ObjectResponsibility.id == resp_id).delete()
        
        self.db.delete(self.test_agent)
        self.db.delete(self.test_model)
        self.db.commit()
        self.db.close()

    async def test_relationship_lifecycle_and_graph(self):
        # 1. Create a relationship via POST /api/registry/relationships/
        payload = {
            "source_type": "agents",
            "source_id": str(self.test_agent.id),
            "relationship_type": "uses",
            "target_type": "ai_models",
            "target_id": str(self.test_model.id),
            "relationship_scope": "Testing Scope",
            "effective_from": datetime.now(timezone.utc).isoformat(),
            "effective_to": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
        }
        
        response = self.client.post("/api/registry/relationships", json=payload, headers=self.headers)
        self.assertEqual(response.status_code, 200, response.text)
        res_data = response.json()
        self.assertTrue(res_data["success"])
        rel_id = res_data["data"]["id"]
        self.created_relationship_ids.append(rel_id)
        
        self.assertEqual(res_data["data"]["status"], "PROPOSED")
        self.assertEqual(res_data["data"]["source_type"], "agents")
        self.assertEqual(res_data["data"]["target_type"], "ai_models")

        # 2. List relationships via GET /api/registry/relationships
        list_response = self.client.get("/api/registry/relationships?source_type=agents", headers=self.headers)
        self.assertEqual(list_response.status_code, 200)
        list_data = list_response.json()
        self.assertTrue(list_data["success"])
        items = list_data["data"]["items"]
        self.assertTrue(any(item["id"] == rel_id for item in items))

        # 3. Update the relationship via PUT /api/registry/relationships/{id}
        update_payload = {
            "relationship_scope": "Updated Scope"
        }
        update_response = self.client.put(f"/api/registry/relationships/{rel_id}", json=update_payload, headers=self.headers)
        self.assertEqual(update_response.status_code, 200)
        update_data = update_response.json()
        self.assertEqual(update_data["data"]["relationship_scope"], "Updated Scope")

        # 4. Approve the relationship via POST /api/registry/relationships/{id}/approve
        approve_res = self.client.post(f"/api/registry/relationships/{rel_id}/approve", headers=self.headers)
        self.assertEqual(approve_res.status_code, 200)
        
        # 5. Activate the relationship via POST /api/registry/relationships/{id}/activate
        activate_res = self.client.post(f"/api/registry/relationships/{rel_id}/activate", headers=self.headers)
        self.assertEqual(activate_res.status_code, 200)

        # Verify status is active
        get_list = self.client.get("/api/registry/relationships", headers=self.headers)
        items = get_list.json()["data"]["items"]
        rel_item = next(item for item in items if item["id"] == rel_id)
        self.assertEqual(rel_item["status"], "ACTIVE")

        # 6. Suspend the relationship via POST /api/registry/relationships/{id}/suspend
        suspend_res = self.client.post(f"/api/registry/relationships/{rel_id}/suspend?reason=Temporary+suspend", headers=self.headers)
        self.assertEqual(suspend_res.status_code, 200)

        # 7. Revoke/delete the relationship via DELETE /api/registry/relationships/{id}
        revoke_res = self.client.delete(f"/api/registry/relationships/{rel_id}?reason=Revoked+reason", headers=self.headers)
        self.assertEqual(revoke_res.status_code, 200)

        # 8. Get Graph View via GET /api/registry/relationships/graph/{object_type}/{object_id}
        graph_res = self.client.get(f"/api/registry/relationships/graph/agents/{self.test_agent.id}", headers=self.headers)
        self.assertEqual(graph_res.status_code, 200)
        graph_data = graph_res.json()
        self.assertTrue(graph_data["success"])
        self.assertEqual(graph_data["data"]["root"]["id"], str(self.test_agent.id))

        # 9. Get Impact Analysis via GET /api/registry/relationships/impact/{object_type}/{object_id}
        impact_res = self.client.get(f"/api/registry/relationships/impact/ai_models/{self.test_model.id}", headers=self.headers)
        self.assertEqual(impact_res.status_code, 200)
        impact_data = impact_res.json()
        self.assertTrue(impact_data["success"])
        self.assertEqual(impact_data["data"]["root"]["id"], str(self.test_model.id))

    async def test_responsibilities_management(self):
        # 1. Assign responsibility via POST /api/registry/relationships/responsibilities
        payload = {
            "object_type": "agents",
            "object_id": str(self.test_agent.id),
            "actor_type": "USER",
            "actor_id": str(self.admin_id),
            "responsibility_type": "OWNER",
            "is_primary": True,
            "effective_from": datetime.now(timezone.utc).isoformat()
        }
        response = self.client.post("/api/registry/relationships/responsibilities", json=payload, headers=self.headers)
        self.assertEqual(response.status_code, 200, response.text)
        res_data = response.json()
        self.assertTrue(res_data["success"])
        resp_id = res_data["data"]["id"]
        self.created_responsibility_ids.append(resp_id)

        self.assertEqual(res_data["data"]["responsibility_type"], "OWNER")
        self.assertTrue(res_data["data"]["is_primary"])

        # 2. Get responsibilities via GET /api/registry/relationships/responsibilities/{object_type}/{object_id}
        get_res = self.client.get(f"/api/registry/relationships/responsibilities/agents/{self.test_agent.id}", headers=self.headers)
        self.assertEqual(get_res.status_code, 200)
        get_data = get_res.json()
        self.assertTrue(get_data["success"])
        self.assertTrue(len(get_data["data"]) > 0)
        self.assertEqual(get_data["data"][0]["id"], resp_id)

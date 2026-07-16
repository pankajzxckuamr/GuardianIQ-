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

    async def test_relationship_filtering_and_standalone_validation(self):
        # 1. Test standalone validation endpoint POST /api/registry/relationships/validate
        valid_payload = {
            "source_type": "agents",
            "source_id": str(self.test_agent.id),
            "relationship_type": "uses",
            "target_type": "ai_models",
            "target_id": str(self.test_model.id),
            "relationship_scope": "Dry-run Testing",
            "effective_from": datetime.now(timezone.utc).isoformat()
        }
        val_res = self.client.post("/api/registry/relationships/validate", json=valid_payload, headers=self.headers)
        self.assertEqual(val_res.status_code, 200)
        val_data = val_res.json()
        self.assertTrue(val_data["success"])
        self.assertTrue(val_data["data"]["valid"])
        self.assertEqual(len(val_data["data"]["errors"]), 0)

        # 2. Test validation failures
        invalid_payload = {
            "source_type": "agents",
            "source_id": str(self.test_agent.id),
            "relationship_type": "uses",
            "target_type": "ai_models",
            "target_id": str(uuid4()), # Non-existent model ID
            "relationship_scope": "Dry-run Testing Fail",
            "effective_from": datetime.now(timezone.utc).isoformat()
        }
        val_res_fail = self.client.post("/api/registry/relationships/validate", json=invalid_payload, headers=self.headers)
        self.assertEqual(val_res_fail.status_code, 200)
        val_data_fail = val_res_fail.json()
        self.assertTrue(val_data_fail["success"])
        self.assertFalse(val_data_fail["data"]["valid"])
        self.assertTrue(len(val_data_fail["data"]["errors"]) > 0)
        self.assertIn("GRAPH_INTEGRITY-002", val_data_fail["data"]["errors"][0]["rule_id"])

        # 3. Test list endpoint filtering by source_id
        # Create a relationship first
        create_res = self.client.post("/api/registry/relationships", json=valid_payload, headers=self.headers)
        self.assertEqual(create_res.status_code, 200)
        rel_id = create_res.json()["data"]["id"]
        self.created_relationship_ids.append(rel_id)

        # Query filtering by correct source_id
        filter_res = self.client.get(f"/api/registry/relationships?source_type=agents&source_id={self.test_agent.id}", headers=self.headers)
        self.assertEqual(filter_res.status_code, 200)
        filter_data = filter_res.json()
        self.assertTrue(any(item["id"] == rel_id for item in filter_data["data"]["items"]))

        # Query filtering by incorrect/random source_id
        filter_res_empty = self.client.get(f"/api/registry/relationships?source_type=agents&source_id={uuid4()}", headers=self.headers)
        self.assertEqual(filter_res_empty.status_code, 200)
        self.assertEqual(len(filter_res_empty.json()["data"]["items"]), 0)

    async def test_relationship_caching_and_invalidation(self):
        # 1. Create relationship
        payload = {
            "source_type": "agents",
            "source_id": str(self.test_agent.id),
            "relationship_type": "uses",
            "target_type": "ai_models",
            "target_id": str(self.test_model.id),
            "relationship_scope": "Cache test scope",
            "effective_from": datetime.now(timezone.utc).isoformat()
        }
        res = self.client.post("/api/registry/relationships", json=payload, headers=self.headers)
        self.assertEqual(res.status_code, 200)
        rel_id = res.json()["data"]["id"]
        self.created_relationship_ids.append(rel_id)

        # Approve and activate so it is fully active
        self.client.post(f"/api/registry/relationships/{rel_id}/approve", headers=self.headers)
        self.client.post(f"/api/registry/relationships/{rel_id}/activate", headers=self.headers)

        # Clear cache first to start clean
        from app.modules.relationship.cache_service import MemoryCacheService
        MemoryCacheService().clear()

        # First request - caches
        res1 = self.client.get(f"/api/registry/relationships/graph/agents/{self.test_agent.id}", headers=self.headers)
        self.assertEqual(res1.status_code, 200)
        self.assertEqual(res1.json()["message"], "Graph retrieved")

        # Second request - cached
        res2 = self.client.get(f"/api/registry/relationships/graph/agents/{self.test_agent.id}", headers=self.headers)
        self.assertEqual(res2.status_code, 200)
        self.assertEqual(res2.json()["message"], "Graph retrieved (cached)")

        # Invalidate via write action (suspend)
        self.client.post(f"/api/registry/relationships/{rel_id}/suspend?reason=cache+invalidation+test", headers=self.headers)

        # Third request - cache bypassed/regenerated
        res3 = self.client.get(f"/api/registry/relationships/graph/agents/{self.test_agent.id}", headers=self.headers)
        self.assertEqual(res3.status_code, 200)
        self.assertEqual(res3.json()["message"], "Graph retrieved")

    async def test_relationship_read_clearance_redaction(self):
        # 1. Create a high-sensitivity tool in the database
        from app.modules.registry.models import Tool
        confidential_tool = Tool(
            id=uuid4(),
            tenant_id=self.tenant_id,
            tool_code=f"conf-tool-{uuid4().hex[:6]}",
            tool_name="Confidential Government Tool",
            tool_category="GOVERNMENT",
            access_mode="WRITE_ONLY",
            sensitivity_level="CONFIDENTIAL",
            allowed_operations_json=[],
            status="ACTIVE"
        )
        self.db.add(confidential_tool)
        self.db.commit()

        # 2. Create a low-clearance user (BUSINESS_USER)
        low_user_email = f"user-{uuid4().hex[:6]}@guardianiq.com"
        low_role = self.db.query(Role).filter(Role.role_code == "BUSINESS_USER").first()
        if not low_role:
            low_role = Role(id=uuid4(), role_code="BUSINESS_USER", role_name="Business User")
            self.db.add(low_role)
            self.db.commit()

        from app.core.security import hash_password
        low_user = User(
            id=uuid4(),
            email=low_user_email,
            name="Low Clearance User",
            full_name="Low Clearance User",
            hashed_password=hash_password("LowPass@1234!"),
            status="ACTIVE"
        )
        low_user.roles.append(low_role)
        self.db.add(low_user)
        self.db.commit()

        try:
            # 3. Create relationship directly in DB under the low user's tenant
            # (The low user's tenant_id == low_user.id per get_tenant_id logic)
            from app.modules.relationship.models import GenericRelationship as RelModel
            confidential_rel = RelModel(
                id=uuid4(),
                tenant_id=low_user.id,
                source_type="agents",
                source_id=str(self.test_agent.id),
                relationship_type="uses_tool",
                target_type="tools",
                target_id=str(confidential_tool.id),
                relationship_scope="Secure Scope",
                status="ACTIVE",
                effective_from=datetime.now(timezone.utc)
            )
            self.db.add(confidential_rel)
            self.db.commit()

            # Login as low-clearance user
            login_res = self.client.post(
                "/api/auth/login",
                data={"username": low_user_email, "password": "LowPass@1234!"}
            )
            self.assertEqual(login_res.status_code, 200)
            low_token = login_res.json()["access_token"]
            low_headers = {"Authorization": f"Bearer {low_token}"}

            # Clear cache first to guarantee fresh database query
            from app.modules.relationship.cache_service import MemoryCacheService
            MemoryCacheService().clear()

            # Query graph as low clearance user
            graph_res = self.client.get(f"/api/registry/relationships/graph/agents/{self.test_agent.id}", headers=low_headers)
            self.assertEqual(graph_res.status_code, 200)
            data = graph_res.json()["data"]
            
            # Verify that the confidential tool is redacted in outgoing relations list
            outgoing = data["outgoing"]
            tool_node = next(x for x in outgoing if x["other_entity_id"] == str(confidential_tool.id))
            self.assertEqual(tool_node["other_entity_name"], "[REDACTED (Insufficient Clearance)]")
            self.assertEqual(tool_node["metadata_json"], {})
            self.assertIsNone(tool_node["relationship_scope"])
        finally:
            # Cleanup — delete relationship first to avoid FK violation
            self.db.query(GenericRelationship).filter(GenericRelationship.tenant_id == low_user.id).delete()
            self.db.commit()
            self.db.delete(confidential_tool)
            self.db.delete(low_user)
            self.db.commit()

    async def test_unauthorized_write_operations_blocked(self):
        # 1. Create low-clearance user (BUSINESS_USER)
        low_user_email = f"user-{uuid4().hex[:6]}@guardianiq.com"
        low_role = self.db.query(Role).filter(Role.role_code == "BUSINESS_USER").first()
        if not low_role:
            low_role = Role(id=uuid4(), role_code="BUSINESS_USER", role_name="Business User")
            self.db.add(low_role)
            self.db.commit()

        from app.core.security import hash_password
        low_user = User(
            id=uuid4(),
            email=low_user_email,
            name="Low User",
            full_name="Low User",
            hashed_password=hash_password("LowPass@1234!"),
            status="ACTIVE"
        )
        low_user.roles.append(low_role)
        self.db.add(low_user)
        self.db.commit()

        try:
            # Login as low-clearance user
            login_res = self.client.post(
                "/api/auth/login",
                data={"username": low_user_email, "password": "LowPass@1234!"}
            )
            self.assertEqual(login_res.status_code, 200)
            low_token = login_res.json()["access_token"]
            low_headers = {"Authorization": f"Bearer {low_token}"}

            # Create a relationship belonging to low_user's tenant directly in DB
            unauthorized_rel = GenericRelationship(
                id=uuid4(),
                tenant_id=low_user.id,
                source_type="agents",
                source_id=str(self.test_agent.id),
                relationship_type="uses",
                target_type="ai_models",
                target_id=str(self.test_model.id),
                relationship_scope="Unauthorized Scope",
                status="PROPOSED",
                effective_from=datetime.now(timezone.utc)
            )
            self.db.add(unauthorized_rel)
            self.db.commit()

            # 2. Verify write path blockages return 403 Forbidden
            approve_res = self.client.post(f"/api/registry/relationships/{unauthorized_rel.id}/approve", headers=low_headers)
            self.assertEqual(approve_res.status_code, 403)

            activate_res = self.client.post(f"/api/registry/relationships/{unauthorized_rel.id}/activate", headers=low_headers)
            self.assertEqual(activate_res.status_code, 403)

            suspend_res = self.client.post(f"/api/registry/relationships/{unauthorized_rel.id}/suspend?reason=hack", headers=low_headers)
            self.assertEqual(suspend_res.status_code, 403)

            revoke_res = self.client.delete(f"/api/registry/relationships/{unauthorized_rel.id}?reason=hack", headers=low_headers)
            self.assertEqual(revoke_res.status_code, 403)

        finally:
            # Cleanup rel and user
            self.db.query(GenericRelationship).filter(GenericRelationship.tenant_id == low_user.id).delete()
            self.db.delete(low_user)
            self.db.commit()

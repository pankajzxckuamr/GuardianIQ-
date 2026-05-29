import unittest
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal
from app.modules.registry.models import RegistryAIModel, RegistryAIAgent, RegistryTool, RegistryWorkflow

class RegistryIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.db = SessionLocal()
        
        # Seed registry data if not already present
        from app.modules.registry.seed import seed_registry_data
        seed_registry_data(self.db)
        
        self.created_model_ids = []
        self.created_agent_ids = []
        self.created_tool_ids = []
        self.created_workflow_ids = []

        # Login to get authorization token
        login_response = self.client.post(
            "/api/auth/login",
            data={"username": "admin@guardianiq.com", "password": "Admin@1234!"}
        )
        self.assertEqual(login_response.status_code, 200)
        login_data = login_response.json()
        self.access_token = login_data["access_token"]
        self.headers = {"Authorization": f"Bearer {self.access_token}"}

        # Retrieve a valid department
        dept_response = self.client.get("/api/registry/departments/lookup", headers=self.headers)
        self.assertEqual(dept_response.status_code, 200)
        dept_data = dept_response.json()
        self.assertTrue(len(dept_data["data"]) > 0, "No departments found in test database lookup")
        self.department_id = dept_data["data"][0]["id"]

        # Retrieve a valid user
        user_response = self.client.get("/api/registry/users/lookup", headers=self.headers)
        self.assertEqual(user_response.status_code, 200)
        user_data = user_response.json()
        self.assertTrue(len(user_data["data"]) > 0, "No users found in test database lookup")
        self.user_id = user_data["data"][0]["id"]

    def tearDown(self):
        # Cleanup any created registry entities to keep test database pristine
        try:
            for mid in self.created_model_ids:
                model = self.db.query(RegistryAIModel).filter(RegistryAIModel.id == mid).first()
                if model:
                    self.db.delete(model)
            for aid in self.created_agent_ids:
                agent = self.db.query(RegistryAIAgent).filter(RegistryAIAgent.id == aid).first()
                if agent:
                    self.db.delete(agent)
            for tid in self.created_tool_ids:
                tool = self.db.query(RegistryTool).filter(RegistryTool.id == tid).first()
                if tool:
                    self.db.delete(tool)
            for wid in self.created_workflow_ids:
                workflow = self.db.query(RegistryWorkflow).filter(RegistryWorkflow.id == wid).first()
                if workflow:
                    self.db.delete(workflow)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            print(f"Failed to clean up registry entities: {e}")
        self.db.close()

    def test_registry_lifecycle_and_summary(self):
        # 1. Create AI Model
        model_payload = {
            "model_code": "TEST-MODEL-001",
            "model_name": "Test LLM Model",
            "model_type": "LLM",
            "provider": "OpenAI",
            "version": "gpt-4",
            "purpose": "Testing integration functionality",
            "department_id": self.department_id,
            "owner_user_id": self.user_id,
            "risk_level": "LOW",
            "deployment_environment": "staging",
            "status": "DRAFT",
            "metadata_json": {}
        }
        model_response = self.client.post("/api/registry/models", json=model_payload, headers=self.headers)
        self.assertEqual(model_response.status_code, 200, f"Failed to create AI Model: {model_response.text}")
        model_data = model_response.json()
        self.assertEqual(model_data["status"], "success")
        self.assertEqual(model_data["data"]["model_code"], "TEST-MODEL-001")
        self.created_model_ids.append(model_data["data"]["id"])

        # 2. Create AI Agent
        agent_payload = {
            "agent_code": "TEST-AGENT-001",
            "agent_name": "Test Triage Agent",
            "agent_type": "TRIAGE",
            "description": "Testing agent functionality",
            "department_id": self.department_id,
            "owner_user_id": self.user_id,
            "execution_mode": "RECOMMEND_ONLY",
            "risk_level": "MEDIUM",
            "confidence_threshold": 0.85,
            "status": "DRAFT",
            "capabilities_json": {},
            "metadata_json": {}
        }
        agent_response = self.client.post("/api/registry/agents", json=agent_payload, headers=self.headers)
        self.assertEqual(agent_response.status_code, 200, f"Failed to create AI Agent: {agent_response.text}")
        agent_data = agent_response.json()
        self.assertEqual(agent_data["status"], "success")
        self.assertEqual(agent_data["data"]["agent_code"], "TEST-AGENT-001")
        self.created_agent_ids.append(agent_data["data"]["id"])

        # 3. Create Tool
        tool_payload = {
            "tool_code": "TEST-TOOL-001",
            "tool_name": "Test Webhook Tool",
            "tool_category": "WEBHOOK",
            "access_mode": "EXECUTE",
            "owner_user_id": self.user_id,
            "sensitivity_level": "CONFIDENTIAL",
            "allowed_operations_json": ["post", "get"],
            "endpoint_reference": "https://api.test.local/webhook",
            "status": "ACTIVE",
            "metadata_json": {}
        }
        tool_response = self.client.post("/api/registry/tools", json=tool_payload, headers=self.headers)
        self.assertEqual(tool_response.status_code, 200, f"Failed to create Tool: {tool_response.text}")
        tool_data = tool_response.json()
        self.assertEqual(tool_data["status"], "success")
        self.assertEqual(tool_data["data"]["tool_code"], "TEST-TOOL-001")
        self.created_tool_ids.append(tool_data["data"]["id"])

        # 4. Create Workflow
        workflow_payload = {
            "workflow_code": "TEST-WF-001",
            "workflow_name": "Test Risk Review Workflow",
            "workflow_type": "RISK_REVIEW",
            "department_id": self.department_id,
            "owner_user_id": self.user_id,
            "description": "Testing workflow functionality",
            "approval_required": True,
            "business_criticality": "HIGH",
            "status": "DRAFT",
            "steps_json": [],
            "metadata_json": {}
        }
        workflow_response = self.client.post("/api/registry/workflows", json=workflow_payload, headers=self.headers)
        self.assertEqual(workflow_response.status_code, 200, f"Failed to create Workflow: {workflow_response.text}")
        workflow_data = workflow_response.json()
        self.assertEqual(workflow_data["status"], "success")
        self.assertEqual(workflow_data["data"]["workflow_code"], "TEST-WF-001")
        self.created_workflow_ids.append(workflow_data["data"]["id"])

        # 5. Retrieve Lists and verify they show what was created
        # List Models
        models_list = self.client.get("/api/registry/models", headers=self.headers)
        self.assertEqual(models_list.status_code, 200)
        self.assertIn("TEST-MODEL-001", [m["model_code"] for m in models_list.json()["data"]["items"]])

        # List Agents
        agents_list = self.client.get("/api/registry/agents", headers=self.headers)
        self.assertEqual(agents_list.status_code, 200)
        self.assertIn("TEST-AGENT-001", [a["agent_code"] for a in agents_list.json()["data"]["items"]])

        # List Tools
        tools_list = self.client.get("/api/registry/tools", headers=self.headers)
        self.assertEqual(tools_list.status_code, 200)
        self.assertIn("TEST-TOOL-001", [t["tool_code"] for t in tools_list.json()["data"]["items"]])

        # List Workflows
        workflows_list = self.client.get("/api/registry/workflows", headers=self.headers)
        self.assertEqual(workflows_list.status_code, 200)
        self.assertIn("TEST-WF-001", [w["workflow_code"] for w in workflows_list.json()["data"]["items"]])

        # 6. Check Registry Summary to confirm count tracking
        summary_response = self.client.get("/api/registry/summary", headers=self.headers)
        self.assertEqual(summary_response.status_code, 200)
        summary_data = summary_response.json()["data"]
        self.assertTrue(summary_data["models"]["total"] > 0)
        self.assertTrue(summary_data["agents"]["total"] > 0)
        self.assertTrue(summary_data["tools"]["total"] > 0)
        self.assertTrue(summary_data["workflows"]["total"] > 0)

    def test_model_filtering_combinations(self):
        # 1. Create Model A (LLM, LOW risk)
        model_a_payload = {
            "model_code": "FILTER-MODEL-A",
            "model_name": "Filter Model A LLM",
            "model_type": "LLM",
            "provider": "OpenAI",
            "version": "gpt-4",
            "purpose": "Filter testing model A",
            "department_id": self.department_id,
            "owner_user_id": self.user_id,
            "risk_level": "LOW",
            "deployment_environment": "staging",
            "status": "DRAFT",
            "metadata_json": {}
        }
        res_a = self.client.post("/api/registry/models", json=model_a_payload, headers=self.headers)
        self.assertEqual(res_a.status_code, 200)
        self.created_model_ids.append(res_a.json()["data"]["id"])

        # 2. Create Model B (ML, HIGH risk)
        model_b_payload = {
            "model_code": "FILTER-MODEL-B",
            "model_name": "Filter Model B ML",
            "model_type": "ML",
            "provider": "Scikit-Learn",
            "version": "v1.0",
            "purpose": "Filter testing model B",
            "department_id": self.department_id,
            "owner_user_id": self.user_id,
            "risk_level": "HIGH",
            "deployment_environment": "staging",
            "status": "DRAFT",
            "metadata_json": {}
        }
        res_b = self.client.post("/api/registry/models", json=model_b_payload, headers=self.headers)
        self.assertEqual(res_b.status_code, 200)
        self.created_model_ids.append(res_b.json()["data"]["id"])

        # 3. Test filtering by model_type=LLM
        res = self.client.get("/api/registry/models?model_type=LLM", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        items = res.json()["data"]["items"]
        codes = [item["model_code"] for item in items]
        self.assertIn("FILTER-MODEL-A", codes)
        self.assertNotIn("FILTER-MODEL-B", codes)

        # 4. Test filtering by model_type=ML
        res = self.client.get("/api/registry/models?model_type=ML", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        items = res.json()["data"]["items"]
        codes = [item["model_code"] for item in items]
        self.assertIn("FILTER-MODEL-B", codes)
        self.assertNotIn("FILTER-MODEL-A", codes)

        # 5. Test filtering by risk_level=LOW
        res = self.client.get("/api/registry/models?risk_level=LOW", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        items = res.json()["data"]["items"]
        codes = [item["model_code"] for item in items]
        self.assertIn("FILTER-MODEL-A", codes)
        self.assertNotIn("FILTER-MODEL-B", codes)

        # 6. Test filtering by risk_level=HIGH
        res = self.client.get("/api/registry/models?risk_level=HIGH", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        items = res.json()["data"]["items"]
        codes = [item["model_code"] for item in items]
        self.assertIn("FILTER-MODEL-B", codes)
        self.assertNotIn("FILTER-MODEL-A", codes)

        # 7. Test filtering by status=DRAFT
        res = self.client.get("/api/registry/models?status=DRAFT", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        items = res.json()["data"]["items"]
        codes = [item["model_code"] for item in items]
        self.assertIn("FILTER-MODEL-A", codes)
        self.assertIn("FILTER-MODEL-B", codes)

if __name__ == "__main__":
    unittest.main()

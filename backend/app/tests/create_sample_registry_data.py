import sys
import os
from fastapi.testclient import TestClient

# Add the backend directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from app.main import app

def create_sample_data():
    client = TestClient(app)
    
    # 1. Login to retrieve access token
    print("Logging in...")
    login_res = client.post(
        "/api/auth/login",
        data={"username": "admin@guardianiq.com", "password": "Admin@1234!"}
    )
    if login_res.status_code != 200:
        print(f"Login failed: {login_res.text}")
        return
        
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("Logged in successfully!")

    # Helper function to get or create
    def get_or_create(endpoint_path, entity_type, list_field_key, code_or_email_key, payload):
        code_value = payload[code_or_email_key]
        print(f"Checking if {entity_type} '{code_value}' exists...")
        
        # List existing entities
        list_res = client.get(f"{endpoint_path}?page_size=100", headers=headers)
        if list_res.status_code != 200:
            print(f"Failed to list {entity_type}: {list_res.text}")
            sys.exit(1)
            
        items = list_res.json()["data"]["items"]
        existing = next((item for item in items if item[code_or_email_key] == code_value), None)
        
        if existing:
            print(f"{entity_type} '{code_value}' already exists with ID: {existing['id']}")
            return existing["id"]
            
        print(f"Creating new {entity_type} '{code_value}'...")
        create_res = client.post(endpoint_path, json=payload, headers=headers)
        if create_res.status_code != 200:
            print(f"Failed to create {entity_type} '{code_value}': {create_res.text}")
            sys.exit(1)
            
        new_entity = create_res.json()["data"]
        print(f"Successfully created {entity_type} '{code_value}' with ID: {new_entity['id']}")
        return new_entity["id"]

    # 1. Department
    dept_payload = {
        "department_code": "CLINICAL_ANALYTICS",
        "department_name": "Clinical Analytics & Insights",
        "status": "ACTIVE",
        "metadata_json": {"hospital_branch": "CareShield Main Campus", "cost_center": "CC-9012"}
    }
    dept_id = get_or_create(
        "/api/registry/departments",
        "Department",
        "items",
        "department_code",
        dept_payload
    )

    # 2. Role
    role_payload = {
        "role_code": "CLINICAL_DATA_ANALYST",
        "role_name": "Clinical Data Analyst",
        "role_type": "BUSINESS",
        "permissions_json": {"view_patient_data": True, "run_risk_analysis": True},
        "status": "ACTIVE"
    }
    role_id = get_or_create(
        "/api/registry/roles",
        "Role",
        "items",
        "role_code",
        role_payload
    )

    # 3. User
    user_payload = {
        "email": "turing.alan@careshield.com",
        "full_name": "Dr. Alan Turing",
        "department_id": dept_id,
        "role_id": role_id,
        "approval_limit_level": "L2",
        "status": "ACTIVE"
    }
    user_id = get_or_create(
        "/api/registry/users",
        "User",
        "items",
        "email",
        user_payload
    )

    # 4. Data Source
    datasource_payload = {
        "source_code": "CLINICAL_EHR_REPLICA",
        "source_name": "CareShield EHR Read Replica",
        "source_type": "DATABASE",
        "owner_user_id": user_id,
        "department_id": dept_id,
        "classification": "RESTRICTED",
        "sensitivity_level": "CRITICAL",
        "region": "us-east-2",
        "contains_pii": True,
        "retention_policy": "HIPAA_7_YEARS",
        "connection_reference": "postgresql://ehr-read-replica.careshield.internal:5432/patient_records",
        "status": "ACTIVE",
        "metadata_json": {"compliance_tags": ["HIPAA", "HITRUST"], "last_sync": "2026-06-04"}
    }
    datasource_id = get_or_create(
        "/api/registry/data-sources",
        "Data Source",
        "items",
        "source_code",
        datasource_payload
    )

    # 5. AI Model
    model_payload = {
        "model_code": "CLINICAL_NLP_DIAGNOSIS",
        "model_name": "Clinical NLP Diagnosis Classifier",
        "model_type": "CLASSIFIER",
        "version": "v3.1.2",
        "purpose": "Extracting clinical entities and diagnostics from unstructured physician notes.",
        "owner_user_id": user_id,
        "department_id": dept_id,
        "risk_level": "HIGH",
        "deployment_environment": "K8S_CLINICAL_PROD",
        "status": "ACTIVE",
        "metadata_json": {"base_model": "Llama-3-8B-Instruct", "f1_score": 0.945}
    }
    model_id = get_or_create(
        "/api/registry/models",
        "AI Model",
        "items",
        "model_code",
        model_payload
    )

    # 6. AI Agent
    agent_payload = {
        "agent_code": "CLINICAL_TRIAGE_BOT",
        "agent_name": "Clinical Triage Recommendation Agent",
        "agent_type": "TRIAGE",
        "description": "Recommends department assignment and urgency triage level based on EHR notes.",
        "owner_user_id": user_id,
        "department_id": dept_id,
        "execution_mode": "RECOMMEND_ONLY",
        "risk_level": "HIGH",
        "confidence_threshold": 90.0,
        "status": "ACTIVE",
        "capabilities_json": {"supported_specialties": ["Cardiology", "Neurology", "General Medicine"]},
        "metadata_json": {"audit_frequency": "weekly"}
    }
    agent_id = get_or_create(
        "/api/registry/agents",
        "AI Agent",
        "items",
        "agent_code",
        agent_payload
    )

    # 7. Tool
    tool_payload = {
        "tool_code": "CARESHIELD_HL7_PUBLISHER",
        "tool_name": "CareShield HL7 Event Publisher Tool",
        "tool_category": "WEBHOOK",
        "access_mode": "EXECUTE",
        "owner_user_id": user_id,
        "sensitivity_level": "HIGH",
        "allowed_operations_json": ["publish_hl7_event", "validate_schema"],
        "endpoint_reference": "https://hl7.careshield.internal/v1/publish",
        "status": "ACTIVE",
        "metadata_json": {"payload_format": "HL7_v2"}
    }
    tool_id = get_or_create(
        "/api/registry/tools",
        "Tool",
        "items",
        "tool_code",
        tool_payload
    )

    # 8. Workflow
    workflow_payload = {
        "workflow_code": "CLINICAL_REFERRAL_TRIAGE",
        "workflow_name": "Clinical Patient Referral Triage Workflow",
        "workflow_type": "RISK_REVIEW",
        "department_id": dept_id,
        "owner_user_id": user_id,
        "description": "Automated processing pipeline for classifying clinical patient referral files.",
        "approval_required": True,
        "business_criticality": "HIGH",
        "status": "ACTIVE",
        "steps_json": [
            {"step_name": "Read EHR File", "description": "Triggered when new referral is added to EHR database"},
            {"step_name": "Extract Symptoms", "description": "Run Clinical NLP Classifier on the notes"},
            {"step_name": "Calculate Triage Level", "description": "Clinical Triage Agent recommends triage level"},
            {"step_name": "Publish HL7 Event", "description": "Publish formatted event to CareShield HL7 server for department scheduling"}
        ],
        "metadata_json": {"sla_hours": 4}
    }
    workflow_id = get_or_create(
        "/api/registry/workflows",
        "Workflow",
        "items",
        "workflow_code",
        workflow_payload
    )

    # 9. Relationships
    relationships = [
        # AGENT (CLINICAL_TRIAGE_BOT) -> USES -> MODEL (CLINICAL_NLP_DIAGNOSIS)
        {
            "source_entity_type": "AGENT",
            "source_entity_id": agent_id,
            "relationship_type": "USES",
            "target_entity_type": "MODEL",
            "target_entity_id": model_id
        },
        # AGENT (CLINICAL_TRIAGE_BOT) -> USES -> TOOL (CARESHIELD_HL7_PUBLISHER)
        {
            "source_entity_type": "AGENT",
            "source_entity_id": agent_id,
            "relationship_type": "USES",
            "target_entity_type": "TOOL",
            "target_entity_id": tool_id
        },
        # WORKFLOW (CLINICAL_REFERRAL_TRIAGE) -> USES -> DATA_SOURCE (CLINICAL_EHR_REPLICA)
        {
            "source_entity_type": "WORKFLOW",
            "source_entity_id": workflow_id,
            "relationship_type": "USES",
            "target_entity_type": "DATA_SOURCE",
            "target_entity_id": datasource_id
        }
    ]

    for rel in relationships:
        print(f"Checking relationship: {rel['source_entity_type']} ({rel['source_entity_id']}) -> {rel['relationship_type']} -> {rel['target_entity_type']} ({rel['target_entity_id']})...")
        
        # Check if already exists via GET `/api/registry/relationships`
        rel_list_res = client.get(
            f"/api/registry/relationships?entity_type={rel['source_entity_type']}&entity_id={rel['source_entity_id']}",
            headers=headers
        )
        if rel_list_res.status_code != 200:
            print(f"Failed to fetch relationships: {rel_list_res.text}")
            sys.exit(1)
            
        existing_rels = rel_list_res.json()["data"]["outgoing"]
        duplicate = next((
            r for r in existing_rels 
            if r["relationship_type"] == rel["relationship_type"] 
            and r["other_entity_type"] == rel["target_entity_type"] 
            and r["other_entity_id"] == str(rel["target_entity_id"])
        ), None)
        
        if duplicate:
            print("Relationship already exists.")
        else:
            print("Creating relationship...")
            create_rel_res = client.post("/api/registry/relationships", json=rel, headers=headers)
            if create_rel_res.status_code != 200:
                print(f"Failed to create relationship: {create_rel_res.text}")
                sys.exit(1)
            print("Relationship successfully created.")

    print("\n--- SAMPLE DATA REGISTRATION REPORT ---")
    print(f"Department ID: {dept_id}")
    print(f"Role ID:       {role_id}")
    print(f"User ID:       {user_id}")
    print(f"Data Source ID:{datasource_id}")
    print(f"AI Model ID:   {model_id}")
    print(f"AI Agent ID:   {agent_id}")
    print(f"Tool ID:       {tool_id}")
    print(f"Workflow ID:   {workflow_id}")
    print("All entities are registered in the DB and will persist for frontend validation.")

if __name__ == "__main__":
    create_sample_data()

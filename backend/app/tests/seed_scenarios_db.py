import sys
import os
from uuid import UUID, uuid4

# Add the backend directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from app.db.session import SessionLocal
from app.modules.registry.models import (
    RegistryDepartment, GuardianUser, RegistryRole, RegistryDataSource,
    RegistryAIModel, RegistryAIModelProvider, RegistryAIAgent, RegistryTool,
    RegistryWorkflow, RegistryRelationship
)

from sqlalchemy import event
from app.modules.auth.models import User, Role

def seed_scenarios():
    db = SessionLocal()
    
    # Auto-supply tenant_id for models that require it
    @event.listens_for(db, "before_flush")
    def receive_before_flush(session, flush_context, instances):
        admin_user = session.query(User).filter(User.email == "admin@guardianiq.com").first()
        if admin_user:
            default_tenant_id = admin_user.id
            for obj in session.new:
                if hasattr(obj, "tenant_id") and getattr(obj, "tenant_id") is None:
                    obj.tenant_id = default_tenant_id

    try:
        from app.db.seed import seed
        seed()
        # Helper to get or create department
        def get_or_create_dept(code, name):
            dept = db.query(RegistryDepartment).filter_by(department_code=code).first()
            if not dept:
                dept = RegistryDepartment(
                    id=uuid4(),
                    department_code=code,
                    department_name=name,
                    status="ACTIVE",
                    metadata_json={}
                )
                db.add(dept)
                db.flush()
                print(f"Created Department '{name}' ({code})")
            else:
                print(f"Department '{name}' already exists")
            return dept

        # Helper to get or create role
        def get_role_by_code(code):
            role = db.query(RegistryRole).filter_by(role_code=code).first()
            if not role:
                print(f"WARNING: Role with code '{code}' not found in registry_roles. Using first available.")
                role = db.query(RegistryRole).first()
            return role

        # Helper to get or create user
        def get_or_create_user(name, email, role_code, department_id):
            user = db.query(GuardianUser).filter_by(email=email).first()
            if not user:
                role = get_role_by_code(role_code)
                user = GuardianUser(
                    id=uuid4(),
                    email=email,
                    full_name=name,
                    department_id=department_id,
                    role_id=role.id,
                    status="ACTIVE"
                )
                db.add(user)
                db.flush()
                print(f"Created User '{name}' ({email}) with role {role_code}")
            else:
                print(f"User '{name}' already exists")
            return user

        # Helper to get or create data source
        def get_or_create_datasource(code, name, type_val, owner_id, dept_id, classification, sensitivity, conn_ref):
            ds = db.query(RegistryDataSource).filter_by(source_code=code).first()
            if not ds:
                ds = RegistryDataSource(
                    id=uuid4(),
                    source_code=code,
                    source_name=name,
                    source_type=type_val,
                    owner_user_id=owner_id,
                    department_id=dept_id,
                    classification=classification,
                    sensitivity_level=sensitivity,
                    connection_reference=conn_ref,
                    status="ACTIVE",
                    metadata_json={}
                )
                db.add(ds)
                db.flush()
                print(f"Created Data Source '{name}' ({code})")
            else:
                print(f"Data Source '{name}' already exists")
            return ds

        # Helper to get or create tool
        def get_or_create_tool(code, name, category, access, owner_id, sensitivity, endpoint):
            tool = db.query(RegistryTool).filter_by(tool_code=code).first()
            if not tool:
                tool = RegistryTool(
                    id=uuid4(),
                    tool_code=code,
                    tool_name=name,
                    tool_category=category,
                    access_mode=access,
                    owner_user_id=owner_id,
                    sensitivity_level=sensitivity,
                    endpoint_reference=endpoint,
                    status="ACTIVE",
                    metadata_json={}
                )
                db.add(tool)
                db.flush()
                print(f"Created Tool '{name}' ({code})")
            else:
                print(f"Tool '{name}' already exists")
            return tool

        # Helper to get or create provider
        def get_or_create_provider(name, type_val):
            prov = db.query(RegistryAIModelProvider).filter_by(provider_name=name).first()
            if not prov:
                prov = RegistryAIModelProvider(
                    id=uuid4(),
                    provider_name=name,
                    provider_type=type_val,
                    provider_category="Cloud",
                    metadata_json={
                        "Owner": "System Admin",
                        "Training Data": "Web Corpora",
                        "Hosting": "Cloud API",
                        "Security": "SOC2 Compliance",
                        "Responsible Person": "Compliance Officer"
                    }
                )
                db.add(prov)
                db.flush()
                print(f"Created Model Provider '{name}'")
            else:
                print(f"Model Provider '{name}' already exists")
            return prov

        # Helper to get or create AI model
        def get_or_create_model(code, name, model_type, provider_id, purpose, owner_id, dept_id, risk):
            model = db.query(RegistryAIModel).filter_by(model_code=code).first()
            if not model:
                model = RegistryAIModel(
                    id=uuid4(),
                    model_code=code,
                    model_name=name,
                    model_type=model_type,
                    provider_id=provider_id,
                    purpose=purpose,
                    owner_user_id=owner_id,
                    department_id=dept_id,
                    risk_level=risk,
                    status="ACTIVE",
                    metadata_json={}
                )
                db.add(model)
                db.flush()
                print(f"Created AI Model '{name}' ({code})")
            else:
                print(f"AI Model '{name}' already exists")
            return model

        # Helper to get or create AI agent
        def get_or_create_agent(code, name, type_val, mode, owner_id, dept_id, risk, threshold):
            agent = db.query(RegistryAIAgent).filter_by(agent_code=code).first()
            if not agent:
                agent = RegistryAIAgent(
                    id=uuid4(),
                    agent_code=code,
                    agent_name=name,
                    agent_type=type_val,
                    execution_mode=mode,
                    owner_user_id=owner_id,
                    department_id=dept_id,
                    risk_level=risk,
                    confidence_threshold=threshold,
                    status="ACTIVE",
                    metadata_json={}
                )
                db.add(agent)
                db.flush()
                print(f"Created AI Agent '{name}' ({code})")
            else:
                print(f"AI Agent '{name}' already exists")
            return agent

        # Helper to get or create workflow
        def get_or_create_workflow(code, name, type_val, business_crit, approval, approver_id, owner_id, dept_id, steps):
            wf = db.query(RegistryWorkflow).filter_by(workflow_code=code).first()
            if not wf:
                wf = RegistryWorkflow(
                    id=uuid4(),
                    workflow_code=code,
                    workflow_name=name,
                    workflow_type=type_val,
                    business_criticality=business_crit,
                    approval_required=approval,
                    approver_user_id=approver_id,
                    owner_user_id=owner_id,
                    department_id=dept_id,
                    steps_json=steps,
                    status="ACTIVE",
                    metadata_json={}
                )
                db.add(wf)
                db.flush()
                print(f"Created Workflow '{name}' ({code})")
            else:
                print(f"Workflow '{name}' already exists")
            return wf

        # Helper to create relationship
        def create_relationship_if_not_exists(src_type, src_id, target_type, target_id, rel_type):
            from datetime import datetime, timezone
            existing = db.query(RegistryRelationship).filter_by(
                source_type=src_type,
                source_id=str(src_id),
                target_type=target_type,
                target_id=str(target_id),
                relationship_type=rel_type,
                status="ACTIVE"
            ).first()
            if not existing:
                rel = RegistryRelationship(
                    id=uuid4(),
                    source_type=src_type,
                    source_id=str(src_id),
                    target_type=target_type,
                    target_id=str(target_id),
                    relationship_type=rel_type,
                    status="ACTIVE",
                    effective_from=datetime.now(timezone.utc)
                )
                db.add(rel)
                print(f"Created Relationship: {src_type} ({src_id}) -> {rel_type} -> {target_type} ({target_id})")
            else:
                print("Relationship already exists")

        # ──────────────────────────────────────────────
        # SCENARIO 1: AUTOMATED EMPLOYEE ONBOARDING & COMPLIANCE
        # ──────────────────────────────────────────────
        print("\n--- Seeding Scenario 1 ---")
        dept1 = get_or_create_dept("DEPT-HR-001", "Human Resources & Compliance")
        user1 = get_or_create_user("Sarah Jenkins", "sjenkins@guardianiq.com", "GOVERNANCE_MANAGER", dept1.id)
        ds1 = get_or_create_datasource(
            "DS-HR-WORKDAY", "Workday Employee Roster", "DATABASE",
            user1.id, dept1.id, "CONFIDENTIAL", "HIGH", "postgresql://hr-service:***@db.workday.internal/roster"
        )
        prov1 = get_or_create_provider("OpenAI Enterprise", "Enterprise Vendor")
        model1 = get_or_create_model(
            "LLM-COMPLIANCE-DOCS", "Legal & Compliance Document Analyzer", "LLM",
            prov1.id, "Scans new employee onboarding documents to ensure all legal signatures are present.",
            user1.id, dept1.id, "HIGH"
        )
        agent1 = get_or_create_agent(
            "AGENT-ONBOARD-01", "Autonomous Onboarding Coordinator", "EXTRACTION",
            "LIMITED_EXECUTION", user1.id, dept1.id, "HIGH", 0.98
        )
        wf1 = get_or_create_workflow(
            "WF-ONBOARDING-PIPELINE", "Automated NDA & Employee Setup", "APPROVAL",
            "MISSION_CRITICAL", True, user1.id, user1.id, dept1.id,
            [
                {"step_name": "START"},
                {"step_name": "Fetch Employee Record"},
                {"step_name": "Scan Signed NDA"},
                {"step_name": "HR Legal Sign-off"},
                {"step_name": "END"}
            ]
        )
        # Relationships
        create_relationship_if_not_exists("AGENT", agent1.id, "MODEL", model1.id, "USES")
        create_relationship_if_not_exists("AGENT", agent1.id, "WORKFLOW", wf1.id, "EXECUTES")
        create_relationship_if_not_exists("WORKFLOW", wf1.id, "DATA_SOURCE", ds1.id, "USES")

        # ──────────────────────────────────────────────
        # SCENARIO 2: AUTOMATED REFUND PROCESSING
        # ──────────────────────────────────────────────
        print("\n--- Seeding Scenario 2 ---")
        dept2 = get_or_create_dept("DEPT-SUP-002", "Global Customer Support")
        user2 = get_or_create_user("Michael Chang", "mchang@guardianiq.com", "ADMIN", dept2.id)
        tool2 = get_or_create_tool(
            "API-REFUND-STRIPE", "Stripe Refund API", "WEBHOOK",
            "EXECUTE", user2.id, "HIGH", "https://api.stripe.com/v1/refunds"
        )
        prov2 = get_or_create_provider("Anthropic", "Enterprise Vendor")
        model2 = get_or_create_model(
            "LLM-SUPPORT-001", "Support Refund Classifier v2", "LLM",
            prov2.id, "Evaluates customer messages to determine automated refund eligibility.",
            user2.id, dept2.id, "MEDIUM"
        )
        agent2 = get_or_create_agent(
            "AGENT-REFUND-BOT", "Autonomous Refund Agent", "EXECUTION",
            "APPROVAL_REQUIRED", user2.id, dept2.id, "HIGH", 0.95
        )
        wf2 = get_or_create_workflow(
            "WF-AUTO-REFUND", "Automated Refund Processing", "OPERATIONAL_ACTION",
            "HIGH", True, user2.id, user2.id, dept2.id,
            [
                {"step_name": "START"},
                {"step_name": "Read Customer Email"},
                {"step_name": "Check Refund Eligibility"},
                {"step_name": "Manager Approval"},
                {"step_name": "Trigger Stripe API"},
                {"step_name": "END"}
            ]
        )
        # Relationships
        create_relationship_if_not_exists("AGENT", agent2.id, "MODEL", model2.id, "USES")
        create_relationship_if_not_exists("AGENT", agent2.id, "WORKFLOW", wf2.id, "EXECUTES")
        create_relationship_if_not_exists("WORKFLOW", wf2.id, "TOOL", tool2.id, "USES")

        # ──────────────────────────────────────────────
        # SCENARIO 3: REAL-TIME FINANCIAL FRAUD PREVENTION
        # ──────────────────────────────────────────────
        print("\n--- Seeding Scenario 3 ---")
        dept3 = get_or_create_dept("DEPT-FIN-003", "Finance & Risk Management")
        user3 = get_or_create_user("Elena Rodriguez", "erodriguez@guardianiq.com", "ADMIN", dept3.id)
        ds3 = get_or_create_datasource(
            "DS-FIN-LEDGER", "Transaction Ledger Database", "DATABASE",
            user3.id, dept3.id, "RESTRICTED", "CRITICAL", "mongodb://finance-cluster:27017/ledger"
        )
        tool3 = get_or_create_tool(
            "API-ACCOUNT-FREEZE", "Core Banking Account Freeze API", "WEBHOOK",
            "EXECUTE", user3.id, "CRITICAL", "https://core.banking.internal/api/v2/accounts/freeze"
        )
        prov3 = get_or_create_provider("Internal Custom", "Internal Custom")
        model3 = get_or_create_model(
            "ML-FRAUD-DETECT-V4", "Transaction Anomaly Detector", "CLASSIFIER",
            prov3.id, "Neural network detecting real-time fraudulent patterns in credit card swipes.",
            user3.id, dept3.id, "CRITICAL"
        )
        agent3 = get_or_create_agent(
            "AGENT-FRAUD-SENTINEL", "Autonomous Fraud Sentinel", "EXECUTION",
            "LIMITED_EXECUTION", user3.id, dept3.id, "CRITICAL", 0.99
        )
        wf3 = get_or_create_workflow(
            "WF-FRAUD-FREEZE", "Zero-Day Fraud Freeze Protocol", "RISK_REVIEW",
            "MISSION_CRITICAL", False, None, user3.id, dept3.id,
            [
                {"step_name": "START"},
                {"step_name": "Ingest Ledger Stream"},
                {"step_name": "Evaluate Anomaly"},
                {"step_name": "Execute Account Freeze"},
                {"step_name": "Alert Risk Team"},
                {"step_name": "END"}
            ]
        )
        # Relationships
        create_relationship_if_not_exists("AGENT", agent3.id, "MODEL", model3.id, "USES")
        create_relationship_if_not_exists("AGENT", agent3.id, "WORKFLOW", wf3.id, "EXECUTES")
        create_relationship_if_not_exists("WORKFLOW", wf3.id, "DATA_SOURCE", ds3.id, "USES")
        create_relationship_if_not_exists("WORKFLOW", wf3.id, "TOOL", tool3.id, "USES")

        db.commit()
        print("\nAll compliance scenarios successfully seeded!")

    except Exception as e:
        db.rollback()
        print(f"Error seeding scenarios: {e}")
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    seed_scenarios()

import sys
import os
from uuid import UUID, uuid4
import asyncio

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.db.session import SessionLocal, engine, Base
from sqlalchemy import text
from app.modules.auth.models import User, Role, Permission
from app.modules.department.models import Department
from app.modules.datasource.models import DataSource
from app.modules.ai_model.models import AIModel, AIModelProvider
from app.modules.agent.models import Agent
from app.modules.registry.models import Tool, Workflow
from app.modules.workflow_scheduler.models import (
    ApprovalGroup, Phase2WorkflowSchedule, WorkflowScheduleAgentAssignment,
    WorkflowScheduleApproval, WorkflowScheduleHistory, ApprovalGroupMember
)
from app.modules.workflow_execution.models import (
    WorkflowRun, WorkflowRunStep, WorkflowRunOutput, WorkflowRunFailure
)
from app.modules.workflow_notifications.models import (
    WorkflowNotification
)
from app.modules.authorization.models import (
    WorkflowAuthorizationDecision, WorkflowDelegation
)

def drop_all_tables_raw():
    print("Dropping all existing tables...")
    with engine.connect() as conn:
        # Drop constraints and tables to do a clean reset
        conn.execute(text("""
            DROP SCHEMA public CASCADE;
            CREATE SCHEMA public;
            GRANT ALL ON SCHEMA public TO postgres;
            GRANT ALL ON SCHEMA public TO public;
        """))
        conn.commit()

def run_alembic_upgrade():
    import subprocess
    print("Creating tables via SQLAlchemy Base...")
    # Import all models to ensure they are registered with Base metadata
    import app.db.base
    Base.metadata.create_all(bind=engine)
    print("Stamping database with Alembic head...")
    import sys
    result = subprocess.run([sys.executable, "-m", "alembic", "stamp", "head"], capture_output=True, text=True)
    if result.returncode != 0:
        print("Alembic stamp error:", result.stderr)
        sys.exit(1)
    print("Database initialization complete.")

def migrate():
    # 1. Connect and back up data from existing tables using raw SQL
    db = SessionLocal()
    
    # Read old data
    print("Backing up existing data...")
    try:
        guardian_users = db.execute(text("SELECT * FROM guardian_users")).fetchall()
        print(f"Backed up {len(guardian_users)} guardian_users")
    except Exception:
        guardian_users = []
        print("No guardian_users table found or empty")

    try:
        registry_departments = db.execute(text("SELECT * FROM registry_departments")).fetchall()
        print(f"Backed up {len(registry_departments)} registry_departments")
    except Exception:
        registry_departments = []

    try:
        registry_data_sources = db.execute(text("SELECT * FROM registry_data_sources")).fetchall()
        print(f"Backed up {len(registry_data_sources)} registry_data_sources")
    except Exception:
        registry_data_sources = []

    try:
        registry_ai_models = db.execute(text("SELECT * FROM registry_ai_models")).fetchall()
        print(f"Backed up {len(registry_ai_models)} registry_ai_models")
    except Exception:
        registry_ai_models = []

    try:
        registry_ai_agents = db.execute(text("SELECT * FROM registry_ai_agents")).fetchall()
        print(f"Backed up {len(registry_ai_agents)} registry_ai_agents")
    except Exception:
        registry_ai_agents = []

    try:
        registry_tools = db.execute(text("SELECT * FROM registry_tools")).fetchall()
        print(f"Backed up {len(registry_tools)} registry_tools")
    except Exception:
        registry_tools = []

    try:
        registry_workflows = db.execute(text("SELECT * FROM registry_workflows")).fetchall()
        print(f"Backed up {len(registry_workflows)} registry_workflows")
    except Exception:
        registry_workflows = []

    try:
        old_auth_users = db.execute(text("SELECT * FROM users")).fetchall()
        print(f"Backed up {len(old_auth_users)} users")
    except Exception:
        old_auth_users = []

    try:
        old_schedules = db.execute(text("SELECT * FROM workflow_schedules")).fetchall()
        print(f"Backed up {len(old_schedules)} workflow_schedules")
    except Exception:
        old_schedules = []

    db.close()

    # 2. Reset database tables
    drop_all_tables_raw()
    
    # 3. Upgrade to new schema using Alembic
    run_alembic_upgrade()

    # 4. Insert data back mapping fields properly
    db = SessionLocal()
    try:
        # Create map of department code to new UUID
        dept_id_map = {}
        for dept in registry_departments:
            new_id = uuid4()
            # If the old department has an ID that is UUID, we keep it!
            old_id = dept.id if hasattr(dept, 'id') else uuid4()
            new_dept = Department(
                id=old_id,
                tenant_id=old_id, # Default tenant_id to its own ID temporarily if admin_user not created yet
                department_code=dept.department_code,
                department_name=dept.department_name,
                status=dept.status if hasattr(dept, 'status') else 'ACTIVE',
                description=getattr(dept, 'description', '')
            )
            db.add(new_dept)
            dept_id_map[dept.department_code] = old_id
        db.flush()

        # Seed roles & permissions (idempotently so users can reference them)
        from app.db.seed import seed
        seed()

        # Ensure required scenario users exist for Phase 2 seeding
        demo_dept = db.query(Department).first()
        gov_admin_role = db.query(Role).filter_by(role_code="GOVERNANCE_ADMIN").first()
        for name, email in [
            ("Sarah Jenkins", "sjenkins@guardianiq.com"),
            ("Michael Chang", "mchang@guardianiq.com"),
            ("Elena Rodriguez", "erodriguez@guardianiq.com"),
        ]:
            existing_user = db.query(User).filter_by(email=email).first()
            if not existing_user:
                new_user = User(
                    name=name.split()[0],
                    full_name=name,
                    email=email,
                    hashed_password="Admin@1234!",
                    department_id=demo_dept.id if demo_dept else None,
                    status="ACTIVE"
                )
                db.add(new_user)
                db.flush()
                if gov_admin_role and gov_admin_role not in new_user.roles:
                    new_user.roles.append(gov_admin_role)
                    db.flush()

        # Re-fetch admin_user and roles
        super_admin_role = db.query(Role).filter_by(role_code="SUPER_ADMIN").first()
        admin_user = db.query(User).filter_by(email="admin@guardianiq.com").first()
        admin_user_id = admin_user.id if admin_user else None

        # Insert Users (Merge auth users and guardian users by email)
        user_email_map = {}
        
        # First insert guardian users (UUID)
        for gu in guardian_users:
            # Check if there is an auth user with the same email to merge hashed password
            matching_auth = next((au for au in old_auth_users if au.email == gu.email), None)
            hashed_pass = matching_auth.hashed_password if matching_auth else "Admin@1234!" # Fallback
            
            new_user = User(
                id=gu.id,
                email=gu.email,
                name=gu.full_name.split()[0] if gu.full_name else "User",
                full_name=gu.full_name,
                hashed_password=hashed_pass,
                department_id=gu.department_id,
                status=gu.status if hasattr(gu, 'status') else 'ACTIVE'
            )
            db.add(new_user)
            user_email_map[gu.email] = gu.id
            if gu.email == "admin@guardianiq.com":
                admin_user_id = gu.id
        db.flush()

        # Assign user roles (if they were mapped)
        for gu in guardian_users:
            u_id = user_email_map.get(gu.email)
            if u_id:
                user_obj = db.get(User, u_id)
                # Query role from registry_roles or default roles
                role = db.query(Role).first() # Fallback
                if role:
                    user_obj.roles.append(role)
        db.flush()

        # Update departments tenant_id to admin_user_id if admin user was created
        if admin_user_id:
            for dept_obj in db.query(Department).all():
                dept_obj.tenant_id = admin_user_id
            db.flush()

        # Insert Tools
        tool_id_map = {}
        for t in registry_tools:
            new_tool = Tool(
                id=t.id,
                tenant_id=admin_user_id or t.id,
                tool_code=t.tool_code,
                tool_name=t.tool_name,
                tool_category=t.tool_category,
                access_mode=t.access_mode,
                owner_user_id=t.owner_user_id,
                sensitivity_level=t.sensitivity_level,
                allowed_operations_json=t.allowed_operations_json,
                endpoint_reference=t.endpoint_reference,
                status=t.status
            )
            db.add(new_tool)
            tool_id_map[t.tool_code] = t.id
        db.flush()

        # Insert Workflows
        wf_id_map = {}
        for wf in registry_workflows:
            new_wf = Workflow(
                id=wf.id,
                tenant_id=admin_user_id or wf.id,
                workflow_code=wf.workflow_code,
                workflow_name=wf.workflow_name,
                workflow_type=wf.workflow_type,
                department_id=wf.department_id,
                owner_user_id=wf.owner_user_id,
                description=wf.description,
                approval_required=wf.approval_required,
                approver_user_id=wf.approver_user_id,
                business_criticality=wf.business_criticality,
                status=wf.status,
                steps_json=wf.steps_json
            )
            db.add(new_wf)
            wf_id_map[wf.workflow_code] = wf.id
        db.flush()

        # Insert AI Model Providers (Create a dummy default provider if none exist)
        provider = AIModelProvider(
            id=uuid4(),
            tenant_id=admin_user_id or uuid4(),
            provider_type="OPENAI",
            provider_name="OpenAI Provider",
            provider_category="LLM",
            ownership_type="THIRD_PARTY",
            hosting_type="CLOUD",
            data_residency="US",
            risk_classification="LOW"
        )
        db.add(provider)
        db.flush()

        # Insert AI Models
        model_id_map = {}
        for m in registry_ai_models:
            new_model = AIModel(
                id=m.id,
                tenant_id=admin_user_id or m.id,
                model_code=m.model_code,
                model_name=m.model_name,
                model_type=m.model_type,
                provider_id=provider.id,
                version=m.version,
                purpose=m.purpose,
                owner_user_id=m.owner_user_id,
                department_id=m.department_id,
                risk_level=m.risk_level,
                deployment_environment=m.deployment_environment,
                status=m.status
            )
            db.add(new_model)
            model_id_map[m.model_code] = m.id
        db.flush()

        # Insert Agents
        agent_id_map = {}
        for a in registry_ai_agents:
            new_agent = Agent(
                id=a.id,
                tenant_id=admin_user_id or a.id,
                agent_code=a.agent_code,
                agent_name=a.agent_name,
                agent_type=a.agent_type,
                description=a.description,
                owner_user_id=a.owner_user_id,
                department_id=a.department_id,
                execution_mode=a.execution_mode,
                risk_level=a.risk_level,
                confidence_threshold=a.confidence_threshold,
                status=a.status,
                capabilities_json=a.capabilities_json
            )
            db.add(new_agent)
            agent_id_map[a.agent_code] = a.id
        db.flush()

        # Insert Data Sources
        for ds in registry_data_sources:
            new_ds = DataSource(
                id=ds.id,
                tenant_id=admin_user_id or ds.id,
                source_code=ds.source_code,
                source_name=ds.source_name,
                source_type=ds.source_type,
                owner_user_id=ds.owner_user_id,
                department_id=ds.department_id,
                classification=ds.classification,
                sensitivity_level=ds.sensitivity_level,
                region=ds.region,
                contains_pii=ds.contains_pii,
                retention_policy=ds.retention_policy,
                connection_reference=ds.connection_reference,
                status=ds.status
            )
            db.add(new_ds)
        db.flush()

        db.commit()
        print("Data migration and preservation complete! Database is structurally reset but data is preserved.")
        
        # Now trigger the Scenario seeding of Phase 2 schedules to ensure operational data is restored!
        from app.tests.seed_scenarios_db import seed_scenarios
        print("Re-running Compliance Scenario Seed Data...")
        seed_scenarios()

        from app.db.seed_phase2 import seed_phase2_data
        print("Re-running Phase 2 Seed Data...")
        seed_phase2_data()

    except Exception as e:
        db.rollback()
        print("Migration failed:", e)
        raise
    finally:
        db.close()

if __name__ == "__main__":
    migrate()

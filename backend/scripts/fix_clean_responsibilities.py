import sys
import os

# Add parent directory to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.db.session import SessionLocal
from app.modules.datasource.models import DataSource
from app.modules.registry.models import Tool, Workflow
from app.modules.department.models import Department
from app.modules.ai_model.models import AIModel
from app.modules.agent.models import Agent
from app.modules.relationship.models import ObjectResponsibility
from app.modules.auth.models import User
from app.modules.relationship.cache_service import MemoryCacheService
from uuid import uuid4
from datetime import datetime, timezone

def fix_responsibilities():
    db = SessionLocal()
    try:
        MemoryCacheService().clear()
        users = db.query(User).all()
        user_map = {u.id: u for u in users}
        print(f"Loaded {len(users)} users.")

        elena = next((u for u in users if "Elena" in u.name or "erodriguez" in u.email), users[0])
        michael = next((u for u in users if "Michael" in u.name or "mchang" in u.email), users[0])
        sarah_j = next((u for u in users if "sjenkins" in u.email or "Sarah" in u.name), users[0])
        sarah_c = next((u for u in users if "sarah.chen" in u.email), sarah_j)
        priya = next((u for u in users if "priya" in u.email), users[0])
        james = next((u for u in users if "james" in u.email), users[0])
        alex = next((u for u in users if "alex" in u.email), users[0])
        gov_admin = next((u for u in users if "governance" in u.email), users[0])
        comp_off = next((u for u in users if "compliance" in u.email), users[0])
        risk_mgr = next((u for u in users if "risk" in u.email), users[0])

        admin_user = db.query(User).filter(User.email == "admin@guardianiq.com").first() or users[0]
        tenant_id = admin_user.id

        # Clean invalid actor_ids from object_responsibilities
        invalid_resps = db.query(ObjectResponsibility).all()
        for r in invalid_resps:
            if r.actor_id not in user_map:
                print(f"Cleaning invalid actor_id: {r.actor_id} for {r.object_type} {r.object_id}")
                db.delete(r)
        db.commit()

        # Helper to set clean primary owner
        def set_primary_owner(obj_type, obj_id, owner_user):
            # Deactivate any existing primary owners
            existing_primaries = db.query(ObjectResponsibility).filter(
                ObjectResponsibility.tenant_id == tenant_id,
                ObjectResponsibility.object_type == obj_type.upper(),
                ObjectResponsibility.object_id == str(obj_id),
                ObjectResponsibility.responsibility_type == "OWNER",
                ObjectResponsibility.is_primary == True
            ).all()
            for p in existing_primaries:
                p.is_primary = False
                p.status = "REVOKED"

            # Create or activate target owner
            target_resp = db.query(ObjectResponsibility).filter_by(
                tenant_id=tenant_id,
                object_type=obj_type.upper(),
                object_id=str(obj_id),
                responsibility_type="OWNER",
                actor_id=str(owner_user.id)
            ).first()

            if target_resp:
                target_resp.is_primary = True
                target_resp.status = "ACTIVE"
            else:
                target_resp = ObjectResponsibility(
                    id=uuid4(),
                    tenant_id=tenant_id,
                    object_type=obj_type.upper(),
                    object_id=str(obj_id),
                    responsibility_type="OWNER",
                    actor_type="USER",
                    actor_id=str(owner_user.id),
                    is_primary=True,
                    status="ACTIVE",
                    effective_from=datetime.now(timezone.utc),
                    created_by=admin_user.id
                )
                db.add(target_resp)
            print(f"Set Primary Owner: [{obj_type.upper()}] {obj_id} -> {owner_user.name}")

        # AGENTS
        for a in db.query(Agent).all():
            n = a.agent_name.lower()
            if "fraud" in n: set_primary_owner("AGENTS", a.id, elena)
            elif "onboarding" in n: set_primary_owner("AGENTS", a.id, sarah_j)
            elif "refund" in n: set_primary_owner("AGENTS", a.id, michael)
            elif "compliance" in n: set_primary_owner("AGENTS", a.id, comp_off)
            elif "quality" in n or "sentinel" in n: set_primary_owner("AGENTS", a.id, alex)
            else: set_primary_owner("AGENTS", a.id, gov_admin)

        # AI MODELS
        for m in db.query(AIModel).all():
            n = m.model_name.lower()
            if "fraud" in n or "anomaly" in n: set_primary_owner("AI_MODELS", m.id, elena)
            elif "legal" in n or "document" in n: set_primary_owner("AI_MODELS", m.id, sarah_j)
            elif "refund" in n or "classifier" in n or "sentiment" in n: set_primary_owner("AI_MODELS", m.id, sarah_c)
            elif "governance" in n or "gpt-4o" in n: set_primary_owner("AI_MODELS", m.id, james)
            else: set_primary_owner("AI_MODELS", m.id, alex)

        # TOOLS
        for t in db.query(Tool).all():
            n = t.tool_name.lower()
            if "stripe" in n or "refund" in n: set_primary_owner("TOOLS", t.id, michael)
            elif "freeze" in n or "banking" in n: set_primary_owner("TOOLS", t.id, elena)
            elif "policy" in n: set_primary_owner("TOOLS", t.id, sarah_j)
            else: set_primary_owner("TOOLS", t.id, alex)

        # WORKFLOWS
        for w in db.query(Workflow).all():
            n = w.workflow_name.lower()
            if "fraud" in n or "freeze" in n: set_primary_owner("WORKFLOWS", w.id, elena)
            elif "nda" in n or "employee" in n: set_primary_owner("WORKFLOWS", w.id, sarah_j)
            elif "refund" in n: set_primary_owner("WORKFLOWS", w.id, michael)
            else: set_primary_owner("WORKFLOWS", w.id, comp_off)

        # DATA SOURCES
        for d in db.query(DataSource).all():
            n = d.source_name.lower()
            if "workday" in n or "employee" in n: set_primary_owner("DATA_SOURCES", d.id, sarah_j)
            elif "ledger" in n or "transaction" in n: set_primary_owner("DATA_SOURCES", d.id, elena)
            else: set_primary_owner("DATA_SOURCES", d.id, alex)

        # DEPARTMENTS
        for dep in db.query(Department).all():
            n = dep.department_name.lower()
            if "hr" in n or "human" in n: set_primary_owner("DEPARTMENTS", dep.id, sarah_j)
            elif "risk" in n or "finance" in n: set_primary_owner("DEPARTMENTS", dep.id, risk_mgr)
            elif "operations" in n: set_primary_owner("DEPARTMENTS", dep.id, michael)
            elif "engineering" in n or "data" in n: set_primary_owner("DEPARTMENTS", dep.id, alex)
            else: set_primary_owner("DEPARTMENTS", dep.id, james)

        db.commit()
        MemoryCacheService().clear()
        print("Fix responsibilities completed successfully!")
    except Exception as e:
        db.rollback()
        print(f"Error fixing responsibilities: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    fix_responsibilities()

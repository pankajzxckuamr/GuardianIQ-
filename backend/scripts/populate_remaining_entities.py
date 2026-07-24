import sys
import os

# Add parent directory to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.db.session import SessionLocal
from app.modules.relationship.models import GenericRelationship, ObjectResponsibility
from app.modules.auth.models import User
from app.modules.ai_model.models import AIModel
from app.modules.agent.models import Agent
from app.modules.registry.models import Tool, Workflow
from app.modules.datasource.models import DataSource
from app.modules.department.models import Department
from app.modules.relationship.cache_service import MemoryCacheService
from uuid import uuid4
from datetime import datetime, timezone

def populate_remaining():
    db = SessionLocal()
    try:
        MemoryCacheService().clear()
        admin_user = db.query(User).filter(User.email == "admin@guardianiq.com").first() or db.query(User).first()
        tenant_id = admin_user.id
        print(f"Populating Remaining Unpopulated Entities for Tenant: {tenant_id}")

        users = db.query(User).all()
        user_map = {u.email: u for u in users}

        def get_user(email_substr):
            return next((u for e, u in user_map.items() if email_substr in e), users[0])

        def create_rel(src_type, src_id, rel_type, tgt_type, tgt_id, scope="DEFAULT"):
            if not src_id or not tgt_id: return None
            dup = db.query(GenericRelationship).filter_by(
                tenant_id=tenant_id,
                source_type=src_type.lower(),
                source_id=str(src_id),
                relationship_type=rel_type.lower(),
                target_type=tgt_type.lower(),
                target_id=str(tgt_id),
                status="ACTIVE"
            ).first()
            if dup: return dup

            new_rel = GenericRelationship(
                id=uuid4(),
                tenant_id=tenant_id,
                source_type=src_type.lower(),
                source_id=str(src_id),
                relationship_type=rel_type.lower(),
                target_type=tgt_type.lower(),
                target_id=str(tgt_id),
                relationship_scope=scope,
                effective_from=datetime.now(timezone.utc),
                status="ACTIVE",
                metadata_json={"seeded": True}
            )
            db.add(new_rel)
            print(f"Created Rel: {src_type} ({src_id}) -[{rel_type}]-> {tgt_type} ({tgt_id})")
            return new_rel

        # Get Maps
        models = db.query(AIModel).all()
        mod_map = {m.model_name.lower(): m for m in models}
        agents = db.query(Agent).all()
        ag_map = {a.agent_name.lower(): a for a in agents}
        tools = db.query(Tool).all()
        tool_map = {t.tool_name.lower(): t for t in tools}
        workflows = db.query(Workflow).all()
        wf_map = {w.workflow_name.lower(): w for w in workflows}
        datasources = db.query(DataSource).all()
        ds_map = {d.source_name.lower(): d for d in datasources}
        departments = db.query(Department).all()
        dept_map = {d.department_name.lower(): d for d in departments}

        # -------------------------------------------------------------
        # 1. POPULATE REMAINING AI MODELS
        # -------------------------------------------------------------
        fraud_ag = next((a for k, a in ag_map.items() if "fraud" in k), agents[0])
        comp_ag = next((a for k, a in ag_map.items() if "compliance" in k), agents[0])
        test_ag = next((a for k, a in ag_map.items() if "test" in k or "execution" in k), agents[0])

        tx_ds = next((d for k, d in ds_map.items() if "ledger" in k or "transaction" in k), datasources[0])
        stream_ds = next((d for k, d in ds_map.items() if "stream" in k), datasources[0])
        cust_ds = next((d for k, d in ds_map.items() if "customer" in k), datasources[0])
        workday_ds = next((d for k, d in ds_map.items() if "workday" in k), datasources[0])

        for m_name, m in mod_map.items():
            if "gpt-3.5-turbo" in m_name:
                create_rel("agents", comp_ag.id, "uses_model", "ai_models", m.id, "FALLBACK_MODEL")
                create_rel("ai_models", m.id, "uses_data_source", "data_sources", cust_ds.id, "PROMPT_CACHE")
            elif "gpt-4o fraud analyzer" in m_name:
                create_rel("agents", fraud_ag.id, "uses_model", "ai_models", m.id, "DEEP_FRAUD_ANALYSIS")
                create_rel("ai_models", m.id, "uses_data_source", "data_sources", tx_ds.id, "TRANSACTION_LOGS")
            elif "fraudguard neural net" in m_name:
                create_rel("agents", fraud_ag.id, "uses_model", "ai_models", m.id, "REALTIME_FRAUD_SCORING")
                create_rel("ai_models", m.id, "uses_data_source", "data_sources", stream_ds.id, "LIVE_STREAM")
            elif "execution run test model" in m_name:
                create_rel("agents", test_ag.id, "uses_model", "ai_models", m.id, "UNIT_TESTING")
                create_rel("ai_models", m.id, "uses_data_source", "data_sources", workday_ds.id, "TEST_DATA")

        # -------------------------------------------------------------
        # 2. POPULATE REMAINING TOOLS
        # -------------------------------------------------------------
        for t_name, t in tool_map.items():
            if "confidential government tool" in t_name:
                create_rel("agents", comp_ag.id, "uses_tool", "tools", t.id, "GOVT_VERIFICATION")
                create_rel("tools", t.id, "uses_data_source", "data_sources", cust_ds.id, "SECURE_ID_LOOKUP")

        # -------------------------------------------------------------
        # 3. POPULATE REMAINING WORKFLOWS
        # -------------------------------------------------------------
        for w_name, w in wf_map.items():
            if "execution run test workflow" in w_name:
                create_rel("workflows", w.id, "participates_in_workflow", "agents", test_ag.id, "AUTOMATED_TEST")
                comp_wf = next((wf for k, wf in wf_map.items() if "compliance" in k), None)
                if comp_wf:
                    create_rel("workflows", w.id, "triggers_workflow", "workflows", comp_wf.id, "TEST_TRIGGER")

        # -------------------------------------------------------------
        # 4. POPULATE REMAINING DEPARTMENTS
        # -------------------------------------------------------------
        user_erodriguez = get_user("erodriguez")
        user_mchang = get_user("mchang")
        user_sjenkins = get_user("sjenkins")
        user_sarah_chen = get_user("sarah.chen")
        user_alex_kim = get_user("alex.kim")
        user_priya = get_user("priya")
        user_james = get_user("james")
        user_risk = get_user("risk")
        user_compliance = get_user("compliance")
        user_auditor = get_user("auditor")

        dept_user_links = [
            ("global customer support", user_mchang, cust_ds),
            ("sales", user_sarah_chen, cust_ds),
            ("risk", user_risk, tx_ds),
            ("compliance", user_compliance, workday_ds),
            ("finance", user_erodriguez, tx_ds),
            ("data & ai", user_alex_kim, stream_ds),
            ("ai research lab", user_james, workday_ds),
            ("compliance & risk", user_auditor, workday_ds),
            ("product management", user_priya, cust_ds)
        ]

        for d_name, d_obj in dept_map.items():
            for term, usr, ds_obj in dept_user_links:
                if term in d_name:
                    create_rel("data_sources", ds_obj.id, "belongs_to_department", "departments", d_obj.id, "DEPARTMENT_BOUNDING")
                    create_rel("departments", d_obj.id, "managed_by_user", "users", usr.id, "DEPARTMENT_LEAD")

        db.commit()
        MemoryCacheService().clear()
        print("Successfully populated ALL remaining unpopulated entities!")
    except Exception as e:
        db.rollback()
        print(f"Population error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    populate_remaining()

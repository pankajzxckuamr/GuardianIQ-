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

def populate():
    db = SessionLocal()
    try:
        MemoryCacheService().clear()

        admin_user = db.query(User).filter(User.email == "admin@guardianiq.com").first() or db.query(User).first()
        tenant_id = admin_user.id
        print(f"Populating Full 5-Hop Governance Architecture for Tenant: {tenant_id}")

        # Fetch users
        users = db.query(User).all()
        elena = next((u for u in users if "Elena" in u.name or "erodriguez" in u.email), users[0])
        michael = next((u for u in users if "Michael" in u.name or "mchang" in u.email), users[0])
        sarah_j = next((u for u in users if "sjenkins" in u.email or "Sarah" in u.name), users[0])
        sarah_c = next((u for u in users if "sarah.chen" in u.email), sarah_j)
        priya = next((u for u in users if "priya" in u.email), users[0])
        james = next((u for u in users if "james" in u.email), users[0])
        alex = next((u for u in users if "alex" in u.email), users[0])
        governance_admin = next((u for u in users if "governance" in u.email), admin_user)
        compliance_officer = next((u for u in users if "compliance" in u.email), admin_user)
        risk_manager = next((u for u in users if "risk" in u.email), admin_user)
        auditor = next((u for u in users if "auditor" in u.email), admin_user)

        def assign_resp(obj_type, obj_id, resp_type, actor_id, is_prim=False):
            if not obj_id or not actor_id: return
            dup = db.query(ObjectResponsibility).filter_by(
                tenant_id=tenant_id,
                object_type=obj_type.upper(),
                object_id=str(obj_id),
                responsibility_type=resp_type.upper(),
                actor_id=str(actor_id),
                status="ACTIVE"
            ).first()
            if dup: return dup

            if is_prim and resp_type.upper() == "OWNER":
                old_primaries = db.query(ObjectResponsibility).filter_by(
                    tenant_id=tenant_id,
                    object_type=obj_type.upper(),
                    object_id=str(obj_id),
                    responsibility_type="OWNER",
                    is_primary=True,
                    status="ACTIVE"
                ).all()
                for op in old_primaries:
                    op.is_primary = False
                    op.status = "REVOKED"

            new_resp = ObjectResponsibility(
                id=uuid4(),
                tenant_id=tenant_id,
                object_type=obj_type.upper(),
                object_id=str(obj_id),
                responsibility_type=resp_type.upper(),
                actor_type="USER",
                actor_id=str(actor_id),
                is_primary=is_prim,
                status="ACTIVE",
                effective_from=datetime.now(timezone.utc),
                created_by=admin_user.id
            )
            db.add(new_resp)
            return new_resp

        def create_rel(src_type, src_id, rel_type, tgt_type, tgt_id, scope=None):
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
                relationship_scope=scope or "DEFAULT",
                effective_from=datetime.now(timezone.utc),
                status="ACTIVE",
                metadata_json={"seeded": True}
            )
            db.add(new_rel)
            return new_rel

        # Assign Primary Owners & Responsibilities across ALL entities
        agents = db.query(Agent).all()
        for a in agents:
            n = a.agent_name.lower()
            if "fraud" in n:
                assign_resp("AGENTS", a.id, "OWNER", elena.id, is_prim=True)
                assign_resp("AGENTS", a.id, "REVIEWER", michael.id)
                assign_resp("AGENTS", a.id, "APPROVER", admin_user.id)
            elif "onboarding" in n:
                assign_resp("AGENTS", a.id, "OWNER", sarah_j.id, is_prim=True)
                assign_resp("AGENTS", a.id, "REVIEWER", priya.id)
                assign_resp("AGENTS", a.id, "APPROVER", governance_admin.id)
            elif "refund" in n:
                assign_resp("AGENTS", a.id, "OWNER", michael.id, is_prim=True)
                assign_resp("AGENTS", a.id, "REVIEWER", sarah_c.id)
                assign_resp("AGENTS", a.id, "APPROVER", risk_manager.id)
            elif "compliance" in n:
                assign_resp("AGENTS", a.id, "OWNER", compliance_officer.id, is_prim=True)
                assign_resp("AGENTS", a.id, "REVIEWER", auditor.id)
                assign_resp("AGENTS", a.id, "APPROVER", governance_admin.id)
            else:
                assign_resp("AGENTS", a.id, "OWNER", alex.id, is_prim=True)
                assign_resp("AGENTS", a.id, "REVIEWER", james.id)
                assign_resp("AGENTS", a.id, "APPROVER", admin_user.id)

        models = db.query(AIModel).all()
        for m in models:
            n = m.model_name.lower()
            if "anomaly" in n or "fraud" in n:
                assign_resp("AI_MODELS", m.id, "OWNER", elena.id, is_prim=True)
                assign_resp("AI_MODELS", m.id, "REVIEWER", michael.id)
                assign_resp("AI_MODELS", m.id, "APPROVER", risk_manager.id)
            elif "legal" in n or "document" in n:
                assign_resp("AI_MODELS", m.id, "OWNER", sarah_j.id, is_prim=True)
                assign_resp("AI_MODELS", m.id, "REVIEWER", priya.id)
                assign_resp("AI_MODELS", m.id, "APPROVER", compliance_officer.id)
            else:
                assign_resp("AI_MODELS", m.id, "OWNER", sarah_c.id, is_prim=True)
                assign_resp("AI_MODELS", m.id, "REVIEWER", james.id)
                assign_resp("AI_MODELS", m.id, "APPROVER", admin_user.id)

        tools = db.query(Tool).all()
        for t in tools:
            n = t.tool_name.lower()
            if "stripe" in n or "refund" in n:
                assign_resp("TOOLS", t.id, "OWNER", michael.id, is_prim=True)
                assign_resp("TOOLS", t.id, "REVIEWER", sarah_c.id)
                assign_resp("TOOLS", t.id, "APPROVER", admin_user.id)
            elif "freeze" in n or "banking" in n:
                assign_resp("TOOLS", t.id, "OWNER", elena.id, is_prim=True)
                assign_resp("TOOLS", t.id, "REVIEWER", risk_manager.id)
                assign_resp("TOOLS", t.id, "APPROVER", admin_user.id)
            else:
                assign_resp("TOOLS", t.id, "OWNER", sarah_j.id, is_prim=True)
                assign_resp("TOOLS", t.id, "REVIEWER", compliance_officer.id)
                assign_resp("TOOLS", t.id, "APPROVER", governance_admin.id)

        workflows = db.query(Workflow).all()
        for w in workflows:
            n = w.workflow_name.lower()
            if "fraud" in n or "freeze" in n:
                assign_resp("WORKFLOWS", w.id, "OWNER", elena.id, is_prim=True)
                assign_resp("WORKFLOWS", w.id, "REVIEWER", risk_manager.id)
                assign_resp("WORKFLOWS", w.id, "APPROVER", admin_user.id)
            elif "nda" in n or "employee" in n or "setup" in n:
                assign_resp("WORKFLOWS", w.id, "OWNER", sarah_j.id, is_prim=True)
                assign_resp("WORKFLOWS", w.id, "REVIEWER", priya.id)
                assign_resp("WORKFLOWS", w.id, "APPROVER", governance_admin.id)
            else:
                assign_resp("WORKFLOWS", w.id, "OWNER", michael.id, is_prim=True)
                assign_resp("WORKFLOWS", w.id, "REVIEWER", sarah_c.id)
                assign_resp("WORKFLOWS", w.id, "APPROVER", admin_user.id)

        datasources = db.query(DataSource).all()
        for d in datasources:
            n = d.source_name.lower()
            if "workday" in n or "employee" in n:
                assign_resp("DATA_SOURCES", d.id, "OWNER", sarah_j.id, is_prim=True)
            elif "ledger" in n or "transaction" in n:
                assign_resp("DATA_SOURCES", d.id, "OWNER", elena.id, is_prim=True)
            else:
                assign_resp("DATA_SOURCES", d.id, "OWNER", alex.id, is_prim=True)
            assign_resp("DATA_SOURCES", d.id, "REVIEWER", james.id)
            assign_resp("DATA_SOURCES", d.id, "APPROVER", governance_admin.id)

        departments = db.query(Department).all()
        dept_hr = next((dep for dep in departments if "HR" in dep.department_name or "Human" in dep.department_name), departments[0] if departments else None)
        dept_risk = next((dep for dep in departments if "Risk" in dep.department_name or "Finance" in dep.department_name), dept_hr)
        dept_ops = next((dep for dep in departments if "Operations" in dep.department_name or "Engineering" in dep.department_name), dept_hr)

        # Build 5-Hop Deep Relationship Chains for ALL Agents, Models, Tools, Workflows

        ag_map = {a.agent_name.lower(): a for a in agents}
        mod_map = {m.model_name.lower(): m for m in models}
        tool_map = {t.tool_name.lower(): t for t in tools}
        wf_map = {w.workflow_name.lower(): w for w in workflows}
        ds_map = {d.source_name.lower(): d for d in datasources}

        def get_agent(term): return next((a for k, a in ag_map.items() if term in k), agents[0] if agents else None)
        def get_model(term): return next((m for k, m in mod_map.items() if term in k), models[0] if models else None)
        def get_tool(term): return next((t for k, t in tool_map.items() if term in k), tools[0] if tools else None)
        def get_wf(term): return next((w for k, w in wf_map.items() if term in k), workflows[0] if workflows else None)
        def get_ds(term): return next((d for k, d in ds_map.items() if term in k), datasources[0] if datasources else None)

        # -------------------------------------------------------------
        # CHAIN 1: Fraud Sentinel & Anomaly Detector Subsystem (5 Hops)
        # -------------------------------------------------------------
        fraud_ag = get_agent("fraud")
        anomaly_mod = get_model("anomaly")
        freeze_tool = get_tool("freeze")
        fraud_wf = get_wf("fraud")
        risk_wf = get_wf("risk")
        ledger_ds = get_ds("ledger")

        if fraud_ag and anomaly_mod: create_rel("agents", fraud_ag.id, "uses_model", "ai_models", anomaly_mod.id, "FRAUD_ANALYSIS")
        if fraud_ag and freeze_tool: create_rel("agents", fraud_ag.id, "uses_tool", "tools", freeze_tool.id, "ACCOUNT_FREEZE")
        if fraud_wf and fraud_ag: create_rel("workflows", fraud_wf.id, "participates_in_workflow", "agents", fraud_ag.id, "RESPONSE_PROTOCOL")

        # Hop 2
        if anomaly_mod and ledger_ds: create_rel("ai_models", anomaly_mod.id, "uses_data_source", "data_sources", ledger_ds.id, "TRANSACTION_LOGS")
        if freeze_tool and ledger_ds: create_rel("tools", freeze_tool.id, "uses_data_source", "data_sources", ledger_ds.id, "CORE_BANKING")
        if risk_wf and fraud_wf: create_rel("workflows", risk_wf.id, "triggers_workflow", "workflows", fraud_wf.id, "RISK_TRIGGER")

        # Hop 3
        if ledger_ds and dept_risk: create_rel("data_sources", ledger_ds.id, "belongs_to_department", "departments", dept_risk.id, "RISK_GOVERNANCE")

        # Hop 4
        if dept_risk and elena: create_rel("departments", dept_risk.id, "managed_by_user", "users", elena.id, "LEAD_ARCHITECT")

        # Hop 5
        if elena and dept_ops: create_rel("users", elena.id, "assigned_to_committee", "departments", dept_ops.id, "EXECUTIVE_RISK_BOARD")

        # -------------------------------------------------------------
        # CHAIN 2: Autonomous Onboarding & Document Analyzer Subsystem (5 Hops)
        # -------------------------------------------------------------
        onboarding_ag = get_agent("onboarding")
        legal_mod = get_model("legal")
        policy_tool = get_tool("policy")
        nda_wf = get_wf("nda") or get_wf("employee")
        comp_wf = get_wf("compliance")
        workday_ds = get_ds("workday")

        if onboarding_ag and legal_mod: create_rel("agents", onboarding_ag.id, "uses_model", "ai_models", legal_mod.id, "DOCUMENT_ANALYSIS")
        if onboarding_ag and policy_tool: create_rel("agents", onboarding_ag.id, "uses_tool", "tools", policy_tool.id, "POLICY_CHECK")
        if nda_wf and onboarding_ag: create_rel("workflows", nda_wf.id, "participates_in_workflow", "agents", onboarding_ag.id, "ONBOARDING_PIPELINE")

        # Hop 2
        if legal_mod and workday_ds: create_rel("ai_models", legal_mod.id, "uses_data_source", "data_sources", workday_ds.id, "HR_RECORDS")
        if policy_tool and workday_ds: create_rel("tools", policy_tool.id, "uses_data_source", "data_sources", workday_ds.id, "USER_ROSTER")
        if comp_wf and nda_wf: create_rel("workflows", comp_wf.id, "governs_workflow", "workflows", nda_wf.id, "COMPLIANCE_GOVERNANCE")

        # Hop 3
        if workday_ds and dept_hr: create_rel("data_sources", workday_ds.id, "belongs_to_department", "departments", dept_hr.id, "HR_COMPLIANCE")

        # Hop 4
        if dept_hr and sarah_j: create_rel("departments", dept_hr.id, "managed_by_user", "users", sarah_j.id, "HR_DIRECTOR")

        # Hop 5
        if sarah_j and dept_risk: create_rel("users", sarah_j.id, "assigned_to_committee", "departments", dept_risk.id, "AUDIT_COMMITTEE")

        # -------------------------------------------------------------
        # CHAIN 3: Autonomous Refund & Stripe API Subsystem (5 Hops)
        # -------------------------------------------------------------
        refund_ag = get_agent("refund")
        refund_mod = get_model("refund") or get_model("classifier")
        stripe_tool = get_tool("stripe") or get_tool("refund")
        refund_wf = get_wf("refund")
        customer_ds = get_ds("customer") or get_ds("stream")

        if refund_ag and refund_mod: create_rel("agents", refund_ag.id, "uses_model", "ai_models", refund_mod.id, "INTENT_CLASSIFIER")
        if refund_ag and stripe_tool: create_rel("agents", refund_ag.id, "uses_tool", "tools", stripe_tool.id, "PAYMENT_GATEWAY")
        if refund_wf and refund_ag: create_rel("workflows", refund_wf.id, "participates_in_workflow", "agents", refund_ag.id, "REFUND_EXECUTION")

        # Hop 2
        if refund_mod and customer_ds: create_rel("ai_models", refund_mod.id, "uses_data_source", "data_sources", customer_ds.id, "CUSTOMER_HISTORY")
        if stripe_tool and customer_ds: create_rel("tools", stripe_tool.id, "uses_data_source", "data_sources", customer_ds.id, "TRANSACTION_LEDGER")

        # Hop 3
        if customer_ds and dept_ops: create_rel("data_sources", customer_ds.id, "belongs_to_department", "departments", dept_ops.id, "OPERATIONS")

        # Hop 4
        if dept_ops and michael: create_rel("departments", dept_ops.id, "managed_by_user", "users", michael.id, "VP_OPERATIONS")

        # Hop 5
        if michael and dept_hr: create_rel("users", michael.id, "assigned_to_committee", "departments", dept_hr.id, "GOVERNANCE_COUNCIL")

        # -------------------------------------------------------------
        # CHAIN 4: ComplianceBot Alpha & Data Quality Sentinel Subsystem (5 Hops)
        # -------------------------------------------------------------
        comp_ag = get_agent("compliance")
        quality_ag = get_agent("quality") or get_agent("sentinel")
        gov_mod = get_model("governance") or get_model("gpt-4o")
        sentiment_mod = get_model("sentiment")
        lineage_tool = get_tool("lineage") or get_tool("write")

        if comp_ag and gov_mod: create_rel("agents", comp_ag.id, "uses_model", "ai_models", gov_mod.id, "GOVERNANCE_EVALUATION")
        if comp_ag and lineage_tool: create_rel("agents", comp_ag.id, "uses_tool", "tools", lineage_tool.id, "DATA_TRACING")

        if quality_ag and sentiment_mod: create_rel("agents", quality_ag.id, "uses_model", "ai_models", sentiment_mod.id, "SENTIMENT_ANALYSIS")

        db.commit()
        MemoryCacheService().clear()
        print("Full 5-Hop Governance Architecture population committed successfully!")
    except Exception as e:
        db.rollback()
        print(f"Population error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    populate()

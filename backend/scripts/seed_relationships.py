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

def seed():
    db = SessionLocal()
    try:
        # Clear cache so fresh relationship graph is built
        MemoryCacheService().clear()

        admin_user = db.query(User).filter(User.email == "admin@guardianiq.com").first() or db.query(User).first()
        tenant_id = admin_user.id
        print(f"Seeding 5-Hop Deep Governance Graph for Tenant: {tenant_id}")

        # -------------------------------------------------------------
        # Fetch or Create Entities Across All Types
        # -------------------------------------------------------------
        fraud_agent = db.query(Agent).filter(Agent.agent_name.ilike("%Fraud%")).first() or db.query(Agent).first()

        anomaly_model = db.query(AIModel).filter(AIModel.model_name.ilike("%Anomaly%")).first() or db.query(AIModel).first()
        classifier_model = db.query(AIModel).filter(AIModel.model_name.ilike("%Classifier%")).first() or anomaly_model

        freeze_tool = db.query(Tool).filter(Tool.tool_name.ilike("%Freeze%")).first() or db.query(Tool).first()
        payment_tool = db.query(Tool).filter(Tool.tool_name.ilike("%Stripe%")).first() or freeze_tool

        fraud_wf = db.query(Workflow).filter(Workflow.workflow_name.ilike("%Fraud%")).first() or db.query(Workflow).first()
        risk_wf = db.query(Workflow).filter(Workflow.workflow_name.ilike("%Risk%")).first() or fraud_wf
        policy_wf = db.query(Workflow).filter(Workflow.workflow_name.ilike("%Policy%")).first() or risk_wf

        data_sources = db.query(DataSource).all()
        ds1 = data_sources[0] if len(data_sources) > 0 else None
        ds2 = data_sources[1] if len(data_sources) > 1 else ds1

        departments = db.query(Department).all()
        dept_risk = next((d for d in departments if "Risk" in getattr(d, "department_name", "")), departments[0] if departments else None)
        dept_ops = next((d for d in departments if "Ops" in getattr(d, "department_name", "") or "Engineering" in getattr(d, "department_name", "")), dept_risk)

        users = db.query(User).all()
        user_pankaj = next((u for u in users if "Pankaj" in u.name), users[0] if users else None)
        user_admin = next((u for u in users if "Admin" in u.name or "Super" in u.name), user_pankaj)

        def create_rel(src_type, src_id, rel_type, tgt_type, tgt_id, scope=None):
            if not src_id or not tgt_id:
                return None
            dup = db.query(GenericRelationship).filter_by(
                tenant_id=tenant_id,
                source_type=src_type.lower(),
                source_id=str(src_id),
                relationship_type=rel_type.lower(),
                target_type=tgt_type.lower(),
                target_id=str(tgt_id),
                status="ACTIVE"
            ).first()
            if dup:
                return dup
            
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
            print(f"Created rel: {src_type} ({src_id}) -[{rel_type}]-> {tgt_type} ({tgt_id})")
            return new_rel

        # =============================================================
        # 5-HOP DEEP RELATIONSHIP CHAIN FOR "Autonomous Fraud Sentinel"
        # =============================================================

        # -------------------------------------------------------------
        # HOP 1: Direct links to/from Fraud Agent
        # -------------------------------------------------------------
        if fraud_agent:
            if anomaly_model:
                create_rel("agents", fraud_agent.id, "uses_model", "ai_models", anomaly_model.id, "FRAUD_DETECTION")
            if freeze_tool:
                create_rel("agents", fraud_agent.id, "uses_tool", "tools", freeze_tool.id, "BANK_API")
            if classifier_model:
                create_rel("agents", fraud_agent.id, "uses_model", "ai_models", classifier_model.id, "PATTERN_MATCHING")
            if fraud_wf:
                create_rel("workflows", fraud_wf.id, "participates_in_workflow", "agents", fraud_agent.id, "RESPONSE_PROTOCOL")

        # -------------------------------------------------------------
        # HOP 2: Transitive links starting from Hop 1 entities
        # -------------------------------------------------------------
        if anomaly_model and ds1:
            create_rel("ai_models", anomaly_model.id, "uses_data_source", "data_sources", ds1.id, "TRANSACTION_LEDGER")
        if freeze_tool and ds2:
            create_rel("tools", freeze_tool.id, "uses_data_source", "data_sources", ds2.id, "CORE_BANKING_DB")
        if risk_wf and fraud_wf:
            create_rel("workflows", risk_wf.id, "triggers_workflow", "workflows", fraud_wf.id, "CASCADE_TRIGGER")

        # -------------------------------------------------------------
        # HOP 3: Deep Transitive links starting from Hop 2 entities
        # -------------------------------------------------------------
        if ds1 and dept_risk:
            create_rel("data_sources", ds1.id, "belongs_to_department", "departments", dept_risk.id, "DATA_GOVERNANCE")
        if ds2 and dept_ops:
            create_rel("data_sources", ds2.id, "belongs_to_department", "departments", dept_ops.id, "INFRASTRUCTURE")
        if policy_wf and risk_wf:
            create_rel("workflows", policy_wf.id, "governs_workflow", "workflows", risk_wf.id, "POLICY_ENFORCEMENT")

        # -------------------------------------------------------------
        # HOP 4: Deep Transitive links starting from Hop 3 entities
        # -------------------------------------------------------------
        if dept_risk and user_pankaj:
            create_rel("departments", dept_risk.id, "managed_by_user", "users", user_pankaj.id, "DEPARTMENT_HEAD")
        if dept_ops and user_admin:
            create_rel("departments", dept_ops.id, "managed_by_user", "users", user_admin.id, "OPERATIONS_LEAD")
        if policy_wf and user_admin:
            create_rel("workflows", policy_wf.id, "reviewed_by_user", "users", user_admin.id, "AUDIT_REVIEW")

        # -------------------------------------------------------------
        # HOP 5: Deep Transitive links starting from Hop 4 entities
        # -------------------------------------------------------------
        if user_pankaj and dept_ops:
            create_rel("users", user_pankaj.id, "assigned_to_committee", "departments", dept_ops.id, "EXECUTIVE_COMMITTEE")
        if user_admin and dept_risk:
            create_rel("users", user_admin.id, "assigned_to_committee", "departments", dept_risk.id, "RISK_COMMITTEE")

        db.commit()
        # Clear cache again after committing
        MemoryCacheService().clear()
        print("5-Hop Governance Graph committed successfully!")
    except Exception as e:
        db.rollback()
        print(f"Seeding error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed()

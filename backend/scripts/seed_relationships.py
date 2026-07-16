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
from uuid import uuid4
from datetime import datetime, timezone

def seed():
    db = SessionLocal()
    try:
        # Get default admin user as tenant owner / actor
        admin_user = db.query(User).filter(User.email == "admin@guardianiq.com").first()
        if not admin_user:
            print("Error: admin user not found. Please run core/registry seeding first.")
            return

        tenant_id = admin_user.id
        
        # Query some assets
        model = db.query(AIModel).first()
        agent = db.query(Agent).first()
        tool = db.query(Tool).first()
        workflow = db.query(Workflow).first()
        data_source = db.query(DataSource).first()
        
        # Fetch other users for responsibilities
        reviewer = db.query(User).filter(User.email == "reviewer@guardianiq.com").first()
        auditor = db.query(User).filter(User.email == "auditor@guardianiq.com").first()

        print(f"Seeding relationships for Tenant: {tenant_id}")
        
        # Helper to create relationship
        def create_rel(src_type, src_id, rel_type, tgt_type, tgt_id):
            # Check duplicate
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
                print(f"Relationship {src_type} ({src_id}) -[{rel_type}]-> {tgt_type} ({tgt_id}) already exists.")
                return dup
            
            new_rel = GenericRelationship(
                id=uuid4(),
                tenant_id=tenant_id,
                source_type=src_type.lower(),
                source_id=str(src_id),
                relationship_type=rel_type.lower(),
                target_type=tgt_type.lower(),
                target_id=str(tgt_id),
                effective_from=datetime.now(timezone.utc),
                status="ACTIVE",
                metadata_json={"seeded": True}
            )
            db.add(new_rel)
            print(f"Seeded relationship: {src_type} -[{rel_type}]-> {tgt_type}")
            return new_rel

        # Helper to create responsibility
        def create_resp(obj_type, obj_id, actor_type, actor_id, resp_type, is_primary=True):
            # Check duplicate
            dup = db.query(ObjectResponsibility).filter_by(
                tenant_id=tenant_id,
                object_type=obj_type.lower(),
                object_id=str(obj_id),
                actor_type=actor_type.upper(),
                actor_id=str(actor_id),
                responsibility_type=resp_type.upper(),
                status="ACTIVE"
            ).first()
            if dup:
                print(f"Responsibility for {obj_type} ({obj_id}) already assigned to {actor_id}.")
                return dup
            
            new_resp = ObjectResponsibility(
                id=uuid4(),
                tenant_id=tenant_id,
                object_type=obj_type.lower(),
                object_id=str(obj_id),
                actor_type=actor_type.upper(),
                actor_id=str(actor_id),
                responsibility_type=resp_type.upper(),
                is_primary=is_primary,
                effective_from=datetime.now(timezone.utc),
                status="ACTIVE",
                metadata_json={"seeded": True}
            )
            db.add(new_resp)
            print(f"Seeded responsibility: {actor_type} is {resp_type} of {obj_type}")
            return new_resp

        # Seed relationships if targets exist
        if agent and tool:
            create_rel("agents", agent.id, "uses_tool", "tools", tool.id)
        if agent and model:
            create_rel("agents", agent.id, "uses_model", "ai_models", model.id)
        if agent and data_source:
            create_rel("agents", agent.id, "uses_data_source", "data_sources", data_source.id)
        if model and data_source:
            create_rel("ai_models", model.id, "uses_data_source", "data_sources", data_source.id)
        if workflow and agent:
            create_rel("workflows", workflow.id, "participates_in_workflow", "agents", agent.id)

        # Seed responsibilities
        if agent:
            create_resp("agents", agent.id, "USER", admin_user.id, "OWNER")
            if auditor:
                create_resp("agents", agent.id, "USER", auditor.id, "AUDITOR", is_primary=False)
        if model:
            create_resp("ai_models", model.id, "USER", admin_user.id, "OWNER")
            if reviewer:
                create_resp("ai_models", model.id, "USER", reviewer.id, "REVIEWER", is_primary=False)
        if workflow:
            create_resp("workflows", workflow.id, "USER", admin_user.id, "OWNER")
        if tool:
            create_resp("tools", tool.id, "USER", admin_user.id, "OWNER")

        db.commit()
        print("Reference and sample data seeded successfully!")
    except Exception as e:
        db.rollback()
        print(f"Error during seeding: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed()

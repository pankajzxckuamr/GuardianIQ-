import sys, os
from dotenv import load_dotenv
load_dotenv('.env')
sys.path.append('.')
from app.db.session import SessionLocal
from app.modules.agent.models import Agent
from app.modules.ai_model.models import AIModel
from app.modules.registry.models import Tool, Workflow
from app.modules.auth.models import User
from app.modules.relationship.models import GenericRelationship, ObjectResponsibility

db = SessionLocal()
print("=== AGENTS ===")
for a in db.query(Agent).all():
    print(f"ID: {a.id} | Agent Name: {getattr(a, 'agent_name', getattr(a, 'name', 'N/A'))}")

print("\n=== AI MODELS ===")
for m in db.query(AIModel).all():
    print(f"ID: {m.id} | Model Name: {getattr(m, 'model_name', getattr(m, 'name', 'N/A'))}")

print("\n=== TOOLS ===")
for t in db.query(Tool).all():
    print(f"ID: {t.id} | Tool Name: {getattr(t, 'tool_name', getattr(t, 'name', 'N/A'))}")

print("\n=== WORKFLOWS ===")
for w in db.query(Workflow).all():
    print(f"ID: {w.id} | Workflow Name: {getattr(w, 'workflow_name', getattr(w, 'name', 'N/A'))}")

print("\n=== USERS ===")
for u in db.query(User).all():
    print(f"ID: {u.id} | Email: {u.email}")

print("\n=== RELATIONSHIPS ===")
for r in db.query(GenericRelationship).all():
    print(f"Source: {r.source_type} ({r.source_id}) -[{r.relationship_type}]-> Target: {r.target_type} ({r.target_id}) | Status: {r.status}")

print("\n=== RESPONSIBILITIES ===")
for resp in db.query(ObjectResponsibility).all():
    print(f"Object: {resp.object_type} ({resp.object_id}) | Role: {resp.responsibility_type} | Actor: {resp.actor_id} | Primary: {resp.is_primary} | Status: {resp.status}")

db.close()

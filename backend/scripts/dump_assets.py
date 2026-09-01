import sys
sys.path.insert(0, '.')
from app.db.session import SessionLocal
import app.db.base
from app.modules.agent.models import Agent
from app.modules.registry.models import Tool, Workflow
from app.modules.datasource.models import DataSource
from app.modules.ai_model.models import AIModel
from app.modules.policy_engine.models import GovernancePolicy

db = SessionLocal()
print('=== TOP 10 PRIMARY AGENTS ===')
for a in db.query(Agent).filter(Agent.agent_name.in_([
    "Autonomous Fraud Sentinel", "Autonomous Onboarding Coordinator", "Autonomous Refund Agent",
    "ComplianceBot Alpha", "DataQuality Sentinel", "Customer Summary Agent", "Treasury Agent",
    "Permitted Analytics Agent", "Read Only Search Agent", "Model Invocator Agent"
])).all():
    print(f'{a.id} | {a.agent_name} | Risk: {a.risk_level}')

print('\n=== PRIMARY TOOLS ===')
for t in db.query(Tool).all()[:10]:
    print(f'{t.id} | {t.tool_code} | {t.tool_name}')

print('\n=== PRIMARY DATA SOURCES ===')
for d in db.query(DataSource).all()[:10]:
    print(f'{d.id} | {d.source_code} | {d.source_name}')

print('\n=== PRIMARY AI MODELS ===')
for m in db.query(AIModel).all()[:10]:
    print(f'{m.id} | {m.model_code} | {m.model_name}')

print('\n=== PRIMARY WORKFLOWS ===')
for w in db.query(Workflow).all()[:10]:
    print(f'{w.id} | {w.workflow_code} | {w.workflow_name}')

print('\n=== PRIMARY POLICIES ===')
for p in db.query(GovernancePolicy).all():
    print(f'{p.id} | {p.policy_code} | {p.name}')

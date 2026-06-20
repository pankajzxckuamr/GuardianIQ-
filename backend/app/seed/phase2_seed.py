import logging
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.modules.registry.models import (
    GuardianUser, RegistryRole, RegistryDepartment, 
    RegistryWorkflow, RegistryAIAgent, RegistryAIModel
)
from app.modules.workflow_scheduler.models import (
    ApprovalGroup, Phase2WorkflowSchedule, WorkflowScheduleAgentAssignment, ApprovalGroupMember
)
from app.modules.workflow_execution.models import WorkflowRun
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def seed_data():
    db = SessionLocal()
    try:
        # Get or create a default department and role for users
        dept = db.query(RegistryDepartment).first()
        if not dept:
            dept = RegistryDepartment(department_code="DEMO_DEPT", department_name="Demo Department")
            db.add(dept)
            db.flush()

        role = db.query(RegistryRole).first()
        if not role:
            role = RegistryRole(role_code="DEMO_ROLE", role_name="Demo Role", role_type="DEMO")
            db.add(role)
            db.flush()

        # Users
        users_data = [
            ("governance_admin", "GOVERNANCE_ADMIN", "governance@guardianiq.demo"),
            ("risk_manager", "RISK_MANAGER", "risk@guardianiq.demo"),
            ("compliance_officer", "COMPLIANCE_OFFICER", "compliance@guardianiq.demo"),
            ("auditor", "AUDITOR", "auditor@guardianiq.demo"),
            ("business_approver", "BUSINESS_APPROVER", "approver@guardianiq.demo")
        ]
        user_ids = {}
        for name, role_code, email in users_data:
            user = db.query(GuardianUser).filter_by(email=email).first()
            if not user:
                user = GuardianUser(
                    full_name=name.replace('_', ' ').title(),
                    email=email,
                    department_id=dept.id,
                    role_id=role.id,
                    status="ACTIVE"
                )
                db.add(user)
                db.flush()
            user_ids[name] = user.id
            logger.info(f"User {name} processed.")

        # Approval Group
        ag = db.query(ApprovalGroup).filter_by(name="AI Governance Board").first()
        if not ag:
            ag = ApprovalGroup(
                name="AI Governance Board",
                tenant_id=user_ids["governance_admin"]
            )
            db.add(ag)
            db.flush()
            
            # Members
            member1 = ApprovalGroupMember(approval_group_id=ag.id, user_id=user_ids["risk_manager"])
            member2 = ApprovalGroupMember(approval_group_id=ag.id, user_id=user_ids["compliance_officer"])
            db.add_all([member1, member2])
            db.flush()
        logger.info("Approval Group processed.")

        # Workflow
        wf = db.query(RegistryWorkflow).filter_by(workflow_code="AI_RECOMMENDATION_REVIEW").first()
        if not wf:
            wf = RegistryWorkflow(
                workflow_code="AI_RECOMMENDATION_REVIEW",
                workflow_name="AI Recommendation Review Workflow",
                workflow_type="ASSESSMENT",
                business_criticality="HIGH",
                owner_user_id=user_ids["governance_admin"],
                status="ACTIVE",
                metadata_json={}
            )
            db.add(wf)
            db.flush()
        logger.info("Workflow processed.")

        # AI Agent
        agent = db.query(RegistryAIAgent).filter_by(agent_code="GOV_REVIEW_AGENT_001").first()
        if not agent:
            agent = RegistryAIAgent(
                agent_code="GOV_REVIEW_AGENT_001",
                agent_name="Governance Review Agent",
                agent_type="REVIEW",
                execution_mode="RECOMMEND_ONLY",
                risk_level="HIGH",
                owner_user_id=user_ids["governance_admin"],
                status="ACTIVE"
            )
            db.add(agent)
            db.flush()
        logger.info("Agent processed.")

        # AI Model
        model = db.query(RegistryAIModel).filter_by(model_code="RISK_CLASSIFICATION_MODEL").first()
        if not model:
            model = RegistryAIModel(
                model_code="RISK_CLASSIFICATION_MODEL",
                model_name="Risk Classification Model v2.1",
                model_type="CLASSIFICATION",
                version="2.1",
                purpose="Risk Classification",
                risk_level="HIGH",
                owner_user_id=user_ids["governance_admin"],
                status="ACTIVE"
            )
            db.add(model)
            db.flush()
        logger.info("Model processed.")

        # Schedule
        sched = db.query(Phase2WorkflowSchedule).filter_by(schedule_code="DAILY_MODEL_RISK_REVIEW").first()
        if not sched:
            sched = Phase2WorkflowSchedule(
                schedule_code="DAILY_MODEL_RISK_REVIEW",
                schedule_name="Daily AI Model Risk Review",
                workflow_id=wf.id,
                schedule_type="DAILY",
                cron_expression="0 9 * * *",
                timezone="Asia/Kolkata",
                owner_user_id=user_ids["governance_admin"],
                risk_level="HIGH",
                approval_required=True,
                approval_group_id=ag.id,
                max_runtime_seconds=3600,
                schedule_status="DRAFT",
                tenant_id=user_ids["governance_admin"]
            )
            db.add(sched)
            db.flush()

            # Agent Assignment
            assignment = WorkflowScheduleAgentAssignment(
                schedule_id=sched.id,
                agent_id=agent.id,
                model_id=model.id,
                assignment_role="PRIMARY",
                execution_mode="RECOMMEND_ONLY",
                confidence_threshold=80.0,
                allowed_tools_json=["REGISTRY_READ_API","AUDIT_READ_API"],
                allowed_data_sources_json=[],
                blocked_operations_json=["UPDATE_POLICY","EXECUTE_EXTERNAL_ACTION","SEND_EMAIL_WITHOUT_APPROVAL"],
                tenant_id=user_ids["governance_admin"]
            )
            db.add(assignment)
        
        db.commit()
        logger.info("Schedule and Assignment processed.")
        logger.info("Seed complete.")
    except Exception as e:
        db.rollback()
        logger.error(f"Error seeding data: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()

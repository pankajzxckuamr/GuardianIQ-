import logging
from uuid import uuid4
from datetime import datetime, timedelta, timezone
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import delete

from app.db.session import SessionLocal
from app.modules.registry.models import (
    GuardianUser, RegistryRole, RegistryDepartment,
    RegistryWorkflow, RegistryAIAgent, RegistryAIModel,
    RegistryDataSource, RegistryTool, RegistryRelationship,
    RegistryRegisterAll
)
from app.modules.workflow_scheduler.models import (
    ApprovalGroup, ApprovalGroupMember, Phase2WorkflowSchedule,
    WorkflowScheduleAgentAssignment, WorkflowScheduleApproval
)
from app.modules.workflow_execution.models import WorkflowRun
from app.modules.workflow_notifications.models import WorkflowNotification
from app.modules.auth.models import User

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("populate_5")

now = datetime.now(timezone.utc)

def populate_5():
    db = SessionLocal()
    try:
        prefix = "POP_"
        
        # Clean up previously generated dummy data
        logger.info("Cleaning up old dummy data...")
        from sqlalchemy import select
        # Delete dependent data using subqueries
        dummy_schedules = select(Phase2WorkflowSchedule.id).where(Phase2WorkflowSchedule.schedule_code.like(f"{prefix}%"))
        db.execute(delete(WorkflowNotification).where(WorkflowNotification.title.like(f"{prefix}%")))
        db.execute(delete(WorkflowRun).where(WorkflowRun.schedule_id.in_(dummy_schedules)))
        db.execute(delete(WorkflowScheduleApproval).where(WorkflowScheduleApproval.schedule_id.in_(dummy_schedules)))
        db.execute(delete(WorkflowScheduleAgentAssignment).where(WorkflowScheduleAgentAssignment.schedule_id.in_(dummy_schedules)))
        db.execute(delete(Phase2WorkflowSchedule).where(Phase2WorkflowSchedule.schedule_code.like(f"{prefix}%")))
        db.execute(delete(ApprovalGroupMember))
        db.execute(delete(ApprovalGroup).where(ApprovalGroup.name.like(f"{prefix}%")))
        db.execute(delete(RegistryRegisterAll))
        db.execute(delete(RegistryRelationship))
        db.execute(delete(RegistryWorkflow).where(RegistryWorkflow.workflow_code.like(f"{prefix}%")))
        db.execute(delete(RegistryTool).where(RegistryTool.tool_code.like(f"{prefix}%")))
        db.execute(delete(RegistryAIAgent).where(RegistryAIAgent.agent_code.like(f"{prefix}%")))
        db.execute(delete(RegistryAIModel).where(RegistryAIModel.model_code.like(f"{prefix}%")))
        db.execute(delete(RegistryDataSource).where(RegistryDataSource.source_code.like(f"{prefix}%")))
        user_emails = [
            "alice.morgan@guardianiq.com",
            "bob.chen@guardianiq.com",
            "charlie.davies@guardianiq.com",
            "diana.prince@guardianiq.com",
            "ethan.hunt@guardianiq.com"
        ]
        db.execute(delete(GuardianUser).where(GuardianUser.email.in_(user_emails)))
        db.execute(delete(RegistryRole).where(RegistryRole.role_code.like(f"{prefix}%")))
        db.execute(delete(RegistryDepartment).where(RegistryDepartment.department_code.like(f"{prefix}%")))
        db.flush()

        logger.info("Inserting meaningful data...")

        # 1. Departments (5)
        dept_names = ["Risk & Compliance", "AI Ethics Board", "Data Science & Engineering", "Legal Counsel", "Cybersecurity"]
        depts = []
        for i, name in enumerate(dept_names, 1):
            dept = RegistryDepartment(
                department_code=f"{prefix}DEPT_{i}",
                department_name=name,
                status="ACTIVE"
            )
            db.add(dept)
            depts.append(dept)
        db.flush()

        # 2. Roles (5)
        role_names = ["Governance Lead", "Risk Assessor", "Data Scientist", "Compliance Officer", "System Admin"]
        roles = []
        for i, name in enumerate(role_names, 1):
            role = RegistryRole(
                role_code=f"{prefix}ROLE_{i}",
                role_name=name,
                role_type="GOVERNANCE" if "Gov" in name or "Risk" in name or "Comp" in name else "TECHNICAL",
                permissions_json={}
            )
            db.add(role)
            roles.append(role)
        db.flush()
        
        # 3. Users (5)
        user_data = [
            ("Alice Morgan", "alice.morgan@guardianiq.com"),
            ("Bob Chen", "bob.chen@guardianiq.com"),
            ("Charlie Davies", "charlie.davies@guardianiq.com"),
            ("Diana Prince", "diana.prince@guardianiq.com"),
            ("Ethan Hunt", "ethan.hunt@guardianiq.com")
        ]
        users = []
        for i, (name, email) in enumerate(user_data, 1):
            user = GuardianUser(
                email=email,
                full_name=name,
                department_id=depts[i-1].id,
                role_id=roles[i-1].id,
                status="ACTIVE"
            )
            db.add(user)
            users.append(user)
        db.flush()

        tenant_id = users[0].id

        # 4. Data Sources (5)
        ds_data = [
            ("Production Customer DB", "DATABASE", "HIGH"),
            ("AWS S3 Analytics DataLake", "DATA_LAKE", "MEDIUM"),
            ("HR Employee Records", "DATABASE", "CRITICAL"),
            ("Marketing Campaign API", "API", "LOW"),
            ("Financial Transaction Logs", "DATABASE", "HIGH")
        ]
        data_sources = []
        for i, (name, ds_type, sensitivity) in enumerate(ds_data, 1):
            ds = RegistryDataSource(
                source_code=f"{prefix}DS_{i}",
                source_name=name,
                source_type=ds_type,
                owner_user_id=users[i-1].id,
                department_id=depts[i-1].id,
                classification="INTERNAL",
                sensitivity_level=sensitivity,
                status="ACTIVE"
            )
            db.add(ds)
            data_sources.append(ds)
        db.flush()

        # 5. AI Models (5)
        model_data = [
            ("GPT-4 Financial Summarizer", "LLM", "HIGH", "Summarize financial news and reports"),
            ("Fraud Detection Random Forest", "CLASSIFICATION", "HIGH", "Detect fraudulent credit card transactions"),
            ("Customer Churn Predictor", "FORECASTING", "MEDIUM", "Predict likelihood of customer cancelling subscription"),
            ("Helpdesk Chatbot (Llama3)", "LLM", "LOW", "Answer basic customer support queries"),
            ("Image KYC Verification", "ML", "HIGH", "Verify identity documents for KYC compliance")
        ]
        models = []
        for i, (name, m_type, risk, purpose) in enumerate(model_data, 1):
            model = RegistryAIModel(
                model_code=f"{prefix}MODEL_{i}",
                model_name=name,
                model_type=m_type,
                purpose=purpose,
                owner_user_id=users[i-1].id,
                department_id=depts[i-1].id,
                risk_level=risk,
                status="ACTIVE"
            )
            db.add(model)
            models.append(model)
        db.flush()

        # 6. AI Agents (5)
        agent_data = [
            ("Automated Risk Assessor", "REVIEW", "HIGH"),
            ("Compliance Doc Generator", "RECOMMENDATION", "MEDIUM"),
            ("PII Redaction Bot", "EXTRACTION", "HIGH"),
            ("Customer Support Assistant", "TRIAGE", "LOW"),
            ("Code Review Copilot", "REVIEW", "MEDIUM")
        ]
        agents = []
        for i, (name, a_type, risk) in enumerate(agent_data, 1):
            agent = RegistryAIAgent(
                agent_code=f"{prefix}AGENT_{i}",
                agent_name=name,
                agent_type=a_type,
                owner_user_id=users[i-1].id,
                department_id=depts[i-1].id,
                execution_mode="RECOMMEND_ONLY" if risk != "LOW" else "LIMITED_EXECUTION",
                risk_level=risk,
                status="ACTIVE"
            )
            db.add(agent)
            agents.append(agent)
        db.flush()
        
        # 7. Tools (5)
        tool_data = [
            ("Jira Ticket Creator", "WEBHOOK", "MEDIUM"),
            ("Slack Notifier", "WEBHOOK", "LOW"),
            ("Data Profiler", "DATABASE", "HIGH"),
            ("Compliance Report Exporter", "FILE", "LOW"),
            ("Vulnerability Scanner", "TEST", "HIGH")
        ]
        tools = []
        for i, (name, category, sensitivity) in enumerate(tool_data, 1):
            tool = RegistryTool(
                tool_code=f"{prefix}TOOL_{i}",
                tool_name=name,
                tool_category=category,
                access_mode="EXECUTE",
                owner_user_id=users[i-1].id,
                sensitivity_level=sensitivity,
                allowed_operations_json=["READ", "WRITE"] if sensitivity == "LOW" else ["READ"],
                status="ACTIVE"
            )
            db.add(tool)
            tools.append(tool)
        db.flush()
        
        # 8. Workflows (5)
        wf_data = [
            ("Monthly Model Drift Review", "ASSESSMENT", "HIGH"),
            ("New AI Model Onboarding", "APPROVAL", "HIGH"),
            ("Quarterly Data Privacy Audit", "RISK_REVIEW", "CRITICAL"),
            ("Weekly Automated QA", "TEST", "MEDIUM"),
            ("Security Incident Response", "OPERATIONAL_ACTION", "HIGH")
        ]
        workflows = []
        for i, (name, w_type, criticality) in enumerate(wf_data, 1):
            wf = RegistryWorkflow(
                workflow_code=f"{prefix}WF_{i}",
                workflow_name=name,
                workflow_type=w_type,
                owner_user_id=users[i-1].id,
                department_id=depts[i-1].id,
                business_criticality=criticality,
                status="ACTIVE"
            )
            db.add(wf)
            workflows.append(wf)
        db.flush()
        
        # 9. Relationships (5)
        relationships = []
        for i in range(1, 6):
            rel = RegistryRelationship(
                source_entity_type="AI_AGENT",
                source_entity_id=agents[i-1].id,
                relationship_type="USES_MODEL",
                target_entity_type="AI_MODEL",
                target_entity_id=models[i-1].id,
                status="ACTIVE"
            )
            db.add(rel)
            relationships.append(rel)
        db.flush()

        # 10. Register All (5)
        register_alls = []
        for i in range(1, 6):
            ra = RegistryRegisterAll(
                name=f"Comprehensive Bundle {i}",
                department_id=depts[i-1].id,
                role_id=roles[i-1].id,
                user_id=users[i-1].id,
                data_source_id=data_sources[i-1].id,
                model_id=models[i-1].id,
                agent_id=agents[i-1].id,
                tool_id=tools[i-1].id,
                workflow_id=workflows[i-1].id
            )
            db.add(ra)
            register_alls.append(ra)
        db.flush()

        # Approval group
        ag = ApprovalGroup(name=f"{prefix}Global Risk Board", tenant_id=tenant_id)
        db.add(ag)
        db.flush()
        agm1 = ApprovalGroupMember(approval_group_id=ag.id, user_id=users[0].id)
        agm2 = ApprovalGroupMember(approval_group_id=ag.id, user_id=users[1].id)
        db.add_all([agm1, agm2])
        db.flush()

        # 11. Workflow Schedules (5)
        sched_data = [
            ("Monthly Drift Review Schedule", "MONTHLY"),
            ("Weekly Model Onboarding Sync", "WEEKLY"),
            ("Quarterly Privacy Audit", "CRON"),
            ("Daily QA Tests", "DAILY"),
            ("Continuous Security Scan", "HOURLY")
        ]
        schedules = []
        for i, (name, s_type) in enumerate(sched_data, 1):
            sched = Phase2WorkflowSchedule(
                workflow_id=workflows[i-1].id,
                schedule_code=f"{prefix}SCHED_{i}",
                schedule_name=name,
                schedule_type=s_type,
                cron_expression="0 9 1 * *" if s_type == "MONTHLY" else "0 9 * * 1" if s_type == "WEEKLY" else "0 9 * * *",
                owner_user_id=users[i-1].id,
                owner_department_id=depts[i-1].id,
                risk_level="HIGH" if i % 2 != 0 else "MEDIUM",
                approval_required=True,
                approval_group_id=ag.id,
                schedule_status="ACTIVE",
                tenant_id=tenant_id
            )
            db.add(sched)
            schedules.append(sched)
        db.flush()

        # 12. Agent Assignments (5)
        assignments = []
        for i in range(1, 6):
            assign = WorkflowScheduleAgentAssignment(
                schedule_id=schedules[i-1].id,
                agent_id=agents[i-1].id,
                model_id=models[i-1].id,
                assignment_role="PRIMARY",
                execution_mode="RECOMMEND_ONLY",
                tenant_id=tenant_id
            )
            db.add(assign)
            assignments.append(assign)
        db.flush()

        # 13. Schedule Approvals (5)
        approvals = []
        for i in range(1, 6):
            appr = WorkflowScheduleApproval(
                schedule_id=schedules[i-1].id,
                approval_type="ACTIVATION",
                approval_status="PENDING" if i % 2 == 0 else "APPROVED",
                approval_group_id=ag.id,
                submitted_by=users[i-1].id,
                tenant_id=tenant_id
            )
            db.add(appr)
            approvals.append(appr)
        db.flush()

        # 14. Workflow Runs (5)
        runs = []
        for i in range(1, 6):
            run = WorkflowRun(
                schedule_id=schedules[i-1].id,
                workflow_id=workflows[i-1].id,
                run_code=f"{prefix}RUN_{i}",
                trigger_type="SCHEDULED",
                run_status="COMPLETED" if i < 4 else ("FAILED" if i == 4 else "RUNNING"),
                started_at=now - timedelta(hours=i),
                completed_at=now - timedelta(hours=i-1) if i < 5 else None,
                duration_ms=60000 + (i * 15000),
                risk_level="MEDIUM" if i % 2 == 0 else "HIGH",
                tenant_id=tenant_id
            )
            db.add(run)
            runs.append(run)
        db.flush()

        # 15. Workflow Notifications (5)
        notif_data = [
            ("SLA Breach Warning", "Weekly QA tests are running 30% slower than usual.", "WARNING", "HIGH"),
            ("New Model Approval Required", "GPT-4 Summarizer is waiting for your review.", "INFO", "MEDIUM"),
            ("Security Scan Completed", "No critical vulnerabilities found.", "SUCCESS", "LOW"),
            ("Audit Pipeline Failure", "Quarterly audit run failed due to data access error.", "ERROR", "CRITICAL"),
            ("Drift Detected", "Customer Churn Predictor shows 5% drift.", "WARNING", "HIGH")
        ]
        notifications = []
        for i, (title, message, n_type, sev) in enumerate(notif_data, 1):
            notif = WorkflowNotification(
                recipient_user_id=users[0].id,
                notification_type=n_type,
                title=f"{prefix}{title}",
                message=message,
                severity=sev,
                status="UNREAD" if i % 2 != 0 else "READ",
                tenant_id=tenant_id
            )
            db.add(notif)
            notifications.append(notif)
        db.flush()

        db.commit()
        logger.info("Successfully populated 5 realistic records for each entity.")
    except Exception as e:
        db.rollback()
        logger.error(f"Error populating data: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    populate_5()

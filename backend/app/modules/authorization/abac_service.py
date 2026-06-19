from uuid import UUID
from datetime import datetime, timezone
import sqlalchemy as sa
from sqlalchemy.future import select
from app.modules.workflow_scheduler.models import ApprovalGroupMember
from app.modules.authorization.models import WorkflowDelegation
from app.modules.registry.models import RegistryAIAgent
import inspect

async def execute_statement(db, stmt):
    res = db.execute(stmt)
    if inspect.isawaitable(res):
        return await res
    return res

async def evaluate_context(subject: dict, object_context: dict, action: str, db) -> tuple[bool, list[str]]:
    allowed = True
    failed_conditions = []
    action_upper = action.upper()

    user_id = subject.get("user_id")
    
    # 1. ACTIVATE_WORKFLOW_SCHEDULE
    if action_upper == "ACTIVATE_WORKFLOW_SCHEDULE":
        risk_level = str(object_context.get("risk_level", "MEDIUM")).upper()
        if risk_level in ["HIGH", "CRITICAL"]:
            approval_group_id = object_context.get("approval_group_id")
            
            # Check membership in the approval group
            is_member = False
            if approval_group_id and user_id:
                member_stmt = select(ApprovalGroupMember.user_id).where(
                    ApprovalGroupMember.approval_group_id == approval_group_id,
                    ApprovalGroupMember.user_id == user_id
                )
                member_res = await execute_statement(db, member_stmt)
                is_member = member_res.scalar() is not None
            
            # Check active delegation
            has_delegation = False
            if not is_member and approval_group_id and user_id:
                now = datetime.now(timezone.utc)
                delegation_stmt = (
                    select(WorkflowDelegation.id)
                    .join(ApprovalGroupMember, ApprovalGroupMember.user_id == WorkflowDelegation.delegator_user_id)
                    .where(
                        WorkflowDelegation.delegatee_user_id == user_id,
                        ApprovalGroupMember.approval_group_id == approval_group_id,
                        WorkflowDelegation.start_at <= now,
                        WorkflowDelegation.end_at >= now,
                        WorkflowDelegation.status == "ACTIVE",
                        WorkflowDelegation.is_deleted == False
                    )
                )
                delegation_res = await execute_statement(db, delegation_stmt)
                has_delegation = delegation_res.scalar() is not None
            
            if not (is_member or has_delegation):
                allowed = False
                failed_conditions.append("High risk schedules require approval group membership or active delegation to activate")

    # 2. ASSIGN_AI_AGENT_TO_WORKFLOW
    elif action_upper == "ASSIGN_AI_AGENT_TO_WORKFLOW":
        agent_id = object_context.get("agent_id")
        requested_mode = str(object_context.get("execution_mode", "RECOMMEND_ONLY")).upper()
        
        agent_registry_mode = None
        if agent_id:
            agent_stmt = select(RegistryAIAgent.execution_mode).where(RegistryAIAgent.id == agent_id)
            agent_res = await execute_statement(db, agent_stmt)
            agent_registry_mode = agent_res.scalar()
        
        reg_mode = str(agent_registry_mode).upper() if agent_registry_mode else "READ_ONLY"
        
        MODE_RANK = {
            "READ_ONLY": 1,
            "RECOMMEND_ONLY": 2,
            "APPROVAL_REQUIRED": 3,
            "LIMITED_EXECUTION": 4,
            "FULLY_BLOCKED": 5
        }
        
        if MODE_RANK.get(requested_mode, 0) > MODE_RANK.get(reg_mode, 0):
            allowed = False
            failed_conditions.append("Requested execution mode exceeds agent max execution mode in registry")

    # 3. RUN_WORKFLOW_SCHEDULE
    elif action_upper == "RUN_WORKFLOW_SCHEDULE":
        schedule_status = str(object_context.get("schedule_status", "DRAFT")).upper()
        if schedule_status != "ACTIVE":
            allowed = False
            failed_conditions.append("Schedule status must be ACTIVE to run")

    # 4. VIEW_WORKFLOW_RUN_OUTPUT
    elif action_upper == "VIEW_WORKFLOW_RUN_OUTPUT":
        output_sens = str(object_context.get("sensitivity_level") or object_context.get("severity") or "PUBLIC").upper()
        
        SENSITIVITY_RANK = {
            "PUBLIC": 1,
            "INTERNAL": 2,
            "RESTRICTED": 3,
            "CONFIDENTIAL": 4
        }
        
        # Mapping severity high/critical to CONFIDENTIAL, medium to RESTRICTED, low to INTERNAL
        if output_sens not in SENSITIVITY_RANK:
            if output_sens in ["HIGH", "CRITICAL"]:
                output_sens = "CONFIDENTIAL"
            elif output_sens == "MEDIUM":
                output_sens = "RESTRICTED"
            elif output_sens == "LOW":
                output_sens = "INTERNAL"
            else:
                output_sens = "PUBLIC"

        # Determine user's maximum clearance based on their roles
        ROLE_CLEARANCE = {
            "SUPER_ADMIN": "CONFIDENTIAL",
            "GOVERNANCE_ADMIN": "CONFIDENTIAL",
            "RISK_MANAGER": "CONFIDENTIAL",
            "AI_REVIEWER": "CONFIDENTIAL",
            "AUDITOR": "RESTRICTED",
            "BUSINESS_USER": "INTERNAL"
        }
        
        user_roles = [r.upper() for r in subject.get("roles", [])]
        user_max_rank = 1  # Default is PUBLIC (rank 1)
        
        for r in user_roles:
            clearance = ROLE_CLEARANCE.get(r, "INTERNAL")
            rank = SENSITIVITY_RANK.get(clearance.upper(), 2)
            if rank > user_max_rank:
                user_max_rank = rank
        
        output_rank = SENSITIVITY_RANK.get(output_sens, 1)
        if output_rank > user_max_rank:
            allowed = False
            failed_conditions.append("User scope is insufficient for output sensitivity level")

    return allowed, failed_conditions

from uuid import UUID
from datetime import datetime, timezone
import sqlalchemy as sa
from sqlalchemy.future import select
from app.modules.authorization.rbac_service import is_in_approval_group, has_active_delegation
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
    user_roles = [r.upper() for r in subject.get("roles", [])]
    user_dept = subject.get("department_id")
    
    # 1. CREATE / ACTIVATE / RUN_NOW
    if action_upper in ["CREATE_WORKFLOW_SCHEDULE", "ACTIVATE_WORKFLOW_SCHEDULE", "RUN_WORKFLOW_SCHEDULE"]:
        # Department check
        owner_dept = object_context.get("owner_department_id")
        if owner_dept and user_dept and str(owner_dept) != str(user_dept):
            if "GOVERNANCE_ADMIN" not in user_roles and "SUPER_ADMIN" not in user_roles:
                allowed = False
                failed_conditions.append("Subject department does not match schedule owner department")

    if action_upper == "ACTIVATE_WORKFLOW_SCHEDULE":
        risk_level = str(object_context.get("risk_level", "MEDIUM")).upper()
        approval_group_id = object_context.get("approval_group_id")
        
        # Risk level approval check
        if risk_level in ["HIGH", "CRITICAL"]:
            if "RISK_MANAGER" not in user_roles and "SUPER_ADMIN" not in user_roles:
                is_member = False
                has_deleg = False
                if approval_group_id and user_id:
                    is_member = await is_in_approval_group(user_id, approval_group_id, db)
                    has_deleg = await has_active_delegation(user_id, approval_group_id, db)
                
                if not (is_member or has_deleg):
                    allowed = False
                    failed_conditions.append("High risk schedules require approval group membership or active delegation to activate")

        # Execution mode check
        exec_mode = str(object_context.get("execution_mode", "READ_ONLY")).upper()
        if exec_mode not in ["READ_ONLY", "RECOMMEND_ONLY"]:
            if "ACTIVATE_HIGH_RISK_SCHEDULE" not in user_roles and "GOVERNANCE_ADMIN" not in user_roles and "SUPER_ADMIN" not in user_roles:
                allowed = False
                failed_conditions.append("Execution mode above RECOMMEND_ONLY requires ACTIVATE_HIGH_RISK_SCHEDULE permission")

        # Write-capable tool check
        write_tools_present = object_context.get("write_tools_present", False)
        approval_required = object_context.get("approval_required", False)
        if write_tools_present and not approval_required:
            allowed = False
            failed_conditions.append("Schedules with write-capable tools must have approval_required=True to be activated")

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
        
        if output_sens not in SENSITIVITY_RANK:
            if output_sens in ["HIGH", "CRITICAL"]:
                output_sens = "CONFIDENTIAL"
            elif output_sens == "MEDIUM":
                output_sens = "RESTRICTED"
            elif output_sens == "LOW":
                output_sens = "INTERNAL"
            else:
                output_sens = "PUBLIC"

        ROLE_CLEARANCE = {
            "SUPER_ADMIN": "CONFIDENTIAL",
            "SYSTEM_ADMIN": "CONFIDENTIAL",
            "GOVERNANCE_ADMIN": "CONFIDENTIAL",
            "RISK_MANAGER": "CONFIDENTIAL",
            "COMPLIANCE_OFFICER": "CONFIDENTIAL",
            "AI_REVIEWER": "CONFIDENTIAL",
            "AI_ASSET_OWNER": "CONFIDENTIAL",
            "BUSINESS_APPROVER": "RESTRICTED",
            "AUDITOR": "RESTRICTED",
            "BUSINESS_USER": "INTERNAL"
        }
        
        user_max_rank = 1
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

# --- Phase 3 Relationship ABAC ---
async def check_relationship_modification_access(subject: dict, object_type: str, object_id: str, db) -> tuple[bool, str]:
    """
    To modify a relationship or responsibility:
    - User must be a GOVERNANCE_ADMIN or SUPER_ADMIN
    - OR User must be an active OWNER of the source object in object_responsibilities
    - OR User's department matches the department of the source object (simplification for MVP)
    """
    user_roles = [r.upper() for r in subject.get("roles", [])]
    if "GOVERNANCE_ADMIN" in user_roles or "SUPER_ADMIN" in user_roles:
        return True, ""
        
    user_id = subject.get("user_id")
    user_dept = subject.get("department_id")
    tenant_id = subject.get("tenant_id")
    
    # Check if user is an active owner in object_responsibilities
    stmt = select(sa.text("1")).select_from(sa.table("object_responsibilities")).where(
        sa.and_(
            sa.text(f"object_type = '{object_type}'"),
            sa.text(f"object_id = '{object_id}'"),
            sa.text("actor_type = 'USER'"),
            sa.text(f"actor_id = '{user_id}'"),
            sa.text("responsibility_type = 'OWNER'"),
            sa.text("status = 'ACTIVE'")
        )
    )
    is_owner = await execute_statement(db, stmt)
    if is_owner.scalar():
        return True, ""
        
    # Check if department matches (assuming valid tables have department_id)
    if user_dept and object_type in ["ai_models", "agents", "workflows", "tools", "departments", "users"]:
        try:
            dept_stmt = select(sa.text("department_id")).select_from(sa.table(object_type)).where(
                sa.text(f"id = '{object_id}'")
            )
            obj_dept = await execute_statement(db, dept_stmt)
            obj_dept_id = obj_dept.scalar()
            if obj_dept_id and str(obj_dept_id) == str(user_dept):
                return True, ""
        except Exception:
            pass # Fallback to deny if table doesn't have department_id
            
    return False, f"User lacks GOVERNANCE_ADMIN role, OWNER responsibility, or department match for {object_type}/{object_id}"


def get_object_sensitivity(db, object_type: str, object_id: str) -> str:
    try:
        from sqlalchemy import text
        normalized = object_type.lower()
        if normalized == "model": normalized = "ai_models"
        elif normalized == "agent": normalized = "agents"
        elif normalized == "tool": normalized = "tools"
        elif normalized == "workflow": normalized = "workflows"
        elif normalized == "datasource" or normalized == "data_source": normalized = "data_sources"
        elif normalized == "department": normalized = "departments"
        elif normalized == "user": normalized = "users"
        
        # Only query tables that actually contain the columns to prevent Postgres transaction aborts
        if normalized in ["tools", "data_sources"]:
            try:
                res = db.execute(text(f"SELECT sensitivity_level FROM {normalized} WHERE id = :id LIMIT 1"), {"id": object_id})
                val = res.scalar()
                if val:
                    return str(val).upper()
            except Exception:
                pass
                
        if normalized in ["workflow_run_outputs", "workflow_run_failures"]:
            try:
                res = db.execute(text(f"SELECT severity FROM {normalized} WHERE id = :id LIMIT 1"), {"id": object_id})
                val = res.scalar()
                if val:
                    return str(val).upper()
            except Exception:
                pass
    except Exception:
        pass
    return "PUBLIC"


async def check_node_read_clearance(subject: dict, object_type: str, object_id: str, db) -> bool:
    user_roles = [r.upper() for r in subject.get("roles", [])]
    if "SUPER_ADMIN" in user_roles or "SYSTEM_ADMIN" in user_roles or "GOVERNANCE_ADMIN" in user_roles:
        return True

    sens = get_object_sensitivity(db, object_type, object_id)
    
    SENSITIVITY_RANK = {
        "PUBLIC": 1,
        "INTERNAL": 2,
        "RESTRICTED": 3,
        "CONFIDENTIAL": 4
    }
    
    if sens not in SENSITIVITY_RANK:
        if sens in ["HIGH", "CRITICAL"]:
            sens = "CONFIDENTIAL"
        elif sens == "MEDIUM":
            sens = "RESTRICTED"
        elif sens == "LOW":
            sens = "INTERNAL"
        else:
            sens = "PUBLIC"

    ROLE_CLEARANCE = {
        "SUPER_ADMIN": "CONFIDENTIAL",
        "SYSTEM_ADMIN": "CONFIDENTIAL",
        "GOVERNANCE_ADMIN": "CONFIDENTIAL",
        "RISK_MANAGER": "CONFIDENTIAL",
        "COMPLIANCE_OFFICER": "CONFIDENTIAL",
        "AI_REVIEWER": "CONFIDENTIAL",
        "AI_ASSET_OWNER": "CONFIDENTIAL",
        "BUSINESS_APPROVER": "RESTRICTED",
        "AUDITOR": "RESTRICTED",
        "BUSINESS_USER": "INTERNAL"
    }

    user_max_rank = 1
    for r in user_roles:
        clearance = ROLE_CLEARANCE.get(r, "INTERNAL")
        rank = SENSITIVITY_RANK.get(clearance.upper(), 2)
        if rank > user_max_rank:
            user_max_rank = rank
            
    output_rank = SENSITIVITY_RANK.get(sens, 1)
    if output_rank > user_max_rank:
        return False
        
    return True

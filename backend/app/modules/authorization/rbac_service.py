from uuid import UUID
import sqlalchemy as sa
from sqlalchemy.future import select
from app.modules.auth.models import User, Role, Permission, user_roles, role_permissions
from app.modules.registry.models import GuardianUser
from app.modules.workflow_scheduler.models import ApprovalGroupMember
from app.modules.authorization.models import WorkflowDelegation
from datetime import datetime, timezone
import inspect

async def execute_statement(db, stmt):
    res = db.execute(stmt)
    if inspect.isawaitable(res):
        return await res
    return res

async def check_permission(user_id: UUID, permission_code: str, db) -> bool:
    email_stmt = select(GuardianUser.email).where(GuardianUser.id == user_id)
    email_res = await execute_statement(db, email_stmt)
    email = email_res.scalar()
    if not email:
        return False
    
    user_stmt = select(User.id).where(User.email == email)
    user_res = await execute_statement(db, user_stmt)
    int_user_id = user_res.scalar()
    if not int_user_id:
        return False
    
    perm_stmt = (
        select(Permission.id)
        .join(role_permissions, role_permissions.c.permission_id == Permission.id)
        .join(user_roles, user_roles.c.role_id == role_permissions.c.role_id)
        .where(user_roles.c.user_id == int_user_id)
        .where(sa.func.lower(Permission.permission_code) == sa.func.lower(permission_code))
    )
    perm_res = await execute_statement(db, perm_stmt)
    return perm_res.scalar() is not None

async def get_user_roles(user_id: UUID, db) -> list[str]:
    roles = []
    g_user_stmt = select(GuardianUser).where(GuardianUser.id == user_id)
    g_user_res = await execute_statement(db, g_user_stmt)
    g_user = g_user_res.scalar()
    if g_user:
        roles_stmt = (
            select(Role.role_code)
            .join(user_roles, user_roles.c.role_id == Role.id)
            .join(User, User.id == user_roles.c.user_id)
            .where(User.email == g_user.email)
        )
        roles_res = await execute_statement(db, roles_stmt)
        roles = [r[0] for r in roles_res.fetchall()]
        
        from app.modules.registry.models import RegistryRole
        reg_role_stmt = select(RegistryRole.role_code).where(RegistryRole.id == g_user.role_id)
        reg_role_res = await execute_statement(db, reg_role_stmt)
        reg_role_code = reg_role_res.scalar()
        if reg_role_code and reg_role_code not in roles:
            roles.append(reg_role_code)
    return roles

async def is_in_approval_group(user_id: UUID, approval_group_id: UUID, db) -> bool:
    member_stmt = select(ApprovalGroupMember.id).where(
        ApprovalGroupMember.approval_group_id == approval_group_id,
        ApprovalGroupMember.user_id == user_id
    )
    member_res = await execute_statement(db, member_stmt)
    return member_res.scalar() is not None

async def has_active_delegation(user_id: UUID, approval_group_id: UUID, db) -> bool:
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
    return delegation_res.scalar() is not None

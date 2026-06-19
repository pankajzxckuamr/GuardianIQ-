from uuid import UUID
import sqlalchemy as sa
from sqlalchemy.future import select
from app.modules.auth.models import User, Permission, user_roles, role_permissions
from app.modules.registry.models import GuardianUser
import inspect

async def execute_statement(db, stmt):
    res = db.execute(stmt)
    if inspect.isawaitable(res):
        return await res
    return res

async def check_permission(user_id: UUID, permission_code: str, db) -> bool:
    # 1. Look up the email of the guardian user by their UUID
    email_stmt = select(GuardianUser.email).where(GuardianUser.id == user_id)
    email_res = await execute_statement(db, email_stmt)
    email = email_res.scalar()
    if not email:
        return False
    
    # 2. Look up the integer user id from the users table by email
    user_stmt = select(User.id).where(User.email == email)
    user_res = await execute_statement(db, user_stmt)
    int_user_id = user_res.scalar()
    if not int_user_id:
        return False
    
    # 3. Query user_roles -> role_permissions -> permissions to verify permission_code
    perm_stmt = (
        select(Permission.id)
        .join(role_permissions, role_permissions.c.permission_id == Permission.id)
        .join(user_roles, user_roles.c.role_id == role_permissions.c.role_id)
        .where(user_roles.c.user_id == int_user_id)
        .where(sa.func.lower(Permission.permission_code) == sa.func.lower(permission_code))
    )
    perm_res = await execute_statement(db, perm_stmt)
    return perm_res.scalar() is not None

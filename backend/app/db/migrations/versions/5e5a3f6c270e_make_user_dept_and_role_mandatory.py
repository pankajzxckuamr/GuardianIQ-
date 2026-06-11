"""make_user_dept_and_role_mandatory

Revision ID: 5e5a3f6c270e
Revises: 78f13eb6750a
Create Date: 2026-06-11 13:54:38.426827

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5e5a3f6c270e'
down_revision: Union[str, Sequence[str], None] = '78f13eb6750a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Backfill existing null department_id and role_id values
    connection = op.get_bind()
    
    # Get a department ID to use as fallback
    dept_res = connection.execute(
        sa.text("SELECT id FROM registry_departments WHERE department_code = 'COMPLIANCE'")
    ).fetchone()
    if not dept_res:
        dept_res = connection.execute(
            sa.text("SELECT id FROM registry_departments LIMIT 1")
        ).fetchone()
    
    # Get a role ID to use as fallback
    role_res = connection.execute(
        sa.text("SELECT id FROM registry_roles WHERE role_code = 'REVIEWER'")
    ).fetchone()
    if not role_res:
        role_res = connection.execute(
            sa.text("SELECT id FROM registry_roles LIMIT 1")
        ).fetchone()
        
    if dept_res:
        dept_id = dept_res[0]
        connection.execute(
            sa.text("UPDATE guardian_users SET department_id = :dept_id WHERE department_id IS NULL"),
            {"dept_id": dept_id}
        )
        
    if role_res:
        role_id = role_res[0]
        connection.execute(
            sa.text("UPDATE guardian_users SET role_id = :role_id WHERE role_id IS NULL"),
            {"role_id": role_id}
        )

    # 2. Alter columns to nullable=False
    op.alter_column('guardian_users', 'department_id',
               existing_type=sa.UUID(),
               nullable=False)
    op.alter_column('guardian_users', 'role_id',
               existing_type=sa.UUID(),
               nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column('guardian_users', 'role_id',
               existing_type=sa.UUID(),
               nullable=True)
    op.alter_column('guardian_users', 'department_id',
               existing_type=sa.UUID(),
               nullable=True)

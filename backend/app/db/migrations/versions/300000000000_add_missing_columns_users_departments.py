"""add_missing_columns_users_departments

Revision ID: 300000000000
Revises: 2ffed4997630
Create Date: 2026-05-28 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '300000000000'
down_revision: Union[str, Sequence[str], None] = '2ffed4997630'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # users table additions
    users_columns = [c['name'] for c in inspector.get_columns('users')]
    if 'full_name' not in users_columns:
        op.add_column('users', sa.Column('full_name', sa.String(length=200), nullable=True))
    if 'status' not in users_columns:
        op.add_column('users', sa.Column('status', sa.String(length=30), nullable=False, server_default='ACTIVE'))
    if 'created_at' not in users_columns:
        op.add_column('users', sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')))
    if 'updated_at' not in users_columns:
        op.add_column('users', sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')))

    # departments table additions
    depts_columns = [c['name'] for c in inspector.get_columns('departments')]
    if 'parent_id' not in depts_columns:
        op.add_column('departments', sa.Column('parent_id', sa.Integer(), nullable=True))
    if 'owner_user_id' not in depts_columns:
        op.add_column('departments', sa.Column('owner_user_id', sa.Integer(), nullable=True))
    if 'status' not in depts_columns:
        op.add_column('departments', sa.Column('status', sa.String(length=30), nullable=False, server_default='ACTIVE'))
    if 'created_at' not in depts_columns:
        op.add_column('departments', sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')))
    if 'updated_at' not in depts_columns:
        op.add_column('departments', sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')))

    # foreign key constraints
    existing_fks = [fk['name'] for fk in inspector.get_foreign_keys('departments')]
    if 'fk_departments_parent_id' not in existing_fks:
        op.create_foreign_key('fk_departments_parent_id', 'departments', 'departments', ['parent_id'], ['id'], ondelete='SET NULL')
    if 'fk_departments_owner_user_id' not in existing_fks:
        op.create_foreign_key('fk_departments_owner_user_id', 'departments', 'users', ['owner_user_id'], ['id'], ondelete='SET NULL')


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # Drop foreign keys first
    existing_fks = [fk['name'] for fk in inspector.get_foreign_keys('departments')]
    if 'fk_departments_owner_user_id' in existing_fks:
        op.drop_constraint('fk_departments_owner_user_id', 'departments', type_='foreignkey')
    if 'fk_departments_parent_id' in existing_fks:
        op.drop_constraint('fk_departments_parent_id', 'departments', type_='foreignkey')

    # departments removals
    depts_columns = [c['name'] for c in inspector.get_columns('departments')]
    if 'updated_at' in depts_columns:
        op.drop_column('departments', 'updated_at')
    if 'created_at' in depts_columns:
        op.drop_column('departments', 'created_at')
    if 'status' in depts_columns:
        op.drop_column('departments', 'status')
    if 'owner_user_id' in depts_columns:
        op.drop_column('departments', 'owner_user_id')
    if 'parent_id' in depts_columns:
        op.drop_column('departments', 'parent_id')

    # users removals
    users_columns = [c['name'] for c in inspector.get_columns('users')]
    if 'updated_at' in users_columns:
        op.drop_column('users', 'updated_at')
    if 'created_at' in users_columns:
        op.drop_column('users', 'created_at')
    if 'status' in users_columns:
        op.drop_column('users', 'status')
    if 'full_name' in users_columns:
        op.drop_column('users', 'full_name')


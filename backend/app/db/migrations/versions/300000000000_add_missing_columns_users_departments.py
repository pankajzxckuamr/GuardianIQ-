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
    # users table additions
    op.add_column('users', sa.Column('full_name', sa.String(length=200), nullable=True))
    op.add_column('users', sa.Column('status', sa.String(length=30), nullable=False, server_default='ACTIVE'))
    op.add_column('users', sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')))
    op.add_column('users', sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')))

    # departments table additions
    op.add_column('departments', sa.Column('parent_id', sa.Integer(), nullable=True))
    op.add_column('departments', sa.Column('owner_user_id', sa.Integer(), nullable=True))
    op.add_column('departments', sa.Column('status', sa.String(length=30), nullable=False, server_default='ACTIVE'))
    op.add_column('departments', sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')))
    op.add_column('departments', sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')))

    # foreign key constraints
    op.create_foreign_key('fk_departments_parent_id', 'departments', 'departments', ['parent_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_departments_owner_user_id', 'departments', 'users', ['owner_user_id'], ['id'], ondelete='SET NULL')


def downgrade() -> None:
    # Drop foreign keys first
    op.drop_constraint('fk_departments_owner_user_id', 'departments', type_='foreignkey')
    op.drop_constraint('fk_departments_parent_id', 'departments', type_='foreignkey')

    # departments removals
    op.drop_column('departments', 'updated_at')
    op.drop_column('departments', 'created_at')
    op.drop_column('departments', 'status')
    op.drop_column('departments', 'owner_user_id')
    op.drop_column('departments', 'parent_id')

    # users removals
    op.drop_column('users', 'updated_at')
    op.drop_column('users', 'created_at')
    op.drop_column('users', 'status')
    op.drop_column('users', 'full_name')

"""Add registry_register_all table

Revision ID: 5e692c1093bf
Revises: e716f1929aa1
Create Date: 2026-06-09 17:23:40.537266

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '5e692c1093bf'
down_revision: Union[str, Sequence[str], None] = 'e716f1929aa1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('registry_register_all',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('department_id', sa.UUID(), nullable=True),
    sa.Column('role_id', sa.UUID(), nullable=True),
    sa.Column('user_id', sa.UUID(), nullable=True),
    sa.Column('data_source_id', sa.UUID(), nullable=True),
    sa.Column('model_id', sa.UUID(), nullable=True),
    sa.Column('agent_id', sa.UUID(), nullable=True),
    sa.Column('tool_id', sa.UUID(), nullable=True),
    sa.Column('workflow_id', sa.UUID(), nullable=True),
    sa.Column('created_at', sa.TIMESTAMP(), nullable=False),
    sa.Column('created_by', sa.UUID(), nullable=True),
    sa.ForeignKeyConstraint(['agent_id'], ['registry_ai_agents.id'], ),
    sa.ForeignKeyConstraint(['data_source_id'], ['registry_data_sources.id'], ),
    sa.ForeignKeyConstraint(['department_id'], ['registry_departments.id'], ),
    sa.ForeignKeyConstraint(['model_id'], ['registry_ai_models.id'], ),
    sa.ForeignKeyConstraint(['role_id'], ['registry_roles.id'], ),
    sa.ForeignKeyConstraint(['tool_id'], ['registry_tools.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['guardian_users.id'], ),
    sa.ForeignKeyConstraint(['workflow_id'], ['registry_workflows.id'], ),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('registry_register_all')


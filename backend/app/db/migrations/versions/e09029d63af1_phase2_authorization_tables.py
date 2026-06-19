"""phase2_authorization_tables

Revision ID: e09029d63af1
Revises: 556b8fc07b20
Create Date: 2026-06-19 11:49:20.342042

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision: str = 'e09029d63af1'
down_revision: Union[str, Sequence[str], None] = '556b8fc07b20'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def get_standard_columns():
    return [
        sa.Column('id', sa.UUID(), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', sa.UUID(), sa.ForeignKey('guardian_users.id'), nullable=False),
        sa.Column('created_by', sa.UUID(), sa.ForeignKey('guardian_users.id'), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_by', sa.UUID(), sa.ForeignKey('guardian_users.id'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('version_no', sa.Integer(), server_default='1', nullable=True),
        sa.Column('is_deleted', sa.Boolean(), server_default='FALSE', nullable=True),
        sa.Column('metadata_json', JSONB(astext_type=sa.Text()), server_default='{}', nullable=True),
    ]


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'approval_group_members',
        sa.Column('approval_group_id', sa.UUID(), sa.ForeignKey('approval_groups.id', ondelete='CASCADE'), primary_key=True, nullable=False),
        sa.Column('user_id', sa.UUID(), sa.ForeignKey('guardian_users.id', ondelete='CASCADE'), primary_key=True, nullable=False)
    )

    op.create_table(
        'workflow_delegations',
        *(get_standard_columns() + [
            sa.Column('delegator_user_id', sa.UUID(), sa.ForeignKey('guardian_users.id'), nullable=False),
            sa.Column('delegatee_user_id', sa.UUID(), sa.ForeignKey('guardian_users.id'), nullable=False),
            sa.Column('start_at', sa.TIMESTAMP(timezone=True), nullable=False),
            sa.Column('end_at', sa.TIMESTAMP(timezone=True), nullable=False),
            sa.Column('status', sa.String(length=50), server_default='ACTIVE', nullable=True)
        ])
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('workflow_delegations')
    op.drop_table('approval_group_members')


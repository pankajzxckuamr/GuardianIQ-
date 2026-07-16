"""add_phase3_composite_indexes

Revision ID: 73433bbfa6a5
Revises: 038855822792
Create Date: 2026-07-16 12:58:29.468805

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '73433bbfa6a5'
down_revision: Union[str, Sequence[str], None] = '038855822792'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. generic_relationships
    op.create_index(
        'ix_composite_rel_source',
        'generic_relationships',
        ['tenant_id', 'source_type', 'source_id', 'relationship_type', 'status'],
        unique=False
    )
    op.create_index(
        'ix_composite_rel_target',
        'generic_relationships',
        ['tenant_id', 'target_type', 'target_id', 'relationship_type', 'status'],
        unique=False
    )
    op.create_index(
        'ix_composite_rel_lifecycle',
        'generic_relationships',
        ['tenant_id', 'status', 'effective_from', 'effective_to'],
        unique=False
    )

    # 2. object_responsibilities
    op.create_index(
        'ix_composite_resp_object',
        'object_responsibilities',
        ['tenant_id', 'object_type', 'object_id', 'responsibility_type', 'status'],
        unique=False
    )

    # 3. policy_bindings
    op.create_index(
        'ix_composite_pb_target',
        'policy_bindings',
        ['tenant_id', 'target_type', 'target_id', 'status'],
        unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_composite_pb_target', table_name='policy_bindings')
    op.drop_index('ix_composite_resp_object', table_name='object_responsibilities')
    op.drop_index('ix_composite_rel_lifecycle', table_name='generic_relationships')
    op.drop_index('ix_composite_rel_target', table_name='generic_relationships')
    op.drop_index('ix_composite_rel_source', table_name='generic_relationships')

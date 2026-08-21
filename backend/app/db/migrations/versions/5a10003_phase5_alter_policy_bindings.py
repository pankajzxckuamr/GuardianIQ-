"""phase5_alter_policy_bindings

Revision ID: 5a10003_phase5_alter_policy_bindings
Revises: 5a10002_phase5_agent_boundary
Create Date: 2026-08-17 13:40:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '5a10003_p5_bind'
down_revision: Union[str, Sequence[str], None] = '5a10002_p5_agnt'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add missing columns to policy_bindings
    op.add_column(
        'policy_bindings',
        sa.Column('version_strategy', sa.String(length=50), server_default='LATEST', nullable=False)
    )
    op.add_column(
        'policy_bindings',
        sa.Column('pinned_policy_version_id', postgresql.UUID(as_uuid=True), nullable=True)
    )
    op.add_column(
        'policy_bindings',
        sa.Column('condition_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True)
    )

    # 2. Update FKs and constraints
    # Drop old FK to policies.id if present
    try:
        op.drop_constraint('policy_bindings_policy_id_fkey', 'policy_bindings', type_='foreignkey')
    except Exception:
        pass

    # Add new FKs
    op.create_foreign_key(
        'policy_bindings_policy_id_fkey',
        'policy_bindings',
        'governance_policies',
        ['policy_id'],
        ['id'],
        ondelete='CASCADE'
    )
    op.create_foreign_key(
        'policy_bindings_pinned_version_fkey',
        'policy_bindings',
        'policy_versions',
        ['pinned_policy_version_id'],
        ['id'],
        ondelete='SET NULL'
    )

    # 3. Performance indexes
    op.create_index('idx_policy_bindings_target_status', 'policy_bindings', ['target_type', 'target_id', 'status'], unique=False)
    op.create_index('idx_policy_bindings_policy_status', 'policy_bindings', ['policy_id', 'status'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_policy_bindings_policy_status', table_name='policy_bindings')
    op.drop_index('idx_policy_bindings_target_status', table_name='policy_bindings')
    
    try:
        op.drop_constraint('policy_bindings_pinned_version_fkey', 'policy_bindings', type_='foreignkey')
    except Exception:
        pass
    try:
        op.drop_constraint('policy_bindings_policy_id_fkey', 'policy_bindings', type_='foreignkey')
    except Exception:
        pass

    # Reconnect to legacy policies table if exists
    try:
        op.create_foreign_key(
            'policy_bindings_policy_id_fkey',
            'policy_bindings',
            'policies',
            ['policy_id'],
            ['id']
        )
    except Exception:
        pass

    op.drop_column('policy_bindings', 'condition_json')
    op.drop_column('policy_bindings', 'pinned_policy_version_id')
    op.drop_column('policy_bindings', 'version_strategy')

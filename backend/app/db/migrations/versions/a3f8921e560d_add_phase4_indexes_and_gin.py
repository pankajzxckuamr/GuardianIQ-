"""add_phase4_indexes_and_gin

Revision ID: a3f8921e560d
Revises: e4a2b91c801d
Create Date: 2026-07-31 11:49:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a3f8921e560d'
down_revision: Union[str, Sequence[str], None] = 'e4a2b91c801d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. idx_events_tenant_time
    op.create_index(
        'idx_events_tenant_time',
        'governance_events',
        ['tenant_id', sa.text('occurred_at DESC')],
        unique=False
    )

    # 2. idx_events_type_time
    op.create_index(
        'idx_events_type_time',
        'governance_events',
        ['event_type', sa.text('occurred_at DESC')],
        unique=False
    )

    # 3. idx_events_category_time
    op.create_index(
        'idx_events_category_time',
        'governance_events',
        ['event_category', sa.text('occurred_at DESC')],
        unique=False
    )

    # 4. idx_events_correlation
    op.create_index(
        'idx_events_correlation',
        'governance_events',
        ['correlation_id'],
        unique=False,
        postgresql_where=sa.text('correlation_id IS NOT NULL')
    )

    # 5. idx_events_subject_gin (GIN index on subject_json)
    op.create_index(
        'idx_events_subject_gin',
        'governance_events',
        ['subject_json'],
        unique=False,
        postgresql_using='gin'
    )

    # 6. idx_events_actor_gin (GIN index on actor_json)
    op.create_index(
        'idx_events_actor_gin',
        'governance_events',
        ['actor_json'],
        unique=False,
        postgresql_using='gin'
    )

    # 7. idx_outbox_status_retry
    op.create_index(
        'idx_outbox_status_retry',
        'event_outbox',
        ['status', 'next_retry_at'],
        unique=False
    )

    # 8. idx_processing_event_consumer
    op.create_index(
        'idx_processing_event_consumer',
        'event_processing_log',
        ['event_id', 'consumer_id'],
        unique=False
    )

    # 9. idx_dead_letter_status
    op.create_index(
        'idx_dead_letter_status',
        'event_dead_letter',
        ['tenant_id', 'status'],
        unique=False
    )


def downgrade() -> None:
    op.drop_index('idx_dead_letter_status', table_name='event_dead_letter')
    op.drop_index('idx_processing_event_consumer', table_name='event_processing_log')
    op.drop_index('idx_outbox_status_retry', table_name='event_outbox')
    op.drop_index('idx_events_actor_gin', table_name='governance_events', postgresql_using='gin')
    op.drop_index('idx_events_subject_gin', table_name='governance_events', postgresql_using='gin')
    op.drop_index('idx_events_correlation', table_name='governance_events')
    op.drop_index('idx_events_category_time', table_name='governance_events')
    op.drop_index('idx_events_type_time', table_name='governance_events')
    op.drop_index('idx_events_tenant_time', table_name='governance_events')

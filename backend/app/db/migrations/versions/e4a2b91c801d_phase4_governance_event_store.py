"""phase4_governance_event_store

Revision ID: e4a2b91c801d
Revises: 73433bbfa6a5
Create Date: 2026-07-31 11:43:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# revision identifiers, used by Alembic.
revision: str = 'e4a2b91c801d'
down_revision: Union[str, Sequence[str], None] = '73433bbfa6a5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create governance_events
    op.create_table(
        'governance_events',
        sa.Column('event_id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('event_category', sa.String(50), nullable=False),
        sa.Column('event_version', sa.String(20), nullable=False, server_default='1.0'),
        sa.Column('occurred_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('recorded_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('source_service', sa.String(100), nullable=False),
        sa.Column('source_system', sa.String(100), nullable=False, server_default='guardianiq-backend'),
        sa.Column('actor_json', JSONB(), nullable=False),
        sa.Column('subject_json', JSONB(), nullable=False),
        sa.Column('correlation_id', UUID(as_uuid=True), nullable=True),
        sa.Column('causation_id', UUID(as_uuid=True), nullable=True),
        sa.Column('risk_context_json', JSONB(), nullable=True),
        sa.Column('policy_context_json', JSONB(), nullable=True),
        sa.Column('payload_json', JSONB(), nullable=False),
        sa.Column('classification', sa.String(50), nullable=False, server_default='INTERNAL'),
        sa.Column('retention_class', sa.String(50), nullable=False, server_default='STANDARD_90_DAYS'),
        sa.Column('event_hash', sa.String(64), nullable=False),
        sa.Column('previous_event_hash', sa.String(64), nullable=True),
    )
    op.create_index('ix_governance_events_tenant_id', 'governance_events', ['tenant_id'])
    op.create_index('ix_governance_events_event_type', 'governance_events', ['event_type'])
    op.create_index('ix_governance_events_event_category', 'governance_events', ['event_category'])
    op.create_index('ix_governance_events_occurred_at', 'governance_events', ['occurred_at'])
    op.create_index('ix_governance_events_correlation_id', 'governance_events', ['correlation_id'])

    # 2. Create event_outbox
    op.create_table(
        'event_outbox',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('event_id', UUID(as_uuid=True), sa.ForeignKey('governance_events.event_id', ondelete='CASCADE'), nullable=False),
        sa.Column('tenant_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('destination', sa.String(100), nullable=False, server_default='internal_bus'),
        sa.Column('payload_json', JSONB(), nullable=False),
        sa.Column('status', sa.String(30), nullable=False, server_default='PENDING'),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('max_retries', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('dispatched_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('next_retry_at', sa.TIMESTAMP(timezone=True), nullable=True),
    )
    op.create_index('ix_event_outbox_status_next_retry', 'event_outbox', ['status', 'next_retry_at'])
    op.create_index('ix_event_outbox_tenant_id', 'event_outbox', ['tenant_id'])

    # 3. Create event_processing_log
    op.create_table(
        'event_processing_log',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('event_id', UUID(as_uuid=True), sa.ForeignKey('governance_events.event_id', ondelete='CASCADE'), nullable=False),
        sa.Column('consumer_id', sa.String(100), nullable=False),
        sa.Column('status', sa.String(30), nullable=False, server_default='PROCESSED'),
        sa.Column('processed_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('execution_time_ms', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.UniqueConstraint('event_id', 'consumer_id', name='uq_event_consumer'),
    )
    op.create_index('ix_event_processing_log_event_id', 'event_processing_log', ['event_id'])

    # 4. Create event_dead_letter
    op.create_table(
        'event_dead_letter',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('outbox_id', UUID(as_uuid=True), sa.ForeignKey('event_outbox.id', ondelete='CASCADE'), nullable=False),
        sa.Column('event_id', UUID(as_uuid=True), sa.ForeignKey('governance_events.event_id', ondelete='CASCADE'), nullable=False),
        sa.Column('tenant_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('failure_reason', sa.Text(), nullable=False),
        sa.Column('failed_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('retry_attempts', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(30), nullable=False, server_default='UNRESOLVED'),
        sa.Column('resolved_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('resolved_by', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
    )
    op.create_index('ix_event_dead_letter_tenant_status', 'event_dead_letter', ['tenant_id', 'status'])

    # 5. Create event_schema_registry
    op.create_table(
        'event_schema_registry',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('version', sa.String(20), nullable=False, server_default='1.0'),
        sa.Column('json_schema', JSONB(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('created_by', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.UniqueConstraint('event_type', 'version', name='uq_event_type_version'),
    )

    # 6. Create event_retention_rules
    op.create_table(
        'event_retention_rules',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('event_category', sa.String(50), nullable=False),
        sa.Column('retention_days', sa.Integer(), nullable=False, server_default='90'),
        sa.Column('action', sa.String(30), nullable=False, server_default='PURGE'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint('tenant_id', 'event_category', name='uq_tenant_category_retention'),
    )

    # 7. Create event_export_log
    op.create_table(
        'event_export_log',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('exported_by', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('filter_params_json', JSONB(), nullable=False),
        sa.Column('format', sa.String(20), nullable=False, server_default='JSON'),
        sa.Column('record_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('file_hash', sa.String(64), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_event_export_log_tenant_id', 'event_export_log', ['tenant_id'])


def downgrade() -> None:
    op.drop_table('event_export_log')
    op.drop_table('event_retention_rules')
    op.drop_table('event_schema_registry')
    op.drop_table('event_dead_letter')
    op.drop_table('event_processing_log')
    op.drop_table('event_outbox')
    op.drop_table('governance_events')

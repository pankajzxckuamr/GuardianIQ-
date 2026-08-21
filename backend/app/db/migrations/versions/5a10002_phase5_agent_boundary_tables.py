"""phase5_agent_boundary_tables

Revision ID: 5a10002_phase5_agent_boundary
Revises: 5a10001_phase5_policy_engine
Create Date: 2026-08-17 13:35:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '5a10002_p5_agnt'
down_revision: Union[str, Sequence[str], None] = '5a10001_p5_pol'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. agent_runtime_boundaries
    op.create_table(
        'agent_runtime_boundaries',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=True),
        sa.Column('version_no', sa.Integer(), server_default='1', nullable=True),
        sa.Column('is_deleted', sa.Boolean(), server_default='FALSE', nullable=True),
        sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=True),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('agents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('max_autonomy_level', sa.String(length=50), server_default='HUMAN_SUPERVISED', nullable=False),
        sa.Column('allowed_access_modes_json', postgresql.JSONB(astext_type=sa.Text()), server_default='["READ_ONLY"]', nullable=False),
        sa.Column('rate_limit_per_minute', sa.Integer(), nullable=True),
        sa.Column('max_concurrency', sa.Integer(), server_default='5', nullable=True),
        sa.Column('allow_sub_agent_spawn', sa.Boolean(), server_default='FALSE', nullable=False),
        sa.Column('require_approval_threshold', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='TRUE', nullable=False),
    )
    op.create_index('ix_agent_runtime_boundaries_agent_id', 'agent_runtime_boundaries', ['agent_id'], unique=True)

    # 2. tool_capabilities
    op.create_table(
        'tool_capabilities',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=True),
        sa.Column('version_no', sa.Integer(), server_default='1', nullable=True),
        sa.Column('is_deleted', sa.Boolean(), server_default='FALSE', nullable=True),
        sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=True),
        sa.Column('tool_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tools.id', ondelete='CASCADE'), nullable=False),
        sa.Column('capability_name', sa.String(length=150), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('access_mode', sa.String(length=50), server_default='EXECUTE', nullable=False),
        sa.Column('requires_approval', sa.Boolean(), server_default='FALSE', nullable=False),
        sa.Column('input_schema_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('rate_limit', sa.Integer(), nullable=True),
    )
    op.create_index('idx_tool_capabilities_lookup', 'tool_capabilities', ['tool_id', 'capability_name'], unique=False)

    # 3. agent_tool_permissions
    op.create_table(
        'agent_tool_permissions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=True),
        sa.Column('version_no', sa.Integer(), server_default='1', nullable=True),
        sa.Column('is_deleted', sa.Boolean(), server_default='FALSE', nullable=True),
        sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=True),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('agents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('tool_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tools.id', ondelete='CASCADE'), nullable=False),
        sa.Column('capability_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tool_capabilities.id', ondelete='CASCADE'), nullable=True),
        sa.Column('permission_level', sa.String(length=50), server_default='EXECUTE', nullable=False),
        sa.Column('max_calls_per_run', sa.Integer(), nullable=True),
        sa.Column('require_approval', sa.Boolean(), server_default='FALSE', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='TRUE', nullable=False),
    )
    op.create_index('idx_agent_tool_perms_lookup', 'agent_tool_permissions', ['agent_id', 'tool_id', 'is_active'], unique=False)

    # 4. data_source_fields
    op.create_table(
        'data_source_fields',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=True),
        sa.Column('version_no', sa.Integer(), server_default='1', nullable=True),
        sa.Column('is_deleted', sa.Boolean(), server_default='FALSE', nullable=True),
        sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=True),
        sa.Column('data_source_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('data_sources.id', ondelete='CASCADE'), nullable=False),
        sa.Column('field_name', sa.String(length=255), nullable=False),
        sa.Column('data_type', sa.String(length=100), server_default='STRING', nullable=False),
        sa.Column('classification', sa.String(length=50), server_default='INTERNAL', nullable=False),
        sa.Column('sensitivity_level', sa.String(length=50), server_default='MEDIUM', nullable=False),
        sa.Column('is_pii', sa.Boolean(), server_default='FALSE', nullable=False),
        sa.Column('masking_strategy', sa.String(length=50), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='TRUE', nullable=False),
    )
    op.create_index('idx_data_source_fields_lookup', 'data_source_fields', ['data_source_id', 'field_name'], unique=False)

    # 5. agent_data_permissions
    op.create_table(
        'agent_data_permissions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=True),
        sa.Column('version_no', sa.Integer(), server_default='1', nullable=True),
        sa.Column('is_deleted', sa.Boolean(), server_default='FALSE', nullable=True),
        sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=True),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('agents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('data_source_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('data_sources.id', ondelete='CASCADE'), nullable=False),
        sa.Column('field_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('data_source_fields.id', ondelete='CASCADE'), nullable=True),
        sa.Column('allowed_operations_json', postgresql.JSONB(astext_type=sa.Text()), server_default='["READ"]', nullable=False),
        sa.Column('max_classification', sa.String(length=50), server_default='CONFIDENTIAL', nullable=False),
        sa.Column('max_sensitivity', sa.String(length=50), server_default='HIGH', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='TRUE', nullable=False),
    )
    op.create_index('idx_agent_data_perms_lookup', 'agent_data_permissions', ['agent_id', 'data_source_id', 'is_active'], unique=False)


def downgrade() -> None:
    op.drop_table('agent_data_permissions')
    op.drop_table('data_source_fields')
    op.drop_table('agent_tool_permissions')
    op.drop_table('tool_capabilities')
    op.drop_table('agent_runtime_boundaries')

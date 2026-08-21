"""phase5_policy_engine_tables

Revision ID: 5a10001_phase5_policy_engine
Revises: a3f8921e560d
Create Date: 2026-08-17 13:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '5a10001_p5_pol'
down_revision: Union[str, Sequence[str], None] = 'a3f8921e560d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. governance_policies
    op.create_table(
        'governance_policies',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=True),
        sa.Column('version_no', sa.Integer(), server_default='1', nullable=True),
        sa.Column('is_deleted', sa.Boolean(), server_default='FALSE', nullable=True),
        sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=True),
        sa.Column('status', sa.String(length=30), server_default='ACTIVE', nullable=False),
        sa.Column('owner_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('policy_code', sa.String(length=100), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=100), server_default='GENERAL', nullable=False),
        sa.Column('enforcement_mode', sa.String(length=50), server_default='BLOCKING', nullable=False),
        sa.Column('priority', sa.Integer(), server_default='100', nullable=False),
        sa.Column('effective_from', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('effective_to', sa.TIMESTAMP(timezone=True), nullable=True),
    )
    op.create_index('ix_governance_policies_policy_code', 'governance_policies', ['policy_code'], unique=True)
    op.create_index('idx_gov_policies_tenant_status', 'governance_policies', ['tenant_id', 'status'], unique=False)
    op.create_index('idx_gov_policies_effective', 'governance_policies', ['effective_from', 'effective_to'], unique=False)

    # 2. policy_versions
    op.create_table(
        'policy_versions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=True),
        sa.Column('version_no', sa.Integer(), server_default='1', nullable=True),
        sa.Column('is_deleted', sa.Boolean(), server_default='FALSE', nullable=True),
        sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=True),
        sa.Column('policy_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('governance_policies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=50), server_default='DRAFT', nullable=False),
        sa.Column('changelog', sa.Text(), nullable=True),
        sa.Column('rules_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('activated_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('activated_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('checksum', sa.String(length=64), nullable=True),
    )
    op.create_index('idx_policy_versions_policy_num', 'policy_versions', ['policy_id', 'version_number'], unique=True)
    op.create_index('idx_policy_versions_status', 'policy_versions', ['policy_id', 'status'], unique=False)

    # 3. policy_rules
    op.create_table(
        'policy_rules',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=True),
        sa.Column('version_no', sa.Integer(), server_default='1', nullable=True),
        sa.Column('is_deleted', sa.Boolean(), server_default='FALSE', nullable=True),
        sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=True),
        sa.Column('policy_version_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('policy_versions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('rule_code', sa.String(length=100), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('rule_type', sa.String(length=100), nullable=False),
        sa.Column('target_type', sa.String(length=100), nullable=False),
        sa.Column('target_id', sa.String(length=255), nullable=True),
        sa.Column('condition_expression', sa.Text(), nullable=True),
        sa.Column('condition_json', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('action', sa.String(length=50), server_default='DENY', nullable=False),
        sa.Column('severity', sa.String(length=50), server_default='HIGH', nullable=False),
        sa.Column('execution_order', sa.Integer(), server_default='10', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='TRUE', nullable=False),
    )
    op.create_index('idx_policy_rules_version', 'policy_rules', ['policy_version_id', 'execution_order'], unique=False)
    op.create_index('idx_policy_rules_target', 'policy_rules', ['target_type', 'target_id'], unique=False)

    # 4. policy_exceptions
    op.create_table(
        'policy_exceptions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=True),
        sa.Column('version_no', sa.Integer(), server_default='1', nullable=True),
        sa.Column('is_deleted', sa.Boolean(), server_default='FALSE', nullable=True),
        sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=True),
        sa.Column('policy_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('governance_policies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('policy_version_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('policy_versions.id', ondelete='SET NULL'), nullable=True),
        sa.Column('target_type', sa.String(length=100), nullable=False),
        sa.Column('target_id', sa.String(length=255), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('approved_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('valid_from', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('valid_to', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('status', sa.String(length=50), server_default='ACTIVE', nullable=False),
    )
    op.create_index('idx_policy_exceptions_lookup', 'policy_exceptions', ['policy_id', 'target_type', 'target_id', 'status'], unique=False)


def downgrade() -> None:
    op.drop_table('policy_exceptions')
    op.drop_table('policy_rules')
    op.drop_table('policy_versions')
    op.drop_table('governance_policies')

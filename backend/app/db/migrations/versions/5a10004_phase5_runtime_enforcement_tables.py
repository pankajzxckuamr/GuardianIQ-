"""phase5_runtime_enforcement_tables

Revision ID: 5a10004_phase5_runtime_enforcement
Revises: 5a10003_phase5_alter_policy_bindings
Create Date: 2026-08-17 13:45:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '5a10004_p5_rt'
down_revision: Union[str, Sequence[str], None] = '5a10003_p5_bind'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. policy_evaluations
    op.create_table(
        'policy_evaluations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=True),
        sa.Column('version_no', sa.Integer(), server_default='1', nullable=True),
        sa.Column('is_deleted', sa.Boolean(), server_default='FALSE', nullable=True),
        sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=True),
        sa.Column('request_id', sa.String(length=150), nullable=False),
        sa.Column('correlation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('causation_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('policy_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('governance_policies.id'), nullable=False),
        sa.Column('policy_version_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('policy_versions.id'), nullable=True),
        sa.Column('target_type', sa.String(length=100), nullable=False),
        sa.Column('target_id', sa.String(length=255), nullable=False),
        sa.Column('trigger_event', sa.String(length=100), nullable=False),
        sa.Column('decision', sa.String(length=50), nullable=False),
        sa.Column('reasons_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('evaluation_latency_ms', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('context_snapshot_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.create_index('ix_policy_evaluations_request_id', 'policy_evaluations', ['request_id'], unique=False)
    op.create_index('ix_policy_evaluations_correlation_id', 'policy_evaluations', ['correlation_id'], unique=False)
    op.create_index('idx_policy_eval_lookup', 'policy_evaluations', ['policy_id', 'decision', 'created_at'], unique=False)

    # 2. policy_rule_evaluations
    op.create_table(
        'policy_rule_evaluations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=True),
        sa.Column('version_no', sa.Integer(), server_default='1', nullable=True),
        sa.Column('is_deleted', sa.Boolean(), server_default='FALSE', nullable=True),
        sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=True),
        sa.Column('evaluation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('policy_evaluations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('rule_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('policy_rules.id', ondelete='CASCADE'), nullable=False),
        sa.Column('matched', sa.Boolean(), nullable=False),
        sa.Column('decision', sa.String(length=50), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('execution_order', sa.Integer(), server_default='10', nullable=False),
        sa.Column('latency_ms', sa.Numeric(precision=10, scale=2), nullable=True),
    )
    op.create_index('idx_policy_rule_eval_lookup', 'policy_rule_evaluations', ['evaluation_id', 'rule_id'], unique=False)

    # 3. enforcement_decisions
    op.create_table(
        'enforcement_decisions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=True),
        sa.Column('version_no', sa.Integer(), server_default='1', nullable=True),
        sa.Column('is_deleted', sa.Boolean(), server_default='FALSE', nullable=True),
        sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=True),
        sa.Column('request_id', sa.String(length=150), nullable=False),
        sa.Column('correlation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('agents.id'), nullable=True),
        sa.Column('workflow_run_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('workflow_runs.id'), nullable=True),
        sa.Column('tool_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tools.id'), nullable=True),
        sa.Column('decision', sa.String(length=50), nullable=False),
        sa.Column('execution_permitted', sa.Boolean(), server_default='TRUE', nullable=False),
        sa.Column('modified_payload_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('violations_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('approval_required', sa.Boolean(), server_default='FALSE', nullable=False),
        sa.Column('enforced_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_enforcement_decisions_request_id', 'enforcement_decisions', ['request_id'], unique=False)
    op.create_index('ix_enforcement_decisions_correlation_id', 'enforcement_decisions', ['correlation_id'], unique=False)
    op.create_index('idx_enforcement_decisions_agent', 'enforcement_decisions', ['agent_id', 'enforced_at'], unique=False)

    # 4. runtime_authorizations
    op.create_table(
        'runtime_authorizations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=True),
        sa.Column('version_no', sa.Integer(), server_default='1', nullable=True),
        sa.Column('is_deleted', sa.Boolean(), server_default='FALSE', nullable=True),
        sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=True),
        sa.Column('request_id', sa.String(length=150), nullable=False),
        sa.Column('correlation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('agents.id'), nullable=False),
        sa.Column('operation', sa.String(length=100), nullable=False),
        sa.Column('authorized', sa.Boolean(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('expires_at', sa.TIMESTAMP(timezone=True), nullable=True),
    )
    op.create_index('ix_runtime_authorizations_request_id', 'runtime_authorizations', ['request_id'], unique=False)
    op.create_index('ix_runtime_authorizations_correlation_id', 'runtime_authorizations', ['correlation_id'], unique=False)

    # 5. runtime_enforcement_log
    op.create_table(
        'runtime_enforcement_log',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=True),
        sa.Column('version_no', sa.Integer(), server_default='1', nullable=True),
        sa.Column('is_deleted', sa.Boolean(), server_default='FALSE', nullable=True),
        sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=True),
        sa.Column('request_id', sa.String(length=150), nullable=False),
        sa.Column('correlation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('causation_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('agents.id'), nullable=True),
        sa.Column('tool_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tools.id'), nullable=True),
        sa.Column('decision', sa.String(length=50), nullable=False),
        sa.Column('action_taken', sa.String(length=100), nullable=False),
        sa.Column('latency_ms', sa.Numeric(precision=10, scale=2), nullable=True),
    )
    op.create_index('ix_runtime_enforcement_log_request_id', 'runtime_enforcement_log', ['request_id'], unique=False)
    op.create_index('ix_runtime_enforcement_log_correlation_id', 'runtime_enforcement_log', ['correlation_id'], unique=False)

    # 6. policy_approvals
    op.create_table(
        'policy_approvals',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=True),
        sa.Column('version_no', sa.Integer(), server_default='1', nullable=True),
        sa.Column('is_deleted', sa.Boolean(), server_default='FALSE', nullable=True),
        sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=True),
        sa.Column('request_id', sa.String(length=150), nullable=False),
        sa.Column('correlation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('policy_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('governance_policies.id'), nullable=False),
        sa.Column('evaluation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('policy_evaluations.id'), nullable=True),
        sa.Column('approval_tier', sa.Integer(), server_default='1', nullable=False),
        sa.Column('required_role', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=50), server_default='PENDING', nullable=False),
        sa.Column('approver_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('decision_reason', sa.Text(), nullable=True),
        sa.Column('timeout_at', sa.TIMESTAMP(timezone=True), nullable=False),
    )
    op.create_index('ix_policy_approvals_request_id', 'policy_approvals', ['request_id'], unique=False)
    op.create_index('ix_policy_approvals_correlation_id', 'policy_approvals', ['correlation_id'], unique=False)
    op.create_index('idx_policy_approvals_status_tier', 'policy_approvals', ['status', 'approval_tier'], unique=False)

    # 7. Apply existing prevent_update_delete() trigger to governance_events
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        op.execute("""
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM pg_proc WHERE proname = 'prevent_update_delete'
                ) THEN
                    DROP TRIGGER IF EXISTS trg_immutability_governance_events ON governance_events;
                    CREATE TRIGGER trg_immutability_governance_events
                    BEFORE UPDATE OR DELETE ON governance_events
                    FOR EACH ROW EXECUTE FUNCTION prevent_update_delete();
                END IF;
            END $$;
        """)


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        op.execute("DROP TRIGGER IF EXISTS trg_immutability_governance_events ON governance_events;")

    op.drop_table('policy_approvals')
    op.drop_table('runtime_enforcement_log')
    op.drop_table('runtime_authorizations')
    op.drop_table('enforcement_decisions')
    op.drop_table('policy_rule_evaluations')
    op.drop_table('policy_evaluations')

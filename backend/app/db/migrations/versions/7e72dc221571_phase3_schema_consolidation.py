"""phase3_schema_consolidation

Revision ID: 7e72dc221571
Revises: c8946d1c5403
Create Date: 2026-07-09 12:58:45.669519

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


def add_col_if_not_exists(table_name, column):
    from sqlalchemy import inspect
    from alembic import op
    conn = op.get_bind()
    inspector = inspect(conn)
    columns = [c['name'] for c in inspector.get_columns(table_name)]
    if column.name not in columns:
        op.add_column(table_name, column)


# revision identifiers, used by Alembic.
revision: str = '7e72dc221571'
down_revision: Union[str, Sequence[str], None] = 'c8946d1c5403'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.execute('''
DO $$
DECLARE r RECORD;
BEGIN
    FOR r IN (
        SELECT c.conname, c.conrelid::regclass::text as tablename
        FROM pg_constraint c
        JOIN pg_class t ON t.oid = c.conrelid
        JOIN pg_attribute a ON a.attnum = ANY(c.conkey) AND a.attrelid = c.conrelid
        JOIN pg_class t2 ON t2.oid = c.confrelid
        JOIN pg_attribute a2 ON a2.attnum = ANY(c.confkey) AND a2.attrelid = c.confrelid
        WHERE c.contype = 'f'
          AND (
             (t.relname = 'agents' AND a.attname = 'ai_model_id')
             OR (t.relname = 'agents' AND a.attname = 'id')
             OR (t.relname = 'ai_models' AND a.attname = 'data_source_id')
             OR (t.relname = 'ai_models' AND a.attname = 'id')
             OR (t.relname = 'approvals' AND a.attname = 'reviewer_id')
             OR (t.relname = 'data_sources' AND a.attname = 'id')
             OR (t.relname = 'departments' AND a.attname = 'parent_id')
             OR (t.relname = 'departments' AND a.attname = 'owner_user_id')
             OR (t.relname = 'departments' AND a.attname = 'id')
             OR (t.relname = 'policies' AND a.attname = 'id')
             OR (t.relname = 'policies' AND a.attname = 'created_by')
             OR (t.relname = 'recommendations' AND a.attname = 'agent_id')
             OR (t.relname = 'recommendations' AND a.attname = 'policy_id')
             OR (t.relname = 'role_permissions' AND a.attname = 'role_id')
             OR (t.relname = 'roles' AND a.attname = 'id')
             OR (t.relname = 'user_roles' AND a.attname = 'user_id')
             OR (t.relname = 'user_roles' AND a.attname = 'role_id')
             OR (t.relname = 'users' AND a.attname = 'id')
             OR (t2.relname = 'agents' AND a2.attname = 'ai_model_id')
             OR (t2.relname = 'agents' AND a2.attname = 'id')
             OR (t2.relname = 'ai_models' AND a2.attname = 'data_source_id')
             OR (t2.relname = 'ai_models' AND a2.attname = 'id')
             OR (t2.relname = 'approvals' AND a2.attname = 'reviewer_id')
             OR (t2.relname = 'data_sources' AND a2.attname = 'id')
             OR (t2.relname = 'departments' AND a2.attname = 'parent_id')
             OR (t2.relname = 'departments' AND a2.attname = 'owner_user_id')
             OR (t2.relname = 'departments' AND a2.attname = 'id')
             OR (t2.relname = 'policies' AND a2.attname = 'id')
             OR (t2.relname = 'policies' AND a2.attname = 'created_by')
             OR (t2.relname = 'recommendations' AND a2.attname = 'agent_id')
             OR (t2.relname = 'recommendations' AND a2.attname = 'policy_id')
             OR (t2.relname = 'role_permissions' AND a2.attname = 'role_id')
             OR (t2.relname = 'roles' AND a2.attname = 'id')
             OR (t2.relname = 'user_roles' AND a2.attname = 'user_id')
             OR (t2.relname = 'user_roles' AND a2.attname = 'role_id')
             OR (t2.relname = 'users' AND a2.attname = 'id')
          )
    )
    LOOP
        EXECUTE 'ALTER TABLE ' || quote_ident(r.tablename) || ' DROP CONSTRAINT IF EXISTS ' || quote_ident(r.conname);
    END LOOP;
END $$;
    ''')
    op.execute('ALTER TABLE departments DROP CONSTRAINT IF EXISTS fk_departments_parent_id')
    op.execute('ALTER TABLE approvals DROP CONSTRAINT IF EXISTS approvals_reviewer_id_fkey')
    op.drop_constraint(op.f('ai_models_owner_department_id_fkey'), 'ai_models', type_='foreignkey')
    op.drop_constraint(op.f('approval_group_members_user_id_fkey'), 'approval_group_members', type_='foreignkey')
    op.drop_constraint(op.f('approval_groups_tenant_id_fkey'), 'approval_groups', type_='foreignkey')
    op.drop_constraint(op.f('approval_groups_updated_by_fkey'), 'approval_groups', type_='foreignkey')
    op.drop_constraint(op.f('approval_groups_created_by_fkey'), 'approval_groups', type_='foreignkey')
    op.drop_constraint(op.f('data_sources_owner_department_id_fkey'), 'data_sources', type_='foreignkey')
    op.drop_constraint(op.f('orchestration_workflow_executions_workflow_id_fkey'), 'orchestration_workflow_executions', type_='foreignkey')
    op.drop_constraint(op.f('orchestration_workflow_schedules_workflow_id_fkey'), 'orchestration_workflow_schedules', type_='foreignkey')
    op.drop_constraint(op.f('workflow_authorization_decisions_updated_by_fkey'), 'workflow_authorization_decisions', type_='foreignkey')
    op.drop_constraint(op.f('workflow_authorization_decisions_created_by_fkey'), 'workflow_authorization_decisions', type_='foreignkey')
    op.drop_constraint(op.f('workflow_authorization_decisions_subject_user_id_fkey'), 'workflow_authorization_decisions', type_='foreignkey')
    op.drop_constraint(op.f('workflow_authorization_decisions_tenant_id_fkey'), 'workflow_authorization_decisions', type_='foreignkey')
    op.drop_constraint(op.f('workflow_authorization_decisions_subject_agent_id_fkey'), 'workflow_authorization_decisions', type_='foreignkey')
    op.drop_constraint(op.f('workflow_delegations_delegatee_user_id_fkey'), 'workflow_delegations', type_='foreignkey')
    op.drop_constraint(op.f('workflow_delegations_tenant_id_fkey'), 'workflow_delegations', type_='foreignkey')
    op.drop_constraint(op.f('workflow_delegations_created_by_fkey'), 'workflow_delegations', type_='foreignkey')
    op.drop_constraint(op.f('workflow_delegations_delegator_user_id_fkey'), 'workflow_delegations', type_='foreignkey')
    op.drop_constraint(op.f('workflow_delegations_updated_by_fkey'), 'workflow_delegations', type_='foreignkey')
    op.drop_constraint(op.f('workflow_notifications_updated_by_fkey'), 'workflow_notifications', type_='foreignkey')
    op.drop_constraint(op.f('workflow_notifications_recipient_user_id_fkey'), 'workflow_notifications', type_='foreignkey')
    op.drop_constraint(op.f('workflow_notifications_tenant_id_fkey'), 'workflow_notifications', type_='foreignkey')
    op.drop_constraint(op.f('workflow_notifications_created_by_fkey'), 'workflow_notifications', type_='foreignkey')
    op.drop_constraint(op.f('workflow_run_failures_updated_by_fkey'), 'workflow_run_failures', type_='foreignkey')
    op.drop_constraint(op.f('workflow_run_failures_created_by_fkey'), 'workflow_run_failures', type_='foreignkey')
    op.drop_constraint(op.f('workflow_run_failures_tenant_id_fkey'), 'workflow_run_failures', type_='foreignkey')
    op.drop_constraint(op.f('workflow_run_outputs_updated_by_fkey'), 'workflow_run_outputs', type_='foreignkey')
    op.drop_constraint(op.f('workflow_run_outputs_created_by_fkey'), 'workflow_run_outputs', type_='foreignkey')
    op.drop_constraint(op.f('workflow_run_outputs_tenant_id_fkey'), 'workflow_run_outputs', type_='foreignkey')
    op.drop_constraint(op.f('workflow_run_steps_created_by_fkey'), 'workflow_run_steps', type_='foreignkey')
    op.drop_constraint(op.f('workflow_run_steps_tenant_id_fkey'), 'workflow_run_steps', type_='foreignkey')
    op.drop_constraint(op.f('workflow_run_steps_updated_by_fkey'), 'workflow_run_steps', type_='foreignkey')
    op.drop_constraint(op.f('workflow_runs_workflow_id_fkey'), 'workflow_runs', type_='foreignkey')
    op.drop_constraint(op.f('workflow_runs_created_by_fkey'), 'workflow_runs', type_='foreignkey')
    op.drop_constraint(op.f('workflow_runs_triggered_by_user_id_fkey'), 'workflow_runs', type_='foreignkey')
    op.drop_constraint(op.f('workflow_runs_tenant_id_fkey'), 'workflow_runs', type_='foreignkey')
    op.drop_constraint(op.f('workflow_runs_updated_by_fkey'), 'workflow_runs', type_='foreignkey')
    op.drop_constraint(op.f('workflow_schedule_agent_assignments_agent_id_fkey'), 'workflow_schedule_agent_assignments', type_='foreignkey')
    op.drop_constraint(op.f('workflow_schedule_agent_assignments_model_id_fkey'), 'workflow_schedule_agent_assignments', type_='foreignkey')
    op.drop_constraint(op.f('workflow_schedule_agent_assignments_tenant_id_fkey'), 'workflow_schedule_agent_assignments', type_='foreignkey')
    op.drop_constraint(op.f('workflow_schedule_agent_assignments_updated_by_fkey'), 'workflow_schedule_agent_assignments', type_='foreignkey')
    op.drop_constraint(op.f('workflow_schedule_agent_assignments_created_by_fkey'), 'workflow_schedule_agent_assignments', type_='foreignkey')
    op.drop_constraint(op.f('workflow_schedule_approvals_submitted_by_fkey'), 'workflow_schedule_approvals', type_='foreignkey')
    op.drop_constraint(op.f('workflow_schedule_approvals_tenant_id_fkey'), 'workflow_schedule_approvals', type_='foreignkey')
    op.drop_constraint(op.f('workflow_schedule_approvals_created_by_fkey'), 'workflow_schedule_approvals', type_='foreignkey')
    op.drop_constraint(op.f('workflow_schedule_approvals_approver_user_id_fkey'), 'workflow_schedule_approvals', type_='foreignkey')
    op.drop_constraint(op.f('workflow_schedule_approvals_updated_by_fkey'), 'workflow_schedule_approvals', type_='foreignkey')
    op.drop_constraint(op.f('workflow_schedule_history_created_by_fkey'), 'workflow_schedule_history', type_='foreignkey')
    op.drop_constraint(op.f('workflow_schedule_history_tenant_id_fkey'), 'workflow_schedule_history', type_='foreignkey')
    op.drop_constraint(op.f('workflow_schedule_history_updated_by_fkey'), 'workflow_schedule_history', type_='foreignkey')
    op.drop_constraint(op.f('workflow_schedule_history_changed_by_fkey'), 'workflow_schedule_history', type_='foreignkey')
    op.drop_constraint(op.f('workflow_schedules_created_by_fkey'), 'workflow_schedules', type_='foreignkey')
    op.drop_constraint(op.f('workflow_schedules_updated_by_fkey'), 'workflow_schedules', type_='foreignkey')
    op.drop_constraint(op.f('workflow_schedules_owner_department_id_fkey'), 'workflow_schedules', type_='foreignkey')
    op.drop_constraint(op.f('workflow_schedules_owner_user_id_fkey'), 'workflow_schedules', type_='foreignkey')
    op.drop_constraint(op.f('workflow_schedules_tenant_id_fkey'), 'workflow_schedules', type_='foreignkey')
    op.drop_constraint(op.f('workflow_schedules_workflow_id_fkey'), 'workflow_schedules', type_='foreignkey')
    op.execute('ALTER TABLE user_roles DROP CONSTRAINT IF EXISTS user_roles_user_id_fkey')
    op.execute('ALTER TABLE ai_models DROP CONSTRAINT IF EXISTS ai_models_data_source_id_fkey')
    op.execute('ALTER TABLE policies DROP CONSTRAINT IF EXISTS policies_created_by_fkey')
    op.execute('ALTER TABLE recommendations DROP CONSTRAINT IF EXISTS recommendations_agent_id_fkey')
    op.execute('ALTER TABLE user_roles DROP CONSTRAINT IF EXISTS user_roles_role_id_fkey')
    op.execute('ALTER TABLE role_permissions DROP CONSTRAINT IF EXISTS role_permissions_role_id_fkey')
    op.execute('ALTER TABLE departments DROP CONSTRAINT IF EXISTS departments_owner_user_id_fkey')
    op.execute('ALTER TABLE recommendations DROP CONSTRAINT IF EXISTS recommendations_policy_id_fkey')
    op.execute('ALTER TABLE agents DROP CONSTRAINT IF EXISTS agents_ai_model_id_fkey')
    # ### commands auto generated by Alembic - please adjust! ###
    op.execute('ALTER TABLE agents ALTER COLUMN id DROP DEFAULT')
    op.execute('ALTER TABLE ai_models ALTER COLUMN id DROP DEFAULT')
    op.execute('ALTER TABLE data_sources ALTER COLUMN id DROP DEFAULT')
    op.execute('ALTER TABLE departments ALTER COLUMN id DROP DEFAULT')
    op.execute('ALTER TABLE policies ALTER COLUMN id DROP DEFAULT')
    op.execute('ALTER TABLE roles ALTER COLUMN id DROP DEFAULT')
    op.execute('ALTER TABLE users ALTER COLUMN id DROP DEFAULT')
    add_col_if_not_exists('agents', sa.Column('agent_code', sa.String(length=80), nullable=False))
    add_col_if_not_exists('agents', sa.Column('agent_type', sa.String(length=80), nullable=False))
    add_col_if_not_exists('agents', sa.Column('owner_user_id', sa.UUID(), nullable=True))
    add_col_if_not_exists('agents', sa.Column('department_id', sa.UUID(), nullable=True))
    add_col_if_not_exists('agents', sa.Column('risk_level', sa.String(length=50), nullable=False))
    add_col_if_not_exists('agents', sa.Column('confidence_threshold', sa.Numeric(precision=5, scale=2), nullable=True))
    add_col_if_not_exists('agents', sa.Column('status', sa.String(length=30), nullable=True))
    add_col_if_not_exists('agents', sa.Column('capabilities_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    add_col_if_not_exists('agents', sa.Column('version_no', sa.Integer(), server_default='1', nullable=True))
    add_col_if_not_exists('agents', sa.Column('is_deleted', sa.Boolean(), server_default='FALSE', nullable=True))
    add_col_if_not_exists('agents', sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=True))
    add_col_if_not_exists('agents', sa.Column('tenant_id', sa.UUID(), nullable=False))
    add_col_if_not_exists('agents', sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True))
    add_col_if_not_exists('agents', sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True))
    add_col_if_not_exists('agents', sa.Column('created_by', sa.UUID(), nullable=True))
    add_col_if_not_exists('agents', sa.Column('updated_by', sa.UUID(), nullable=True))
    op.alter_column('agents', 'description',
               existing_type=sa.VARCHAR(),
               type_=sa.Text(),
               existing_nullable=True)
    op.alter_column('agents', 'execution_mode',
               existing_type=postgresql.ENUM('READ_ONLY', 'RECOMMEND_ONLY', 'APPROVAL_REQUIRED', 'LIMITED_EXECUTION', 'FULLY_BLOCKED', name='executionmode'),
               type_=sa.String(length=80),
               existing_nullable=False)
    op.alter_column('agents', 'ai_model_id',
               existing_type=sa.INTEGER(),
               type_=sa.UUID(),
               postgresql_using='gen_random_uuid()',
               existing_nullable=True)
    op.alter_column('agents', 'id',
               existing_type=sa.INTEGER(),
               type_=sa.UUID(),
               server_default=sa.text('gen_random_uuid()'),
               postgresql_using='gen_random_uuid()',
               existing_nullable=False)
    op.drop_index(op.f('ix_agents_id'), table_name='agents')
    op.create_unique_constraint(None, 'agents', ['agent_code'])
    add_col_if_not_exists('ai_models', sa.Column('model_code', sa.String(length=80), nullable=False))
    add_col_if_not_exists('ai_models', sa.Column('provider_id', sa.UUID(), nullable=True))
    add_col_if_not_exists('ai_models', sa.Column('purpose', sa.Text(), nullable=False))
    add_col_if_not_exists('ai_models', sa.Column('owner_user_id', sa.UUID(), nullable=True))
    add_col_if_not_exists('ai_models', sa.Column('department_id', sa.UUID(), nullable=True))
    add_col_if_not_exists('ai_models', sa.Column('deployment_environment', sa.String(length=50), nullable=True))
    add_col_if_not_exists('ai_models', sa.Column('version_no', sa.Integer(), server_default='1', nullable=True))
    add_col_if_not_exists('ai_models', sa.Column('is_deleted', sa.Boolean(), server_default='FALSE', nullable=True))
    add_col_if_not_exists('ai_models', sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=True))
    add_col_if_not_exists('ai_models', sa.Column('tenant_id', sa.UUID(), nullable=False))
    add_col_if_not_exists('ai_models', sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True))
    add_col_if_not_exists('ai_models', sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True))
    add_col_if_not_exists('ai_models', sa.Column('created_by', sa.UUID(), nullable=True))
    add_col_if_not_exists('ai_models', sa.Column('updated_by', sa.UUID(), nullable=True))
    op.alter_column('ai_models', 'version',
               existing_type=sa.VARCHAR(),
               nullable=True)
    op.alter_column('ai_models', 'data_source_id',
               existing_type=sa.INTEGER(),
               type_=sa.UUID(),
               postgresql_using='gen_random_uuid()',
               existing_nullable=True)
    op.alter_column('ai_models', 'id',
               existing_type=sa.INTEGER(),
               type_=sa.UUID(),
               server_default=sa.text('gen_random_uuid()'),
               postgresql_using='gen_random_uuid()',
               existing_nullable=False)
    op.drop_index(op.f('ix_ai_models_id'), table_name='ai_models')
    op.create_unique_constraint(None, 'ai_models', ['model_code'])
    op.drop_column('ai_models', 'owner_department_id')
    op.alter_column('approval_groups', 'metadata_json',
               existing_type=postgresql.JSONB(astext_type=sa.Text()),
               type_=postgresql.JSONB(astext_type=sa.Text()),
               existing_nullable=True,
               existing_server_default=sa.text("'{}'::jsonb"))
    op.alter_column('approvals', 'reviewer_id',
               existing_type=sa.INTEGER(),
               type_=sa.UUID(),
               postgresql_using='gen_random_uuid()',
               existing_nullable=True)
    add_col_if_not_exists('data_sources', sa.Column('source_code', sa.String(length=80), nullable=False))
    add_col_if_not_exists('data_sources', sa.Column('owner_user_id', sa.UUID(), nullable=True))
    add_col_if_not_exists('data_sources', sa.Column('department_id', sa.UUID(), nullable=True))
    add_col_if_not_exists('data_sources', sa.Column('classification', sa.String(length=80), nullable=False))
    add_col_if_not_exists('data_sources', sa.Column('sensitivity_level', sa.String(length=50), nullable=False))
    add_col_if_not_exists('data_sources', sa.Column('region', sa.String(length=80), nullable=True))
    add_col_if_not_exists('data_sources', sa.Column('contains_pii', sa.Boolean(), nullable=True))
    add_col_if_not_exists('data_sources', sa.Column('retention_policy', sa.String(length=200), nullable=True))
    add_col_if_not_exists('data_sources', sa.Column('connection_reference', sa.String(length=500), nullable=True))
    add_col_if_not_exists('data_sources', sa.Column('version_no', sa.Integer(), server_default='1', nullable=True))
    add_col_if_not_exists('data_sources', sa.Column('is_deleted', sa.Boolean(), server_default='FALSE', nullable=True))
    add_col_if_not_exists('data_sources', sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=True))
    add_col_if_not_exists('data_sources', sa.Column('tenant_id', sa.UUID(), nullable=False))
    add_col_if_not_exists('data_sources', sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True))
    add_col_if_not_exists('data_sources', sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True))
    add_col_if_not_exists('data_sources', sa.Column('created_by', sa.UUID(), nullable=True))
    add_col_if_not_exists('data_sources', sa.Column('updated_by', sa.UUID(), nullable=True))
    op.alter_column('data_sources', 'id',
               existing_type=sa.INTEGER(),
               type_=sa.UUID(),
               server_default=sa.text('gen_random_uuid()'),
               postgresql_using='gen_random_uuid()',
               existing_nullable=False)
    op.drop_index(op.f('ix_data_sources_id'), table_name='data_sources')
    op.create_unique_constraint(None, 'data_sources', ['source_code'])
    op.drop_column('data_sources', 'owner_department_id')
    op.drop_column('data_sources', 'description')
    add_col_if_not_exists('departments', sa.Column('version_no', sa.Integer(), server_default='1', nullable=True))
    add_col_if_not_exists('departments', sa.Column('is_deleted', sa.Boolean(), server_default='FALSE', nullable=True))
    add_col_if_not_exists('departments', sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=True))
    add_col_if_not_exists('departments', sa.Column('tenant_id', sa.UUID(), nullable=False))
    add_col_if_not_exists('departments', sa.Column('created_by', sa.UUID(), nullable=True))
    add_col_if_not_exists('departments', sa.Column('updated_by', sa.UUID(), nullable=True))
    op.alter_column('departments', 'parent_id',
               existing_type=sa.INTEGER(),
               type_=sa.UUID(),
               postgresql_using='gen_random_uuid()',
               existing_nullable=True)
    op.alter_column('departments', 'owner_user_id',
               existing_type=sa.INTEGER(),
               type_=sa.UUID(),
               postgresql_using='gen_random_uuid()',
               existing_nullable=True)
    op.alter_column('departments', 'id',
               existing_type=sa.INTEGER(),
               type_=sa.UUID(),
               server_default=sa.text('gen_random_uuid()'),
               postgresql_using='gen_random_uuid()',
               existing_nullable=False)
    op.alter_column('departments', 'created_at',
               existing_type=postgresql.TIMESTAMP(timezone=True),
               nullable=True,
               existing_server_default=sa.text('now()'))
    op.alter_column('departments', 'updated_at',
               existing_type=postgresql.TIMESTAMP(timezone=True),
               nullable=True,
               existing_server_default=sa.text('now()'))
    op.drop_index(op.f('ix_departments_id'), table_name='departments')
    add_col_if_not_exists('policies', sa.Column('version_no', sa.Integer(), server_default='1', nullable=True))
    add_col_if_not_exists('policies', sa.Column('is_deleted', sa.Boolean(), server_default='FALSE', nullable=True))
    add_col_if_not_exists('policies', sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=True))
    add_col_if_not_exists('policies', sa.Column('tenant_id', sa.UUID(), nullable=False))
    add_col_if_not_exists('policies', sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True))
    add_col_if_not_exists('policies', sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True))
    add_col_if_not_exists('policies', sa.Column('updated_by', sa.UUID(), nullable=True))
    op.alter_column('policies', 'id',
               existing_type=sa.INTEGER(),
               type_=sa.UUID(),
               server_default=sa.text('gen_random_uuid()'),
               postgresql_using='gen_random_uuid()',
               existing_nullable=False)
    op.alter_column('policies', 'created_by',
               existing_type=sa.INTEGER(),
               type_=sa.UUID(),
               postgresql_using='gen_random_uuid()',
               existing_nullable=True)
    op.drop_index(op.f('ix_policies_id'), table_name='policies')
    op.alter_column('recommendations', 'agent_id',
               existing_type=sa.INTEGER(),
               type_=sa.UUID(),
               postgresql_using='gen_random_uuid()',
               existing_nullable=True)
    op.alter_column('recommendations', 'policy_id',
               existing_type=sa.INTEGER(),
               type_=sa.UUID(),
               postgresql_using='gen_random_uuid()',
               existing_nullable=True)
    op.alter_column('role_permissions', 'role_id',
               existing_type=sa.INTEGER(),
               type_=sa.UUID(),
               postgresql_using='gen_random_uuid()',
               existing_nullable=True)
    op.alter_column('roles', 'id',
               existing_type=sa.INTEGER(),
               type_=sa.UUID(),
               server_default=sa.text('gen_random_uuid()'),
               postgresql_using='gen_random_uuid()',
               existing_nullable=False)
    op.drop_index(op.f('ix_roles_id'), table_name='roles')
    op.alter_column('user_roles', 'user_id',
               existing_type=sa.INTEGER(),
               type_=sa.UUID(),
               postgresql_using='gen_random_uuid()',
               existing_nullable=True)
    op.alter_column('user_roles', 'role_id',
               existing_type=sa.INTEGER(),
               type_=sa.UUID(),
               postgresql_using='gen_random_uuid()',
               existing_nullable=True)
    add_col_if_not_exists('users', sa.Column('department_id', sa.UUID(), nullable=True))
    add_col_if_not_exists('users', sa.Column('approval_limit_level', sa.String(length=50), nullable=True))
    op.alter_column('users', 'id',
               existing_type=sa.INTEGER(),
               type_=sa.UUID(),
               server_default=sa.text('gen_random_uuid()'),
               postgresql_using='gen_random_uuid()',
               existing_nullable=False)
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.alter_column('workflow_authorization_decisions', 'metadata_json',
               existing_type=postgresql.JSONB(astext_type=sa.Text()),
               type_=postgresql.JSONB(astext_type=sa.Text()),
               existing_nullable=True,
               existing_server_default=sa.text("'{}'::jsonb"))
    op.alter_column('workflow_delegations', 'metadata_json',
               existing_type=postgresql.JSONB(astext_type=sa.Text()),
               type_=postgresql.JSONB(astext_type=sa.Text()),
               existing_nullable=True,
               existing_server_default=sa.text("'{}'::jsonb"))
    # add_col_if_not_exists('workflow_notifications', sa.Column('related_entity_type', sa.String(length=100), nullable=True))
    # add_col_if_not_exists('workflow_notifications', sa.Column('related_entity_id', sa.UUID(), nullable=True))
    op.alter_column('workflow_notifications', 'metadata_json',
               existing_type=postgresql.JSONB(astext_type=sa.Text()),
               type_=postgresql.JSONB(astext_type=sa.Text()),
               existing_nullable=True,
               existing_server_default=sa.text("'{}'::jsonb"))
    op.drop_index(op.f('ix_workflow_notifications_recipient_status'), table_name='workflow_notifications')
    op.drop_column('workflow_notifications', 'entity_id')
    op.drop_column('workflow_notifications', 'entity_type')
    add_col_if_not_exists('workflow_run_failures', sa.Column('next_retry_at', sa.TIMESTAMP(timezone=True), nullable=True))
    op.alter_column('workflow_run_failures', 'metadata_json',
               existing_type=postgresql.JSONB(astext_type=sa.Text()),
               type_=postgresql.JSONB(astext_type=sa.Text()),
               existing_nullable=True,
               existing_server_default=sa.text("'{}'::jsonb"))
    add_col_if_not_exists('workflow_run_outputs', sa.Column('raw_output', sa.Text(), nullable=True))
    op.alter_column('workflow_run_outputs', 'metadata_json',
               existing_type=postgresql.JSONB(astext_type=sa.Text()),
               type_=postgresql.JSONB(astext_type=sa.Text()),
               existing_nullable=True,
               existing_server_default=sa.text("'{}'::jsonb"))
    op.drop_index(op.f('ix_workflow_run_outputs_findings_json'), table_name='workflow_run_outputs', postgresql_using='gin')
    add_col_if_not_exists('workflow_run_steps', sa.Column('error_detail', sa.Text(), nullable=True))
    op.alter_column('workflow_run_steps', 'metadata_json',
               existing_type=postgresql.JSONB(astext_type=sa.Text()),
               type_=postgresql.JSONB(astext_type=sa.Text()),
               existing_nullable=True,
               existing_server_default=sa.text("'{}'::jsonb"))
    op.drop_index(op.f('ix_workflow_run_steps_run_id'), table_name='workflow_run_steps')
    op.alter_column('workflow_runs', 'metadata_json',
               existing_type=postgresql.JSONB(astext_type=sa.Text()),
               type_=postgresql.JSONB(astext_type=sa.Text()),
               existing_nullable=True,
               existing_server_default=sa.text("'{}'::jsonb"))
    op.drop_index(op.f('ix_workflow_runs_created_at_desc'), table_name='workflow_runs')
    op.drop_index(op.f('ix_workflow_runs_result_json'), table_name='workflow_runs', postgresql_using='gin')
    op.drop_index(op.f('ix_workflow_runs_run_status'), table_name='workflow_runs')
    op.drop_index(op.f('ix_workflow_runs_schedule_id'), table_name='workflow_runs')
    op.drop_constraint(op.f('uq_workflow_runs_tenant_run_code'), 'workflow_runs', type_='unique')
    op.alter_column('workflow_schedule_agent_assignments', 'metadata_json',
               existing_type=postgresql.JSONB(astext_type=sa.Text()),
               type_=postgresql.JSONB(astext_type=sa.Text()),
               existing_nullable=True,
               existing_server_default=sa.text("'{}'::jsonb"))
    op.drop_constraint(op.f('uq_wf_sch_agent_assg_tenant_sch_agent_role'), 'workflow_schedule_agent_assignments', type_='unique')
    op.alter_column('workflow_schedule_approvals', 'metadata_json',
               existing_type=postgresql.JSONB(astext_type=sa.Text()),
               type_=postgresql.JSONB(astext_type=sa.Text()),
               existing_nullable=True,
               existing_server_default=sa.text("'{}'::jsonb"))
    op.drop_index(op.f('ix_workflow_schedule_approvals_sched_status'), table_name='workflow_schedule_approvals')
    op.alter_column('workflow_schedule_history', 'metadata_json',
               existing_type=postgresql.JSONB(astext_type=sa.Text()),
               type_=postgresql.JSONB(astext_type=sa.Text()),
               existing_nullable=True,
               existing_server_default=sa.text("'{}'::jsonb"))
    op.drop_index(op.f('ix_workflow_schedule_history_schedule_id'), table_name='workflow_schedule_history')
    op.alter_column('workflow_schedules', 'metadata_json',
               existing_type=postgresql.JSONB(astext_type=sa.Text()),
               type_=postgresql.JSONB(astext_type=sa.Text()),
               existing_nullable=True,
               existing_server_default=sa.text("'{}'::jsonb"))
    op.drop_index(op.f('ix_workflow_schedules_metadata_json'), table_name='workflow_schedules', postgresql_using='gin')
    op.drop_index(op.f('ix_workflow_schedules_next_run_at'), table_name='workflow_schedules')
    op.drop_index(op.f('ix_workflow_schedules_owner_user_id'), table_name='workflow_schedules')
    op.drop_index(op.f('ix_workflow_schedules_schedule_status'), table_name='workflow_schedules')
    op.drop_index(op.f('ix_workflow_schedules_tenant_id'), table_name='workflow_schedules')
    op.drop_index(op.f('ix_workflow_schedules_workflow_id'), table_name='workflow_schedules')
    op.drop_constraint(op.f('uq_workflow_schedules_tenant_code'), 'workflow_schedules', type_='unique')
    op.create_unique_constraint('uix_tenant_schedule_code', 'workflow_schedules', ['tenant_id', 'schedule_code'])
    op.create_unique_constraint('uix_tenant_schedule_name', 'workflow_schedules', ['tenant_id', 'schedule_name'])
    op.create_table('ai_model_providers',
    sa.Column('provider_type', sa.String(length=80), nullable=False),
    sa.Column('provider_name', sa.String(length=200), nullable=False),
    sa.Column('provider_category', sa.String(length=80), nullable=True),
    sa.Column('ownership_type', sa.String(length=80), nullable=True),
    sa.Column('hosting_type', sa.String(length=80), nullable=True),
    sa.Column('data_residency', sa.String(length=80), nullable=True),
    sa.Column('risk_classification', sa.String(length=50), nullable=True),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('version_no', sa.Integer(), server_default='1', nullable=True),
    sa.Column('is_deleted', sa.Boolean(), server_default='FALSE', nullable=True),
    sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=True),
    sa.Column('tenant_id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('created_by', sa.UUID(), nullable=True),
    sa.Column('updated_by', sa.UUID(), nullable=True),
    sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
    sa.ForeignKeyConstraint(['tenant_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('evidence_links',
    sa.Column('evidence_id', sa.UUID(), nullable=False),
    sa.Column('target_type', sa.String(length=100), nullable=False),
    sa.Column('target_id', sa.String(length=255), nullable=False),
    sa.Column('link_type', sa.String(length=100), nullable=False),
    sa.Column('confidence_score', sa.Numeric(precision=5, scale=2), nullable=True),
    sa.Column('source_system', sa.String(length=150), nullable=True),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('version_no', sa.Integer(), server_default='1', nullable=True),
    sa.Column('is_deleted', sa.Boolean(), server_default='FALSE', nullable=True),
    sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=True),
    sa.Column('tenant_id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('created_by', sa.UUID(), nullable=True),
    sa.Column('updated_by', sa.UUID(), nullable=True),
    sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
    sa.ForeignKeyConstraint(['tenant_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_evidence_links_evidence_id'), 'evidence_links', ['evidence_id'], unique=False)
    op.create_index(op.f('ix_evidence_links_target_id'), 'evidence_links', ['target_id'], unique=False)
    op.create_index(op.f('ix_evidence_links_target_type'), 'evidence_links', ['target_type'], unique=False)
    op.create_table('generic_relationships',
    sa.Column('source_type', sa.String(length=100), nullable=False),
    sa.Column('source_id', sa.String(length=255), nullable=False),
    sa.Column('relationship_type', sa.String(length=100), nullable=False),
    sa.Column('target_type', sa.String(length=100), nullable=False),
    sa.Column('target_id', sa.String(length=255), nullable=False),
    sa.Column('relationship_scope', sa.String(length=255), nullable=True),
    sa.Column('scope_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('responsibility_type', sa.String(length=100), nullable=True),
    sa.Column('effective_from', sa.TIMESTAMP(timezone=True), nullable=False),
    sa.Column('effective_to', sa.TIMESTAMP(timezone=True), nullable=True),
    sa.Column('status', sa.String(length=50), nullable=False),
    sa.Column('approved_by', sa.UUID(), nullable=True),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('version_no', sa.Integer(), server_default='1', nullable=True),
    sa.Column('is_deleted', sa.Boolean(), server_default='FALSE', nullable=True),
    sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=True),
    sa.Column('tenant_id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('created_by', sa.UUID(), nullable=True),
    sa.Column('updated_by', sa.UUID(), nullable=True),
    sa.ForeignKeyConstraint(['approved_by'], ['users.id'], ),
    sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
    sa.ForeignKeyConstraint(['tenant_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_generic_relationships_relationship_type'), 'generic_relationships', ['relationship_type'], unique=False)
    op.create_index(op.f('ix_generic_relationships_source_id'), 'generic_relationships', ['source_id'], unique=False)
    op.create_index(op.f('ix_generic_relationships_source_type'), 'generic_relationships', ['source_type'], unique=False)
    op.create_index(op.f('ix_generic_relationships_target_id'), 'generic_relationships', ['target_id'], unique=False)
    op.create_index(op.f('ix_generic_relationships_target_type'), 'generic_relationships', ['target_type'], unique=False)
    op.create_table('object_responsibilities',
    sa.Column('object_type', sa.String(length=100), nullable=False),
    sa.Column('object_id', sa.String(length=255), nullable=False),
    sa.Column('actor_type', sa.String(length=50), nullable=False),
    sa.Column('actor_id', sa.String(length=255), nullable=False),
    sa.Column('responsibility_type', sa.String(length=50), nullable=False),
    sa.Column('is_primary', sa.Boolean(), nullable=False),
    sa.Column('effective_from', sa.TIMESTAMP(timezone=True), nullable=False),
    sa.Column('effective_to', sa.TIMESTAMP(timezone=True), nullable=True),
    sa.Column('status', sa.String(length=50), nullable=False),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('version_no', sa.Integer(), server_default='1', nullable=True),
    sa.Column('is_deleted', sa.Boolean(), server_default='FALSE', nullable=True),
    sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=True),
    sa.Column('tenant_id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('created_by', sa.UUID(), nullable=True),
    sa.Column('updated_by', sa.UUID(), nullable=True),
    sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
    sa.ForeignKeyConstraint(['tenant_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_object_responsibilities_actor_id'), 'object_responsibilities', ['actor_id'], unique=False)
    op.create_index(op.f('ix_object_responsibilities_object_id'), 'object_responsibilities', ['object_id'], unique=False)
    op.create_index(op.f('ix_object_responsibilities_object_type'), 'object_responsibilities', ['object_type'], unique=False)
    op.create_table('relationship_graph_snapshots',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('tenant_id', sa.UUID(), nullable=False),
    sa.Column('root_object_type', sa.String(length=100), nullable=False),
    sa.Column('root_object_id', sa.String(length=255), nullable=False),
    sa.Column('depth', sa.Integer(), nullable=False),
    sa.Column('snapshot_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('generated_by', sa.UUID(), nullable=True),
    sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('expires_at', sa.TIMESTAMP(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['generated_by'], ['users.id'], ),
    sa.ForeignKeyConstraint(['tenant_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_relationship_graph_snapshots_root_object_id'), 'relationship_graph_snapshots', ['root_object_id'], unique=False)
    op.create_index(op.f('ix_relationship_graph_snapshots_root_object_type'), 'relationship_graph_snapshots', ['root_object_type'], unique=False)
    op.create_table('relationship_validation_results',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('tenant_id', sa.UUID(), nullable=False),
    sa.Column('request_id', sa.String(length=150), nullable=False),
    sa.Column('relationship_id', sa.UUID(), nullable=True),
    sa.Column('validation_rule_id', sa.String(length=50), nullable=False),
    sa.Column('validation_status', sa.String(length=50), nullable=False),
    sa.Column('severity', sa.String(length=50), nullable=False),
    sa.Column('message', sa.Text(), nullable=False),
    sa.Column('resolution_hint', sa.Text(), nullable=True),
    sa.Column('payload_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['tenant_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_relationship_validation_results_request_id'), 'relationship_validation_results', ['request_id'], unique=False)
    op.create_table('tools',
    sa.Column('tool_code', sa.String(length=80), nullable=False),
    sa.Column('tool_name', sa.String(length=200), nullable=False),
    sa.Column('tool_category', sa.String(length=80), nullable=False),
    sa.Column('access_mode', sa.String(length=80), nullable=False),
    sa.Column('owner_user_id', sa.UUID(), nullable=True),
    sa.Column('sensitivity_level', sa.String(length=50), nullable=False),
    sa.Column('allowed_operations_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('endpoint_reference', sa.String(length=500), nullable=True),
    sa.Column('status', sa.String(length=30), nullable=True),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('version_no', sa.Integer(), server_default='1', nullable=True),
    sa.Column('is_deleted', sa.Boolean(), server_default='FALSE', nullable=True),
    sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=True),
    sa.Column('tenant_id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('created_by', sa.UUID(), nullable=True),
    sa.Column('updated_by', sa.UUID(), nullable=True),
    sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
    sa.ForeignKeyConstraint(['owner_user_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['tenant_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('tool_code')
    )
    op.create_table('workflows',
    sa.Column('workflow_code', sa.String(length=80), nullable=False),
    sa.Column('workflow_name', sa.String(length=200), nullable=False),
    sa.Column('workflow_type', sa.String(length=80), nullable=False),
    sa.Column('department_id', sa.UUID(), nullable=True),
    sa.Column('owner_user_id', sa.UUID(), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('approval_required', sa.Boolean(), nullable=True),
    sa.Column('approver_user_id', sa.UUID(), nullable=True),
    sa.Column('business_criticality', sa.String(length=50), nullable=False),
    sa.Column('status', sa.String(length=30), nullable=True),
    sa.Column('steps_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('version_no', sa.Integer(), server_default='1', nullable=True),
    sa.Column('is_deleted', sa.Boolean(), server_default='FALSE', nullable=True),
    sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=True),
    sa.Column('tenant_id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('created_by', sa.UUID(), nullable=True),
    sa.Column('updated_by', sa.UUID(), nullable=True),
    sa.ForeignKeyConstraint(['approver_user_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
    sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ),
    sa.ForeignKeyConstraint(['owner_user_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['tenant_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('workflow_code')
    )
    op.create_table('policy_bindings',
    sa.Column('policy_id', sa.UUID(), nullable=False),
    sa.Column('target_type', sa.String(length=100), nullable=False),
    sa.Column('target_id', sa.String(length=255), nullable=False),
    sa.Column('binding_scope', sa.String(length=255), nullable=True),
    sa.Column('priority', sa.Integer(), nullable=False),
    sa.Column('is_mandatory', sa.Boolean(), nullable=False),
    sa.Column('effective_from', sa.TIMESTAMP(timezone=True), nullable=False),
    sa.Column('effective_to', sa.TIMESTAMP(timezone=True), nullable=True),
    sa.Column('status', sa.String(length=50), nullable=False),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('version_no', sa.Integer(), server_default='1', nullable=True),
    sa.Column('is_deleted', sa.Boolean(), server_default='FALSE', nullable=True),
    sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=True),
    sa.Column('tenant_id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('created_by', sa.UUID(), nullable=True),
    sa.Column('updated_by', sa.UUID(), nullable=True),
    sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
    sa.ForeignKeyConstraint(['policy_id'], ['policies.id'], ),
    sa.ForeignKeyConstraint(['tenant_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_policy_bindings_target_id'), 'policy_bindings', ['target_id'], unique=False)
    op.create_index(op.f('ix_policy_bindings_target_type'), 'policy_bindings', ['target_type'], unique=False)
    op.create_table('register_all',
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('department_id', sa.UUID(), nullable=True),
    sa.Column('role_id', sa.UUID(), nullable=True),
    sa.Column('user_id', sa.UUID(), nullable=True),
    sa.Column('data_source_id', sa.UUID(), nullable=True),
    sa.Column('model_id', sa.UUID(), nullable=True),
    sa.Column('agent_id', sa.UUID(), nullable=True),
    sa.Column('tool_id', sa.UUID(), nullable=True),
    sa.Column('workflow_id', sa.UUID(), nullable=True),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('version_no', sa.Integer(), server_default='1', nullable=True),
    sa.Column('is_deleted', sa.Boolean(), server_default='FALSE', nullable=True),
    sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=True),
    sa.Column('tenant_id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('created_by', sa.UUID(), nullable=True),
    sa.Column('updated_by', sa.UUID(), nullable=True),
    sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ),
    sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
    sa.ForeignKeyConstraint(['data_source_id'], ['data_sources.id'], ),
    sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ),
    sa.ForeignKeyConstraint(['model_id'], ['ai_models.id'], ),
    sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ),
    sa.ForeignKeyConstraint(['tenant_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['tool_id'], ['tools.id'], ),
    sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['workflow_id'], ['workflows.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.execute('DROP TABLE IF EXISTS \"registry_relationships\" CASCADE')
    op.execute('DROP TABLE IF EXISTS \"registry_audit_events\" CASCADE')
    op.execute('DROP TABLE IF EXISTS \"registry_workflows\" CASCADE')
    op.execute('DROP TABLE IF EXISTS \"registry_roles\" CASCADE')
    op.execute('DROP TABLE IF EXISTS \"guardian_users\" CASCADE')
    op.execute('DROP TABLE IF EXISTS \"registry_ai_agents\" CASCADE')
    op.execute('DROP TABLE IF EXISTS \"registry_departments\" CASCADE')
    op.execute('DROP TABLE IF EXISTS \"registry_ai_models\" CASCADE')
    op.execute('DROP TABLE IF EXISTS \"registry_ai_model_providers\" CASCADE')
    op.execute('DROP TABLE IF EXISTS \"registry_data_sources\" CASCADE')
    op.execute('DROP TABLE IF EXISTS \"registry_tools\" CASCADE')
    op.execute('DROP TABLE IF EXISTS \"registry_register_all\" CASCADE')

    # --- DYNAMIC ORPHAN CLEANUP WITH SAVEPOINTS ---
    conn = op.get_bind()
    orphan_queries = [
        "DELETE FROM agents WHERE owner_user_id NOT IN (SELECT id FROM users) AND owner_user_id IS NOT NULL",
        "DELETE FROM agents WHERE created_by NOT IN (SELECT id FROM users) AND created_by IS NOT NULL",
        "DELETE FROM agents WHERE tenant_id NOT IN (SELECT id FROM users) AND tenant_id IS NOT NULL",
        "DELETE FROM agents WHERE updated_by NOT IN (SELECT id FROM users) AND updated_by IS NOT NULL",
        "DELETE FROM agents WHERE department_id NOT IN (SELECT id FROM departments) AND department_id IS NOT NULL",
        "DELETE FROM ai_models WHERE department_id NOT IN (SELECT id FROM departments) AND department_id IS NOT NULL",
        "DELETE FROM ai_models WHERE tenant_id NOT IN (SELECT id FROM users) AND tenant_id IS NOT NULL",
        "DELETE FROM ai_models WHERE created_by NOT IN (SELECT id FROM users) AND created_by IS NOT NULL",
        "DELETE FROM ai_models WHERE owner_user_id NOT IN (SELECT id FROM users) AND owner_user_id IS NOT NULL",
        "DELETE FROM ai_models WHERE updated_by NOT IN (SELECT id FROM users) AND updated_by IS NOT NULL",
        "DELETE FROM ai_models WHERE provider_id NOT IN (SELECT id FROM ai_model_providers) AND provider_id IS NOT NULL",
        "DELETE FROM approval_group_members WHERE user_id NOT IN (SELECT id FROM users) AND user_id IS NOT NULL",
        "DELETE FROM approval_groups WHERE created_by NOT IN (SELECT id FROM users) AND created_by IS NOT NULL",
        "DELETE FROM approval_groups WHERE tenant_id NOT IN (SELECT id FROM users) AND tenant_id IS NOT NULL",
        "DELETE FROM approval_groups WHERE updated_by NOT IN (SELECT id FROM users) AND updated_by IS NOT NULL",
        "DELETE FROM data_sources WHERE department_id NOT IN (SELECT id FROM departments) AND department_id IS NOT NULL",
        "DELETE FROM data_sources WHERE tenant_id NOT IN (SELECT id FROM users) AND tenant_id IS NOT NULL",
        "DELETE FROM data_sources WHERE owner_user_id NOT IN (SELECT id FROM users) AND owner_user_id IS NOT NULL",
        "DELETE FROM data_sources WHERE created_by NOT IN (SELECT id FROM users) AND created_by IS NOT NULL",
        "DELETE FROM data_sources WHERE updated_by NOT IN (SELECT id FROM users) AND updated_by IS NOT NULL",
        "DELETE FROM departments WHERE updated_by NOT IN (SELECT id FROM users) AND updated_by IS NOT NULL",
        "DELETE FROM departments WHERE tenant_id NOT IN (SELECT id FROM users) AND tenant_id IS NOT NULL",
        "DELETE FROM departments WHERE created_by NOT IN (SELECT id FROM users) AND created_by IS NOT NULL",
        "DELETE FROM orchestration_workflow_executions WHERE workflow_id NOT IN (SELECT id FROM workflows) AND workflow_id IS NOT NULL",
        "DELETE FROM orchestration_workflow_schedules WHERE workflow_id NOT IN (SELECT id FROM workflows) AND workflow_id IS NOT NULL",
        "DELETE FROM policies WHERE updated_by NOT IN (SELECT id FROM users) AND updated_by IS NOT NULL",
        "DELETE FROM policies WHERE created_by NOT IN (SELECT id FROM users) AND created_by IS NOT NULL",
        "DELETE FROM policies WHERE tenant_id NOT IN (SELECT id FROM users) AND tenant_id IS NOT NULL",
        "DELETE FROM users WHERE department_id NOT IN (SELECT id FROM departments) AND department_id IS NOT NULL",
        "DELETE FROM workflow_authorization_decisions WHERE subject_agent_id NOT IN (SELECT id FROM agents) AND subject_agent_id IS NOT NULL",
        "DELETE FROM workflow_authorization_decisions WHERE tenant_id NOT IN (SELECT id FROM users) AND tenant_id IS NOT NULL",
        "DELETE FROM workflow_authorization_decisions WHERE updated_by NOT IN (SELECT id FROM users) AND updated_by IS NOT NULL",
        "DELETE FROM workflow_authorization_decisions WHERE subject_user_id NOT IN (SELECT id FROM users) AND subject_user_id IS NOT NULL",
        "DELETE FROM workflow_authorization_decisions WHERE created_by NOT IN (SELECT id FROM users) AND created_by IS NOT NULL",
        "DELETE FROM workflow_delegations WHERE delegatee_user_id NOT IN (SELECT id FROM users) AND delegatee_user_id IS NOT NULL",
        "DELETE FROM workflow_delegations WHERE delegator_user_id NOT IN (SELECT id FROM users) AND delegator_user_id IS NOT NULL",
        "DELETE FROM workflow_delegations WHERE created_by NOT IN (SELECT id FROM users) AND created_by IS NOT NULL",
        "DELETE FROM workflow_delegations WHERE tenant_id NOT IN (SELECT id FROM users) AND tenant_id IS NOT NULL",
        "DELETE FROM workflow_delegations WHERE updated_by NOT IN (SELECT id FROM users) AND updated_by IS NOT NULL",
        "DELETE FROM workflow_notifications WHERE tenant_id NOT IN (SELECT id FROM users) AND tenant_id IS NOT NULL",
        "DELETE FROM workflow_notifications WHERE updated_by NOT IN (SELECT id FROM users) AND updated_by IS NOT NULL",
        "DELETE FROM workflow_notifications WHERE recipient_user_id NOT IN (SELECT id FROM users) AND recipient_user_id IS NOT NULL",
        "DELETE FROM workflow_notifications WHERE created_by NOT IN (SELECT id FROM users) AND created_by IS NOT NULL",
        "DELETE FROM workflow_run_failures WHERE created_by NOT IN (SELECT id FROM users) AND created_by IS NOT NULL",
        "DELETE FROM workflow_run_failures WHERE tenant_id NOT IN (SELECT id FROM users) AND tenant_id IS NOT NULL",
        "DELETE FROM workflow_run_failures WHERE updated_by NOT IN (SELECT id FROM users) AND updated_by IS NOT NULL",
        "DELETE FROM workflow_run_outputs WHERE tenant_id NOT IN (SELECT id FROM users) AND tenant_id IS NOT NULL",
        "DELETE FROM workflow_run_outputs WHERE updated_by NOT IN (SELECT id FROM users) AND updated_by IS NOT NULL",
        "DELETE FROM workflow_run_outputs WHERE created_by NOT IN (SELECT id FROM users) AND created_by IS NOT NULL",
        "DELETE FROM workflow_run_steps WHERE created_by NOT IN (SELECT id FROM users) AND created_by IS NOT NULL",
        "DELETE FROM workflow_run_steps WHERE tenant_id NOT IN (SELECT id FROM users) AND tenant_id IS NOT NULL",
        "DELETE FROM workflow_run_steps WHERE updated_by NOT IN (SELECT id FROM users) AND updated_by IS NOT NULL",
        "DELETE FROM workflow_runs WHERE workflow_id NOT IN (SELECT id FROM workflows) AND workflow_id IS NOT NULL",
        "DELETE FROM workflow_runs WHERE triggered_by_user_id NOT IN (SELECT id FROM users) AND triggered_by_user_id IS NOT NULL",
        "DELETE FROM workflow_runs WHERE tenant_id NOT IN (SELECT id FROM users) AND tenant_id IS NOT NULL",
        "DELETE FROM workflow_runs WHERE updated_by NOT IN (SELECT id FROM users) AND updated_by IS NOT NULL",
        "DELETE FROM workflow_runs WHERE created_by NOT IN (SELECT id FROM users) AND created_by IS NOT NULL",
        "DELETE FROM workflow_schedule_agent_assignments WHERE created_by NOT IN (SELECT id FROM users) AND created_by IS NOT NULL",
        "DELETE FROM workflow_schedule_agent_assignments WHERE updated_by NOT IN (SELECT id FROM users) AND updated_by IS NOT NULL",
        "DELETE FROM workflow_schedule_agent_assignments WHERE agent_id NOT IN (SELECT id FROM agents) AND agent_id IS NOT NULL",
        "DELETE FROM workflow_schedule_agent_assignments WHERE model_id NOT IN (SELECT id FROM ai_models) AND model_id IS NOT NULL",
        "DELETE FROM workflow_schedule_agent_assignments WHERE tenant_id NOT IN (SELECT id FROM users) AND tenant_id IS NOT NULL",
        "DELETE FROM workflow_schedule_approvals WHERE submitted_by NOT IN (SELECT id FROM users) AND submitted_by IS NOT NULL",
        "DELETE FROM workflow_schedule_approvals WHERE approver_user_id NOT IN (SELECT id FROM users) AND approver_user_id IS NOT NULL",
        "DELETE FROM workflow_schedule_approvals WHERE tenant_id NOT IN (SELECT id FROM users) AND tenant_id IS NOT NULL",
        "DELETE FROM workflow_schedule_approvals WHERE created_by NOT IN (SELECT id FROM users) AND created_by IS NOT NULL",
        "DELETE FROM workflow_schedule_approvals WHERE updated_by NOT IN (SELECT id FROM users) AND updated_by IS NOT NULL",
        "DELETE FROM workflow_schedule_history WHERE created_by NOT IN (SELECT id FROM users) AND created_by IS NOT NULL",
        "DELETE FROM workflow_schedule_history WHERE updated_by NOT IN (SELECT id FROM users) AND updated_by IS NOT NULL",
        "DELETE FROM workflow_schedule_history WHERE tenant_id NOT IN (SELECT id FROM users) AND tenant_id IS NOT NULL",
        "DELETE FROM workflow_schedule_history WHERE changed_by NOT IN (SELECT id FROM users) AND changed_by IS NOT NULL",
        "DELETE FROM workflow_schedules WHERE tenant_id NOT IN (SELECT id FROM users) AND tenant_id IS NOT NULL",
        "DELETE FROM workflow_schedules WHERE created_by NOT IN (SELECT id FROM users) AND created_by IS NOT NULL",
        "DELETE FROM workflow_schedules WHERE updated_by NOT IN (SELECT id FROM users) AND updated_by IS NOT NULL",
        "DELETE FROM workflow_schedules WHERE owner_department_id NOT IN (SELECT id FROM departments) AND owner_department_id IS NOT NULL",
        "DELETE FROM workflow_schedules WHERE owner_user_id NOT IN (SELECT id FROM users) AND owner_user_id IS NOT NULL",
        "DELETE FROM workflow_schedules WHERE workflow_id NOT IN (SELECT id FROM workflows) AND workflow_id IS NOT NULL",
        "DELETE FROM agents WHERE ai_model_id NOT IN (SELECT id FROM ai_models) AND ai_model_id IS NOT NULL",
        "DELETE FROM departments WHERE owner_user_id NOT IN (SELECT id FROM users) AND owner_user_id IS NOT NULL",
        "DELETE FROM ai_models WHERE data_source_id NOT IN (SELECT id FROM data_sources) AND data_source_id IS NOT NULL",
        "DELETE FROM user_roles WHERE user_id NOT IN (SELECT id FROM users) AND user_id IS NOT NULL",
        "DELETE FROM policies WHERE created_by NOT IN (SELECT id FROM users) AND created_by IS NOT NULL",
        "DELETE FROM user_roles WHERE role_id NOT IN (SELECT id FROM roles) AND role_id IS NOT NULL",
        "DELETE FROM role_permissions WHERE role_id NOT IN (SELECT id FROM roles) AND role_id IS NOT NULL",
        "DELETE FROM recommendations WHERE agent_id NOT IN (SELECT id FROM agents) AND agent_id IS NOT NULL",
        "DELETE FROM recommendations WHERE policy_id NOT IN (SELECT id FROM policies) AND policy_id IS NOT NULL",
        "DELETE FROM workflow_schedules WHERE workflow_id NOT IN (SELECT id FROM registry_workflows) AND workflow_id IS NOT NULL",
        "DELETE FROM workflow_schedules WHERE tenant_id NOT IN (SELECT id FROM guardian_users) AND tenant_id IS NOT NULL",
        "DELETE FROM workflow_schedules WHERE owner_user_id NOT IN (SELECT id FROM guardian_users) AND owner_user_id IS NOT NULL",
        "DELETE FROM workflow_schedules WHERE owner_department_id NOT IN (SELECT id FROM registry_departments) AND owner_department_id IS NOT NULL",
        "DELETE FROM workflow_schedules WHERE updated_by NOT IN (SELECT id FROM guardian_users) AND updated_by IS NOT NULL",
        "DELETE FROM workflow_schedules WHERE created_by NOT IN (SELECT id FROM guardian_users) AND created_by IS NOT NULL",
        "DELETE FROM workflow_schedule_history WHERE changed_by NOT IN (SELECT id FROM guardian_users) AND changed_by IS NOT NULL",
        "DELETE FROM workflow_schedule_history WHERE updated_by NOT IN (SELECT id FROM guardian_users) AND updated_by IS NOT NULL",
        "DELETE FROM workflow_schedule_history WHERE tenant_id NOT IN (SELECT id FROM guardian_users) AND tenant_id IS NOT NULL",
        "DELETE FROM workflow_schedule_history WHERE created_by NOT IN (SELECT id FROM guardian_users) AND created_by IS NOT NULL",
        "DELETE FROM workflow_schedule_approvals WHERE updated_by NOT IN (SELECT id FROM guardian_users) AND updated_by IS NOT NULL",
        "DELETE FROM workflow_schedule_approvals WHERE approver_user_id NOT IN (SELECT id FROM guardian_users) AND approver_user_id IS NOT NULL",
        "DELETE FROM workflow_schedule_approvals WHERE created_by NOT IN (SELECT id FROM guardian_users) AND created_by IS NOT NULL",
        "DELETE FROM workflow_schedule_approvals WHERE tenant_id NOT IN (SELECT id FROM guardian_users) AND tenant_id IS NOT NULL",
        "DELETE FROM workflow_schedule_approvals WHERE submitted_by NOT IN (SELECT id FROM guardian_users) AND submitted_by IS NOT NULL",
        "DELETE FROM workflow_schedule_agent_assignments WHERE created_by NOT IN (SELECT id FROM guardian_users) AND created_by IS NOT NULL",
        "DELETE FROM workflow_schedule_agent_assignments WHERE updated_by NOT IN (SELECT id FROM guardian_users) AND updated_by IS NOT NULL",
        "DELETE FROM workflow_schedule_agent_assignments WHERE tenant_id NOT IN (SELECT id FROM guardian_users) AND tenant_id IS NOT NULL",
        "DELETE FROM workflow_schedule_agent_assignments WHERE model_id NOT IN (SELECT id FROM registry_ai_models) AND model_id IS NOT NULL",
        "DELETE FROM workflow_schedule_agent_assignments WHERE agent_id NOT IN (SELECT id FROM registry_ai_agents) AND agent_id IS NOT NULL",
        "DELETE FROM workflow_runs WHERE updated_by NOT IN (SELECT id FROM guardian_users) AND updated_by IS NOT NULL",
        "DELETE FROM workflow_runs WHERE tenant_id NOT IN (SELECT id FROM guardian_users) AND tenant_id IS NOT NULL",
        "DELETE FROM workflow_runs WHERE triggered_by_user_id NOT IN (SELECT id FROM guardian_users) AND triggered_by_user_id IS NOT NULL",
        "DELETE FROM workflow_runs WHERE created_by NOT IN (SELECT id FROM guardian_users) AND created_by IS NOT NULL",
        "DELETE FROM workflow_runs WHERE workflow_id NOT IN (SELECT id FROM registry_workflows) AND workflow_id IS NOT NULL",
        "DELETE FROM workflow_run_steps WHERE updated_by NOT IN (SELECT id FROM guardian_users) AND updated_by IS NOT NULL",
        "DELETE FROM workflow_run_steps WHERE tenant_id NOT IN (SELECT id FROM guardian_users) AND tenant_id IS NOT NULL",
        "DELETE FROM workflow_run_steps WHERE created_by NOT IN (SELECT id FROM guardian_users) AND created_by IS NOT NULL",
        "DELETE FROM workflow_run_outputs WHERE tenant_id NOT IN (SELECT id FROM guardian_users) AND tenant_id IS NOT NULL",
        "DELETE FROM workflow_run_outputs WHERE created_by NOT IN (SELECT id FROM guardian_users) AND created_by IS NOT NULL",
        "DELETE FROM workflow_run_outputs WHERE updated_by NOT IN (SELECT id FROM guardian_users) AND updated_by IS NOT NULL",
        "DELETE FROM workflow_run_failures WHERE tenant_id NOT IN (SELECT id FROM guardian_users) AND tenant_id IS NOT NULL",
        "DELETE FROM workflow_run_failures WHERE created_by NOT IN (SELECT id FROM guardian_users) AND created_by IS NOT NULL",
        "DELETE FROM workflow_run_failures WHERE updated_by NOT IN (SELECT id FROM guardian_users) AND updated_by IS NOT NULL",
        "DELETE FROM workflow_notifications WHERE created_by NOT IN (SELECT id FROM guardian_users) AND created_by IS NOT NULL",
        "DELETE FROM workflow_notifications WHERE tenant_id NOT IN (SELECT id FROM guardian_users) AND tenant_id IS NOT NULL",
        "DELETE FROM workflow_notifications WHERE recipient_user_id NOT IN (SELECT id FROM guardian_users) AND recipient_user_id IS NOT NULL",
        "DELETE FROM workflow_notifications WHERE updated_by NOT IN (SELECT id FROM guardian_users) AND updated_by IS NOT NULL",
        "DELETE FROM workflow_delegations WHERE updated_by NOT IN (SELECT id FROM guardian_users) AND updated_by IS NOT NULL",
        "DELETE FROM workflow_delegations WHERE delegator_user_id NOT IN (SELECT id FROM guardian_users) AND delegator_user_id IS NOT NULL",
        "DELETE FROM workflow_delegations WHERE created_by NOT IN (SELECT id FROM guardian_users) AND created_by IS NOT NULL",
        "DELETE FROM workflow_delegations WHERE tenant_id NOT IN (SELECT id FROM guardian_users) AND tenant_id IS NOT NULL",
        "DELETE FROM workflow_delegations WHERE delegatee_user_id NOT IN (SELECT id FROM guardian_users) AND delegatee_user_id IS NOT NULL",
        "DELETE FROM workflow_authorization_decisions WHERE subject_agent_id NOT IN (SELECT id FROM registry_ai_agents) AND subject_agent_id IS NOT NULL",
        "DELETE FROM workflow_authorization_decisions WHERE tenant_id NOT IN (SELECT id FROM guardian_users) AND tenant_id IS NOT NULL",
        "DELETE FROM workflow_authorization_decisions WHERE subject_user_id NOT IN (SELECT id FROM guardian_users) AND subject_user_id IS NOT NULL",
        "DELETE FROM workflow_authorization_decisions WHERE created_by NOT IN (SELECT id FROM guardian_users) AND created_by IS NOT NULL",
        "DELETE FROM workflow_authorization_decisions WHERE updated_by NOT IN (SELECT id FROM guardian_users) AND updated_by IS NOT NULL",
        "DELETE FROM orchestration_workflow_schedules WHERE workflow_id NOT IN (SELECT id FROM registry_workflows) AND workflow_id IS NOT NULL",
        "DELETE FROM orchestration_workflow_executions WHERE workflow_id NOT IN (SELECT id FROM registry_workflows) AND workflow_id IS NOT NULL",
        "DELETE FROM data_sources WHERE owner_department_id NOT IN (SELECT id FROM departments) AND owner_department_id IS NOT NULL",
        "DELETE FROM approval_groups WHERE created_by NOT IN (SELECT id FROM guardian_users) AND created_by IS NOT NULL",
        "DELETE FROM approval_groups WHERE updated_by NOT IN (SELECT id FROM guardian_users) AND updated_by IS NOT NULL",
        "DELETE FROM approval_groups WHERE tenant_id NOT IN (SELECT id FROM guardian_users) AND tenant_id IS NOT NULL",
        "DELETE FROM approval_group_members WHERE user_id NOT IN (SELECT id FROM guardian_users) AND user_id IS NOT NULL",
        "DELETE FROM ai_models WHERE owner_department_id NOT IN (SELECT id FROM departments) AND owner_department_id IS NOT NULL",
        "DELETE FROM agents WHERE ai_model_id NOT IN (SELECT id FROM ai_models) AND ai_model_id IS NOT NULL",
        "DELETE FROM departments WHERE owner_user_id NOT IN (SELECT id FROM users) AND owner_user_id IS NOT NULL",
        "DELETE FROM ai_models WHERE data_source_id NOT IN (SELECT id FROM data_sources) AND data_source_id IS NOT NULL",
        "DELETE FROM user_roles WHERE user_id NOT IN (SELECT id FROM users) AND user_id IS NOT NULL",
        "DELETE FROM policies WHERE created_by NOT IN (SELECT id FROM users) AND created_by IS NOT NULL",
        "DELETE FROM user_roles WHERE role_id NOT IN (SELECT id FROM roles) AND role_id IS NOT NULL",
        "DELETE FROM role_permissions WHERE role_id NOT IN (SELECT id FROM roles) AND role_id IS NOT NULL",
        "DELETE FROM recommendations WHERE agent_id NOT IN (SELECT id FROM agents) AND agent_id IS NOT NULL",
        "DELETE FROM recommendations WHERE policy_id NOT IN (SELECT id FROM policies) AND policy_id IS NOT NULL",
    ]
    for _ in range(10):  # Maximum dependency depth
        for query in orphan_queries:
            try:
                with conn.begin_nested():
                    conn.execute(sa.text(query))
            except Exception:
                pass
    # ----------------------------------------------
    op.execute('''
    DO $$
    DECLARE r RECORD;
    BEGIN
        FOR r IN (
            SELECT constraint_name
            FROM information_schema.key_column_usage
            WHERE table_name = 'agents' AND column_name = 'owner_user_id'
        ) LOOP
            EXECUTE 'ALTER TABLE agents DROP CONSTRAINT IF EXISTS ' || r.constraint_name || ' CASCADE';
        END LOOP;
    END $$;
    ''')
    op.create_foreign_key(None, 'agents', 'users', ['owner_user_id'], ['id'])
    op.execute('''
    DO $$
    DECLARE r RECORD;
    BEGIN
        FOR r IN (
            SELECT constraint_name
            FROM information_schema.key_column_usage
            WHERE table_name = 'agents' AND column_name = 'created_by'
        ) LOOP
            EXECUTE 'ALTER TABLE agents DROP CONSTRAINT IF EXISTS ' || r.constraint_name || ' CASCADE';
        END LOOP;
    END $$;
    ''')
    op.create_foreign_key(None, 'agents', 'users', ['created_by'], ['id'])
    op.execute('''
    DO $$
    DECLARE r RECORD;
    BEGIN
        FOR r IN (
            SELECT constraint_name
            FROM information_schema.key_column_usage
            WHERE table_name = 'agents' AND column_name = 'tenant_id'
        ) LOOP
            EXECUTE 'ALTER TABLE agents DROP CONSTRAINT IF EXISTS ' || r.constraint_name || ' CASCADE';
        END LOOP;
    END $$;
    ''')
    op.create_foreign_key(None, 'agents', 'users', ['tenant_id'], ['id'])
    op.execute('''
    DO $$
    DECLARE r RECORD;
    BEGIN
        FOR r IN (
            SELECT constraint_name
            FROM information_schema.key_column_usage
            WHERE table_name = 'agents' AND column_name = 'updated_by'
        ) LOOP
            EXECUTE 'ALTER TABLE agents DROP CONSTRAINT IF EXISTS ' || r.constraint_name || ' CASCADE';
        END LOOP;
    END $$;
    ''')
    op.create_foreign_key(None, 'agents', 'users', ['updated_by'], ['id'])
    op.execute('''
    DO $$
    DECLARE r RECORD;
    BEGIN
        FOR r IN (
            SELECT constraint_name
            FROM information_schema.key_column_usage
            WHERE table_name = 'agents' AND column_name = 'department_id'
        ) LOOP
            EXECUTE 'ALTER TABLE agents DROP CONSTRAINT IF EXISTS ' || r.constraint_name || ' CASCADE';
        END LOOP;
    END $$;
    ''')
    op.create_foreign_key(None, 'agents', 'departments', ['department_id'], ['id'])
    op.execute('''
    DO $$
    DECLARE r RECORD;
    BEGIN
        FOR r IN (
            SELECT constraint_name
            FROM information_schema.key_column_usage
            WHERE table_name = 'ai_models' AND column_name = 'department_id'
        ) LOOP
            EXECUTE 'ALTER TABLE ai_models DROP CONSTRAINT IF EXISTS ' || r.constraint_name || ' CASCADE';
        END LOOP;
    END $$;
    ''')
    op.create_foreign_key(None, 'ai_models', 'departments', ['department_id'], ['id'])
    op.execute('''
    DO $$
    DECLARE r RECORD;
    BEGIN
        FOR r IN (
            SELECT constraint_name
            FROM information_schema.key_column_usage
            WHERE table_name = 'ai_models' AND column_name = 'tenant_id'
        ) LOOP
            EXECUTE 'ALTER TABLE ai_models DROP CONSTRAINT IF EXISTS ' || r.constraint_name || ' CASCADE';
        END LOOP;
    END $$;
    ''')
    op.create_foreign_key(None, 'ai_models', 'users', ['tenant_id'], ['id'])
    op.execute('''
    DO $$
    DECLARE r RECORD;
    BEGIN
        FOR r IN (
            SELECT constraint_name
            FROM information_schema.key_column_usage
            WHERE table_name = 'ai_models' AND column_name = 'created_by'
        ) LOOP
            EXECUTE 'ALTER TABLE ai_models DROP CONSTRAINT IF EXISTS ' || r.constraint_name || ' CASCADE';
        END LOOP;
    END $$;
    ''')
    op.create_foreign_key(None, 'ai_models', 'users', ['created_by'], ['id'])
    op.execute('''
    DO $$
    DECLARE r RECORD;
    BEGIN
        FOR r IN (
            SELECT constraint_name
            FROM information_schema.key_column_usage
            WHERE table_name = 'ai_models' AND column_name = 'owner_user_id'
        ) LOOP
            EXECUTE 'ALTER TABLE ai_models DROP CONSTRAINT IF EXISTS ' || r.constraint_name || ' CASCADE';
        END LOOP;
    END $$;
    ''')
    op.create_foreign_key(None, 'ai_models', 'users', ['owner_user_id'], ['id'])
    op.execute('''
    DO $$
    DECLARE r RECORD;
    BEGIN
        FOR r IN (
            SELECT constraint_name
            FROM information_schema.key_column_usage
            WHERE table_name = 'ai_models' AND column_name = 'updated_by'
        ) LOOP
            EXECUTE 'ALTER TABLE ai_models DROP CONSTRAINT IF EXISTS ' || r.constraint_name || ' CASCADE';
        END LOOP;
    END $$;
    ''')
    op.create_foreign_key(None, 'ai_models', 'users', ['updated_by'], ['id'])
    # [Safe Migrations] Skipped FK to dropped table ai_model_providers: op.create_foreign_key(None, 'ai_models', 'ai_model_providers', ['provider_id'], ['id'])
    op.execute('''
    DO $$
    DECLARE r RECORD;
    BEGIN
        FOR r IN (
            SELECT constraint_name
            FROM information_schema.key_column_usage
            WHERE table_name = 'approval_group_members' AND column_name = 'user_id'
        ) LOOP
            EXECUTE 'ALTER TABLE approval_group_members DROP CONSTRAINT IF EXISTS ' || r.constraint_name || ' CASCADE';
        END LOOP;
    END $$;
    ''')
    op.create_foreign_key(None, 'approval_group_members', 'users', ['user_id'], ['id'], ondelete='CASCADE')
    op.execute('''
    DO $$
    DECLARE r RECORD;
    BEGIN
        FOR r IN (
            SELECT constraint_name
            FROM information_schema.key_column_usage
            WHERE table_name = 'approval_groups' AND column_name = 'created_by'
        ) LOOP
            EXECUTE 'ALTER TABLE approval_groups DROP CONSTRAINT IF EXISTS ' || r.constraint_name || ' CASCADE';
        END LOOP;
    END $$;
    ''')
    op.create_foreign_key(None, 'approval_groups', 'users', ['created_by'], ['id'])
    op.execute('''
    DO $$
    DECLARE r RECORD;
    BEGIN
        FOR r IN (
            SELECT constraint_name
            FROM information_schema.key_column_usage
            WHERE table_name = 'approval_groups' AND column_name = 'tenant_id'
        ) LOOP
            EXECUTE 'ALTER TABLE approval_groups DROP CONSTRAINT IF EXISTS ' || r.constraint_name || ' CASCADE';
        END LOOP;
    END $$;
    ''')
    op.create_foreign_key(None, 'approval_groups', 'users', ['tenant_id'], ['id'])
    op.execute('''
    DO $$
    DECLARE r RECORD;
    BEGIN
        FOR r IN (
            SELECT constraint_name
            FROM information_schema.key_column_usage
            WHERE table_name = 'approval_groups' AND column_name = 'updated_by'
        ) LOOP
            EXECUTE 'ALTER TABLE approval_groups DROP CONSTRAINT IF EXISTS ' || r.constraint_name || ' CASCADE';
        END LOOP;
    END $$;
    ''')
    op.create_foreign_key(None, 'approval_groups', 'users', ['updated_by'], ['id'])
    op.execute('''
    DO $$
    DECLARE r RECORD;
    BEGIN
        FOR r IN (
            SELECT constraint_name
            FROM information_schema.key_column_usage
            WHERE table_name = 'data_sources' AND column_name = 'department_id'
        ) LOOP
            EXECUTE 'ALTER TABLE data_sources DROP CONSTRAINT IF EXISTS ' || r.constraint_name || ' CASCADE';
        END LOOP;
    END $$;
    ''')
    op.create_foreign_key(None, 'data_sources', 'departments', ['department_id'], ['id'])
    op.execute('''
    DO $$
    DECLARE r RECORD;
    BEGIN
        FOR r IN (
            SELECT constraint_name
            FROM information_schema.key_column_usage
            WHERE table_name = 'data_sources' AND column_name = 'tenant_id'
        ) LOOP
            EXECUTE 'ALTER TABLE data_sources DROP CONSTRAINT IF EXISTS ' || r.constraint_name || ' CASCADE';
        END LOOP;
    END $$;
    ''')
    op.create_foreign_key(None, 'data_sources', 'users', ['tenant_id'], ['id'])
    op.execute('''
    DO $$
    DECLARE r RECORD;
    BEGIN
        FOR r IN (
            SELECT constraint_name
            FROM information_schema.key_column_usage
            WHERE table_name = 'data_sources' AND column_name = 'owner_user_id'
        ) LOOP
            EXECUTE 'ALTER TABLE data_sources DROP CONSTRAINT IF EXISTS ' || r.constraint_name || ' CASCADE';
        END LOOP;
    END $$;
    ''')
    op.create_foreign_key(None, 'data_sources', 'users', ['owner_user_id'], ['id'])
    op.execute('''
    DO $$
    DECLARE r RECORD;
    BEGIN
        FOR r IN (
            SELECT constraint_name
            FROM information_schema.key_column_usage
            WHERE table_name = 'data_sources' AND column_name = 'created_by'
        ) LOOP
            EXECUTE 'ALTER TABLE data_sources DROP CONSTRAINT IF EXISTS ' || r.constraint_name || ' CASCADE';
        END LOOP;
    END $$;
    ''')
    op.create_foreign_key(None, 'data_sources', 'users', ['created_by'], ['id'])
    op.execute('''
    DO $$
    DECLARE r RECORD;
    BEGIN
        FOR r IN (
            SELECT constraint_name
            FROM information_schema.key_column_usage
            WHERE table_name = 'data_sources' AND column_name = 'updated_by'
        ) LOOP
            EXECUTE 'ALTER TABLE data_sources DROP CONSTRAINT IF EXISTS ' || r.constraint_name || ' CASCADE';
        END LOOP;
    END $$;
    ''')
    op.create_foreign_key(None, 'data_sources', 'users', ['updated_by'], ['id'])
    op.execute('''
    DO $$
    DECLARE r RECORD;
    BEGIN
        FOR r IN (
            SELECT constraint_name
            FROM information_schema.key_column_usage
            WHERE table_name = 'departments' AND column_name = 'updated_by'
        ) LOOP
            EXECUTE 'ALTER TABLE departments DROP CONSTRAINT IF EXISTS ' || r.constraint_name || ' CASCADE';
        END LOOP;
    END $$;
    ''')
    op.create_foreign_key(None, 'departments', 'users', ['updated_by'], ['id'])
    op.execute('''
    DO $$
    DECLARE r RECORD;
    BEGIN
        FOR r IN (
            SELECT constraint_name
            FROM information_schema.key_column_usage
            WHERE table_name = 'departments' AND column_name = 'tenant_id'
        ) LOOP
            EXECUTE 'ALTER TABLE departments DROP CONSTRAINT IF EXISTS ' || r.constraint_name || ' CASCADE';
        END LOOP;
    END $$;
    ''')
    op.create_foreign_key(None, 'departments', 'users', ['tenant_id'], ['id'])
    op.execute('''
    DO $$
    DECLARE r RECORD;
    BEGIN
        FOR r IN (
            SELECT constraint_name
            FROM information_schema.key_column_usage
            WHERE table_name = 'departments' AND column_name = 'created_by'
        ) LOOP
            EXECUTE 'ALTER TABLE departments DROP CONSTRAINT IF EXISTS ' || r.constraint_name || ' CASCADE';
        END LOOP;
    END $$;
    ''')
    op.create_foreign_key(None, 'departments', 'users', ['created_by'], ['id'])
    # [Safe Migrations] Skipped FK to dropped table workflows: op.create_foreign_key(None, 'orchestration_workflow_executions', 'workflows', ['workflow_id'], ['id'])
    # [Safe Migrations] Skipped FK to dropped table workflows: op.create_foreign_key(None, 'orchestration_workflow_schedules', 'workflows', ['workflow_id'], ['id'])
    op.execute('''
    DO $$
    DECLARE r RECORD;
    BEGIN
        FOR r IN (
            SELECT constraint_name
            FROM information_schema.key_column_usage
            WHERE table_name = 'policies' AND column_name = 'updated_by'
        ) LOOP
            EXECUTE 'ALTER TABLE policies DROP CONSTRAINT IF EXISTS ' || r.constraint_name || ' CASCADE';
        END LOOP;
    END $$;
    ''')
    op.create_foreign_key(None, 'policies', 'users', ['updated_by'], ['id'])
    op.execute('''
    DO $$
    DECLARE r RECORD;
    BEGIN
        FOR r IN (
            SELECT constraint_name
            FROM information_schema.key_column_usage
            WHERE table_name = 'policies' AND column_name = 'created_by'
        ) LOOP
            EXECUTE 'ALTER TABLE policies DROP CONSTRAINT IF EXISTS ' || r.constraint_name || ' CASCADE';
        END LOOP;
    END $$;
    ''')
    op.create_foreign_key(None, 'policies', 'users', ['created_by'], ['id'])
    op.execute('''
    DO $$
    DECLARE r RECORD;
    BEGIN
        FOR r IN (
            SELECT constraint_name
            FROM information_schema.key_column_usage
            WHERE table_name = 'policies' AND column_name = 'tenant_id'
        ) LOOP
            EXECUTE 'ALTER TABLE policies DROP CONSTRAINT IF EXISTS ' || r.constraint_name || ' CASCADE';
        END LOOP;
    END $$;
    ''')
    op.create_foreign_key(None, 'policies', 'users', ['tenant_id'], ['id'])
    op.execute('''
    DO $$
    DECLARE r RECORD;
    BEGIN
        FOR r IN (
            SELECT constraint_name
            FROM information_schema.key_column_usage
            WHERE table_name = 'users' AND column_name = 'department_id'
        ) LOOP
            EXECUTE 'ALTER TABLE users DROP CONSTRAINT IF EXISTS ' || r.constraint_name || ' CASCADE';
        END LOOP;
    END $$;
    ''')
    op.create_foreign_key(None, 'users', 'departments', ['department_id'], ['id'])
    op.execute('''
    DO $$
    DECLARE r RECORD;
    BEGIN
        FOR r IN (
            SELECT constraint_name
            FROM information_schema.key_column_usage
            WHERE table_name = 'workflow_authorization_decisions' AND column_name = 'subject_agent_id'
        ) LOOP
            EXECUTE 'ALTER TABLE workflow_authorization_decisions DROP CONSTRAINT IF EXISTS ' || r.constraint_name || ' CASCADE';
        END LOOP;
    END $$;
    ''')
    op.create_foreign_key(None, 'workflow_authorization_decisions', 'agents', ['subject_agent_id'], ['id'])
    op.execute('''
    DO $$
    DECLARE r RECORD;
    BEGIN
        FOR r IN (
            SELECT constraint_name
            FROM information_schema.key_column_usage
            WHERE table_name = 'workflow_authorization_decisions' AND column_name = 'tenant_id'
        ) LOOP
            EXECUTE 'ALTER TABLE workflow_authorization_decisions DROP CONSTRAINT IF EXISTS ' || r.constraint_name || ' CASCADE';
        END LOOP;
    END $$;
    ''')
    op.create_foreign_key(None, 'workflow_authorization_decisions', 'users', ['tenant_id'], ['id'])
    op.execute('''
    DO $$
    DECLARE r RECORD;
    BEGIN
        FOR r IN (
            SELECT constraint_name
            FROM information_schema.key_column_usage
            WHERE table_name = 'workflow_authorization_decisions' AND column_name = 'updated_by'
        ) LOOP
            EXECUTE 'ALTER TABLE workflow_authorization_decisions DROP CONSTRAINT IF EXISTS ' || r.constraint_name || ' CASCADE';
        END LOOP;
    END $$;
    ''')
    op.create_foreign_key(None, 'workflow_authorization_decisions', 'users', ['updated_by'], ['id'])
    op.execute('''
    DO $$
    DECLARE r RECORD;
    BEGIN
        FOR r IN (
            SELECT constraint_name
            FROM information_schema.key_column_usage
            WHERE table_name = 'workflow_authorization_decisions' AND column_name = 'subject_user_id'
        ) LOOP
            EXECUTE 'ALTER TABLE workflow_authorization_decisions DROP CONSTRAINT IF EXISTS ' || r.constraint_name || ' CASCADE';
        END LOOP;
    END $$;
    ''')
    op.create_foreign_key(None, 'workflow_authorization_decisions', 'users', ['subject_user_id'], ['id'])
    op.execute('''
    DO $$
    DECLARE r RECORD;
    BEGIN
        FOR r IN (
            SELECT constraint_name
            FROM information_schema.key_column_usage
            WHERE table_name = 'workflow_authorization_decisions' AND column_name = 'created_by'
        ) LOOP
            EXECUTE 'ALTER TABLE workflow_authorization_decisions DROP CONSTRAINT IF EXISTS ' || r.constraint_name || ' CASCADE';
        END LOOP;
    END $$;
    ''')
    op.create_foreign_key(None, 'workflow_authorization_decisions', 'users', ['created_by'], ['id'])
    op.execute('''
    DO $$
    DECLARE r RECORD;
    BEGIN
        FOR r IN (
            SELECT constraint_name
            FROM information_schema.key_column_usage
            WHERE table_name = 'workflow_delegations' AND column_name = 'delegatee_user_id'
        ) LOOP
            EXECUTE 'ALTER TABLE workflow_delegations DROP CONSTRAINT IF EXISTS ' || r.constraint_name || ' CASCADE';
        END LOOP;
    END $$;
    ''')
    op.create_foreign_key(None, 'workflow_delegations', 'users', ['delegatee_user_id'], ['id'])
    op.execute('''
    DO $$
    DECLARE r RECORD;
    BEGIN
        FOR r IN (
            SELECT constraint_name
            FROM information_schema.key_column_usage
            WHERE table_name = 'workflow_delegations' AND column_name = 'delegator_user_id'
        ) LOOP
            EXECUTE 'ALTER TABLE workflow_delegations DROP CONSTRAINT IF EXISTS ' || r.constraint_name || ' CASCADE';
        END LOOP;
    END $$;
    ''')
    op.create_foreign_key(None, 'workflow_delegations', 'users', ['delegator_user_id'], ['id'])
    op.execute('''
    DO $$
    DECLARE r RECORD;
    BEGIN
        FOR r IN (
            SELECT constraint_name
            FROM information_schema.key_column_usage
            WHERE table_name = 'workflow_delegations' AND column_name = 'created_by'
        ) LOOP
            EXECUTE 'ALTER TABLE workflow_delegations DROP CONSTRAINT IF EXISTS ' || r.constraint_name || ' CASCADE';
        END LOOP;
    END $$;
    ''')
    op.create_foreign_key(None, 'workflow_delegations', 'users', ['created_by'], ['id'])
    op.execute('''
    DO $$
    DECLARE r RECORD;
    BEGIN
        FOR r IN (
            SELECT constraint_name
            FROM information_schema.key_column_usage
            WHERE table_name = 'workflow_delegations' AND column_name = 'tenant_id'
        ) LOOP
            EXECUTE 'ALTER TABLE workflow_delegations DROP CONSTRAINT IF EXISTS ' || r.constraint_name || ' CASCADE';
        END LOOP;
    END $$;
    ''')
    op.create_foreign_key(None, 'workflow_delegations', 'users', ['tenant_id'], ['id'])
    op.execute('''
    DO $$
    DECLARE r RECORD;
    BEGIN
        FOR r IN (
            SELECT constraint_name
            FROM information_schema.key_column_usage
            WHERE table_name = 'workflow_delegations' AND column_name = 'updated_by'
        ) LOOP
            EXECUTE 'ALTER TABLE workflow_delegations DROP CONSTRAINT IF EXISTS ' || r.constraint_name || ' CASCADE';
        END LOOP;
    END $$;
    ''')
    op.create_foreign_key(None, 'workflow_delegations', 'users', ['updated_by'], ['id'])
    op.execute('''
    DO $$
    DECLARE r RECORD;
    BEGIN
        FOR r IN (
            SELECT constraint_name
            FROM information_schema.key_column_usage
            WHERE table_name = 'workflow_notifications' AND column_name = 'tenant_id'
        ) LOOP
            EXECUTE 'ALTER TABLE workflow_notifications DROP CONSTRAINT IF EXISTS ' || r.constraint_name || ' CASCADE';
        END LOOP;
    END $$;
    ''')
    op.create_foreign_key(None, 'workflow_notifications', 'users', ['tenant_id'], ['id'])
    op.execute('''
    DO $$
    DECLARE r RECORD;
    BEGIN
        FOR r IN (
            SELECT constraint_name
            FROM information_schema.key_column_usage
            WHERE table_name = 'workflow_notifications' AND column_name = 'updated_by'
        ) LOOP
            EXECUTE 'ALTER TABLE workflow_notifications DROP CONSTRAINT IF EXISTS ' || r.constraint_name || ' CASCADE';
        END LOOP;
    END $$;
    ''')
    op.create_foreign_key(None, 'workflow_notifications', 'users', ['updated_by'], ['id'])
    op.execute('''
    DO $$
    DECLARE r RECORD;
    BEGIN
        FOR r IN (
            SELECT constraint_name
            FROM information_schema.key_column_usage
            WHERE table_name = 'workflow_notifications' AND column_name = 'recipient_user_id'
        ) LOOP
            EXECUTE 'ALTER TABLE workflow_notifications DROP CONSTRAINT IF EXISTS ' || r.constraint_name || ' CASCADE';
        END LOOP;
    END $$;
    ''')
    op.create_foreign_key(None, 'workflow_notifications', 'users', ['recipient_user_id'], ['id'])
    op.execute('''
    DO $$
    DECLARE r RECORD;
    BEGIN
        FOR r IN (
            SELECT constraint_name
            FROM information_schema.key_column_usage
            WHERE table_name = 'workflow_notifications' AND column_name = 'created_by'
        ) LOOP
            EXECUTE 'ALTER TABLE workflow_notifications DROP CONSTRAINT IF EXISTS ' || r.constraint_name || ' CASCADE';
        END LOOP;
    END $$;
    ''')
    op.create_foreign_key(None, 'workflow_notifications', 'users', ['created_by'], ['id'])
    op.execute('''
    DO $$
    DECLARE r RECORD;
    BEGIN
        FOR r IN (
            SELECT constraint_name
            FROM information_schema.key_column_usage
            WHERE table_name = 'workflow_run_failures' AND column_name = 'created_by'
        ) LOOP
            EXECUTE 'ALTER TABLE workflow_run_failures DROP CONSTRAINT IF EXISTS ' || r.constraint_name || ' CASCADE';
        END LOOP;
    END $$;
    ''')
    op.create_foreign_key(None, 'workflow_run_failures', 'users', ['created_by'], ['id'])
    op.execute('''
    DO $$
    DECLARE r RECORD;
    BEGIN
        FOR r IN (
            SELECT constraint_name
            FROM information_schema.key_column_usage
            WHERE table_name = 'workflow_run_failures' AND column_name = 'tenant_id'
        ) LOOP
            EXECUTE 'ALTER TABLE workflow_run_failures DROP CONSTRAINT IF EXISTS ' || r.constraint_name || ' CASCADE';
        END LOOP;
    END $$;
    ''')
    op.create_foreign_key(None, 'workflow_run_failures', 'users', ['tenant_id'], ['id'])
    op.execute('''
    DO $$
    DECLARE r RECORD;
    BEGIN
        FOR r IN (
            SELECT constraint_name
            FROM information_schema.key_column_usage
            WHERE table_name = 'workflow_run_failures' AND column_name = 'updated_by'
        ) LOOP
            EXECUTE 'ALTER TABLE workflow_run_failures DROP CONSTRAINT IF EXISTS ' || r.constraint_name || ' CASCADE';
        END LOOP;
    END $$;
    ''')
    op.create_foreign_key(None, 'workflow_run_failures', 'users', ['updated_by'], ['id'])
    op.execute('''
    DO $$
    DECLARE r RECORD;
    BEGIN
        FOR r IN (
            SELECT constraint_name
            FROM information_schema.key_column_usage
            WHERE table_name = 'workflow_run_outputs' AND column_name = 'tenant_id'
        ) LOOP
            EXECUTE 'ALTER TABLE workflow_run_outputs DROP CONSTRAINT IF EXISTS ' || r.constraint_name || ' CASCADE';
        END LOOP;
    END $$;
    ''')
    op.create_foreign_key(None, 'workflow_run_outputs', 'users', ['tenant_id'], ['id'])
    op.execute('''
    DO $$
    DECLARE r RECORD;
    BEGIN
        FOR r IN (
            SELECT constraint_name
            FROM information_schema.key_column_usage
            WHERE table_name = 'workflow_run_outputs' AND column_name = 'updated_by'
        ) LOOP
            EXECUTE 'ALTER TABLE workflow_run_outputs DROP CONSTRAINT IF EXISTS ' || r.constraint_name || ' CASCADE';
        END LOOP;
    END $$;
    ''')
    op.create_foreign_key(None, 'workflow_run_outputs', 'users', ['updated_by'], ['id'])
    op.execute('''
    DO $$
    DECLARE r RECORD;
    BEGIN
        FOR r IN (
            SELECT constraint_name
            FROM information_schema.key_column_usage
            WHERE table_name = 'workflow_run_outputs' AND column_name = 'created_by'
        ) LOOP
            EXECUTE 'ALTER TABLE workflow_run_outputs DROP CONSTRAINT IF EXISTS ' || r.constraint_name || ' CASCADE';
        END LOOP;
    END $$;
    ''')
    op.create_foreign_key(None, 'workflow_run_outputs', 'users', ['created_by'], ['id'])
    op.execute('''
    DO $$
    DECLARE r RECORD;
    BEGIN
        FOR r IN (
            SELECT constraint_name
            FROM information_schema.key_column_usage
            WHERE table_name = 'workflow_run_steps' AND column_name = 'created_by'
        ) LOOP
            EXECUTE 'ALTER TABLE workflow_run_steps DROP CONSTRAINT IF EXISTS ' || r.constraint_name || ' CASCADE';
        END LOOP;
    END $$;
    ''')
    op.create_foreign_key(None, 'workflow_run_steps', 'users', ['created_by'], ['id'])
    op.execute('''
    DO $$
    DECLARE r RECORD;
    BEGIN
        FOR r IN (
            SELECT constraint_name
            FROM information_schema.key_column_usage
            WHERE table_name = 'workflow_run_steps' AND column_name = 'tenant_id'
        ) LOOP
            EXECUTE 'ALTER TABLE workflow_run_steps DROP CONSTRAINT IF EXISTS ' || r.constraint_name || ' CASCADE';
        END LOOP;
    END $$;
    ''')
    op.create_foreign_key(None, 'workflow_run_steps', 'users', ['tenant_id'], ['id'])
    op.execute('''
    DO $$
    DECLARE r RECORD;
    BEGIN
        FOR r IN (
            SELECT constraint_name
            FROM information_schema.key_column_usage
            WHERE table_name = 'workflow_run_steps' AND column_name = 'updated_by'
        ) LOOP
            EXECUTE 'ALTER TABLE workflow_run_steps DROP CONSTRAINT IF EXISTS ' || r.constraint_name || ' CASCADE';
        END LOOP;
    END $$;
    ''')
    op.create_foreign_key(None, 'workflow_run_steps', 'users', ['updated_by'], ['id'])
    # [Safe Migrations] Skipped FK to dropped table workflows: op.create_foreign_key(None, 'workflow_runs', 'workflows', ['workflow_id'], ['id'])
    op.execute('''
    DO $$
    DECLARE r RECORD;
    BEGIN
        FOR r IN (
            SELECT constraint_name
            FROM information_schema.key_column_usage
            WHERE table_name = 'workflow_runs' AND column_name = 'triggered_by_user_id'
        ) LOOP
            EXECUTE 'ALTER TABLE workflow_runs DROP CONSTRAINT IF EXISTS ' || r.constraint_name || ' CASCADE';
        END LOOP;
    END $$;
    ''')
    op.create_foreign_key(None, 'workflow_runs', 'users', ['triggered_by_user_id'], ['id'])
    op.execute('''
    DO $$
    DECLARE r RECORD;
    BEGIN
        FOR r IN (
            SELECT constraint_name
            FROM information_schema.key_column_usage
            WHERE table_name = 'workflow_runs' AND column_name = 'tenant_id'
        ) LOOP
            EXECUTE 'ALTER TABLE workflow_runs DROP CONSTRAINT IF EXISTS ' || r.constraint_name || ' CASCADE';
        END LOOP;
    END $$;
    ''')
    op.create_foreign_key(None, 'workflow_runs', 'users', ['tenant_id'], ['id'])
    op.execute('''
    DO $$
    DECLARE r RECORD;
    BEGIN
        FOR r IN (
            SELECT constraint_name
            FROM information_schema.key_column_usage
            WHERE table_name = 'workflow_runs' AND column_name = 'updated_by'
        ) LOOP
            EXECUTE 'ALTER TABLE workflow_runs DROP CONSTRAINT IF EXISTS ' || r.constraint_name || ' CASCADE';
        END LOOP;
    END $$;
    ''')
    op.create_foreign_key(None, 'workflow_runs', 'users', ['updated_by'], ['id'])
    op.execute('''
    DO $$
    DECLARE r RECORD;
    BEGIN
        FOR r IN (
            SELECT constraint_name
            FROM information_schema.key_column_usage
            WHERE table_name = 'workflow_runs' AND column_name = 'created_by'
        ) LOOP
            EXECUTE 'ALTER TABLE workflow_runs DROP CONSTRAINT IF EXISTS ' || r.constraint_name || ' CASCADE';
        END LOOP;
    END $$;
    ''')
    op.create_foreign_key(None, 'workflow_runs', 'users', ['created_by'], ['id'])
    op.execute('''
    DO $$
    DECLARE r RECORD;
    BEGIN
        FOR r IN (
            SELECT constraint_name
            FROM information_schema.key_column_usage
            WHERE table_name = 'workflow_schedule_agent_assignments' AND column_name = 'created_by'
        ) LOOP
            EXECUTE 'ALTER TABLE workflow_schedule_agent_assignments DROP CONSTRAINT IF EXISTS ' || r.constraint_name || ' CASCADE';
        END LOOP;
    END $$;
    ''')
    op.create_foreign_key(None, 'workflow_schedule_agent_assignments', 'users', ['created_by'], ['id'])
    op.execute('''
    DO $$
    DECLARE r RECORD;
    BEGIN
        FOR r IN (
            SELECT constraint_name
            FROM information_schema.key_column_usage
            WHERE table_name = 'workflow_schedule_agent_assignments' AND column_name = 'updated_by'
        ) LOOP
            EXECUTE 'ALTER TABLE workflow_schedule_agent_assignments DROP CONSTRAINT IF EXISTS ' || r.constraint_name || ' CASCADE';
        END LOOP;
    END $$;
    ''')
    op.create_foreign_key(None, 'workflow_schedule_agent_assignments', 'users', ['updated_by'], ['id'])
    op.execute('''
    DO $$
    DECLARE r RECORD;
    BEGIN
        FOR r IN (
            SELECT constraint_name
            FROM information_schema.key_column_usage
            WHERE table_name = 'workflow_schedule_agent_assignments' AND column_name = 'agent_id'
        ) LOOP
            EXECUTE 'ALTER TABLE workflow_schedule_agent_assignments DROP CONSTRAINT IF EXISTS ' || r.constraint_name || ' CASCADE';
        END LOOP;
    END $$;
    ''')
    op.create_foreign_key(None, 'workflow_schedule_agent_assignments', 'agents', ['agent_id'], ['id'])
    op.execute('''
    DO $$
    DECLARE r RECORD;
    BEGIN
        FOR r IN (
            SELECT constraint_name
            FROM information_schema.key_column_usage
            WHERE table_name = 'workflow_schedule_agent_assignments' AND column_name = 'model_id'
        ) LOOP
            EXECUTE 'ALTER TABLE workflow_schedule_agent_assignments DROP CONSTRAINT IF EXISTS ' || r.constraint_name || ' CASCADE';
        END LOOP;
    END $$;
    ''')
    op.create_foreign_key(None, 'workflow_schedule_agent_assignments', 'ai_models', ['model_id'], ['id'])
    op.execute('''
    DO $$
    DECLARE r RECORD;
    BEGIN
        FOR r IN (
            SELECT constraint_name
            FROM information_schema.key_column_usage
            WHERE table_name = 'workflow_schedule_agent_assignments' AND column_name = 'tenant_id'
        ) LOOP
            EXECUTE 'ALTER TABLE workflow_schedule_agent_assignments DROP CONSTRAINT IF EXISTS ' || r.constraint_name || ' CASCADE';
        END LOOP;
    END $$;
    ''')
    op.create_foreign_key(None, 'workflow_schedule_agent_assignments', 'users', ['tenant_id'], ['id'])
    op.execute('''
    DO $$
    DECLARE r RECORD;
    BEGIN
        FOR r IN (
            SELECT constraint_name
            FROM information_schema.key_column_usage
            WHERE table_name = 'workflow_schedule_approvals' AND column_name = 'submitted_by'
        ) LOOP
            EXECUTE 'ALTER TABLE workflow_schedule_approvals DROP CONSTRAINT IF EXISTS ' || r.constraint_name || ' CASCADE';
        END LOOP;
    END $$;
    ''')
    op.create_foreign_key(None, 'workflow_schedule_approvals', 'users', ['submitted_by'], ['id'])
    op.execute('''
    DO $$
    DECLARE r RECORD;
    BEGIN
        FOR r IN (
            SELECT constraint_name
            FROM information_schema.key_column_usage
            WHERE table_name = 'workflow_schedule_approvals' AND column_name = 'approver_user_id'
        ) LOOP
            EXECUTE 'ALTER TABLE workflow_schedule_approvals DROP CONSTRAINT IF EXISTS ' || r.constraint_name || ' CASCADE';
        END LOOP;
    END $$;
    ''')
    op.create_foreign_key(None, 'workflow_schedule_approvals', 'users', ['approver_user_id'], ['id'])
    op.execute('''
    DO $$
    DECLARE r RECORD;
    BEGIN
        FOR r IN (
            SELECT constraint_name
            FROM information_schema.key_column_usage
            WHERE table_name = 'workflow_schedule_approvals' AND column_name = 'tenant_id'
        ) LOOP
            EXECUTE 'ALTER TABLE workflow_schedule_approvals DROP CONSTRAINT IF EXISTS ' || r.constraint_name || ' CASCADE';
        END LOOP;
    END $$;
    ''')
    op.create_foreign_key(None, 'workflow_schedule_approvals', 'users', ['tenant_id'], ['id'])
    op.execute('''
    DO $$
    DECLARE r RECORD;
    BEGIN
        FOR r IN (
            SELECT constraint_name
            FROM information_schema.key_column_usage
            WHERE table_name = 'workflow_schedule_approvals' AND column_name = 'created_by'
        ) LOOP
            EXECUTE 'ALTER TABLE workflow_schedule_approvals DROP CONSTRAINT IF EXISTS ' || r.constraint_name || ' CASCADE';
        END LOOP;
    END $$;
    ''')
    op.create_foreign_key(None, 'workflow_schedule_approvals', 'users', ['created_by'], ['id'])
    op.execute('''
    DO $$
    DECLARE r RECORD;
    BEGIN
        FOR r IN (
            SELECT constraint_name
            FROM information_schema.key_column_usage
            WHERE table_name = 'workflow_schedule_approvals' AND column_name = 'updated_by'
        ) LOOP
            EXECUTE 'ALTER TABLE workflow_schedule_approvals DROP CONSTRAINT IF EXISTS ' || r.constraint_name || ' CASCADE';
        END LOOP;
    END $$;
    ''')
    op.create_foreign_key(None, 'workflow_schedule_approvals', 'users', ['updated_by'], ['id'])
    op.execute('''
    DO $$
    DECLARE r RECORD;
    BEGIN
        FOR r IN (
            SELECT constraint_name
            FROM information_schema.key_column_usage
            WHERE table_name = 'workflow_schedule_history' AND column_name = 'created_by'
        ) LOOP
            EXECUTE 'ALTER TABLE workflow_schedule_history DROP CONSTRAINT IF EXISTS ' || r.constraint_name || ' CASCADE';
        END LOOP;
    END $$;
    ''')
    op.create_foreign_key(None, 'workflow_schedule_history', 'users', ['created_by'], ['id'])
    op.execute('''
    DO $$
    DECLARE r RECORD;
    BEGIN
        FOR r IN (
            SELECT constraint_name
            FROM information_schema.key_column_usage
            WHERE table_name = 'workflow_schedule_history' AND column_name = 'updated_by'
        ) LOOP
            EXECUTE 'ALTER TABLE workflow_schedule_history DROP CONSTRAINT IF EXISTS ' || r.constraint_name || ' CASCADE';
        END LOOP;
    END $$;
    ''')
    op.create_foreign_key(None, 'workflow_schedule_history', 'users', ['updated_by'], ['id'])
    op.execute('''
    DO $$
    DECLARE r RECORD;
    BEGIN
        FOR r IN (
            SELECT constraint_name
            FROM information_schema.key_column_usage
            WHERE table_name = 'workflow_schedule_history' AND column_name = 'tenant_id'
        ) LOOP
            EXECUTE 'ALTER TABLE workflow_schedule_history DROP CONSTRAINT IF EXISTS ' || r.constraint_name || ' CASCADE';
        END LOOP;
    END $$;
    ''')
    op.create_foreign_key(None, 'workflow_schedule_history', 'users', ['tenant_id'], ['id'])
    op.execute('''
    DO $$
    DECLARE r RECORD;
    BEGIN
        FOR r IN (
            SELECT constraint_name
            FROM information_schema.key_column_usage
            WHERE table_name = 'workflow_schedule_history' AND column_name = 'changed_by'
        ) LOOP
            EXECUTE 'ALTER TABLE workflow_schedule_history DROP CONSTRAINT IF EXISTS ' || r.constraint_name || ' CASCADE';
        END LOOP;
    END $$;
    ''')
    op.create_foreign_key(None, 'workflow_schedule_history', 'users', ['changed_by'], ['id'])
    op.execute('''
    DO $$
    DECLARE r RECORD;
    BEGIN
        FOR r IN (
            SELECT constraint_name
            FROM information_schema.key_column_usage
            WHERE table_name = 'workflow_schedules' AND column_name = 'tenant_id'
        ) LOOP
            EXECUTE 'ALTER TABLE workflow_schedules DROP CONSTRAINT IF EXISTS ' || r.constraint_name || ' CASCADE';
        END LOOP;
    END $$;
    ''')
    op.create_foreign_key(None, 'workflow_schedules', 'users', ['tenant_id'], ['id'])
    op.execute('''
    DO $$
    DECLARE r RECORD;
    BEGIN
        FOR r IN (
            SELECT constraint_name
            FROM information_schema.key_column_usage
            WHERE table_name = 'workflow_schedules' AND column_name = 'created_by'
        ) LOOP
            EXECUTE 'ALTER TABLE workflow_schedules DROP CONSTRAINT IF EXISTS ' || r.constraint_name || ' CASCADE';
        END LOOP;
    END $$;
    ''')
    op.create_foreign_key(None, 'workflow_schedules', 'users', ['created_by'], ['id'])
    op.execute('''
    DO $$
    DECLARE r RECORD;
    BEGIN
        FOR r IN (
            SELECT constraint_name
            FROM information_schema.key_column_usage
            WHERE table_name = 'workflow_schedules' AND column_name = 'updated_by'
        ) LOOP
            EXECUTE 'ALTER TABLE workflow_schedules DROP CONSTRAINT IF EXISTS ' || r.constraint_name || ' CASCADE';
        END LOOP;
    END $$;
    ''')
    op.create_foreign_key(None, 'workflow_schedules', 'users', ['updated_by'], ['id'])
    op.execute('''
    DO $$
    DECLARE r RECORD;
    BEGIN
        FOR r IN (
            SELECT constraint_name
            FROM information_schema.key_column_usage
            WHERE table_name = 'workflow_schedules' AND column_name = 'owner_department_id'
        ) LOOP
            EXECUTE 'ALTER TABLE workflow_schedules DROP CONSTRAINT IF EXISTS ' || r.constraint_name || ' CASCADE';
        END LOOP;
    END $$;
    ''')
    op.create_foreign_key(None, 'workflow_schedules', 'departments', ['owner_department_id'], ['id'])
    op.execute('''
    DO $$
    DECLARE r RECORD;
    BEGIN
        FOR r IN (
            SELECT constraint_name
            FROM information_schema.key_column_usage
            WHERE table_name = 'workflow_schedules' AND column_name = 'owner_user_id'
        ) LOOP
            EXECUTE 'ALTER TABLE workflow_schedules DROP CONSTRAINT IF EXISTS ' || r.constraint_name || ' CASCADE';
        END LOOP;
    END $$;
    ''')
    op.create_foreign_key(None, 'workflow_schedules', 'users', ['owner_user_id'], ['id'])
    # [Safe Migrations] Skipped FK to dropped table workflows: op.create_foreign_key(None, 'workflow_schedules', 'workflows', ['workflow_id'], ['id'])
    op.execute('''
    DO $$
    DECLARE r RECORD;
    BEGIN
        FOR r IN (
            SELECT constraint_name
            FROM information_schema.key_column_usage
            WHERE table_name = 'agents' AND column_name = 'ai_model_id'
        ) LOOP
            EXECUTE 'ALTER TABLE agents DROP CONSTRAINT IF EXISTS ' || r.constraint_name || ' CASCADE';
        END LOOP;
    END $$;
    ''')
    op.create_foreign_key('agents_ai_model_id_fkey', 'agents', 'ai_models', ['ai_model_id'], ['id'])
    op.execute('''
    DO $$
    DECLARE r RECORD;
    BEGIN
        FOR r IN (
            SELECT constraint_name
            FROM information_schema.key_column_usage
            WHERE table_name = 'departments' AND column_name = 'owner_user_id'
        ) LOOP
            EXECUTE 'ALTER TABLE departments DROP CONSTRAINT IF EXISTS ' || r.constraint_name || ' CASCADE';
        END LOOP;
    END $$;
    ''')
    op.create_foreign_key('departments_owner_user_id_fkey', 'departments', 'users', ['owner_user_id'], ['id'])
    op.execute('''
    DO $$
    DECLARE r RECORD;
    BEGIN
        FOR r IN (
            SELECT constraint_name
            FROM information_schema.key_column_usage
            WHERE table_name = 'ai_models' AND column_name = 'data_source_id'
        ) LOOP
            EXECUTE 'ALTER TABLE ai_models DROP CONSTRAINT IF EXISTS ' || r.constraint_name || ' CASCADE';
        END LOOP;
    END $$;
    ''')
    op.create_foreign_key('ai_models_data_source_id_fkey', 'ai_models', 'data_sources', ['data_source_id'], ['id'])
    op.execute('''
    DO $$
    DECLARE r RECORD;
    BEGIN
        FOR r IN (
            SELECT constraint_name
            FROM information_schema.key_column_usage
            WHERE table_name = 'user_roles' AND column_name = 'user_id'
        ) LOOP
            EXECUTE 'ALTER TABLE user_roles DROP CONSTRAINT IF EXISTS ' || r.constraint_name || ' CASCADE';
        END LOOP;
    END $$;
    ''')
    op.create_foreign_key('user_roles_user_id_fkey', 'user_roles', 'users', ['user_id'], ['id'])
    op.execute('''
    DO $$
    DECLARE r RECORD;
    BEGIN
        FOR r IN (
            SELECT constraint_name
            FROM information_schema.key_column_usage
            WHERE table_name = 'policies' AND column_name = 'created_by'
        ) LOOP
            EXECUTE 'ALTER TABLE policies DROP CONSTRAINT IF EXISTS ' || r.constraint_name || ' CASCADE';
        END LOOP;
    END $$;
    ''')
    op.create_foreign_key('policies_created_by_fkey', 'policies', 'users', ['created_by'], ['id'])
    op.execute('''
    DO $$
    DECLARE r RECORD;
    BEGIN
        FOR r IN (
            SELECT constraint_name
            FROM information_schema.key_column_usage
            WHERE table_name = 'user_roles' AND column_name = 'role_id'
        ) LOOP
            EXECUTE 'ALTER TABLE user_roles DROP CONSTRAINT IF EXISTS ' || r.constraint_name || ' CASCADE';
        END LOOP;
    END $$;
    ''')
    op.create_foreign_key('user_roles_role_id_fkey', 'user_roles', 'roles', ['role_id'], ['id'])
    op.execute('''
    DO $$
    DECLARE r RECORD;
    BEGIN
        FOR r IN (
            SELECT constraint_name
            FROM information_schema.key_column_usage
            WHERE table_name = 'role_permissions' AND column_name = 'role_id'
        ) LOOP
            EXECUTE 'ALTER TABLE role_permissions DROP CONSTRAINT IF EXISTS ' || r.constraint_name || ' CASCADE';
        END LOOP;
    END $$;
    ''')
    op.create_foreign_key('role_permissions_role_id_fkey', 'role_permissions', 'roles', ['role_id'], ['id'])
    op.execute('''
    DO $$
    DECLARE r RECORD;
    BEGIN
        FOR r IN (
            SELECT constraint_name
            FROM information_schema.key_column_usage
            WHERE table_name = 'recommendations' AND column_name = 'agent_id'
        ) LOOP
            EXECUTE 'ALTER TABLE recommendations DROP CONSTRAINT IF EXISTS ' || r.constraint_name || ' CASCADE';
        END LOOP;
    END $$;
    ''')
    op.create_foreign_key('recommendations_agent_id_fkey', 'recommendations', 'agents', ['agent_id'], ['id'])
    op.execute('''
    DO $$
    DECLARE r RECORD;
    BEGIN
        FOR r IN (
            SELECT constraint_name
            FROM information_schema.key_column_usage
            WHERE table_name = 'recommendations' AND column_name = 'policy_id'
        ) LOOP
            EXECUTE 'ALTER TABLE recommendations DROP CONSTRAINT IF EXISTS ' || r.constraint_name || ' CASCADE';
        END LOOP;
    END $$;
    ''')
    op.create_foreign_key('recommendations_policy_id_fkey', 'recommendations', 'policies', ['policy_id'], ['id'])
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""

    op.execute('''
DO $$
DECLARE r RECORD;
BEGIN
    FOR r IN (
        SELECT c.conname, c.conrelid::regclass::text as tablename
        FROM pg_constraint c
        JOIN pg_class t ON t.oid = c.conrelid
        JOIN pg_attribute a ON a.attnum = ANY(c.conkey) AND a.attrelid = c.conrelid
        JOIN pg_class t2 ON t2.oid = c.confrelid
        JOIN pg_attribute a2 ON a2.attnum = ANY(c.confkey) AND a2.attrelid = c.confrelid
        WHERE c.contype = 'f'
          AND (
             (t.relname = 'agents' AND a.attname = 'ai_model_id')
             OR (t.relname = 'agents' AND a.attname = 'id')
             OR (t.relname = 'ai_models' AND a.attname = 'data_source_id')
             OR (t.relname = 'ai_models' AND a.attname = 'id')
             OR (t.relname = 'approvals' AND a.attname = 'reviewer_id')
             OR (t.relname = 'data_sources' AND a.attname = 'id')
             OR (t.relname = 'departments' AND a.attname = 'parent_id')
             OR (t.relname = 'departments' AND a.attname = 'owner_user_id')
             OR (t.relname = 'departments' AND a.attname = 'id')
             OR (t.relname = 'policies' AND a.attname = 'id')
             OR (t.relname = 'policies' AND a.attname = 'created_by')
             OR (t.relname = 'recommendations' AND a.attname = 'agent_id')
             OR (t.relname = 'recommendations' AND a.attname = 'policy_id')
             OR (t.relname = 'role_permissions' AND a.attname = 'role_id')
             OR (t.relname = 'roles' AND a.attname = 'id')
             OR (t.relname = 'user_roles' AND a.attname = 'user_id')
             OR (t.relname = 'user_roles' AND a.attname = 'role_id')
             OR (t.relname = 'users' AND a.attname = 'id')
             OR (t2.relname = 'agents' AND a2.attname = 'ai_model_id')
             OR (t2.relname = 'agents' AND a2.attname = 'id')
             OR (t2.relname = 'ai_models' AND a2.attname = 'data_source_id')
             OR (t2.relname = 'ai_models' AND a2.attname = 'id')
             OR (t2.relname = 'approvals' AND a2.attname = 'reviewer_id')
             OR (t2.relname = 'data_sources' AND a2.attname = 'id')
             OR (t2.relname = 'departments' AND a2.attname = 'parent_id')
             OR (t2.relname = 'departments' AND a2.attname = 'owner_user_id')
             OR (t2.relname = 'departments' AND a2.attname = 'id')
             OR (t2.relname = 'policies' AND a2.attname = 'id')
             OR (t2.relname = 'policies' AND a2.attname = 'created_by')
             OR (t2.relname = 'recommendations' AND a2.attname = 'agent_id')
             OR (t2.relname = 'recommendations' AND a2.attname = 'policy_id')
             OR (t2.relname = 'role_permissions' AND a2.attname = 'role_id')
             OR (t2.relname = 'roles' AND a2.attname = 'id')
             OR (t2.relname = 'user_roles' AND a2.attname = 'user_id')
             OR (t2.relname = 'user_roles' AND a2.attname = 'role_id')
             OR (t2.relname = 'users' AND a2.attname = 'id')
          )
    )
    LOOP
        EXECUTE 'ALTER TABLE ' || quote_ident(r.tablename) || ' DROP CONSTRAINT IF EXISTS ' || quote_ident(r.conname);
    END LOOP;
END $$;
    ''')
    op.execute('ALTER TABLE departments DROP CONSTRAINT IF EXISTS fk_departments_parent_id')
    op.execute('ALTER TABLE approvals DROP CONSTRAINT IF EXISTS approvals_reviewer_id_fkey')
    op.drop_constraint(None, 'workflow_schedules', type_='foreignkey')
    op.drop_constraint(None, 'workflow_schedules', type_='foreignkey')
    op.drop_constraint(None, 'workflow_schedules', type_='foreignkey')
    op.drop_constraint(None, 'workflow_schedules', type_='foreignkey')
    op.drop_constraint(None, 'workflow_schedules', type_='foreignkey')
    op.drop_constraint(None, 'workflow_schedules', type_='foreignkey')
    op.drop_constraint(None, 'workflow_schedule_history', type_='foreignkey')
    op.drop_constraint(None, 'workflow_schedule_history', type_='foreignkey')
    op.drop_constraint(None, 'workflow_schedule_history', type_='foreignkey')
    op.drop_constraint(None, 'workflow_schedule_history', type_='foreignkey')
    op.drop_constraint(None, 'workflow_schedule_approvals', type_='foreignkey')
    op.drop_constraint(None, 'workflow_schedule_approvals', type_='foreignkey')
    op.drop_constraint(None, 'workflow_schedule_approvals', type_='foreignkey')
    op.drop_constraint(None, 'workflow_schedule_approvals', type_='foreignkey')
    op.drop_constraint(None, 'workflow_schedule_approvals', type_='foreignkey')
    op.drop_constraint(None, 'workflow_schedule_agent_assignments', type_='foreignkey')
    op.drop_constraint(None, 'workflow_schedule_agent_assignments', type_='foreignkey')
    op.drop_constraint(None, 'workflow_schedule_agent_assignments', type_='foreignkey')
    op.drop_constraint(None, 'workflow_schedule_agent_assignments', type_='foreignkey')
    op.drop_constraint(None, 'workflow_schedule_agent_assignments', type_='foreignkey')
    op.drop_constraint(None, 'workflow_runs', type_='foreignkey')
    op.drop_constraint(None, 'workflow_runs', type_='foreignkey')
    op.drop_constraint(None, 'workflow_runs', type_='foreignkey')
    op.drop_constraint(None, 'workflow_runs', type_='foreignkey')
    op.drop_constraint(None, 'workflow_runs', type_='foreignkey')
    op.drop_constraint(None, 'workflow_run_steps', type_='foreignkey')
    op.drop_constraint(None, 'workflow_run_steps', type_='foreignkey')
    op.drop_constraint(None, 'workflow_run_steps', type_='foreignkey')
    op.drop_constraint(None, 'workflow_run_outputs', type_='foreignkey')
    op.drop_constraint(None, 'workflow_run_outputs', type_='foreignkey')
    op.drop_constraint(None, 'workflow_run_outputs', type_='foreignkey')
    op.drop_constraint(None, 'workflow_run_failures', type_='foreignkey')
    op.drop_constraint(None, 'workflow_run_failures', type_='foreignkey')
    op.drop_constraint(None, 'workflow_run_failures', type_='foreignkey')
    op.drop_constraint(None, 'workflow_notifications', type_='foreignkey')
    op.drop_constraint(None, 'workflow_notifications', type_='foreignkey')
    op.drop_constraint(None, 'workflow_notifications', type_='foreignkey')
    op.drop_constraint(None, 'workflow_notifications', type_='foreignkey')
    op.drop_constraint(None, 'workflow_delegations', type_='foreignkey')
    op.drop_constraint(None, 'workflow_delegations', type_='foreignkey')
    op.drop_constraint(None, 'workflow_delegations', type_='foreignkey')
    op.drop_constraint(None, 'workflow_delegations', type_='foreignkey')
    op.drop_constraint(None, 'workflow_delegations', type_='foreignkey')
    op.drop_constraint(None, 'workflow_authorization_decisions', type_='foreignkey')
    op.drop_constraint(None, 'workflow_authorization_decisions', type_='foreignkey')
    op.drop_constraint(None, 'workflow_authorization_decisions', type_='foreignkey')
    op.drop_constraint(None, 'workflow_authorization_decisions', type_='foreignkey')
    op.drop_constraint(None, 'workflow_authorization_decisions', type_='foreignkey')
    op.drop_constraint(None, 'users', type_='foreignkey')
    op.drop_constraint(None, 'policies', type_='foreignkey')
    op.drop_constraint(None, 'policies', type_='foreignkey')
    op.drop_constraint(None, 'policies', type_='foreignkey')
    op.drop_constraint(None, 'orchestration_workflow_schedules', type_='foreignkey')
    op.drop_constraint(None, 'orchestration_workflow_executions', type_='foreignkey')
    op.drop_constraint(None, 'departments', type_='foreignkey')
    op.drop_constraint(None, 'departments', type_='foreignkey')
    op.drop_constraint(None, 'departments', type_='foreignkey')
    op.drop_constraint(None, 'data_sources', type_='foreignkey')
    op.drop_constraint(None, 'data_sources', type_='foreignkey')
    op.drop_constraint(None, 'data_sources', type_='foreignkey')
    op.drop_constraint(None, 'data_sources', type_='foreignkey')
    op.drop_constraint(None, 'data_sources', type_='foreignkey')
    op.drop_constraint(None, 'approval_groups', type_='foreignkey')
    op.drop_constraint(None, 'approval_groups', type_='foreignkey')
    op.drop_constraint(None, 'approval_groups', type_='foreignkey')
    op.drop_constraint(None, 'approval_group_members', type_='foreignkey')
    op.drop_constraint(None, 'ai_models', type_='foreignkey')
    op.drop_constraint(None, 'ai_models', type_='foreignkey')
    op.drop_constraint(None, 'ai_models', type_='foreignkey')
    op.drop_constraint(None, 'ai_models', type_='foreignkey')
    op.drop_constraint(None, 'ai_models', type_='foreignkey')
    op.drop_constraint(None, 'ai_models', type_='foreignkey')
    op.drop_constraint(None, 'agents', type_='foreignkey')
    op.drop_constraint(None, 'agents', type_='foreignkey')
    op.drop_constraint(None, 'agents', type_='foreignkey')
    op.drop_constraint(None, 'agents', type_='foreignkey')
    op.drop_constraint(None, 'agents', type_='foreignkey')
    op.execute('ALTER TABLE user_roles DROP CONSTRAINT IF EXISTS user_roles_user_id_fkey')
    op.execute('ALTER TABLE ai_models DROP CONSTRAINT IF EXISTS ai_models_data_source_id_fkey')
    op.execute('ALTER TABLE policies DROP CONSTRAINT IF EXISTS policies_created_by_fkey')
    op.execute('ALTER TABLE recommendations DROP CONSTRAINT IF EXISTS recommendations_agent_id_fkey')
    op.execute('ALTER TABLE user_roles DROP CONSTRAINT IF EXISTS user_roles_role_id_fkey')
    op.execute('ALTER TABLE role_permissions DROP CONSTRAINT IF EXISTS role_permissions_role_id_fkey')
    op.execute('ALTER TABLE departments DROP CONSTRAINT IF EXISTS departments_owner_user_id_fkey')
    op.execute('ALTER TABLE recommendations DROP CONSTRAINT IF EXISTS recommendations_policy_id_fkey')
    op.execute('ALTER TABLE agents DROP CONSTRAINT IF EXISTS agents_ai_model_id_fkey')
    # ### commands auto generated by Alembic - please adjust! ###
    op.execute('DROP TABLE IF EXISTS \"register_all\" CASCADE')
    op.drop_index(op.f('ix_policy_bindings_target_type'), table_name='policy_bindings')
    op.drop_index(op.f('ix_policy_bindings_target_id'), table_name='policy_bindings')
    op.execute('DROP TABLE IF EXISTS \"policy_bindings\" CASCADE')
    op.execute('DROP TABLE IF EXISTS \"workflows\" CASCADE')
    op.execute('DROP TABLE IF EXISTS \"tools\" CASCADE')
    op.drop_index(op.f('ix_relationship_validation_results_request_id'), table_name='relationship_validation_results')
    op.execute('DROP TABLE IF EXISTS \"relationship_validation_results\" CASCADE')
    op.drop_index(op.f('ix_relationship_graph_snapshots_root_object_type'), table_name='relationship_graph_snapshots')
    op.drop_index(op.f('ix_relationship_graph_snapshots_root_object_id'), table_name='relationship_graph_snapshots')
    op.execute('DROP TABLE IF EXISTS \"relationship_graph_snapshots\" CASCADE')
    op.drop_index(op.f('ix_object_responsibilities_object_type'), table_name='object_responsibilities')
    op.drop_index(op.f('ix_object_responsibilities_object_id'), table_name='object_responsibilities')
    op.drop_index(op.f('ix_object_responsibilities_actor_id'), table_name='object_responsibilities')
    op.execute('DROP TABLE IF EXISTS \"object_responsibilities\" CASCADE')
    op.drop_index(op.f('ix_generic_relationships_target_type'), table_name='generic_relationships')
    op.drop_index(op.f('ix_generic_relationships_target_id'), table_name='generic_relationships')
    op.drop_index(op.f('ix_generic_relationships_source_type'), table_name='generic_relationships')
    op.drop_index(op.f('ix_generic_relationships_source_id'), table_name='generic_relationships')
    op.drop_index(op.f('ix_generic_relationships_relationship_type'), table_name='generic_relationships')
    op.execute('DROP TABLE IF EXISTS \"generic_relationships\" CASCADE')
    op.drop_index(op.f('ix_evidence_links_target_type'), table_name='evidence_links')
    op.drop_index(op.f('ix_evidence_links_target_id'), table_name='evidence_links')
    op.drop_index(op.f('ix_evidence_links_evidence_id'), table_name='evidence_links')
    op.execute('DROP TABLE IF EXISTS \"evidence_links\" CASCADE')
    op.execute('DROP TABLE IF EXISTS \"ai_model_providers\" CASCADE')
    op.drop_constraint('uix_tenant_schedule_name', 'workflow_schedules', type_='unique')
    op.drop_constraint('uix_tenant_schedule_code', 'workflow_schedules', type_='unique')
    op.create_unique_constraint(op.f('uq_workflow_schedules_tenant_code'), 'workflow_schedules', ['tenant_id', 'schedule_code'], postgresql_nulls_not_distinct=False)
    op.create_index(op.f('ix_workflow_schedules_workflow_id'), 'workflow_schedules', ['workflow_id'], unique=False)
    op.create_index(op.f('ix_workflow_schedules_tenant_id'), 'workflow_schedules', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_workflow_schedules_schedule_status'), 'workflow_schedules', ['schedule_status'], unique=False)
    op.create_index(op.f('ix_workflow_schedules_owner_user_id'), 'workflow_schedules', ['owner_user_id'], unique=False)
    op.create_index(op.f('ix_workflow_schedules_next_run_at'), 'workflow_schedules', ['next_run_at'], unique=False)
    op.create_index(op.f('ix_workflow_schedules_metadata_json'), 'workflow_schedules', ['metadata_json'], unique=False, postgresql_using='gin')
    op.alter_column('workflow_schedules', 'metadata_json',
               existing_type=sa.JSON(),
               type_=postgresql.JSONB(astext_type=sa.Text()),
               existing_nullable=True,
               existing_server_default=sa.text("'{}'::jsonb"))
    op.create_index(op.f('ix_workflow_schedule_history_schedule_id'), 'workflow_schedule_history', ['schedule_id'], unique=False)
    op.alter_column('workflow_schedule_history', 'metadata_json',
               existing_type=sa.JSON(),
               type_=postgresql.JSONB(astext_type=sa.Text()),
               existing_nullable=True,
               existing_server_default=sa.text("'{}'::jsonb"))
    op.create_index(op.f('ix_workflow_schedule_approvals_sched_status'), 'workflow_schedule_approvals', ['schedule_id', 'approval_status'], unique=False)
    op.alter_column('workflow_schedule_approvals', 'metadata_json',
               existing_type=sa.JSON(),
               type_=postgresql.JSONB(astext_type=sa.Text()),
               existing_nullable=True,
               existing_server_default=sa.text("'{}'::jsonb"))
    op.create_unique_constraint(op.f('uq_wf_sch_agent_assg_tenant_sch_agent_role'), 'workflow_schedule_agent_assignments', ['tenant_id', 'schedule_id', 'agent_id', 'assignment_role'], postgresql_nulls_not_distinct=False)
    op.alter_column('workflow_schedule_agent_assignments', 'metadata_json',
               existing_type=sa.JSON(),
               type_=postgresql.JSONB(astext_type=sa.Text()),
               existing_nullable=True,
               existing_server_default=sa.text("'{}'::jsonb"))
    op.create_unique_constraint(op.f('uq_workflow_runs_tenant_run_code'), 'workflow_runs', ['tenant_id', 'run_code'], postgresql_nulls_not_distinct=False)
    op.create_index(op.f('ix_workflow_runs_schedule_id'), 'workflow_runs', ['schedule_id'], unique=False)
    op.create_index(op.f('ix_workflow_runs_run_status'), 'workflow_runs', ['run_status'], unique=False)
    op.create_index(op.f('ix_workflow_runs_result_json'), 'workflow_runs', ['result_json'], unique=False, postgresql_using='gin')
    op.create_index(op.f('ix_workflow_runs_created_at_desc'), 'workflow_runs', [sa.literal_column('created_at DESC')], unique=False)
    op.alter_column('workflow_runs', 'metadata_json',
               existing_type=sa.JSON(),
               type_=postgresql.JSONB(astext_type=sa.Text()),
               existing_nullable=True,
               existing_server_default=sa.text("'{}'::jsonb"))
    op.create_index(op.f('ix_workflow_run_steps_run_id'), 'workflow_run_steps', ['run_id'], unique=False)
    op.alter_column('workflow_run_steps', 'metadata_json',
               existing_type=sa.JSON(),
               type_=postgresql.JSONB(astext_type=sa.Text()),
               existing_nullable=True,
               existing_server_default=sa.text("'{}'::jsonb"))
    op.drop_column('workflow_run_steps', 'error_detail')
    op.create_index(op.f('ix_workflow_run_outputs_findings_json'), 'workflow_run_outputs', ['findings_json'], unique=False, postgresql_using='gin')
    op.alter_column('workflow_run_outputs', 'metadata_json',
               existing_type=sa.JSON(),
               type_=postgresql.JSONB(astext_type=sa.Text()),
               existing_nullable=True,
               existing_server_default=sa.text("'{}'::jsonb"))
    op.drop_column('workflow_run_outputs', 'raw_output')
    op.alter_column('workflow_run_failures', 'metadata_json',
               existing_type=sa.JSON(),
               type_=postgresql.JSONB(astext_type=sa.Text()),
               existing_nullable=True,
               existing_server_default=sa.text("'{}'::jsonb"))
    op.drop_column('workflow_run_failures', 'next_retry_at')
    add_col_if_not_exists('workflow_notifications', sa.Column('entity_type', sa.VARCHAR(length=100), autoincrement=False, nullable=True))
    add_col_if_not_exists('workflow_notifications', sa.Column('entity_id', sa.UUID(), autoincrement=False, nullable=True))
    op.create_index(op.f('ix_workflow_notifications_recipient_status'), 'workflow_notifications', ['recipient_user_id', 'status'], unique=False)
    op.alter_column('workflow_notifications', 'metadata_json',
               existing_type=sa.JSON(),
               type_=postgresql.JSONB(astext_type=sa.Text()),
               existing_nullable=True,
               existing_server_default=sa.text("'{}'::jsonb"))
    op.drop_column('workflow_notifications', 'related_entity_id')
    op.drop_column('workflow_notifications', 'related_entity_type')
    op.alter_column('workflow_delegations', 'metadata_json',
               existing_type=sa.JSON(),
               type_=postgresql.JSONB(astext_type=sa.Text()),
               existing_nullable=True,
               existing_server_default=sa.text("'{}'::jsonb"))
    op.alter_column('workflow_authorization_decisions', 'metadata_json',
               existing_type=sa.JSON(),
               type_=postgresql.JSONB(astext_type=sa.Text()),
               existing_nullable=True,
               existing_server_default=sa.text("'{}'::jsonb"))
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.alter_column('users', 'id',
               existing_type=sa.UUID(),
               type_=sa.INTEGER(),
               postgresql_using='0',
               existing_nullable=False)
    op.drop_column('users', 'approval_limit_level')
    op.drop_column('users', 'department_id')
    op.alter_column('user_roles', 'role_id',
               existing_type=sa.UUID(),
               type_=sa.INTEGER(),
               postgresql_using='0',
               existing_nullable=True)
    op.alter_column('user_roles', 'user_id',
               existing_type=sa.UUID(),
               type_=sa.INTEGER(),
               postgresql_using='0',
               existing_nullable=True)
    op.create_index(op.f('ix_roles_id'), 'roles', ['id'], unique=False)
    op.alter_column('roles', 'id',
               existing_type=sa.UUID(),
               type_=sa.INTEGER(),
               postgresql_using='0',
               existing_nullable=False)
    op.alter_column('role_permissions', 'role_id',
               existing_type=sa.UUID(),
               type_=sa.INTEGER(),
               postgresql_using='0',
               existing_nullable=True)
    op.alter_column('recommendations', 'policy_id',
               existing_type=sa.UUID(),
               type_=sa.INTEGER(),
               postgresql_using='0',
               existing_nullable=True)
    op.alter_column('recommendations', 'agent_id',
               existing_type=sa.UUID(),
               type_=sa.INTEGER(),
               postgresql_using='0',
               existing_nullable=True)
    op.create_index(op.f('ix_policies_id'), 'policies', ['id'], unique=False)
    op.alter_column('policies', 'created_by',
               existing_type=sa.UUID(),
               type_=sa.INTEGER(),
               postgresql_using='0',
               existing_nullable=True)
    op.alter_column('policies', 'id',
               existing_type=sa.UUID(),
               type_=sa.INTEGER(),
               postgresql_using='0',
               existing_nullable=False)
    op.drop_column('policies', 'updated_by')
    op.drop_column('policies', 'updated_at')
    op.drop_column('policies', 'created_at')
    op.drop_column('policies', 'tenant_id')
    op.drop_column('policies', 'metadata_json')
    op.drop_column('policies', 'is_deleted')
    op.drop_column('policies', 'version_no')
    op.create_index(op.f('ix_departments_id'), 'departments', ['id'], unique=False)
    op.alter_column('departments', 'updated_at',
               existing_type=postgresql.TIMESTAMP(timezone=True),
               nullable=False,
               existing_server_default=sa.text('now()'))
    op.alter_column('departments', 'created_at',
               existing_type=postgresql.TIMESTAMP(timezone=True),
               nullable=False,
               existing_server_default=sa.text('now()'))
    op.alter_column('departments', 'id',
               existing_type=sa.UUID(),
               type_=sa.INTEGER(),
               postgresql_using='0',
               existing_nullable=False)
    op.alter_column('departments', 'owner_user_id',
               existing_type=sa.UUID(),
               type_=sa.INTEGER(),
               postgresql_using='0',
               existing_nullable=True)
    op.alter_column('departments', 'parent_id',
               existing_type=sa.UUID(),
               type_=sa.INTEGER(),
               postgresql_using='0',
               existing_nullable=True)
    op.drop_column('departments', 'updated_by')
    op.drop_column('departments', 'created_by')
    op.drop_column('departments', 'tenant_id')
    op.drop_column('departments', 'metadata_json')
    op.drop_column('departments', 'is_deleted')
    op.drop_column('departments', 'version_no')
    add_col_if_not_exists('data_sources', sa.Column('description', sa.VARCHAR(), autoincrement=False, nullable=True))
    add_col_if_not_exists('data_sources', sa.Column('owner_department_id', sa.INTEGER(), autoincrement=False, nullable=True))
    op.drop_constraint(None, 'data_sources', type_='unique')
    op.create_index(op.f('ix_data_sources_id'), 'data_sources', ['id'], unique=False)
    op.alter_column('data_sources', 'id',
               existing_type=sa.UUID(),
               type_=sa.INTEGER(),
               postgresql_using='0',
               existing_nullable=False)
    op.drop_column('data_sources', 'updated_by')
    op.drop_column('data_sources', 'created_by')
    op.drop_column('data_sources', 'updated_at')
    op.drop_column('data_sources', 'created_at')
    op.drop_column('data_sources', 'tenant_id')
    op.drop_column('data_sources', 'metadata_json')
    op.drop_column('data_sources', 'is_deleted')
    op.drop_column('data_sources', 'version_no')
    op.drop_column('data_sources', 'connection_reference')
    op.drop_column('data_sources', 'retention_policy')
    op.drop_column('data_sources', 'contains_pii')
    op.drop_column('data_sources', 'region')
    op.drop_column('data_sources', 'sensitivity_level')
    op.drop_column('data_sources', 'classification')
    op.drop_column('data_sources', 'department_id')
    op.drop_column('data_sources', 'owner_user_id')
    op.drop_column('data_sources', 'source_code')
    op.alter_column('approvals', 'reviewer_id',
               existing_type=sa.UUID(),
               type_=sa.INTEGER(),
               postgresql_using='0',
               existing_nullable=True)
    op.alter_column('approval_groups', 'metadata_json',
               existing_type=sa.JSON(),
               type_=postgresql.JSONB(astext_type=sa.Text()),
               existing_nullable=True,
               existing_server_default=sa.text("'{}'::jsonb"))
    add_col_if_not_exists('ai_models', sa.Column('owner_department_id', sa.INTEGER(), autoincrement=False, nullable=True))
    op.drop_constraint(None, 'ai_models', type_='unique')
    op.create_index(op.f('ix_ai_models_id'), 'ai_models', ['id'], unique=False)
    op.alter_column('ai_models', 'id',
               existing_type=sa.UUID(),
               type_=sa.INTEGER(),
               postgresql_using='0',
               existing_nullable=False)
    op.alter_column('ai_models', 'data_source_id',
               existing_type=sa.UUID(),
               type_=sa.INTEGER(),
               postgresql_using='0',
               existing_nullable=True)
    op.alter_column('ai_models', 'version',
               existing_type=sa.VARCHAR(),
               nullable=False)
    op.drop_column('ai_models', 'updated_by')
    op.drop_column('ai_models', 'created_by')
    op.drop_column('ai_models', 'updated_at')
    op.drop_column('ai_models', 'created_at')
    op.drop_column('ai_models', 'tenant_id')
    op.drop_column('ai_models', 'metadata_json')
    op.drop_column('ai_models', 'is_deleted')
    op.drop_column('ai_models', 'version_no')
    op.drop_column('ai_models', 'deployment_environment')
    op.drop_column('ai_models', 'department_id')
    op.drop_column('ai_models', 'owner_user_id')
    op.drop_column('ai_models', 'purpose')
    op.drop_column('ai_models', 'provider_id')
    op.drop_column('ai_models', 'model_code')
    op.drop_constraint(None, 'agents', type_='unique')
    op.create_index(op.f('ix_agents_id'), 'agents', ['id'], unique=False)
    op.alter_column('agents', 'id',
               existing_type=sa.UUID(),
               type_=sa.INTEGER(),
               postgresql_using='0',
               existing_nullable=False)
    op.alter_column('agents', 'ai_model_id',
               existing_type=sa.UUID(),
               type_=sa.INTEGER(),
               postgresql_using='0',
               existing_nullable=True)
    op.alter_column('agents', 'execution_mode',
               existing_type=sa.String(length=80),
               type_=postgresql.ENUM('READ_ONLY', 'RECOMMEND_ONLY', 'APPROVAL_REQUIRED', 'LIMITED_EXECUTION', 'FULLY_BLOCKED', name='executionmode'),
               existing_nullable=False)
    op.alter_column('agents', 'description',
               existing_type=sa.Text(),
               type_=sa.VARCHAR(),
               existing_nullable=True)
    op.drop_column('agents', 'updated_by')
    op.drop_column('agents', 'created_by')
    op.drop_column('agents', 'updated_at')
    op.drop_column('agents', 'created_at')
    op.drop_column('agents', 'tenant_id')
    op.drop_column('agents', 'metadata_json')
    op.drop_column('agents', 'is_deleted')
    op.drop_column('agents', 'version_no')
    op.drop_column('agents', 'capabilities_json')
    op.drop_column('agents', 'status')
    op.drop_column('agents', 'confidence_threshold')
    op.drop_column('agents', 'risk_level')
    op.drop_column('agents', 'department_id')
    op.drop_column('agents', 'owner_user_id')
    op.drop_column('agents', 'agent_type')
    op.drop_column('agents', 'agent_code')
    op.create_table('registry_register_all',
    sa.Column('id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('name', sa.VARCHAR(length=200), autoincrement=False, nullable=False),
    sa.Column('department_id', sa.UUID(), autoincrement=False, nullable=True),
    sa.Column('role_id', sa.UUID(), autoincrement=False, nullable=True),
    sa.Column('user_id', sa.UUID(), autoincrement=False, nullable=True),
    sa.Column('data_source_id', sa.UUID(), autoincrement=False, nullable=True),
    sa.Column('model_id', sa.UUID(), autoincrement=False, nullable=True),
    sa.Column('agent_id', sa.UUID(), autoincrement=False, nullable=True),
    sa.Column('tool_id', sa.UUID(), autoincrement=False, nullable=True),
    sa.Column('workflow_id', sa.UUID(), autoincrement=False, nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
    sa.Column('created_by', sa.UUID(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['agent_id'], ['registry_ai_agents.id'], name=op.f('registry_register_all_agent_id_fkey')),
    sa.ForeignKeyConstraint(['data_source_id'], ['registry_data_sources.id'], name=op.f('registry_register_all_data_source_id_fkey')),
    sa.ForeignKeyConstraint(['department_id'], ['registry_departments.id'], name=op.f('registry_register_all_department_id_fkey')),
    sa.ForeignKeyConstraint(['model_id'], ['registry_ai_models.id'], name=op.f('registry_register_all_model_id_fkey')),
    sa.ForeignKeyConstraint(['role_id'], ['registry_roles.id'], name=op.f('registry_register_all_role_id_fkey')),
    sa.ForeignKeyConstraint(['tool_id'], ['registry_tools.id'], name=op.f('registry_register_all_tool_id_fkey')),
    sa.ForeignKeyConstraint(['user_id'], ['guardian_users.id'], name=op.f('registry_register_all_user_id_fkey')),
    sa.ForeignKeyConstraint(['workflow_id'], ['registry_workflows.id'], name=op.f('registry_register_all_workflow_id_fkey')),
    sa.PrimaryKeyConstraint('id', name=op.f('registry_register_all_pkey'))
    )
    op.create_table('registry_tools',
    sa.Column('id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('tool_code', sa.VARCHAR(length=80), autoincrement=False, nullable=False),
    sa.Column('tool_name', sa.VARCHAR(length=200), autoincrement=False, nullable=False),
    sa.Column('tool_category', sa.VARCHAR(length=80), autoincrement=False, nullable=False),
    sa.Column('access_mode', sa.VARCHAR(length=80), autoincrement=False, nullable=False),
    sa.Column('owner_user_id', sa.UUID(), autoincrement=False, nullable=True),
    sa.Column('sensitivity_level', sa.VARCHAR(length=50), autoincrement=False, nullable=False),
    sa.Column('allowed_operations_json', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=False),
    sa.Column('endpoint_reference', sa.VARCHAR(length=500), autoincrement=False, nullable=True),
    sa.Column('status', sa.VARCHAR(length=30), autoincrement=False, nullable=True),
    sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
    sa.Column('updated_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['owner_user_id'], ['guardian_users.id'], name=op.f('registry_tools_owner_user_id_fkey')),
    sa.PrimaryKeyConstraint('id', name=op.f('registry_tools_pkey')),
    sa.UniqueConstraint('tool_code', name=op.f('registry_tools_tool_code_key'), postgresql_include=[], postgresql_nulls_not_distinct=False)
    )
    op.create_table('registry_data_sources',
    sa.Column('id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('source_code', sa.VARCHAR(length=80), autoincrement=False, nullable=False),
    sa.Column('source_name', sa.VARCHAR(length=200), autoincrement=False, nullable=False),
    sa.Column('source_type', sa.VARCHAR(length=80), autoincrement=False, nullable=False),
    sa.Column('owner_user_id', sa.UUID(), autoincrement=False, nullable=True),
    sa.Column('department_id', sa.UUID(), autoincrement=False, nullable=True),
    sa.Column('classification', sa.VARCHAR(length=80), autoincrement=False, nullable=False),
    sa.Column('sensitivity_level', sa.VARCHAR(length=50), autoincrement=False, nullable=False),
    sa.Column('region', sa.VARCHAR(length=80), autoincrement=False, nullable=True),
    sa.Column('contains_pii', sa.BOOLEAN(), autoincrement=False, nullable=True),
    sa.Column('retention_policy', sa.VARCHAR(length=200), autoincrement=False, nullable=True),
    sa.Column('connection_reference', sa.VARCHAR(length=500), autoincrement=False, nullable=True),
    sa.Column('status', sa.VARCHAR(length=30), autoincrement=False, nullable=True),
    sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
    sa.Column('updated_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
    sa.Column('created_by', sa.UUID(), autoincrement=False, nullable=True),
    sa.Column('updated_by', sa.UUID(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['department_id'], ['registry_departments.id'], name=op.f('registry_data_sources_department_id_fkey')),
    sa.ForeignKeyConstraint(['owner_user_id'], ['guardian_users.id'], name=op.f('registry_data_sources_owner_user_id_fkey')),
    sa.PrimaryKeyConstraint('id', name=op.f('registry_data_sources_pkey')),
    sa.UniqueConstraint('source_code', name=op.f('registry_data_sources_source_code_key'), postgresql_include=[], postgresql_nulls_not_distinct=False)
    )
    op.create_table('registry_ai_model_providers',
    sa.Column('id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('provider_type', sa.VARCHAR(length=80), autoincrement=False, nullable=False),
    sa.Column('provider_name', sa.VARCHAR(length=200), autoincrement=False, nullable=False),
    sa.Column('provider_category', sa.VARCHAR(length=80), autoincrement=False, nullable=True),
    sa.Column('ownership_type', sa.VARCHAR(length=80), autoincrement=False, nullable=True),
    sa.Column('hosting_type', sa.VARCHAR(length=80), autoincrement=False, nullable=True),
    sa.Column('data_residency', sa.VARCHAR(length=80), autoincrement=False, nullable=True),
    sa.Column('risk_classification', sa.VARCHAR(length=50), autoincrement=False, nullable=True),
    sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
    sa.Column('updated_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
    sa.Column('created_by', sa.UUID(), autoincrement=False, nullable=True),
    sa.Column('updated_by', sa.UUID(), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name=op.f('registry_ai_model_providers_pkey'))
    )
    op.create_table('registry_ai_models',
    sa.Column('id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('model_code', sa.VARCHAR(length=80), autoincrement=False, nullable=False),
    sa.Column('model_name', sa.VARCHAR(length=200), autoincrement=False, nullable=False),
    sa.Column('model_type', sa.VARCHAR(length=80), autoincrement=False, nullable=False),
    sa.Column('version', sa.VARCHAR(length=80), autoincrement=False, nullable=True),
    sa.Column('purpose', sa.TEXT(), autoincrement=False, nullable=False),
    sa.Column('owner_user_id', sa.UUID(), autoincrement=False, nullable=True),
    sa.Column('department_id', sa.UUID(), autoincrement=False, nullable=True),
    sa.Column('risk_level', sa.VARCHAR(length=50), autoincrement=False, nullable=False),
    sa.Column('deployment_environment', sa.VARCHAR(length=50), autoincrement=False, nullable=True),
    sa.Column('status', sa.VARCHAR(length=30), autoincrement=False, nullable=True),
    sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
    sa.Column('updated_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
    sa.Column('created_by', sa.UUID(), autoincrement=False, nullable=True),
    sa.Column('updated_by', sa.UUID(), autoincrement=False, nullable=True),
    sa.Column('provider_id', sa.UUID(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['department_id'], ['registry_departments.id'], name=op.f('registry_ai_models_department_id_fkey')),
    sa.ForeignKeyConstraint(['owner_user_id'], ['guardian_users.id'], name=op.f('registry_ai_models_owner_user_id_fkey')),
    sa.ForeignKeyConstraint(['provider_id'], ['registry_ai_model_providers.id'], name=op.f('registry_ai_models_provider_id_fkey')),
    sa.PrimaryKeyConstraint('id', name=op.f('registry_ai_models_pkey')),
    sa.UniqueConstraint('model_code', name=op.f('registry_ai_models_model_code_key'), postgresql_include=[], postgresql_nulls_not_distinct=False)
    )
    op.create_table('registry_departments',
    sa.Column('id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('department_code', sa.VARCHAR(length=50), autoincrement=False, nullable=False),
    sa.Column('department_name', sa.VARCHAR(length=150), autoincrement=False, nullable=False),
    sa.Column('parent_department_id', sa.UUID(), autoincrement=False, nullable=True),
    sa.Column('business_owner_user_id', sa.UUID(), autoincrement=False, nullable=True),
    sa.Column('escalation_owner_user_id', sa.UUID(), autoincrement=False, nullable=True),
    sa.Column('status', sa.VARCHAR(length=30), autoincrement=False, nullable=True),
    sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
    sa.Column('updated_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
    sa.Column('created_by', sa.UUID(), autoincrement=False, nullable=True),
    sa.Column('updated_by', sa.UUID(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['business_owner_user_id'], ['guardian_users.id'], name=op.f('fk_reg_dept_biz_owner')),
    sa.ForeignKeyConstraint(['escalation_owner_user_id'], ['guardian_users.id'], name=op.f('fk_reg_dept_esc_owner')),
    sa.ForeignKeyConstraint(['parent_department_id'], ['registry_departments.id'], name=op.f('registry_departments_parent_department_id_fkey')),
    sa.PrimaryKeyConstraint('id', name=op.f('registry_departments_pkey')),
    sa.UniqueConstraint('department_code', name=op.f('registry_departments_department_code_key'), postgresql_include=[], postgresql_nulls_not_distinct=False)
    )
    op.create_table('registry_ai_agents',
    sa.Column('id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('agent_code', sa.VARCHAR(length=80), autoincrement=False, nullable=False),
    sa.Column('agent_name', sa.VARCHAR(length=200), autoincrement=False, nullable=False),
    sa.Column('agent_type', sa.VARCHAR(length=80), autoincrement=False, nullable=False),
    sa.Column('description', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('owner_user_id', sa.UUID(), autoincrement=False, nullable=True),
    sa.Column('department_id', sa.UUID(), autoincrement=False, nullable=True),
    sa.Column('execution_mode', sa.VARCHAR(length=80), autoincrement=False, nullable=False),
    sa.Column('risk_level', sa.VARCHAR(length=50), autoincrement=False, nullable=False),
    sa.Column('confidence_threshold', sa.NUMERIC(precision=5, scale=2), autoincrement=False, nullable=True),
    sa.Column('status', sa.VARCHAR(length=30), autoincrement=False, nullable=True),
    sa.Column('capabilities_json', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=True),
    sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
    sa.Column('updated_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
    sa.Column('created_by', sa.UUID(), autoincrement=False, nullable=True),
    sa.Column('updated_by', sa.UUID(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['department_id'], ['registry_departments.id'], name=op.f('registry_ai_agents_department_id_fkey')),
    sa.ForeignKeyConstraint(['owner_user_id'], ['guardian_users.id'], name=op.f('registry_ai_agents_owner_user_id_fkey')),
    sa.PrimaryKeyConstraint('id', name=op.f('registry_ai_agents_pkey')),
    sa.UniqueConstraint('agent_code', name=op.f('registry_ai_agents_agent_code_key'), postgresql_include=[], postgresql_nulls_not_distinct=False)
    )
    op.create_table('guardian_users',
    sa.Column('id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('email', sa.VARCHAR(length=255), autoincrement=False, nullable=False),
    sa.Column('full_name', sa.VARCHAR(length=200), autoincrement=False, nullable=False),
    sa.Column('department_id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('role_id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('approval_limit_level', sa.VARCHAR(length=50), autoincrement=False, nullable=True),
    sa.Column('status', sa.VARCHAR(length=30), autoincrement=False, nullable=True),
    sa.Column('last_login_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
    sa.Column('updated_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['department_id'], ['registry_departments.id'], name=op.f('guardian_users_department_id_fkey')),
    sa.ForeignKeyConstraint(['role_id'], ['registry_roles.id'], name=op.f('guardian_users_role_id_fkey')),
    sa.PrimaryKeyConstraint('id', name=op.f('guardian_users_pkey')),
    sa.UniqueConstraint('email', name=op.f('guardian_users_email_key'), postgresql_include=[], postgresql_nulls_not_distinct=False)
    )
    op.create_table('registry_roles',
    sa.Column('id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('role_code', sa.VARCHAR(length=50), autoincrement=False, nullable=False),
    sa.Column('role_name', sa.VARCHAR(length=150), autoincrement=False, nullable=False),
    sa.Column('role_type', sa.VARCHAR(length=50), autoincrement=False, nullable=False),
    sa.Column('permissions_json', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=False),
    sa.Column('status', sa.VARCHAR(length=30), autoincrement=False, nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
    sa.Column('updated_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('registry_roles_pkey')),
    sa.UniqueConstraint('role_code', name=op.f('registry_roles_role_code_key'), postgresql_include=[], postgresql_nulls_not_distinct=False)
    )
    op.create_table('registry_workflows',
    sa.Column('id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('workflow_code', sa.VARCHAR(length=80), autoincrement=False, nullable=False),
    sa.Column('workflow_name', sa.VARCHAR(length=200), autoincrement=False, nullable=False),
    sa.Column('workflow_type', sa.VARCHAR(length=80), autoincrement=False, nullable=False),
    sa.Column('department_id', sa.UUID(), autoincrement=False, nullable=True),
    sa.Column('owner_user_id', sa.UUID(), autoincrement=False, nullable=True),
    sa.Column('description', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('approval_required', sa.BOOLEAN(), autoincrement=False, nullable=True),
    sa.Column('business_criticality', sa.VARCHAR(length=50), autoincrement=False, nullable=False),
    sa.Column('status', sa.VARCHAR(length=30), autoincrement=False, nullable=True),
    sa.Column('steps_json', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=True),
    sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
    sa.Column('updated_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
    sa.Column('approver_user_id', sa.UUID(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['approver_user_id'], ['guardian_users.id'], name=op.f('registry_workflows_approver_user_id_fkey')),
    sa.ForeignKeyConstraint(['department_id'], ['registry_departments.id'], name=op.f('registry_workflows_department_id_fkey')),
    sa.ForeignKeyConstraint(['owner_user_id'], ['guardian_users.id'], name=op.f('registry_workflows_owner_user_id_fkey')),
    sa.PrimaryKeyConstraint('id', name=op.f('registry_workflows_pkey')),
    sa.UniqueConstraint('workflow_code', name=op.f('registry_workflows_workflow_code_key'), postgresql_include=[], postgresql_nulls_not_distinct=False)
    )
    op.create_table('registry_audit_events',
    sa.Column('id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('entity_type', sa.VARCHAR(length=80), autoincrement=False, nullable=False),
    sa.Column('entity_id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('event_type', sa.VARCHAR(length=80), autoincrement=False, nullable=False),
    sa.Column('changed_by', sa.UUID(), autoincrement=False, nullable=True),
    sa.Column('change_summary', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('before_json', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=True),
    sa.Column('after_json', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('registry_audit_events_pkey'))
    )
    op.create_table('registry_relationships',
    sa.Column('id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('source_entity_type', sa.VARCHAR(length=80), autoincrement=False, nullable=False),
    sa.Column('source_entity_id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('relationship_type', sa.VARCHAR(length=80), autoincrement=False, nullable=False),
    sa.Column('target_entity_type', sa.VARCHAR(length=80), autoincrement=False, nullable=False),
    sa.Column('target_entity_id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('status', sa.VARCHAR(length=30), autoincrement=False, nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
    sa.Column('created_by', sa.UUID(), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name=op.f('registry_relationships_pkey'))
    )
    # [Safe Migrations] Skipped FK to dropped table registry_workflows: op.create_foreign_key(op.f('workflow_schedules_workflow_id_fkey'), 'workflow_schedules', 'registry_workflows', ['workflow_id'], ['id'])
    # [Safe Migrations] Skipped FK to dropped table guardian_users: op.create_foreign_key(op.f('workflow_schedules_tenant_id_fkey'), 'workflow_schedules', 'guardian_users', ['tenant_id'], ['id'])
    # [Safe Migrations] Skipped FK to dropped table guardian_users: op.create_foreign_key(op.f('workflow_schedules_owner_user_id_fkey'), 'workflow_schedules', 'guardian_users', ['owner_user_id'], ['id'])
    # [Safe Migrations] Skipped FK to dropped table registry_departments: op.create_foreign_key(op.f('workflow_schedules_owner_department_id_fkey'), 'workflow_schedules', 'registry_departments', ['owner_department_id'], ['id'])
    # [Safe Migrations] Skipped FK to dropped table guardian_users: op.create_foreign_key(op.f('workflow_schedules_updated_by_fkey'), 'workflow_schedules', 'guardian_users', ['updated_by'], ['id'])
    # [Safe Migrations] Skipped FK to dropped table guardian_users: op.create_foreign_key(op.f('workflow_schedules_created_by_fkey'), 'workflow_schedules', 'guardian_users', ['created_by'], ['id'])
    # [Safe Migrations] Skipped FK to dropped table guardian_users: op.create_foreign_key(op.f('workflow_schedule_history_changed_by_fkey'), 'workflow_schedule_history', 'guardian_users', ['changed_by'], ['id'])
    # [Safe Migrations] Skipped FK to dropped table guardian_users: op.create_foreign_key(op.f('workflow_schedule_history_updated_by_fkey'), 'workflow_schedule_history', 'guardian_users', ['updated_by'], ['id'])
    # [Safe Migrations] Skipped FK to dropped table guardian_users: op.create_foreign_key(op.f('workflow_schedule_history_tenant_id_fkey'), 'workflow_schedule_history', 'guardian_users', ['tenant_id'], ['id'])
    # [Safe Migrations] Skipped FK to dropped table guardian_users: op.create_foreign_key(op.f('workflow_schedule_history_created_by_fkey'), 'workflow_schedule_history', 'guardian_users', ['created_by'], ['id'])
    # [Safe Migrations] Skipped FK to dropped table guardian_users: op.create_foreign_key(op.f('workflow_schedule_approvals_updated_by_fkey'), 'workflow_schedule_approvals', 'guardian_users', ['updated_by'], ['id'])
    # [Safe Migrations] Skipped FK to dropped table guardian_users: op.create_foreign_key(op.f('workflow_schedule_approvals_approver_user_id_fkey'), 'workflow_schedule_approvals', 'guardian_users', ['approver_user_id'], ['id'])
    # [Safe Migrations] Skipped FK to dropped table guardian_users: op.create_foreign_key(op.f('workflow_schedule_approvals_created_by_fkey'), 'workflow_schedule_approvals', 'guardian_users', ['created_by'], ['id'])
    # [Safe Migrations] Skipped FK to dropped table guardian_users: op.create_foreign_key(op.f('workflow_schedule_approvals_tenant_id_fkey'), 'workflow_schedule_approvals', 'guardian_users', ['tenant_id'], ['id'])
    # [Safe Migrations] Skipped FK to dropped table guardian_users: op.create_foreign_key(op.f('workflow_schedule_approvals_submitted_by_fkey'), 'workflow_schedule_approvals', 'guardian_users', ['submitted_by'], ['id'])
    # [Safe Migrations] Skipped FK to dropped table guardian_users: op.create_foreign_key(op.f('workflow_schedule_agent_assignments_created_by_fkey'), 'workflow_schedule_agent_assignments', 'guardian_users', ['created_by'], ['id'])
    # [Safe Migrations] Skipped FK to dropped table guardian_users: op.create_foreign_key(op.f('workflow_schedule_agent_assignments_updated_by_fkey'), 'workflow_schedule_agent_assignments', 'guardian_users', ['updated_by'], ['id'])
    # [Safe Migrations] Skipped FK to dropped table guardian_users: op.create_foreign_key(op.f('workflow_schedule_agent_assignments_tenant_id_fkey'), 'workflow_schedule_agent_assignments', 'guardian_users', ['tenant_id'], ['id'])
    # [Safe Migrations] Skipped FK to dropped table registry_ai_models: op.create_foreign_key(op.f('workflow_schedule_agent_assignments_model_id_fkey'), 'workflow_schedule_agent_assignments', 'registry_ai_models', ['model_id'], ['id'])
    # [Safe Migrations] Skipped FK to dropped table registry_ai_agents: op.create_foreign_key(op.f('workflow_schedule_agent_assignments_agent_id_fkey'), 'workflow_schedule_agent_assignments', 'registry_ai_agents', ['agent_id'], ['id'])
    # [Safe Migrations] Skipped FK to dropped table guardian_users: op.create_foreign_key(op.f('workflow_runs_updated_by_fkey'), 'workflow_runs', 'guardian_users', ['updated_by'], ['id'])
    # [Safe Migrations] Skipped FK to dropped table guardian_users: op.create_foreign_key(op.f('workflow_runs_tenant_id_fkey'), 'workflow_runs', 'guardian_users', ['tenant_id'], ['id'])
    # [Safe Migrations] Skipped FK to dropped table guardian_users: op.create_foreign_key(op.f('workflow_runs_triggered_by_user_id_fkey'), 'workflow_runs', 'guardian_users', ['triggered_by_user_id'], ['id'])
    # [Safe Migrations] Skipped FK to dropped table guardian_users: op.create_foreign_key(op.f('workflow_runs_created_by_fkey'), 'workflow_runs', 'guardian_users', ['created_by'], ['id'])
    # [Safe Migrations] Skipped FK to dropped table registry_workflows: op.create_foreign_key(op.f('workflow_runs_workflow_id_fkey'), 'workflow_runs', 'registry_workflows', ['workflow_id'], ['id'])
    # [Safe Migrations] Skipped FK to dropped table guardian_users: op.create_foreign_key(op.f('workflow_run_steps_updated_by_fkey'), 'workflow_run_steps', 'guardian_users', ['updated_by'], ['id'])
    # [Safe Migrations] Skipped FK to dropped table guardian_users: op.create_foreign_key(op.f('workflow_run_steps_tenant_id_fkey'), 'workflow_run_steps', 'guardian_users', ['tenant_id'], ['id'])
    # [Safe Migrations] Skipped FK to dropped table guardian_users: op.create_foreign_key(op.f('workflow_run_steps_created_by_fkey'), 'workflow_run_steps', 'guardian_users', ['created_by'], ['id'])
    # [Safe Migrations] Skipped FK to dropped table guardian_users: op.create_foreign_key(op.f('workflow_run_outputs_tenant_id_fkey'), 'workflow_run_outputs', 'guardian_users', ['tenant_id'], ['id'])
    # [Safe Migrations] Skipped FK to dropped table guardian_users: op.create_foreign_key(op.f('workflow_run_outputs_created_by_fkey'), 'workflow_run_outputs', 'guardian_users', ['created_by'], ['id'])
    # [Safe Migrations] Skipped FK to dropped table guardian_users: op.create_foreign_key(op.f('workflow_run_outputs_updated_by_fkey'), 'workflow_run_outputs', 'guardian_users', ['updated_by'], ['id'])
    # [Safe Migrations] Skipped FK to dropped table guardian_users: op.create_foreign_key(op.f('workflow_run_failures_tenant_id_fkey'), 'workflow_run_failures', 'guardian_users', ['tenant_id'], ['id'])
    # [Safe Migrations] Skipped FK to dropped table guardian_users: op.create_foreign_key(op.f('workflow_run_failures_created_by_fkey'), 'workflow_run_failures', 'guardian_users', ['created_by'], ['id'])
    # [Safe Migrations] Skipped FK to dropped table guardian_users: op.create_foreign_key(op.f('workflow_run_failures_updated_by_fkey'), 'workflow_run_failures', 'guardian_users', ['updated_by'], ['id'])
    # [Safe Migrations] Skipped FK to dropped table guardian_users: op.create_foreign_key(op.f('workflow_notifications_created_by_fkey'), 'workflow_notifications', 'guardian_users', ['created_by'], ['id'])
    # [Safe Migrations] Skipped FK to dropped table guardian_users: op.create_foreign_key(op.f('workflow_notifications_tenant_id_fkey'), 'workflow_notifications', 'guardian_users', ['tenant_id'], ['id'])
    # [Safe Migrations] Skipped FK to dropped table guardian_users: op.create_foreign_key(op.f('workflow_notifications_recipient_user_id_fkey'), 'workflow_notifications', 'guardian_users', ['recipient_user_id'], ['id'])
    # [Safe Migrations] Skipped FK to dropped table guardian_users: op.create_foreign_key(op.f('workflow_notifications_updated_by_fkey'), 'workflow_notifications', 'guardian_users', ['updated_by'], ['id'])
    # [Safe Migrations] Skipped FK to dropped table guardian_users: op.create_foreign_key(op.f('workflow_delegations_updated_by_fkey'), 'workflow_delegations', 'guardian_users', ['updated_by'], ['id'])
    # [Safe Migrations] Skipped FK to dropped table guardian_users: op.create_foreign_key(op.f('workflow_delegations_delegator_user_id_fkey'), 'workflow_delegations', 'guardian_users', ['delegator_user_id'], ['id'])
    # [Safe Migrations] Skipped FK to dropped table guardian_users: op.create_foreign_key(op.f('workflow_delegations_created_by_fkey'), 'workflow_delegations', 'guardian_users', ['created_by'], ['id'])
    # [Safe Migrations] Skipped FK to dropped table guardian_users: op.create_foreign_key(op.f('workflow_delegations_tenant_id_fkey'), 'workflow_delegations', 'guardian_users', ['tenant_id'], ['id'])
    # [Safe Migrations] Skipped FK to dropped table guardian_users: op.create_foreign_key(op.f('workflow_delegations_delegatee_user_id_fkey'), 'workflow_delegations', 'guardian_users', ['delegatee_user_id'], ['id'])
    # [Safe Migrations] Skipped FK to dropped table registry_ai_agents: op.create_foreign_key(op.f('workflow_authorization_decisions_subject_agent_id_fkey'), 'workflow_authorization_decisions', 'registry_ai_agents', ['subject_agent_id'], ['id'])
    # [Safe Migrations] Skipped FK to dropped table guardian_users: op.create_foreign_key(op.f('workflow_authorization_decisions_tenant_id_fkey'), 'workflow_authorization_decisions', 'guardian_users', ['tenant_id'], ['id'])
    # [Safe Migrations] Skipped FK to dropped table guardian_users: op.create_foreign_key(op.f('workflow_authorization_decisions_subject_user_id_fkey'), 'workflow_authorization_decisions', 'guardian_users', ['subject_user_id'], ['id'])
    # [Safe Migrations] Skipped FK to dropped table guardian_users: op.create_foreign_key(op.f('workflow_authorization_decisions_created_by_fkey'), 'workflow_authorization_decisions', 'guardian_users', ['created_by'], ['id'])
    # [Safe Migrations] Skipped FK to dropped table guardian_users: op.create_foreign_key(op.f('workflow_authorization_decisions_updated_by_fkey'), 'workflow_authorization_decisions', 'guardian_users', ['updated_by'], ['id'])
    # [Safe Migrations] Skipped FK to dropped table registry_workflows: op.create_foreign_key(op.f('orchestration_workflow_schedules_workflow_id_fkey'), 'orchestration_workflow_schedules', 'registry_workflows', ['workflow_id'], ['id'])
    # [Safe Migrations] Skipped FK to dropped table registry_workflows: op.create_foreign_key(op.f('orchestration_workflow_executions_workflow_id_fkey'), 'orchestration_workflow_executions', 'registry_workflows', ['workflow_id'], ['id'])
    op.execute('''
    DO $$
    DECLARE r RECORD;
    BEGIN
        FOR r IN (
            SELECT constraint_name
            FROM information_schema.key_column_usage
            WHERE table_name = 'data_sources' AND column_name = 'owner_department_id'
        ) LOOP
            EXECUTE 'ALTER TABLE data_sources DROP CONSTRAINT IF EXISTS ' || r.constraint_name || ' CASCADE';
        END LOOP;
    END $$;
    ''')
    op.create_foreign_key(op.f('data_sources_owner_department_id_fkey'), 'data_sources', 'departments', ['owner_department_id'], ['id'])
    # [Safe Migrations] Skipped FK to dropped table guardian_users: op.create_foreign_key(op.f('approval_groups_created_by_fkey'), 'approval_groups', 'guardian_users', ['created_by'], ['id'])
    # [Safe Migrations] Skipped FK to dropped table guardian_users: op.create_foreign_key(op.f('approval_groups_updated_by_fkey'), 'approval_groups', 'guardian_users', ['updated_by'], ['id'])
    # [Safe Migrations] Skipped FK to dropped table guardian_users: op.create_foreign_key(op.f('approval_groups_tenant_id_fkey'), 'approval_groups', 'guardian_users', ['tenant_id'], ['id'])
    # [Safe Migrations] Skipped FK to dropped table guardian_users: op.create_foreign_key(op.f('approval_group_members_user_id_fkey'), 'approval_group_members', 'guardian_users', ['user_id'], ['id'], ondelete='CASCADE')
    op.execute('''
    DO $$
    DECLARE r RECORD;
    BEGIN
        FOR r IN (
            SELECT constraint_name
            FROM information_schema.key_column_usage
            WHERE table_name = 'ai_models' AND column_name = 'owner_department_id'
        ) LOOP
            EXECUTE 'ALTER TABLE ai_models DROP CONSTRAINT IF EXISTS ' || r.constraint_name || ' CASCADE';
        END LOOP;
    END $$;
    ''')
    op.create_foreign_key(op.f('ai_models_owner_department_id_fkey'), 'ai_models', 'departments', ['owner_department_id'], ['id'])
    op.execute('''
    DO $$
    DECLARE r RECORD;
    BEGIN
        FOR r IN (
            SELECT constraint_name
            FROM information_schema.key_column_usage
            WHERE table_name = 'agents' AND column_name = 'ai_model_id'
        ) LOOP
            EXECUTE 'ALTER TABLE agents DROP CONSTRAINT IF EXISTS ' || r.constraint_name || ' CASCADE';
        END LOOP;
    END $$;
    ''')
    op.create_foreign_key('agents_ai_model_id_fkey', 'agents', 'ai_models', ['ai_model_id'], ['id'])
    op.execute('''
    DO $$
    DECLARE r RECORD;
    BEGIN
        FOR r IN (
            SELECT constraint_name
            FROM information_schema.key_column_usage
            WHERE table_name = 'departments' AND column_name = 'owner_user_id'
        ) LOOP
            EXECUTE 'ALTER TABLE departments DROP CONSTRAINT IF EXISTS ' || r.constraint_name || ' CASCADE';
        END LOOP;
    END $$;
    ''')
    op.create_foreign_key('departments_owner_user_id_fkey', 'departments', 'users', ['owner_user_id'], ['id'])
    op.execute('''
    DO $$
    DECLARE r RECORD;
    BEGIN
        FOR r IN (
            SELECT constraint_name
            FROM information_schema.key_column_usage
            WHERE table_name = 'ai_models' AND column_name = 'data_source_id'
        ) LOOP
            EXECUTE 'ALTER TABLE ai_models DROP CONSTRAINT IF EXISTS ' || r.constraint_name || ' CASCADE';
        END LOOP;
    END $$;
    ''')
    op.create_foreign_key('ai_models_data_source_id_fkey', 'ai_models', 'data_sources', ['data_source_id'], ['id'])
    op.execute('''
    DO $$
    DECLARE r RECORD;
    BEGIN
        FOR r IN (
            SELECT constraint_name
            FROM information_schema.key_column_usage
            WHERE table_name = 'user_roles' AND column_name = 'user_id'
        ) LOOP
            EXECUTE 'ALTER TABLE user_roles DROP CONSTRAINT IF EXISTS ' || r.constraint_name || ' CASCADE';
        END LOOP;
    END $$;
    ''')
    op.create_foreign_key('user_roles_user_id_fkey', 'user_roles', 'users', ['user_id'], ['id'])
    op.execute('''
    DO $$
    DECLARE r RECORD;
    BEGIN
        FOR r IN (
            SELECT constraint_name
            FROM information_schema.key_column_usage
            WHERE table_name = 'policies' AND column_name = 'created_by'
        ) LOOP
            EXECUTE 'ALTER TABLE policies DROP CONSTRAINT IF EXISTS ' || r.constraint_name || ' CASCADE';
        END LOOP;
    END $$;
    ''')
    op.create_foreign_key('policies_created_by_fkey', 'policies', 'users', ['created_by'], ['id'])
    op.execute('''
    DO $$
    DECLARE r RECORD;
    BEGIN
        FOR r IN (
            SELECT constraint_name
            FROM information_schema.key_column_usage
            WHERE table_name = 'user_roles' AND column_name = 'role_id'
        ) LOOP
            EXECUTE 'ALTER TABLE user_roles DROP CONSTRAINT IF EXISTS ' || r.constraint_name || ' CASCADE';
        END LOOP;
    END $$;
    ''')
    op.create_foreign_key('user_roles_role_id_fkey', 'user_roles', 'roles', ['role_id'], ['id'])
    op.execute('''
    DO $$
    DECLARE r RECORD;
    BEGIN
        FOR r IN (
            SELECT constraint_name
            FROM information_schema.key_column_usage
            WHERE table_name = 'role_permissions' AND column_name = 'role_id'
        ) LOOP
            EXECUTE 'ALTER TABLE role_permissions DROP CONSTRAINT IF EXISTS ' || r.constraint_name || ' CASCADE';
        END LOOP;
    END $$;
    ''')
    op.create_foreign_key('role_permissions_role_id_fkey', 'role_permissions', 'roles', ['role_id'], ['id'])
    op.execute('''
    DO $$
    DECLARE r RECORD;
    BEGIN
        FOR r IN (
            SELECT constraint_name
            FROM information_schema.key_column_usage
            WHERE table_name = 'recommendations' AND column_name = 'agent_id'
        ) LOOP
            EXECUTE 'ALTER TABLE recommendations DROP CONSTRAINT IF EXISTS ' || r.constraint_name || ' CASCADE';
        END LOOP;
    END $$;
    ''')
    op.create_foreign_key('recommendations_agent_id_fkey', 'recommendations', 'agents', ['agent_id'], ['id'])
    op.execute('''
    DO $$
    DECLARE r RECORD;
    BEGIN
        FOR r IN (
            SELECT constraint_name
            FROM information_schema.key_column_usage
            WHERE table_name = 'recommendations' AND column_name = 'policy_id'
        ) LOOP
            EXECUTE 'ALTER TABLE recommendations DROP CONSTRAINT IF EXISTS ' || r.constraint_name || ' CASCADE';
        END LOOP;
    END $$;
    ''')
    op.create_foreign_key('recommendations_policy_id_fkey', 'recommendations', 'policies', ['policy_id'], ['id'])
    # ### end Alembic commands ###

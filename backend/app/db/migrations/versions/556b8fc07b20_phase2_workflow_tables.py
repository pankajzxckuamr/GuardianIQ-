"""phase2_workflow_tables

Revision ID: 556b8fc07b20
Revises: 5e5a3f6c270e
Create Date: 2026-06-19 11:34:44.958821

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision: str = '556b8fc07b20'
down_revision: Union[str, Sequence[str], None] = '5e5a3f6c270e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def get_standard_columns():
    """Helper to return new standard columns for each table to avoid sharing column instances."""
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


def get_or_create_role(conn, role_code: str, role_name: str = None, description: str = None):
    if role_name is None:
        role_name = role_code.replace('_', ' ').title()
    if description is None:
        description = f"{role_name} Role"
    
    res = conn.execute(
        sa.text("SELECT id FROM roles WHERE role_code = :code"),
        {"code": role_code}
    ).fetchone()
    if res:
        return res[0]
    
    conn.execute(
        sa.text("INSERT INTO roles (role_code, role_name, description) VALUES (:code, :name, :desc)"),
        {"code": role_code, "name": role_name, "desc": description}
    )
    res = conn.execute(
        sa.text("SELECT id FROM roles WHERE role_code = :code"),
        {"code": role_code}
    ).fetchone()
    return res[0]


def get_or_create_permission(conn, permission_code: str, description: str = None):
    if description is None:
        description = permission_code.replace('_', ' ').title()
    
    res = conn.execute(
        sa.text("SELECT id FROM permissions WHERE permission_code = :code"),
        {"code": permission_code}
    ).fetchone()
    if res:
        return res[0]
    
    conn.execute(
        sa.text("INSERT INTO permissions (permission_code, description) VALUES (:code, :desc)"),
        {"code": permission_code, "desc": description}
    )
    res = conn.execute(
        sa.text("SELECT id FROM permissions WHERE permission_code = :code"),
        {"code": permission_code}
    ).fetchone()
    return res[0]


def map_role_to_permission(conn, role_id, permission_id):
    res = conn.execute(
        sa.text("SELECT 1 FROM role_permissions WHERE role_id = :r_id AND permission_id = :p_id"),
        {"r_id": role_id, "p_id": permission_id}
    ).fetchone()
    if not res:
        conn.execute(
            sa.text("INSERT INTO role_permissions (role_id, permission_id) VALUES (:r_id, :p_id)"),
            {"r_id": role_id, "p_id": permission_id}
        )


def upgrade() -> None:
    """Upgrade schema."""
    # Ensure pgcrypto extension is installed for gen_random_uuid()
    op.execute(sa.text('CREATE EXTENSION IF NOT EXISTS "pgcrypto"'))

    # 1. Create approval_groups table (Option A)
    op.create_table(
        'approval_groups',
        *(get_standard_columns() + [
            sa.Column('name', sa.String(length=255), nullable=False)
        ])
    )

    # 2. Create workflow_schedules table
    op.create_table(
        'workflow_schedules',
        *(get_standard_columns() + [
            sa.Column('workflow_id', sa.UUID(), sa.ForeignKey('registry_workflows.id'), nullable=False),
            sa.Column('schedule_code', sa.String(length=100), nullable=False),
            sa.Column('schedule_name', sa.String(length=255), nullable=False),
            sa.Column('schedule_type', sa.String(length=50), nullable=False),
            sa.Column('cron_expression', sa.String(length=120), nullable=True),
            sa.Column('timezone', sa.String(length=100), server_default='Asia/Kolkata', nullable=False),
            sa.Column('start_at', sa.TIMESTAMP(timezone=True), nullable=True),
            sa.Column('end_at', sa.TIMESTAMP(timezone=True), nullable=True),
            sa.Column('next_run_at', sa.TIMESTAMP(timezone=True), nullable=True),
            sa.Column('last_run_at', sa.TIMESTAMP(timezone=True), nullable=True),
            sa.Column('concurrency_policy', sa.String(length=50), server_default='SKIP_IF_RUNNING', nullable=True),
            sa.Column('max_runtime_seconds', sa.Integer(), server_default='1800', nullable=True),
            sa.Column('retry_policy_json', JSONB(astext_type=sa.Text()), server_default='{"max_retries":1,"retry_delay_seconds":300}', nullable=True),
            sa.Column('owner_user_id', sa.UUID(), sa.ForeignKey('guardian_users.id'), nullable=False),
            sa.Column('owner_department_id', sa.UUID(), sa.ForeignKey('registry_departments.id'), nullable=True),
            sa.Column('approval_required', sa.Boolean(), server_default='FALSE', nullable=True),
            sa.Column('approval_group_id', sa.UUID(), sa.ForeignKey('approval_groups.id'), nullable=True),
            sa.Column('risk_level', sa.String(length=50), server_default='MEDIUM', nullable=True),
            sa.Column('schedule_status', sa.String(length=50), server_default='DRAFT', nullable=True),
            sa.UniqueConstraint('tenant_id', 'schedule_code', name='uq_workflow_schedules_tenant_code'),
            sa.CheckConstraint('end_at > start_at', name='chk_workflow_schedules_end_after_start')
        ])
    )

    op.create_index('ix_workflow_schedules_tenant_id', 'workflow_schedules', ['tenant_id'])
    op.create_index('ix_workflow_schedules_workflow_id', 'workflow_schedules', ['workflow_id'])
    op.create_index('ix_workflow_schedules_schedule_status', 'workflow_schedules', ['schedule_status'])
    op.create_index('ix_workflow_schedules_next_run_at', 'workflow_schedules', ['next_run_at'])
    op.create_index('ix_workflow_schedules_owner_user_id', 'workflow_schedules', ['owner_user_id'])
    op.create_index('ix_workflow_schedules_metadata_json', 'workflow_schedules', ['metadata_json'], postgresql_using='gin')

    # 3. Create workflow_schedule_agent_assignments table
    op.create_table(
        'workflow_schedule_agent_assignments',
        *(get_standard_columns() + [
            sa.Column('schedule_id', sa.UUID(), sa.ForeignKey('workflow_schedules.id', ondelete='CASCADE'), nullable=False),
            sa.Column('agent_id', sa.UUID(), sa.ForeignKey('registry_ai_agents.id'), nullable=False),
            sa.Column('model_id', sa.UUID(), sa.ForeignKey('registry_ai_models.id'), nullable=True),
            sa.Column('assignment_role', sa.String(length=50), server_default='PRIMARY', nullable=True),
            sa.Column('execution_mode', sa.String(length=50), server_default='RECOMMEND_ONLY', nullable=True),
            sa.Column('confidence_threshold', sa.Numeric(precision=5, scale=2), nullable=True),
            sa.Column('allowed_tools_json', JSONB(astext_type=sa.Text()), server_default='[]', nullable=True),
            sa.Column('allowed_data_sources_json', JSONB(astext_type=sa.Text()), server_default='[]', nullable=True),
            sa.Column('blocked_operations_json', JSONB(astext_type=sa.Text()), server_default='[]', nullable=True),
            sa.Column('boundary_rules_json', JSONB(astext_type=sa.Text()), server_default='{}', nullable=True),
            sa.Column('status', sa.String(length=50), server_default='ACTIVE', nullable=True),
            sa.UniqueConstraint('tenant_id', 'schedule_id', 'agent_id', 'assignment_role', name='uq_wf_sch_agent_assg_tenant_sch_agent_role'),
            sa.CheckConstraint('confidence_threshold >= 0 AND confidence_threshold <= 100', name='chk_workflow_schedule_agent_assignments_conf')
        ])
    )

    # 4. Create workflow_runs table
    op.create_table(
        'workflow_runs',
        *(get_standard_columns() + [
            sa.Column('schedule_id', sa.UUID(), sa.ForeignKey('workflow_schedules.id'), nullable=False),
            sa.Column('workflow_id', sa.UUID(), sa.ForeignKey('registry_workflows.id'), nullable=False),
            sa.Column('run_code', sa.String(length=120), nullable=False),
            sa.Column('trigger_type', sa.String(length=50), nullable=False),
            sa.Column('triggered_by_user_id', sa.UUID(), sa.ForeignKey('guardian_users.id'), nullable=True),
            sa.Column('triggered_by_actor_type', sa.String(length=50), server_default='SYSTEM', nullable=True),
            sa.Column('run_status', sa.String(length=50), server_default='QUEUED', nullable=True),
            sa.Column('started_at', sa.TIMESTAMP(timezone=True), nullable=True),
            sa.Column('completed_at', sa.TIMESTAMP(timezone=True), nullable=True),
            sa.Column('duration_ms', sa.BigInteger(), nullable=True),
            sa.Column('risk_level', sa.String(length=50), nullable=True),
            sa.Column('summary', sa.Text(), nullable=True),
            sa.Column('context_json', JSONB(astext_type=sa.Text()), server_default='{}', nullable=True),
            sa.Column('result_json', JSONB(astext_type=sa.Text()), server_default='{}', nullable=True),
            sa.UniqueConstraint('tenant_id', 'run_code', name='uq_workflow_runs_tenant_run_code')
        ])
    )

    op.create_index('ix_workflow_runs_schedule_id', 'workflow_runs', ['schedule_id'])
    op.create_index('ix_workflow_runs_run_status', 'workflow_runs', ['run_status'])
    op.create_index('ix_workflow_runs_created_at_desc', 'workflow_runs', [sa.text('created_at DESC')])
    op.create_index('ix_workflow_runs_result_json', 'workflow_runs', ['result_json'], postgresql_using='gin')

    # 5. Create workflow_run_steps table
    op.create_table(
        'workflow_run_steps',
        *(get_standard_columns() + [
            sa.Column('run_id', sa.UUID(), sa.ForeignKey('workflow_runs.id', ondelete='CASCADE'), nullable=False),
            sa.Column('step_code', sa.String(length=100), nullable=False),
            sa.Column('step_order', sa.Integer(), nullable=False),
            sa.Column('step_type', sa.String(length=100), nullable=True),
            sa.Column('step_status', sa.String(length=50), server_default='PENDING', nullable=True),
            sa.Column('started_at', sa.TIMESTAMP(timezone=True), nullable=True),
            sa.Column('completed_at', sa.TIMESTAMP(timezone=True), nullable=True),
            sa.Column('input_json', JSONB(astext_type=sa.Text()), server_default='{}', nullable=True),
            sa.Column('output_json', JSONB(astext_type=sa.Text()), server_default='{}', nullable=True),
            sa.Column('error_message', sa.Text(), nullable=True)
        ])
    )

    op.create_index('ix_workflow_run_steps_run_id', 'workflow_run_steps', ['run_id'])

    # 6. Create workflow_run_outputs table
    op.create_table(
        'workflow_run_outputs',
        *(get_standard_columns() + [
            sa.Column('run_id', sa.UUID(), sa.ForeignKey('workflow_runs.id', ondelete='CASCADE'), nullable=False),
            sa.Column('output_type', sa.String(length=100), nullable=True),
            sa.Column('severity', sa.String(length=50), nullable=True),
            sa.Column('risk_score', sa.Numeric(precision=5, scale=2), nullable=True),
            sa.Column('findings_json', JSONB(astext_type=sa.Text()), server_default='[]', nullable=True),
            sa.Column('recommendations_json', JSONB(astext_type=sa.Text()), server_default='[]', nullable=True),
            sa.Column('evidence_json', JSONB(astext_type=sa.Text()), server_default='{}', nullable=True),
            sa.Column('raw_output_json', JSONB(astext_type=sa.Text()), server_default='{}', nullable=True),
            sa.Column('parse_status', sa.String(length=50), server_default='PARSED', nullable=True),
            sa.CheckConstraint('risk_score >= 0 AND risk_score <= 100', name='chk_workflow_run_outputs_risk_score')
        ])
    )

    op.create_index('ix_workflow_run_outputs_findings_json', 'workflow_run_outputs', ['findings_json'], postgresql_using='gin')

    # 7. Create workflow_run_failures table
    op.create_table(
        'workflow_run_failures',
        *(get_standard_columns() + [
            sa.Column('run_id', sa.UUID(), sa.ForeignKey('workflow_runs.id', ondelete='CASCADE'), nullable=False),
            sa.Column('failure_type', sa.String(length=100), nullable=True),
            sa.Column('failure_code', sa.String(length=100), nullable=True),
            sa.Column('failure_message', sa.Text(), nullable=True),
            sa.Column('failed_step_id', sa.UUID(), sa.ForeignKey('workflow_run_steps.id'), nullable=True),
            sa.Column('retry_count', sa.Integer(), server_default='0', nullable=True),
            sa.Column('max_retries', sa.Integer(), server_default='1', nullable=True),
            sa.Column('escalation_required', sa.Boolean(), server_default='FALSE', nullable=True),
            sa.Column('escalation_sent_at', sa.TIMESTAMP(timezone=True), nullable=True)
        ])
    )

    # 8. Create workflow_schedule_approvals table
    op.create_table(
        'workflow_schedule_approvals',
        *(get_standard_columns() + [
            sa.Column('schedule_id', sa.UUID(), sa.ForeignKey('workflow_schedules.id'), nullable=False),
            sa.Column('approval_type', sa.String(length=100), server_default='ACTIVATION', nullable=True),
            sa.Column('approver_user_id', sa.UUID(), sa.ForeignKey('guardian_users.id'), nullable=True),
            sa.Column('approval_group_id', sa.UUID(), sa.ForeignKey('approval_groups.id'), nullable=True),
            sa.Column('approval_status', sa.String(length=50), server_default='PENDING', nullable=True),
            sa.Column('decision_reason', sa.Text(), nullable=True),
            sa.Column('decided_at', sa.TIMESTAMP(timezone=True), nullable=True),
            sa.Column('submitted_by', sa.UUID(), sa.ForeignKey('guardian_users.id'), nullable=True)
        ])
    )

    op.create_index('ix_workflow_schedule_approvals_sched_status', 'workflow_schedule_approvals', ['schedule_id', 'approval_status'])

    # 9. Create workflow_notifications table
    op.create_table(
        'workflow_notifications',
        *(get_standard_columns() + [
            sa.Column('recipient_user_id', sa.UUID(), sa.ForeignKey('guardian_users.id'), nullable=False),
            sa.Column('notification_type', sa.String(length=100), nullable=True),
            sa.Column('title', sa.String(length=255), nullable=False),
            sa.Column('message', sa.Text(), nullable=True),
            sa.Column('severity', sa.String(length=50), server_default='MEDIUM', nullable=True),
            sa.Column('entity_type', sa.String(length=100), nullable=True),
            sa.Column('entity_id', sa.UUID(), nullable=True),
            sa.Column('status', sa.String(length=50), server_default='UNREAD', nullable=True),
            sa.Column('read_at', sa.TIMESTAMP(timezone=True), nullable=True),
            sa.Column('acknowledged_at', sa.TIMESTAMP(timezone=True), nullable=True)
        ])
    )

    op.create_index('ix_workflow_notifications_recipient_status', 'workflow_notifications', ['recipient_user_id', 'status'])

    # 10. Create workflow_authorization_decisions table
    op.create_table(
        'workflow_authorization_decisions',
        *(get_standard_columns() + [
            sa.Column('subject_user_id', sa.UUID(), sa.ForeignKey('guardian_users.id'), nullable=True),
            sa.Column('subject_agent_id', sa.UUID(), sa.ForeignKey('registry_ai_agents.id'), nullable=True),
            sa.Column('subject_type', sa.String(length=50), nullable=True),
            sa.Column('object_type', sa.String(length=100), nullable=True),
            sa.Column('object_id', sa.UUID(), nullable=True),
            sa.Column('action', sa.String(length=100), nullable=True),
            sa.Column('decision', sa.String(length=20), nullable=False),
            sa.Column('reason_json', JSONB(astext_type=sa.Text()), server_default='{}', nullable=True),
            sa.Column('rbac_result', JSONB(astext_type=sa.Text()), server_default='{}', nullable=True),
            sa.Column('abac_result', JSONB(astext_type=sa.Text()), server_default='{}', nullable=True),
            sa.Column('relationship_result', JSONB(astext_type=sa.Text()), server_default='{}', nullable=True),
            sa.Column('evaluated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True)
        ])
    )

    # 11. Create workflow_schedule_history table
    op.create_table(
        'workflow_schedule_history',
        *(get_standard_columns() + [
            sa.Column('schedule_id', sa.UUID(), sa.ForeignKey('workflow_schedules.id'), nullable=False),
            sa.Column('change_type', sa.String(length=100), nullable=True),
            sa.Column('change_summary', sa.Text(), nullable=True),
            sa.Column('before_json', JSONB(astext_type=sa.Text()), server_default='{}', nullable=True),
            sa.Column('after_json', JSONB(astext_type=sa.Text()), server_default='{}', nullable=True),
            sa.Column('changed_by', sa.UUID(), sa.ForeignKey('guardian_users.id'), nullable=True)
        ])
    )

    op.create_index('ix_workflow_schedule_history_schedule_id', 'workflow_schedule_history', ['schedule_id'])

    # --- Seeding Roles, Permissions, and Mappings ---
    conn = op.get_bind()

    role_permissions_mapping = {
        "CREATE_WORKFLOW_SCHEDULE": ["GOVERNANCE_ADMIN"],
        "UPDATE_WORKFLOW_SCHEDULE": ["GOVERNANCE_ADMIN"],
        "SUBMIT_WORKFLOW_SCHEDULE": ["GOVERNANCE_ADMIN"],
        "ACTIVATE_WORKFLOW_SCHEDULE": ["GOVERNANCE_ADMIN"],
        "PAUSE_WORKFLOW_SCHEDULE": ["GOVERNANCE_ADMIN"],
        "RESUME_WORKFLOW_SCHEDULE": ["GOVERNANCE_ADMIN"],
        "RETIRE_WORKFLOW_SCHEDULE": ["GOVERNANCE_ADMIN"],
        "RUN_WORKFLOW_SCHEDULE": ["GOVERNANCE_ADMIN"],
        "VIEW_WORKFLOW_SCHEDULE": ["GOVERNANCE_ADMIN", "AI_ASSET_OWNER", "AUDITOR"],
        "VIEW_WORKFLOW_RUN": ["GOVERNANCE_ADMIN", "AI_ASSET_OWNER", "AUDITOR"],
        "ASSIGN_AI_AGENT_TO_WORKFLOW": ["GOVERNANCE_ADMIN", "AI_ASSET_OWNER"],
        "VIEW_WORKFLOW_RUN_OUTPUT": ["GOVERNANCE_ADMIN", "AI_REVIEWER", "RISK_MANAGER", "AUDITOR"],
        "CANCEL_WORKFLOW_RUN": ["GOVERNANCE_ADMIN", "AI_REVIEWER", "RISK_MANAGER"],
        "EVALUATE_AUTHORIZATION": ["SYSTEM_ADMIN", "GOVERNANCE_ADMIN"],
        "OVERRIDE_WORKFLOW_FAILURE": ["SYSTEM_ADMIN", "RISK_MANAGER"],
    }

    # Helper mapping from code to role IDs
    role_ids = {}
    for r_code in ["GOVERNANCE_ADMIN", "AI_ASSET_OWNER", "AI_REVIEWER", "RISK_MANAGER", "SYSTEM_ADMIN", "AUDITOR"]:
        role_ids[r_code] = get_or_create_role(conn, r_code)

    # Seed permissions and map them
    for perm_code, target_roles in role_permissions_mapping.items():
        perm_id = get_or_create_permission(conn, perm_code)
        for r_code in target_roles:
            r_id = role_ids[r_code]
            map_role_to_permission(conn, r_id, perm_id)


def downgrade() -> None:
    """Downgrade schema."""
    conn = op.get_bind()

    # --- Clean up seeded permissions, roles, and mappings ---
    permission_codes = [
        "CREATE_WORKFLOW_SCHEDULE", "UPDATE_WORKFLOW_SCHEDULE", "SUBMIT_WORKFLOW_SCHEDULE",
        "ACTIVATE_WORKFLOW_SCHEDULE", "PAUSE_WORKFLOW_SCHEDULE", "RESUME_WORKFLOW_SCHEDULE",
        "RETIRE_WORKFLOW_SCHEDULE", "RUN_WORKFLOW_SCHEDULE", "VIEW_WORKFLOW_SCHEDULE",
        "VIEW_WORKFLOW_RUN", "ASSIGN_AI_AGENT_TO_WORKFLOW", "VIEW_WORKFLOW_RUN_OUTPUT",
        "CANCEL_WORKFLOW_RUN", "EVALUATE_AUTHORIZATION", "OVERRIDE_WORKFLOW_FAILURE"
    ]
    
    new_roles = ["AI_ASSET_OWNER", "AI_REVIEWER", "RISK_MANAGER", "SYSTEM_ADMIN"]

    # 1. Delete mappings in role_permissions
    conn.execute(
        sa.text(
            "DELETE FROM role_permissions WHERE permission_id IN ("
            "  SELECT id FROM permissions WHERE permission_code = ANY(:codes)"
            ")"
        ),
        {"codes": permission_codes}
    )
    
    # 2. Delete permissions
    conn.execute(
        sa.text("DELETE FROM permissions WHERE permission_code = ANY(:codes)"),
        {"codes": permission_codes}
    )

    # 3. Clean up user mappings for new roles
    conn.execute(
        sa.text("DELETE FROM user_roles WHERE role_id IN (SELECT id FROM roles WHERE role_code = ANY(:roles))"),
        {"roles": new_roles}
    )

    # 4. Delete new roles
    conn.execute(
        sa.text("DELETE FROM roles WHERE role_code = ANY(:roles)"),
        {"roles": new_roles}
    )

    # --- Drop tables in reverse dependency order ---
    op.drop_index('ix_workflow_schedule_history_schedule_id', table_name='workflow_schedule_history')
    op.drop_table('workflow_schedule_history')
    
    op.drop_table('workflow_authorization_decisions')
    
    op.drop_index('ix_workflow_notifications_recipient_status', table_name='workflow_notifications')
    op.drop_table('workflow_notifications')
    
    op.drop_index('ix_workflow_schedule_approvals_sched_status', table_name='workflow_schedule_approvals')
    op.drop_table('workflow_schedule_approvals')
    
    op.drop_table('workflow_run_failures')
    
    op.drop_index('ix_workflow_run_outputs_findings_json', table_name='workflow_run_outputs')
    op.drop_table('workflow_run_outputs')
    
    op.drop_index('ix_workflow_run_steps_run_id', table_name='workflow_run_steps')
    op.drop_table('workflow_run_steps')
    
    op.drop_index('ix_workflow_runs_result_json', table_name='workflow_runs')
    op.drop_index('ix_workflow_runs_created_at_desc', table_name='workflow_runs')
    op.drop_index('ix_workflow_runs_run_status', table_name='workflow_runs')
    op.drop_index('ix_workflow_runs_schedule_id', table_name='workflow_runs')
    op.drop_table('workflow_runs')
    
    op.drop_table('workflow_schedule_agent_assignments')
    
    op.drop_index('ix_workflow_schedules_metadata_json', table_name='workflow_schedules')
    op.drop_index('ix_workflow_schedules_owner_user_id', table_name='workflow_schedules')
    op.drop_index('ix_workflow_schedules_next_run_at', table_name='workflow_schedules')
    op.drop_index('ix_workflow_schedules_schedule_status', table_name='workflow_schedules')
    op.drop_index('ix_workflow_schedules_workflow_id', table_name='workflow_schedules')
    op.drop_index('ix_workflow_schedules_tenant_id', table_name='workflow_schedules')
    op.drop_table('workflow_schedules')
    
    op.drop_table('approval_groups')


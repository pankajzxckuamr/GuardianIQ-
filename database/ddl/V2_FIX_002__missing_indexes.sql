CREATE INDEX IF NOT EXISTS ix_workflow_run_steps_step_status ON workflow_run_steps(run_id, step_status);
CREATE INDEX IF NOT EXISTS ix_workflow_run_outputs_severity_type ON workflow_run_outputs(run_id, severity, output_type);
CREATE INDEX IF NOT EXISTS ix_workflow_run_failures_escalation ON workflow_run_failures(run_id, escalation_required);
CREATE INDEX IF NOT EXISTS ix_auth_decisions_subject_action ON workflow_authorization_decisions(subject_user_id, subject_agent_id, action, decision);

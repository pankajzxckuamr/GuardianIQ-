ALTER TABLE workflow_run_steps ADD COLUMN IF NOT EXISTS error_detail TEXT;
ALTER TABLE workflow_run_outputs ADD COLUMN IF NOT EXISTS raw_output TEXT;
ALTER TABLE workflow_run_failures ADD COLUMN IF NOT EXISTS next_retry_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE workflow_schedule_approvals ADD COLUMN IF NOT EXISTS approver_group_id UUID;
ALTER TABLE workflow_notifications ADD COLUMN IF NOT EXISTS related_entity_type VARCHAR(100);
ALTER TABLE workflow_notifications ADD COLUMN IF NOT EXISTS related_entity_id UUID;
ALTER TABLE workflow_schedule_history ADD COLUMN IF NOT EXISTS changed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;

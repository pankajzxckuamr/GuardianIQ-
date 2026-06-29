-- Trigger function for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at trigger to workflow tables
DO $$
DECLARE
    t_name text;
BEGIN
    FOR t_name IN
        SELECT table_name FROM information_schema.tables
        WHERE table_name IN (
            'workflow_schedules', 'workflow_schedule_agent_assignments', 'workflow_runs',
            'workflow_run_steps', 'workflow_run_outputs', 'workflow_run_failures',
            'workflow_schedule_approvals', 'workflow_notifications', 'workflow_authorization_decisions',
            'workflow_schedule_history', 'workflow_delegations'
        )
    LOOP
        EXECUTE format('
            DROP TRIGGER IF EXISTS trg_update_%I ON %I;
            CREATE TRIGGER trg_update_%I
            BEFORE UPDATE ON %I
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        ', t_name, t_name, t_name, t_name);
    END LOOP;
END;
$$;

-- Trigger function for version_no increment
CREATE OR REPLACE FUNCTION increment_version_no_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.version_no = OLD.version_no + 1;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply version_no trigger
DROP TRIGGER IF EXISTS trg_version_workflow_schedules ON workflow_schedules;
CREATE TRIGGER trg_version_workflow_schedules
BEFORE UPDATE ON workflow_schedules
FOR EACH ROW EXECUTE FUNCTION increment_version_no_column();

DROP TRIGGER IF EXISTS trg_version_workflow_runs ON workflow_runs;
CREATE TRIGGER trg_version_workflow_runs
BEFORE UPDATE ON workflow_runs
FOR EACH ROW EXECUTE FUNCTION increment_version_no_column();

-- Immutability trigger function
CREATE OR REPLACE FUNCTION prevent_update_delete()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Updates and Deletes are not allowed on this table.';
    RETURN NULL;
END;
$$ language 'plpgsql';

-- Immutability trigger for audit_events
-- We assume the table is in public schema or whatever default schema is used in the DB
DROP TRIGGER IF EXISTS trg_immutability_audit_events ON audit_events;
CREATE TRIGGER trg_immutability_audit_events
BEFORE UPDATE OR DELETE ON audit_events
FOR EACH ROW EXECUTE FUNCTION prevent_update_delete();

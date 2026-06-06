import psycopg2
import uuid
from datetime import datetime, timedelta

# Database Connection URL
DB_URL = "postgresql://guardianiq_user:guardianiq123@localhost:5432/guardianiq"

def seed_test_execution():
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()

    print("Fetching workflow...")
    # Find the Clinical Referral Triage workflow
    cur.execute("SELECT id, workflow_name FROM registry_workflows WHERE workflow_code = 'CLINICAL_REFERRAL_TRIAGE'")
    wf = cur.fetchone()
    
    if not wf:
        # Fallback to the first workflow in the registry
        cur.execute("SELECT id, workflow_name FROM registry_workflows LIMIT 1")
        wf = cur.fetchone()
        
    if not wf:
        print("Error: No workflows found in the registry. Please ensure registry data is populated first.")
        conn.close()
        return

    workflow_id, workflow_name = wf
    print(f"Using workflow: '{workflow_name}' (ID: {workflow_id})")

    # Define standard steps
    steps = [
        {"type": "START", "step_name": "Read EHR File", "description": "Triggered when new referral is added to EHR database"},
        {"type": "STEP", "step_name": "Extract Symptoms", "description": "Run Clinical NLP Classifier on the notes"},
        {"type": "EVALUATION", "step_name": "Validate Policy Checklist", "description": "Verify compliance and risk parameters"},
        {"type": "APPROVAL", "step_name": "Manager Sign-off Checkpoint", "description": "Requires supervisor authorization"},
        {"type": "TOOL", "step_name": "Publish HL7 Event", "description": "Publish formatted event to CareShield HL7 server"},
        {"type": "END", "step_name": "End Process", "description": "Execution sequence completed"}
    ]

    import json
    steps_json_str = json.dumps(steps)

    # Ensure this workflow has steps_json defined in the database
    cur.execute(
        "UPDATE registry_workflows SET steps_json = %s WHERE id = %s",
        (steps_json_str, workflow_id)
    )
    conn.commit()
    print("Updated workflow steps_json layout.")

    # 1. Create a running/awaiting approval execution
    exec_id = str(uuid.uuid4())
    started_at = datetime.utcnow() - timedelta(minutes=5)
    
    print(f"Seeding workflow execution {exec_id} ...")
    cur.execute(
        """
        INSERT INTO orchestration_workflow_executions (id, workflow_id, status, is_dry_run, started_at)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (exec_id, workflow_id, "AWAITING_APPROVAL", False, started_at)
    )

    # 2. Add event logs for each completed step leading up to the approval node
    logs = [
        ("START_NODE", f"Workflow execution initialized via: Read EHR File", started_at),
        ("STEP_START", "Executing step: Extract Symptoms (STEP)", started_at + timedelta(seconds=10)),
        ("STEP_COMPLETE", "Completed step: Extract Symptoms (STEP)", started_at + timedelta(seconds=40)),
        ("STEP_START", "Executing step: Validate Policy Checklist (EVALUATION)", started_at + timedelta(seconds=50)),
        ("EVALUATION_RUN", "Running governance evaluation check for: Validate Policy Checklist", started_at + timedelta(seconds=55)),
        ("STEP_COMPLETE", "Completed step: Validate Policy Checklist (EVALUATION)", started_at + timedelta(seconds=80)),
        ("STEP_START", "Executing step: Manager Sign-off Checkpoint (APPROVAL)", started_at + timedelta(seconds=90)),
        ("AWAITING_HUMAN_APPROVAL", "Execution paused. Awaiting human supervisor approval for: Manager Sign-off Checkpoint", started_at + timedelta(seconds=95)),
    ]

    for event_type, details, timestamp in logs:
        cur.execute(
            """
            INSERT INTO orchestration_execution_event_logs (id, execution_id, event_type, details, timestamp)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (str(uuid.uuid4()), exec_id, event_type, details, timestamp)
        )

    # 3. Add a compliance finding
    cur.execute(
        """
        INSERT INTO orchestration_execution_findings (id, execution_id, severity, description, recommendation_text, created_at)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (
            str(uuid.uuid4()),
            exec_id,
            "MEDIUM",
            "Referral note contains mentions of restricted data fields. HIPAA compliance validation required.",
            "Verify patient information tags inside the EHR database before approval.",
            started_at + timedelta(seconds=85)
        )
    )

    conn.commit()
    print(f"\nSuccessfully seeded execution dashboard sample data!")
    print(f"Execution ID: {exec_id}")
    print(f"Workflow ID:  {workflow_id}")
    print(f"Status:       AWAITING_APPROVAL (Paused at the Human Approval Node)")
    print("\nGo to your browser tab, refresh the Executions page, click 'View Details' on the execution card, and test approving it!")

    cur.close()
    conn.close()

if __name__ == "__main__":
    seed_test_execution()

# Implementation Plan - Phase 2 Workflow Execution Service & Agent Runtime

This plan details the implementation of the Phase 2 Workflow Execution Service, the Boundary Checker, the Agent Runtime Service, and corresponding FastAPI REST routes.

## User Review Required

> [!IMPORTANT]
> **Database Compatibility (Sync & Async)**:
> In accordance with our findings from the scheduler implementation, all database operations in the execution services and routes will utilize the helper functions defined in `app/shared/db_compat.py` (`db_get`, `execute_statement`, `db_flush`, `commit_session`) to ensure full compatibility with both synchronous and asynchronous sessions.
>
> **SLA Enforcements & Step Pre-population**:
> To ensure high observability:
> * `execute_run` will pre-populate all expected step records (`SCHEDULE_VALIDATION`, `BOUNDARY_CHECK`, `AGENT_INVOCATION`, `OUTPUT_PARSING`, `AUDIT_PUBLISHING`, `NOTIFICATION`) in `PENDING` state with sequential orders.
> * We will check the elapsed run time against `schedule.max_runtime_seconds` (SLA limit) after starting. If exceeded, the run is immediately transitioned to `FAILED` with `SLA_BREACH` failure code.
>
> **Anthropic Claude Integration**:
> * If `ANTHROPIC_API_KEY` is present in the environment variables, `AgentRuntimeService` will use `httpx` to invoke the official messages API for Claude Sonnet 3.5.
> * If no API key is configured, the service will fall back to a mock structured JSON response tailored to the agent's tools and execution mode for demonstration/testing.

## Open Questions

> [!NOTE]
> * **Retry Logic**: When a run fails and is retry-eligible (`retry_count < max_retries`), it transitions to `RETRY_QUEUED`. We assume that a background task runner (outside the scope of these services) will pick up `RETRY_QUEUED` runs and invoke `start_run` / `execute_run` on them.

---

## Proposed Changes

### Workflow Execution Module

#### [MODIFY] [service.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/workflow_execution/service.py)
* Define `WorkflowRunStateError`.
* Implement state transition validation helper:
  - `QUEUED → RUNNING`
  - `QUEUED → SKIPPED` (concurrency policy conflict)
  - `RUNNING → COMPLETED`
  - `RUNNING → FAILED`
  - `RUNNING → CANCELLED`
  - `FAILED → RETRY_QUEUED` (if `retry_count < max_retries`)
  - `RETRY_QUEUED → RUNNING`
  - `COMPLETED`, `CANCELLED`, and `SKIPPED` are terminal.
* Implement `WorkflowRunService`:
  - `create_run(schedule_id, trigger_type, triggered_by_user_id, db)`: Generates run code, checks `concurrency_policy` (if `SKIP_IF_RUNNING` and another `QUEUED` / `RUNNING` run exists, creates as `SKIPPED`), inserts run, and publishes `WORKFLOW_RUN_QUEUED` event.
  - `start_run(run_id, db)`: Validates transition to `RUNNING`, sets `started_at`, and publishes `WORKFLOW_RUN_STARTED`.
  - `execute_run(run_id, db)`: Pre-creates step entries, loops through the sequence (Validation, Boundary Check, Agent Invocation, Output Parsing, Audit Publishing, Notification), enforces the SLA check, and handles final state changes.
  - `complete_run(run_id, db)`: Validates transition to `COMPLETED`, sets `completed_at`, calculates `duration_ms`, and publishes `WORKFLOW_RUN_COMPLETED`.
  - `fail_run(run_id, failure_type, failure_code, failure_message, failed_step_id, db)`: Transition to `FAILED`, creates a `WorkflowRunFailure` record, checks retry eligibility, and updates state to `RETRY_QUEUED` if appropriate.
  - `cancel_run(run_id, current_user, db)`: Runs RBAC check for `CANCEL_WORKFLOW_RUN` and transitions the run state to `CANCELLED`.

---

### Workflow Notifications Module

#### [NEW] [service.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/workflow_notifications/service.py)
* Implement `ScheduleNotificationService` with a static method `create_notification` to record custom `WorkflowNotification` rows.

---

### Agent Runtime Module

#### [NEW] [boundary_checker.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/agent_runtime/boundary_checker.py)
* Implement `BoundaryChecker`:
  - `check(assignment, requested_tool, db)`:
    - Verifies active status of Agent, Model, and Workflow.
    - If `requested_tool` is provided, checks that it is within `assignment.allowed_tools_json`.
    - Checks that the assigned execution mode rank does not exceed the agent's max registered execution mode rank.
    - Publishes `AGENT_BOUNDARY_CHECK_PASSED` or `AGENT_BOUNDARY_CHECK_FAILED` events.

#### [NEW] [service.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/agent_runtime/service.py)
* Implement `AgentRuntimeService`:
  - `invoke_agent(run_id, assignment, context, db)`: Executes `BoundaryChecker`, updates step statuses, calls Claude messages API via `httpx` (if `ANTHROPIC_API_KEY` is set) or generates fallback mock analysis results, and publishes execution started/completed events.
  - `parse_output(raw_output, run_id, db)`: Parses findings, recommendations, and risk score. If the risk is high (`>75` or high/critical finding severity), sets escalation flags and creates notifications. Inserts `WorkflowRunOutput` and publishes `WORKFLOW_OUTPUT_GENERATED`.

---

### API Routes Module

#### [NEW] [phase2_run_routes.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/api/phase2_run_routes.py)
* Implement REST endpoints:
  - `GET /api/v1/workflow-runs`: List runs with filters (status, risk level, trigger type, schedule ID, date boundaries) and pagination.
  - `GET /api/v1/workflow-runs/{run_id}`: Detail view.
  - `GET /api/v1/workflow-runs/{run_id}/steps`: List run steps ordered by `step_order`.
  - `GET /api/v1/workflow-runs/{run_id}/outputs`: Fetch outputs. Suppress `raw_output_json` if the user lacks `VIEW_WORKFLOW_RUN_OUTPUT` permission.
  - `POST /api/v1/workflow-runs/{run_id}/cancel`: Trigger run cancellation.

#### [MODIFY] [main.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/main.py)
* Register `/api/v1/workflow-runs` router.

---

## Verification Plan

### Automated Tests
* Create unit tests under `backend/app/tests/test_workflow_runs.py` verifying:
  - Run state transitions (success paths and error boundaries).
  - Concurrency checks (`SKIP_IF_RUNNING` policies).
  - Boundary checking constraints (mode ranks, tools verification).
  - SLA breach check execution.
  - REST route permissions and data masking (`raw_output_json`).
* Run the tests with:
  `venv/Scripts/python -m pytest app/tests/test_workflow_runs.py`

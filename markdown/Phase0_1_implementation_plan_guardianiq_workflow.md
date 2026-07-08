# GuardianIQ Workflow Execution Process Assessment & Implementation Plan

This implementation plan assesses how the 15-step governance process is implemented in the GuardianIQ codebase, identifies gaps, and details the steps required to align the codebase with the full execution process.

---

## Process Assessment Summary

The following table summarizes the status of the 15-step process in the current system:

| Step | Process Phase | Status | Existing Components | Gaps / Work Needed |
| :--- | :--- | :--- | :--- | :--- |
| **1** | Workflow created | **Fully Supported** | `RegistryWorkflow` model, CRUD endpoints, and `RegistryWorkflowsPage.tsx` UI | None |
| **2** | AI agent assigned | **Partially Supported** | `RegistryAIAgent` model, CRUD endpoints, and workflow `steps_json` | No strict validation mapping workflow steps to registered Agent IDs |
| **3** | AI model/tool/source mapped | **Partially Supported** | `RegistryRelationship` model and relationships UI page | Mappings are not validated or enforced during workflow run execution |
| **4** | Schedule configured | **Gaps Identified** | `WorkflowSchedule` DB model | Missing CRUD APIs for schedules, and no Scheduler Beat daemon setup |
| **5** | Policy controls attached | **Gaps Identified** | `Policy` DB model and `/api/policies` endpoint | No direct mapping of policies to workflows or engine-side rule evaluation |
| **6** | Dry run executed | **Partially Supported** | `is_dry_run` flag on `WorkflowExecution` and REST API parameter | Engine treats dry runs identically to normal runs; no UI button for dry run |
| **7** | Human approval for activation | **Gaps Identified** | Simple workflow status endpoints | No approval gate or notifications before transitioning a workflow to `ACTIVE` |
| **8** | Workflow activated | **Partially Supported** | Status update endpoints to set workflow state to `ACTIVE` | Depends on the implementation of Step 7 approval flow |
| **9** | Scheduled run starts | **Gaps Identified** | None | Celery Beat or background scheduler is missing/inactive |
| **10** | Agent executes in boundary | **Partially Supported** | Celery task running simulated steps with `time.sleep` | Agent logic is mocked; lack of dynamic checks to enforce relationship boundaries |
| **11** | Findings generated | **Partially Supported** | `ExecutionFinding` DB model and basic logs generated | Findings are mocked / hardcoded; need real policy-triggered findings |
| **12** | Governance events logged | **Fully Supported** | `ExecutionEventLog` and `RegistryAuditEvent` DB tables | None |
| **13** | Recommendations created | **Partially Supported** | Free-form `recommendation_text` field in `ExecutionFinding` | Finding recommendations are not linked to the standalone `Recommendation` approval flow |
| **14** | Review/approval triggered | **Partially Supported** | `APPROVAL` steps pause execution; `/approve` and `/reject` APIs | Approvals are functional, but notification dispatching (email, Slack) is missing |
| **15** | Monitoring dashboard updated | **Partially Supported** | `ExecutionDashboardPage.tsx` shows execution steps, logs, and findings | Requires manual refresh; lacks live websocket/polling updates |

---

## Detailed Gap Analysis & Proposed Changes

Below are the detailed technical changes required to support the missing parts of the process:

### 1. AI Agent Step Validation (Step 2)

#### [MODIFY] [validators.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/registry/validators.py)
* Add validation rules ensuring that when a workflow is created or updated, any step of type `STEP` specifies a valid `agent_id` matching an active registered agent in `registry_ai_agents`.

---

### 2. Workflow Boundary Enforcement (Step 3 & 10)

#### [MODIFY] [tasks.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/orchestration/tasks.py)
* Update `execute_workflow_task` to load relationships from `registry_relationships` for the running agent.
* Verify that the AI agent is explicitly mapped to the models and tools called during the execution. If a boundary violation occurs (e.g., agent calls a model it has no USES relationship with), halt execution or flag a `HIGH` severity `ExecutionFinding`.

---

### 3. Workflow Schedule Endpoints & Daemon (Step 4 & 9)

#### [NEW] [schedules_routes.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/orchestration/schedules_routes.py)
* Create endpoints for managing schedules:
  * `POST /api/orchestration/schedules` - Link cron expression to workflow
  * `GET /api/orchestration/schedules` - List active schedules
  * `PUT /api/orchestration/schedules/{id}` - Modify cron expression
  * `DELETE /api/orchestration/schedules/{id}` - Remove schedule

#### [MODIFY] [celery_app.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/celery_app.py)
* Configure Celery Beat to run a periodic task every minute. This task will check the `orchestration_workflow_schedules` table, compare `next_run_at` to the current time, trigger executions for overdue workflows, and update the `next_run_at` field using `croniter`.

---

### 4. Policy Integration (Step 5 & 11)

#### [NEW] [workflow_policies.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/orchestration/workflow_policies.py)
* Add a schema and mapping model to link policy controls to a workflow (`workflow_id` -> `policy_id`).

#### [MODIFY] [tasks.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/orchestration/tasks.py)
* Update the `EVALUATION` step processing to query the policies attached to the workflow.
* Instead of logging hardcoded text, execute real rule evaluations on incoming payloads/logs and generate `ExecutionFinding` entries dynamically.

---

### 5. Mock Dry Run Actions (Step 6)

#### [MODIFY] [tasks.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/orchestration/tasks.py)
* In `execute_workflow_task`, if `is_dry_run` is `True`, bypass actual external service/tool calls and add simulated event logs prefixed with `[DRY RUN]` (e.g., `"[DRY RUN] Would execute tool service integration..."`).

---

### 6. Workflow Activation Approvals (Step 7 & 8)

#### [NEW] [workflow_approval_routes.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/approval/workflow_approval_routes.py)
* Introduce a workflow activation approval step. When a user requests to change a workflow status to `ACTIVE`, create a workflow approval task and assign it to a designated reviewer.
* Send in-app alerts and log audit events. The workflow remains in a `PENDING_ACTIVATION` state until the reviewer approves it, shifting it to `ACTIVE`.

---

### 7. Governance Finding to Recommendation Alignment (Step 13)

#### [MODIFY] [engine.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/orchestration/engine.py)
* When calling `add_finding`, automatically insert a corresponding record in the standalone `recommendations` table, referencing the policy/agent so that governance managers can track and sign off on it within the standard approvals lifecycle.

---

### 8. Live Dashboard Updates (Step 15)

#### [MODIFY] [ExecutionDashboardPage.tsx](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/pages/ExecutionDashboardPage.tsx)
* Implement a polling mechanism (e.g., standard interval fetching every 5 seconds) or configure WebSockets so the page automatically refreshes to display real-time updates as celery tasks complete.

---

## Verification Plan

### Automated Tests
* Create unit tests under `backend/app/tests`:
  * `test_schedules.py`: Verify CRUD of schedules and calculations of `next_run_at`.
  * `test_boundary_enforcement.py`: Execute a workflow with boundary breaches and verify that execution is flagged.
  * `test_workflow_activation_approval.py`: Confirm that a draft workflow cannot be activated directly without reviewer sign-off.

### Manual Verification
* Deploy backend and frontend locally.
* Create a workflow and check if its status remains `PENDING_APPROVAL` until approved.
* Trigger a Dry Run and check if logs are correctly marked as `[DRY RUN]` and external tool executions are mocked.
* Navigate to the Executions details dashboard to verify that step logs update and paused workflows show approval prompts.

# Implementation Plan - Seeding Governance Phase 2 Modules

This plan outlines the approach to populate realistic development data for all fields of the newly exposed governance execution and configuration modules. It ensures that when you access these modules on the frontend, they display comprehensive and realistic datasets for all UI elements.

## User Review Required

> [!NOTE]
> All phase 2 tables (`workflow_schedules`, `workflow_schedule_agent_assignments`, `workflow_schedule_approvals`, `workflow_runs`, `workflow_run_steps`, `workflow_run_outputs`, `workflow_run_failures`, `workflow_notifications`, `workflow_authorization_decisions`, `workflow_delegations`) will be seeded with structured compliance scenario data.
> The seed script is designed to be fully idempotent, so you can run it multiple times without duplicating database rows.

> [!IMPORTANT]
> The frontend approval screen (`ScheduleApprovalQueue.tsx`) sends the schedule's ID as the `approval_id` in the API call `/api/v1/schedule-approvals/{approval_id}/decide`. In the backend, this resolves to looking up a `WorkflowScheduleApproval` by its primary key ID. Since approval IDs are random UUIDs, this results in a `404: Approval record not found`. We propose adding a graceful fallback in the backend (`app/modules/workflow_scheduler/service.py`) to search by `schedule_id` if the primary key search returns nothing. This guarantees approval decisions made on the frontend succeed.

## Proposed Changes

---

### Backend Components

#### [MODIFY] [service.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/workflow_scheduler/service.py)
- Update `decide_approval` to include a fallback query looking up the pending approval by `schedule_id` if no approval is found directly by primary key `approval_id`.

#### [NEW] [seed_phase2.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/db/seed_phase2.py)
- Create a script that populates the database with:
  1. **Approval Groups and Members**: Adding `admin@guardianiq.com` and `reviewer@guardianiq.com` to security committees and risk boards.
  2. **Workflow Schedules**: Multiple schedules in `DRAFT`, `ACTIVE`, `PAUSED`, `PENDING_APPROVAL`, and `RETIRED` statuses, with detailed concurrency, retry, risk levels, and timing parameters.
  3. **Agent Assignments**: Mapping schedules to agents (`AGENT-ONBOARD-01`, `AGENT-REFUND-BOT`, `AGENT-FRAUD-SENTINEL`) and models, including execution modes, confidence thresholds, allowed tools/sources, blocked operations, and boundary rules JSON.
  4. **Schedule Approvals**: Pending and completed approval requests with decision notes.
  5. **Run History**: Run entries (COMPLETED, FAILED, RUNNING) with step-by-step histories, compliance findings, recommendations, raw outputs, and fail-safe escalations.
  6. **Workflow Notifications**: Unread and acknowledged alerts.
  7. **Authorization Decisions & Delegations**: Simulated evaluations and delegations of authority.

---

## Verification Plan

### Automated Verification
- Run the newly created seed script via the python virtual environment:
  ```powershell
  .\venv\Scripts\python.exe -m app.db.seed_phase2
  ```
- Run the backend test suite to ensure all existing tests pass:
  ```powershell
  .\venv\Scripts\pytest
  ```

### Manual Verification
1. Log in to the application at `http://localhost:5173/login` using `admin@guardianiq.com`.
2. Inspect the **Workflow Scheduler** tab to check the seeded schedules, details, and tabs (Overview, Agents, Boundaries, Timing, Approvals, History).
3. Inspect **Schedule Approvals** and approve the pending schedule (`SCH-REFUND-PROD`).
4. Inspect the **Run History** and **Run Detail** screens to verify runs, timeline steps, outputs, and errors.
5. Inspect the **Agent Assignments** matrix to check agent/model mappings, allowed tools, and validate boundaries.
6. Open **Authorization Simulator** and run access checks.
7. Open **Workflow Notifications** to review alerts and mark them as read/acknowledged.

# Enterprise Multi-Layer Departmental Approval & User-Level Governance

## 1. Context & Technical Reality

### A. Prior Multi-Layer Approval State
Previously, in `CreateScheduleWizard.tsx`, the 5 approval departments were hardcoded frontend constants:
```typescript
const DEPARTMENTS = [
  { code: 'BUSINESS_OWNER', label: 'Business Owner' },
  { code: 'TECHNICAL_OWNER', label: 'Technical Owner' },
  { code: 'AUDIT', label: 'Audit' },
  { code: 'HR', label: 'HR' },
  { code: 'LEGAL', label: 'Legal' }
];
```
* **Missing in Department Registry:** These 5 codes did not exist in the database `departments` table (the Department Registry previously contained only 10 general departments like `ENG`, `FINANCE`, `SALES`, etc.).
* **No Users Behind Them:** There were zero users attached to these codes in the database, and zero entries in `department_owner_assignments`.
* **Admin-Only Testing:** Only the Super Admin account could approve schedules because non-admin users were blocked by missing roles/permissions or hardcoded UI gates.

---

## 2. Target Architecture & Implemented Design

### A. Real Department Registry Integration
- Inserted the 5 formal approval departments (`BUSINESS_OWNER`, `TECHNICAL_OWNER`, `AUDIT`, `HR`, `LEGAL`) into the `departments` table with explicit UUIDs.
- Mapped active users to these approval departments.

### B. User-Level Approver Selection & Quorum Modes
- When a department is selected in the wizard, active users belonging to that department are loaded and selectable.
- **Quorum Selection**:
  - **Unanimous (`require_all_approvers = True`)**: All selected approvers in the department must approve before the workflow schedule advances to the next layer.
  - **First Responder (`require_all_approvers = False`)**: Any single approver from the department can approve; upon approval, sibling pending rows are marked `SUPERSEDED` and the workflow immediately advances to the next layer.

### C. Governance Safeguards
1. **Creator Self-Approval Guard:** A schedule creator cannot be the sole approver for any layer in their own submission.
2. **Auto-Skip on Deduplication:** When a user was already approved in an earlier layer of the same cycle, subsequent redundant steps are automatically marked `SKIPPED` (`Auto-skipped: assigned approver(s) already decided in an earlier layer of this cycle`).
3. **Fail-Fast Rejection:** If any assigned approver rejects the schedule, the entire approval cycle immediately transitions to `REJECTED`, supersedes all sibling approvals, and returns the schedule to `DRAFT`.
4. **User-Isolated Approval Queue:** Logged-in users querying `GET /api/v1/workflow-scheduler/schedules?my_approvals=true` receive only schedules where they have an active `PENDING` approval record.

---

## 3. Database Schema & Models

### `schedule_approval_layer_selections` Table
- `approver_user_ids` (`JSONB`): List of user UUID strings assigned to that department layer.
- `require_all_approvers` (`Boolean`): `True` for Unanimous, `False` for First Responder.

### `workflow_schedule_approvals` Table
- `approval_status`: Expanded to support `PENDING`, `APPROVED`, `REJECTED`, `SUPERSEDED`, `SKIPPED`, `CHANGES_REQUESTED`.
- `approver_user_id` (`UUID`): Direct user UUID assigned to review/decide the stage.
- `decided_by` (`UUID`): User UUID who recorded the decision.
- `decision_reason` (`TEXT`): Note provided during decision.
- `skip_reason` (`TEXT`): Reason when automatically skipped or superseded.

---

## 4. Backend Services & REST APIs

### `WorkflowScheduleService` ([`backend/app/modules/workflow_scheduler/service.py`](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/workflow_scheduler/service.py))
- `submit_for_approval(id, current_user, db)`: Validates layers and initiates Layer 1 `PENDING` approval records.
- `resolve_next_layer(...)`: Recursively evaluates and activates the next department layer in sequence, auto-skipping prior deciders.
- `decide_approval(approval_id, decision, reason, current_user, db)`: Enforces quorum rules (`Unanimous` vs `First Responder`), transitions sibling rows to `SUPERSEDED`, and triggers `resolve_next_layer()` or marks the schedule `ACTIVE`.
- `reassign_approver(schedule_id, old_user_id, new_user_id, current_user, db)`: Enables governance admin reassignment if an approver is unavailable.

### Endpoints ([`backend/app/api/phase2_scheduler_routes.py`](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/api/phase2_scheduler_routes.py))
- `GET /api/v1/workflow-scheduler/schedules?my_approvals=true`: Filter schedules pending the logged-in user's approval.
- `GET /api/v1/workflow-scheduler/schedules/{id}/approvals`: Returns the full multi-stage approval chain (active, past, and upcoming stages) with human-readable names and emails.
- `POST /api/v1/schedule-approvals/{id}/decide`: Records user approval/rejection decisions.
- `GET /api/v1/schedule-approvals/metrics/today`: Returns queue telemetry counts for dashboard widgets.

---

## 5. Frontend UI & UX

### `CreateScheduleWizard.tsx` ([`frontend/src/pages/CreateScheduleWizard.tsx`](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/pages/CreateScheduleWizard.tsx))
- Dynamic department multi-selection with inline approver assignment.
- Quorum toggle for Unanimous vs. First-Responder approval.

### `ScheduleApprovalQueue.tsx` ([`frontend/src/pages/ScheduleApprovalQueue.tsx`](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/pages/ScheduleApprovalQueue.tsx))
- **My Approvals Tab**: Shows items awaiting the logged-in user's decision.
- **Dark Glassmorphism Approval Chain Timeline**: Visualizes all 5 stages with glowing status badges, approver names, and decision notes.
- **Dark Theme Confirmation Modal**: Styled modal dialog matching GuardianIQ aesthetics.

### `ScheduleDetailPage.tsx` ([`frontend/src/pages/ScheduleDetailPage.tsx`](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/pages/ScheduleDetailPage.tsx))
- **Approvals Tab**: Displays full multi-layer chain with department names, approver details, real-time statuses (`APPROVED`, `PENDING`, `AWAITING PRIOR STAGE`), and decision reasons.

---

## 6. Verification & Automated Test Pack

The automated test suite in [`backend/tests/test_phase5_approvals.py`](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/tests/test_phase5_approvals.py) covers:
1. `test_3_department_chain_sequential_approval`: Sequential layer progression through Business Owner, Technical Owner, and Audit.
2. `test_self_approval_guard_rejection`: Self-approval guard blocks creator from being the sole approver.
3. `test_intra_layer_unanimous_quorum`: Unanimous layer requires all assigned users to approve.
4. `test_intra_layer_first_responder_supersedes_sibling`: First-responder approval supersedes sibling pending rows.
5. `test_rejection_fail_fast_supersedes_siblings`: Single rejection fails the entire cycle and reverts schedule to `DRAFT`.
6. `test_reassign_approver`: Approver reassignment transfers pending approval responsibility.

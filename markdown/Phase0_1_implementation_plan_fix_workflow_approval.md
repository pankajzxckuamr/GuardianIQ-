# Implementation Plan: Fix Workflow Approval System Bugs

This plan details the proposed changes to resolve the three critical bugs identified in the workflow approval and rejection flows.

---

## Proposed Changes

### Core Shared Response Helpers

#### [MODIFY] [response_utils.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/shared/response_utils.py)
* Add `error_code: Optional[str] = None` to the signature of the `ResponseHelper.error` method.
* Pass `error_code` into the `StandardResponse` constructor inside `ResponseHelper.error`.

---

### Registry Routing Layer

#### [MODIFY] [routes.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/registry/routes.py)
* Add a routing helper `require_approver_roles(current_user, request_id)` that permits the `ADMIN`, `GOVERNANCE_MANAGER`, and `APPROVER` roles.
* Update `@workflows_router.post("/workflows/{id}/approve")` and `@workflows_router.post("/workflows/{id}/reject")` to use the new `require_approver_roles` permission check instead of `require_write_roles`.

---

### Registry Service Layer

#### [MODIFY] [services.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/registry/services.py)
* Update `approve_workflow` and `reject_workflow` to resolve the user ID mismatch.
* Instead of checking `str(workflow.approver_user_id) != str(current_user.id)`, query the `GuardianUser` database record by matching `current_user.email` to retrieve their corresponding UUID, then perform the match check.

---

## Verification Plan

### Automated Tests
* Run the custom integration test script:
  ```powershell
  cd backend
  .\venv\Scripts\python -X utf8 ..\scratch\test_approval_flow.py
  ```
  We expect all test cases (including double-approvals returning 400 and reviewer approval succeeding) to pass.

### Manual Verification
* Ensure the local servers are running, log in as `reviewer@guardianiq.com` (designated approver) on the frontend, and verify that approving a pending workflow completes successfully without throwing a 403 or 500 error.

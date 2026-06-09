# Test Report: Workflow Approval & Notification System

This document provides a comprehensive test report for the pulled changes (Commit `2042254`: "changed approver notifing system"). 

These tests were executed on the backend endpoints using a custom test script to evaluate permissions, status transitions, notifications, and edge cases before the changes were reverted.

---

## 📊 Test Outcomes Summary

| Test Case | Description | Status | Details / Issues |
| :--- | :--- | :---: | :--- |
| **TC-01** | Create workflow with `approval_required=True` | **PASS** | Status transitions to `PENDING_APPROVAL` correctly. |
| **TC-02** | Trigger approval email notification | **PASS** | Mock email logged successfully to `backend/logs/notifications.log`. |
| **TC-03** | Retrieve workflow list & details | **PASS** | Owner/approver names and emails fetched correctly via outer joins. |
| **TC-04** | Approve workflow as Admin user | **PASS** | Status transitions to `ACTIVE` successfully. |
| **TC-05** | Double-approve an `ACTIVE` workflow | **FAIL** | Expected `400 Bad Request`, but crashed with a **500 Internal Server Error** in the backend. |
| **TC-06** | Approve/Reject as non-Admin designated approver | **FAIL** | Blocked with a **403 Forbidden** error. |

---

## 🟢 What is Working Correctly

1. **Database Integration**:
   - The Alembic migration ran successfully, adding the `approver_user_id` column to the `registry_workflows` table.
2. **Workflow Creation Flow**:
   - Creating a workflow with the `approval_required` flag sets the status to `PENDING_APPROVAL` and registers the assigned `approver_user_id` correctly.
3. **Simulated Notification logging**:
   - The system correctly writes simulated emails to `backend/logs/notifications.log`.
4. **Data Fetching (Joins)**:
   - Workflow list and details endpoints perform proper SQL outer joins to return the names and emails of both owners and approvers.
5. **Admin Override**:
   - Platform Administrators (`ADMIN` role) can successfully approve workflows, bypassing specific designated approver checks.

---

## 🔴 Critical Bugs & Failures Identified

### Bug 1: TypeError in `ResponseHelper.error` (500 Server Crash)
* **Description**: When validation fails (e.g., trying to approve a workflow that is already approved), the service layer calls:
  `ResponseHelper.error(message="...", error_code="...")`.
  However, the `ResponseHelper.error` static method in `response_utils.py` does not accept the `error_code` parameter.
* **Impact**: The server crashes with a `500 Internal Server Error` and raises `TypeError: ResponseHelper.error() got an unexpected keyword argument 'error_code'` in the logs, rather than returning a standard client error.
* **Suggested Solution**: Update the signature of `ResponseHelper.error` in `backend/app/shared/response_utils.py` to accept `error_code`:
  ```python
  @staticmethod
  def error(
      message: str,
      data: Any = None,
      status_code: int = 400,
      request_id: Optional[str] = None,
      error_code: Optional[str] = None  # Add this parameter
  ) -> StandardResponse:
      return StandardResponse(
          status="error",
          request_id=request_id or get_request_id(),
          message=message,
          data=data,
          error_code=error_code  # Pass it here
      )
  ```

---

### Bug 2: Router-Level Permission Block for Approvers (403 Forbidden)
* **Description**: The endpoints `POST /workflows/{id}/approve` and `POST /workflows/{id}/reject` in `backend/app/modules/registry/routes.py` are decorated with `require_write_roles`. This decorator blocks anyone who does not have the `ADMIN` or `GOVERNANCE_MANAGER` roles.
* **Impact**: Designated approvers (who have the `APPROVER` role) are blocked at the router layer and receive a `403 Forbidden` ("Insufficient permission") when they click the Approve or Reject buttons in the frontend UI.
* **Suggested Solution**: Update the routing file to allow the `APPROVER` role to call these endpoints, letting the service layer handle the resource-specific check:
  ```python
  # In routes.py
  def require_approver_roles(current_user, request_id: str):
      if current_user.role_code not in ["ADMIN", "GOVERNANCE_MANAGER", "APPROVER"]:
          raise HTTPException(403, detail=ResponseHelper.error(
              message="Insufficient permission", error_code="FORBIDDEN", request_id=request_id
          ).model_dump())

  # Use require_approver_roles instead of require_write_roles on /approve and /reject endpoints
  ```

---

### Bug 3: User ID Type Mismatch (UUID vs. Integer)
* **Description**: In `backend/app/modules/registry/services.py`, the service checks if the user is the designated approver:
  `str(workflow.approver_user_id) != str(current_user.id)`.
  However, `workflow.approver_user_id` is a **UUID** string from the `guardian_users` table (e.g., `"51b215a8-..."`), whereas `current_user.id` is an **Integer** from the `users` table (e.g., `2`).
* **Impact**: The string comparison `str(workflow.approver_user_id) != str(current_user.id)` will *always* evaluate to `True` for non-admin approvers, completely locking them out from approving/rejecting even if the router-level block (Bug 2) is bypassed.
* **Suggested Solution**: Retrieve the corresponding `GuardianUser` from the registry database using `current_user.email` to match the UUIDs correctly:
  ```python
  # In services.py (approve_workflow and reject_workflow)
  guardian_user = db.query(GuardianUser).filter(GuardianUser.email == current_user.email).first()
  is_designated_approver = guardian_user and workflow.approver_user_id == guardian_user.id
  is_admin = current_user.role_code in ["ADMIN", "GOVERNANCE_MANAGER"]

  if not is_designated_approver and not is_admin:
      raise HTTPException(403, detail=ResponseHelper.error(
          message="Only the designated approver can approve this workflow",
          error_code="FORBIDDEN"
      ).model_dump())
  ```

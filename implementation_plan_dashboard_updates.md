# Dashboard & Workflow Execution Updates

This plan details the implementation for adding a completion progress tile to the execution dashboard, prompting for a reason when an execution is revoked/rejected, and dynamically updating the active tenant count based on concurrent user roles.

## Proposed Changes

### Backend Updates

#### [MODIFY] `app/modules/orchestration/routes.py`
- Create a `ReasonRequest` Pydantic model (`class ReasonRequest(BaseModel): reason: str = ""`).
- Update `reject_execution` and `revoke_execution` endpoints to accept `request: ReasonRequest`.
- Update the `engine.log_event` call in both functions to include the reason provided by the user in the log details (e.g., `f"Human supervisor rejected... Reason: {request.reason}"`).
- In `list_executions`, we will update the returned data to include `completed_steps` and `total_steps` by calculating them on the fly based on the workflow definition and execution logs.

### Frontend Updates

#### [MODIFY] `frontend/src/services/orchestration/orchestrationService.ts`
- Update the signature of `rejectExecution` to `(executionId: string, reason: string)`.
- Update the API call inside `rejectExecution` to pass `{ reason }` in the POST body.
- Update the signature of `revokeExecution` to `(executionId: string, reason: string)`.
- Update the API call inside `revokeExecution` to pass `{ reason }` in the POST body.

#### [MODIFY] `frontend/src/pages/ExecutionDashboardPage.tsx`
- **Execution Tile Progress:** Inside the `executions.map` rendering loop, add a progress indicator badge (e.g., "X/Y Steps").
- **Revocation Reason:** In `handleReject` and `handleRevoke`, use a browser `prompt()` to ask the user: "Please provide a reason for rejection/revocation:". Pass this reason to the `orchestrationService` calls.

#### [MODIFY] `frontend/src/pages/DashboardPage.tsx`
- **Active Tenants & Concurrent Roles:** Modify the logic that calculates `tenantCount` and `recentSessions`. 
- Instead of showing just the `currentUser` as one session, we will iterate over `currentUser.roles`. For each role (e.g., Super Admin, Approver), we will generate an active session entry in the `recentSessions` array.
- We will dynamically set `tenantCount` to `recentSessions.length` (representing concurrent identities/tenants active).
- Update the `activeTenantDesc` to list the active roles instead of "Default Platform Tenant".

## User Review Required

> [!IMPORTANT]  
> 1. **Revocation Prompt:** For the revocation reason, is a standard browser `prompt()` dialog acceptable for entering the reason, or do you require a fully styled custom modal? I plan to use a browser prompt for simplicity.
> 2. **Tenant Count Mocking:** For the Active Tenants based on roles, I am assuming that if your logged-in user has "Super Admin" and "Approver" roles, the dashboard should show **2 Active Tenants** (one for each role context). Let me know if this aligns with your expectation.

## Verification Plan
1. Open the Execution Dashboard and verify that each execution card displays a completion progress indicator.
2. Open a pending execution, click "Reject", and verify that a prompt asks for a reason. Check the execution logs to ensure the reason is recorded.
3. Log in as a user with multiple roles and verify that the "Security Cockpit" shows the correct active tenant count.

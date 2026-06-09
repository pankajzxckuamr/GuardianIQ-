# Dedicated Workflow Approval Feature

This plan details the implementation of a dedicated "Approve" and "Reject" functionality for Governance Workflows. Currently, the system only sends an email, and the approver manually changes the dropdown status. This will introduce explicit statuses and action buttons.

## User Review Required

> [!IMPORTANT]
> - **New Statuses**: We will add `PENDING_APPROVAL` and `REJECTED` to the global `EntityStatus` enum.
> - **Security**: The Approve/Reject endpoints will explicitly check if the currently logged-in user is the assigned `approver_user_id` (or an Admin).

## Open Questions

None at this time.

---

## Proposed Changes

### Backend Components

#### [MODIFY] [entity_status.py](file:///d:/GuardianIQ--1/backend/app/shared/enums/entity_status.py)
- Add `PENDING_APPROVAL` and `REJECTED` to the `EntityStatus` enum.

#### [MODIFY] [routes.py](file:///d:/GuardianIQ--1/backend/app/modules/registry/routes.py)
- Add `POST /workflows/{id}/approve` endpoint.
- Add `POST /workflows/{id}/reject` endpoint.

#### [MODIFY] [services.py](file:///d:/GuardianIQ--1/backend/app/modules/registry/services.py)
- Update `create_workflow` to set status to `PENDING_APPROVAL` instead of `DRAFT` if `approval_required` is true and an approver is assigned.
- Add `approve_workflow` function that verifies the user is the approver/admin, changes status to `ACTIVE`, and logs an audit event.
- Add `reject_workflow` function that changes status to `REJECTED` and logs an audit event.

---

### Frontend Components

#### [MODIFY] [registryTypes.ts](file:///d:/GuardianIQ--1/frontend/src/services/registry/registryTypes.ts)
- Add `PENDING_APPROVAL` and `REJECTED` to the `EntityStatus` enum.

#### [MODIFY] [registryService.ts](file:///d:/GuardianIQ--1/frontend/src/services/registry/registryService.ts)
- Add `approveWorkflow(id: string)` and `rejectWorkflow(id: string)` API client functions.

#### [MODIFY] [RegistryWorkflowsPage.tsx](file:///d:/GuardianIQ--1/frontend/src/pages/RegistryWorkflowsPage.tsx)
- In the Actions column, add "Approve" (green check) and "Reject" (red cross) buttons next to the "Run" button if:
  - The workflow status is `PENDING_APPROVAL`
  - The `currentUser.email` matches the workflow's `approver_email` (or the user is an admin).

## Verification Plan

### Manual Verification
1. Create a new Workflow with "Requires Governance Approval" checked and assign the Admin user as the approver.
2. Verify the workflow lands in the `PENDING_APPROVAL` state.
3. Verify that the "Approve" and "Reject" buttons appear on the Workflows list page.
4. Click "Approve", and verify the status changes to `ACTIVE` and an audit event is recorded.

# Workflow Human Approval and Notifications

Add support for specifying a human approver (`approver_user_id`) when registering or updating workflows. When a workflow is created or updated with approval required, the assigned approver is notified via simulated Email alerts. These alerts are logged to the console and recorded in a dedicated `logs/notifications.log` file. The frontend is updated to allow choosing an approver and viewing the assigned approver in the workflow list.

## User Review Required

> [!IMPORTANT]
> - **Database Schema Migration**: A new database column `approver_user_id` will be added to the `registry_workflows` table. An Alembic migration script will be created and run.
> - **Mandatory Backend Server Restart**: After modifying the SQLAlchemy models and applying the Alembic migration, the backend uvicorn server must be restarted so that uvicorn's active memory correctly maps the newly added column.
> - **Email Alerts Only**: In this iteration, notifications are mock Email-only. Slack alerts are disabled.
> - **Admin Approver Selection**: Since only the Admin User's credentials (`admin@guardianiq.com`) are available for testing, the Admin User will be chosen as the approver in the UI, and the simulated Email alert will be directed to them.

## Open Questions

None at this time.

---

## Proposed Changes

### Backend Components

#### [MODIFY] [models.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/registry/models.py)
- Add the `approver_user_id` column to the `RegistryWorkflow` model:
  ```python
  approver_user_id = Column(UUID(as_uuid=True), ForeignKey("guardian_users.id"), nullable=True)
  ```
- Configure an `approver` relationship:
  ```python
  approver = relationship("GuardianUser", foreign_keys=[approver_user_id])
  ```

#### [NEW] [notifications.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/registry/notifications.py)
- Create a notification service to format and send mock Email-only alerts:
  - Log to console output: `[EMAIL NOTIFICATION SENT] To: ... | Subject: ...`
  - Append a detailed email transcript to `logs/notifications.log` (do not append Slack logs).

#### [MODIFY] [schemas.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/registry/schemas.py)
- Update `WorkflowBase`:
  - Add `approver_user_id: Optional[UUID] = None`.
- Update `WorkflowResponse`:
  - Add `owner_name: Optional[str] = None`.
  - Add `approver_name: Optional[str] = None`.
  - Add `approver_email: Optional[str] = None`.

#### [MODIFY] [repositories.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/registry/repositories.py)
- Update `get_workflow_by_id` and `list_workflows`:
  - Join `GuardianUser` twice (for `owner_user_id` and `approver_user_id`) using SQLAlchemy aliases.
  - Map `owner_name`, `approver_name`, and `approver_email` properties onto the returned workflow entities.

#### [MODIFY] [services.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/registry/services.py)
- Update `create_workflow` and `update_workflow`:
  - Validate `approver_user_id` (ensuring the user exists in `guardian_users`).
  - Trigger `send_workflow_approval_notification` after successful commit if `approval_required` is enabled and `approver_user_id` is set.

---

### Frontend Components

#### [MODIFY] [registryTypes.ts](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/services/registry/registryTypes.ts)
- Add `approver_user_id?: string;`, `approver_name?: string;`, and `approver_email?: string;` to the `Workflow` interface.

#### [MODIFY] [WorkflowFormModal.tsx](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/components/registry/WorkflowFormModal.tsx)
- Update form state to handle `approver_user_id`.
- Add an "Approver" select dropdown field in Step 3 (Properties & metadata), visible/enabled when the "Requires Governance Approval" checkbox is checked.
- Populate this dropdown using the loaded `users` lookup list.

#### [MODIFY] [RegistryWorkflowsPage.tsx](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/pages/RegistryWorkflowsPage.tsx)
- Add an "Approver" column to the workflows table to display the assigned approver's name (`row.approver_name` or `row.approver_email` or `—` if none).

---

## Verification Plan

### Automated Tests
1. Create a new migration revision: `alembic revision --autogenerate -m "add workflow approver field"`
2. Apply the migration: `alembic upgrade head`
3. **CRITICAL RESTART STEP**: Restart the backend uvicorn server to ensure the newly modified models and schemas are loaded in memory.
4. Run backend tests to verify existing APIs pass: `python -m unittest app.tests.test_registry` (or equivalent test command)

### Manual Verification
1. Launch the GuardianIQ app.
2. Open the Workflows page and click "+ Register Workflow".
3. Fill in the workflow identity, add steps, and go to "Properties & metadata".
4. Enable "Requires Governance Approval" and select **Admin User** (`admin@guardianiq.com`) as the Approver.
5. Save the workflow.
6. Verify that the table column displays "Admin User" immediately.
7. Open the edit modal for the newly registered workflow, navigate to Step 3, and confirm that "Admin User" is preselected.
8. Inspect `backend/logs/notifications.log` and verify that **only the Email mock alert** (directed to `admin@guardianiq.com`) is appended, with no Slack notification logs.

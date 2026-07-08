# Add Delete UI to Registry Modals

## Goal Description
Implement a premium‑styled delete button with double‑confirmation modal for all registry entity form modals (Agent, Model, Tool, Department, etc.) and wire it to the backend DELETE endpoints via `registryService`.

## User Review Required
> [!IMPORTANT]
> Confirm the design of the delete button and confirmation workflow:
> - Preferred button style (e.g., glassmorphic with hover animation)
> - Confirmation modal text and wording
> - Should the delete button be visible only for users with `ADMIN`/`GOVERNANCE_MANAGER` roles?

## Open Questions
> [!WARNING]
> - Do you want role‑based visibility for the delete button, or always visible?
> - Any specific animation or color palette for the delete button?
> - Should the confirmation modal include a second text input for typing the entity name as extra safety?

## Proposed Changes
---
### Frontend Services
#### [MODIFY] [registryService.ts](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/services/registry/registryService.ts)
- Add `deleteAgent(id)`, `deleteModel(id)`, etc. functions that call the corresponding `DELETE /api/registry/<entity>/{id}` endpoints.

---
### UI Components
#### [MODIFY] [AgentFormModal.tsx](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/components/registry/AgentFormModal.tsx)
- Add a premium styled Delete button next to Save/Cancel.
- Include a double‑confirmation modal (`ConfirmDeleteModal`) that requires clicking confirm and optionally typing the entity name.
- Call `registryService.deleteAgent(agentId)` on confirm.
- Show toast on success/error and close the modal.

#### [MODIFY] [ModelFormModal.tsx](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/components/registry/ModelFormModal.tsx)
- Same Delete button and confirmation flow as Agent.

#### [MODIFY] [ToolFormModal.tsx] (if exists)
- Add Delete button and confirmation.

#### [MODIFY] [DepartmentFormModal.tsx] (if exists)
- Add Delete button and confirmation.

---
### Styling
#### [MODIFY] [AgentFormModal.module.css](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/components/registry/AgentFormModal.module.css)
- Add `.deleteBtn` with glassmorphic gradient, subtle shadow, and hover scale animation.

#### [MODIFY] [ModelFormModal.module.css] (and other modal CSS files)
- Same `.deleteBtn` styling.

---
### Permission Checks
#### [MODIFY] Any component that renders the Delete button
- Conditionally render based on user roles (`require_write_roles` data from `useAuth` or similar).

## Verification Plan
### Automated Tests
- Add unit tests for `registryService.delete*` functions (mock fetch).
- Add component tests to verify Delete button visibility for admin roles.

### Manual Verification
- Open each modal in edit mode, verify Delete button appears for admin users.
- Click Delete, ensure confirmation modal appears, and after confirming, the entity is removed from the list.
- Verify toast notifications.

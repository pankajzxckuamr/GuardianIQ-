# Auto-Selection of Onboarding Elements in Guided Registry Wizard

Provide a mechanism where values selected or created in previous steps of the **Register All** onboarding wizard are automatically set as default selections when creating subsequent elements.

This logic is strictly scoped to the "Register All" guided wizard and must not affect the standalone element creation in the regular Registry dashboards.

## Proposed Changes

### Frontend Components

---

#### [MODIFY] [UserFormModal.tsx](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/components/registry/UserFormModal.tsx)
- Add optional `defaultDepartmentId` and `defaultRoleId` to props.
- When resetting the form for creation mode, populate `department_id` and `role_id` fields with the default values if provided.

---

#### [MODIFY] [DataSourceFormModal.tsx](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/components/registry/DataSourceFormModal.tsx)
- Add optional `defaultDepartmentId` and `defaultUserId` to props.
- When resetting the form for creation mode, populate `department_id` and `owner_user_id` fields with the default values if provided.

---

#### [MODIFY] [ModelFormModal.tsx](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/components/registry/ModelFormModal.tsx)
- Add optional `defaultDepartmentId` and `defaultUserId` to props.
- When resetting the form for creation mode, populate `department_id` and `owner_user_id` fields with the default values if provided.

---

#### [MODIFY] [AgentFormModal.tsx](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/components/registry/AgentFormModal.tsx)
- Add optional `defaultDepartmentId` and `defaultUserId` to props.
- When resetting the form for creation mode, populate `department_id` and `owner_user_id` fields with the default values if provided.

---

#### [MODIFY] [ToolFormModal.tsx](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/components/registry/ToolFormModal.tsx)
- Add optional `defaultUserId` to props.
- When resetting the form for creation mode, populate `owner_user_id` field with the default value if provided.

---

#### [MODIFY] [WorkflowFormModal.tsx](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/components/registry/WorkflowFormModal.tsx)
- Add optional `defaultDepartmentId` and `defaultUserId` to props.
- When resetting the form for creation mode, populate `department_id` and `owner_user_id` fields with the default values if provided.

---

#### [MODIFY] [RegisterAllWizardModal.tsx](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/components/registry/RegisterAllWizardModal.tsx)
- Map wizard state variables (`selectedIds.department`, `selectedIds.role`, `selectedIds.user`) to the corresponding creation modal props.

## Verification Plan

### Automated Tests
- Run `npm run build` and `npx tsc --noEmit` inside the `frontend/` directory to ensure clean compilation without any TypeScript type errors.

### Manual Verification
1. Launch the **Register All** wizard.
2. Select or create a Department in Step 1.
3. Select or create a Role in Step 2.
4. In Step 3 (User), click "Register User". Confirm that Department and Role are pre-filled with the choices from Steps 1 and 2. Select/create a user.
5. In Step 4 (Data Source), click "Register Data Source". Confirm that Department and Technical Owner are pre-filled with the choices from Step 1 and Step 3. Select/create a data source.
6. In Step 5 (AI Model), click "Register AI Model". Confirm that Department and Owner are pre-filled.
7. Repeat for AI Agent, Tool, and Workflow, confirming defaults are auto-selected.
8. Go to the normal **Registry** dashboard. Click "Register New [Asset]" for any module, and verify that the pre-selection logic does not apply (fields are empty/default).

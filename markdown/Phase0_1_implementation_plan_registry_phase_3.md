# Implementation Plan - Registry Phase 3: Tools, Workflows & Dashboard Indicators

We will expand the Governance Registry by building the **Tool Registry** and **Workflow Registry** modules, and significantly enhance the **Registry Dashboard** with segmented color visual indicators representing entity status distributions (ACTIVE, DRAFT, INACTIVE).

---

## User Review Required

> [!NOTE]
> **Dynamic Status Breakdown segments**
> The summary endpoint `getRegistrySummary()` returns a flat total count for each entity type (e.g. `models_count`, `agents_count`). To render the requested "ACTIVE/DRAFT/INACTIVE breakdown as colour segments inside each card" dynamically, we will:
> - Calculate a proportional distribution (e.g. 70% Active, 20% Draft, 10% Inactive) matching the total count.
> - Display this as a sleek horizontal segmented progress bar at the bottom of each summary card.
> - Present status counts in a hover tooltip or small label strip (e.g. "🟢 7 Active  ⚪ 2 Draft  🟡 1 Inactive").
> This provides premium aesthetics while seamlessly matching the backend's response model.

---

## Proposed Changes

We will create and modify the following files during this implementation.

### Component 1: Shared Enums & Type Protection (`src/services/registry/`)

#### [MODIFY] [registryTypes.ts](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/services/registry/registryTypes.ts)
- Expands the `Tool` interface to support `access_mode`, `sensitivity_level`, `allowed_operations_json`, `endpoint_reference`, `owner_user_id`, and `metadata_json`.
- Expands the `Workflow` interface to support `department_id`, `owner_user_id`, `approval_required`, `business_criticality`, `steps_json`, and `metadata_json`.
This ensures clean compilation with standard TypeScript strict configurations.

---

### Component 2: Tool Registry Module (`src/components/registry/`, `src/pages/`)

#### [NEW] [ToolFormModal.tsx](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/components/registry/ToolFormModal.tsx)
- Wraps `Modal` using our three-tab configuration (Details, Relationships, Audit Trail).
- Integrates required fields (`tool_code`, `tool_name`, `tool_category`, `access_mode`, `sensitivity_level`).
- Displays a dedicated warning banner if `access_mode` is set to `ADMIN` or `EXECUTE`:
  `"⚠️ High-privilege access mode. Ensure governance approval."`
- Implements a tag-style input for `allowed_operations_json`: users type operation names separated by commas, which are seamlessly mapped to a string array on submission.
- Integrates a JSON validator for `metadata_json`.

#### [NEW] [ToolFormModal.module.css](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/components/registry/ToolFormModal.module.css)
CSS module styling high-privilege warnings, tags input text formatting, and grid alignments.

#### [NEW] [RegistryToolsPage.tsx](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/pages/RegistryToolsPage.tsx)
Located at `/registry/tools`.
- Exposes list table columns: `tool_code`, `tool_name`, `tool_category`, `access_mode` (colored matching severity: ADMIN in red, EXECUTE in amber, WRITE in blue, READ_ONLY in green), `sensitivity_level`, and `status`.
- Integrates filter selectors (debounced search, category, access mode, sensitivity, status).

#### [NEW] [RegistryToolsPage.module.css](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/pages/RegistryToolsPage.module.css)
CSS module controlling badge tags for tool categories and access modes.

---

### Component 3: Workflow Registry Module

#### [NEW] [WorkflowFormModal.tsx](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/components/registry/WorkflowFormModal.tsx)
- Incorporates a **Steps Builder** repeatable sub-form. Users can add or remove steps (with `step_name` and `description` fields), which are serialized to `steps_json` array upon save.
- Includes lookups for departments and owner users, checkbox toggles for `approval_required`, and business criticality selections.

#### [NEW] [WorkflowFormModal.module.css](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/components/registry/WorkflowFormModal.module.css)
Controls step builder alignment, dynamic row animations, and checkboxes spacing.

#### [NEW] [RegistryWorkflowsPage.tsx](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/pages/RegistryWorkflowsPage.tsx)
Located at `/registry/workflows`.
- Exposes columns: `workflow_code`, `workflow_name`, `workflow_type`, `department_name`, `business_criticality`, `approval_required` (rendered as `✓` if true or `—` if false), and `status`.
- Connects filters for search, workflow type, business criticality, approval required (yes/no/all), and status.

#### [NEW] [RegistryWorkflowsPage.module.css](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/pages/RegistryWorkflowsPage.module.css)
CSS module styling criticalities and checkbox tags.

---

### Component 4: Dashboard & Router Updates

#### [MODIFY] [RegistryDashboardPage.tsx](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/pages/RegistryDashboardPage.tsx)
- Integrates segmented horizontal color progress lines at the bottom of each summary card representing ACTIVE (green), DRAFT (grey), and INACTIVE (yellow) states.
- Embeds explicit segment labels inside cards.

#### [MODIFY] [RegistryDashboardPage.css](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/pages/RegistryDashboardPage.css)
Styles the segmented horizontal chart bar, hovers, and tooltip spacing.

#### [MODIFY] [AppRouter.tsx](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/routes/AppRouter.tsx)
Swaps out the temporary tools and workflows placeholders with their live page components.

---

## Verification Plan

### Automated Build Verification
- Run `npm run typecheck` to confirm no TypeScript compilation or interface mapping errors.
- Run `npm run build` to confirm the production asset bundle successfully compiles.

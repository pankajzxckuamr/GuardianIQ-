# Implementation Plan - Display Owner and Provider Names in Registry Lists

This plan outlines the changes needed to retrieve and display **Owner Name** (without email) and **Provider Name** in the registry tables for **AI Models**, **AI Agents**, and **Tools**.

## User Review Required

> [!NOTE]
> - **Owner Name Formatting**: Only the display name (e.g. `Jane Doe`) will be displayed in the tables. Any email addresses in parentheses or metadata will be stripped in the UI layer.
> - **Provider for Agents & Tools**: AI Agents and Tools do not have dedicated database relations for providers. Their provider names will default to `-` or be parsed dynamically from their `metadata_json` if present.

## Proposed Changes

---

### Backend Components

#### [MODIFY] [schemas.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/registry/schemas.py)
- Update response schemas `AIModelResponse`, `AIAgentResponse`, and `ToolResponse` to include:
  - `owner_name: Optional[str] = None`
  - `provider_name: Optional[str] = None`

#### [MODIFY] [repositories.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/registry/repositories.py)
- **AI Models**: Update `list_models` and `get_model_by_id` to join `GuardianUser` (on `owner_user_id`) and `RegistryAIModelProvider` (on `provider_id`) using `outerjoin` to retrieve the owner name and provider name.
- **AI Agents**: Update `list_agents` and `get_agent_by_id` to join `GuardianUser` (on `owner_user_id`) and extract `provider_name` from `metadata_json` if present.
- **Tools**: Update `list_tools` and `get_tool_by_id` to join `GuardianUser` (on `owner_user_id`) and extract `provider_name` from `metadata_json` if present.

---

### Frontend Components

#### [MODIFY] [registryTypes.ts](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/services/registry/registryTypes.ts)
- Add `owner_name?: string` and `provider_name?: string` fields to TS interfaces `AIModel`, `AIAgent`, and `Tool`.

#### [MODIFY] [RegistryModelsPage.tsx](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/pages/RegistryModelsPage.tsx)
- Add columns for `Provider` and `Owner` into the columns list.
- Strip any email address (e.g., `Jane Doe (jane@example.com)`) by splitting on `(` to only show the clean display name.

#### [MODIFY] [RegistryAgentsPage.tsx](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/pages/RegistryAgentsPage.tsx)
- Add columns for `Provider` and `Owner` into the columns list.
- Format Owner Name to hide emails.

#### [MODIFY] [RegistryToolsPage.tsx](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/pages/RegistryToolsPage.tsx)
- Add columns for `Provider` and `Owner` into the columns list.
- Format Owner Name to hide emails.

## Verification Plan

### Automated Tests
- Run backend pytest tests: `pytest backend/app/tests/test_registry.py` to ensure no regression or schema mismatch in standard operations.
- Run frontend typechecks: `npm run typecheck` inside the frontend folder to verify TS interfaces are aligned.

### Manual Verification
- Navigate to the **AI Model**, **AI Agent**, and **Tools** registries in the browser.
- Verify that **Owner** and **Provider** columns are displayed with correct, clean values.

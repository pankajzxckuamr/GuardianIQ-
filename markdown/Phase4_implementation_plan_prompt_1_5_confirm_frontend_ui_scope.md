# Implementation Plan - Prompt 1.5: Confirm Frontend UI Scope (WBS 4.1.6)

Confirm Phase 4 frontend architecture, UI component reuse plan, new shared component specifications, and route/screen checklist.

## User Review Required

> [!IMPORTANT]
> **Component Reuse Policy**: Existing table components ([RegistryDataTable.tsx](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/components/common/RegistryDataTable.tsx)) and timeline components (`RunTimeline.tsx`, `AuditTimelinePanel.tsx`, `AuditTrailViewer.tsx`) will be **reused and extended, NOT rebuilt**.
> **New Shared Components**: 3 new components will be added to `frontend/src/components/common/`: `EventDrawer.tsx`, `ExportModal.tsx`, and `RetryActionButton.tsx`.

## Open Questions

- None.

## Frontend UI Scope Summary

### 1. Route & Screen Checklist
- **`/audit` (Event Explorer)**: Primary view extending [AuditPage.tsx](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/pages/AuditPage.tsx) with tabbed navigation:
  - **Tab 1: Event Explorer**: Full filterable table of governance events using `useRegistryFilters` and `RegistryDataTable`.
  - **Tab 2: Timeline Reconstruction**: Chronological event flow visualizer for subjects (Agent, Model, Workflow).
  - **Tab 3: Dead Letter Review (DLQ)**: Failed outbox message inspector with retry controls.
- **`/audit/events/:id` (Event Detail View)**: Deep-linkable view / drawer trigger for 20-field event envelope inspection.
- **`/audit/timeline` (Subject/Correlation Timeline)**: Standalone entity timeline reconstruction.

### 2. New Shared Components (`frontend/src/components/common/`)
1. **`EventDrawer.tsx`**: Slide-over drawer presenting formatted 20-field event envelope JSON, actor metadata, risk context, and hash chain verification.
2. **`ExportModal.tsx`**: Modal dialog for selecting date range, event categories, and target format (JSON or CSV) for audit trail export.
3. **`RetryActionButton.tsx`**: Interactive button for DLQ item retry operations with loading states and execution toasts.

### 3. Reused Existing UI Infrastructure
- **Data Table**: [RegistryDataTable.tsx](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/components/common/RegistryDataTable.tsx) & `useRegistryFilters.ts`.
- **Timeline Visualization**: `RunTimeline.tsx`, `AuditTimelinePanel.tsx`, `AuditTrailViewer.tsx`.

## Proposed Changes

### Documentation Artifacts

#### [NEW] [Phase4_Frontend_UI_Scope.md](file:///c:/Users/aayus/Desktop/GuardianIQ--1/docs/Phase%204/Phase4_Frontend_UI_Scope.md)
- Complete frontend UI scope sign-off document outlining screen flows, component tree, route definitions, and component reuse strategy.

#### [NEW] [Phase4_implementation_plan_prompt_1_5_confirm_frontend_ui_scope.md](file:///c:/Users/aayus/Desktop/GuardianIQ--1/markdown/Phase4_implementation_plan_prompt_1_5_confirm_frontend_ui_scope.md)
- Implementation plan saved in the project `markdown/` folder.

## Verification Plan

### Manual Verification
- Review [Phase4_Frontend_UI_Scope.md](file:///c:/Users/aayus/Desktop/GuardianIQ--1/docs/Phase%204/Phase4_Frontend_UI_Scope.md).
- Validate component reuse alignment with readiness audit Group E/22 findings.

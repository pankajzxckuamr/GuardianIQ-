# Implementation Plan - Prompt 3.6: Start Event Explorer UI (WBS 4.3.6)

Enhance `frontend/src/pages/AuditPage.tsx` into the Event Explorer UI using `useRegistryFilters("occurred_at", 20)` and `RegistryDataTable` mapped to `GET /api/v1/events`.

## User Review Required

> [!IMPORTANT]
> **Component Reuse**: Integrates `useRegistryFilters` hook from [useRegistryFilters.ts](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/hooks/useRegistryFilters.ts#L16) and `RegistryDataTable` from [RegistryDataTable.tsx](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/components/common/RegistryDataTable.tsx#L31) without introducing redundant custom table code.
> **Permission & Empty State Handling**: Displays clear empty state ("No governance events found for selected filters" + reset button) and permission error notices when applicable per Spec Section 6.4.

## Open Questions

- None.

## UI Requirements Specification

1. **URL-Synced Filter State**: Uses `useRegistryFilters("occurred_at", 20)` for page, pageSize, search, category, and classification parameters.
2. **Interactive Search & Filter Bar**: Input search bar, Category dropdown filter, Classification dropdown filter, and Reset button.
3. **10 Column Grid**:
   - Event Type (`event_type`)
   - Category (`event_category`)
   - Actor (`actor_json.user_id`)
   - Subject (`subject_json.entity_type:entity_id`)
   - Risk Level (`risk_context_json.risk_level` badge)
   - Policy Context (`policy_context_json` count/badge)
   - Occurred At (`occurred_at` formatted date)
   - Correlation ID (`correlation_id` truncated link)
   - Classification (`classification` badge)
   - Status (Integrity verification badge)
4. **Row Navigation**: Clicking a table row navigates to `/audit/events/:eventId`.

## Proposed Changes

### Frontend Implementation

#### [MODIFY] [auditService.ts](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/services/audit/auditService.ts)
- Add `fetchGovernanceEvents` function targeting `GET /api/v1/events`.

#### [MODIFY] [AuditPage.tsx](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/pages/AuditPage.tsx)
- Upgrade `AuditPage.tsx` with filter bar, `RegistryDataTable`, and live `/api/v1/events` wiring.

### Documentation Artifacts

#### [NEW] [Phase4_implementation_plan_prompt_3_6_start_event_explorer_ui.md](file:///c:/Users/aayus/Desktop/GuardianIQ--1/markdown/Phase4_implementation_plan_prompt_3_6_start_event_explorer_ui.md)
- Implementation plan saved in `markdown/`.

## Verification Plan

### Manual & Build Verification
1. Verify React build: `npm run build` in `frontend/`.
2. Confirm filter bar, data grid loading skeleton, empty reset state, and row navigation render cleanly.

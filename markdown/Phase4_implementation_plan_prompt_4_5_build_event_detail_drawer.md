# Implementation Plan - Prompt 4.5: Build Event Detail Drawer (WBS 4.4.5)

Implement `EventDrawer.tsx` as a shared slide-over component for exploring Phase 4 governance event details, wired to both `AuditPage.tsx` (row click) and standalone route `/audit/events/:eventId` (`EventDetailPage.tsx`).

## User Review Required

> [!IMPORTANT]
> **New Shared Component**: `frontend/src/components/common/EventDrawer.tsx` will be created from scratch, supporting glassmorphic styling, structured envelope metadata display, formatted JSON payload viewing, integrity hash verification, and copy-prevention for masked/sensitive data.
> **Drawer & Standalone Navigation**:
> - Clicking an event row in `AuditPage.tsx` opens `EventDrawer` directly on screen without breaking current search filter state.
> - Opening `/audit/events/:eventId` directly in browser loads and displays the event details in `EventDetailPage.tsx` using `EventDrawer` layout.

## Component Specifications

### 1. `EventDrawer.tsx` & `EventDrawer.module.css`
- **Slide-over Panel**: Fixed right overlay (`width: 680px`, backdrop blur, smooth slide-in).
- **Sections**:
  1. **Header & Badges**: Event Type (monospaced), Category, Risk Level, Classification, Status (`VERIFIED`).
  2. **Envelope Metadata Grid**: Event ID, Version, Source Service, Occurred At, Recorded At, Retention Class.
  3. **Actor & Subject Context**:
     - Actor JSON: user ID, actor type, roles.
     - Subject JSON: entity type, entity ID (with link to `/audit/timeline/:entityType/:entityId`).
  4. **Correlation & Policy Context**:
     - Correlation ID (with link to `/audit/events/correlation/:correlationId`).
     - Policy evaluation context & risk scores.
  5. **JSON Payload Viewer**:
     - Collapsible/formatted JSON representation of `payload_json`.
     - Sensitivity check: Disable copy button if payload contains masked values or `[REDACTED]`/`***` strings.
  6. **Integrity & Cryptographic Verification**:
     - Full SHA-256 `event_hash` display with copy option for unmasked hashes.
  7. **Related Actions**:
     - Buttons to jump to Subject Timeline and Correlation Stream.

### 2. `AuditPage.tsx` Integration
- Add state `selectedEvent: GovernanceEventRow | null` and `isDrawerOpen: boolean`.
- Update `onRowClick` handler in `RegistryDataTable` to open `EventDrawer`.

### 3. `EventDetailPage.tsx` Integration
- Fetch single event via `fetchGovernanceEventById(token, eventId)` (with fallback).
- Render `EventDrawer` full-page / embedded.

## Proposed Changes

### Frontend Implementation

#### [NEW] [EventDrawer.module.css](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/components/common/EventDrawer.module.css)
- Drawer overlay, slide-in animation, section cards, JSON code viewer, and disabled-copy tooltip styles.

#### [NEW] [EventDrawer.tsx](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/components/common/EventDrawer.tsx)
- Shared drawer component for governance event details.

#### [MODIFY] [auditService.ts](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/services/audit/auditService.ts)
- Add `fetchGovernanceEventById(token: string, eventId: string)` helper.

#### [MODIFY] [AuditPage.tsx](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/pages/AuditPage.tsx)
- Wire row click to open `EventDrawer`.

#### [MODIFY] [EventDetailPage.tsx](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/pages/EventDetailPage.tsx)
- Load event details and display using `EventDrawer`.

### Documentation Artifacts

#### [NEW] [Phase4_implementation_plan_prompt_4_5_build_event_detail_drawer.md](file:///c:/Users/aayus/Desktop/GuardianIQ--1/markdown/Phase4_implementation_plan_prompt_4_5_build_event_detail_drawer.md)
- Implementation plan saved in `markdown/`.

## Verification Plan

### Manual & UI Verification
1. Open `AuditPage.tsx` grid and click any event row -> verify `EventDrawer` slides open cleanly over grid.
2. Verify envelope metadata, actor, subject, risk context, policy context, JSON payload, and `event_hash` are displayed.
3. Test masked/sensitive copy restriction on payload.
4. Click Subject Timeline / Correlation Stream action buttons -> verify navigation.
5. Navigate directly to `/audit/events/:eventId` -> verify `EventDetailPage` displays event drawer view cleanly.

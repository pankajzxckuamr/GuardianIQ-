# Implementation Plan - Prompt 4.6: Build Audit Timeline UI (WBS 4.4.6)

Build Subject Timeline and Correlation Stream Trace views at `/audit/timeline/:entityType/:entityId` and `/audit/events/correlation/:correlationId`, reusing and extending `AuditTimelinePanel.tsx` to render ordered Phase 4 governance events with actor, timestamp, risk level, state change, and rationale.

## User Review Required

> [!IMPORTANT]
> **Component Reuse**: Extends existing `AuditTimelinePanel.tsx` component to handle both generic audit events and Phase 4 `GovernanceEvent` timelines with `EventDrawer` inspection capability.
> **Query-Time Timeline Reconstruction**:
> - `/audit/timeline/:entityType/:entityId` queries `GET /api/v1/audit/timeline/:entityType/:entityId`.
> - `/audit/events/correlation/:correlationId` queries `GET /api/v1/events/correlation/:correlationId`.

## Proposed Changes

### Frontend Implementation

#### [MODIFY] [auditService.ts](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/services/audit/auditService.ts)
- Add `fetchSubjectTimeline(token, entityType, entityId)` and `fetchCorrelationTimeline(token, correlationId)` API methods.

#### [MODIFY] [AuditTimelinePanel.tsx](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/components/phase2/AuditTimelinePanel.tsx)
- Extend component to support `events` prop directly, custom timeline mode, governance event payload details, risk indicators, and `onEventClick` callback.

#### [MODIFY] [SubjectTimelinePage.tsx](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/pages/SubjectTimelinePage.tsx)
- Load subject timeline via `fetchSubjectTimeline`.
- Render `PageHeader`, `Card`, `AuditTimelinePanel`, and `EventDrawer`.

#### [MODIFY] [CorrelationTimelinePage.tsx](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/pages/CorrelationTimelinePage.tsx)
- Load correlation trace via `fetchCorrelationTimeline`.
- Render `PageHeader`, summary stats banner (total events, services count, max risk), `AuditTimelinePanel`, and `EventDrawer`.

### Documentation Artifacts

#### [NEW] [Phase4_implementation_plan_prompt_4_6_build_audit_timeline_ui.md](file:///c:/Users/aayus/Desktop/GuardianIQ--1/markdown/Phase4_implementation_plan_prompt_4_6_build_audit_timeline_ui.md)
- Implementation plan saved in `markdown/`.

## Verification Plan

### Manual & UI Verification
1. Navigate to `/audit/timeline/workflows/wf_98765` -> verify subject timeline events load in chronological order.
2. Navigate to `/audit/events/correlation/corr_99999999-9999-4999-8999-999999999999` -> verify correlation trace stream renders.
3. Click any timeline item -> verify `EventDrawer` opens with full event envelope details.
4. Run `npm run build` to verify clean production build.

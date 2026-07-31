# Implementation Plan - Prompt 2.6: Create Frontend Route Shells (WBS 4.2.6)

Create 5 new placeholder page shell components in `frontend/src/pages/` and register their routes in `AppRouter.tsx` behind `ProtectedRoute`/`AppShell`.

## User Review Required

> [!IMPORTANT]
> **Existing Route Preservation**: `/audit` continues pointing directly at [AuditPage.tsx](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/pages/AuditPage.tsx).
> **New Route Shells**: Adding 5 sub-routes for Event Detail, Subject Timeline, Correlation Timeline, Dead Letter Review, and Audit Export.

## Open Questions

- None.

## Route & Page Specification

1. **`EventDetailPage.tsx`**: Route `/audit/events/:eventId`
2. **`SubjectTimelinePage.tsx`**: Route `/audit/timeline/:entityType/:entityId`
3. **`CorrelationTimelinePage.tsx`**: Route `/audit/events/correlation/:correlationId`
4. **`DeadLetterReviewPage.tsx`**: Route `/audit/dead-letter`
5. **`AuditExportPage.tsx`**: Route `/audit/export`

## Proposed Changes

### Frontend Pages & AppRouter

#### [NEW] [EventDetailPage.tsx](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/pages/EventDetailPage.tsx)
- Placeholder page component with loading spinner / shell for event detail inspection.

#### [NEW] [SubjectTimelinePage.tsx](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/pages/SubjectTimelinePage.tsx)
- Placeholder page component for entity timeline reconstruction.

#### [NEW] [CorrelationTimelinePage.tsx](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/pages/CorrelationTimelinePage.tsx)
- Placeholder page component for correlation stream visualization.

#### [NEW] [DeadLetterReviewPage.tsx](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/pages/DeadLetterReviewPage.tsx)
- Placeholder page component for DLQ management.

#### [NEW] [AuditExportPage.tsx](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/pages/AuditExportPage.tsx)
- Placeholder page component for audit export generation.

#### [MODIFY] [AppRouter.tsx](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/routes/AppRouter.tsx)
- Import new pages and register the 5 new sub-routes wrapped in `<ProtectedRoute>` and `<AppShell>`.

### Documentation Artifacts

#### [NEW] [Phase4_implementation_plan_prompt_2_6_create_frontend_route_shells.md](file:///c:/Users/aayus/Desktop/GuardianIQ--1/markdown/Phase4_implementation_plan_prompt_2_6_create_frontend_route_shells.md)
- Implementation plan saved in `markdown/`.

## Verification Plan

### Manual Verification
- Verify TypeScript compilation (`tsc --noEmit` or frontend build check if available).
- Validate all 5 routes render cleanly inside `AppShell` with placeholder loading UI.

# Implementation Plan - Enhanced Audit Timeline

We will improve the Audit logs timeline display under the Workflow Scheduler detail page to make it visually richer and more informative. This includes exposing the actor's name/email from the backend and rendering a color-coded vertical timeline in the frontend.

## Proposed Changes

### Backend Component

#### [MODIFY] [phase2_scheduler_routes.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/api/phase2_scheduler_routes.py)
- Modify `/api/v1/audit/events` to:
  1. Map `actor_user_id` to the user's name or email from the `User` table.
  2. Return `actor_name` in each timeline item payload.

---

### Frontend Component

#### [MODIFY] [phase2.ts](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/types/phase2.ts)
- Add `AuditTimelineEvent` interface to explicitly document the response structure:
  ```typescript
  export interface AuditTimelineEvent {
    id: string;
    action_type: string;
    event_summary: string;
    actor_name: string;
    created_at: string;
  }
  ```

#### [MODIFY] [AuditTimelinePanel.tsx](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/components/phase2/AuditTimelinePanel.tsx)
- Redesign the timeline layout to display:
  - Color-coded icons based on `action_type` (e.g., green for `CREATE`/`APPROVE`, blue for standard runs, orange for `REJECT`/`UPDATE`).
  - An inline sub-label showing the actor's username (e.g., `by admin@guardianiq.com` or `by System`).
  - Align spacing, fonts, and borders with the premium design aesthetics of the details panel.

---

## Verification Plan

### Automated Tests
- Run `venv/Scripts/python -m pytest app/tests/test_audit_timeline_api.py` to ensure the timeline api returns `actor_name` and runs successfully.
- Run `npm run typecheck` to verify frontend TypeScript compilation.

### Manual Verification
- View the schedule's Audit tab and inspect the updated vertical timeline layout, color-coded badges, and displayed actor names.

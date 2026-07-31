# Implementation Plan - Prompt 5.4: Build Dead Letter Queue Screen (WBS 4.5.4)

Build the Dead Letter Review screen at `/audit/dead-letter` with a reusable shared `RetryActionButton` component, status filtering (`ALL`, `UNRESOLVED`, `RESOLVED`), failure reason inspection, retry count badges, and retry action calling `POST /api/v1/events/dead-letter/{id}/retry`.

## User Review Required

> [!IMPORTANT]
> **Shared Retry Component**: Creates `frontend/src/components/common/RetryActionButton.tsx` & `.module.css` for consistent, accessible retry actions with loading spinners and error handling.
> **Error Handling**: On retry failure, displays a clear error message in toast/inline alert and keeps the dead letter item in `UNRESOLVED` status per spec section 6.4.

## Proposed Changes

### Shared Components

#### [NEW] [RetryActionButton.tsx](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/components/common/RetryActionButton.tsx)
#### [NEW] [RetryActionButton.module.css](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/components/common/RetryActionButton.module.css)
- Reusable button component handling async retry execution, loading spinner, and error state reporting.

### Audit Service

#### [MODIFY] [auditService.ts](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/services/audit/auditService.ts)
- Add `DeadLetterEvent` type definition.
- Add `fetchDeadLetterEvents(token)` and `retryDeadLetterEvent(token, id)`.

### Frontend Pages

#### [MODIFY] [DeadLetterReviewPage.tsx](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/pages/DeadLetterReviewPage.tsx)
#### [NEW] [DeadLetterReviewPage.module.css](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/pages/DeadLetterReviewPage.module.css)
- Full grid layout displaying dead letter entries, filter tabs (`ALL`, `UNRESOLVED`, `RESOLVED`), search input, retry count badges, failure rationale, and `RetryActionButton`.

### Documentation Artifacts

#### [NEW] [Phase4_implementation_plan_prompt_5_4_build_dead_letter_queue_screen.md](file:///c:/Users/aayus/Desktop/GuardianIQ--1/markdown/Phase4_implementation_plan_prompt_5_4_build_dead_letter_queue_screen.md)
- Implementation plan saved in `markdown/`.

## Verification Plan

### Automated Tests
1. Run `npm run build` in `frontend/` to verify zero TypeScript or CSS module compilation errors.
2. Run backend unit tests (`pytest app/tests/test_dead_letter_apis.py`).

### Manual Verification
1. Navigate to `/audit/dead-letter`.
2. Verify list displays failure reason, retry attempts, and status badges.
3. Click Retry button for an unresolved record and verify status updates to `RESOLVED`.

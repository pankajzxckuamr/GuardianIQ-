# Implementation Plan - Prompt 6.2: E2E Audit Timeline Flow (WBS 4.6.2 / QA4-004)

Create an end-to-end integration test suite `backend/app/tests/test_e2e_correlation_timeline_flow.py` verifying multi-step correlated event flow reconstruction (`GET /api/v1/events/correlation/{correlation_id}`), chronological ordering, parent-child event linkages, and correlation timeline UI integration.

## User Review Required

> [!IMPORTANT]
> **Correlation Chain Verification**:
> 1. Multi-step sequence (`WORKFLOW_RUN_STARTED` → `AGENT_ACTION_BLOCKED` → `WORKFLOW_RUN_COMPLETED`) sharing a single `correlation_id` UUID.
> 2. Database verification: All events store identical `correlation_id` and parent/causation linkages.
> 3. API Verification: `GET /api/v1/events/correlation/{correlation_id}` reconstructs the stream ordered by `occurred_at` ascending.
> 4. UI Verification: `CorrelationTimelinePage.tsx` renders stream with `AuditTimelinePanel` and triggers `EventDrawer.tsx` on row selection.

## Proposed Changes

### Tests

#### [NEW] [test_e2e_correlation_timeline_flow.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/tests/test_e2e_correlation_timeline_flow.py)
- `test_e2e_correlation_timeline_chain_reconstruction` (QA4-004)

### Documentation Artifacts

#### [NEW] [Phase4_implementation_plan_prompt_6_2_e2e_audit_timeline_flow.md](file:///c:/Users/aayus/Desktop/GuardianIQ--1/markdown/Phase4_implementation_plan_prompt_6_2_e2e_audit_timeline_flow.md)
- Implementation plan saved in `markdown/`.

## Verification Plan

### Automated Tests
1. Run `pytest app/tests/test_e2e_correlation_timeline_flow.py -v`.
2. Run full backend test suite (`pytest app/tests/`).

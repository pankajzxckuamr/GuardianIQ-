# Implementation Plan - Prompt 4.3: Implement AuditTimelineService (WBS 4.4.3)

Implement `AuditTimelineService` in `backend/app/modules/audit/timeline_service.py` for query-time reconstruction of subject and correlation audit streams over `governance_events`.

## User Review Required

> [!IMPORTANT]
> **Query-Time Reconstruction (No Derived Table)**: Reconstructs subject timelines and correlation traces dynamically at query time from `governance_events` (not `audit_events`). Per Day 1 Scope Lock, no materialized `audit_timelines` table is introduced.
> **Tenant Isolation & Ordering**: All queries enforce strict `tenant_id` filtering and order events chronologically by `occurred_at`.

## Open Questions

- None.

## Service Architecture

- **`build_subject_timeline(db, tenant_id, entity_type, entity_id, limit)`**:
  Queries `governance_events` where `tenant_id == tenant_id` AND `subject_json->>'entity_type' == entity_type` AND `subject_json->>'entity_id' == entity_id`, ordered by `occurred_at ASC`.
- **`build_correlation_timeline(db, tenant_id, correlation_id, limit)`**:
  Queries `governance_events` where `tenant_id == tenant_id` AND `correlation_id == correlation_id`, ordered by `occurred_at ASC`.

## Proposed Changes

### Backend Implementation

#### [MODIFY] [timeline_service.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/audit/timeline_service.py)
- Implement `AuditTimelineService` class with `build_subject_timeline` and `build_correlation_timeline`.

#### [MODIFY] [router.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/events/router.py)
- Wire timeline endpoints to `AuditTimelineService` and add `GET /api/v1/audit/timeline/{entity_type}/{entity_id}` alias.

#### [NEW] [test_audit_timeline_service.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/tests/test_audit_timeline_service.py)
- Unit test suite for subject and correlation timeline reconstruction.

### Documentation Artifacts

#### [NEW] [Phase4_implementation_plan_prompt_4_3_implement_audittimelineservice.md](file:///c:/Users/aayus/Desktop/GuardianIQ--1/markdown/Phase4_implementation_plan_prompt_4_3_implement_audittimelineservice.md)
- Implementation plan saved in `markdown/`.

## Verification Plan

### Automated / Unit Test Verification
1. Run pytest suite: `pytest app/tests/test_audit_timeline_service.py`
2. Confirm subject timeline ordering, tenant filtering, and correlation trace streams return 200 OK cleanly.

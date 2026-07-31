# Implementation Plan - Prompt 2.3: Create Indexes and Constraints (WBS 4.2.3)

Create Alembic migration to add exact composite, B-tree, and GIN indexes for Phase 4 event store performance optimization and GIN verification.

## User Review Required

> [!IMPORTANT]
> **First GIN Index in Schema**: Creating `idx_events_subject_gin` and `idx_events_actor_gin` using `postgresql_using='gin'`.
> **Migration Revision Chaining**: Creating migration `a3f8921e560d_add_phase4_indexes_and_gin.py` chained from `e4a2b91c801d`.

## Open Questions

- None.

## Index Specifications (Spec Section 8.3)

1. **`idx_events_tenant_time`**: Composite B-tree index on `governance_events(tenant_id, occurred_at DESC)`.
2. **`idx_events_type_time`**: Composite B-tree index on `governance_events(event_type, occurred_at DESC)`.
3. **`idx_events_category_time`**: Composite B-tree index on `governance_events(event_category, occurred_at DESC)`.
4. **`idx_events_correlation`**: Partial index on `governance_events(correlation_id)` WHERE `correlation_id IS NOT NULL`.
5. **`idx_events_subject_gin`**: GIN index on `governance_events(subject_json)` using `postgresql_using='gin'`.
6. **`idx_events_actor_gin`**: GIN index on `governance_events(actor_json)` using `postgresql_using='gin'`.
7. **`idx_outbox_status_retry`**: Composite B-tree index on `event_outbox(status, next_retry_at)`.
8. **`idx_processing_event_consumer`**: Composite B-tree index on `event_processing_log(event_id, consumer_id)`.
9. **`idx_dead_letter_status`**: Composite B-tree index on `event_dead_letter(tenant_id, status)`.

## Proposed Changes

### Backend Database Migration

#### [NEW] [a3f8921e560d_add_phase4_indexes_and_gin.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/db/migrations/versions/a3f8921e560d_add_phase4_indexes_and_gin.py)
- Migration creating all 9 specified composite, partial, and GIN indexes.

### Documentation Artifacts

#### [NEW] [Phase4_implementation_plan_prompt_2_3_create_indexes_and_constraints.md](file:///c:/Users/aayus/Desktop/GuardianIQ--1/markdown/Phase4_implementation_plan_prompt_2_3_create_indexes_and_constraints.md)
- Implementation plan saved in `markdown/`.

## Verification Plan

### Automated / Command Verification
1. Run `alembic upgrade head` in `backend/` directory.
2. Confirm PostgreSQL GIN index creation succeeds without syntax or engine errors.
3. Query `pg_indexes` to verify all 9 index definitions in the dev database.

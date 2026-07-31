# Implementation Plan - Prompt 3.2: Implement EventRepository (WBS 4.3.2)

Implement SQLAlchemy ORM models in `models.py` and `EventRepository` in `repository.py` with append-only semantics, mandatory fail-closed `tenant_id` filtering, and unit test suite in `test_event_repository.py`.

## User Review Required

> [!IMPORTANT]
> **Strict Immutability Guarantee**: `EventRepository` exposes **zero update or delete methods** (`insert_event` is append-only per Spec Section 12).
> **Mandatory Fail-Closed Tenant Isolation**: All query methods require an explicit non-null `tenant_id`. If `tenant_id` is missing/None, a `ValueError` is raised immediately.

## Open Questions

- None.

## Repository Method Specification

1. `insert_event(db: Session, event: GovernanceEvent) -> GovernanceEvent`: Append-only event store writer.
2. `search_events(db: Session, tenant_id: UUID, filters: GovernanceEventSearchFilter) -> Tuple[List[GovernanceEvent], int]`: Paginated filtering across tenant_id, date bounds, taxonomy, subject, actor, correlation, and risk JSON.
3. `get_event_by_id(db: Session, tenant_id: UUID, event_id: UUID) -> Optional[GovernanceEvent]`: Single event lookup with tenant isolation.
4. `get_subject_events(db: Session, tenant_id: UUID, entity_type: str, entity_id: str, limit: int = 100) -> List[GovernanceEvent]`: Entity timeline query.
5. `get_correlation_events(db: Session, tenant_id: UUID, correlation_id: UUID, limit: int = 100) -> List[GovernanceEvent]`: Correlation stream trace query.

## Proposed Changes

### Backend Implementation

#### [NEW] [models.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/events/models.py)
- SQLAlchemy ORM models (`GovernanceEvent`, `EventOutbox`, `EventProcessingLog`, `EventDeadLetter`, `EventSchemaRegistry`, `EventRetentionRule`, `EventExportLog`).

#### [MODIFY] [repository.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/events/repository.py)
- Implement `EventRepository` with append-only and fail-closed tenant query methods.

#### [NEW] [test_event_repository.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/tests/test_event_repository.py)
- Unit tests verifying append-only immutability and mandatory tenant filtering enforcement.

### Documentation Artifacts

#### [NEW] [Phase4_implementation_plan_prompt_3_2_implement_event_repository.md](file:///c:/Users/aayus/Desktop/GuardianIQ--1/markdown/Phase4_implementation_plan_prompt_3_2_implement_event_repository.md)
- Implementation plan saved in `markdown/`.

## Verification Plan

### Automated / Unit Test Verification
1. Run pytest suite: `pytest app/tests/test_event_repository.py`
2. Confirm immutability tests and fail-closed tenant validation pass cleanly.

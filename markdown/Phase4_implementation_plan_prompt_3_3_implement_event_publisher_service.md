# Implementation Plan - Prompt 3.3: Implement EventPublisherService (WBS 4.3.3)

Implement `EventPublisherService` in `backend/app/modules/events/service.py` featuring transactional outbox pattern, actor context enrichment, business-flow correlation ID generation, SHA-256 payload hashing, and unit test suite.

## User Review Required

> [!IMPORTANT]
> **Transactional Outbox Pattern**: Event creation in `governance_events` and outbox queue insertion in `event_outbox` occur within the **exact same database transaction** (atomically committed or rolled back together).
> **Correlation vs HTTP Request ID**: Business correlation IDs are generated as new UUIDs for unlinked flows, keeping business trace chains distinct from transient HTTP `X-Request-ID` headers.
> **Actor Context Reuse**: Employs `get_current_actor_id()` from [audit_listeners.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/shared/audit_listeners.py#L8) and `get_user_context()` from [middleware.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/core/middleware.py#L159).

## Open Questions

- None.

## Service Method Specification

1. `publish_event(db: Session, event_data: GovernanceEventCreate, tenant_id: UUID) -> GovernanceEvent`: Primary entry point executing enrichment, validation, event append, and transactional outbox row creation.
2. `enrich_event(event_data: GovernanceEventCreate, tenant_id: UUID) -> GovernanceEventCreate`: Resolves actor user_id/roles, assigns business correlation_id, sets causation_id, and computes SHA-256 event_hash using [hashing.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/shared/hashing.py).
3. `validate_event(event_data: GovernanceEventCreate) -> bool`: Validates mandatory envelope properties and schema shape.
4. `append_event(db: Session, event_data: GovernanceEventCreate, tenant_id: UUID) -> GovernanceEvent`: Invokes `EventRepository.insert_event` for append-only storage.

## Proposed Changes

### Backend Service Implementation

#### [MODIFY] [service.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/events/service.py)
- Replace stub with complete `EventPublisherService` implementation.

#### [NEW] [test_event_publisher_service.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/tests/test_event_publisher_service.py)
- Unit tests verifying event publishing, outbox atomicity, actor enrichment, SHA-256 hashing, and correlation ID generation.

### Documentation Artifacts

#### [NEW] [Phase4_implementation_plan_prompt_3_3_implement_event_publisher_service.md](file:///c:/Users/aayus/Desktop/GuardianIQ--1/markdown/Phase4_implementation_plan_prompt_3_3_implement_event_publisher_service.md)
- Implementation plan saved in `markdown/`.

## Verification Plan

### Automated / Unit Test Verification
1. Run pytest suite: `pytest app/tests/test_event_publisher_service.py`
2. Verify event and outbox rows are committed together atomically.

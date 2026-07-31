# Implementation Plan - Prompt 3.1: Implement GovernanceEvent Pydantic Schemas (WBS 4.3.1)

Implement Pydantic data schemas for Event Creation, Canonical Event Response, Search Filters, Audit Timelines, Outbox Queue Records, and Dead Letter Queue Records in `backend/app/modules/events/schemas.py`.

## User Review Required

> [!IMPORTANT]
> **Schema Validation Against Frozen Envelope**: All Pydantic models strictly validate against the 20-field canonical event envelope from Prompt 1.3 and Spec Section 6.3.

## Open Questions

- None.

## Schema List Specification

1. **`ActorContext`**: Pydantic schema for `actor_json`.
2. **`SubjectContext`**: Pydantic schema for `subject_json`.
3. **`GovernanceEventCreate`**: Event creation request schema.
4. **`GovernanceEventResponse`**: Full 20-field canonical event response schema (`from_attributes=True`).
5. **`GovernanceEventSearchFilter`**: Search query filters matching Spec Section 6.3 (`start_date`, `end_date`, `event_type`, `event_category`, `subject_type`, `subject_id`, `actor_id`, `correlation_id`, `risk_level`, `source_service`, `classification`).
6. **`TimelineResponse`**: Reconstructed subject/correlation timeline response payload.
7. **`EventOutboxResponse`**: Transactional outbox record schema.
8. **`EventDeadLetterResponse`**: Dead Letter Queue (DLQ) record schema.

## Proposed Changes

### Backend Schemas

#### [MODIFY] [schemas.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/events/schemas.py)
- Replace stub with complete Pydantic v2 schemas and validation models.

### Documentation Artifacts

#### [NEW] [Phase4_implementation_plan_prompt_3_1_implement_governance_event_pydantic_schemas.md](file:///c:/Users/aayus/Desktop/GuardianIQ--1/markdown/Phase4_implementation_plan_prompt_3_1_implement_governance_event_pydantic_schemas.md)
- Implementation plan saved in `markdown/`.

## Verification Plan

### Automated Verification
- Run python schema validation test: `python -c "from app.modules.events.schemas import GovernanceEventResponse, GovernanceEventSearchFilter; print('Schemas Valid!')"`

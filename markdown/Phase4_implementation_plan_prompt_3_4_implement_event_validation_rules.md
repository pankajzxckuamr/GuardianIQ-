# Implementation Plan - Prompt 3.4: Implement Event Validation Rules (WBS 4.3.4)

Implement pre-ingest event validation rules in `backend/app/modules/events/validators.py` for envelope field presence, active schema registry lookup, payload size limits, and secret/PII key rejection.

## User Review Required

> [!IMPORTANT]
> **Pre-Persistence Fail-Fast Guarantee**: All event validation checks execute **before any database transaction** occurs. Any invalid event throws a `ValueError` immediately, preventing partial writes.
> **Secret Key Rejection**: Reuses secret detection keys from `registry/audit_service.py` (`password`, `token`, `secret`, `client_secret`, `api_key`, `private_key`). If unredacted secret keys are present in `payload_json`, validation fails closed.

## Open Questions

- None.

## Validation Rule Specification

1. **Required Fields Check**: Validates non-null presence of `tenant_id`, `event_type`, `event_version`, `actor_json`, `subject_json`, `classification`, `retention_class`.
2. **Schema Registry Active Check**: Queries `event_schema_registry` to confirm `event_type` is present and `is_active` is `True`.
3. **Payload Sensitivity Check**: Scans `payload_json` keys recursively for unredacted sensitive keys (`password`, `token`, `secret`, `client_secret`, `api_key`, `private_key`).
4. **Payload Size Check**: Enforces maximum payload size limit (500 KB).

## Proposed Changes

### Backend Implementation

#### [MODIFY] [validators.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/events/validators.py)
- Implement `EventValidator` class with static validation methods.

#### [MODIFY] [service.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/events/service.py)
- Integrate `EventValidator.validate_event(db, enriched_data)` into `EventPublisherService.publish_event`.

#### [NEW] [test_event_validators.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/tests/test_event_validators.py)
- Unit test suite verifying schema registry lookup, required field checks, secret rejection, and pre-persistence fail-fast behavior.

### Documentation Artifacts

#### [NEW] [Phase4_implementation_plan_prompt_3_4_implement_event_validation_rules.md](file:///c:/Users/aayus/Desktop/GuardianIQ--1/markdown/Phase4_implementation_plan_prompt_3_4_implement_event_validation_rules.md)
- Implementation plan saved in `markdown/`.

## Verification Plan

### Automated / Unit Test Verification
1. Run pytest suite: `pytest app/tests/test_event_validators.py`
2. Confirm invalid events (missing fields, secret keys, inactive schema) are rejected prior to DB write.

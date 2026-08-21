# Implementation Plan - Prompt 4.3: Implement Data Permission Guard and Transformations (WBS 4.3)

Implement the enterprise `DataPermissionGuard` and field-level transformation engine (`MASK`, `REDACT`, `TOKENIZE`, `HASH`), enforcing active `USES_DATA_SOURCE` graph relationships, operation authorizations, classification/sensitivity ceilings (reusing `DataClassification` and `SensitivityLevel`), denied fields filtering, and record limits.

## User Review Required

> [!IMPORTANT]
> **Key Data Governance & Security Rules**:
> 1. **Prerequisite: Active Relationship Graph Check**:
>    - Validates active `USES_DATA_SOURCE` or generic `USES` (target_type in `DATA_SOURCE`/`DATASOURCE`) relationship. Missing/expired links return `Decision.DENY`.
> 2. **Field-Level Classification & Sensitivity Ceilings**:
>    - Reuses `DataClassification` (`PUBLIC` < `INTERNAL` < `CONFIDENTIAL` < `RESTRICTED`) and `SensitivityLevel` (`LOW` < `MEDIUM` < `HIGH` < `CRITICAL`).
>    - Access is blocked if requested fields exceed `max_classification` or `max_sensitivity`.
> 3. **Denied Fields Filtering**:
>    - Denied or unauthorized fields are completely stripped from data queries and payloads.
> 4. **Field Transformation Engine**:
>    - Built-in transformations executed before model or tool exposure:
>      - `MASK`: Partial masking (emails, phones, numbers).
>      - `REDACT`: Full replacement with `[REDACTED]`.
>      - `TOKENIZE`: Deterministic format-preserving token `tok_<hash>`.
>      - `HASH`: Cryptographic SHA-256 digest.
> 5. **Export & Record Limits**:
>    - Enforces maximum record counts on bulk exports.

## Open Questions

- None.

## Proposed Changes

### Data Governance Module

#### [NEW] [backend/app/modules/data_governance/guard.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/data_governance/guard.py)
- Implement `DataTransformer`:
  - `transform_value(val, strategy)`
  - `transform_record(record_dict, field_strategies)`
  - `transform_dataset(records, field_strategies)`
- Implement `DataPermissionGuard`:
  - `evaluate_data_access(tenant_id, agent_id, data_source_id, operation, requested_fields, record_count, as_of)`
  - Returns `DataGuardResult(decision, is_permitted, allowed_fields, denied_fields, transformation_map, transformed_data, reason, violations)`

#### [MODIFY] [backend/app/modules/data_governance/service.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/data_governance/service.py)
- Integrate `DataPermissionGuard` and `DataTransformer` into `DataGovernanceService`.

#### [MODIFY] [backend/app/modules/data_governance/router.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/data_governance/router.py)
- Expose `POST /api/v1/data-governance/evaluate`.

## Verification Plan

### Automated Tests
- Create [backend/app/tests/test_phase5_data_permission_guard.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/tests/test_phase5_data_permission_guard.py):
  1. **Relationship Prerequisite Test**: Verify data access without `USES_DATA_SOURCE` relationship returns `Decision.DENY`.
  2. **Classification Ceiling Test**: Verify agent with `CONFIDENTIAL` max classification attempting to read `RESTRICTED` field returns `Decision.DENY`.
  3. **Transformation Pipeline Test**: Verify `MASK`, `REDACT`, `TOKENIZE`, and `HASH` hooks accurately transform records before exposure.
  4. **Denied Fields Test**: Verify denied fields are stripped from the dataset.
  5. **Bulk Record Limits Test**: Verify exceeding record limits returns `Decision.DENY`.
  6. **Permitted Access Test**: Verify compliant access returns `Decision.ALLOW` or `Decision.ALLOW_WITH_OBLIGATIONS`.

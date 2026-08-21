# Implementation Plan - Prompt 1.2: Freeze v1 Domain Enums and Runtime Contract (WBS 1.2)

Establish single-source-of-truth domain enumerations and the canonical `GovernedRuntimeRequest` / `GovernedRuntimeResponse` runtime contracts across the backend and frontend.

## User Review Required

> [!IMPORTANT]
> **Enum Reuse & Unification Constraints**:
> 1. **Data Classification**: Reuse the existing `DataClassification` (`registry/constants.py`) and `SensitivityLevel` (`shared/enums/sensitivity_level.py`) without defining parallel duplicate classification enums.
> 2. **Shared Engine Enums Module**: Create `backend/app/modules/policy_engine/enums.py` containing:
>    - `PolicyStatus` (`DRAFT`, `ACTIVE`, `PAUSED`, `ARCHIVED`, `RETIRED`)
>    - `VersionStatus` (`DRAFT`, `ACTIVE`, `DEPRECATED`, `ARCHIVED`)
>    - `BindingStatus` (`ACTIVE`, `INACTIVE`, `SUSPENDED`)
>    - `Decision` (`ALLOW`, `DENY`, `MODIFY`, `REQUIRE_APPROVAL`)
>    - `TargetType` (`AGENT`, `TOOL`, `DATA_SOURCE`, `WORKFLOW`, `MODEL`)
>    - `VersionStrategy` (`LATEST`, `PINNED`, `STRICT_LATEST`)
>    - `AutonomyLevel` (`FULL_AUTONOMY`, `HUMAN_IN_THE_LOOP`, `HUMAN_SUPERVISED`, `STRICT_OVERSIGHT`)
>    - `AccessMode` (`READ_ONLY`, `WRITE`, `EXECUTE`, `ADMIN`, `READ_WRITE`)
>    - `DataOperation` (`READ`, `WRITE`, `EXPORT`, `TRANSFORM`, `DELETE`, `AGGREGATE`)
>    - `EnforcementMode` (`BLOCKING`, `MONITORING`, `WARN`, `DRY_RUN`)
> 3. **Canonical Runtime Contracts**:
>    - `GovernedRuntimeRequest` (UUID `request_id`, UUID `correlation_id`, `actor`, `agent`, `workflow`, `model`, `operation`, `tool`, `data_requests`, `facts`, `idempotency_key`).
>    - `GovernedRuntimeResponse` (`request_id`, `correlation_id`, `decision`, `reasons`, `enforced_at`, `modified_payload`, `approval_requirements`, `violations`, `policy_evaluations`).
> 4. **Frontend TypeScript Parity**: Export matching TypeScript enums and request/response interfaces in `frontend/src/types/policy_engine.ts`.

## Open Questions

- None. Enums and contracts match the Step 4 & Policy Engine specifications.

## Proposed Changes

### Backend - Policy Engine Enums & Contracts

#### [NEW] [backend/app/modules/policy_engine/__init__.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/policy_engine/__init__.py)
- Package initializer exporting core enums and schemas.

#### [NEW] [backend/app/modules/policy_engine/enums.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/policy_engine/enums.py)
- Defines frozen v1 enums: `PolicyStatus`, `VersionStatus`, `BindingStatus`, `Decision`, `TargetType`, `VersionStrategy`, `AutonomyLevel`, `AccessMode`, `DataOperation`, `EnforcementMode`.
- Imports and re-exports `DataClassification` and `SensitivityLevel` from existing modules.

#### [NEW] [backend/app/modules/policy_engine/schemas.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/policy_engine/schemas.py)
- Defines Pydantic v2 models for:
  - `GovernedRuntimeRequest`
  - `GovernedRuntimeResponse`
  - Sub-envelopes (`ActorContext`, `AgentContext`, `WorkflowContext`, `ModelContext`, `ToolContext`, `DataRequestContext`, `PolicyEvaluationResult`, `ApprovalRequirement`, `ViolationDetail`).

### Frontend - TypeScript Type Definitions

#### [NEW] [frontend/src/types/policy_engine.ts](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/types/policy_engine.ts)
- TypeScript enums and interfaces for `GovernedRuntimeRequest`, `GovernedRuntimeResponse`, `Decision`, `PolicyStatus`, `VersionStatus`, `BindingStatus`, `TargetType`, `VersionStrategy`, `AutonomyLevel`, `AccessMode`, `DataOperation`, `EnforcementMode`.

### Documentation Artifact

#### [NEW] [docs/Phase 5/Phase5_Frozen_Enums_and_Runtime_Contract.md](file:///c:/Users/aayus/Desktop/GuardianIQ--1/docs/Phase%205/Phase5_Frozen_Enums_and_Runtime_Contract.md)
- Complete reference catalog of all frozen domain enums, JSON schema definitions, and validation rules.

## Verification Plan

### Automated Tests
- Run Python schema validation test verifying:
  - Valid and invalid `GovernedRuntimeRequest` parsing.
  - Strict UUID parsing for `request_id` and `correlation_id`.
  - Serialization and deserialization of all enum values.
- Verify zero symbol collision with existing `AuthorizationDecision` or legacy `AccessMode`.

### Manual Verification
- Validate TypeScript definitions against backend Pydantic models to guarantee exact structural parity.

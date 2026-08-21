# Implementation Plan - Prompt 4.4: Implement Model/Provider Guard (WBS 4.4)

Implement the enterprise `ModelProviderGuard` engine validating agent LLM/AI model invocations against active graph relationships (`USES_MODEL` / `USES`), approved model status & version, provider hosting and data residency restrictions, deployment environment compatibility (`PRODUCTION` vs `DEVELOPMENT`), and restricted data classification compatibility. Blocks unauthorized fallback models.

## User Review Required

> [!IMPORTANT]
> **Key Model Governance & Provider Security Rules**:
> 1. **Prerequisite: Active Relationship Graph Check**:
>    - Validates active `USES_MODEL` or generic `USES` (target_type in `MODEL`/`AI_MODEL`) relationship in `generic_relationships`. Missing/expired links return `Decision.DENY`.
> 2. **Model Status & Version Validation**:
>    - Verifies model status is `ACTIVE`. If specific version requested, validates against model `version`.
> 3. **Environment Compatibility**:
>    - `DEVELOPMENT` or `STAGING` models cannot be invoked in `PRODUCTION` runtime requests.
> 4. **Data Classification & Provider Residency Compatibility**:
>    - If requested context contains `CONFIDENTIAL` or `RESTRICTED` data, external/public hosted providers or providers with incompatible data residency (e.g. cross-border transfer violations) are blocked with `Decision.DENY`.
> 5. **Unauthorized Fallback Model Prevention**:
>    - Fallback models must be explicitly validated against the agent's authorized relationships and governance boundaries.

## Open Questions

- None.

## Proposed Changes

### Model Governance / Agent Boundary Module

#### [NEW] [backend/app/modules/agent_boundary/model_guard.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/agent_boundary/model_guard.py)
- Implement `ModelProviderGuard`:
  - `evaluate_model_invocation(tenant_id, agent_id, model_id, requested_version, environment, data_classification, is_fallback, as_of)`
  - Returns `ModelGuardResult(decision, is_permitted, model, provider, reason, violations, obligations)`

#### [MODIFY] [backend/app/modules/agent_boundary/service.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/agent_boundary/service.py)
- Integrate `ModelProviderGuard` into `AgentBoundaryService`.

#### [MODIFY] [backend/app/modules/agent_boundary/__init__.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/agent_boundary/__init__.py)
- Export `ModelProviderGuard` and `ModelGuardResult`.

## Verification Plan

### Automated Tests
- Create [backend/app/tests/test_phase5_model_provider_guard.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/tests/test_phase5_model_provider_guard.py):
  1. **Relationship Prerequisite Test**: Verify model invocation without `USES_MODEL` relationship returns `Decision.DENY`.
  2. **Environment Compatibility Test**: Verify invoking a `DEVELOPMENT` model in `PRODUCTION` environment returns `Decision.DENY`.
  3. **Data Classification & Provider Incompatibility Test**: Verify sending `RESTRICTED` data to an unapproved/external public provider returns `Decision.DENY`.
  4. **Unauthorized Fallback Model Test**: Verify unlinked fallback model is blocked with `Decision.DENY`.
  5. **Compliant Model Invocation Test**: Verify valid invocation returns `Decision.ALLOW`.

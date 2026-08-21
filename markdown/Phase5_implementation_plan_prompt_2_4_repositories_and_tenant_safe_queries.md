# Implementation Plan - Prompt 2.4: Implement Repositories and Tenant-Safe Query Patterns (WBS 2.4)

Implement robust, tenant-isolated, lifecycle-aware repository layers across Policy Engine, Agent Boundary, Tool Governance, and Data Governance. Integrate strict relationship resolution through `RelationshipRepository.find_active` and `find_targets` respecting temporal validity (`as_of`).

## User Review Required

> [!IMPORTANT]
> **Key Architecture & Security Rules**:
> 1. **Strict Tenant Isolation**:
>    - All queries enforce `tenant_id == tenant_id`. Cross-tenant data leakage is strictly blocked.
> 2. **Temporal Validity (`as_of`) & Status Filtering**:
>    - Every effective entity query accepts an optional `as_of: datetime` (defaulting to `datetime.now(timezone.utc)`).
>    - Enforce `(effective_from <= as_of OR effective_from IS NULL)` AND `(effective_to >= as_of OR effective_to IS NULL)`.
> 3. **Load-Bearing Relationship Resolution**:
>    - Transitive binding and permission lookups MUST call `RelationshipRepository.find_active` / `RelationshipRepository.find_targets` (e.g., discovering tools used by an agent via `USES_TOOL`, or workflows governing an agent via `GOVERNED_BY`).
>    - Bypassing repository methods or querying `status == "ACTIVE"` directly without checking effective dates is strictly forbidden.
> 4. **Policy Version Immutability**:
>    - `PolicyVersionRepository.update_draft` strictly enforces that only `DRAFT` or `IN_REVIEW` versions are mutable. `ACTIVE`, `SUPERSEDED`, and `RETIRED` versions are immutable at repository level.

## Open Questions

- None.

## Proposed Changes

### 1. Common Repository Base & Query Helpers
#### [NEW] [backend/app/modules/policy_engine/query_utils.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/policy_engine/query_utils.py)
- Utility functions for tenant filtering, effective-date range expressions, and pagination.

### 2. Policy Engine Repositories
#### [MODIFY] [backend/app/modules/policy_engine/repository.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/policy_engine/repository.py)
- `PolicyRepository`: Full CRUD, tenant isolation, category & status filters, pagination.
- `PolicyVersionRepository`: Version creation, draft mutation checks, active version resolution, lifecycle transitions (`ACTIVE`, `SUPERSEDED`, `RETIRED`).
- `PolicyRuleRepository`: Order-aware listing, bulk rule insertion.
- `PolicyBindingRepository`: Direct binding queries + transitive binding resolution via `RelationshipRepository`.
- `PolicyExceptionRepository`: Temporal exception checks by target and policy.
- `PolicyEvaluationRepository`: Immutability-compliant evaluation log insertion.

### 3. Agent Boundary & Tool/Data Governance Repositories
#### [MODIFY] [backend/app/modules/agent_boundary/repository.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/agent_boundary/repository.py)
- `AgentBoundaryRepository`: Boundary lifecycle, pagination, and tenant isolation.
#### [MODIFY] [backend/app/modules/tool_governance/repository.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/tool_governance/repository.py)
- `ToolGovernanceRepository`: Capability queries, direct permission queries, and transitive tool permission resolution via `RelationshipRepository.find_targets(..., relationship_type="USES_TOOL")`.
#### [MODIFY] [backend/app/modules/data_governance/repository.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/data_governance/repository.py)
- `DataGovernanceRepository`: Field classification queries, direct permission queries, and transitive data permission resolution via `RelationshipRepository.find_targets(..., relationship_type="USES_DATA_SOURCE")`.

## Verification Plan

### Automated Tests
- Create [backend/app/tests/test_phase5_repositories.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/tests/test_phase5_repositories.py):
  1. **Tenant Isolation Test**: Prove Tenant A cannot read or modify Tenant B's policies, versions, boundaries, or permissions.
  2. **Effective Date / Temporal Lifecycle Test**: Prove that expired relationships (`effective_to < as_of`) and future-dated policies (`effective_from > as_of`) are excluded.
  3. **Policy Version Immutability Test**: Prove attempting to update an `ACTIVE` policy version raises ValueError.
  4. **Transitive Relationship Resolution Test**: Prove `USES_TOOL` and `USES_DATA_SOURCE` active relationships resolve properly using `RelationshipRepository.find_targets`.

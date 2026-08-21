# Implementation Plan - Prompt 1.4: Finalize Physical Schema and Migration Order (WBS 1.4)

Finalize the comprehensive physical schema specifications, DDL constraints, UUID column typing, migration batch sequencing, and immutability guard rules for Phase 5.

## User Review Required

> [!IMPORTANT]
> **Key Schema & Migration Guard Rules**:
> 1. **Mixin Consistency**: All new tables must use `GovernableMixin`, `WorkflowBaseMixin`, or `TenantMixin` from `backend/app/shared/mixins.py`.
> 2. **Strict UUID Typing**: `correlation_id` and `causation_id` across `policy_evaluations`, `runtime_authorizations`, and `runtime_enforcement_log` MUST be typed as `UUID` (not VARCHAR) to support foreign join integrity with `governance_events.correlation_id`.
> 3. **Dedicated `request_id` Column**: All Phase 5 evaluation and runtime tables receive a dedicated indexed `request_id` column (VARCHAR(150) / UUID).
> 4. **Four-Part Migration Sequence**:
>    - **Batch A (Core Policy Tables)**: `governance_policies`, `policy_versions`, `policy_rules`, `policy_exceptions`.
>    - **Batch B (Agent Boundary & Data Governance Tables)**: `agent_runtime_boundaries`, `tool_capabilities`, `agent_tool_permissions`, `data_source_fields`, `agent_data_permissions`.
>    - **Batch C (`policy_bindings` ALTER + Repoint)**: Add `version_strategy`, `pinned_policy_version_id`, `condition_json`, and repoint FK to `governance_policies.id`.
>    - **Batch D (Runtime Enforcement Logs & Immutability Trigger)**: `policy_evaluations`, `policy_rule_evaluations`, `enforcement_decisions`, `runtime_authorizations`, `runtime_enforcement_log`, `policy_approvals`, plus applying the existing `prevent_update_delete()` trigger to `governance_events`.
> 5. **`policy_versions` Immutability Rule**: Do **not** attach SQL database triggers to `policy_versions` (since DRAFT/IN_REVIEW versions require edits). Enforce immutability purely at the repository/service layer (reject updates once status is ACTIVE, DEPRECATED, or ARCHIVED).

## Open Questions

- None.

## Proposed Deliverables & Artifacts

### Documentation & DDL Specs

#### [NEW] [docs/Phase 5/Phase5_Physical_Schema_and_Migration_Plan.md](file:///c:/Users/aayus/Desktop/GuardianIQ--1/docs/Phase%205/Phase5_Physical_Schema_and_Migration_Plan.md)
- Complete specification containing:
  - Exact DDL definitions for all 15 tables with column types, nullable flags, defaults, FKs, and indexes.
  - Mixin lineage mapping.
  - Migration sequence, roll-forward, and rollback specifications.
  - Immutability trigger integration and repository-layer immutability rules.

#### [NEW] [Phase5_implementation_plan_prompt_1_4_physical_schema_and_migration_order.md](file:///c:/Users/aayus/Desktop/GuardianIQ--1/markdown/Phase5_implementation_plan_prompt_1_4_physical_schema_and_migration_order.md)
- Standardized implementation plan saved in `markdown/`.

## Verification Plan

### Manual Verification
- Review DDL against `backend/app/shared/mixins.py` and `database/ddl/V2_FIX_003__missing_triggers.sql`.
- Verify every foreign key relationship is indexed and UUID fields match across modules.

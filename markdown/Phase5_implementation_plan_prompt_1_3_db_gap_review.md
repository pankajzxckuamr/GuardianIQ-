# Implementation Plan - Prompt 1.3: DB Gap Review Against Existing Phase 0–4 Schema (WBS 1.3)

Conduct and finalize the database gap review against existing Phase 0–4 schemas, establishing the migration roadmap, table reuse mapping, relationship conventions, and repository resolution patterns.

## User Review Required

> [!IMPORTANT]
> **Key Database & Architecture Alignment Findings**:
> 1. **`policy_bindings` (Existing Table Reuse)**:
>    - Already defined in `backend/app/modules/relationship/models.py` on `WorkflowBaseMixin` (0 rows).
>    - Needs `ALTER TABLE` to add: `version_strategy`, `pinned_policy_version_id`, `condition_json` and repoint `policy_id` FK to `governance_policies.id`.
> 2. **Fresh Tables to Create (6 New Policy Tables + 1 Data Source Fields Table + 1 Runtime Approval Table)**:
>    - `governance_policies` (with `GovernableMixin` for `owner_user_id` parity)
>    - `policy_versions`
>    - `policy_rules`
>    - `policy_evaluations`
>    - `policy_rule_evaluations`
>    - `policy_exceptions`
>    - `enforcement_decisions`
>    - `data_source_fields`
>    - `policy_approvals` (dedicated runtime approvals bypassing legacy `approvals` FK restriction)
> 3. **`evidence_links` Reuse**:
>    - Exists in `relationship/models.py` (0 rows, read-only GET routes). Phase 5 becomes its first active writer for obligation and policy evaluation evidence links.
> 4. **Relationship Literals & Graph Semantics**:
>    - `GOVERNED_BY` is standard.
>    - `USES_MODEL`, `USES_TOOL`, `USES_DATA_SOURCE` (and generic `"USES"` with `target_type`) supported.
>    - `PARTICIPATES_IN_WORKFLOW` is the real literal (not `PARTICIPATES_IN`).
>    - `REQUIRES_APPROVAL` is an evaluation decision outcome, not a graph relationship edge.
> 5. **Centralized Relationship Resolution**:
>    - Phase 5 binding resolvers and boundary guards MUST call centralized `RelationshipRepository.find_active` / `RelationshipRepository.find_targets` (respecting `effective_from`/`effective_to` temporal windows), avoiding legacy bugs where status was hardcoded to `"ACTIVE"` while ignoring effective dates.

## Open Questions

- None. Gap assessment is finalized and aligned with the architectural specifications.

## Proposed Deliverables & Artifacts

### Documentation & Gap Assessment

#### [NEW] [docs/Phase 5/Phase5_DB_Gap_Assessment_and_Schema_Mapping.md](file:///c:/Users/aayus/Desktop/GuardianIQ--1/docs/Phase%205/Phase5_DB_Gap_Assessment_and_Schema_Mapping.md)
- Complete database gap assessment report detailing:
  - Table-by-table reuse vs new creation matrix.
  - Column delta specifications for `policy_bindings` ALTER.
  - Foreign key and index mappings.
  - Relationship taxonomy and resolution patterns using `RelationshipRepository`.
  - Ownership synchronization strategy (`GovernableMixin` -> `object_responsibilities`).

#### [NEW] [Phase5_implementation_plan_prompt_1_3_db_gap_review.md](file:///c:/Users/aayus/Desktop/GuardianIQ--1/markdown/Phase5_implementation_plan_prompt_1_3_db_gap_review.md)
- Standardized implementation plan saved in `markdown/`.

## Verification Plan

### Manual Verification
- Validate the schema gap matrix against `backend/app/db/base.py`, `backend/app/modules/relationship/models.py`, and `backend/app/modules/approval/models.py`.
- Confirm no collisions exist for table names, foreign keys, or enum types.

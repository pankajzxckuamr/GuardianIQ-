# Implementation Plan - Prompt 1.4: Review Phase 0–3 Data Dependencies (WBS 4.1.5)

Audit and document Phase 0–3 database dependencies to ensure `governance_events` does not duplicate `audit_events`, and confirm subject table decoupling without schema changes.

## User Review Required

> [!IMPORTANT]
> **Coexistence Strategy**: `audit_events` remains untouched to serve existing legacy writers. `governance_events` will be created as the dedicated Phase 4 event store.
> **Schema Decoupling**: All subject entity relationships are referenced loosely via `subject_json` (type + UUID string), requiring **zero schema modifications** to existing Phase 0-3 tables.

## Open Questions

- None.

## Dependency Review Summary

### 1. Dual Audit Strategy: Coexistence of `audit_events` & `governance_events`
- **`audit_events`**: Retains existing structure ([models.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/audit/models.py#L7)) and continues to receive activity logs from legacy writers without alteration.
- **`governance_events`**: New append-only, rich, 20-field event store that handles Phase 4 event-driven governance, outbox dispatching, and timeline reconstruction.

### 2. Verified Subject Entity Reference Points (10 Entities)
Phase 4 events will point at the following 10 existing system entities via `subject_json` payload context:
1. `ai_models.id` (`backend/app/modules/registry/models.py`)
2. `agents.id` (`backend/app/modules/registry/models.py`)
3. `tools.id` (`backend/app/modules/registry/models.py`)
4. `workflows.id` (`backend/app/modules/workflow_scheduler/models.py`)
5. `generic_relationships.id` (`backend/app/modules/relationship/models.py`)
6. `workflow_runs.id` (`backend/app/modules/workflow_execution/models.py`)
7. `workflow_schedules.id` (`backend/app/modules/workflow_scheduler/models.py`)
8. `policies.id` (`backend/app/modules/policy/models.py`)
9. `policy_bindings.id` (`backend/app/modules/policy/models.py`)
10. `evidence_links.id` (`backend/app/modules/relationship/models.py`)

### 3. Non-Invasive Reference Confirmation
- All 10 subject tables require **NO DDL or schema changes**.
- `governance_events` references subjects via `subject_json = {"entity_type": "ai_models", "entity_id": "<uuid>"}` instead of rigid foreign key constraints.

## Proposed Changes

### Documentation Artifacts

#### [NEW] [Phase4_Data_Dependency_Review.md](file:///c:/Users/aayus/Desktop/GuardianIQ--1/docs/Phase%204/Phase4_Data_Dependency_Review.md)
- Complete dependency review document covering the dual audit coexistence model, full list of 10 subject entity targets, and schema decoupling sign-off.

#### [NEW] [Phase4_implementation_plan_prompt_1_4_review_phase_0_3_data_dependencies.md](file:///c:/Users/aayus/Desktop/GuardianIQ--1/markdown/Phase4_implementation_plan_prompt_1_4_review_phase_0_3_data_dependencies.md)
- Implementation plan saved in the project `markdown/` folder.

## Verification Plan

### Manual Verification
- Review [Phase4_Data_Dependency_Review.md](file:///c:/Users/aayus/Desktop/GuardianIQ--1/docs/Phase%204/Phase4_Data_Dependency_Review.md).
- Cross-reference subject entity table definitions across backend modules.

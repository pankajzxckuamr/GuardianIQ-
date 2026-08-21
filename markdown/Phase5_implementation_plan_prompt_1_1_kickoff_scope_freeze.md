# Implementation Plan - Prompt 1.1: Kickoff and Implementation Scope Freeze (WBS 1.1)

Freeze the one-week MVP scope for Phase 5 (Policy ENFORCE: Policy Binding Resolution & Agent Boundary Runtime Enforcement Engine) and establish a signed sprint scope note and architectural decision log.

## User Review Required

> [!IMPORTANT]
> **Key Structural Decisions & Sprint Constraints**:
> 1. **`policy_bindings` Table**: Existing table (0 rows) will receive an `ALTER` + foreign key repoint, rather than creating a new duplicate table.
> 2. **Enforcement Call Site**: The primary enforcement call site is `AgentRuntimeService.invoke_agent` (already live). Task 5.2 rewires this call site; it does not build a parallel or duplicate gateway.
> 3. **Approval Model Isolation**: The legacy `approvals` table cannot be reused directly due to a non-nullable `recommendation_id` FK constraint. Task 5.4 introduces a dedicated runtime approval record model (`policy_approvals` / `enforcement_approvals`).
> 4. **Escalation Module Stubbing**: There is no dedicated escalation module in the current architecture. Task 5.4 stubs escalation via the existing notification service; a full escalation engine is out of scope for this sprint.

## Open Questions

- None. Requirements, corrections, and spec baselines are strictly aligned with Phase 5 documentation.

## Scope Lock Summary

### In-Scope Modules & Components (Phase 5 MVP)
1. **Core Enums & Canonical Envelopes (WBS 1.2, 5.1)**:
   - Shared enum definitions (`PolicyStatus`, `VersionStatus`, `BindingStatus`, `Decision`, `TargetType`, `VersionStrategy`, `AutonomyLevel`, `AccessMode`, `DataOperation`, `EnforcementMode`).
   - Reuse existing `DataClassification`/`SensitivityLevel` enums without duplication.
   - Canonical `GovernedRuntimeRequest` and `GovernedRuntimeResponse` contracts with UUID correlation/request IDs.
2. **Database Schema & Migrations (WBS 2.1 - 2.4)**:
   - Tables: `governance_policies`, `policy_versions`, `policy_rules`, `policy_evaluations`, `policy_rule_evaluations`, `policy_exceptions`, `enforcement_decisions`, `data_source_fields`, and dedicated runtime approval records.
   - Migration: Alembic migration altering existing `policy_bindings` (adding `version_strategy`, `pinned_policy_version_id`, `condition_json` and FK repoint).
   - Relationship integration (`GOVERNED_BY`, `USES_MODEL`, `USES_TOOL`, `USES_DATA_SOURCE`, `PARTICIPATES_IN_WORKFLOW`).
3. **Policy Engine & Boundary Enforcement Services (WBS 3.1 - 4.4)**:
   - Policy repository and version lifecycle manager.
   - Deterministic policy binding resolver and rule evaluation engine.
   - Agent tool boundary validator (RBAC/ABAC, schema validation, autonomy limits).
   - Data access policy evaluator (data classification, column/row filtering, sensitivity checks).
4. **Runtime Integration & Pipeline Rewiring (WBS 5.1 - 5.5)**:
   - `GovernedRuntimeContextBuilder` constructing runtime context.
   - Integration into `AgentRuntimeService.invoke_agent`.
   - Event publishing via Phase 4 `EventPublisherService` for all policy evaluations and enforcement decisions.
   - Two-layer approval workflow integration for conditional approvals.
5. **Frontend Simulation & Policy Management UI (WBS 6.1 - 6.4)**:
   - Policy Registry / Editor view for managing policies, versions, and rules.
   - Policy Binding manager UI (linking agents/tools/data to policies).
   - Agent Boundary & Enforcement Simulation test workbench.
   - Live audit & decision history timeline integration.
6. **E2E Validation & Quality Gates (WBS 7.1 - 7.5)**:
   - Comprehensive test suite covering allow, deny, modify, and require_approval decisions.
   - Immutability and tamper-resistance verification.
   - Handover package and release candidate sign-off.

### Out-of-Scope Items (Deferred / Non-Goals)
1. **Stand-alone Escalation Module**: Full dynamic escalation management workflow (stubbed via notification service).
2. **External Policy Engine Offloading**: Offloading to external OPA / Cedar servers (pure deterministic Python in-engine evaluation for MVP).
3. **Dynamic ML Content Safety Filtering**: Real-time LLM token stream filtering / prompt injection ML classifiers (rule/metadata/tool boundary enforcement in scope).
4. **Full Replay & State Rewind**: Historical policy state time-travel execution.

## Proposed Changes

### Documentation & Scope Artifacts

#### [NEW] [Phase5_MVP_Scope_Lock_and_Decision_Log.md](file:///c:/Users/aayus/Desktop/GuardianIQ--1/docs/Phase%205/Phase5_MVP_Scope_Lock_and_Decision_Log.md)
- Complete signed-off document recording:
  - MVP scope baseline and boundary freeze.
  - Architectural decision log with structural facts (a, b, c) and `policy_bindings` ALTER confirmation.
  - Branching and DB environment strategy.
  - API naming conventions and event taxonomy alignment.
  - Definition of Done (DoD) and acceptance gates.

#### [NEW] [Phase5_implementation_plan_prompt_1_1_kickoff_scope_freeze.md](file:///c:/Users/aayus/Desktop/GuardianIQ--1/markdown/Phase5_implementation_plan_prompt_1_1_kickoff_scope_freeze.md)
- Standardized task implementation plan saved to the project `markdown/` repository directory.

## Verification Plan

### Manual Verification
- Review [Phase5_MVP_Scope_Lock_and_Decision_Log.md](file:///c:/Users/aayus/Desktop/GuardianIQ--1/docs/Phase%205/Phase5_MVP_Scope_Lock_and_Decision_Log.md) against:
  - Step 4 Spec (`docs/Phase 5/01GuardianIQ_Step4_End_to_End_Engineering_Implementation_Specification.pdf`)
  - Policy Binding Spec (`docs/Phase 5/02GuardianIQ_Policy_Binding_Resolution_Runtime_Enforcement_Engine_Implementation_Specification.pdf`)
  - Agent Boundary Spec (`docs/Phase 5/03GuardianIQ_Agent_Boundary_Tool_Data_Access_Enforcement_Engine_End_to_End_Engineering_Implementation_Specification.pdf`)
- Verify all 4 structural decisions are clearly itemized in the Decision Log.

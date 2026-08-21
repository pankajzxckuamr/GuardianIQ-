# Implementation Plan - Prompt 2.1: Create and Run PostgreSQL Migrations (WBS 2.1)

Create, execute, and verify all Phase 5 Alembic database migrations across policy engine, agent boundaries, `policy_bindings` alteration, runtime enforcement logs, and audit immutability triggers. Update core audit event enums.

## User Review Required

> [!IMPORTANT]
> **Migration Batching & Execution Strategy**:
> 1. **Four Modular Migration Batches**:
>    - `..._phase5_policy_engine_tables.py`: Creates `governance_policies`, `policy_versions`, `policy_rules`, `policy_exceptions`.
>    - `..._phase5_agent_boundary_tables.py`: Creates `agent_runtime_boundaries`, `tool_capabilities`, `agent_tool_permissions`, `data_source_fields`, `agent_data_permissions`.
>    - `..._phase5_alter_policy_bindings.py`: Alters `policy_bindings` (adds `version_strategy`, `pinned_policy_version_id`, `condition_json`, and repoints `policy_id` FK to `governance_policies.id`).
>    - `..._phase5_runtime_enforcement_tables.py`: Creates `policy_evaluations`, `policy_rule_evaluations`, `enforcement_decisions`, `runtime_authorizations`, `runtime_enforcement_log`, `policy_approvals`, and attaches the existing `prevent_update_delete()` trigger to `governance_events`.
> 2. **Audit Event Enum Expansions**:
>    - Add Phase 5 event types (`POLICY_CREATED`, `POLICY_ACTIVATED`, `POLICY_BINDING_CREATED`, `POLICY_EVALUATION_COMPLETED`, `POLICY_VIOLATION_DETECTED`, `AGENT_ACTION_BLOCKED`, `TOOL_ACCESS_DENIED`, `DATA_ACCESS_DENIED`, `DATA_ACCESS_MASKED`, `AUTONOMY_CAP_EXCEEDED`, `RATE_LIMIT_EXCEEDED`, `POLICY_APPROVAL_REQUESTED`, `POLICY_APPROVAL_GRANTED`, `POLICY_APPROVAL_REJECTED`, `POLICY_OVERRIDE_APPLIED`) into `backend/app/shared/enums/audit_event_type.py` and `backend/app/modules/audit/event_codes.py`.
> 3. **SQLAlchemy Declarative Models**:
>    - Implement SQLAlchemy models in `backend/app/modules/policy_engine/models.py` and `backend/app/modules/agent_boundary/models.py`.
>    - Register all new models in `backend/app/db/base.py`.
> 4. **Migration & Rollback Verification**:
>    - Execute `alembic upgrade head`.
>    - Test rollback `alembic downgrade a3f8921e560d` and re-upgrade to `head` to prove clean idempotency and reversibility.

## Open Questions

- None.

## Proposed Changes

### Database Migrations

#### [NEW] [backend/app/db/migrations/versions/5a10001_phase5_policy_engine_tables.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/db/migrations/versions/5a10001_phase5_policy_engine_tables.py)
#### [NEW] [backend/app/db/migrations/versions/5a10002_phase5_agent_boundary_tables.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/db/migrations/versions/5a10002_phase5_agent_boundary_tables.py)
#### [NEW] [backend/app/db/migrations/versions/5a10003_phase5_alter_policy_bindings.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/db/migrations/versions/5a10003_phase5_alter_policy_bindings.py)
#### [NEW] [backend/app/db/migrations/versions/5a10004_phase5_runtime_enforcement_tables.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/db/migrations/versions/5a10004_phase5_runtime_enforcement_tables.py)

### Backend Models & Enums

#### [NEW] [backend/app/modules/policy_engine/models.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/policy_engine/models.py)
- Models: `GovernancePolicy`, `PolicyVersion`, `PolicyRule`, `PolicyException`, `PolicyEvaluation`, `PolicyRuleEvaluation`, `EnforcementDecision`, `PolicyApproval`.

#### [NEW] [backend/app/modules/agent_boundary/models.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/agent_boundary/models.py)
- Models: `AgentRuntimeBoundary`, `ToolCapability`, `AgentToolPermission`, `DataSourceField`, `AgentDataPermission`, `RuntimeAuthorization`, `RuntimeEnforcementLog`.

#### [MODIFY] [backend/app/modules/relationship/models.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/relationship/models.py)
- Update `PolicyBinding` model with `version_strategy`, `pinned_policy_version_id`, `condition_json` and repoint `policy_id` FK.

#### [MODIFY] [backend/app/shared/enums/audit_event_type.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/shared/enums/audit_event_type.py)
- Add Phase 5 event types.

#### [MODIFY] [backend/app/modules/audit/event_codes.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/audit/event_codes.py)
- Add Phase 5 policy and boundary event codes.

#### [MODIFY] [backend/app/db/base.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/db/base.py)
- Import and register all Phase 5 models.

## Verification Plan

### Automated Tests
- Run `alembic upgrade head` to apply migrations.
- Run `alembic downgrade a3f8921e560d` to test rollback.
- Re-run `alembic upgrade head` to re-apply.
- Run test script verifying table presence, indexes, FK constraints, and trigger behavior.

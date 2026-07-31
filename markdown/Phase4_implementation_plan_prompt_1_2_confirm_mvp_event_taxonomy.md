# Implementation Plan - Prompt 1.2: Confirm MVP Event Taxonomy (WBS 4.1.3)

Select and map the MVP subset of governance event types grouped by category, cross-referencing existing producer audit hooks and identifying missing hook modules.

## User Review Required

> [!IMPORTANT]
> **Event Taxonomy Classification**: Confirming the MVP event catalogue structure across 9 categories and identifying modules requiring fresh hooks in Day 4.

## Open Questions

- None.

## Taxonomy Summary

### 9 Event Categories & Producer Module Mapping

| Category | MVP Event Types | Producer Module | Existing Hook Status |
| :--- | :--- | :--- | :--- |
| **Identity** | `USER_LOGIN`, `USER_LOGOUT`, `ROLE_ASSIGNED`, `PERMISSION_REVOKED` | `auth` / `tenant` | ❌ **No existing hook** (Needs new hook in Day 4) |
| **Registry** | `MODEL_REGISTERED`, `MODEL_UPDATED`, `AGENT_REGISTERED`, `AGENT_UPDATED` | `registry` | ⚠️ Partial lifecycle events (Needs standard outbox hook) |
| **Relationship** | `RELATIONSHIP_CREATED`, `RELATIONSHIP_DELETED`, `OWNERSHIP_TRANSFERRED` | `relationship` | ✅ [audit_service.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/relationship/audit_service.py) (`RelationshipAuditService`) |
| **Workflow** | `WORKFLOW_CREATED`, `WORKFLOW_SCHEDULED`, `WORKFLOW_RUN_STARTED`, `WORKFLOW_RUN_COMPLETED`, `WORKFLOW_RUN_FAILED` | `workflow_scheduler` & `workflow_execution` | ✅ Call sites in [service.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/workflow_scheduler/service.py) & [service.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/workflow_execution/service.py) |
| **Policy** | `POLICY_CREATED`, `POLICY_UPDATED`, `POLICY_EVALUATED`, `POLICY_VIOLATED` | `policy` | ❌ **No existing hook** (Needs new hook in Day 4) |
| **Approval** | `APPROVAL_REQUESTED`, `APPROVAL_GRANTED`, `APPROVAL_REJECTED` | `approval` | ❌ **No existing hook** (Needs new hook in Day 4) |
| **Agent** | `AGENT_STEP_STARTED`, `AGENT_STEP_COMPLETED`, `AGENT_TOOL_CALLED` | `agent_runtime` | ✅ [boundary_checker.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/agent_runtime/boundary_checker.py) (`BoundaryChecker`) |
| **Audit** | `AUDIT_TIMELINE_QUERIED`, `AUDIT_EXPORT_GENERATED` | `audit` | ⚠️ Existing audit logger (To be refactored into event emitter) |
| **Violation** | `BOUNDARY_BREACH_ATTEMPTED`, `UNAUTHORIZED_ACCESS_BLOCKED` | `agent_runtime` / `authorization` | ✅ [boundary_checker.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/agent_runtime/boundary_checker.py) |

## Proposed Changes

### Documentation Artifacts

#### [NEW] [Phase4_MVP_Event_Taxonomy.md](file:///c:/Users/aayus/Desktop/GuardianIQ--1/docs/Phase%204/Phase4_MVP_Event_Taxonomy.md)
- Approved event catalogue document detailing all MVP event types, schemas, producer modules, payload contracts, and audit hook mappings.

#### [NEW] [Phase4_implementation_plan_prompt_1_2_confirm_mvp_event_taxonomy.md](file:///c:/Users/aayus/Desktop/GuardianIQ--1/markdown/Phase4_implementation_plan_prompt_1_2_confirm_mvp_event_taxonomy.md)
- Implementation plan saved in the project `markdown/` folder.

## Verification Plan

### Manual Verification
- Review approved event catalogue table in [Phase4_MVP_Event_Taxonomy.md](file:///c:/Users/aayus/Desktop/GuardianIQ--1/docs/Phase%204/Phase4_MVP_Event_Taxonomy.md).
- Cross-reference with Phase 4 spec Appendix 18.1 catalogue.

# Implementation Plan - Prompt 5.5: Extend Governance Event Integration (WBS 5.5)

Extend the governance event publishing infrastructure to emit structured, categorized, and correlation-linked audit events across the complete enforcement lifecycle: `POLICY_EVALUATED`/`TRIGGERED`, `AGENT_ACTION_REQUESTED`/`VALIDATED`/`BLOCKED`, `TOOL_ACCESS_ATTEMPTED`/`DENIED`, `DATA_ACCESS_REQUESTED`/`DENIED`, `DATA_TRANSFORMATION_APPLIED`, `MODEL_INVOCATION_BLOCKED`, `ACTION_EXECUTED`/`FAILED`.

## User Review Required

> [!IMPORTANT]
> **Key Event Registration & Privacy Guarantees**:
> 1. **Strict Category Assignment (`event_category` NOT NULL)**:
>    - Registers schemas in `event_schema_registry` for all 13 Phase 5 governance events mapped to valid categories:
>      - `POLICY_EVALUATED`, `POLICY_TRIGGERED` $\rightarrow$ `ENFORCEMENT`
>      - `AGENT_ACTION_REQUESTED`, `AGENT_ACTION_VALIDATED`, `AGENT_ACTION_BLOCKED` $\rightarrow$ `AGENT_RUNTIME`
>      - `TOOL_ACCESS_ATTEMPTED`, `TOOL_ACCESS_DENIED` $\rightarrow$ `TOOL_GOVERNANCE`
>      - `DATA_ACCESS_REQUESTED`, `DATA_ACCESS_DENIED`, `DATA_TRANSFORMATION_APPLIED` $\rightarrow$ `DATA_GOVERNANCE`
>      - `MODEL_INVOCATION_BLOCKED` $\rightarrow$ `AGENT_BOUNDARY`
>      - `ACTION_EXECUTED`, `ACTION_FAILED` $\rightarrow$ `RUNTIME`
> 2. **Correlation & Causation Linkage**:
>    - Every emitted event carries the unified `correlation_id` of the runtime request/session, establishing a single traceable audit chain from request to decision to target execution.
> 3. **Payload Sanitization & Secret Redaction**:
>    - Ensures zero raw sensitive tokens or unredacted secrets in `payload_json`.

## Open Questions

- None.

## Proposed Changes

### Events & Enforcement Modules

#### [MODIFY] [backend/app/db/seed_phase5.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/db/seed_phase5.py)
- Register all 13 Phase 5 event types in `event_schema_registry` with non-null `event_category` and schema definitions.

#### [NEW] [backend/app/modules/enforcement/event_integration.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/enforcement/event_integration.py)
- Implement `GovernanceEventEmitter` with helper methods to publish:
  - Policy events (`POLICY_EVALUATED`, `POLICY_TRIGGERED`)
  - Agent runtime events (`AGENT_ACTION_REQUESTED`, `AGENT_ACTION_VALIDATED`, `AGENT_ACTION_BLOCKED`)
  - Tool events (`TOOL_ACCESS_ATTEMPTED`, `TOOL_ACCESS_DENIED`)
  - Data governance events (`DATA_ACCESS_REQUESTED`, `DATA_ACCESS_DENIED`, `DATA_TRANSFORMATION_APPLIED`)
  - Model safety events (`MODEL_INVOCATION_BLOCKED`)
  - Execution lifecycle events (`ACTION_EXECUTED`, `ACTION_FAILED`)
- Integrate sanitization to prevent sensitive payload leakage.

#### [MODIFY] [backend/app/modules/enforcement/__init__.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/enforcement/__init__.py)
- Export `GovernanceEventEmitter`.

## Verification Plan

### Automated Tests
- Create [backend/app/tests/test_phase5_governance_event_integration.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/tests/test_phase5_governance_event_integration.py):
  1. **Complete Event Chain Correlation**: Publish complete lifecycle chain (`AGENT_ACTION_REQUESTED` $\rightarrow$ `POLICY_EVALUATED` $\rightarrow$ `DATA_TRANSFORMATION_APPLIED` $\rightarrow$ `ACTION_EXECUTED`) and verify they share identical `correlation_id` and have valid `event_category`.
  2. **Interception & Block Events**: Verify `TOOL_ACCESS_DENIED`, `DATA_ACCESS_DENIED`, `MODEL_INVOCATION_BLOCKED`, `AGENT_ACTION_BLOCKED` events are published with violation reasons and without raw secrets.
  3. **Schema Registry Validation**: Verify all 13 event types pass `EventValidator` schema checks and transactional outbox persistence.

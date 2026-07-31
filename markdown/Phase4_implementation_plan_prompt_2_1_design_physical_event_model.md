# Implementation Plan - Prompt 2.1: Design the Phase 4 Physical Event Model (WBS 4.2.1)

Design the PostgreSQL DDL for 7 core Phase 4 event tables using the frozen canonical envelope from Prompt 1.3, confirming zero materialized timeline tables for MVP.

## User Review Required

> [!IMPORTANT]
> **Tenant ID Constraint**: `tenant_id` across all event tables strictly adheres to `UUID NOT NULL REFERENCES users(id)`, matching [TenantMixin](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/shared/mixins.py#L6-L10).
> **Query-Time Timeline Reconstruction**: Confirming that **NO `audit_timelines` materialized table** is designed or created this sprint; audit timelines will be dynamically reconstructed at query time per Spec Section 7.2.

## Open Questions

- None.

## DDL Architecture Summary (7 Core Tables)

1. **`governance_events`**: Immutable event store with JSONB columns for `actor_json`, `subject_json`, `risk_context_json`, `policy_context_json`, and `payload_json`, indexed by `tenant_id`, `event_type`, `occurred_at`, and `event_hash`.
2. **`event_outbox`**: Transactional outbox pattern queue storing pending/dispatched/failed messages.
3. **`event_processing_log`**: Processing execution log tracking consumer idempotency and execution latency.
4. **`event_dead_letter`**: Dead Letter Queue (DLQ) table tracking failed outbox dispatches requiring operator intervention.
5. **`event_schema_registry`**: Versioned JSON Schema definition table for event payload validation.
6. **`event_retention_rules`**: Category-level log retention policies (`STANDARD_90_DAYS`, `COMPLIANCE_7_YEARS`).
7. **`event_export_log`**: Export audit log recording generated export files, hashes, filters, and user context.

## Proposed Changes

### Documentation Artifacts

#### [NEW] [Phase4_Physical_Event_Model_DDL.md](file:///c:/Users/aayus/Desktop/GuardianIQ--1/docs/Phase%204/Phase4_Physical_Event_Model_DDL.md)
- Complete PostgreSQL DDL design document containing SQL table definitions, constraints, composite indexes, JSONB GIN indexes, and query-time timeline reconstruction design.

#### [NEW] [Phase4_implementation_plan_prompt_2_1_design_physical_event_model.md](file:///c:/Users/aayus/Desktop/GuardianIQ--1/markdown/Phase4_implementation_plan_prompt_2_1_design_physical_event_model.md)
- Implementation plan saved in the project `markdown/` folder.

## Verification Plan

### Manual Verification
- Review [Phase4_Physical_Event_Model_DDL.md](file:///c:/Users/aayus/Desktop/GuardianIQ--1/docs/Phase%204/Phase4_Physical_Event_Model_DDL.md).
- Validate column types, JSONB fields, foreign keys, and indexes against Phase 4 Spec Section 8.2 & 8.4.

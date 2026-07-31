# Implementation Plan - Prompt 1.3: Freeze the Canonical Event Envelope (WBS 4.1.4)

Freeze the canonical 20-field `governance_events` envelope specification (Phase 4 Spec Section 8.2), confirming `tenant_id` alignment with `TenantMixin`, and output a Pydantic schema draft for sign-off.

## User Review Required

> [!IMPORTANT]
> **Tenant ID Constraint Confirmation**: `tenant_id` is strictly typed as `UUID(as_uuid=True)` with a foreign key constraint to `users.id` (`NOT NULL`), matching [mixins.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/shared/mixins.py#L6-L10).

## Open Questions

- None.

## Envelope Specification Summary

The canonical event envelope freezes all 20 required governance fields:
1. `event_id`: UUID (Primary Key, default uuid4)
2. `tenant_id`: UUID (FK -> `users.id`, `nullable=False`, matching `TenantMixin`)
3. `event_type`: String (e.g. `"WORKFLOW_RUN_STARTED"`)
4. `event_category`: String (e.g. `"Workflow"`)
5. `event_version`: String (Default: `"1.0"`)
6. `occurred_at`: datetime (ISO-8601 UTC timestamp of occurrence)
7. `recorded_at`: datetime (ISO-8601 UTC timestamp of database insertion)
8. `source_service`: String (Producer service name)
9. `source_system`: String (System name `"guardianiq-backend"`)
10. `actor_json`: Dict[str, Any] (JSON object of actor details)
11. `subject_json`: Dict[str, Any] (JSON object of target subject/entity)
12. `correlation_id`: Optional[UUID] (Distributed tracing correlation ID)
13. `causation_id`: Optional[UUID] (Direct causal parent event ID)
14. `risk_context_json`: Optional[Dict[str, Any]] (Risk & threat context JSON)
15. `policy_context_json`: Optional[Dict[str, Any]] (Policy evaluation & compliance context JSON)
16. `payload_json`: Dict[str, Any] (Domain event payload)
17. `classification`: String (Default: `"INTERNAL"`)
18. `retention_class`: String (Default: `"STANDARD_90_DAYS"`)
19. `event_hash`: String (SHA-256 hash of event data for tamperpruf verification)
20. `previous_event_hash`: Optional[String] (Hash chain parent reference)

## Proposed Changes

### Documentation Artifacts

#### [NEW] [Phase4_Canonical_Event_Envelope.md](file:///c:/Users/aayus/Desktop/GuardianIQ--1/docs/Phase%204/Phase4_Canonical_Event_Envelope.md)
- Frozen envelope specification document containing the full 20-field table, type mapping, Pydantic schema draft (`GovernanceEventEnvelopeSchema`), and `TenantMixin` alignment declaration.

#### [NEW] [Phase4_implementation_plan_prompt_1_3_freeze_canonical_event_envelope.md](file:///c:/Users/aayus/Desktop/GuardianIQ--1/markdown/Phase4_implementation_plan_prompt_1_3_freeze_canonical_event_envelope.md)
- Standardized implementation plan saved to `markdown/`.

## Verification Plan

### Manual Verification
- Review [Phase4_Canonical_Event_Envelope.md](file:///c:/Users/aayus/Desktop/GuardianIQ--1/docs/Phase%204/Phase4_Canonical_Event_Envelope.md) against Phase 4 Spec section 8.2.
- Verify `tenant_id` field type aligns with [mixins.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/shared/mixins.py#L6-L10).

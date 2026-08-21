# Implementation Plan - Prompt 2.2: Seed Reference Data & Tool Capabilities Backfill (WBS 2.2)

Implement and execute comprehensive reference and pilot seed data for Phase 5, including reference governance policies, policy versions, rules, data source fields, agent runtime boundaries, tool permissions, policy bindings, and the automated `tool_capabilities` backfill.

## User Review Required

> [!IMPORTANT]
> **Key Seeding & Backfill Specifications**:
> 1. **`tool_capabilities` Automated Backfill**:
>    - Iterate through all existing `tools` table rows and explode `allowed_operations_json` into granular `tool_capabilities` records.
>    - Apply heuristic access mode inference: operations starting with `get_`, `read_`, `view_`, `list_`, `fetch_` mapped to `READ_ONLY`; others mapped to `EXECUTE` / `WRITE`.
>    - Explicitly tag all backfilled rows with `metadata_json={"_backfilled": true}` and `input_schema_json={"_backfilled": true}` so QA fixtures in subsequent tasks can disambiguate them.
> 2. **Master Pilot Governance Policies (Versioned & Activated)**:
>    - **`POL-DLP-001` (PII Data Loss Prevention & Redaction)**: Rules blocking direct unmasked export of SSN / Credit Card and enforcing masking or approval.
>    - **`POL-TOOL-001` (Agent Tool Execution Boundary Whitelist)**: Rules governing tool category permissions, restricting unapproved WRITE/ADMIN invocations.
>    - **`POL-AUTONOMY-001` (Financial Autonomy & Approval Cap)**: Rules enforcing 2-layer supervisor approval for transactions exceeding threshold ($10,000).
> 3. **Pilot Data Source Fields & Permissions**:
>    - Populate `data_source_fields` with realistic enterprise column classifications (`customer_id` [PUBLIC], `email` [INTERNAL], `annual_income` [CONFIDENTIAL], `ssn` [RESTRICTED, PII, REDACT]).
>    - Seed `agent_data_permissions` and `agent_runtime_boundaries`.
> 4. **Policy Bindings**:
>    - Bind policies to pilot agents with `version_strategy="LATEST"`.

## Open Questions

- None.

## Proposed Changes

### Database Seeding Module

#### [NEW] [backend/app/db/seed_phase5.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/db/seed_phase5.py)
- Standalone runnable seed script:
  - `backfill_tool_capabilities(db, tenant_id)`
  - `seed_governance_policies_and_rules(db, tenant_id)`
  - `seed_data_source_fields_and_permissions(db, tenant_id)`
  - `seed_agent_runtime_boundaries(db, tenant_id)`
  - `seed_policy_bindings(db, tenant_id)`

#### [MODIFY] [backend/app/db/seed.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/db/seed.py)
- Integrate Phase 5 seed invocation if called during master seeding.

## Verification Plan

### Automated Tests
- Run `python -m app.db.seed_phase5` to execute seeding.
- Add test in `backend/app/tests/test_phase5_database.py` verifying:
  - Backfilled tool capabilities exist with `_backfilled=True`.
  - Active pilot policies, versions, and rules exist and can be queried.
  - Data source fields and policy bindings are correctly wired.

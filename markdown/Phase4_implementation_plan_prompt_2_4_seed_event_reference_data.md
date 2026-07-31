# Implementation Plan - Prompt 2.4: Seed Event Reference Data (WBS 4.2.4)

Create database seeding script to populate `event_schema_registry` with the approved MVP event catalogue and `event_retention_rules` using `DataClassification` enum values.

## User Review Required

> [!IMPORTANT]
> **Data Classification Enum Reuse**: Reusing `DataClassification` from [constants.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/registry/constants.py#L81) (`PUBLIC`, `INTERNAL`, `CONFIDENTIAL`, `RESTRICTED`).
> **Default Retention Days**: Setting reasonable MVP defaults: `PUBLIC` (90 days), `INTERNAL` (365 days), `CONFIDENTIAL` (1825 days / 5 yrs), `RESTRICTED` (2555 days / 7 yrs).

## Open Questions

- None.

## Seeding Specification

1. **`event_schema_registry`**:
   - Seeds all 30 approved event types from [Phase4_MVP_Event_Taxonomy.md](file:///c:/Users/aayus/Desktop/GuardianIQ--1/docs/Phase%204/Phase4_MVP_Event_Taxonomy.md) across the 9 categories.
   - Standard version `'1.0'`, `is_active = True`, JSON schema defining standard 20-field envelope structure.
2. **`event_retention_rules`**:
   - Seeds default retention rules per category and classification.

## Proposed Changes

### Backend Seeding Script

#### [NEW] [phase4_seed.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/seed/phase4_seed.py)
- Python seed script establishing initial schema registry definitions and default retention rules in `event_schema_registry` and `event_retention_rules`.

### Documentation Artifacts

#### [NEW] [Phase4_implementation_plan_prompt_2_4_seed_event_reference_data.md](file:///c:/Users/aayus/Desktop/GuardianIQ--1/markdown/Phase4_implementation_plan_prompt_2_4_seed_event_reference_data.md)
- Implementation plan saved in `markdown/`.

## Verification Plan

### Automated / Command Verification
1. Run `python -m app.seed.phase4_seed` in `backend/` directory.
2. Verify database records in `event_schema_registry` (30 event types) and `event_retention_rules`.

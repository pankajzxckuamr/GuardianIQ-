# Phase 3 Database Schema Migration Plan

This plan details the code changes required to address the gaps identified in the Database Gap Assessment and prepare the database for the Phase 3 Relationship Engine.

## Resolved Decisions
Based on user review, the following architectural decisions have been finalized:
- **Table Naming Convention**: Drop the `registry_` prefix from all consolidated tables. The operational tables (e.g., `ai_models`, `agents`, `users`) will become the single source of truth.
- **Tenant ID Strategy**: A default `tenant_id` will be introduced and applied to existing data. For examples and templates, the dummy tenant `TEN_INNOVANT` will be used.
- **Data Migration Approach**: The database will be structurally reset (dropping old schemas and creating new ones), but a custom migration script will be written to extract, transform, and preserve the current Phase 0-2 data into the new consolidated schema.

## Proposed Changes

### `backend/app/modules/relationship`
#### [NEW] `backend/app/modules/relationship/models.py`
- Define `GenericRelationship` mapping to `generic_relationships`.
- Define `ObjectResponsibility` mapping to `object_responsibilities`.
- Define `RelationshipValidationResult` mapping to `relationship_validation_results`.
- Define `RelationshipGraphSnapshot` mapping to `relationship_graph_snapshots`.
- Define `PolicyBinding` mapping to `policy_bindings`.
- Define `EvidenceLink` mapping to `evidence_links`.

---

### Core Data Models
#### [MODIFY] [registry/models.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/registry/models.py)
- **Delete** duplicate models that will be consolidated into operational modules: `GuardianUser`, `RegistryRole`, `RegistryDepartment`, `RegistryAIAgent`, `RegistryAIModel`, `RegistryDataSource`, `RegistryAuditEvent`.
- **Modify** remaining models (like `RegistryTool`, `RegistryWorkflow`) to include `tenant_id`, strict `status` lifecycles, and `metadata_json`.

#### [MODIFY] [auth/models.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/auth/models.py)
- Consolidate `User` and `Role` models with the fields previously found in the registry (e.g., `department_id`, `approval_limit_level`).
- Add `tenant_id`.

#### [MODIFY] [agent/models.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/agent/models.py)
- Expand `Agent` model to include all Phase 3 required fields (`risk_level`, `metadata_json`, etc.).
- Add `tenant_id`.

#### [MODIFY] [ai_model/models.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/ai_model/models.py)
- Expand `AIModel` model with registry fields.
- Add `tenant_id`.

*(Similar modifications will be made to `datasource`, `department`, and `audit` models.)*

---

### Database Migrations & Seeding
#### [NEW] `backend/app/db/migrations/versions/...`
- Create an Alembic revision to generate the new consolidated tables.
- Develop a custom Python migration script (or use Alembic's data migration capabilities) to:
  1. Extract existing data from `registry_*` tables.
  2. Transform the records (adding a default `tenant_id`, merging duplicate fields).
  3. Load the data into the newly created operational tables (`ai_models`, `users`, etc.) before the old tables are dropped.

#### [MODIFY] [db/seed.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/db/seed.py)
#### [MODIFY] [db/seed_phase2.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/db/seed_phase2.py)
- Update seeding logic to use the consolidated tables.
- Inject a default `tenant_id` into all seeded records.

## Verification Plan

### Automated Tests
- Run existing test suites (`pytest tests/`) to identify all broken repository and service layers.

### Manual Verification
- Run the API server (`uvicorn main:app --reload`) and verify that the database builds successfully without SQLAlchemy mapping errors.
- Inspect the generated DB schema to ensure `tenant_id` exists on all governable objects and the `generic_relationships` table matches Volume 1 specifications.

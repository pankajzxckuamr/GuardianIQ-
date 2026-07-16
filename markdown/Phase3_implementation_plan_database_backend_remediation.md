# Implementation Plan: Re-mediating Database & Backend Tasks (Phase 3)

This plan outlines the design and proposed changes to resolve the **Missed** and **Partial** tasks identified in the [Phase3_Database_Backend_Tasks_Audit.md](file:///c:/Users/aayus/Desktop/GuardianIQ--1/Phase3_Database_Backend_Tasks_Audit.md) file.

## Re-mediated Tasks

1. **Task 2: Create indexes and constraints** (Status: **Missed**)
2. **Task 3: Create seed/reference data** (Status: **Missed**)
3. **Task 13: Graph/resolver APIs** (Status: **Partial**)
4. **Task 14: Authorization bridge** (Status: **Partial**)
5. **Task 15: OpenAPI contract draft** (Status: **Missed**)
6. **Task 20: Performance and cache baseline** (Status: **Partial**)

---

## User Review Required

> [!IMPORTANT]
> - **Graph Filtering**: Hiding nodes or edges in the Graph and Impact traversal APIs when a user lacks permission might lead to disjointed subgraphs (where intermediate nodes are hidden). We propose returning the full structural graph but masking/hiding name labels and metadata details for unauthorized nodes, replacing them with a placeholder (e.g. `"[REDACTED (Insufficient Clearance)]"`).
> - **Cache Strategy**: To avoid introducing external dependencies like Redis for this phase, we will implement an in-memory cache provider inside the application service layer. This cache will invalidates on write operations.

---

## Open Questions

> [!NOTE]
> None at this stage. The planned scope strictly addresses the gaps logged in the audit checklist.

---

## Proposed Changes

### Database Workstream

#### [NEW] [alembic migration script](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/db/migrations/versions/add_phase3_composite_indexes.py)
Create a new Alembic migration version containing composite indexes for traversal optimization:
- `ix_composite_rel_source`: `(tenant_id, source_type, source_id, relationship_type, status)`
- `ix_composite_rel_target`: `(tenant_id, target_type, target_id, relationship_type, status)`
- `ix_composite_rel_lifecycle`: `(tenant_id, status, effective_from, effective_to)`
- `ix_composite_resp_object`: `(tenant_id, object_type, object_id, responsibility_type, status)`

#### [NEW] [seed_relationships.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/scripts/seed_relationships.py)
A CLI Python script using the SQLAlchemy session to seed:
- Valid relationship types (`USES`, `MONITORS`, `DEPENDS_ON`, `OWNED_BY`, etc.).
- Active sample relationships connecting seeded models, agents, tools, workflows, users, and departments.
- Active responsibilities (Owners, Approvers, Reviewers) mapped to resources.
- Sample policy bindings and evidence links.

---

### Backend Workstream

#### [MODIFY] [api.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/relationship/api.py)
1. **Extend Graph Traversals**:
   - Update `get_relationship_graph` and `get_impact_analysis` to query `policy_bindings` and `evidence_links` connected to nodes.
2. **Hiding/Redacting Nodes**:
   - Introduce filtering inside `get_relationship_graph` and `get_impact_analysis` by calling a security evaluator. If the subject has no read clearance for a node, its name/label is replaced with `"[REDACTED]"` and attributes are cleared.
3. **Write API Security Hooks**:
   - Secure the remaining write paths: revoke/delete (`delete_relationship`), suspend (`suspend_relationship`), approve (`approve_relationship`), and activate (`activate_relationship`) by adding the `check_relationship_modification_access` validation hook.
4. **Caching Layer**:
   - Add in-memory cache hooks using a global thread-safe repository inside `api.py` or service layer to cache graph traversals.
   - Clear the cache on mutations (create, update, delete, suspend, approve, activate).

#### [NEW] [cache_service.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/relationship/cache_service.py)
Introduce a lightweight memory cache manager supporting:
- Scoped keys by tenant and request signature.
- Time-To-Live (TTL) configuration.
- Cache invalidation methods.

#### [NEW] [PHASE3_API_SPEC.md](file:///c:/Users/aayus/Desktop/GuardianIQ--1/docs/PHASE3_API_SPEC.md)
Document the entire Phase 3 API specifications:
- REST endpoint signatures, path/query params.
- JSON Request/Response schemas (including validation errors structure).
- Required roles, ABAC permissions, and sensitivity clearances.
- Generated audit event catalog.

---

## Verification Plan

### Automated Tests
- Run all existing tests to verify no regressions:
  ```powershell
  pytest backend/app/tests/test_relationship.py
  ```
- Run python seed script to confirm reference seeding:
  ```powershell
  python backend/scripts/seed_relationships.py
  ```
- Write new backend tests in [test_relationship.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/tests/test_relationship.py) checking:
  - Cache invalidation on relationship status changes.
  - Graph query redacted node outputs.
  - Write checks block unauthorized deletions, approvals, and suspensions.

### Manual Verification
- Review the `/docs` auto-generated OpenAPI Swagger specification.
- Inspect the generated migration script and run `alembic upgrade head`.

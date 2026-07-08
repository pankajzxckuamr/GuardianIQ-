# Implementation Plan — Phase 1 Day 9 Seeding Verification & Handover Documentation

This plan details the steps to verify the database seeding pipeline and construct a comprehensive handover document (`PHASE1_HANDOVER.md`) for the GuardianIQ Registry API (Phase 1).

## Proposed Changes

We will execute this task in two consecutive, logical phases:

### 1. Seeding Enhancements & Verification (Task A)

To ensure that running `python -m app.db.seed` (or running `seed.py` directly) successfully seeds **all 10 registry tables** cleanly on an empty database, we will perform the following modifications:

#### [MODIFY] [registry/seed.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/registry/seed.py)
We will expand the seeding script to register all Phase 1 Day 9 demo entities in a strictly idempotent manner. It will look up existing codes before inserting to avoid primary key/unique constraint violations.
- **AI Models (3)**: Seeding `GPT-4-ENTERPRISE` (ACTIVE), `FRAUD-DETECT-ML` (ACTIVE), and `CUSTOMER-TRIAGE-LLM` (DRAFT).
- **AI Agents (3)**: Seeding `triage-agent-01` (ACTIVE, RECOMMEND_ONLY), `routing-agent-01` (ACTIVE, HUMAN_IN_THE_LOOP), and `ops-agent-01` (ACTIVE, FULLY_AUTONOMOUS).
- **Integration Tools (4)**: Seeding `slack-alerts` (WEBHOOK, EXECUTE), `jira-triage` (API, WRITE), `user-db-query` (DATABASE, READ), and `model-scanner` (CUSTOM, EXECUTE).
- **Security Workflows (2)**: Seeding `risk-review-wf` (approval required: `true`, HIGH criticality) and `deployment-wf` (approval required: `false`, MEDIUM criticality).
- **Data Sources (3)**: Seeding `customer-profile-db` (RESTRICTED sensitivity, contains PII), `financial-transactions` (CONFIDENTIAL), and `system-logs` (INTERNAL).
- **Relationships (5)**: Mapped relationships linking agents, models, tools, workflows, and data sources.
- **Audit Trails**: Recording a `CREATE` event type for each newly created record inside `registry_audit_events` to ensure the audit table has active historical entries.

#### [MODIFY] [db/seed.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/db/seed.py)
We will add an invocation to trigger the registry seeding script immediately after seeding the auth system (permissions, roles, and default admin user) inside the transaction:
```python
        # --- Seed Registry Day 9 Demo Data ---
        print("\n🌱 Seeding Registry Day 9 Demo Data...")
        from app.modules.registry.seed import seed_registry_data
        seed_registry_data(db)
        print("   ✅ Registry seeding complete!")
```

### 2. Handover Documentation (Task B)

#### [NEW] [PHASE1_HANDOVER.md](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/PHASE1_HANDOVER.md)
We will create a comprehensive, premium handover document inside the `backend/` directory structured exactly as requested:
1. **Folder Map**: Breakdown of each file in `backend/app/modules/registry/` explaining its architectural function.
2. **Execution Guide**: Step-by-step shell commands to activate the virtual environment, install dependencies, run migrations (`alembic upgrade head`), and boot the server.
3. **Seeding Guide**: Documenting how to execute the comprehensive seed script.
4. **Endpoint Reference Directory**: A complete catalog listing the `Method`, `Path`, `Allowed RBAC Roles`, and `Functional Purpose` for all 24 registry API routes.
5. **Key Validation Policies**: Details on semantic check gates, unique codes (409), transition constraints (400), permission blocks (403), confidence checks, parent-department controls, and endpoint pattern security.
6. **Known Defect Registry**: Highlighting minor schema validation anomalies (such as `page_size` being excluded from Pydantic exports on models and data-sources) and concurrency constraints.
7. **Phase 2 Coordination Dependency Note**:
   > [!IMPORTANT]
   > "Phase 2 Policy Engine must consume /api/registry/models, /api/registry/agents, /api/registry/relationships. Do not modify registry_* table structure without Phase 2 coordination. Recommended new tables for Phase 2: policies_v2, policy_rules, approval_matrix, governance_events."
8. **Required Environment Configurations**: Mapping key parameters (`DATABASE_URL`, `JWT_SECRET`, `JWT_ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`).

---

## Verification Plan

### Automated Verification
We will run:
1. Python seed execution:
   ```bash
   python backend/app/db/seed.py
   ```
2. Unittest suite:
   ```bash
   pytest backend/app/tests/test_registry.py -v
   ```

### Manual Verification
- We will inspect the database tables using SQLAlchemy scripts or standard CLI tools to guarantee all 10 tables are populated with data.
- We will inspect `/docs` or compile schemas to verify that all endpoints are documented, validate correctly, and that no schema discrepancies occur.

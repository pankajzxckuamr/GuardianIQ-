# QA Validation Plan: GuardianIQ Platform Fourth-Wave Verification

This plan defines the step-by-step verification pipeline for the **GuardianIQ Platform**, following the requirements in the [testing_guide_for_ai.md](file:///c:/Users/aayus/AppData/Local/Packages/5319275A.WhatsAppDesktop_cv1g1gvanyjgm/LocalState/sessions/CA3E0DA77BCA56ED2FFED9EB5A65878376463EE5/transfers/2026-24/testing_guide_for_ai.md).

## User Review Required

> [!NOTE]
> All tasks will be executed using the local environment context. If there are database connectivity or configuration issues during migrations/tests, they will be reported.

## Open Questions

> [!NOTE]
> None. The test execution guide is fully detailed and the database schema/seeding setup is standard.

## Proposed Changes

### [Verification Steps]

No source code changes are required as this is a QA/testing task. We will execute the validation steps, analyze results, check code compliance, and generate a comprehensive verification report.

---

### Step 1: Database Migration & Seeding Verification
We will verify that the database migrations and data seeds execute cleanly.
1. Run `alembic downgrade base` and `alembic upgrade head` inside the `backend` folder using the virtual environment python interpreter.
2. Run the seeding script `python -m app.db.seed` with `PYTHONIOENCODING=utf-8`.
3. Check migrations and seed outputs to verify completion.

---

### Step 2: Backend Integration & Test Suite Execution
We will run the complete integration test suite to verify the REST API endpoints and business logic.
1. Run the full pytest suite: `python -m pytest app/tests/` inside the `backend` directory.
2. Run individual test suites:
   - `python -m pytest app/tests/test_health.py`
   - `python -m pytest app/tests/test_rbac_routes.py`
   - `python -m pytest app/tests/test_auth_audit.py`
   - `python -m pytest app/tests/test_registry.py`

---

### Step 3: Specific Audit Steps for Scope Compliance (CL-001 to CL-007)
We will perform static code analysis and schema audits to confirm changes match requirements:
1. **Model Provider Checks (CL-001 to CL-005)**: Verify `AIModelBase` schema defines provider references, the `registry_ai_model_providers` table structure tracks required fields (`provider_name`, `provider_type`, governance fields in `metadata_json`), and models perform outer joins to dynamically resolve provider name (inspecting `repositories.py`).
2. **Workflow Stage Redesign (CL-006)**: Validate default pending status, notification logging to `backend/logs/notifications.log`, and state transitions via `/approve` and `/reject`.
3. **Relationship Viewer (CL-007)**: Verify constraints on allowed mappings (e.g. `MODEL -> USES -> DATA_SOURCE`, `AGENT -> USES -> MODEL`, etc.) in `services.py` and verify `409 CONFLICT` check for duplicates.

---

### Step 4: Frontend Compilation & TypeScript Type Safety
We will verify the frontend builds cleanly without type issues.
1. Install node dependencies in `frontend` folder using `npm install`.
2. Run strict TypeScript check: `npm run typecheck`.
3. Build Vite bundle: `npm run build`.

---

### Step 5: End-to-End Scenario Verification
We will script the seeding of the three scenarios in `Demo_Scenarios.txt`:
1. **Scenario 1**: HR Department, Sarah Jenkins user, DS-HR-WORKDAY, LLM-COMPLIANCE-DOCS, AGENT-ONBOARD-01, WF-ONBOARDING-PIPELINE, and their respective relationships.
2. **Scenario 2**: Customer Support Department, Michael Chang user, API-REFUND-STRIPE tool, LLM-SUPPORT-001 model, AGENT-REFUND-BOT agent, WF-AUTO-REFUND workflow, and relationships.
3. **Scenario 3**: Finance Department, Elena Rodriguez user, DS-FIN-LEDGER database, API-ACCOUNT-FREEZE tool, ML-FRAUD-DETECT-V4 model, AGENT-FRAUD-SENTINEL agent, WF-FRAUD-FREEZE workflow, and relationships.
We will create a Python script similar to `create_sample_registry_data.py` to automate this seeding process and assert that the endpoints create these entities successfully.

---

### Step 6: Post-Execution Verification Audit
Confirm the application is running stably and generate the final QA report at `docs/test_report.md` (or `test_report.md` in workspace root, updating or creating the file).

## Verification Plan

### Automated Tests
We will execute:
- `python -m pytest app/tests/`
- `npm run typecheck`
- `npm run build`

### Manual Verification
- We will inspect the code files and verify database migrations.
- We will script scenario insertion and verify HTTP response codes.

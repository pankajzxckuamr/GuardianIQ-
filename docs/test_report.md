# GuardianIQ Platform Test Report

This document records the baseline verification results for both the backend and frontend components of the **GuardianIQ** application. All tests and checks were executed on the active codebase to establish correctness before any new changes are introduced.

---

## 📋 Executive Summary

| Verification Area | Method / Tool | Status | Findings |
| :--- | :--- | :---: | :--- |
| **Backend Unit Tests** | `unittest` | ✅ PASS | 7/7 tests passed successfully |
| **Database Migrations** | Alembic | ✅ UP TO DATE | Migrated to head: `cc023be5e56e` |
| **Database Seed State** | PostgreSQL Inspection | ✅ VERIFIED | Roles, permissions, users, and registry records correctly seeded |
| **Frontend Compilation** | `tsc --noEmit` | ✅ SUCCESS | 0 TypeScript errors |
| **Frontend Production Build** | `vite build` | ✅ SUCCESS | Assets compiled and bundled successfully in ~12s |

---

## ⚙️ Backend Testing Details

### 1. Automated Test Suite Output
The unit tests were executed inside the virtual environment from the `backend/` directory using the verbose flag.

**Command:**
```powershell
.\venv\Scripts\python -m unittest discover -v -s app/tests -p "test_*.py"
```

**Results Output:**
```text
test_failed_login_records_audit_event (test_auth_audit.AuthAuditIntegrationTests.test_failed_login_records_audit_event) ... ok
test_failed_password_records_audit_event (test_auth_audit.AuthAuditIntegrationTests.test_failed_password_records_audit_event) ... ok
test_successful_login_records_audit_event (test_auth_audit.AuthAuditIntegrationTests.test_successful_login_records_audit_event) ... ok
test_health_check_returns_success (test_health.HealthCheckTests.test_health_check_returns_success) ... ok
test_module_routes_require_authentication (test_rbac_routes.RBACRouteProtectionTests.test_module_routes_require_authentication) ... ok
test_model_filtering_combinations (test_registry.RegistryIntegrationTests.test_model_filtering_combinations) ... ok
test_registry_lifecycle_and_summary (test_registry.RegistryIntegrationTests.test_registry_lifecycle_and_summary) ... ok

----------------------------------------------------------------------
Ran 7 tests in 3.385s

OK
```

### 2. Migration Status
The database migration engine (Alembic) shows that all schema updates are fully synchronized with the local PostgreSQL server:

**Command:**
```powershell
.\venv\Scripts\alembic current
```

**Output:**
```text
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
cc023be5e56e (head)
```

---

## 🗄️ Database State & Inspection

An inspection of the public schema was performed to count table entries and verify seeding integrity.

### Table Row Counts

| Table Name | Row Count | Description / Verification |
| :--- | :---: | :--- |
| **`roles`** | `6` | Seeded roles (Super Admin, Governance Admin, Approver, etc.) |
| **`permissions`** | `8` | Seeded capabilities (`registry.read`, `registry.write`, `audit.read`, etc.) |
| **`role_permissions`** | `22` | Mappings between roles and their granted permissions |
| **`users`** | `3` | Seeded demo users (`admin@guardianiq.com`, `reviewer@guardianiq.com`, `auditor@guardianiq.com`) |
| **`user_roles`** | `3` | Mappings between seeded users and their respective roles |
| **`registry_departments`** | `10` | seeded departments for registry governance |
| **`registry_ai_models`** | `4` | Seeded AI Models |
| **`registry_ai_agents`** | `4` | Seeded AI Agents |
| **`registry_tools`** | `4` | Seeded integration tools |
| **`registry_workflows`** | `4` | Seeded security workflows |
| **`registry_data_sources`** | `4` | Seeded data sources |
| **`registry_relationships`** | `15` | Relationships mapped between registry entities |
| **`registry_audit_events`** | `80` | Logged actions on the registry registry |
| **`audit_events`** | `55` | System security and authentication events logged |
| **`token_blocklist`** | `9` | Revoked JWT tokens list |
| **`policies`** | `2` | Governance policies |

---

## 🖥️ Frontend Testing Details

### 1. TypeScript Codebase Validation
The frontend codebase compiles successfully under TypeScript strictness configuration.

**Command:**
```powershell
npm run typecheck
```

**Output:**
```text
> guardianiq-frontend@0.1.0 typecheck
> tsc --noEmit
```
*(No compilation or typings errors detected.)*

### 2. Production Assets Build
The production bundler generates optimized chunks under strict Content Security Policies.

**Command:**
```powershell
npm run build
```

**Output:**
```text
vite v5.4.21 building for production...
transforming...
✓ 2840 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                     1.00 kB │ gzip:   0.58 kB
dist/assets/index-DG2Yp65x.css    132.72 kB │ gzip:  19.42 kB
dist/assets/index-DvIlYSiA.js   1,101.88 kB │ gzip: 322.07 kB
✓ built in 12.77s
```

---

## 📝 Next Steps: Addressing Pending Issues
Based on the project review, here are the outstanding items in the development queue:

1. **Centralized Audit Logging Integration**: Currently, the audit service (`create_audit_event()`) is defined, but needs to be wired into business logic operations across various modules.
2. **Missing `ApplicationSettings` Table**: A model and table for application settings does not exist and requires an Alembic migration.
3. **Missing `GET /api/version` Endpoint**: An endpoint is needed in `app/main.py` to return the current deployment version.
4. **Log directory safety guard**: Add safety checks in `app/core/logging.py` to ensure `logs/` directory exists before starting the file handlers.

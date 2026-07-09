# Implementation Plan: Pre-Phase 3 Legacies & Governance Standardization

This plan outlines the design and proposed changes to resolve the remaining gaps identified in the gap verification report: standardizing ownership tracking, automating audit trail events, and declaring class-level canonical object type constants.

## User Review Required

> [!IMPORTANT]
> **Schema and Ownership Column Migration**
> Abstracting `owner_user_id` into a shared `GovernableMixin` requires removing local declarations from individual models. Since the column name `owner_user_id` and its foreign key setup already align across all models, this refactor is non-breaking for existing data fields, but requires careful ORM registry compilation validation.

---

## Proposed Changes

### Shared DB Mixins
#### [MODIFY] [mixins.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/shared/mixins.py)
- Create a unified `GovernableMixin` inheriting from `TenantMixin` and `TimestampMixin`:
  ```python
  class GovernableMixin(TenantMixin, TimestampMixin):
      id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, server_default=func.gen_random_uuid())
      version_no = Column(Integer, server_default="1", default=1, nullable=True)
      is_deleted = Column(Boolean, server_default="FALSE", default=False, nullable=True)
      metadata_json = Column(JSON, server_default="{}", default=None, nullable=True)
      status = Column(String(30), default='ACTIVE', nullable=False)

      @declared_attr
      def owner_user_id(cls):
          return Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
  ```

---

### Core Data Models
#### [MODIFY] [agent/models.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/agent/models.py)
#### [MODIFY] [ai_model/models.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/ai_model/models.py)
#### [MODIFY] [datasource/models.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/datasource/models.py)
#### [MODIFY] [department/models.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/department/models.py)
#### [MODIFY] [registry/models.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/registry/models.py)
- Update all operational models to inherit from `GovernableMixin` instead of `WorkflowBaseMixin`.
- Remove redundant local definitions of `owner_user_id`, `status`, `metadata_json`, etc.
- Declare class-level constant `__object_type__` matching their canonical string representation (e.g., `__object_type__ = "AGENT"`, `__object_type__ = "AI_MODEL"`).

---

### Registry Lookup Maps
#### [MODIFY] [services.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/registry/services.py)
#### [MODIFY] [repositories.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/registry/repositories.py)
- Replace static dictionary mappings mapping type strings to classes (e.g., `"AGENT": RegistryAIAgent`) with a dynamic registry mapper. The registry mapper searches all SQLAlchemy classes inheriting from `GovernableMixin` and extracts their `__object_type__` values at application start-up.

---

### Automated Audit Interceptors
#### [NEW] `backend/app/shared/audit_listeners.py`
- Register SQLAlchemy event listeners (`after_insert`, `after_update`) for all classes implementing `GovernableMixin`.
- Automatically construct and publish a central audit event (e.g., `ENTITY_CREATED` or `ENTITY_UPDATED`) containing metadata, actor context (loaded from a thread/request context local variable), and change details.

---

## Verification Plan

### Automated Tests
- Run full pytest suites to ensure no ORM mapping compilation errors occur:
  ```powershell
  $env:PYTHONPATH="."
  venv\Scripts\python.exe -m pytest app/tests/
  venv\Scripts\python.exe -m pytest tests/test_phase2_e2e.py
  ```

### Manual Verification
- Verify that saving any operational model (e.g., creating a new Agent or DataSource) automatically populates an immutable record in the timeline database table without explicit manual controller calls.

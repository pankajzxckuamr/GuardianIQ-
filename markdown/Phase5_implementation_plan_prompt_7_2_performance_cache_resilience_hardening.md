# Phase 5 Implementation Plan — Prompt 7.2: Performance/Cache/Resilience Hardening

## 1. Goal Description
Harden performance, in-memory caching, and resilience across the Phase 5 runtime governance stack. Utilize `MemoryCacheService` to cache active policy versions, rules, bindings, agent boundaries, and tool/data permissions with automatic cache invalidation upon mutations. Implement graceful database fallback, strict evaluation timeouts, millisecond latency metrics, and fail-closed security guarantees on unexpected engine or database timeouts.

---

## 2. Technical Architecture & Design Decisions

### In-Memory Caching Strategy (Single-Instance `MemoryCacheService`)
- As mandated by the specification correction, we will reuse the existing thread-safe `MemoryCacheService` (`app.modules.relationship.cache_service.MemoryCacheService`).
- Standardized cache keys:
  - Active Version & Rules: `f"policy_version:{tenant_id}:{policy_id}"`
  - Effective Bindings: `f"bindings:{tenant_id}:{target_type}:{target_id}"`
  - Agent Runtime Boundary: `f"boundary:{tenant_id}:{agent_id}"`
  - Tool Capabilities: `f"tool_caps:{tenant_id}:{tool_id}"`
  - Data Permissions: `f"data_perms:{tenant_id}:{data_source_id}"`
- TTL: 300 seconds default.
- Invalidation Triggers:
  - Creating/updating/activating policy versions $\rightarrow$ invalidates policy version cache.
  - Creating/suspending/revoking bindings $\rightarrow$ invalidates binding cache.
  - Updating agent boundaries or toggling kill switch $\rightarrow$ invalidates agent boundary cache.

### Timeout Enforcement & Fail-Closed Resilience
- `RuntimeEnforcementEngine.enforce()` will incorporate strict execution timeout protection (e.g. `max_timeout_ms=500ms`).
- If evaluation exceeds the configured timeout threshold or encounters an uncaught runtime/DB exception:
  - Returns `Decision.DENY` (fail-closed).
  - Emits reason `"Evaluation timed out — failing closed for safety"`.
  - Sets violation code `"ENGINE_TIMEOUT_FAIL_CLOSED"`.
  - Records execution latency in `GovernedRuntimeResponse`.

---

## 3. Proposed Changes & Affected Files

### Backend Core
#### [MODIFY] [engine.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/enforcement/engine.py)
- Integrate execution timeout parameter (`timeout_ms: int = 500`) and fail-closed timeout wrapper.
- Integrate cache support across boundary, tool, and data guards via `MemoryCacheService`.
- Compute and attach `latency_ms` on all `GovernedRuntimeResponse` results.

#### [MODIFY] [resolver.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/agent_boundary/resolver.py)
- Add `MemoryCacheService` caching for `resolve_boundary` with DB fallback.

#### [MODIFY] [service.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/agent_boundary/service.py)
- Invalidate boundary cache on `set_boundary` and kill-switch toggle.

### Automated Tests
#### [NEW] [test_phase5_performance_cache_resilience.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/tests/test_phase5_performance_cache_resilience.py)
Create comprehensive test suite verifying:
1. `test_cache_hit_performance_and_latency`: Confirms sub-50ms resolution on warm cache hits.
2. `test_cache_invalidation_on_policy_version_activation`: Verifies newly activated version immediately invalidates stale cache.
3. `test_cache_invalidation_on_boundary_kill_switch`: Verifies kill-switch engagement instantly reflects in runtime engine.
4. `test_cache_failure_graceful_db_fallback`: Validates that corrupted/failing cache falls back to database authoritatively.
5. `test_enforcement_engine_timeout_fail_closed`: Verifies engine enforces fail-closed `Decision.DENY` when policy evaluation exceeds timeout.
6. `test_runtime_latency_measurement`: Ensures `latency_ms` is accurately measured and reported in response envelopes.

---

## 4. Verification Plan
- Run automated performance and resilience test suite:
  ```powershell
  pytest app/tests/test_phase5_performance_cache_resilience.py -v
  ```
- Run full Phase 5 test suite to verify 0 regressions:
  ```powershell
  pytest app/tests/ -k "phase5" -v
  ```

import React, { useState, useEffect, useCallback } from 'react';
import { healthService } from '@/services/health/healthService';
import { HealthCheckResult } from '@/services/health/healthTypes';
import { Badge } from '@/components/common/Badge';
import { PageHeader } from '@/components/common/PageHeader';
import '@/styles/pages/health.css';

const AUTO_REFRESH_MS = 30_000;

// -----------------------------------------------------------------------
// Helpers
// -----------------------------------------------------------------------

function formatTimestamp(iso: string | null): string {
  if (!iso) return '—';
  return new Date(iso).toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
}

function isHealthy(result: HealthCheckResult): boolean {
  return result.response?.status === 'success';
}

// -----------------------------------------------------------------------
// HealthCard subcomponent
// -----------------------------------------------------------------------

interface HealthCardProps {
  title: string;
  endpoint: string;
  result: HealthCheckResult;
  onRetry: () => void;
}

const HealthCard: React.FC<HealthCardProps> = ({ title, endpoint, result, onRetry }) => {
  const healthy = isHealthy(result);
  const hasData = result.response !== null;

  return (
    <div className={`health-card${result.error ? ' health-card--error' : ''}`}>
      {/* Card header */}
      <div className="health-card__header">
        <span className="health-card__title">{title}</span>
        {!result.isLoading && hasData && (
          <Badge variant={healthy ? 'success' : 'danger'}>
            {healthy ? 'Healthy' : 'Error'}
          </Badge>
        )}
        {result.isLoading && (
          <Badge variant="neutral">Checking…</Badge>
        )}
      </div>

      {/* Card body — skeleton | error | data */}
      {result.isLoading && !hasData ? (
        <div className="health-card__skeleton">
          {[80, 55, 100, 40].map((w, i) => (
            <div key={i} className="health-card__skeleton-row">
              <div className="health-card__skeleton-bar" style={{ width: `${w * 0.4}%` }} />
              <div className="health-card__skeleton-bar" style={{ width: `${w * 0.5}%` }} />
            </div>
          ))}
        </div>
      ) : result.error && !hasData ? (
        <div className="health-card__error">
          <div className="health-card__error-icon" aria-hidden="true">⚠</div>
          <p className="health-card__error-msg">{result.error}</p>
          <button type="button" className="health-retry-btn" onClick={onRetry}>
            ↺ Retry
          </button>
        </div>
      ) : hasData ? (
        <div className="health-card__body">
          <div className="health-metric">
            <span className="health-metric__label">Status</span>
            <span className="health-metric__value">
              {result.response!.status === 'success' ? '✓ Operational' : '✗ Degraded'}
            </span>
          </div>

          <div className="health-metric-divider" />

          <div className="health-metric">
            <span className="health-metric__label">Message</span>
            <span className="health-metric__value">{result.response!.message}</span>
          </div>

          <div className="health-metric-divider" />

          <div className="health-metric">
            <span className="health-metric__label">Latency</span>
            <span className="health-metric__value">
              {result.latencyMs !== null ? `${result.latencyMs} ms` : '—'}
            </span>
          </div>

          <div className="health-metric-divider" />

          <div className="health-metric">
            <span className="health-metric__label">Request ID</span>
            <span className="health-metric__value health-metric__value--mono" title={result.response!.request_id}>
              {result.response!.request_id}
            </span>
          </div>

          <div className="health-metric-divider" />

          <div className="health-metric">
            <span className="health-metric__label">Endpoint</span>
            <span className="health-metric__value health-metric__value--mono">{endpoint}</span>
          </div>

          {result.error && (
            <>
              <div className="health-metric-divider" />
              <div className="health-metric">
                <span className="health-metric__label" style={{ color: 'var(--color-danger)' }}>Error</span>
                <span className="health-metric__value">{result.error}</span>
              </div>
            </>
          )}
        </div>
      ) : null}

      {/* Card footer */}
      <div className="health-card__footer">
        <span className="health-card__timestamp">
          Last checked: {formatTimestamp(result.checkedAt)}
        </span>
        {hasData && (
          <button type="button" className="health-retry-btn" onClick={onRetry}>
            ↺ Refresh
          </button>
        )}
      </div>
    </div>
  );
};

// -----------------------------------------------------------------------
// FoundationHealthPage
// -----------------------------------------------------------------------

const INITIAL_STATE: HealthCheckResult = {
  response: null,
  latencyMs: null,
  checkedAt: null,
  isLoading: true,
  error: null,
};

const FoundationHealthPage: React.FC = () => {
  const [appHealth, setAppHealth] = useState<HealthCheckResult>(INITIAL_STATE);
  const [dbHealth, setDbHealth] = useState<HealthCheckResult>(INITIAL_STATE);

  const fetchAppHealth = useCallback(async () => {
    setAppHealth((prev) => ({ ...prev, isLoading: true, error: null }));
    const t0 = performance.now();
    try {
      const response = await healthService.getAppHealth();
      const latencyMs = Math.round(performance.now() - t0);
      setAppHealth({
        response,
        latencyMs,
        checkedAt: new Date().toISOString(),
        isLoading: false,
        error: response.status === 'error' ? response.message : null,
      });
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Network error — backend unreachable';
      setAppHealth({
        response: null,
        latencyMs: null,
        checkedAt: new Date().toISOString(),
        isLoading: false,
        error: message,
      });
    }
  }, []);

  const fetchDbHealth = useCallback(async () => {
    setDbHealth((prev) => ({ ...prev, isLoading: true, error: null }));
    const t0 = performance.now();
    try {
      const response = await healthService.getDbHealth();
      const latencyMs = Math.round(performance.now() - t0);
      setDbHealth({
        response,
        latencyMs,
        checkedAt: new Date().toISOString(),
        isLoading: false,
        // Backend sends status: "error" with HTTP 503 for DB failures
        error: response.status === 'error' ? response.message : null,
      });
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Network error — database unreachable';
      setDbHealth({
        response: null,
        latencyMs: null,
        checkedAt: new Date().toISOString(),
        isLoading: false,
        error: message,
      });
    }
  }, []);

  const fetchAll = useCallback(() => {
    void fetchAppHealth();
    void fetchDbHealth();
  }, [fetchAppHealth, fetchDbHealth]);

  // Initial fetch + auto-refresh every 30 seconds
  useEffect(() => {
    fetchAll();
    const interval = setInterval(fetchAll, AUTO_REFRESH_MS);
    return () => clearInterval(interval);
  }, [fetchAll]);

  return (
    <main className="health-page">
      <PageHeader
        title="Foundation Health"
        subtitle="Live system health checks for TC-05-005 — Backend & Database"
        breadcrumbs={[{ label: 'Dashboard', href: '/dashboard' }, { label: 'Health' }]}
      />

      <div className="health-cards-grid">
        <HealthCard
          title="Application Health"
          endpoint="GET /api/health"
          result={appHealth}
          onRetry={fetchAppHealth}
        />
        <HealthCard
          title="Database Health"
          endpoint="GET /api/health/db"
          result={dbHealth}
          onRetry={fetchDbHealth}
        />
      </div>

      <div className="health-refresh-notice" role="status" aria-live="polite">
        <span className="health-refresh-dot" aria-hidden="true" />
        Auto-refreshes every 30 seconds
      </div>
    </main>
  );
};

export default FoundationHealthPage;

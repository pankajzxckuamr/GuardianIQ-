import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import { healthService } from '@/services/health/healthService';
import { HealthCheckResult } from '@/services/health/healthTypes';
import { Badge } from '@/components/common/Badge';
import { StatusIndicator } from '@/components/common/StatusIndicator';
import { PageHeader } from '@/components/common/PageHeader';
import { DataTable, ColumnDef } from '@/components/tables/DataTable';
import '@/styles/pages/dashboard.css';

// -----------------------------------------------------------------------
// Phase 0 QA Checklist data
// -----------------------------------------------------------------------

type ChecklistStatus = 'success' | 'warning' | 'danger' | 'info' | 'neutral';

interface ChecklistItem {
  id: string;
  test_case: string;
  description: string;
  status: ChecklistStatus;
  phase: string;
}

const CHECKLIST: ChecklistItem[] = [
  { id: 'TC-01', test_case: 'TC-01', description: 'Project scaffolding & TypeScript config', status: 'success', phase: '0' },
  { id: 'TC-02', test_case: 'TC-02', description: 'User login execution', status: 'success', phase: '0' },
  { id: 'TC-03', test_case: 'TC-03', description: 'JWT token handling & session persistence', status: 'warning', phase: '0' },
  { id: 'TC-04', test_case: 'TC-04', description: 'RBAC permission enforcement', status: 'warning', phase: '0' },
  { id: 'TC-05-001', test_case: 'TC-05-001', description: 'StandardResponse envelope validation', status: 'success', phase: '0' },
  { id: 'TC-05-005', test_case: 'TC-05-005', description: 'System base API health check', status: 'info', phase: '0' },
  { id: 'TC-06', test_case: 'TC-06', description: 'Audit log write on entity mutation', status: 'neutral', phase: '0' },
  { id: 'TC-07', test_case: 'TC-07', description: 'Policy create / read / update', status: 'neutral', phase: '0' },
];

// -----------------------------------------------------------------------
// Metric card types
// -----------------------------------------------------------------------

interface MetricCardData {
  label: string;
  value: string | null;
  sub: string;
  variant: 'default' | 'error' | 'warning';
  isLoading: boolean;
}

// -----------------------------------------------------------------------
// MetricCard component
// -----------------------------------------------------------------------

interface MetricCardProps extends MetricCardData {
  icon: React.ReactNode;
}

const MetricCard: React.FC<MetricCardProps> = ({ label, value, sub, variant, isLoading, icon }) => (
  <div className={`metric-card${variant !== 'default' ? ` metric-card--${variant}` : ''}`}>
    <div className="metric-card__header">
      <span className="metric-card__label">{label}</span>
      <div className="metric-card__icon" aria-hidden="true">{icon}</div>
    </div>
    {isLoading ? (
      <div className="metric-card__skeleton" aria-hidden="true" />
    ) : (
      <div className="metric-card__value">{value ?? '—'}</div>
    )}
    <div className="metric-card__sub">{sub}</div>
  </div>
);

// -----------------------------------------------------------------------
// Inline SVGs
// -----------------------------------------------------------------------

const ServerIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="2" y="2" width="20" height="8" rx="2"/><rect x="2" y="14" width="20" height="8" rx="2"/>
    <line x1="6" y1="6" x2="6.01" y2="6"/><line x1="6" y1="18" x2="6.01" y2="18"/>
  </svg>
);

const DatabaseIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <ellipse cx="12" cy="5" rx="9" ry="3"/>
    <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/>
    <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/>
  </svg>
);

const ShieldCheckIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
    <polyline points="9 12 11 14 15 10"/>
  </svg>
);

// -----------------------------------------------------------------------
// Checklist columns
// -----------------------------------------------------------------------

const CHECKLIST_COLUMNS: ColumnDef<ChecklistItem>[] = [
  {
    key: 'test_case',
    header: 'Test Case',
    width: '110px',
    render: (row) => (
      <code style={{ fontSize: '0.8125rem', color: 'var(--text-primary)', fontFamily: 'var(--font-mono)' }}>
        {row.test_case}
      </code>
    ),
  },
  {
    key: 'description',
    header: 'Description',
    render: (row) => (
      <span style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>{row.description}</span>
    ),
  },
  {
    key: 'phase',
    header: 'Phase',
    width: '80px',
    render: (row) => (
      <Badge variant="info" size="sm">Phase {row.phase}</Badge>
    ),
  },
  {
    key: 'status',
    header: 'Status',
    width: '120px',
    render: (row) => {
      const labels: Record<ChecklistStatus, string> = {
        success: 'Passed',
        warning: 'In Progress',
        danger: 'Failed',
        info: 'Running',
        neutral: 'Pending',
      };
      return <Badge variant={row.status}>{labels[row.status]}</Badge>;
    },
  },
];

// -----------------------------------------------------------------------
// DashboardPage
// -----------------------------------------------------------------------

const INITIAL_HEALTH: HealthCheckResult = {
  response: null,
  latencyMs: null,
  checkedAt: null,
  isLoading: true,
  error: null,
};

const DashboardPage: React.FC = () => {
  const { user } = useAuth();
  const [appHealth, setAppHealth] = useState<HealthCheckResult>(INITIAL_HEALTH);
  const [dbHealth, setDbHealth] = useState<HealthCheckResult>(INITIAL_HEALTH);

  const fetchHealth = useCallback(async () => {
    // App health
    setAppHealth((p) => ({ ...p, isLoading: true }));
    try {
      const r = await healthService.getAppHealth();
      setAppHealth({ response: r, latencyMs: null, checkedAt: new Date().toISOString(), isLoading: false, error: null });
    } catch {
      setAppHealth({ response: null, latencyMs: null, checkedAt: null, isLoading: false, error: 'Unreachable' });
    }

    // DB health
    setDbHealth((p) => ({ ...p, isLoading: true }));
    try {
      const r = await healthService.getDbHealth();
      setDbHealth({ response: r, latencyMs: null, checkedAt: new Date().toISOString(), isLoading: false, error: r.status === 'error' ? r.message : null });
    } catch {
      setDbHealth({ response: null, latencyMs: null, checkedAt: null, isLoading: false, error: 'Unreachable' });
    }
  }, []);

  useEffect(() => { void fetchHealth(); }, [fetchHealth]);

  // Derive metric card data from fetched health
  const backendStatus: MetricCardData = {
    label: 'Backend',
    value: appHealth.isLoading ? null : appHealth.response?.status === 'success' ? 'Online' : 'Error',
    sub: 'GET /api/health',
    variant: appHealth.error ? 'error' : 'default',
    isLoading: appHealth.isLoading,
  };

  const databaseStatus: MetricCardData = {
    label: 'Database',
    value: dbHealth.isLoading ? null : dbHealth.response?.status === 'success' ? 'Connected' : 'Error',
    sub: 'GET /api/health/db',
    variant: dbHealth.error ? 'error' : 'default',
    isLoading: dbHealth.isLoading,
  };

  const authStatus: MetricCardData = {
    label: 'Auth',
    value: user ? 'Authenticated' : 'Session Invalid',
    sub: user?.email ?? '—',
    variant: user ? 'default' : 'warning',
    isLoading: false,
  };

  return (
    <main className="dashboard-page">
      <PageHeader
        title="Dashboard"
        subtitle="Phase 0 Foundation — System Status Overview"
      />

      {/* Metric cards */}
      <div className="dashboard-metrics">
        <MetricCard {...backendStatus} icon={<ServerIcon />} />
        <MetricCard {...databaseStatus} icon={<DatabaseIcon />} />
        <MetricCard {...authStatus} icon={<ShieldCheckIcon />} />
      </div>

      {/* Phase 0 QA checklist */}
      <section className="dashboard-section" aria-labelledby="checklist-heading">
        <div className="dashboard-section-title">
          <h2 id="checklist-heading" style={{ fontSize: 'inherit', fontWeight: 'inherit' }}>
            Phase 0 QA Checklist
          </h2>
          <span className="dashboard-section-title__tag">Test Plan</span>
        </div>

        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          <DataTable<ChecklistItem>
            columns={CHECKLIST_COLUMNS}
            data={CHECKLIST}
            isLoading={false}
            getRowKey={(row) => row.id}
          />
        </div>
      </section>

      {/* Quick links */}
      <section className="dashboard-section" aria-labelledby="links-heading">
        <div className="dashboard-section-title">
          <h2 id="links-heading" style={{ fontSize: 'inherit', fontWeight: 'inherit' }}>
            Quick Navigation
          </h2>
        </div>
        <div style={{ display: 'flex', gap: 'var(--space-3)', flexWrap: 'wrap' }}>
          <Link to="/health" className="btn btn--secondary btn--md">
            View Health Details →
          </Link>
          <Link to="/profile" className="btn btn--ghost btn--md">
            My Profile
          </Link>
        </div>
      </section>
    </main>
  );
};

export default DashboardPage;

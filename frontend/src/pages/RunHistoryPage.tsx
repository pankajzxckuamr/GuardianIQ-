import React, { useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { WorkflowRunResponse } from '../types/phase2';
import { PageHeader } from '../components/common/PageHeader';
import { RegistryDataTable } from '../components/common/RegistryDataTable';
import { RiskBadge } from '../components/common/RiskBadge';
import { Button } from '../components/common/Button';
import { ScreenGuide } from '../components/common/ScreenGuide';
import { useAuth } from '../hooks/useAuth';
import { useWorkflowRuns, useCancelRun } from '../hooks/usePhase2Runs';
import { AlertTriangle, RefreshCw, Eye, XCircle } from 'lucide-react';
import styles from './phase2Shared.module.css';

const runStatusPillClass = (status: string): string => {
  switch (status) {
    case 'RUNNING': return `${styles.pillInfo} ${styles.pulsing}`;
    case 'QUEUED': return styles.pillNeutral;
    case 'COMPLETED': return styles.pillSuccess;
    case 'FAILED': return styles.pillDanger;
    case 'CANCELLED': return styles.pillWarning;
    case 'SKIPPED': return styles.pillNeutral;
    case 'RETRY_QUEUED': return styles.pillAccent;
    default: return styles.pillNeutral;
  }
};

const formatDuration = (ms: number | null | undefined): string => {
  if (!ms) return '-';
  const totalSeconds = Math.floor(ms / 1000);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  if (minutes > 0) return `${minutes}m ${seconds}s`;
  return `${seconds}s`;
};

const QUICK_FILTERS = [
  { label: 'Failed', value: 'failed' },
  { label: 'Running', value: 'running' },
  { label: 'High Risk', value: 'high_risk' },
  { label: 'SLA Breached', value: 'sla_breached' },
  { label: 'Manual', value: 'manual' },
  { label: 'Today', value: 'today' },
];

export const RunHistoryPage: React.FC = () => {
  const { currentUser } = useAuth();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  const canView = currentUser?.is_superuser || currentUser?.permissions?.includes('VIEW_WORKFLOW_RUN');
  const canCancel = currentUser?.is_superuser || currentUser?.permissions?.includes('CANCEL_WORKFLOW_RUN');

  const page = parseInt(searchParams.get('page') || '1', 10);
  const perPage = parseInt(searchParams.get('per_page') || '10', 10);
  const triggerType = searchParams.get('trigger_type') || '';
  const searchQ = searchParams.get('search') || '';
  const quickFilter = searchParams.get('quick') || '';

  const { runs, total, loading, error, refetch: fetchRuns } = useWorkflowRuns({
    page,
    per_page: perPage,
    trigger_type: triggerType || undefined,
    search: searchQ || undefined,
    quick: quickFilter || undefined,
    schedule_id: searchParams.get('schedule_id') || undefined,
    workflow_id: searchParams.get('workflow_id') || undefined,
    run_status: searchParams.get('run_status') || undefined,
    risk_level: searchParams.get('risk_level') || undefined,
    date_from: searchParams.get('date_from') || undefined,
    date_to: searchParams.get('date_to') || undefined,
  });
  
  const { cancelRun } = useCancelRun();

  useEffect(() => {
    if (!canView) return;
    fetchRuns();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, perPage, triggerType, searchQ, quickFilter]);

  const updateFilters = (updates: Record<string, string | null>) => {
    const newParams = new URLSearchParams(searchParams);
    Object.entries(updates).forEach(([key, val]) => {
      newParams.delete(key);
      if (val === null) return;
      if (val) newParams.set(key, val);
    });
    if (updates.page === undefined) newParams.set('page', '1');
    setSearchParams(newParams);
  };

  const clearFilters = () => setSearchParams(new URLSearchParams({ page: '1', per_page: perPage.toString() }));
  const hasActiveFilters = !!searchQ || !!triggerType || !!quickFilter;

  const handleCancelRun = async (id: string) => {
    if (!window.confirm('Are you sure you want to cancel this run?')) return;
    await cancelRun(id, fetchRuns);
  };

  const stop = (e: React.MouseEvent) => e.stopPropagation();

  if (!canView) {
    return (
      <div className={styles.page}>
        <div className={styles.breadcrumb}>Orchestration &gt; Run History</div>
        <div className={styles.stateCard}>
          <div className={styles.stateTitle}>Access Restricted</div>
          <div className={styles.stateDesc}>You do not have permission to view workflow runs.</div>
        </div>
      </div>
    );
  }

  const columns = [
    {
      key: 'run_code',
      label: 'Run Code',
      render: (r: WorkflowRunResponse) => (
        <button className={styles.linkCell} onClick={(e) => { stop(e); navigate(`/workflow-runs/${r.id}`); }}>
          {r.run_code}
        </button>
      ),
    },
    {
      key: 'schedule_name',
      label: 'Schedule / Workflow',
      render: (r: any) => (
        <div>
          <div>{r.schedule_name || r.schedule_id}</div>
          <div className={styles.subText}>{r.workflow_name || r.workflow_id}</div>
        </div>
      ),
    },
    { key: 'trigger_type', label: 'Trigger', render: (r: any) => <span className={styles.tagChip}>{r.trigger_type}</span> },
    { key: 'triggered_by', label: 'Triggered By', render: (r: any) => <span className={styles.mutedCell}>{r.triggered_by_name || r.triggered_by_user_id || 'System'}</span> },
    { key: 'run_status', label: 'Status', render: (r: any) => <span className={`${styles.pill} ${runStatusPillClass(r.run_status)}`}>{(r.run_status || '').replace(/_/g, ' ')}</span> },
    { key: 'started_at', label: 'Started At', render: (r: any) => <span className={styles.mutedCell}>{r.started_at ? new Date(r.started_at).toLocaleString() : '-'}</span> },
    { key: 'duration_ms', label: 'Duration', render: (r: any) => <span className={styles.mutedCell}>{formatDuration(r.duration_ms)}</span> },
    { key: 'risk_level', label: 'Risk', render: (r: any) => <RiskBadge level={r.risk_level} /> },
    {
      key: 'actions',
      label: 'Actions',
      render: (r: WorkflowRunResponse) => (
        <div className={styles.actions}>
          <button className={styles.actionBtn} title="Open Run" onClick={(e) => { stop(e); navigate(`/workflow-runs/${r.id}`); }}>
            <Eye size={15} />
          </button>
          {canCancel && r.run_status === 'RUNNING' && (
            <button className={`${styles.actionBtn} ${styles.danger}`} title="Cancel" onClick={(e) => { stop(e); handleCancelRun(r.id); }}>
              <XCircle size={15} />
            </button>
          )}
        </div>
      ),
    },
  ];

  return (
    <div className={styles.page}>
      <div className={styles.breadcrumb}>Orchestration &gt; Run History</div>
      <PageHeader
        title="Run History"
        description="Monitor and audit all automated and manual workflow executions"
        actions={
          <ScreenGuide
            content={
              <div style={{ display: "flex", flexDirection: "column", gap: "12px", paddingRight: "4px" }}>
                <h4 style={{ color: "#fbbf24", margin: "0 0 4px 0", fontSize: "0.85rem" }}>Run History</h4>
                <p style={{ margin: 0 }}>View a comprehensive log of all automated workflow executions. You can filter by status or risk level and select a run to see detailed execution traces.</p>
              </div>
            }
          />
        }
      />

      {/* Filters */}
      <div className={styles.filterBar}>
        <div className={styles.quickFilters}>
          <span className={styles.quickLabel}>Quick Filters</span>
          {QUICK_FILTERS.map(qf => (
            <button
              key={qf.value}
              className={`${styles.checkChip} ${quickFilter === qf.value ? styles.active : ''}`}
              onClick={() => updateFilters({ quick: quickFilter === qf.value ? null : qf.value })}
            >
              {qf.label}
            </button>
          ))}
        </div>

        <div className={styles.filterRow}>
          <div className={styles.searchGroup}>
            <input
              type="text"
              className={styles.searchInput}
              placeholder="Search by run code or schedule name..."
              value={searchQ}
              onChange={(e) => updateFilters({ search: e.target.value })}
            />
          </div>
          <div className={styles.filtersGroup}>
            <select
              className={styles.filterSelect}
              value={triggerType}
              onChange={(e) => updateFilters({ trigger_type: e.target.value })}
            >
              <option value="">All Triggers</option>
              <option value="SCHEDULED">SCHEDULED</option>
              <option value="MANUAL">MANUAL</option>
              <option value="EVENT">EVENT</option>
              <option value="API">API</option>
            </select>
            {hasActiveFilters && (
              <button className={styles.clearBtn} onClick={clearFilters}>Clear Filters</button>
            )}
          </div>
        </div>
      </div>

      {/* Table */}
      <div className={styles.tableContainer}>
        {error ? (
          <div className={styles.stateCard}>
            <AlertTriangle size={36} className={styles.stateIcon} />
            <div className={styles.stateTitle}>Error Loading Runs</div>
            <div className={styles.stateDesc}>{error}</div>
            <Button variant="secondary" size="sm" onClick={fetchRuns} icon={<RefreshCw size={14} />}>Retry</Button>
          </div>
        ) : (
          <RegistryDataTable
            columns={columns}
            data={runs}
            isLoading={loading}
            totalCount={total}
            page={page}
            pageSize={perPage}
            onPageChange={(p) => updateFilters({ page: p.toString() })}
            onRowClick={(r) => navigate(`/workflow-runs/${r.id}`)}
            emptyMessage={hasActiveFilters ? 'No workflow runs match your filters.' : 'No workflow runs found. Active schedules will generate runs automatically, or you can trigger them manually.'}
          />
        )}
      </div>
    </div>
  );
};

export default RunHistoryPage;

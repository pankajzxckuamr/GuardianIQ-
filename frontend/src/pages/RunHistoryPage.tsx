import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { runApi } from '../api/phase2Client';
import { WorkflowRunResponse } from '../types/phase2';
import { PageHeader } from '../components/common/PageHeader';
import { RegistryDataTable } from '../components/common/RegistryDataTable';
import { RiskBadge } from '../components/common/RiskBadge';
import { Button } from '../components/common/Button';
import { useAuth } from '../hooks/useAuth';
import { useToast } from '../hooks/useToast';
import { AlertTriangle, RefreshCw, Eye, XCircle } from 'lucide-react';
import styles from './phase2Shared.module.css';

const runStatusPillClass = (status: string): string => {
  switch (status) {
    case 'RUNNING': return styles.pillInfo;
    case 'COMPLETED': return styles.pillSuccess;
    case 'FAILED': return styles.pillDanger;
    case 'CANCELLED': return styles.pillWarning;
    case 'RETRY_QUEUED': return styles.pillAccent;
    default: return styles.pillNeutral;
  }
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
  const { showToast } = useToast();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  const canView = currentUser?.is_superuser || currentUser?.permissions?.includes('VIEW_WORKFLOW_RUN');
  const canCancel = currentUser?.is_superuser || currentUser?.permissions?.includes('CANCEL_WORKFLOW_RUN');

  const [runs, setRuns] = useState<WorkflowRunResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState(0);

  const page = parseInt(searchParams.get('page') || '1', 10);
  const perPage = parseInt(searchParams.get('per_page') || '20', 10);
  const triggerType = searchParams.get('trigger_type') || '';
  const searchQ = searchParams.get('search') || '';
  const quickFilter = searchParams.get('quick') || '';

  useEffect(() => {
    document.title = 'Run History — GuardianIQ';
  }, []);

  const fetchRuns = async () => {
    setLoading(true);
    setError(null);
    try {
      const params: any = { page, per_page: perPage };
      if (triggerType) params.trigger_type = triggerType;
      if (searchQ) params.search = searchQ;
      if (quickFilter) params.quick = quickFilter;

      const res: any = await runApi.list(params);
      setRuns(res.items || []);
      setTotal(res.total || 0);
    } catch (e: any) {
      setError(e.message || 'Failed to load runs');
    } finally {
      setLoading(false);
    }
  };

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
    try {
      await runApi.cancel(id);
      showToast('Run cancelled successfully', 'success');
      fetchRuns();
    } catch (e: any) {
      showToast(e.message || 'Failed to cancel run', 'error');
    }
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
    { key: 'run_status', label: 'Status', render: (r: any) => <span className={`${styles.pill} ${runStatusPillClass(r.run_status)}`}>{(r.run_status || '').replace(/_/g, ' ')}</span> },
    { key: 'started_at', label: 'Started At', render: (r: any) => <span className={styles.mutedCell}>{r.started_at ? new Date(r.started_at).toLocaleString() : '-'}</span> },
    { key: 'duration_ms', label: 'Duration', render: (r: any) => <span className={styles.mutedCell}>{r.duration_ms ? `${(r.duration_ms / 1000).toFixed(1)}s` : '-'}</span> },
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

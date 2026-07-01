import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { scheduleApi } from '../api/phase2Client';
import { WorkflowScheduleListItem } from '../types/phase2';
import { ConfirmActionModal } from '../components/phase2/ConfirmActionModal';
import { PageHeader } from '../components/common/PageHeader';
import { ScreenGuide } from '../components/common/ScreenGuide';
import { RegistryDataTable } from '../components/common/RegistryDataTable';
import { RiskBadge } from '../components/common/RiskBadge';
import { ScheduleStatusBadge } from '../components/common/ScheduleStatusBadge';
import { Button } from '../components/common/Button';
import { useAuth } from '../hooks/useAuth';
import { useToast } from '../hooks/useToast';
import {
  Play,
  Pause,
  Archive,
  Plus,
  AlertCircle,
  RefreshCw,
  Eye,
  PlayCircle,
} from 'lucide-react';
import styles from './phase2Shared.module.css';

const STATUS_OPTIONS = ['DRAFT', 'PENDING_APPROVAL', 'ACTIVE', 'PAUSED', 'FAILED', 'RETIRED'];
const RISK_OPTIONS = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'];



export const WorkflowSchedulerDashboard: React.FC = () => {
  const { currentUser } = useAuth();
  const { showToast } = useToast();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  // Permissions
  const hasPerm = (p: string) => currentUser?.is_superuser || currentUser?.permissions?.includes(p);
  const canCreate = hasPerm('CREATE_WORKFLOW_SCHEDULE');
  const canViewDetail = hasPerm('VIEW_WORKFLOW_SCHEDULE');
  const canRun = hasPerm('RUN_WORKFLOW_SCHEDULE');
  const canPause = hasPerm('PAUSE_WORKFLOW_SCHEDULE');
  const canResume = hasPerm('RESUME_WORKFLOW_SCHEDULE');
  const canRetire = hasPerm('RETIRE_WORKFLOW_SCHEDULE');

  // State
  const [schedules, setSchedules] = useState<WorkflowScheduleListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState(0);

  const [confirmModal, setConfirmModal] = useState<{
    open: boolean;
    title: string;
    message: string;
    action: 'PAUSE' | 'RESUME' | 'RETIRE' | 'SUBMIT' | null;
    scheduleId: string | null;
    requireReason: boolean;
  }>({ open: false, title: '', message: '', action: null, scheduleId: null, requireReason: false });

  // Read filters from URL
  const page = parseInt(searchParams.get('page') || '1', 10);
  const perPage = parseInt(searchParams.get('per_page') || '20', 10);
  const statuses = searchParams.getAll('status');
  const riskLevels = searchParams.getAll('risk_level');
  const scheduleType = searchParams.get('schedule_type') || '';
  const searchQ = searchParams.get('search') || '';

  useEffect(() => {
    document.title = 'Workflow Scheduler — GuardianIQ';
  }, []);

  const fetchSchedules = async () => {
    setLoading(true);
    setError(null);
    try {
      const params: any = { page, per_page: perPage };
      if (statuses.length > 0) params.status = [...statuses];
      if (riskLevels.length > 0) params.risk_level = [...riskLevels];
      if (scheduleType) params.schedule_type = scheduleType;
      if (searchQ) params.search = searchQ;

      const res: any = await scheduleApi.list(params);
      setSchedules(res.items);
      setTotal(res.total);
    } catch (e: any) {
      setError(e.message || 'Failed to load schedules');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSchedules();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, perPage, searchParams.getAll('status').join(','), searchParams.getAll('risk_level').join(','), scheduleType, searchQ]);

  // KPIs
  const [kpis, setKpis] = useState({ active: 0, pending: 0, paused: 0, failed: 0, draft: 0 });
  useEffect(() => {
    const fetchKpis = async () => {
      try {
        const [activeRes, pendingRes, pausedRes, failedRes, draftRes]: any[] = await Promise.all([
          scheduleApi.list({ per_page: 1, status: 'ACTIVE' }),
          scheduleApi.list({ per_page: 1, status: 'PENDING_APPROVAL' }),
          scheduleApi.list({ per_page: 1, status: 'PAUSED' }),
          scheduleApi.list({ per_page: 1, status: 'FAILED' }),
          scheduleApi.list({ per_page: 1, status: 'DRAFT' }),
        ]);
        setKpis({
          active: activeRes.total || 0,
          pending: pendingRes.total || 0,
          paused: pausedRes.total || 0,
          failed: failedRes.total || 0,
          draft: draftRes.total || 0,
        });
      } catch (e) {
        console.error('Failed to load KPIs', e);
      }
    };
    fetchKpis();
  }, []);

  const updateFilters = (updates: Record<string, string | string[]>) => {
    const newParams = new URLSearchParams(searchParams);
    Object.entries(updates).forEach(([key, val]) => {
      newParams.delete(key);
      if (Array.isArray(val)) {
        val.forEach(v => newParams.append(key, v));
      } else if (val) {
        newParams.set(key, val);
      }
    });
    if (updates.page === undefined) newParams.set('page', '1');
    setSearchParams(newParams);
  };

  const clearFilters = () => {
    setSearchParams(new URLSearchParams({ page: '1', per_page: perPage.toString() }));
  };

  const hasActiveFilters = statuses.length > 0 || riskLevels.length > 0 || !!searchQ || !!scheduleType;

  const toggleMulti = (key: 'status' | 'risk_level', value: string, current: string[]) => {
    const next = current.includes(value) ? current.filter(x => x !== value) : [...current, value];
    updateFilters({ [key]: next });
  };

  const handleRunNow = async (id: string) => {
    try {
      await scheduleApi.runNow(id);
      showToast('Workflow triggered successfully', 'success');
      fetchSchedules();
    } catch (e: any) {
      showToast(e.message || 'Failed to trigger run', 'error');
    }
  };

  const handleConfirmAction = async () => {
    const { action, scheduleId } = confirmModal;
    if (!action || !scheduleId) return;
    try {
      if (action === 'PAUSE') await scheduleApi.pause(scheduleId);
      if (action === 'RESUME') await scheduleApi.resume(scheduleId);
      if (action === 'RETIRE') await scheduleApi.retire(scheduleId);
      if (action === 'SUBMIT') await scheduleApi.submit(scheduleId);
      showToast(`Schedule ${action.toLowerCase()}d successfully`, 'success');
      setConfirmModal({ ...confirmModal, open: false });
      fetchSchedules();
    } catch (e: any) {
      showToast(e.message || `Failed to ${action.toLowerCase()} schedule`, 'error');
    }
  };

  const renderHealth = (health: string) => {
    switch (health) {
      case 'HEALTHY': return <span className={styles.health}><span className={`${styles.healthDot} ${styles.dotSuccess}`} /> Healthy</span>;
      case 'ATTENTION': return <span className={styles.health}><span className={`${styles.healthDot} ${styles.dotWarning}`} /> Attention</span>;
      case 'FAILED': return <span className={styles.health}><span className={`${styles.healthDot} ${styles.dotDanger}`} /> Failed</span>;
      case 'SLA_BREACHED': return <span className={styles.health}><span className={`${styles.healthDot} ${styles.dotDanger}`} /> SLA Breached</span>;
      default: return <span className={styles.mutedCell}>-</span>;
    }
  };

  const stop = (e: React.MouseEvent) => e.stopPropagation();

  const columns = [
    {
      key: 'schedule_name',
      label: 'Schedule Name',
      render: (s: WorkflowScheduleListItem) => (
        <div>
          {canViewDetail ? (
            <button className={styles.linkCell} onClick={(e) => { stop(e); navigate(`/workflow-scheduler/${s.id}`); }}>
              {s.schedule_name}
            </button>
          ) : (
            <span>{s.schedule_name}</span>
          )}
          <div className={styles.subText}>{s.schedule_code}</div>
        </div>
      ),
    },
    { key: 'workflow_name', label: 'Workflow', render: (s: any) => <span className={styles.mutedCell}>{s.workflow_name || '-'}</span> },
    { key: 'schedule_type', label: 'Type', render: (s: any) => <span className={styles.tagChip}>{s.schedule_type}</span> },
    { key: 'schedule_status', label: 'Status', render: (s: any) => <ScheduleStatusBadge status={s.schedule_status} /> },
    { key: 'risk_level', label: 'Risk', render: (s: any) => <RiskBadge level={s.risk_level} /> },
    { key: 'owner_name', label: 'Owner', render: (s: any) => <span className={styles.mutedCell}>{s.owner_name || s.owner_user_id || '-'}</span> },
    { key: 'health_status', label: 'Health', render: (s: any) => renderHealth(s.health_status) },
    {
      key: 'next_run_at',
      label: 'Next Run',
      render: (s: any) => (
        <span className={styles.mutedCell}>
          {s.schedule_type === 'MANUAL' ? 'Manual only' : (s.next_run_at ? new Date(s.next_run_at).toLocaleString() : 'Never')}
        </span>
      ),
    },
    {
      key: 'last_run_at',
      label: 'Last Run',
      render: (s: any) => (
        <span className={styles.mutedCell}>
          {s.last_run_at ? new Date(s.last_run_at).toLocaleString() : 'Never'}
        </span>
      ),
    },
    {
      key: 'actions',
      label: 'Actions',
      render: (s: WorkflowScheduleListItem) => (
        <div className={styles.actions}>
          {canViewDetail && (
            <button className={styles.actionBtn} title="View Details" onClick={(e) => { stop(e); navigate(`/workflow-scheduler/${s.id}`); }}>
              <Eye size={15} />
            </button>
          )}
          {canCreate && s.schedule_status === 'DRAFT' && (
            <>
              <button className={`${styles.actionBtn} ${styles.primary}`} title="Edit" onClick={(e) => { stop(e); navigate(`/workflow-scheduler/${s.id}/edit`); }}>
                Edit
              </button>
              <button className={`${styles.actionBtn} ${styles.success}`} title="Submit for Approval" onClick={(e) => { stop(e); setConfirmModal({ open: true, title: 'Submit Schedule', message: 'Submit this schedule for approval or activation?', action: 'SUBMIT' as any, scheduleId: s.id, requireReason: false }); }}>
                Submit
              </button>
            </>
          )}
          {canRun && s.schedule_status === 'ACTIVE' && (
            <button className={`${styles.actionBtn} ${styles.run}`} title="Run Now" onClick={(e) => { stop(e); handleRunNow(s.id); }}>
              <Play size={15} />
            </button>
          )}
          {canPause && s.schedule_status === 'ACTIVE' && (
            <button className={`${styles.actionBtn} ${styles.warning}`} title="Pause" onClick={(e) => { stop(e); setConfirmModal({ open: true, title: 'Pause Schedule', message: 'Are you sure you want to pause this schedule? It will not trigger until resumed.', action: 'PAUSE', scheduleId: s.id, requireReason: false }); }}>
              <Pause size={15} />
            </button>
          )}
          {canResume && s.schedule_status === 'PAUSED' && (
            <button className={`${styles.actionBtn} ${styles.success}`} title="Resume" onClick={(e) => { stop(e); setConfirmModal({ open: true, title: 'Resume Schedule', message: 'Are you sure you want to resume this schedule?', action: 'RESUME', scheduleId: s.id, requireReason: false }); }}>
              <PlayCircle size={15} />
            </button>
          )}
          {canRetire && s.schedule_status !== 'RETIRED' && (
            <button className={`${styles.actionBtn} ${styles.danger}`} title="Retire" onClick={(e) => { stop(e); setConfirmModal({ open: true, title: 'Retire Schedule', message: 'Are you sure you want to permanently retire this schedule? This action cannot be undone.', action: 'RETIRE', scheduleId: s.id, requireReason: true }); }}>
              <Archive size={15} />
            </button>
          )}
        </div>
      ),
    },
  ];

  return (
    <div className={styles.page}>
      <div className={styles.breadcrumb}>Orchestration &gt; Workflow Scheduler</div>
      <PageHeader
        title="Workflow Scheduler"
        description="Manage and monitor automated execution schedules"
        actions={
          <>
            {canCreate && (
              <Button variant="primary" onClick={() => navigate('/workflow-scheduler/new')} icon={<Plus size={16} />}>
                Create Schedule
              </Button>
            )}
            <ScreenGuide
              content={
                <div style={{ display: "flex", flexDirection: "column", gap: "12px", paddingRight: "4px" }}>
                  <h4 style={{ color: "#fbbf24", margin: "0 0 4px 0", fontSize: "0.85rem" }}>Workflow Scheduler</h4>
                  <p style={{ margin: 0 }}>Manage and monitor automated execution schedules. You can create new schedules, view their status, and perform actions like pausing or resuming them.</p>
                </div>
              }
            />
          </>
        }
      />

      {/* KPIs */}
      <div className={styles.kpiGrid}>
        <div className={`${styles.kpiCard} ${styles.clickableCard}`} onClick={() => updateFilters({ status: ['ACTIVE'] })}>
          <span className={styles.kpiLabel}>Active</span>
          <span className={`${styles.kpiValue} ${styles.success}`}>{kpis.active}</span>
        </div>
        <div className={`${styles.kpiCard} ${styles.clickableCard}`} onClick={() => updateFilters({ status: ['PENDING_APPROVAL'] })}>
          <span className={styles.kpiLabel}>Pending Approval</span>
          <span className={`${styles.kpiValue} ${styles.warning}`}>{kpis.pending}</span>
        </div>
        <div className={`${styles.kpiCard} ${styles.clickableCard}`} onClick={() => updateFilters({ status: ['PAUSED'] })}>
          <span className={styles.kpiLabel}>Paused</span>
          <span className={`${styles.kpiValue} ${styles.info}`}>{kpis.paused}</span>
        </div>
        <div className={`${styles.kpiCard} ${styles.clickableCard}`} onClick={() => updateFilters({ status: ['FAILED'] })}>
          <span className={styles.kpiLabel}>Failed</span>
          <span className={`${styles.kpiValue} ${styles.danger}`}>{kpis.failed}</span>
        </div>
        <div className={`${styles.kpiCard} ${styles.clickableCard}`} onClick={() => updateFilters({ status: ['DRAFT'] })}>
          <span className={styles.kpiLabel}>Draft</span>
          <span className={styles.kpiValue}>{kpis.draft}</span>
        </div>
      </div>

      {/* Filters */}
      <div className={styles.filterBar}>
        <div className={styles.filterRow}>
          <div className={styles.searchGroup}>
            <input
              type="text"
              className={styles.searchInput}
              placeholder="Search schedules by name or code..."
              value={searchQ}
              onChange={(e) => updateFilters({ search: e.target.value })}
            />
          </div>
          <div className={styles.filtersGroup}>
            <select
              className={styles.filterSelect}
              value={scheduleType}
              onChange={(e) => updateFilters({ schedule_type: e.target.value })}
            >
              <option value="">All Types</option>
              <option value="CRON">CRON</option>
              <option value="DAILY">DAILY</option>
              <option value="WEEKLY">WEEKLY</option>
              <option value="INTERVAL">INTERVAL</option>
              <option value="MANUAL">MANUAL</option>
            </select>
            {hasActiveFilters && (
              <button className={styles.clearBtn} onClick={clearFilters}>Clear All Filters</button>
            )}
          </div>
        </div>

        <div className={styles.checkSection}>
          <div>
            <span className={styles.checkGroupLabel}>Status</span>
            <div className={styles.checkChips}>
              {STATUS_OPTIONS.map(st => (
                <button
                  key={st}
                  className={`${styles.checkChip} ${statuses.includes(st) ? styles.active : ''}`}
                  onClick={() => toggleMulti('status', st, statuses)}
                >
                  {st.replace(/_/g, ' ')}
                </button>
              ))}
            </div>
          </div>
          <div>
            <span className={styles.checkGroupLabel}>Risk Level</span>
            <div className={styles.checkChips}>
              {RISK_OPTIONS.map(rl => (
                <button
                  key={rl}
                  className={`${styles.checkChip} ${riskLevels.includes(rl) ? styles.active : ''}`}
                  onClick={() => toggleMulti('risk_level', rl, riskLevels)}
                >
                  {rl}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className={styles.tableContainer}>
        {error ? (
          <div className={styles.stateCard}>
            <AlertCircle size={36} className={styles.stateIcon} />
            <div className={styles.stateTitle}>Error Loading Schedules</div>
            <div className={styles.stateDesc}>{error}</div>
            <Button variant="secondary" size="sm" onClick={fetchSchedules} icon={<RefreshCw size={14} />}>Retry</Button>
          </div>
        ) : (
          <RegistryDataTable
            columns={columns}
            data={schedules}
            isLoading={loading}
            totalCount={total}
            page={page}
            pageSize={perPage}
            onPageChange={(p) => updateFilters({ page: p.toString() })}
            onRowClick={canViewDetail ? (s) => navigate(`/workflow-scheduler/${s.id}`) : undefined}
            emptyMessage={hasActiveFilters ? 'No schedules match your filters. Try clearing or adjusting them.' : 'No governed schedules configured. Create your first schedule to get started.'}
          />
        )}
      </div>

      <ConfirmActionModal
        open={confirmModal.open}
        title={confirmModal.title}
        message={confirmModal.message}
        requireReason={confirmModal.requireReason}
        onConfirm={handleConfirmAction}
        onCancel={() => setConfirmModal({ ...confirmModal, open: false })}
      />
    </div>
  );
};

export default WorkflowSchedulerDashboard;

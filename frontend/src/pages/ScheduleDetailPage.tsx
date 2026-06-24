import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { scheduleApi, runApi } from '../api/phase2Client';
import { WorkflowScheduleResponse, ApprovalResponse, HistoryResponse } from '../types/phase2';
import { ConfirmActionModal } from '../components/phase2/ConfirmActionModal';
import { AgentAssignmentPanel } from '../components/phase2/AgentAssignmentPanel';
import { AuditTimelinePanel } from '../components/phase2/AuditTimelinePanel';
import { RiskBadge } from '../components/common/RiskBadge';
import { Button } from '../components/common/Button';
import { useAuth } from '../hooks/useAuth';
import { useToast } from '../hooks/useToast';
import { Play, ArrowLeft } from 'lucide-react';
import styles from './phase2Shared.module.css';

const TABS = ['OVERVIEW', 'AGENTS', 'BOUNDARIES', 'TIMING', 'APPROVALS', 'RUNS', 'AUDIT', 'HISTORY'] as const;
type Tab = typeof TABS[number];

const statusPillClass = (status: string): string => {
  switch (status) {
    case 'ACTIVE': return styles.pillSuccess;
    case 'PENDING_APPROVAL': return styles.pillWarning;
    case 'PAUSED': return styles.pillInfo;
    case 'FAILED': return styles.pillDanger;
    default: return styles.pillNeutral;
  }
};

export const ScheduleDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const { currentUser } = useAuth();
  const { showToast } = useToast();
  const navigate = useNavigate();

  const [schedule, setSchedule] = useState<WorkflowScheduleResponse | null>(null);
  const [approvals, setApprovals] = useState<ApprovalResponse[]>([]);
  const [history, setHistory] = useState<HistoryResponse[]>([]);
  const [runs, setRuns] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<Tab>('OVERVIEW');

  const [confirmModal, setConfirmModal] = useState<{
    open: boolean;
    title: string;
    message: string;
    action: 'PAUSE' | 'RESUME' | 'RETIRE' | 'SUBMIT' | 'ACTIVATE' | null;
    requireReason: boolean;
  }>({ open: false, title: '', message: '', action: null, requireReason: false });

  const hasPerm = (p: string) => currentUser?.is_superuser || currentUser?.permissions?.includes(p);

  const fetchData = async () => {
    if (!id) return;
    setLoading(true);
    try {
      const [schedRes, appRes, histRes, runsRes] = await Promise.all([
        scheduleApi.getById(id),
        scheduleApi.getApprovals(id).catch(() => []),
        scheduleApi.getHistory(id).catch(() => []),
        runApi.list({ schedule_id: id, per_page: 5 }).catch(() => ({ items: [] })),
      ]);
      setSchedule(((schedRes as any).schedule || schedRes) as WorkflowScheduleResponse);
      setApprovals(appRes as any);
      setHistory(histRes as any);
      setRuns((runsRes as any).items || []);
    } catch (e: any) {
      setError(e.message || 'Failed to load schedule');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  const handleAction = async () => {
    const action = confirmModal.action;
    if (!action || !id) return;
    try {
      if (action === 'PAUSE') await scheduleApi.pause(id);
      if (action === 'RESUME') await scheduleApi.resume(id);
      if (action === 'RETIRE') await scheduleApi.retire(id);
      if (action === 'SUBMIT') await scheduleApi.submit(id);
      if (action === 'ACTIVATE') await scheduleApi.activate(id);
      showToast(`Action ${action.toLowerCase()} completed successfully`, 'success');
      setConfirmModal({ ...confirmModal, open: false });
      fetchData();
    } catch (e: any) {
      showToast(e.message || 'Failed to perform action', 'error');
    }
  };

  const handleRunNow = async () => {
    if (!id) return;
    try {
      await scheduleApi.runNow(id);
      showToast('Run triggered successfully', 'success');
      fetchData();
    } catch (e: any) {
      showToast(e.message || 'Failed to trigger run', 'error');
    }
  };

  if (loading) {
    return (
      <div className={styles.page}>
        <div className={styles.stateCard}><div className={styles.stateDesc}>Loading schedule...</div></div>
      </div>
    );
  }
  if (error || !schedule) {
    return (
      <div className={styles.page}>
        <div className={styles.stateCard}>
          <div className={styles.stateTitle}>Unable to load schedule</div>
          <div className={styles.stateDesc}>{error || 'Schedule not found'}</div>
          <Button variant="secondary" size="sm" onClick={() => navigate('/workflow-scheduler')} icon={<ArrowLeft size={14} />}>Back to Scheduler</Button>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.page}>
      <button className={styles.clearBtn} onClick={() => navigate('/workflow-scheduler')} style={{ alignSelf: 'flex-start' }}>
        <ArrowLeft size={14} /> Back to Scheduler
      </button>

      {/* Header */}
      <div className={styles.detailHeaderCard}>
        <div className={styles.detailTopRow}>
          <div>
            <div className={styles.titleRow}>
              <h1 className={styles.detailH1}>{schedule.schedule_name}</h1>
              <span className={`${styles.pill} ${statusPillClass(schedule.schedule_status)}`}>{(schedule.schedule_status || '').replace(/_/g, ' ')}</span>
              <RiskBadge level={schedule.risk_level} />
            </div>
            <div className={styles.monoCode}>{schedule.schedule_code}</div>
              <div className={styles.headerMetaRow}>
              <div className={styles.metaItem}><span className={styles.metaLabel}>Owner</span><span className={styles.metaValue}>{(schedule as any).owner_name || schedule.owner_user_id}</span></div>
              <div className={styles.metaItem}><span className={styles.metaLabel}>Next Run</span><span className={styles.metaValue}>{schedule.next_run_at ? new Date(schedule.next_run_at).toLocaleString() : 'Manual only'} ({schedule.timezone})</span></div>
              <div className={styles.metaItem}><span className={styles.metaLabel}>Last Run</span><span className={styles.metaValue}>{schedule.last_run_at ? new Date(schedule.last_run_at).toLocaleString() : 'Never'}</span></div>
            </div>
          </div>
          <div className={styles.headerActions}>
            {schedule.schedule_status === 'DRAFT' && hasPerm('CREATE_WORKFLOW_SCHEDULE') && (
              <Button variant="secondary" size="sm" onClick={() => setConfirmModal({ open: true, title: 'Submit Schedule', message: 'Submit this schedule for approval or activation?', action: 'SUBMIT', requireReason: false })}>Submit</Button>
            )}
            {schedule.schedule_status === 'PENDING_APPROVAL' && hasPerm('ACTIVATE_WORKFLOW_SCHEDULE') && (
              <Button variant="primary" size="sm" onClick={() => navigate('/schedule-approvals')}>Go to Approvals</Button>
            )}
            {schedule.schedule_status === 'ACTIVE' && hasPerm('RUN_WORKFLOW_SCHEDULE') && (
              <Button variant="primary" size="sm" onClick={handleRunNow} icon={<Play size={14} />}>Run Now</Button>
            )}
            {schedule.schedule_status === 'ACTIVE' && hasPerm('PAUSE_WORKFLOW_SCHEDULE') && (
              <Button variant="secondary" size="sm" onClick={() => setConfirmModal({ open: true, title: 'Pause', message: 'Pause this schedule?', action: 'PAUSE', requireReason: false })}>Pause</Button>
            )}
            {schedule.schedule_status === 'PAUSED' && hasPerm('RESUME_WORKFLOW_SCHEDULE') && (
              <Button variant="secondary" size="sm" onClick={() => setConfirmModal({ open: true, title: 'Resume', message: 'Resume this schedule?', action: 'RESUME', requireReason: false })}>Resume</Button>
            )}
            {schedule.schedule_status !== 'RETIRED' && hasPerm('RETIRE_WORKFLOW_SCHEDULE') && (
              <Button variant="danger" size="sm" onClick={() => setConfirmModal({ open: true, title: 'Retire', message: 'Permanently retire schedule?', action: 'RETIRE', requireReason: true })}>Retire</Button>
            )}
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className={styles.detailCard}>
        <div className={styles.detailTabsHeader}>
          <nav className={styles.detailTabsNav}>
            {TABS.map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`${styles.tabLink} ${activeTab === tab ? styles.activeTab : ''}`}
              >
                {tab.charAt(0) + tab.slice(1).toLowerCase()}
              </button>
            ))}
          </nav>
        </div>

        <div className={styles.tabBody}>
          {activeTab === 'OVERVIEW' && (
            <div className={styles.fieldStack}>
              {schedule.schedule_status === 'PENDING_APPROVAL' && (
                <div className={styles.banner}>
                  This schedule is pending approval.
                  <button className={styles.textBtn} onClick={() => navigate('/schedule-approvals')} style={{ marginLeft: 6 }}>View Queue</button>
                </div>
              )}
              <div className={styles.dlGrid}>
                <div><div className={styles.dlLabel}>Workflow</div><div className={styles.dlValue}>{(schedule as any).workflow_name || schedule.workflow_id}</div></div>
                <div><div className={styles.dlLabel}>Health Status</div><div className={styles.dlValue}>{schedule.health_status}</div></div>
              </div>

              <div>
                <h3 className={styles.sectionHeading}>Recent Runs</h3>
                <div className={styles.miniTableWrap}>
                  <table className={styles.miniTable}>
                    <thead>
                      <tr><th>Run Code</th><th>Status</th><th>Duration</th></tr>
                    </thead>
                    <tbody>
                      {runs.map(r => (
                        <tr key={r.id}>
                          <td><button className={styles.linkCell} onClick={() => navigate(`/workflow-runs/${r.id}`)}>{r.run_code}</button></td>
                          <td>{r.run_status}</td>
                          <td>{r.duration_ms ? `${(r.duration_ms / 1000).toFixed(1)}s` : '-'}</td>
                        </tr>
                      ))}
                      {runs.length === 0 && <tr><td colSpan={3} className={styles.miniEmpty}>No runs yet</td></tr>}
                    </tbody>
                  </table>
                </div>
                <div className={styles.rightLink}>
                  <button className={styles.textBtn} onClick={() => setActiveTab('RUNS')}>View all runs &rarr;</button>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'AGENTS' && (
            <div className={styles.fieldStack}>
              {schedule.agent_assignments?.map((aa, i) => (
                <AgentAssignmentPanel key={i} assignment={aa} readonly={true} />
              ))}
              {(!schedule.agent_assignments || schedule.agent_assignments.length === 0) && (
                <p className={styles.stateDesc}>No agent assignments.</p>
              )}
            </div>
          )}

          {activeTab === 'BOUNDARIES' && (
            <div className={styles.fieldStack}>
              <h3 className={styles.subHeading}>Configured Limits</h3>
              <ul className={styles.bulletList}>
                <li>Max Runtime: {schedule.max_runtime_seconds}s</li>
                <li>Allowed Tools: {schedule.agent_assignments?.[0]?.allowed_tools_json?.join(', ') || 'None'}</li>
                <li>Blocked Ops: {schedule.agent_assignments?.[0]?.blocked_operations_json?.join(', ') || 'None'}</li>
              </ul>
            </div>
          )}

          {activeTab === 'TIMING' && (
            <div className={styles.dlGrid}>
              <div><div className={styles.dlLabel}>Type</div><div className={styles.dlValue}>{schedule.schedule_type}</div></div>
              <div><div className={styles.dlLabel}>Cron</div><div className={styles.dlValue}>{schedule.cron_expression || '-'}</div></div>
              <div><div className={styles.dlLabel}>Timezone</div><div className={styles.dlValue}>{schedule.timezone}</div></div>
              <div><div className={styles.dlLabel}>Concurrency Policy</div><div className={styles.dlValue}>{schedule.concurrency_policy}</div></div>
            </div>
          )}

          {activeTab === 'APPROVALS' && (
            <div className={styles.miniTableWrap}>
              <table className={styles.miniTable}>
                <thead>
                  <tr><th>Type</th><th>Status</th><th>Approver</th><th>Reason</th><th>Date</th></tr>
                </thead>
                <tbody>
                  {approvals.map(a => (
                    <tr key={a.id}>
                      <td>{a.approval_type}</td>
                      <td>{a.approval_status}</td>
                      <td>{a.approver_user_id || '-'}</td>
                      <td>{a.decision_reason || '-'}</td>
                      <td>{a.decided_at ? new Date(a.decided_at).toLocaleString() : '-'}</td>
                    </tr>
                  ))}
                  {approvals.length === 0 && <tr><td colSpan={5} className={styles.miniEmpty}>No approval records found</td></tr>}
                </tbody>
              </table>
            </div>
          )}

          {activeTab === 'RUNS' && (
            <div className={styles.stateCard} style={{ border: 'none', background: 'transparent' }}>
              <div className={styles.stateDesc}>View full paginated runs for this schedule in the Run History page.</div>
              <Button variant="secondary" size="sm" onClick={() => navigate(`/workflow-runs?search=${schedule.schedule_code}`)}>Open Run History</Button>
            </div>
          )}

          {activeTab === 'AUDIT' && (
            <AuditTimelinePanel entityType="WORKFLOW_SCHEDULE" entityId={id || ''} />
          )}

          {activeTab === 'HISTORY' && (
            <div className={styles.miniTableWrap}>
              <table className={styles.miniTable}>
                <thead>
                  <tr><th>Type</th><th>Summary</th><th>User</th><th>Date</th></tr>
                </thead>
                <tbody>
                  {history.map(h => (
                    <tr key={h.id}>
                      <td>{h.change_type}</td>
                      <td>{h.change_summary}</td>
                      <td>{h.changed_by || 'System'}</td>
                      <td>{new Date(h.created_at).toLocaleString()}</td>
                    </tr>
                  ))}
                  {history.length === 0 && <tr><td colSpan={4} className={styles.miniEmpty}>No change history found</td></tr>}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      <ConfirmActionModal
        open={confirmModal.open}
        title={confirmModal.title}
        message={confirmModal.message}
        requireReason={confirmModal.requireReason}
        onConfirm={handleAction}
        onCancel={() => setConfirmModal({ ...confirmModal, open: false })}
      />
    </div>
  );
};

export default ScheduleDetailPage;

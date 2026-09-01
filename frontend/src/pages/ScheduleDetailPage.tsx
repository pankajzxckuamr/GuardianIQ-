import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { scheduleApi, runApi } from '../api/phase2Client';
import { WorkflowScheduleResponse, ApprovalResponse, HistoryResponse } from '../types/phase2';
import { ConfirmActionModal } from '../components/phase2/ConfirmActionModal';
import { AgentAssignmentPanel } from '../components/phase2/AgentAssignmentPanel';
import { AuditTimelinePanel } from '../components/phase2/AuditTimelinePanel';
import { RiskBadge } from '../components/common/RiskBadge';
import { Button } from '../components/common/Button';
import { ScreenGuide } from '../components/common/ScreenGuide';
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
  const [isActionLoading, setIsActionLoading] = useState(false);
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
      const [schedRes, appRes, histRes, runsRes]: any = await Promise.all([
        scheduleApi.getById(id),
        scheduleApi.getApprovals(id).catch(() => []),
        scheduleApi.getHistory(id).catch(() => []),
        runApi.list({ schedule_id: id, per_page: 5 }).catch(() => ({ items: [] })),
      ]);
      setSchedule(((schedRes as any)?.schedule || (schedRes as any)?.data?.schedule || schedRes) as WorkflowScheduleResponse);
      const appList = Array.isArray(appRes) ? appRes : (appRes?.items || appRes?.data?.items || appRes?.data || []);
      setApprovals(Array.isArray(appList) ? appList : []);
      const histList = Array.isArray(histRes) ? histRes : (histRes?.items || histRes?.data?.items || histRes?.data || []);
      setHistory(Array.isArray(histList) ? histList : []);
      setRuns(runsRes?.items || runsRes?.data?.items || (Array.isArray(runsRes) ? runsRes : []));
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
    setIsActionLoading(true);
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
    } finally {
      setIsActionLoading(false);
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
      <button className={styles.clearBtn} onClick={() => window.history.state && window.history.state.idx > 0 ? navigate(-1) : navigate('/workflow-scheduler')} style={{ alignSelf: 'flex-start' }}>
        <ArrowLeft size={14} /> Back
      </button>

      <ScreenGuide
        id="schedule-detail-guide"
        title="Schedule Details"
        description="View and manage the configuration, approvals, and execution history for this specific workflow schedule. Use the tabs below to explore different aspects of the schedule."
      />

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
              <div className={styles.metaItem}><span className={styles.metaLabel}>Owner</span><span className={styles.metaValue}>{schedule.owner_name || schedule.owner_user_id}</span></div>
              <div className={styles.metaItem}><span className={styles.metaLabel}>Next Run</span><span className={styles.metaValue}>{schedule.next_run_at ? new Date(schedule.next_run_at).toLocaleString() : 'Manual only'} ({schedule.timezone})</span></div>
              <div className={styles.metaItem}><span className={styles.metaLabel}>Last Run</span><span className={styles.metaValue}>{schedule.last_run_at ? new Date(schedule.last_run_at).toLocaleString() : 'Never'}</span></div>
            </div>
          </div>
          <div className={styles.headerActions}>
            {schedule.schedule_status === 'DRAFT' && hasPerm('CREATE_WORKFLOW_SCHEDULE') && (
              <>
                <Button variant="secondary" size="sm" onClick={() => navigate(`/workflow-scheduler/${schedule.id}/edit`)}>Edit</Button>
                <Button variant="secondary" size="sm" onClick={() => setConfirmModal({ open: true, title: 'Submit Schedule', message: 'Submit this schedule for approval or activation?', action: 'SUBMIT', requireReason: false })}>Submit</Button>
              </>
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
              {['REJECTED', 'ESCALATED', 'CHANGES_REQUESTED'].includes(schedule.schedule_status || '') && approvals.length > 0 && approvals[0]?.decision_reason && (
                <div className={styles.banner} style={{ backgroundColor: 'var(--color-danger-bg)', color: 'var(--color-danger-fg)' }}>
                  <strong>{schedule.schedule_status.replace('_', ' ')}:</strong> {approvals[0].decision_reason}
                </div>
              )}
              <div className={styles.dlGrid}>
                <div><div className={styles.dlLabel}>Workflow</div><div className={styles.dlValue}>{schedule.workflow_name || schedule.workflow_id}</div></div>
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
              <div><div className={styles.dlLabel}>Start Date</div><div className={styles.dlValue}>{schedule.start_at ? new Date(schedule.start_at).toLocaleString() : 'Immediate'}</div></div>
              <div><div className={styles.dlLabel}>End Date</div><div className={styles.dlValue}>{schedule.end_at ? new Date(schedule.end_at).toLocaleString() : 'Never'}</div></div>
            </div>
          )}

          {activeTab === 'APPROVALS' && (
            <div className={styles.miniTableWrap}>
              <table className={styles.miniTable}>
                <thead>
                  <tr>
                    <th>Stage & Department</th>
                    <th>Status</th>
                    <th>Approver / Decider</th>
                    <th>Decision Note / Reason</th>
                    <th>Date</th>
                  </tr>
                </thead>
                <tbody>
                  {approvals.map(a => {
                    const deptLabel = a.department_name || (a.department_code ? a.department_code.replace(/_/g, ' ') : `Layer ${a.approval_layer || 1}`);
                    const approver = a.decided_by_name 
                      ? `${a.decided_by_name} (${a.decided_by_email || ''})`
                      : a.approver_name 
                      ? `${a.approver_name} (${a.approver_email || ''})`
                      : (a.decided_by || a.approver_user_id || '-');
                    const isApproved = a.approval_status === 'APPROVED';
                    const isPending = a.approval_status === 'PENDING';
                    const isRejected = a.approval_status === 'REJECTED';
                    const isWaiting = a.approval_status === 'WAITING';
                    
                    return (
                      <tr key={a.id}>
                        <td>
                          <span style={{ fontWeight: 600, color: '#f8fafc' }}>
                            Stage {a.approval_layer || 1}: {deptLabel}
                          </span>
                        </td>
                        <td>
                          <span className={`${styles.pill} ${isApproved ? styles.pillSuccess : isPending ? styles.pillWarning : isRejected ? styles.pillDanger : styles.pillMuted}`}>
                            {isWaiting ? 'AWAITING PRIOR STAGE' : a.approval_status}
                          </span>
                        </td>
                        <td>{approver}</td>
                        <td style={{ maxWidth: '280px' }}>{a.decision_reason || a.skip_reason || (isWaiting ? 'Awaiting prior stage approval' : '-')}</td>
                        <td>{a.decided_at ? new Date(a.decided_at).toLocaleString() : a.created_at ? new Date(a.created_at).toLocaleString() : '-'}</td>
                      </tr>
                    );
                  })}
                  {approvals.length === 0 && <tr><td colSpan={5} className={styles.miniEmpty}>No approval records found</td></tr>}
                </tbody>
              </table>
            </div>
          )}

          {activeTab === 'RUNS' && (
            <div className={styles.fieldStack}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <h3 className={styles.sectionHeading} style={{ margin: 0 }}>Performed Runs</h3>
                <Button variant="secondary" size="sm" onClick={() => navigate(`/workflow-runs?search=${schedule.schedule_code}`)}>
                  Open Run History
                </Button>
              </div>
              <div className={styles.miniTableWrap}>
                <table className={styles.miniTable}>
                  <thead>
                    <tr>
                      <th>Run Code</th>
                      <th>Trigger</th>
                      <th>Status</th>
                      <th>Started At</th>
                      <th>Duration</th>
                    </tr>
                  </thead>
                  <tbody>
                    {runs.map(r => (
                      <tr key={r.id}>
                        <td>
                          <button className={styles.linkCell} onClick={() => navigate(`/workflow-runs/${r.id}`)}>
                            {r.run_code}
                          </button>
                        </td>
                        <td>
                          <span className={styles.tagChip}>
                            {r.trigger_type}
                          </span>
                        </td>
                        <td>
                          <span className={`${styles.pill} ${runStatusPillClass(r.run_status)}`}>
                            {(r.run_status || '').replace(/_/g, ' ')}
                          </span>
                        </td>
                        <td>
                          <span className={styles.mutedCell} style={{ fontSize: '0.85rem' }}>
                            {r.started_at ? new Date(r.started_at).toLocaleString() : '-'}
                          </span>
                        </td>
                        <td>
                          <span className={styles.mutedCell} style={{ fontSize: '0.85rem' }}>
                            {r.duration_ms ? `${(r.duration_ms / 1000).toFixed(1)}s` : '-'}
                          </span>
                        </td>
                      </tr>
                    ))}
                    {runs.length === 0 && (
                      <tr>
                        <td colSpan={5} className={styles.miniEmpty}>
                          No performed runs found
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
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
                      <td>{h.changed_by_name || h.changed_by || 'System'}</td>
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
        isLoading={isActionLoading}
      />
    </div>
  );
};

export default ScheduleDetailPage;

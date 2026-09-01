import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { useToast } from '../hooks/useToast';
import { scheduleApi } from '../api/phase2Client';
import { PageHeader } from '../components/common/PageHeader';
import { RiskBadge } from '../components/common/RiskBadge';
import { Button } from '../components/common/Button';
import { ConfirmActionModal } from '../components/phase2/ConfirmActionModal';
import { ApprovalRequirementBanner } from '../components/phase2/ApprovalRequirementBanner';
import { ScreenGuide } from '../components/common/ScreenGuide';
import { Clock, XCircle, CheckCircle2, FastForward, UserCheck, ShieldCheck } from 'lucide-react';
import styles from './phase2Shared.module.css';

type Tab = 'PENDING_MY_APPROVAL' | 'GROUP_QUEUE' | 'COMPLETED';
type Decision = 'APPROVED' | 'REJECTED' | 'ESCALATED' | 'CHANGES_REQUESTED';

const getStatusBadge = (status: string) => {
  switch (status) {
    case 'APPROVED':
      return {
        bg: 'rgba(16, 185, 129, 0.14)',
        border: 'rgba(16, 185, 129, 0.35)',
        color: '#34d399',
        icon: <CheckCircle2 size={13} style={{ marginRight: '5px' }} />,
        label: 'APPROVED'
      };
    case 'PENDING':
      return {
        bg: 'rgba(59, 130, 246, 0.14)',
        border: 'rgba(59, 130, 246, 0.35)',
        color: '#60a5fa',
        icon: <Clock size={13} style={{ marginRight: '5px' }} />,
        label: 'PENDING'
      };
    case 'REJECTED':
      return {
        bg: 'rgba(239, 68, 68, 0.14)',
        border: 'rgba(239, 68, 68, 0.35)',
        color: '#f87171',
        icon: <XCircle size={13} style={{ marginRight: '5px' }} />,
        label: 'REJECTED'
      };
    case 'SUPERSEDED':
      return {
        bg: 'rgba(148, 163, 184, 0.08)',
        border: 'rgba(148, 163, 184, 0.2)',
        color: '#94a3b8',
        icon: <FastForward size={13} style={{ marginRight: '5px' }} />,
        label: 'SUPERSEDED'
      };
    case 'SKIPPED':
      return {
        bg: 'rgba(148, 163, 184, 0.08)',
        border: 'rgba(148, 163, 184, 0.2)',
        color: '#94a3b8',
        icon: <FastForward size={13} style={{ marginRight: '5px' }} />,
        label: 'SKIPPED'
      };
    case 'WAITING':
      return {
        bg: 'rgba(148, 163, 184, 0.08)',
        border: 'rgba(148, 163, 184, 0.2)',
        color: '#94a3b8',
        icon: <Clock size={13} style={{ marginRight: '5px' }} />,
        label: 'AWAITING PRIOR STAGE'
      };
    default:
      return {
        bg: 'rgba(148, 163, 184, 0.1)',
        border: 'rgba(148, 163, 184, 0.2)',
        color: '#cbd5e1',
        icon: null,
        label: status
      };
  }
};

const TABS: { id: Tab; label: string }[] = [
  { id: 'PENDING_MY_APPROVAL', label: 'My Approvals' },
  { id: 'GROUP_QUEUE', label: 'Group Queue' },
  { id: 'COMPLETED', label: 'Completed' },
];

export const ScheduleApprovalQueue: React.FC = () => {
  const { showToast } = useToast();
  const { currentUser } = useAuth();
  const navigate = useNavigate();

  const [activeTab, setActiveTab] = useState<Tab>('PENDING_MY_APPROVAL');
  const [schedules, setSchedules] = useState<any[]>([]);
  const [metrics, setMetrics] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [selectedSchedule, setSelectedSchedule] = useState<any | null>(null);
  const [scheduleDetails, setScheduleDetails] = useState<any | null>(null);
  const [scheduleApprovals, setScheduleApprovals] = useState<any[]>([]);
  const [approvalId, setApprovalId] = useState<string | null>(null);
  const [decision, setDecision] = useState<Decision | null>(null);
  const [reason, setReason] = useState('');
  const [showConfirm, setShowConfirm] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    document.title = 'Schedule Approvals — GuardianIQ';
  }, []);

  const fetchQueue = async () => {
    setLoading(true);
    setError(null);
    try {
      let params: any = {};
      if (activeTab === 'PENDING_MY_APPROVAL') {
        params = { my_approvals: true, status: 'PENDING_APPROVAL' };
      } else if (activeTab === 'GROUP_QUEUE') {
        params = { status: 'PENDING_APPROVAL' };
      } else {
        params = { status: 'ACTIVE,RETIRED' };
      }

      const [res, metricsRes]: any = await Promise.all([
        scheduleApi.list(params),
        scheduleApi.getApprovalMetrics().catch(() => null)
      ]);
      const list = res?.items ?? (Array.isArray(res) ? res : (res?.data?.items ?? res?.data ?? []));
      setSchedules(Array.isArray(list) ? list : []);
      const metricsData = metricsRes?.data ?? metricsRes ?? {};
      setMetrics(metricsData);
    } catch (e: any) {
      setError(e.message || 'Failed to fetch queue');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchQueue();
    setSelectedSchedule(null);
    setScheduleDetails(null);
    setScheduleApprovals([]);
    setApprovalId(null);
    setDecision(null);
    setReason('');
  }, [activeTab]);

  useEffect(() => {
    if (selectedSchedule) {
      setScheduleDetails(null);
      setApprovalId(null);
      scheduleApi.getById(selectedSchedule.id)
        .then((res: any) => {
          const detail = res?.data?.schedule || res?.schedule || res?.data || res;
          setScheduleDetails(detail);
        })
        .catch(() => showToast('Failed to load full schedule details', 'error'));
      
      scheduleApi.getApprovals(selectedSchedule.id)
        .then((res: any) => {
          const list = Array.isArray(res) 
            ? res 
            : (res?.items || res?.data?.items || res?.data || []);
          const approvals = Array.isArray(list) ? list : [];
          setScheduleApprovals(approvals);
          
          // Look for direct assignment for logged in user first, then fallback to any pending
          const myPending = approvals.find((a: any) => 
            (a.approval_status === 'PENDING' || a.approval_status === 'ESCALATED') && 
            (String(a.approver_user_id) === String(currentUser?.id) || currentUser?.is_superuser)
          );
          const anyPending = approvals.find((a: any) => a.approval_status === 'PENDING' || a.approval_status === 'ESCALATED');
          const target = myPending || anyPending;
          
          if (target) {
            setApprovalId(target.id);
          } else {
            setApprovalId(selectedSchedule.id);
          }
        })
        .catch(() => {
          setScheduleApprovals([]);
          setApprovalId(selectedSchedule.id);
        });
    }
  }, [selectedSchedule, currentUser]);

  const handleDecisionSubmit = async () => {
    const activeApprovalId = approvalId || selectedSchedule?.id;
    if (!selectedSchedule || !decision || !activeApprovalId) {
      showToast('No pending approval found for this schedule.', 'error');
      return;
    }
    setIsSubmitting(true);
    try {
      await scheduleApi.decideApproval(activeApprovalId, { decision, reason: reason || 'Decision applied' });
      showToast(`Schedule ${decision.toLowerCase().replace('_', ' ')} successfully.`, 'success');
      
      setShowConfirm(false);
      setSelectedSchedule(null);
      setDecision(null);
      setReason('');
      fetchQueue();
    } catch (e: any) {
      if (e?.response?.status === 403) {
        showToast('You are not authorized to approve this schedule.', 'error');
      } else {
        showToast(e.message || 'Failed to record decision', 'error');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const getPrimaryAssignment = (assignments: any[]) => {
    if (!assignments || assignments.length === 0) return null;
    return assignments.find((a: any) => a.assignment_role === 'PRIMARY') || assignments[0];
  };

  const assignment = scheduleDetails ? getPrimaryAssignment(scheduleDetails.agent_assignments || scheduleDetails.assignments) : null;
  const nonSkippedLayers = Array.isArray(scheduleApprovals) ? scheduleApprovals.filter(a => a.approval_status !== 'SKIPPED').length : 0;
  const activeApproval = Array.isArray(scheduleApprovals) ? scheduleApprovals.find(a => a.id === approvalId) : null;
  const currentLayerOrder = activeApproval?.approval_layer || activeApproval?.layer_order || 1;

  return (
    <div className={styles.page}>
      <div className={styles.breadcrumb}>Orchestration &gt; Schedule Approvals</div>
      <PageHeader
        title="Schedule Approvals"
        description="Review and authorize workflow schedule configurations"
        actions={
          <ScreenGuide
            content={
              <div style={{ display: "flex", flexDirection: "column", gap: "12px", paddingRight: "4px" }}>
                <h4 style={{ color: "#fbbf24", margin: "0 0 4px 0", fontSize: "0.85rem" }}>Approval Queue</h4>
                <p style={{ margin: 0 }}>Review schedules that require your approval due to risk level or tool assignments. Select a schedule to view its details and record your decision.</p>
              </div>
            }
          />
        }
      />

      <div className={styles.kpiGrid} style={{ marginBottom: '24px' }}>
        <div className={styles.kpiCard}>
          <div className={styles.kpiLabel}>Pending Approvals</div>
          <div className={styles.kpiValue}>
            {typeof metrics?.PENDING === 'number' 
              ? metrics.PENDING 
              : schedules.filter(s => s.schedule_status === 'PENDING_APPROVAL').length}
          </div>
        </div>
        <div className={styles.kpiCard}>
          <div className={styles.kpiLabel}>Approved Today</div>
          <div className={styles.kpiValue}>{metrics?.APPROVED || 0}</div>
        </div>
        <div className={styles.kpiCard}>
          <div className={styles.kpiLabel}>Rejected Today</div>
          <div className={styles.kpiValue}>{metrics?.REJECTED || 0}</div>
        </div>
        <div className={styles.kpiCard}>
          <div className={styles.kpiLabel}>Escalated</div>
          <div className={styles.kpiValue}>{metrics?.ESCALATED || 0}</div>
        </div>
        <div className={styles.kpiCard}>
          <div className={styles.kpiLabel}>Changes Required</div>
          <div className={styles.kpiValue}>{metrics?.CHANGES_REQUESTED || 0}</div>
        </div>
      </div>

      <div className={styles.approvalLayout}>
        <div className={styles.listPane}>
          <div className={styles.tabs}>
            {TABS.map(tab => (
              <button
                key={tab.id}
                className={`${styles.tab} ${activeTab === tab.id ? styles.activeTab : ''}`}
                onClick={() => setActiveTab(tab.id)}
              >
                {tab.label}
              </button>
            ))}
          </div>

          <div className={styles.listScroll}>
            {loading ? (
              <div style={{ padding: '1rem' }}>
                <div className={styles.stateDesc}>Loading queue...</div>
              </div>
            ) : error ? (
              <div style={{ padding: '1.5rem', textAlign: 'center' }}>
                <div className={styles.stateDesc} style={{ color: 'var(--color-danger)' }}>{error}</div>
              </div>
            ) : schedules.length === 0 ? (
              <div style={{ padding: '2rem', textAlign: 'center' }}>
                <div className={styles.stateDesc}>All caught up! No schedules waiting for approval.</div>
              </div>
            ) : (
              schedules.map(s => (
                <button
                  key={s.id}
                  className={`${styles.listItem} ${selectedSchedule?.id === s.id ? styles.selected : ''}`}
                  onClick={() => { setSelectedSchedule(s); setDecision(null); setReason(''); }}
                >
                  <div className={styles.listItemTop}>
                    <span className={styles.listItemName}>{s.schedule_name}</span>
                    <RiskBadge level={s.risk_level} />
                  </div>
                  <div className={styles.subText}>Workflow: {s.workflow_name || s.workflow_id}</div>
                  <div className={styles.subText}>Requested By: {s.owner_name || 'Unknown'}</div>
                  <div className={styles.listItemMeta}>
                    <span className={styles.metaTime}>
                      <Clock size={12} /> {new Date(s.created_at || Date.now()).toLocaleDateString()}
                    </span>
                    {activeTab !== 'COMPLETED' && (
                      <span className={`${styles.pill} ${styles.pillWarning}`}>Action Required</span>
                    )}
                  </div>
                </button>
              ))
            )}
          </div>
        </div>

        {selectedSchedule ? (
          <div className={styles.detailPane}>
            <div className={styles.detailHeader}>
              <div>
                <h2 className={styles.detailTitle} style={{ margin: 0, marginBottom: '4px' }}>
                  <button 
                    className={styles.linkCell} 
                    onClick={() => navigate(`/workflow-scheduler/${selectedSchedule.id}`, { state: { from: '/schedule-approvals' } })}
                    style={{ fontSize: 'inherit', fontWeight: 'inherit', padding: 0 }}
                  >
                    {selectedSchedule.schedule_name}
                  </button>
                </h2>
                <div className={styles.subText}>{selectedSchedule.schedule_code || selectedSchedule.id}</div>
              </div>
              <button className={styles.iconBtnPlain} onClick={() => setSelectedSchedule(null)} title="Close">
                <XCircle size={18} />
              </button>
            </div>

            <div className={styles.scrollContent} style={{ padding: '24px', overflowY: 'auto' }}>
              <ApprovalRequirementBanner 
                approvalRequired={true} 
                reasons={[`Risk Level is ${selectedSchedule.risk_level}`, `Tool assignments require review`]} 
              />

              <div className={styles.section} style={{ marginTop: '24px' }}>
                <h3 className={styles.sectionTitle}>Schedule Overview</h3>
                <div className={styles.dlGrid}>
                  <div>
                    <div className={styles.dlLabel}>Workflow</div>
                    <div className={styles.dlValue}>{selectedSchedule.workflow_name || selectedSchedule.workflow_id}</div>
                  </div>
                  <div>
                    <div className={styles.dlLabel}>Risk Level</div>
                    <div className={styles.dlValue}><RiskBadge level={selectedSchedule.risk_level} /></div>
                  </div>
                  <div>
                    <div className={styles.dlLabel}>Execution Mode</div>
                    <div className={styles.dlValue}>{selectedSchedule.execution_mode || 'AUTONOMOUS'}</div>
                  </div>
                  <div>
                    <div className={styles.dlLabel}>Schedule</div>
                    <div className={styles.dlValue}>{selectedSchedule.schedule_type} {selectedSchedule.cron_expression}</div>
                  </div>
                </div>
              </div>

              {scheduleDetails && assignment && (
                <div className={styles.section} style={{ marginTop: '24px' }}>
                  <h3 className={styles.sectionTitle}>Agent Assignment Summary</h3>
                  <div className={styles.dlGrid}>
                    <div>
                      <div className={styles.dlLabel}>Agent</div>
                      <div className={styles.dlValue}>{assignment.agent_id}</div>
                    </div>
                    <div>
                      <div className={styles.dlLabel}>Execution Mode</div>
                      <div className={styles.dlValue}>{assignment.execution_mode}</div>
                    </div>
                    <div>
                      <div className={styles.dlLabel}>Confidence Threshold</div>
                      <div className={styles.dlValue}>{assignment.confidence_threshold}%</div>
                    </div>
                    <div className={styles.dlFull}>
                      <div className={styles.dlLabel}>Allowed Tools</div>
                      <div className={styles.dlValue} style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginTop: '4px' }}>
                        {assignment.allowed_tools?.map((tool: string) => {
                          const isWrite = tool.toLowerCase().includes('write') || tool.toLowerCase().includes('update') || tool.toLowerCase().includes('create');
                          return (
                            <span key={tool} className={isWrite ? `${styles.pill} ${styles.pillWarning}` : styles.tagChip}>
                              {tool}
                            </span>
                          );
                        }) || <span className={styles.subText}>None</span>}
                      </div>
                    </div>
                    <div className={styles.dlFull}>
                      <div className={styles.dlLabel}>Blocked Operations</div>
                      <div className={styles.dlValue} style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginTop: '4px' }}>
                        {assignment.blocked_operations?.map((op: string) => (
                          <span key={op} className={`${styles.pill} ${styles.pillDanger}`}>{op}</span>
                        )) || <span className={styles.subText}>None</span>}
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {activeTab !== 'COMPLETED' && (
                <div className={styles.section} style={{ marginTop: '24px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <h3 className={styles.sectionTitle} style={{ margin: 0 }}>Record Decision</h3>
                    {nonSkippedLayers > 0 && (
                      <span className={styles.pill} style={{ background: '#f3f4f6', color: '#374151' }}>
                        Stage {currentLayerOrder} of {nonSkippedLayers}
                      </span>
                    )}
                  </div>
                  {activeApproval?.department_code && (
                    <div className={styles.subText} style={{ marginBottom: '16px', marginTop: '4px' }}>
                      Current layer: <strong>{activeApproval.department_code.replace('_', ' ')}</strong>
                    </div>
                  )}
                  <div className={styles.decisionButtons}>
                    <button
                      className={`${styles.decisionBtn} ${decision === 'APPROVED' ? styles.selectedApprove : ''}`}
                      onClick={() => setDecision('APPROVED')}
                    >
                      Approve
                    </button>
                    <button
                      className={`${styles.decisionBtn} ${decision === 'REJECTED' ? styles.selectedReject : ''}`}
                      onClick={() => setDecision('REJECTED')}
                    >
                      Reject
                    </button>
                    <button
                      className={`${styles.decisionBtn} ${decision === 'ESCALATED' ? styles.selectedEscalate : ''}`}
                      onClick={() => setDecision('ESCALATED')}
                    >
                      Escalate
                    </button>
                    <button
                      className={`${styles.decisionBtn} ${decision === 'CHANGES_REQUESTED' ? styles.selectedReject : ''}`}
                      onClick={() => setDecision('CHANGES_REQUESTED')}
                    >
                      Request Changes
                    </button>
                  </div>

                  {decision && (
                    <div style={{ marginTop: '16px' }}>
                      <label className={styles.fieldLabel}>
                        {decision === 'APPROVED' ? 'Approval notes (optional)' : `${decision.charAt(0) + decision.slice(1).toLowerCase().replace('_', ' ')} reason (required)`} 
                        {decision !== 'APPROVED' && <span className={styles.req}>*</span>}
                      </label>
                      <textarea
                        className={styles.textarea}
                        rows={3}
                        value={reason}
                        onChange={(e) => setReason(e.target.value)}
                        placeholder={decision === 'APPROVED' ? 'Provide optional approval notes...' : 'Provide a reason (min 10 characters)...'}
                      />
                      <div className={styles.decisionFooter} style={{ marginTop: '16px' }}>
                        <Button
                          variant={decision === 'APPROVED' ? 'primary' : 'danger'}
                          onClick={() => setShowConfirm(true)}
                          disabled={!decision || (decision !== 'APPROVED' && reason.trim().length < 10)}
                        >
                          Submit Decision
                        </Button>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {Array.isArray(scheduleApprovals) && scheduleApprovals.length > 0 && (
                <div className={styles.section} style={{ marginTop: '28px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
                    <ShieldCheck size={18} style={{ color: '#818cf8' }} />
                    <h3 className={styles.sectionTitle} style={{ margin: 0 }}>Approval Chain & History</h3>
                  </div>
                  
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                    {scheduleApprovals.map((appr: any) => {
                      const badge = getStatusBadge(appr.approval_status);
                      const isSkipped = appr.approval_status === 'SKIPPED' || appr.approval_status === 'SUPERSEDED';
                      const deptTitle = appr.department_name || (appr.department_code ? appr.department_code.replace(/_/g, ' ') : 'General');
                      const stageLabel = `Stage ${appr.approval_layer || appr.layer_order || 1}: ${deptTitle}`;
                      const approverDisplay = appr.decided_by_name 
                        ? `${appr.decided_by_name} (${appr.decided_by_email || ''})`
                        : appr.approver_name 
                        ? `${appr.approver_name} (${appr.approver_email || ''})`
                        : (appr.decided_by || appr.approver_user_id || 'Department Approver');

                      return (
                        <div 
                          key={appr.id} 
                          style={{ 
                            padding: '16px 18px', 
                            background: isSkipped 
                              ? 'rgba(15, 23, 42, 0.45)' 
                              : 'linear-gradient(135deg, rgba(26, 36, 61, 0.7) 0%, rgba(17, 24, 43, 0.7) 100%)',
                            border: `1px solid ${isSkipped ? 'rgba(255, 255, 255, 0.06)' : appr.approval_status === 'APPROVED' ? 'rgba(16, 185, 129, 0.3)' : 'rgba(99, 102, 241, 0.25)'}`,
                            borderLeft: `4px solid ${isSkipped ? '#64748b' : appr.approval_status === 'APPROVED' ? '#10b981' : '#6366f1'}`,
                            borderRadius: '10px',
                            backdropFilter: 'blur(10px)',
                            boxShadow: isSkipped ? 'none' : '0 4px 15px rgba(0, 0, 0, 0.25)',
                            opacity: isSkipped ? 0.75 : 1,
                            transition: 'all 0.18s ease'
                          }}
                        >
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                              <span style={{ 
                                color: isSkipped ? '#94a3b8' : '#f8fafc', 
                                fontSize: '0.95rem', 
                                fontWeight: 600,
                                letterSpacing: '0.01em'
                              }}>
                                {stageLabel}
                              </span>
                            </div>
                            <span style={{
                              display: 'inline-flex',
                              alignItems: 'center',
                              padding: '3px 10px',
                              borderRadius: '9999px',
                              fontSize: '0.725rem',
                              fontWeight: 600,
                              letterSpacing: '0.04em',
                              background: badge.bg,
                              border: `1px solid ${badge.border}`,
                              color: badge.color
                            }}>
                              {badge.icon}
                              {badge.label}
                            </span>
                          </div>
                          
                          {isSkipped && appr.skip_reason && (
                            <div style={{ fontSize: '0.825rem', color: '#94a3b8', fontStyle: 'italic', marginBottom: '6px' }}>
                              {appr.skip_reason}
                            </div>
                          )}
                          
                          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '16px', alignItems: 'center', fontSize: '0.825rem', color: '#cbd5e1', marginTop: '6px' }}>
                            {(appr.decided_by_name || appr.decided_by) ? (
                              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                                <UserCheck size={14} style={{ color: '#818cf8' }} />
                                <span>Decided by: <strong style={{ color: '#f8fafc' }}>{approverDisplay}</strong></span>
                              </div>
                            ) : (appr.approver_name || appr.approver_user_id) ? (
                              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                                <Clock size={14} style={{ color: '#60a5fa' }} />
                                <span>Assigned to: <strong style={{ color: '#f8fafc' }}>{approverDisplay}</strong></span>
                              </div>
                            ) : null}

                            {(appr.decided_at || appr.created_at) && (
                              <div style={{ fontSize: '0.775rem', color: '#64748b', marginLeft: 'auto' }}>
                                {new Date(appr.decided_at || appr.created_at).toLocaleString()}
                              </div>
                            )}
                          </div>
                          
                          {appr.decision_reason && (
                            <div style={{ 
                              marginTop: '10px', 
                              padding: '8px 12px', 
                              background: 'rgba(0, 0, 0, 0.25)', 
                              borderLeft: '3px solid #6366f1', 
                              borderRadius: '0 6px 6px 0',
                              fontSize: '0.825rem', 
                              color: '#e2e8f0',
                              lineHeight: 1.4
                            }}>
                              <span style={{ color: '#94a3b8', fontWeight: 500, marginRight: '4px' }}>Decision Note:</span>
                              "{appr.decision_reason}"
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className={styles.detailEmpty}>
            Select a schedule to view details and approve.
          </div>
        )}
      </div>

      {showConfirm && (
        <ConfirmActionModal
          title={`${decision ? (decision === 'APPROVED' ? 'Approve' : decision === 'REJECTED' ? 'Reject' : decision === 'ESCALATED' ? 'Escalate' : 'Request Changes for') : ''} Schedule`}
          message={`Are you sure you want to ${decision ? (decision === 'APPROVED' ? 'approve' : decision === 'REJECTED' ? 'reject' : decision === 'ESCALATED' ? 'escalate' : 'request changes for') : ''} this schedule? This action will advance the workflow approval process.`}
          confirmLabel={decision ? (decision === 'APPROVED' ? 'Approve' : decision === 'REJECTED' ? 'Reject' : decision === 'ESCALATED' ? 'Escalate' : 'Request Changes') : 'Confirm'}
          confirmVariant={decision === 'APPROVED' ? 'primary' : 'danger'}
          onConfirm={handleDecisionSubmit}
          onCancel={() => setShowConfirm(false)}
          isLoading={isSubmitting}
        />
      )}
    </div>
  );
};

export default ScheduleApprovalQueue;

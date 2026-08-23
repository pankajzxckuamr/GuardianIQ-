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
import { Clock, AlertCircle, XCircle } from 'lucide-react';
import styles from './phase2Shared.module.css';

type Tab = 'PENDING_MY_APPROVAL' | 'GROUP_QUEUE' | 'COMPLETED';
type Decision = 'APPROVED' | 'REJECTED' | 'ESCALATED' | 'CHANGES_REQUESTED';

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

  const hasApprovalGroup = currentUser?.is_superuser || (currentUser?.approval_groups && currentUser.approval_groups.length > 0);

  useEffect(() => {
    document.title = 'Schedule Approvals — GuardianIQ';
  }, []);

  const fetchQueue = async () => {
    if (!hasApprovalGroup) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const statusFilter = activeTab === 'COMPLETED' ? 'ACTIVE,RETIRED' : 'PENDING_APPROVAL';
      const [res, metricsRes]: any = await Promise.all([
        scheduleApi.list({ status: statusFilter }),
        scheduleApi.getApprovalMetrics().catch(() => ({ data: null }))
      ]);
      setSchedules(res.items || []);
      setMetrics(metricsRes.data || null);
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
  }, [activeTab, hasApprovalGroup]);

  useEffect(() => {
    if (selectedSchedule) {
      setScheduleDetails(null);
      setApprovalId(null);
      scheduleApi.getById(selectedSchedule.id)
        .then((res: any) => setScheduleDetails(res.data || res))
        .catch(() => showToast('Failed to load full schedule details', 'error'));
      
      scheduleApi.getApprovals(selectedSchedule.id)
        .then((res: any) => {
          const approvals = res.data || res;
          setScheduleApprovals(approvals);
          const pending = approvals.find((a: any) => a.approval_status === 'PENDING' || a.approval_status === 'ESCALATED');
          if (pending) {
            setApprovalId(pending.id);
          }
        })
        .catch(() => {});
    }
  }, [selectedSchedule]);

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

  if (!hasApprovalGroup) {
    return (
      <div className={styles.page}>
        <PageHeader title="Schedule Approvals" description="Review and authorize workflow schedule configurations" />
        <div className={styles.stateCard} style={{ marginTop: '32px' }}>
          <div className={styles.stateTitle}>Access Restricted</div>
          <div className={styles.stateDesc}>You are not a member of any approval group.</div>
        </div>
      </div>
    );
  }

  const assignment = scheduleDetails ? getPrimaryAssignment(scheduleDetails.assignments) : null;
  const nonSkippedLayers = scheduleApprovals.filter(a => a.approval_status !== 'SKIPPED').length;
  const activeApproval = scheduleApprovals.find(a => a.id === approvalId);
  const currentLayerOrder = activeApproval?.layer_order || 1;

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
          <div className={styles.kpiValue}>{schedules.filter(s => s.schedule_status === 'PENDING_APPROVAL').length}</div>
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

              {activeTab !== 'COMPLETED' && activeApproval && (
                <div className={styles.section} style={{ marginTop: '24px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <h3 className={styles.sectionTitle} style={{ margin: 0 }}>Record Decision</h3>
                    <span className={styles.pill} style={{ background: '#f3f4f6', color: '#374151' }}>
                      Stage {currentLayerOrder} of {nonSkippedLayers}
                    </span>
                  </div>
                  <div className={styles.subText} style={{ marginBottom: '16px', marginTop: '4px' }}>
                    Current layer: <strong>{activeApproval.department_code?.replace('_', ' ')}</strong>
                  </div>
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
                          disabled={decision !== 'APPROVED' && reason.length < 10}
                        >
                          Submit Decision
                        </Button>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {scheduleApprovals.length > 0 && (
                <div className={styles.section} style={{ marginTop: '24px' }}>
                  <h3 className={styles.sectionTitle}>Approval Chain</h3>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginTop: '12px' }}>
                    {scheduleApprovals.map((appr: any) => {
                      const isSkipped = appr.approval_status === 'SKIPPED';
                      return (
                        <div 
                          key={appr.id} 
                          style={{ 
                            padding: '12px 16px', 
                            borderLeft: `4px solid ${isSkipped ? '#d1d5db' : appr.approval_status === 'APPROVED' ? '#10b981' : '#3b82f6'}`,
                            background: isSkipped ? '#f9fafb' : '#ffffff',
                            borderTop: '1px solid #f3f4f6',
                            borderRight: '1px solid #f3f4f6',
                            borderBottom: '1px solid #f3f4f6',
                            borderRadius: '0 6px 6px 0',
                            opacity: isSkipped ? 0.7 : 1
                          }}
                        >
                          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                            <strong style={{ color: isSkipped ? '#6b7280' : '#111827' }}>
                              Stage {appr.layer_order}: {appr.department_code?.replace('_', ' ')}
                            </strong>
                            <span className={styles.subText}>{appr.approval_status}</span>
                          </div>
                          
                          {isSkipped && (
                            <div className={styles.subText} style={{ fontStyle: 'italic' }}>
                              Skipped — {appr.skip_reason}
                            </div>
                          )}
                          
                          {appr.decided_by && (
                            <div className={styles.subText}>
                              Decided by: <strong>{appr.decided_by}</strong>
                            </div>
                          )}
                          
                          {appr.decision_reason && (
                            <div className={styles.subText} style={{ marginTop: '4px' }}>
                              Note: {appr.decision_reason}
                            </div>
                          )}
                          
                          {appr.decided_at && (
                            <div className={styles.subText} style={{ fontSize: '0.75rem', marginTop: '8px', color: '#9ca3af' }}>
                              {new Date(appr.decided_at).toLocaleString()}
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
          title={`${decision ? decision.charAt(0) + decision.slice(1).toLowerCase().replace('_', ' ') : ''} Schedule`}
          message={`Are you sure you want to ${decision ? decision.toLowerCase().replace('_', ' ') : ''} this schedule? This action will notify the schedule owner.`}
          confirmLabel={decision ? decision.charAt(0) + decision.slice(1).toLowerCase().replace('_', ' ') : ''}
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

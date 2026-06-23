import React, { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';
import { useToast } from '../hooks/useToast';
import { scheduleApi } from '../api/phase2Client';
import { PageHeader } from '../components/common/PageHeader';
import { RiskBadge } from '../components/common/RiskBadge';
import { Button } from '../components/common/Button';
import { Clock, AlertCircle, XCircle } from 'lucide-react';
import { storage } from '../utils/storage';
import styles from './phase2Shared.module.css';

type Tab = 'PENDING_MY_APPROVAL' | 'GROUP_QUEUE' | 'COMPLETED';
type Decision = 'APPROVED' | 'REJECTED' | 'CHANGES_REQUESTED' | 'ESCALATED';

const TABS: { id: Tab; label: string }[] = [
  { id: 'PENDING_MY_APPROVAL', label: 'My Approvals' },
  { id: 'GROUP_QUEUE', label: 'Group Queue' },
  { id: 'COMPLETED', label: 'Completed' },
];

const DECISIONS: Decision[] = ['APPROVED', 'REJECTED', 'CHANGES_REQUESTED', 'ESCALATED'];

export const ScheduleApprovalQueue: React.FC = () => {
  const { showToast } = useToast();
  useAuth();

  const [activeTab, setActiveTab] = useState<Tab>('PENDING_MY_APPROVAL');
  const [schedules, setSchedules] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [selectedSchedule, setSelectedSchedule] = useState<any | null>(null);
  const [decision, setDecision] = useState<Decision | null>(null);
  const [reason, setReason] = useState('');

  const isDelegated = false; // Mock

  useEffect(() => {
    document.title = 'Schedule Approvals — GuardianIQ';
  }, []);

  const fetchQueue = async () => {
    setLoading(true);
    setError(null);
    try {
      const statusFilter = activeTab === 'COMPLETED' ? ['ACTIVE', 'RETIRED'] : ['PENDING_APPROVAL'];
      const res: any = await scheduleApi.list({ status: statusFilter });
      setSchedules(res.items || []);
    } catch (e: any) {
      setError(e.message || 'Failed to fetch queue');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchQueue();
    setSelectedSchedule(null);
    setDecision(null);
    setReason('');
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab]);

  const handleDecision = async () => {
    if (!selectedSchedule || !decision) return;
    try {
      const token = storage.get<string>('guardianiq_access_token');
      const approvalId = selectedSchedule.id;
      const res = await fetch(`/api/v1/schedule-approvals/${approvalId}/decide`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({ decision, reason }),
      });
      const json = await res.json();
      if (!json.success) throw new Error(json.error);
      showToast(`Decision ${decision} recorded`, 'success');
      setSelectedSchedule(null);
      setDecision(null);
      setReason('');
      fetchQueue();
    } catch (e: any) {
      showToast(e.message || 'Failed to record decision', 'error');
    }
  };

  return (
    <div className={styles.page}>
      <div className={styles.breadcrumb}>Orchestration &gt; Schedule Approvals</div>
      <PageHeader
        title="Schedule Approvals"
        description="Review and authorize workflow schedule configurations"
      />

      {isDelegated && (
        <div className={styles.banner}>
          <AlertCircle size={16} /> You are acting under delegation from [Original Approver].
        </div>
      )}

      <div className={styles.approvalLayout}>
        {/* List Pane */}
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
                <div className={styles.stateDesc}>No schedules found in this queue.</div>
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
                  <div className={styles.subText}>Owner: {s.owner_user_id}</div>
                  <div className={styles.listItemMeta}>
                    <span className={styles.metaTime}>
                      <Clock size={12} /> {new Date(s.created_at || Date.now()).toLocaleDateString()}
                    </span>
                    {activeTab !== 'COMPLETED' && (
                      <span className={`${styles.pill} ${styles.pillWarning}`}>24h left</span>
                    )}
                  </div>
                </button>
              ))
            )}
          </div>
        </div>

        {/* Detail Pane */}
        {selectedSchedule ? (
          <div className={styles.detailPane}>
            <div className={styles.detailHeader}>
              <h2 className={styles.detailTitle}>{selectedSchedule.schedule_name}</h2>
              <button className={styles.iconBtnPlain} onClick={() => setSelectedSchedule(null)} title="Close">
                <XCircle size={18} />
              </button>
            </div>

            <div className={styles.section}>
              <h3 className={styles.sectionTitle}>Schedule Summary</h3>
              <div className={styles.dlGrid}>
                <div>
                  <div className={styles.dlLabel}>Workflow</div>
                  <div className={styles.dlValue}>{selectedSchedule.workflow_id}</div>
                </div>
                <div>
                  <div className={styles.dlLabel}>Risk Level</div>
                  <div className={styles.dlValue}><RiskBadge level={selectedSchedule.risk_level} /></div>
                </div>
                <div className={styles.dlFull}>
                  <div className={styles.dlLabel}>Schedule</div>
                  <div className={styles.dlValue}>{selectedSchedule.schedule_type} {selectedSchedule.cron_expression}</div>
                </div>
              </div>
            </div>

            <div className={styles.noticeBox}>
              <h3 className={styles.noticeTitle}><AlertCircle size={15} /> Approval Reason</h3>
              <p className={styles.noticeText}>
                This schedule requires approval due to configured risk level ({selectedSchedule.risk_level}) and tool assignment boundary.
              </p>
            </div>

            {activeTab !== 'COMPLETED' && (
              <div className={styles.section}>
                <h3 className={styles.sectionTitle}>Record Decision</h3>
                <div className={styles.decisionButtons}>
                  {DECISIONS.map(d => (
                    <button
                      key={d}
                      className={`${styles.decisionBtn} ${decision === d ? (d === 'APPROVED' ? styles.selectedApprove : styles.selectedOther) : ''}`}
                      onClick={() => setDecision(d)}
                    >
                      {d.replace(/_/g, ' ')}
                    </button>
                  ))}
                </div>

                {decision && (
                  <div>
                    <label className={styles.fieldLabel}>
                      Reason / Notes <span className={styles.req}>*</span>
                    </label>
                    <textarea
                      className={styles.textarea}
                      rows={3}
                      value={reason}
                      onChange={(e) => setReason(e.target.value)}
                      placeholder="Provide reasoning for this decision..."
                    />
                    <div className={styles.decisionFooter}>
                      <Button
                        variant="primary"
                        onClick={handleDecision}
                        disabled={!decision || (decision !== 'APPROVED' && reason.length < 10)}
                      >
                        Submit Decision
                      </Button>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        ) : (
          <div className={styles.detailEmpty}>
            Select a schedule to view details and approve.
          </div>
        )}
      </div>
    </div>
  );
};

export default ScheduleApprovalQueue;

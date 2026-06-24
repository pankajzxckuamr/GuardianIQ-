import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { runApi } from '../api/phase2Client';
import { WorkflowRunResponse, WorkflowRunStepResponse, WorkflowRunOutputResponse } from '../types/phase2';
import { RiskBadge } from '../components/common/RiskBadge';
import { Button } from '../components/common/Button';
import { RunTimeline } from '../components/phase2/RunTimeline';
import { RunOutputViewer } from '../components/phase2/RunOutputViewer';
import { AuditTimelinePanel } from '../components/phase2/AuditTimelinePanel';
import { useAuth } from '../hooks/useAuth';
import { useToast } from '../hooks/useToast';
import { AlertCircle, Clock, CheckCircle, XCircle, PlayCircle, Download, ArrowLeft } from 'lucide-react';
import styles from './phase2Shared.module.css';

const TABS = ['SUMMARY', 'STEPS', 'OUTPUTS', 'FAILURES', 'AUDIT'] as const;
type Tab = typeof TABS[number];

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

export const RunDetailPage: React.FC = () => {
  const { runId } = useParams<{ runId: string }>();
  const { currentUser } = useAuth();
  const { showToast } = useToast();
  const navigate = useNavigate();

  const canViewRun = currentUser?.is_superuser || currentUser?.permissions?.includes('VIEW_WORKFLOW_RUN');
  const canViewOutput = currentUser?.is_superuser || currentUser?.permissions?.includes('VIEW_WORKFLOW_RUN_OUTPUT');
  const canCancel = currentUser?.is_superuser || currentUser?.permissions?.includes('CANCEL_WORKFLOW_RUN');

  const [run, setRun] = useState<WorkflowRunResponse | null>(null);
  const [steps, setSteps] = useState<WorkflowRunStepResponse[]>([]);
  const [outputs, setOutputs] = useState<WorkflowRunOutputResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<Tab>('SUMMARY');

  useEffect(() => {
    if (!runId || !canViewRun) return;
    const fetchData = async () => {
      try {
        setLoading(true);
        const [runRes, stepsRes, outputsRes] = await Promise.all([
          runApi.getById(runId),
          runApi.getSteps(runId).catch(() => []),
          runApi.getOutputs(runId).catch(() => []),
        ]);
        setRun(runRes as WorkflowRunResponse);
        setSteps((stepsRes as any)?.items || stepsRes || []);
        setOutputs((outputsRes as any)?.items || outputsRes || []);
      } catch (e: any) {
        setError(e.message || 'Failed to load run details');
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [runId, canViewRun]);

  const handleCancelRun = async () => {
    if (!runId || !window.confirm('Cancel this running workflow?')) return;
    try {
      await runApi.cancel(runId);
      showToast('Run cancelled', 'success');
      const runRes = await runApi.getById(runId);
      setRun(runRes as WorkflowRunResponse);
    } catch (e: any) {
      showToast(e.message || 'Failed to cancel', 'error');
    }
  };

  if (!canViewRun) {
    return (
      <div className={styles.page}>
        <div className={styles.stateCard}>
          <div className={styles.stateTitle}>Access Restricted</div>
          <div className={styles.stateDesc}>You do not have permission to view this run.</div>
        </div>
      </div>
    );
  }
  if (loading) {
    return <div className={styles.page}><div className={styles.stateCard}><div className={styles.stateDesc}>Loading run details...</div></div></div>;
  }
  if (error || !run) {
    return (
      <div className={styles.page}>
        <div className={styles.stateCard}>
          <div className={styles.stateTitle}>Unable to load run</div>
          <div className={styles.stateDesc}>{error || 'Run not found'}</div>
          <Button variant="secondary" size="sm" onClick={() => navigate('/workflow-runs')} icon={<ArrowLeft size={14} />}>Back to Run History</Button>
        </div>
      </div>
    );
  }

  const failedSteps = steps.filter(s => s.step_status === 'FAILED');

  return (
    <div className={styles.page}>
      <button className={styles.clearBtn} onClick={() => navigate('/workflow-runs')} style={{ alignSelf: 'flex-start' }}>
        <ArrowLeft size={14} /> Back to Run History
      </button>

      {/* Header */}
      <div className={styles.detailHeaderCard}>
        <div className={styles.detailTopRow}>
          <div>
            <div className={styles.titleRow}>
              <h1 className={styles.detailH1}>{run.run_code}</h1>
              <span className={`${styles.pill} ${runStatusPillClass(run.run_status)}`}>{(run.run_status || '').replace(/_/g, ' ')}</span>
              <RiskBadge level={run.risk_level as any} />
              <span className={styles.tagChip}>{run.trigger_type}</span>
            </div>
            <div className={styles.monoCode}>
              Schedule:{' '}
              <button className={styles.linkCell} onClick={() => navigate(`/workflow-scheduler/${run.schedule_id}`)}>
                {(run as any).schedule_name || run.schedule_id}
              </button>
            </div>
          </div>
          <div className={styles.headerActions}>
            <Button variant="secondary" size="sm" disabled title="Coming soon" icon={<Download size={14} />}>Evidence</Button>
            {canCancel && run.run_status === 'RUNNING' && (
              <Button variant="danger" size="sm" onClick={handleCancelRun} icon={<XCircle size={14} />}>Cancel Run</Button>
            )}
          </div>
        </div>
        <div className={styles.headerSubBar}>
          <div className={styles.metaItem}><span className={styles.metaLabel}>Started</span><span className={styles.metaValue}>{run.started_at ? new Date(run.started_at).toLocaleString() : '-'}</span></div>
          <div className={styles.metaItem}><span className={styles.metaLabel}>Completed</span><span className={styles.metaValue}>{run.completed_at ? new Date(run.completed_at).toLocaleString() : '-'}</span></div>
          <div className={styles.metaItem}><span className={styles.metaLabel}>Duration</span><span className={styles.metaValue}>{run.duration_ms ? `${(run.duration_ms / 1000).toFixed(1)}s` : '-'}</span></div>
        </div>
      </div>

      {/* Timeline */}
      {steps.length > 0 && (
        <div className={styles.detailHeaderCard}>
          <RunTimeline steps={steps} />
        </div>
      )}

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
                {tab === 'FAILURES' && failedSteps.length > 0 && <AlertCircle size={14} style={{ color: 'var(--color-danger)', marginRight: 4, verticalAlign: 'middle' }} />}
                {tab.charAt(0) + tab.slice(1).toLowerCase()}
              </button>
            ))}
          </nav>
        </div>

        <div className={styles.tabBody}>
          {activeTab === 'SUMMARY' && (
            <div className={styles.dlGrid}>
              <div><div className={styles.dlLabel}>Workflow</div><div className={styles.dlValue}>{run.workflow_name || run.workflow_id}</div></div>
              <div><div className={styles.dlLabel}>Triggered By</div><div className={styles.dlValue}>{run.triggered_by_actor_type} - {run.triggered_by_name || run.triggered_by_user_id || 'System'}</div></div>
              <div className={styles.dlFull}>
                <div className={styles.dlLabel}>Context JSON</div>
                <pre className={styles.codeBlock}>{run.context_json ? JSON.stringify(run.context_json, null, 2) : '{}'}</pre>
              </div>
            </div>
          )}

          {activeTab === 'STEPS' && (
            <div className={styles.fieldStack}>
              {steps.map(step => (
                <div key={step.id} className={styles.stepCard}>
                  <div className={styles.stepHeader}>
                    <div className={styles.stepTitleWrap}>
                      {step.step_status === 'COMPLETED' && <CheckCircle size={18} style={{ color: 'var(--color-success)' }} />}
                      {step.step_status === 'FAILED' && <XCircle size={18} style={{ color: 'var(--color-danger)' }} />}
                      {step.step_status === 'RUNNING' && <PlayCircle size={18} style={{ color: 'var(--color-info)' }} />}
                      {(step.step_status === 'QUEUED' || step.step_status === 'PENDING') && <Clock size={18} style={{ color: 'var(--text-muted)' }} />}
                      <span className={styles.stepTitle}>{step.step_code} <span className={styles.stepType}>({step.step_type})</span></span>
                    </div>
                    <div className={styles.stepTime}>
                      {step.started_at ? new Date(step.started_at).toLocaleTimeString() : ''} - {step.completed_at ? new Date(step.completed_at).toLocaleTimeString() : ''}
                    </div>
                  </div>
                  {step.error_message && (
                    <div className={styles.dangerCard}><p className={styles.dangerText}>{step.error_message}</p></div>
                  )}
                  {step.output_json && (
                    <details className={styles.detailsToggle}>
                      <summary>View Output Data</summary>
                      <pre className={styles.codeBlock} style={{ marginTop: 8 }}>{JSON.stringify(step.output_json, null, 2)}</pre>
                    </details>
                  )}
                </div>
              ))}
              {steps.length === 0 && <p className={styles.stateDesc}>No steps recorded for this run.</p>}
            </div>
          )}

          {activeTab === 'OUTPUTS' && (
            <div>
              {canViewOutput ? (
                <RunOutputViewer outputs={outputs} canViewRaw={true} />
              ) : (
                <div className={styles.banner}>
                  <AlertCircle size={16} /> Raw output is restricted by your access scope.
                </div>
              )}
            </div>
          )}

          {activeTab === 'FAILURES' && (
            <div className={styles.fieldStack}>
              {failedSteps.length > 0 ? (
                failedSteps.map(step => (
                  <div key={step.id} className={styles.dangerCard}>
                    <h4 className={styles.dangerTitle}>{step.step_code} Failed</h4>
                    <p className={styles.dangerText}>{step.error_message || 'Unknown error occurred during step execution.'}</p>
                  </div>
                ))
              ) : (
                <p className={styles.stateDesc}>No failures recorded for this run.</p>
              )}
            </div>
          )}

          {activeTab === 'AUDIT' && (
            <AuditTimelinePanel entityType="WORKFLOW_RUN" entityId={runId || ''} />
          )}
        </div>
      </div>
    </div>
  );
};

export default RunDetailPage;

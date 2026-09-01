import React, { useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { PageHeader } from '../components/common/PageHeader';
import { RiskBadge } from '../components/common/RiskBadge';
import { Button } from '../components/common/Button';
import { RunTimeline } from '../components/phase2/RunTimeline';
import { RunOutputViewer } from '../components/phase2/RunOutputViewer';
import { AuditTimelinePanel } from '../components/phase2/AuditTimelinePanel';
import { ScreenGuide } from '../components/common/ScreenGuide';
import { useAuth } from '../hooks/useAuth';
import { useWorkflowRunDetail, useRunSteps, useRunOutputs, useCancelRun } from '../hooks/usePhase2Runs';
import { ArrowLeft, XCircle, Download } from 'lucide-react';
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

export const RunDetailPage: React.FC = () => {
  const { runId } = useParams<{ runId: string }>();
  const { currentUser } = useAuth();
  const navigate = useNavigate();

  const canViewRun = currentUser?.is_superuser || currentUser?.permissions?.includes('VIEW_WORKFLOW_RUN');
  const canViewOutput = currentUser?.is_superuser || currentUser?.permissions?.includes('VIEW_WORKFLOW_RUN_OUTPUT');
  const canCancelPerm = currentUser?.is_superuser || currentUser?.permissions?.includes('CANCEL_WORKFLOW_RUN');

  const { run, loading, error, refetch: refetchRun } = useWorkflowRunDetail(runId, !!canViewRun);
  const { steps } = useRunSteps(runId, !!canViewRun);
  const { outputs, error: outputError } = useRunOutputs(runId, !!canViewRun);
  const { cancelRun } = useCancelRun();

  useEffect(() => {
    if (run?.run_code) document.title = `${run.run_code} — GuardianIQ`;
  }, [run]);

  const handleCancelRun = async () => {
    if (!runId || !window.confirm('Cancel this running workflow?')) return;
    await cancelRun(runId, refetchRun);
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

  if (loading && !run) {
    return <div className={styles.page}><div className={styles.stateCard}><div className={styles.stateDesc}>Loading run details...</div></div></div>;
  }

  if (error || !run) {
    return (
      <div className={styles.page}>
        <div className={styles.stateCard}>
          <div className={styles.stateTitle}>Unable to load run</div>
          <div className={styles.stateDesc}>{error || 'Run not found'}</div>
          <Button variant="secondary" size="sm" onClick={() => window.history.state && window.history.state.idx > 0 ? navigate(-1) : navigate('/workflow-runs')} icon={<ArrowLeft size={14} />}>Back</Button>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.page}>
      <button className={styles.clearBtn} onClick={() => window.history.state && window.history.state.idx > 0 ? navigate(-1) : navigate('/workflow-runs')} style={{ alignSelf: 'flex-start', marginBottom: '16px' }}>
        <ArrowLeft size={14} /> Back
      </button>

      <PageHeader
        title={`Run ${run.run_code}`}
        description={`Executed on ${run.started_at ? new Date(run.started_at).toLocaleString() : 'N/A'}`}
        actions={
          <ScreenGuide
            content={
              <div style={{ display: "flex", flexDirection: "column", gap: "12px", paddingRight: "4px" }}>
                <h4 style={{ color: "#fbbf24", margin: "0 0 4px 0", fontSize: "0.85rem" }}>Run Details</h4>
                <p style={{ margin: 0 }}>View the complete execution trace for this workflow run. Review agent actions, API calls, and final outputs to understand how the result was generated.</p>
              </div>
            }
          />
        }
      />

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
          </div>
          <div className={styles.headerActions}>
            <Button variant="secondary" size="sm" disabled title="Coming soon" icon={<Download size={14} />}>Evidence</Button>
            {canCancelPerm && (run.run_status === 'RUNNING' || run.run_status === 'QUEUED') && (
              <Button variant="danger" size="sm" onClick={handleCancelRun} icon={<XCircle size={14} />}>Cancel Run</Button>
            )}
          </div>
        </div>
      </div>

      {/* Two-Column Layout */}
      <div style={{ display: 'flex', gap: '24px', alignItems: 'flex-start' }}>
        
        {/* Left Column (60%) */}
        <div style={{ flex: '0 0 60%', display: 'flex', flexDirection: 'column', gap: '24px' }}>
          <div className={styles.detailCard}>
            <h3 className={styles.subHeading} style={{ padding: '20px 24px 0', margin: 0 }}>Execution Timeline</h3>
            <div style={{ padding: '24px' }}>
              <RunTimeline steps={steps} />
            </div>
          </div>

          <div className={styles.detailCard}>
            <h3 className={styles.subHeading} style={{ padding: '20px 24px 0', margin: 0 }}>Run Outputs</h3>
            <div style={{ padding: '24px' }}>
              <RunOutputViewer outputs={outputs} canViewRaw={!!canViewOutput} error={outputError} />
            </div>
          </div>
        </div>

        {/* Right Column (40%) */}
        <div style={{ flex: '1', display: 'flex', flexDirection: 'column', gap: '24px' }}>
          
          <div className={styles.wizardSideCard}>
            <h3 className={styles.subHeading}>Run Metadata</h3>
            
            <div className={styles.metaItem}>
              <span className={styles.metaLabel}>Status</span>
              <span className={`${styles.pill} ${runStatusPillClass(run.run_status)}`} style={{ alignSelf: 'flex-start' }}>
                {(run.run_status || '').replace(/_/g, ' ')}
              </span>
            </div>
            
            <div className={styles.metaItem}>
              <span className={styles.metaLabel}>Risk Level</span>
              <RiskBadge level={run.risk_level as any} />
            </div>
            
            <div className={styles.metaItem}>
              <span className={styles.metaLabel}>Schedule Name</span>
              <button className={styles.linkCell} onClick={() => navigate(`/workflow-scheduler/${run.schedule_id}`)}>
                {(run as any).schedule_name || run.schedule_id}
              </button>
            </div>
            
            <div className={styles.metaItem}>
              <span className={styles.metaLabel}>Workflow Name</span>
              <span className={styles.metaValue}>{run.workflow_name || run.workflow_id}</span>
            </div>

            <div className={styles.metaItem}>
              <span className={styles.metaLabel}>Trigger Type</span>
              <span className={styles.metaValue}>{run.trigger_type}</span>
            </div>
            
            <div className={styles.metaItem}>
              <span className={styles.metaLabel}>Triggered By</span>
              <span className={styles.metaValue}>{run.triggered_by_name || run.triggered_by_user_id || 'System'}</span>
            </div>

            <div className={styles.metaItem}>
              <span className={styles.metaLabel}>Started At</span>
              <span className={styles.metaValue}>{run.started_at ? new Date(run.started_at).toLocaleString() : '-'}</span>
            </div>
            
            <div className={styles.metaItem}>
              <span className={styles.metaLabel}>Completed At</span>
              <span className={styles.metaValue}>{run.completed_at ? new Date(run.completed_at).toLocaleString() : '-'}</span>
            </div>
            
            <div className={styles.metaItem}>
              <span className={styles.metaLabel}>Duration</span>
              <span className={styles.metaValue}>{formatDuration(run.duration_ms)}</span>
            </div>

            {run.error_message && (
               <div className={styles.metaItem} style={{ flexDirection: 'column', alignItems: 'flex-start', gap: '4px' }}>
                  <span className={styles.metaLabel}>Error Message</span>
                  <span className={styles.dangerText}>{run.error_message}</span>
               </div>
            )}
          </div>

          <div className={styles.wizardSideCard}>
            <h3 className={styles.subHeading}>Audit Events</h3>
            <AuditTimelinePanel entityType="WORKFLOW_RUN" entityId={runId || ''} />
          </div>

        </div>
      </div>
    </div>
  );
};

export default RunDetailPage;

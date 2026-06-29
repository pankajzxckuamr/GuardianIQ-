import React from 'react';
import { WorkflowRunStepResponse } from '../../types/phase2';
import { CheckCircle, Clock, PlayCircle, XCircle } from 'lucide-react';
import styles from '../../pages/phase2Shared.module.css';

interface Props {
  steps: WorkflowRunStepResponse[];
}

export const RunTimeline: React.FC<Props> = ({ steps }) => {
  // Ensure we show all steps or fallback order if missing some
  // The actual steps are passed in from DB, so we map them as they are ordered.
  return (
    <div className={styles.timelineTrack}>
      {steps.map((step, idx) => {
        let icon = <Clock size={18} style={{ color: 'var(--text-muted)' }} />;
        let statusClass = '';
        if (step.step_status === 'COMPLETED') { icon = <CheckCircle size={18} style={{ color: 'var(--color-success)' }} />; statusClass = styles.success; }
        else if (step.step_status === 'RUNNING') { icon = <PlayCircle size={18} style={{ color: 'var(--color-info)' }} className={styles.pulsing} />; statusClass = styles.info; }
        else if (step.step_status === 'FAILED') { icon = <XCircle size={18} style={{ color: 'var(--color-danger)' }} />; statusClass = styles.danger; }

        const durationStr = step.duration_ms ? `${(step.duration_ms / 1000).toFixed(1)}s` : '';

        return (
          <React.Fragment key={step.id}>
            <div className={styles.timelineNode}>
              <div className={`${styles.timelineIcon} ${statusClass}`}>{icon}</div>
              <div className={styles.timelineContent}>
                <div className={styles.timelineHeaderRow}>
                  <span className={styles.timelineLabel}>{step.step_code} <span className={styles.stepType}>({step.step_type})</span></span>
                  <span className={styles.timelineTime}>
                    {step.started_at && new Date(step.started_at).toLocaleTimeString()}
                    {durationStr && ` (${durationStr})`}
                  </span>
                </div>
                {step.step_status === 'FAILED' && step.error_message && (
                   <div className={styles.dangerCard} style={{ marginTop: '8px' }}>
                     <p className={styles.dangerText}>{step.error_message}</p>
                     {step.error_detail && <pre className={styles.codeBlock} style={{ marginTop: '4px' }}>{step.error_detail}</pre>}
                   </div>
                )}
                {(step.input_json || step.output_json) && (
                   <details className={styles.detailsToggle} style={{ marginTop: '8px' }}>
                     <summary>View Data Payload</summary>
                     {step.input_json && (
                       <>
                         <div style={{ marginTop: '8px', fontSize: '12px', fontWeight: 'bold' }}>Input:</div>
                         <pre className={styles.codeBlock}>{JSON.stringify(step.input_json, null, 2)}</pre>
                       </>
                     )}
                     {step.output_json && (
                       <>
                         <div style={{ marginTop: '8px', fontSize: '12px', fontWeight: 'bold' }}>Output:</div>
                         <pre className={styles.codeBlock}>{JSON.stringify(step.output_json, null, 2)}</pre>
                       </>
                     )}
                   </details>
                )}
              </div>
            </div>
            {idx < steps.length - 1 && (
              <div className={`${styles.timelineConnector} ${step.step_status === 'COMPLETED' ? styles.done : ''}`} />
            )}
          </React.Fragment>
        );
      })}
      {steps.length === 0 && <div className={styles.stateDesc}>No steps recorded.</div>}
    </div>
  );
};

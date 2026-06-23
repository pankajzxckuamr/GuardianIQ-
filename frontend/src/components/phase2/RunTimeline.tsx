import React from 'react';
import { WorkflowRunStepResponse } from '../../types/phase2';
import { CheckCircle, Clock, PlayCircle, XCircle } from 'lucide-react';
import styles from '../../pages/phase2Shared.module.css';

interface Props {
  steps: WorkflowRunStepResponse[];
}

export const RunTimeline: React.FC<Props> = ({ steps }) => {
  return (
    <div className={styles.timelineTrack}>
      {steps.map((step, idx) => {
        let icon = <Clock size={18} style={{ color: 'var(--text-muted)' }} />;
        if (step.step_status === 'COMPLETED') icon = <CheckCircle size={18} style={{ color: 'var(--color-success)' }} />;
        else if (step.step_status === 'RUNNING') icon = <PlayCircle size={18} style={{ color: 'var(--color-info)' }} />;
        else if (step.step_status === 'FAILED') icon = <XCircle size={18} style={{ color: 'var(--color-danger)' }} />;

        return (
          <React.Fragment key={step.id}>
            <div className={styles.timelineNode}>
              {icon}
              <span className={styles.timelineLabel}>{step.step_code}</span>
            </div>
            {idx < steps.length - 1 && (
              <div className={`${styles.timelineConnector} ${step.step_status === 'COMPLETED' ? styles.done : ''}`} />
            )}
          </React.Fragment>
        );
      })}
    </div>
  );
};

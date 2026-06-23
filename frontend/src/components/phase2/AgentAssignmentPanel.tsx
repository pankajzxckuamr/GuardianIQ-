import React from 'react';
import { AgentAssignmentResponse } from '../../types/phase2';
import styles from '../../pages/phase2Shared.module.css';

interface Props {
  assignment: AgentAssignmentResponse;
  readonly?: boolean;
}

export const AgentAssignmentPanel: React.FC<Props> = ({ assignment, readonly }) => {
  const allowedToolsCount = assignment.allowed_tools_json ? assignment.allowed_tools_json.length : 0;
  const blockedOpsCount = assignment.blocked_operations_json ? assignment.blocked_operations_json.length : 0;

  return (
    <div className={styles.section}>
      <div className={styles.detailHeader} style={{ marginBottom: '1rem' }}>
        <h4 className={styles.subHeading}>Agent ID: {assignment.agent_id}</h4>
        <span className={`${styles.pill} ${assignment.execution_mode === 'AUTONOMOUS' ? styles.pillDanger : styles.pillInfo}`}>
          {assignment.execution_mode}
        </span>
      </div>
      <div className={styles.fieldStack}>
        <div className={styles.mutedCell}>Model ID: {assignment.model_id || 'N/A'}</div>
        <div className={styles.mutedCell}>Role: {assignment.assignment_role}</div>
        <div className={styles.panelRow}>
          <span className={styles.panelStat} title={assignment.allowed_tools_json?.join(', ')}>
            {allowedToolsCount} Allowed Tools
          </span>
          <span className={styles.panelStat} title={assignment.blocked_operations_json?.join(', ')}>
            {blockedOpsCount} Blocked Operations
          </span>
        </div>
      </div>
      {!readonly && (
        <div className={styles.decisionFooter} style={{ marginTop: '1rem' }}>
          <button className={styles.textBtn}>Edit Configuration</button>
        </div>
      )}
    </div>
  );
};

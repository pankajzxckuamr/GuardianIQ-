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
      <div className={styles.detailHeader} style={{ marginBottom: '1rem', alignItems: 'flex-start' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
          <h4 className={styles.subHeading} style={{ margin: 0 }}>Agent: {assignment.agent_name || 'Unknown Agent'}</h4>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted, #64748b)' }}>ID: {assignment.agent_id}</span>
        </div>
        <span className={`${styles.pill} ${assignment.execution_mode === 'AUTONOMOUS' ? styles.pillDanger : styles.pillInfo}`}>
          {assignment.execution_mode}
        </span>
      </div>
      <div className={styles.fieldStack}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
          <div className={styles.mutedCell} style={{ fontWeight: 500, color: 'var(--text-primary, #f8fafc)' }}>
            Model: {assignment.model_name || 'N/A'}
          </div>
          {assignment.model_id && (
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted, #64748b)' }}>
              ID: {assignment.model_id}
            </span>
          )}
        </div>
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

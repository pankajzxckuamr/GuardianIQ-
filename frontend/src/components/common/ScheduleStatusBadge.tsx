import React from 'react';
import styles from './ScheduleStatusBadge.module.css';

export interface ScheduleStatusBadgeProps {
  status: string;
}

export const ScheduleStatusBadge: React.FC<ScheduleStatusBadgeProps> = ({ status }) => {
  let badgeClass = styles.neutral;
  
  switch (status) {
    case 'ACTIVE':
    case 'COMPLETED':
      badgeClass = styles.success;
      break;
    case 'PENDING_APPROVAL':
    case 'CANCELLED':
      badgeClass = styles.warning;
      break;
    case 'PAUSED':
    case 'RUNNING':
      badgeClass = styles.info;
      break;
    case 'FAILED':
      badgeClass = styles.danger;
      break;
    case 'RETRY_QUEUED':
      badgeClass = styles.accent;
      break;
    default:
      badgeClass = styles.neutral;
  }

  return (
    <span className={`${styles.badge} ${badgeClass}`}>
      {(status || '').replace(/_/g, ' ')}
    </span>
  );
};

import React from 'react';

export type IndicatorStatus = 'online' | 'offline' | 'degraded' | 'unknown';

export interface StatusIndicatorProps {
  status: IndicatorStatus;
  label: string;
}

const STATUS_ARIA_LABELS: Record<IndicatorStatus, string> = {
  online: 'Online',
  offline: 'Offline',
  degraded: 'Degraded',
  unknown: 'Unknown',
};

export const StatusIndicator: React.FC<StatusIndicatorProps> = ({ status, label }) => {
  return (
    <span className="status-indicator" role="status">
      <span
        className={`status-indicator__dot status-indicator__dot--${status}`}
        aria-label={STATUS_ARIA_LABELS[status]}
        aria-hidden="true"
      />
      <span className="status-indicator__label">{label}</span>
    </span>
  );
};

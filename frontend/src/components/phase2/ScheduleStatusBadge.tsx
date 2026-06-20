import React from 'react';
import { ScheduleStatus } from '../../types/phase2';

interface Props {
  status: ScheduleStatus;
}

const colorMap: Record<ScheduleStatus, string> = {
  DRAFT: 'bg-gray-100 text-gray-800 border-gray-200',
  PENDING_APPROVAL: 'bg-amber-100 text-amber-800 border-amber-200',
  ACTIVE: 'bg-green-100 text-green-800 border-green-200',
  PAUSED: 'bg-blue-100 text-blue-800 border-blue-200',
  FAILED: 'bg-red-100 text-red-800 border-red-200',
  RETIRED: 'bg-slate-100 text-slate-800 border-slate-200',
};

export const ScheduleStatusBadge: React.FC<Props> = ({ status }) => {
  return (
    <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full border ${colorMap[status] || colorMap.DRAFT}`}>
      {status}
    </span>
  );
};

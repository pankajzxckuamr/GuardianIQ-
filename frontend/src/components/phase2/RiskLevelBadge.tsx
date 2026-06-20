import React from 'react';
import { RiskLevel } from '../../types/phase2';

interface Props {
  riskLevel: RiskLevel;
}

const colorMap: Record<RiskLevel, string> = {
  LOW: 'bg-green-100 text-green-800 border-green-200',
  MEDIUM: 'bg-amber-100 text-amber-800 border-amber-200',
  HIGH: 'bg-orange-100 text-orange-800 border-orange-200',
  CRITICAL: 'bg-red-100 text-red-800 border-red-200',
};

export const RiskLevelBadge: React.FC<Props> = ({ riskLevel }) => {
  return (
    <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full border ${colorMap[riskLevel] || colorMap.LOW}`}>
      {riskLevel}
    </span>
  );
};

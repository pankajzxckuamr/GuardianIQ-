import React from 'react';
import { AlertCircle } from 'lucide-react';

interface Props {
  approvalRequired: boolean;
  reasons: string[];
  approverGroupName?: string;
}

export const ApprovalRequirementBanner: React.FC<Props> = ({ approvalRequired, reasons, approverGroupName }) => {
  if (!approvalRequired) return null;

  return (
    <div className="bg-amber-50 border-l-4 border-amber-400 p-4 my-4">
      <div className="flex items-start">
        <div className="flex-shrink-0">
          <AlertCircle className="h-5 w-5 text-amber-400" aria-hidden="true" />
        </div>
        <div className="ml-3">
          <h3 className="text-sm font-medium text-amber-800">
            Approval Required {approverGroupName && `from ${approverGroupName}`}
          </h3>
          <div className="mt-2 text-sm text-amber-700">
            <ul className="list-disc pl-5 space-y-1">
              {reasons.map((reason, idx) => (
                <li key={idx}>{reason}</li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

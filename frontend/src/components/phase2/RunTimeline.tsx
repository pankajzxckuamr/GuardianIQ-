import React from 'react';
import { WorkflowRunStepResponse } from '../../types/phase2';
import { CheckCircle, Clock, PlayCircle, XCircle } from 'lucide-react';

interface Props {
  steps: WorkflowRunStepResponse[];
}

export const RunTimeline: React.FC<Props> = ({ steps }) => {
  return (
    <div className="flex items-center space-x-4 py-4 overflow-x-auto">
      {steps.map((step, idx) => {
        let icon = <Clock className="w-5 h-5 text-gray-400" />;
        let textColor = 'text-gray-500';
        
        if (step.step_status === 'COMPLETED') {
          icon = <CheckCircle className="w-5 h-5 text-green-500" />;
          textColor = 'text-green-700';
        } else if (step.step_status === 'RUNNING') {
          icon = <PlayCircle className="w-5 h-5 text-blue-500 animate-pulse" />;
          textColor = 'text-blue-700';
        } else if (step.step_status === 'FAILED') {
          icon = <XCircle className="w-5 h-5 text-red-500" />;
          textColor = 'text-red-700';
        }

        return (
          <React.Fragment key={step.id}>
            <div className="flex flex-col items-center min-w-[120px]">
              {icon}
              <span className={`mt-2 text-xs font-medium ${textColor}`}>{step.step_code}</span>
            </div>
            {idx < steps.length - 1 && (
              <div className={`h-0.5 w-16 ${step.step_status === 'COMPLETED' ? 'bg-green-500' : 'bg-gray-200'}`} />
            )}
          </React.Fragment>
        );
      })}
    </div>
  );
};

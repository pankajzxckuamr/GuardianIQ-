import React from 'react';
import { AgentAssignmentResponse } from '../../types/phase2';

interface Props {
  assignment: AgentAssignmentResponse;
  readonly?: boolean;
}

export const AgentAssignmentPanel: React.FC<Props> = ({ assignment, readonly }) => {
  const allowedToolsCount = assignment.allowed_tools_json ? assignment.allowed_tools_json.length : 0;
  const blockedOpsCount = assignment.blocked_operations_json ? assignment.blocked_operations_json.length : 0;

  return (
    <div className="bg-white p-4 rounded shadow-sm border border-gray-200">
      <div className="flex justify-between items-center mb-4">
        <h4 className="font-medium text-gray-900">Agent ID: {assignment.agent_id}</h4>
        <span className={`px-2 py-1 rounded text-xs font-medium ${
          assignment.execution_mode === 'AUTONOMOUS' ? 'bg-red-100 text-red-800' : 'bg-blue-100 text-blue-800'
        }`}>
          {assignment.execution_mode}
        </span>
      </div>
      <div className="text-sm text-gray-600 space-y-2">
        <p>Model ID: {assignment.model_id || 'N/A'}</p>
        <p>Role: {assignment.assignment_role}</p>
        <div className="flex gap-4">
          <p className="font-semibold text-gray-800" title={assignment.allowed_tools_json?.join(', ')}>
            {allowedToolsCount} Allowed Tools
          </p>
          <p className="font-semibold text-gray-800" title={assignment.blocked_operations_json?.join(', ')}>
            {blockedOpsCount} Blocked Operations
          </p>
        </div>
      </div>
      {!readonly && (
        <div className="mt-4 pt-4 border-t text-right">
          <button className="text-sm text-indigo-600 hover:text-indigo-800">Edit Configuration</button>
        </div>
      )}
    </div>
  );
};

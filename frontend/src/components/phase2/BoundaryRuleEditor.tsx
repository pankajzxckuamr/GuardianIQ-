import React from 'react';
import { AlertTriangle } from 'lucide-react';

interface ToolOption {
  id: string;
  name: string;
  capability: string;
}

interface Props {
  allowedTools: string[];
  allowedDataSources: string[];
  blockedOperations: string[];
  onChange: (field: string, value: any) => void;
  toolOptions: ToolOption[];
}

export const BoundaryRuleEditor: React.FC<Props> = ({ allowedTools, allowedDataSources, blockedOperations, onChange, toolOptions }) => {
  return (
    <div className="space-y-4">
      <div>
        <h4 className="text-sm font-medium text-gray-900">Allowed Tools</h4>
        <div className="mt-2 space-y-2">
          {toolOptions.map(tool => (
            <label key={tool.id} className="inline-flex items-center mr-4">
              <input
                type="checkbox"
                checked={allowedTools.includes(tool.id)}
                onChange={(e) => {
                  const newTools = e.target.checked
                    ? [...allowedTools, tool.id]
                    : allowedTools.filter(t => t !== tool.id);
                  onChange('allowedTools', newTools);
                }}
                className="rounded border-gray-300 text-indigo-600 shadow-sm focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50"
              />
              <span className="ml-2 flex items-center gap-1 text-sm text-gray-700">
                {tool.name}
                {tool.capability === 'WRITE' && <AlertTriangle className="w-4 h-4 text-amber-500" title="Write capability" />}
              </span>
            </label>
          ))}
        </div>
      </div>
      <div>
        <h4 className="text-sm font-medium text-gray-900">Blocked Operations (Comma separated)</h4>
        <input
          type="text"
          className="mt-1 block w-full border-gray-300 rounded-md shadow-sm sm:text-sm"
          value={blockedOperations.join(', ')}
          onChange={(e) => onChange('blockedOperations', e.target.value.split(',').map(s => s.trim()).filter(Boolean))}
          placeholder="e.g. DROP TABLE, DELETE, EXECUTE"
        />
      </div>
    </div>
  );
};

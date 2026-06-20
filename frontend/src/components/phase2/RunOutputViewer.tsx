import React, { useState } from 'react';
import { WorkflowRunOutputResponse } from '../../types/phase2';

interface Props {
  outputs: WorkflowRunOutputResponse[];
  canViewRaw: boolean;
}

export const RunOutputViewer: React.FC<Props> = ({ outputs, canViewRaw }) => {
  const [activeTab, setActiveTab] = useState<'FINDINGS' | 'RECOMMENDATIONS' | 'EVIDENCE' | 'RAW'>('FINDINGS');

  const tabs = ['FINDINGS', 'RECOMMENDATIONS', 'EVIDENCE'];
  if (canViewRaw) tabs.push('RAW');

  const activeOutput = outputs.find(o => o.output_type === activeTab) || outputs[0];

  return (
    <div className="bg-white border rounded shadow-sm">
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex">
          {tabs.map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab as any)}
              className={`w-1/4 py-4 px-1 text-center border-b-2 font-medium text-sm ${
                activeTab === tab
                  ? 'border-indigo-500 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab}
            </button>
          ))}
        </nav>
      </div>
      <div className="p-4">
        {activeOutput ? (
          <pre className="whitespace-pre-wrap text-sm text-gray-800 font-mono bg-gray-50 p-4 rounded">
            {activeOutput.output_content}
          </pre>
        ) : (
          <p className="text-gray-500 italic text-sm">No output available for {activeTab}</p>
        )}
      </div>
    </div>
  );
};

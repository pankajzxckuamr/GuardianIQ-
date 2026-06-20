import React, { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';
import { useToast } from '../hooks/useToast';
import { Shield, AlertTriangle, CheckCircle, XCircle, Search, RefreshCw } from 'lucide-react';
import { storage } from '../utils/storage';

export const AuthorizationSimulator: React.FC = () => {
  const { showToast } = useToast();
  
  const [subjectType, setSubjectType] = useState('USER');
  const [subjectId, setSubjectId] = useState('');
  const [objectType, setObjectType] = useState('SCHEDULE');
  const [objectId, setObjectId] = useState('');
  const [actionId, setActionId] = useState('VIEW_WORKFLOW_SCHEDULE');
  
  const [envEmergency, setEnvEmergency] = useState(false);
  const [envDelegation, setEnvDelegation] = useState(false);

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const actions = [
    'CREATE_WORKFLOW_SCHEDULE', 'VIEW_WORKFLOW_SCHEDULE', 'UPDATE_WORKFLOW_SCHEDULE',
    'SUBMIT_WORKFLOW_SCHEDULE', 'ACTIVATE_WORKFLOW_SCHEDULE', 'PAUSE_WORKFLOW_SCHEDULE',
    'RESUME_WORKFLOW_SCHEDULE', 'RETIRE_WORKFLOW_SCHEDULE', 'RUN_WORKFLOW_SCHEDULE',
    'VIEW_WORKFLOW_RUN', 'CANCEL_WORKFLOW_RUN', 'VIEW_WORKFLOW_RUN_OUTPUT',
    'ASSIGN_AI_AGENT_TO_WORKFLOW', 'EVALUATE_AUTHORIZATION'
  ];

  const handleEvaluate = async () => {
    if (!subjectId || !objectId || !actionId) {
      showToast('Please fill out Subject, Object, and Action', 'error');
      return;
    }
    
    setLoading(true);
    try {
      const token = storage.get<string>('guardianiq_access_token');
      const res = await fetch('/api/v1/authorization/evaluate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({
          subject_type: subjectType,
          subject_id: subjectId,
          object_type: objectType,
          object_id: objectId,
          action: actionId,
          environment: {
            emergency_flag: envEmergency,
            delegation_active: envDelegation
          }
        })
      });
      const json = await res.json();
      if (!json.success) throw new Error(json.error);
      setResult(json.data);
    } catch (e: any) {
      showToast(e.message || 'Simulation failed', 'error');
    } finally {
      setLoading(false);
    }
  };

  const copyPayload = () => {
    const payload = {
      subject_type: subjectType, subject_id: subjectId,
      object_type: objectType, object_id: objectId,
      action: actionId,
      environment: { emergency_flag: envEmergency, delegation_active: envDelegation }
    };
    navigator.clipboard.writeText(JSON.stringify(payload, null, 2));
    showToast('Payload copied to clipboard', 'success');
  };

  return (
    <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8 space-y-6">
      <div className="bg-indigo-50 border-l-4 border-indigo-500 p-4">
        <div className="flex">
          <Shield className="h-5 w-5 text-indigo-500" />
          <div className="ml-3">
            <p className="text-sm text-indigo-700">This tool evaluates authorization only. It does not grant access or mutate permissions.</p>
          </div>
        </div>
      </div>

      <div className="bg-white shadow sm:rounded-lg border border-gray-200">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-gray-900 mb-6">Simulation Parameters</h3>
          
          <div className="grid grid-cols-1 gap-y-6 gap-x-4 sm:grid-cols-3">
            {/* Subject */}
            <div className="bg-gray-50 p-4 rounded border border-gray-200">
              <h4 className="font-semibold text-gray-700 mb-4 border-b pb-2">Subject</h4>
              <div className="space-y-4">
                <div>
                  <label className="block text-xs font-medium text-gray-500">Type</label>
                  <select value={subjectType} onChange={e => setSubjectType(e.target.value)} className="mt-1 block w-full text-sm border-gray-300 rounded-md">
                    <option value="USER">User</option>
                    <option value="AGENT">AI Agent</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-500">ID / Search</label>
                  <input type="text" value={subjectId} onChange={e => setSubjectId(e.target.value)} placeholder={`Enter ${subjectType} ID`} className="mt-1 block w-full text-sm border-gray-300 rounded-md" />
                </div>
              </div>
            </div>

            {/* Object */}
            <div className="bg-gray-50 p-4 rounded border border-gray-200">
              <h4 className="font-semibold text-gray-700 mb-4 border-b pb-2">Object</h4>
              <div className="space-y-4">
                <div>
                  <label className="block text-xs font-medium text-gray-500">Type</label>
                  <select value={objectType} onChange={e => setObjectType(e.target.value)} className="mt-1 block w-full text-sm border-gray-300 rounded-md">
                    <option value="SCHEDULE">Schedule</option>
                    <option value="RUN">Run</option>
                    <option value="OUTPUT">Output</option>
                    <option value="ASSIGNMENT">Agent Assignment</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-500">ID / Search</label>
                  <input type="text" value={objectId} onChange={e => setObjectId(e.target.value)} placeholder={`Enter ${objectType} ID`} className="mt-1 block w-full text-sm border-gray-300 rounded-md" />
                </div>
              </div>
            </div>

            {/* Action & Env */}
            <div className="bg-gray-50 p-4 rounded border border-gray-200">
              <h4 className="font-semibold text-gray-700 mb-4 border-b pb-2">Action & Environment</h4>
              <div className="space-y-4">
                <div>
                  <label className="block text-xs font-medium text-gray-500">Action Code</label>
                  <select value={actionId} onChange={e => setActionId(e.target.value)} className="mt-1 block w-full text-sm border-gray-300 rounded-md">
                    {actions.map(a => <option key={a} value={a}>{a}</option>)}
                  </select>
                </div>
                <div className="space-y-2 pt-2">
                  <label className="flex items-center text-sm text-gray-700">
                    <input type="checkbox" checked={envEmergency} onChange={e => setEnvEmergency(e.target.checked)} className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500 mr-2"/>
                    Emergency Flag Active
                  </label>
                  <label className="flex items-center text-sm text-gray-700">
                    <input type="checkbox" checked={envDelegation} onChange={e => setEnvDelegation(e.target.checked)} className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500 mr-2"/>
                    Delegation Active
                  </label>
                </div>
              </div>
            </div>
          </div>
          
          <div className="mt-6 flex justify-end">
            <button onClick={handleEvaluate} disabled={loading} className="inline-flex justify-center py-2 px-6 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700">
              {loading ? <RefreshCw className="w-5 h-5 animate-spin" /> : 'Evaluate Access'}
            </button>
          </div>
        </div>
      </div>

      {result && (
        <div className="bg-white shadow sm:rounded-lg border border-gray-200 overflow-hidden">
          <div className={`px-4 py-5 sm:px-6 ${result.allowed ? 'bg-green-100 border-b border-green-200' : 'bg-red-100 border-b border-red-200'}`}>
            <h3 className={`text-2xl font-bold flex items-center gap-2 ${result.allowed ? 'text-green-800' : 'text-red-800'}`}>
              {result.allowed ? <CheckCircle className="w-8 h-8"/> : <XCircle className="w-8 h-8"/>}
              {result.allowed ? 'ALLOW' : 'DENY'}
            </h3>
            <p className={`mt-1 text-sm ${result.allowed ? 'text-green-700' : 'text-red-700'}`}>
              {result.allowed ? 'Subject is authorized to perform this action.' : 'Subject lacks required permissions or fails ABAC conditions.'}
            </p>
          </div>
          
          <div className="px-4 py-5 sm:p-6 grid grid-cols-1 gap-6 sm:grid-cols-3 text-sm">
            <div>
              <h4 className="font-semibold text-gray-900 border-b pb-1 mb-2">RBAC Check</h4>
              <p className={result.rbac_passed ? 'text-green-600' : 'text-red-600'}>
                {result.rbac_passed ? 'Passed (Roles matched)' : 'Failed (Missing roles)'}
              </p>
            </div>
            <div>
              <h4 className="font-semibold text-gray-900 border-b pb-1 mb-2">ABAC Check</h4>
              <p className={result.abac_passed ? 'text-green-600' : 'text-red-600'}>
                {result.abac_passed ? 'Passed (All conditions met)' : 'Failed (Conditions unmet)'}
              </p>
              {result.failed_conditions && result.failed_conditions.length > 0 && (
                <ul className="list-disc pl-5 mt-2 text-xs text-red-500">
                  {result.failed_conditions.map((fc: string, i: number) => <li key={i}>{fc}</li>)}
                </ul>
              )}
            </div>
            <div>
              <h4 className="font-semibold text-gray-900 border-b pb-1 mb-2">Relationship Check</h4>
              <p className={result.relationship_passed ? 'text-green-600' : 'text-gray-500'}>
                {result.relationship_passed ? 'Passed (Owner/Delegate)' : 'N/A or Failed'}
              </p>
            </div>
          </div>
          <div className="px-4 py-3 bg-gray-50 border-t border-gray-200 text-right">
            <button onClick={copyPayload} className="text-sm text-indigo-600 hover:text-indigo-800 font-medium">Copy Request JSON</button>
          </div>
        </div>
      )}
    </div>
  );
};

export default AuthorizationSimulator;

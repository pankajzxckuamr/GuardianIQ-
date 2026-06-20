import React, { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';
import { useToast } from '../hooks/useToast';
import { BoundaryRuleEditor } from '../components/phase2/BoundaryRuleEditor';
import { AgentAssignmentPanel } from '../components/phase2/AgentAssignmentPanel';
import { Shield, Filter, Search, Plus, X, AlertCircle, Edit2, Play, CheckCircle, RefreshCw } from 'lucide-react';

// A basic drawer component to overlay on the right
const Drawer = ({ open, onClose, title, children }: any) => {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 overflow-hidden">
      <div className="absolute inset-0 bg-gray-500 bg-opacity-75 transition-opacity" onClick={onClose} />
      <div className="fixed inset-y-0 right-0 max-w-xl w-full flex">
        <div className="w-full h-full flex flex-col bg-white shadow-xl">
          <div className="px-4 py-6 bg-gray-50 sm:px-6 flex justify-between items-center border-b">
            <h2 className="text-lg font-medium text-gray-900">{title}</h2>
            <button onClick={onClose} className="text-gray-400 hover:text-gray-500"><X className="w-6 h-6"/></button>
          </div>
          <div className="flex-1 h-0 overflow-y-auto p-6">
            {children}
          </div>
        </div>
      </div>
    </div>
  );
};

export const AgentAssignmentMatrix: React.FC = () => {
  const { currentUser } = useAuth();
  const { showToast } = useToast();

  const canEdit = currentUser?.is_superuser || currentUser?.permissions?.includes('ASSIGN_AI_AGENT_TO_WORKFLOW');

  const [assignments, setAssignments] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [filterWorkflow, setFilterWorkflow] = useState('');
  const [filterAgent, setFilterAgent] = useState('');
  const [filterMode, setFilterMode] = useState('');
  const [filterApproval, setFilterApproval] = useState('');

  // Drawers
  const [drawerMode, setDrawerMode] = useState<'EDIT' | 'READ' | 'CREATE' | null>(null);
  const [selectedAssignment, setSelectedAssignment] = useState<any | null>(null);

  // Edit State
  const [formData, setFormData] = useState<any>({});
  const [validating, setValidating] = useState(false);
  const [validationResult, setValidationResult] = useState<any>(null);

  // Lookups
  const [tools, setTools] = useState<any[]>([]);
  const [agents, setAgents] = useState<any[]>([]);
  const [models, setModels] = useState<any[]>([]);

  const fetchWithAuth = async (url: string) => {
    const token = localStorage.getItem('guardianiq_access_token');
    const res = await fetch(url, { headers: { 'Authorization': `Bearer ${token}` } });
    const json = await res.json();
    return json.data?.items || json.data || [];
  };

  const fetchAssignments = async () => {
    setLoading(true);
    try {
      // Assuming a flattened endpoint or we fetch schedules and flatten. 
      // The prompt suggests /api/v1/workflow-scheduler/agent-assignments
      const items = await fetchWithAuth('/api/v1/workflow-scheduler/agent-assignments');
      setAssignments(items);
    } catch (e: any) {
      setError(e.message || 'Failed to load assignments');
      // Mock data just in case the endpoint isn't fully implemented on backend yet to prevent empty screen crash
      setAssignments([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAssignments();
    fetchWithAuth('/api/registry/tools').then(setTools).catch(() => {});
    fetchWithAuth('/api/registry/agents?status=ACTIVE').then(setAgents).catch(() => {});
    fetchWithAuth('/api/registry/models').then(setModels).catch(() => {});
  }, []);

  const openDrawer = (mode: 'EDIT' | 'READ' | 'CREATE', item?: any) => {
    setDrawerMode(mode);
    setValidationResult(null);
    if (item) {
      setSelectedAssignment(item);
      setFormData({
        id: item.id,
        schedule_id: item.schedule_id,
        agent_id: item.agent_id,
        model_id: item.model_id,
        execution_mode: item.execution_mode,
        confidence_threshold: item.confidence_threshold,
        allowed_tools_json: item.allowed_tools_json || [],
        allowed_data_sources_json: item.allowed_data_sources_json || [],
        blocked_operations_json: item.blocked_operations_json || [],
        status: item.status || 'ACTIVE'
      });
    } else {
      setSelectedAssignment(null);
      setFormData({
        agent_id: '', model_id: '', execution_mode: 'READ_ONLY', confidence_threshold: 80,
        allowed_tools_json: [], allowed_data_sources_json: [], blocked_operations_json: [],
        schedule_id: '', status: 'ACTIVE'
      });
    }
  };

  const closeDrawer = () => setDrawerMode(null);

  const handleRowClick = (item: any) => {
    if (canEdit) openDrawer('EDIT', item);
    else openDrawer('READ', item);
  };

  const handleFormChange = (field: string, val: any) => {
    setFormData((prev: any) => ({ ...prev, [field]: val }));
    setValidationResult(null);
  };

  const handleValidateBoundary = async () => {
    setValidating(true);
    try {
      const token = localStorage.getItem('guardianiq_access_token');
      const res = await fetch('/api/v1/authorization/evaluate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({
          subject_type: 'USER',
          subject_id: currentUser?.id,
          object_type: 'ASSIGNMENT',
          object_id: formData.id || 'new',
          action: 'ASSIGN_AI_AGENT_TO_WORKFLOW',
          environment: { payload: formData }
        })
      });
      const json = await res.json();
      setValidationResult(json.data);
    } catch (e) {
      setValidationResult({ allowed: false, error: 'Validation request failed' });
    } finally {
      setValidating(false);
    }
  };

  const handleSave = async () => {
    try {
      const token = localStorage.getItem('guardianiq_access_token');
      const method = drawerMode === 'CREATE' ? 'POST' : 'PUT';
      const url = drawerMode === 'CREATE' 
        ? `/api/v1/workflow-scheduler/schedules/${formData.schedule_id}/agent-assignments`
        : `/api/v1/workflow-scheduler/schedules/${formData.schedule_id}/agent-assignments/${formData.id}`;

      const res = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify(formData)
      });
      const json = await res.json();
      if (!json.success) throw new Error(json.error);
      
      showToast('Assignment saved successfully', 'success');
      closeDrawer();
      fetchAssignments();
    } catch (e: any) {
      showToast(e.message || 'Failed to save', 'error');
    }
  };

  const handleDisable = async (item: any, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!window.confirm('Are you sure you want to disable this assignment?')) return;
    try {
      const token = localStorage.getItem('guardianiq_access_token');
      const res = await fetch(`/api/v1/workflow-scheduler/schedules/${item.schedule_id}/agent-assignments/${item.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({ ...item, status: 'INACTIVE' })
      });
      const json = await res.json();
      if (!json.success) throw new Error(json.error);
      showToast('Assignment disabled', 'success');
      fetchAssignments();
    } catch (e: any) {
      showToast(e.message || 'Failed to disable', 'error');
    }
  };

  const filtered = assignments.filter(a => {
    if (filterWorkflow && a.workflow_name !== filterWorkflow) return false;
    if (filterAgent && a.agent_id !== filterAgent) return false;
    if (filterMode && a.execution_mode !== filterMode) return false;
    if (filterApproval === 'yes' && !a.approval_required) return false;
    if (filterApproval === 'no' && a.approval_required) return false;
    return true;
  });

  const activeAssignments = filtered.filter(a => a.status !== 'INACTIVE');
  const inactiveAssignments = filtered.filter(a => a.status === 'INACTIVE');
  const displayList = [...activeAssignments, ...inactiveAssignments];

  const hasWriteTool = tools.some(t => formData.allowed_tools_json.includes(t.id) && (t.capability === 'WRITE' || t.capability === 'EXECUTE'));

  return (
    <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">Agent Assignment Matrix</h1>
          <p className="mt-1 text-sm text-gray-500">Global overview of AI agents assigned to governance workflows.</p>
        </div>
        {canEdit && (
          <button onClick={() => openDrawer('CREATE')} className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700">
            <Plus className="mr-2 h-4 w-4"/> Add Assignment
          </button>
        )}
      </div>

      <div className="bg-white p-4 rounded-md shadow border border-gray-200 flex flex-wrap gap-4 items-end">
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">Agent</label>
          <select value={filterAgent} onChange={e => setFilterAgent(e.target.value)} className="block w-full text-sm border-gray-300 rounded-md">
            <option value="">All</option>
            {agents.map(a => <option key={a.id} value={a.id}>{a.name}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">Mode</label>
          <select value={filterMode} onChange={e => setFilterMode(e.target.value)} className="block w-full text-sm border-gray-300 rounded-md">
            <option value="">All</option>
            <option value="READ_ONLY">READ_ONLY</option>
            <option value="RECOMMEND_ONLY">RECOMMEND_ONLY</option>
            <option value="APPROVAL_REQUIRED">APPROVAL_REQUIRED</option>
            <option value="LIMITED_EXECUTION">LIMITED_EXECUTION</option>
          </select>
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">Approval Required</label>
          <select value={filterApproval} onChange={e => setFilterApproval(e.target.value)} className="block w-full text-sm border-gray-300 rounded-md">
            <option value="">All</option>
            <option value="yes">Yes</option>
            <option value="no">No</option>
          </select>
        </div>
        <button onClick={() => { setFilterWorkflow(''); setFilterAgent(''); setFilterMode(''); setFilterApproval(''); }} className="text-sm text-indigo-600 hover:text-indigo-800 pb-2">
          Clear Filters
        </button>
      </div>

      <div className="bg-white shadow border-b border-gray-200 sm:rounded-lg overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Workflow</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Schedule</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Agent</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Mode</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Tools</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Approval</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {displayList.map(a => (
              <tr key={a.id} onClick={() => handleRowClick(a)} className={`cursor-pointer transition-colors ${a.status === 'INACTIVE' ? 'bg-gray-100 opacity-60' : 'hover:bg-gray-50'}`}>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{a.workflow_name || a.workflow_id}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{a.schedule_name || a.schedule_id}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{a.agent_name || a.agent_id}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm">
                  <span className="bg-blue-100 text-blue-800 px-2 py-0.5 rounded text-xs">{a.execution_mode}</span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 group relative">
                  <span className="border-b border-dashed border-gray-400">{a.allowed_tools_json?.length || 0} allowed</span>
                  {a.allowed_tools_json?.length > 0 && (
                    <div className="hidden group-hover:block absolute z-10 w-48 bg-gray-800 text-white text-xs rounded p-2 mt-1">
                      {a.allowed_tools_json.map((t: string) => <div key={t}>{tools.find(x => x.id === t)?.name || t}</div>)}
                    </div>
                  )}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  {a.approval_required ? <span className="text-amber-600 text-xs font-bold bg-amber-100 px-2 py-1 rounded">YES</span> : <span className="text-gray-500 text-xs">NO</span>}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                  {a.status === 'ACTIVE' && canEdit && (
                    <button onClick={(e) => handleDisable(a, e)} className="text-red-500 hover:text-red-700 font-medium text-xs border border-red-200 px-2 py-1 rounded bg-white">Disable</button>
                  )}
                  {a.status === 'INACTIVE' && <span className="text-gray-400 text-xs font-bold">DISABLED</span>}
                </td>
              </tr>
            ))}
            {displayList.length === 0 && (
              <tr><td colSpan={7} className="px-6 py-12 text-center text-gray-500">No agent assignments found.</td></tr>
            )}
          </tbody>
        </table>
      </div>

      <Drawer 
        open={drawerMode !== null} 
        onClose={closeDrawer} 
        title={drawerMode === 'READ' ? 'Assignment Details' : drawerMode === 'EDIT' ? 'Edit Assignment' : 'Create Assignment'}
      >
        {drawerMode === 'READ' ? (
          <AgentAssignmentPanel assignment={selectedAssignment} readonly={true} />
        ) : (
          <div className="space-y-6">
            {drawerMode === 'CREATE' && (
              <div>
                <label className="block text-sm font-medium text-gray-700">Schedule ID</label>
                <input type="text" value={formData.schedule_id} onChange={e => handleFormChange('schedule_id', e.target.value)} className="mt-1 block w-full text-sm border-gray-300 rounded-md" placeholder="Provide schedule UUID" />
              </div>
            )}
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Agent</label>
                <select value={formData.agent_id} onChange={e => handleFormChange('agent_id', e.target.value)} className="mt-1 block w-full text-sm border-gray-300 rounded-md">
                  <option value="">Select Agent</option>
                  {agents.map(a => <option key={a.id} value={a.id}>{a.name}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Model</label>
                <select value={formData.model_id} onChange={e => handleFormChange('model_id', e.target.value)} className="mt-1 block w-full text-sm border-gray-300 rounded-md">
                  <option value="">Select Model</option>
                  {models.map(m => <option key={m.id} value={m.id}>{m.name}</option>)}
                </select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Execution Mode</label>
                <select value={formData.execution_mode} onChange={e => handleFormChange('execution_mode', e.target.value)} className="mt-1 block w-full text-sm border-gray-300 rounded-md">
                  <option value="READ_ONLY">READ_ONLY</option>
                  <option value="RECOMMEND_ONLY">RECOMMEND_ONLY</option>
                  <option value="APPROVAL_REQUIRED">APPROVAL_REQUIRED</option>
                  <option value="LIMITED_EXECUTION">LIMITED_EXECUTION</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Confidence Threshold</label>
                <input type="range" min="0" max="100" value={formData.confidence_threshold} onChange={e => handleFormChange('confidence_threshold', parseInt(e.target.value))} className="mt-1 block w-full" />
                <div className="text-xs text-center text-gray-500 mt-1">{formData.confidence_threshold}%</div>
              </div>
            </div>

            <div className="border-t pt-6">
              <BoundaryRuleEditor 
                allowedTools={formData.allowed_tools_json}
                allowedDataSources={formData.allowed_data_sources_json}
                blockedOperations={formData.blocked_operations_json}
                onChange={handleFormChange}
                toolOptions={tools}
              />
            </div>

            {hasWriteTool && (
              <div className="bg-amber-50 p-3 rounded border border-amber-200 flex gap-2 items-start">
                <AlertCircle className="w-5 h-5 text-amber-500 flex-shrink-0" />
                <p className="text-sm text-amber-800">This tool requires approval_required=true on the schedule. Ensure the schedule is configured correctly.</p>
              </div>
            )}

            <div className="bg-gray-50 p-4 rounded-md border border-gray-200">
              <div className="flex justify-between items-center mb-2">
                <h4 className="text-sm font-semibold text-gray-900">Authorization Check</h4>
                <button onClick={handleValidateBoundary} disabled={validating} className="text-xs font-medium text-indigo-600 hover:text-indigo-800 bg-indigo-50 border border-indigo-200 px-2 py-1 rounded flex items-center">
                  {validating ? <RefreshCw className="w-3 h-3 mr-1 animate-spin" /> : <Shield className="w-3 h-3 mr-1" />}
                  Validate Boundary
                </button>
              </div>
              {validationResult && (
                <div className={`mt-2 p-2 rounded text-xs font-medium flex items-center ${validationResult.allowed ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                  {validationResult.allowed ? <CheckCircle className="w-4 h-4 mr-2" /> : <XCircle className="w-4 h-4 mr-2" />}
                  {validationResult.allowed ? 'Boundary validation passed.' : 'Validation failed: Exceeds allowed limits.'}
                </div>
              )}
            </div>

            <div className="pt-4 flex justify-end gap-3 border-t">
              <button onClick={closeDrawer} className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded hover:bg-gray-50">Cancel</button>
              <button onClick={handleSave} className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded hover:bg-indigo-700">Save Assignment</button>
            </div>
          </div>
        )}
      </Drawer>
    </div>
  );
};

export default AgentAssignmentMatrix;

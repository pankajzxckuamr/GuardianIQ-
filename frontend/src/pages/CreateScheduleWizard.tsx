import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import WizardShell from '../components/common/WizardShell';
import { useAuth } from '../hooks/useAuth';
import { useToast } from '../hooks/useToast';
import { scheduleApi } from '../api/phase2Client';
import { ApprovalRequirementBanner } from '../components/phase2/ApprovalRequirementBanner';
import { CronExpressionBuilder } from '../components/phase2/CronExpressionBuilder';
import { BoundaryRuleEditor } from '../components/phase2/BoundaryRuleEditor';
import { AlertCircle } from 'lucide-react';

const steps = [
  { label: 'Select Workflow' },
  { label: 'Agent & Model' },
  { label: 'Boundaries' },
  { label: 'Schedule Configuration' },
  { label: 'Governance Controls' },
  { label: 'Review & Submit' }
];

export const CreateScheduleWizard: React.FC = () => {
  const { currentUser } = useAuth();
  const { showToast } = useToast();
  const navigate = useNavigate();

  const [currentStep, setCurrentStep] = useState(0);
  const [formData, setFormData] = useState<any>({
    workflow_id: '',
    schedule_name: '',
    schedule_code: '',
    agent_id: '',
    model_id: '',
    execution_mode: 'READ_ONLY',
    confidence_threshold: 80,
    allowed_tools_json: [],
    allowed_data_sources_json: [],
    blocked_operations_json: [],
    max_records: 100,
    max_runtime_seconds: 3600,
    schedule_type: 'MANUAL',
    cron_expression: '',
    timezone: 'UTC',
    start_at: '',
    end_at: '',
    concurrency_policy: 'SKIP_IF_RUNNING',
    retry_policy_json: { max_retries: 0, retry_delay_seconds: 60 },
    owner_user_id: currentUser?.id || '',
    reviewer_user_id: '',
    approval_group_id: '',
    risk_level: 'LOW',
    sla_hours: ''
  });

  // Reference data states
  const [workflows, setWorkflows] = useState<any[]>([]);
  const [agents, setAgents] = useState<any[]>([]);
  const [models, setModels] = useState<any[]>([]);
  const [tools, setTools] = useState<any[]>([]);
  const [dataSources, setDataSources] = useState<any[]>([]);
  const [users, setUsers] = useState<any[]>([]);
  const [approvalGroups, setApprovalGroups] = useState<any[]>([]);

  // Derived states
  const selectedWorkflow = workflows.find(w => w.id === formData.workflow_id);
  const selectedAgent = agents.find(a => a.id === formData.agent_id);
  
  const hasWriteTool = tools.some(t => formData.allowed_tools_json.includes(t.id) && (t.capability === 'WRITE' || t.capability === 'EXECUTE'));
  const isApprovalRequired = formData.risk_level === 'HIGH' || formData.risk_level === 'CRITICAL' || hasWriteTool;
  
  const approvalReasons = [];
  if (hasWriteTool) approvalReasons.push("Write-capable tool selected requires Governance Board approval");
  if (formData.risk_level === 'HIGH' || formData.risk_level === 'CRITICAL') approvalReasons.push(`Risk level is ${formData.risk_level}`);

  const [cronError, setCronError] = useState('');
  const [isDirty, setIsDirty] = useState(false);

  const fetchWithAuth = async (url: string) => {
    const token = localStorage.getItem('guardianiq_access_token');
    const res = await fetch(url, { headers: { 'Authorization': `Bearer ${token}` } });
    const json = await res.json();
    return json.data?.items || json.data || [];
  };

  useEffect(() => {
    // Basic unsaved changes warning
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (isDirty) {
        e.preventDefault();
        e.returnValue = '';
      }
    };
    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [isDirty]);

  useEffect(() => {
    // Load initial reference data
    fetchWithAuth('/api/registry/workflows?status=ACTIVE').then(setWorkflows).catch(() => {});
    fetchWithAuth('/api/registry/agents?status=ACTIVE').then(setAgents).catch(() => {});
    fetchWithAuth('/api/registry/tools').then(setTools).catch(() => {});
    fetchWithAuth('/api/registry/data-sources').then(setDataSources).catch(() => {});
    fetchWithAuth('/api/registry/users/lookup').then(setUsers).catch(() => {});
    fetchWithAuth('/api/v1/approval-groups').then(setApprovalGroups).catch(() => {});
  }, []);

  useEffect(() => {
    if (formData.agent_id) {
      // Typically models would be filtered by agent, assuming API supports it or we do client side
      fetchWithAuth(`/api/registry/models`).then(setModels).catch(() => {});
    }
  }, [formData.agent_id]);

  const handleChange = (field: string, value: any) => {
    setFormData((prev: any) => ({ ...prev, [field]: value }));
    setIsDirty(true);
  };

  const handleCronBlur = async () => {
    if (!formData.cron_expression) return;
    try {
      const token = localStorage.getItem('guardianiq_access_token');
      const res = await fetch('/api/v1/workflow-scheduler/validate-cron', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({ cron_expression: formData.cron_expression })
      });
      const json = await res.json();
      if (!json.success || !json.data.valid) {
        setCronError(json.error || 'Invalid cron expression');
      } else {
        setCronError('');
      }
    } catch (e) {
      setCronError('Could not validate cron');
    }
  };

  const canSaveDraft = formData.workflow_id && formData.schedule_name && formData.owner_user_id;

  const handleSaveDraft = async () => {
    try {
      const payload = {
        ...formData,
        approval_required: isApprovalRequired,
        schedule_status: 'DRAFT',
        agent_assignments: [{
          agent_id: formData.agent_id,
          model_id: formData.model_id,
          assignment_role: 'PRIMARY',
          execution_mode: formData.execution_mode,
          confidence_threshold: formData.confidence_threshold,
          allowed_tools_json: formData.allowed_tools_json,
          allowed_data_sources_json: formData.allowed_data_sources_json,
          blocked_operations_json: formData.blocked_operations_json
        }]
      };
      const res = await scheduleApi.create(payload);
      showToast('Draft saved successfully', 'success');
      setIsDirty(false);
      navigate(`/workflow-scheduler/${res.id}`);
    } catch (e: any) {
      showToast(e.message || 'Failed to save draft', 'error');
    }
  };

  const handleSubmit = async () => {
    try {
      const payload = {
        ...formData,
        approval_required: isApprovalRequired,
        schedule_status: 'PENDING_APPROVAL', // or whatever the workflow dictates
        agent_assignments: [{
          agent_id: formData.agent_id,
          model_id: formData.model_id,
          assignment_role: 'PRIMARY',
          execution_mode: formData.execution_mode,
          confidence_threshold: formData.confidence_threshold,
          allowed_tools_json: formData.allowed_tools_json,
          allowed_data_sources_json: formData.allowed_data_sources_json,
          blocked_operations_json: formData.blocked_operations_json
        }]
      };
      const res = await scheduleApi.create(payload);
      showToast('Schedule created successfully', 'success');
      setIsDirty(false);
      navigate(`/workflow-scheduler/${res.id}`);
    } catch (e: any) {
      // Map 422 errors logic would go here
      showToast(e.message || 'Failed to submit schedule', 'error');
    }
  };

  const executionModeOptions = ['READ_ONLY', 'RECOMMEND_ONLY', 'APPROVAL_REQUIRED', 'LIMITED_EXECUTION'];

  const renderStepContent = () => {
    switch (currentStep) {
      case 0:
        return (
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700">Schedule Name *</label>
              <input type="text" value={formData.schedule_name} onChange={e => handleChange('schedule_name', e.target.value)} className="mt-1 block w-full border-gray-300 rounded-md shadow-sm sm:text-sm" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Schedule Code</label>
              <input type="text" value={formData.schedule_code} onChange={e => handleChange('schedule_code', e.target.value)} className="mt-1 block w-full border-gray-300 rounded-md shadow-sm sm:text-sm" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Workflow *</label>
              <select value={formData.workflow_id} onChange={e => handleChange('workflow_id', e.target.value)} className="mt-1 block w-full border-gray-300 rounded-md shadow-sm sm:text-sm">
                <option value="">Select a workflow</option>
                {workflows.map(w => <option key={w.id} value={w.id}>{w.name || w.workflow_name}</option>)}
              </select>
            </div>
            {selectedWorkflow && (
              <div className="bg-gray-50 p-4 rounded-md text-sm text-gray-700 space-y-2">
                <p><strong>Name:</strong> {selectedWorkflow.name || selectedWorkflow.workflow_name}</p>
                <p><strong>Criticality:</strong> <span className="bg-indigo-100 text-indigo-800 px-2 py-0.5 rounded text-xs">{selectedWorkflow.criticality || 'Unknown'}</span></p>
                <p><strong>Owner:</strong> {selectedWorkflow.owner_name || 'System'}</p>
                <p><strong>Description:</strong> {selectedWorkflow.description}</p>
              </div>
            )}
          </div>
        );
      case 1:
        return (
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700">Agent</label>
              <select value={formData.agent_id} onChange={e => handleChange('agent_id', e.target.value)} className="mt-1 block w-full border-gray-300 rounded-md shadow-sm sm:text-sm">
                <option value="">Select an agent</option>
                {agents.map(a => <option key={a.id} value={a.id}>{a.name}</option>)}
              </select>
            </div>
            {selectedAgent && (
              <div className="bg-gray-50 p-4 rounded-md text-sm text-gray-700 space-y-1">
                <p><strong>Owner:</strong> {selectedAgent.owner_name}</p>
                <p><strong>Description:</strong> {selectedAgent.description}</p>
                <p><strong>Max Execution Mode:</strong> {selectedAgent.max_execution_mode}</p>
              </div>
            )}
            <div>
              <label className="block text-sm font-medium text-gray-700">Model</label>
              <select value={formData.model_id} onChange={e => handleChange('model_id', e.target.value)} className="mt-1 block w-full border-gray-300 rounded-md shadow-sm sm:text-sm">
                <option value="">Select a model</option>
                {models.map(m => <option key={m.id} value={m.id}>{m.name}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Execution Mode</label>
              <select value={formData.execution_mode} onChange={e => handleChange('execution_mode', e.target.value)} className="mt-1 block w-full border-gray-300 rounded-md shadow-sm sm:text-sm">
                {executionModeOptions.map(opt => {
                  // Simplified: we don't have the exact enum ordinals here, but typically you'd disable options > max
                  return <option key={opt} value={opt}>{opt}</option>;
                })}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Confidence Threshold (0-100)</label>
              <input type="number" min="0" max="100" value={formData.confidence_threshold} onChange={e => handleChange('confidence_threshold', parseInt(e.target.value))} className="mt-1 block w-full border-gray-300 rounded-md shadow-sm sm:text-sm" />
            </div>
          </div>
        );
      case 2:
        return (
          <div className="space-y-6">
            <BoundaryRuleEditor
              allowedTools={formData.allowed_tools_json}
              allowedDataSources={formData.allowed_data_sources_json}
              blockedOperations={formData.blocked_operations_json}
              onChange={handleChange}
              toolOptions={tools}
            />
            {hasWriteTool && (
              <ApprovalRequirementBanner approvalRequired={true} reasons={["Write-capable tool selected requires Governance Board approval"]} />
            )}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Max Records</label>
                <input type="number" value={formData.max_records} onChange={e => handleChange('max_records', parseInt(e.target.value))} className="mt-1 block w-full border-gray-300 rounded-md shadow-sm sm:text-sm" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Max Runtime (seconds)</label>
                <input type="number" value={formData.max_runtime_seconds} onChange={e => handleChange('max_runtime_seconds', parseInt(e.target.value))} className="mt-1 block w-full border-gray-300 rounded-md shadow-sm sm:text-sm" />
              </div>
            </div>
          </div>
        );
      case 3:
        return (
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700">Schedule Type</label>
              <select value={formData.schedule_type} onChange={e => handleChange('schedule_type', e.target.value)} className="mt-1 block w-full border-gray-300 rounded-md shadow-sm sm:text-sm">
                <option value="MANUAL">MANUAL</option>
                <option value="CRON">CRON</option>
                <option value="DAILY">DAILY</option>
                <option value="WEEKLY">WEEKLY</option>
                <option value="INTERVAL">INTERVAL</option>
              </select>
            </div>
            {['DAILY', 'WEEKLY', 'CRON'].includes(formData.schedule_type) && (
              <div onBlur={handleCronBlur}>
                <CronExpressionBuilder value={formData.cron_expression} onChange={v => handleChange('cron_expression', v)} timezone={formData.timezone} />
                {cronError && <p className="text-red-500 text-xs mt-1">{cronError}</p>}
              </div>
            )}
            <div>
              <label className="block text-sm font-medium text-gray-700">Timezone</label>
              <select value={formData.timezone} onChange={e => handleChange('timezone', e.target.value)} className="mt-1 block w-full border-gray-300 rounded-md shadow-sm sm:text-sm">
                <option value="UTC">UTC</option>
                <option value="Asia/Kolkata">Asia/Kolkata</option>
                <option value="America/New_York">America/New_York</option>
                <option value="Europe/London">Europe/London</option>
              </select>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Start At</label>
                <input type="datetime-local" value={formData.start_at} onChange={e => handleChange('start_at', e.target.value)} className="mt-1 block w-full border-gray-300 rounded-md shadow-sm sm:text-sm" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">End At</label>
                <input type="datetime-local" value={formData.end_at} onChange={e => handleChange('end_at', e.target.value)} className="mt-1 block w-full border-gray-300 rounded-md shadow-sm sm:text-sm" />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Concurrency Policy</label>
              <select value={formData.concurrency_policy} onChange={e => handleChange('concurrency_policy', e.target.value)} className="mt-1 block w-full border-gray-300 rounded-md shadow-sm sm:text-sm">
                <option value="SKIP_IF_RUNNING">SKIP_IF_RUNNING (recommended)</option>
                <option value="QUEUE">QUEUE</option>
                <option value="ALLOW_PARALLEL">ALLOW_PARALLEL</option>
              </select>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Max Retries</label>
                <input type="number" min="0" max="5" value={formData.retry_policy_json.max_retries} onChange={e => handleChange('retry_policy_json', { ...formData.retry_policy_json, max_retries: parseInt(e.target.value) })} className="mt-1 block w-full border-gray-300 rounded-md shadow-sm sm:text-sm" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Retry Delay (s)</label>
                <input type="number" min="60" max="3600" value={formData.retry_policy_json.retry_delay_seconds} onChange={e => handleChange('retry_policy_json', { ...formData.retry_policy_json, retry_delay_seconds: parseInt(e.target.value) })} className="mt-1 block w-full border-gray-300 rounded-md shadow-sm sm:text-sm" />
              </div>
            </div>
          </div>
        );
      case 4:
        return (
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700">Owner User *</label>
              <select value={formData.owner_user_id} onChange={e => handleChange('owner_user_id', e.target.value)} className="mt-1 block w-full border-gray-300 rounded-md shadow-sm sm:text-sm">
                <option value="">Select an owner</option>
                {users.map(u => <option key={u.id} value={u.id}>{u.full_name || u.email}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Reviewer User</label>
              <select value={formData.reviewer_user_id} onChange={e => handleChange('reviewer_user_id', e.target.value)} className="mt-1 block w-full border-gray-300 rounded-md shadow-sm sm:text-sm">
                <option value="">Select a reviewer</option>
                {users.map(u => <option key={u.id} value={u.id}>{u.full_name || u.email}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Approval Group {isApprovalRequired && <span className="text-red-500">*</span>}
              </label>
              <select value={formData.approval_group_id} onChange={e => handleChange('approval_group_id', e.target.value)} className="mt-1 block w-full border-gray-300 rounded-md shadow-sm sm:text-sm">
                <option value="">Select a group</option>
                {approvalGroups.map(g => <option key={g.id} value={g.id}>{g.name}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Risk Level</label>
              <div className="space-y-2">
                {['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'].map(r => (
                  <label key={r} className="flex items-center">
                    <input type="radio" name="risk_level" value={r} checked={formData.risk_level === r} onChange={e => handleChange('risk_level', e.target.value)} className="focus:ring-indigo-500 h-4 w-4 text-indigo-600 border-gray-300" />
                    <span className="ml-2 text-sm text-gray-700">{r}</span>
                  </label>
                ))}
              </div>
            </div>
            {(formData.risk_level === 'HIGH' || formData.risk_level === 'CRITICAL') && (
              <div>
                <label className="block text-sm font-medium text-gray-700">SLA Hours *</label>
                <input type="number" value={formData.sla_hours} onChange={e => handleChange('sla_hours', parseInt(e.target.value))} className="mt-1 block w-full border-gray-300 rounded-md shadow-sm sm:text-sm" />
              </div>
            )}
            <ApprovalRequirementBanner approvalRequired={isApprovalRequired} reasons={approvalReasons} />
          </div>
        );
      case 5:
        return (
          <div className="space-y-6">
            <h3 className="text-lg font-medium text-gray-900">Review & Submit</h3>
            <div className="grid grid-cols-2 gap-4 text-sm text-gray-700">
              <div className="p-4 bg-gray-50 rounded border border-gray-200">
                <h4 className="font-semibold mb-2">Workflow</h4>
                <p>{selectedWorkflow?.name || 'Not selected'}</p>
              </div>
              <div className="p-4 bg-gray-50 rounded border border-gray-200">
                <h4 className="font-semibold mb-2">Agent</h4>
                <p>{selectedAgent?.name || 'Not selected'}</p>
                <p className="text-xs mt-1">Mode: {formData.execution_mode}</p>
              </div>
              <div className="p-4 bg-gray-50 rounded border border-gray-200">
                <h4 className="font-semibold mb-2">Schedule</h4>
                <p>{formData.schedule_type} {formData.cron_expression}</p>
              </div>
              <div className="p-4 bg-gray-50 rounded border border-gray-200">
                <h4 className="font-semibold mb-2">Governance</h4>
                <p>Risk: {formData.risk_level}</p>
                <p>Approval Required: {isApprovalRequired ? 'Yes' : 'No'}</p>
              </div>
            </div>
            
            <div className="flex gap-4 pt-4 border-t border-gray-200">
              <button onClick={handleSaveDraft} disabled={!canSaveDraft} className="flex-1 px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:bg-gray-100">
                Save as Draft
              </button>
              <button onClick={handleSubmit} className="flex-1 px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700">
                Submit
              </button>
            </div>
          </div>
        );
      default: return null;
    }
  };

  return (
    <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
      <div className="flex justify-between items-center mb-6 px-4 sm:px-0">
        <h1 className="text-2xl font-bold text-gray-900">Create Workflow Schedule</h1>
        <button onClick={handleSaveDraft} disabled={!canSaveDraft} className="text-sm text-indigo-600 font-medium disabled:text-gray-400">
          Save Draft
        </button>
      </div>

      <div className="flex gap-6">
        <div className="flex-1 bg-white shadow sm:rounded-lg">
          <WizardShell
            steps={steps}
            currentStep={currentStep}
            onStepClick={setCurrentStep}
            mode="tabbed"
          >
            <div className="p-6">
              {renderStepContent()}
              
              <div className="mt-8 flex justify-between pt-5 border-t border-gray-200">
                <button
                  type="button"
                  onClick={() => setCurrentStep(prev => Math.max(0, prev - 1))}
                  disabled={currentStep === 0}
                  className="bg-white py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
                >
                  Back
                </button>
                {currentStep < steps.length - 1 && (
                  <button
                    type="button"
                    onClick={() => setCurrentStep(prev => Math.min(steps.length - 1, prev + 1))}
                    className="ml-3 inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700"
                  >
                    Next
                  </button>
                )}
              </div>
            </div>
          </WizardShell>
        </div>

        {/* Right Summary Panel */}
        <div className="hidden lg:block w-80">
          <div className="bg-white p-4 shadow rounded-lg sticky top-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Summary</h3>
            <dl className="space-y-4 text-sm text-gray-600">
              <div>
                <dt className="font-medium text-gray-900">Risk Level</dt>
                <dd>{formData.risk_level}</dd>
              </div>
              <div>
                <dt className="font-medium text-gray-900">Approval Required</dt>
                <dd className={isApprovalRequired ? 'text-amber-600 font-semibold' : ''}>
                  {isApprovalRequired ? 'Yes' : 'No'}
                </dd>
              </div>
              <div>
                <dt className="font-medium text-gray-900">Workflow</dt>
                <dd>{selectedWorkflow?.name || 'Not selected'}</dd>
              </div>
              <div>
                <dt className="font-medium text-gray-900">Agent</dt>
                <dd>{selectedAgent?.name || 'Not selected'}</dd>
              </div>
              <div>
                <dt className="font-medium text-gray-900">Execution Mode</dt>
                <dd>{formData.execution_mode}</dd>
              </div>
            </dl>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CreateScheduleWizard;

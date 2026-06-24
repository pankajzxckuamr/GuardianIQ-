import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import WizardShell from '../components/common/WizardShell';
import { useAuth } from '../hooks/useAuth';
import { useToast } from '../hooks/useToast';
import { scheduleApi } from '../api/phase2Client';
import { ApprovalRequirementBanner } from '../components/phase2/ApprovalRequirementBanner';
import { CronExpressionBuilder } from '../components/phase2/CronExpressionBuilder';
import { BoundaryRuleEditor } from '../components/phase2/BoundaryRuleEditor';
import { PageHeader } from '../components/common/PageHeader';
import { Button } from '../components/common/Button';
import { ArrowLeft } from 'lucide-react';
import { storage } from '../utils/storage';
import styles from './phase2Shared.module.css';

const getAgentLabel = (agent: any) => agent?.agent_name || agent?.name || agent?.agent_code || 'Unknown agent';
const getModelLabel = (model: any) => model?.model_name || model?.name || model?.model_code || 'Unknown model';

const steps = [
  { label: 'Select Workflow' },
  { label: 'Agent & Model' },
  { label: 'Boundaries' },
  { label: 'Schedule Configuration' },
  { label: 'Governance Controls' },
  { label: 'Review & Submit' },
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
    sla_hours: '',
  });

  const [workflows, setWorkflows] = useState<any[]>([]);
  const [agents, setAgents] = useState<any[]>([]);
  const [models, setModels] = useState<any[]>([]);
  const [tools, setTools] = useState<any[]>([]);
  const [, setDataSources] = useState<any[]>([]);
  const [users, setUsers] = useState<any[]>([]);
  const [approvalGroups, setApprovalGroups] = useState<any[]>([]);

  const selectedWorkflow = workflows.find(w => w.id === formData.workflow_id);
  const selectedAgent = agents.find(a => a.id === formData.agent_id);

  const hasWriteTool = tools.some(t => {
    const code = t.tool_code || t.id;
    const mode = t.access_mode || t.capability || '';
    return formData.allowed_tools_json.some((entry: string) => entry === code || entry === t.id)
      && ['WRITE', 'EXECUTE', 'ADMIN'].includes(mode);
  });
  const isApprovalRequired = formData.risk_level === 'HIGH' || formData.risk_level === 'CRITICAL' || hasWriteTool;

  const approvalReasons: string[] = [];
  if (hasWriteTool) approvalReasons.push('Write-capable tool selected requires Governance Board approval');
  if (formData.risk_level === 'HIGH' || formData.risk_level === 'CRITICAL') approvalReasons.push(`Risk level is ${formData.risk_level}`);

  const [cronError, setCronError] = useState('');
  const [isDirty, setIsDirty] = useState(false);

  const fetchWithAuth = async (url: string) => {
    const token = storage.get<string>('guardianiq_access_token');
    const res = await fetch(url, { headers: { 'Authorization': `Bearer ${token}` } });
    const json = await res.json();
    return json.data?.items || json.data || [];
  };

  useEffect(() => {
    document.title = 'Create Schedule — GuardianIQ';
  }, []);

  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (isDirty) { e.preventDefault(); e.returnValue = ''; }
    };
    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [isDirty]);

  useEffect(() => {
    fetchWithAuth('/api/registry/workflows?per_page=100').then(setWorkflows).catch(() => {});
    fetchWithAuth('/api/registry/agents?per_page=100').then(setAgents).catch(() => {});
    fetchWithAuth('/api/registry/models?per_page=100').then(setModels).catch(() => {});
    fetchWithAuth('/api/registry/tools?per_page=100').then(setTools).catch(() => {});
    fetchWithAuth('/api/registry/data-sources?per_page=100').then(setDataSources).catch(() => {});
    fetchWithAuth('/api/registry/users/lookup').then(setUsers).catch(() => {});
    fetchWithAuth('/api/v1/approval-groups').then(setApprovalGroups).catch(() => {});
  }, []);

  const handleChange = (field: string, value: any) => {
    setFormData((prev: any) => ({ ...prev, [field]: value }));
    setIsDirty(true);
  };

  const handleCronBlur = async () => {
    if (!formData.cron_expression) return;
    try {
      const token = storage.get<string>('guardianiq_access_token');
      const res = await fetch('/api/v1/workflow-scheduler/validate-cron', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({ cron_expression: formData.cron_expression }),
      });
      const json = await res.json();
      if (json.status !== 'success' || !json.data.valid) setCronError(json.message || 'Invalid cron expression');
      else setCronError('');
    } catch (e) {
      setCronError('Could not validate cron');
    }
  };

  const canSaveDraft = formData.workflow_id && formData.schedule_name && formData.owner_user_id;

  const buildPayload = (status: string) => {
    const boundary_rules = {
      max_records: formData.max_records || 100,
      allow_write_tools: hasWriteTool,
      requires_human_approval_for_high_risk: formData.risk_level === 'HIGH' || formData.risk_level === 'CRITICAL'
    };

    const payload: any = {
      workflow_id: formData.workflow_id || null,
      schedule_code: formData.schedule_code || null,
      schedule_name: formData.schedule_name || null,
      schedule_type: formData.schedule_type,
      timezone: formData.timezone || "Asia/Kolkata",
      concurrency_policy: formData.concurrency_policy || "SKIP_IF_RUNNING",
      max_runtime_seconds: formData.max_runtime_seconds || 1800,
      retry_policy: formData.retry_policy_json || { max_retries: 0, retry_delay_seconds: 60 },
      owner_user_id: formData.owner_user_id || null,
      approval_required: isApprovalRequired,
      schedule_status: status,
    };

    if (formData.cron_expression && formData.cron_expression.trim() !== '') {
      payload.cron_expression = formData.cron_expression;
    } else {
      payload.cron_expression = null;
    }

    if (formData.start_at && formData.start_at.trim() !== '') {
      payload.start_at = new Date(formData.start_at).toISOString();
    } else {
      payload.start_at = null;
    }

    if (formData.end_at && formData.end_at.trim() !== '') {
      payload.end_at = new Date(formData.end_at).toISOString();
    } else {
      payload.end_at = null;
    }

    if (formData.owner_department_id && formData.owner_department_id.trim() !== '') {
      payload.owner_department_id = formData.owner_department_id;
    } else {
      payload.owner_department_id = null;
    }

    if (formData.approval_group_id && formData.approval_group_id.trim() !== '') {
      payload.approval_group_id = formData.approval_group_id;
    } else {
      payload.approval_group_id = null;
    }

    if (formData.risk_level) {
      payload.risk_level = formData.risk_level;
    }

    if (formData.agent_id && formData.agent_id.trim() !== '') {
      payload.agent_assignments = [{
        agent_id: formData.agent_id,
        model_id: (formData.model_id && formData.model_id.trim() !== '') ? formData.model_id : null,
        assignment_role: 'PRIMARY',
        execution_mode: formData.execution_mode || 'RECOMMEND_ONLY',
        confidence_threshold: formData.confidence_threshold !== undefined ? formData.confidence_threshold : null,
        allowed_tools: formData.allowed_tools_json || [],
        allowed_data_sources: formData.allowed_data_sources_json || [],
        blocked_operations: formData.blocked_operations_json || [],
        boundary_rules: boundary_rules
      }];
    } else {
      payload.agent_assignments = [];
    }

    return payload;
  };

  const handleSaveDraft = async () => {
    try {
      const res: any = await scheduleApi.create(buildPayload('DRAFT'));
      showToast('Draft saved successfully', 'success');
      setIsDirty(false);
      navigate(`/workflow-scheduler/${res.id}`);
    } catch (e: any) {
      showToast(e.message || 'Failed to save draft', 'error');
    }
  };

  const handleSubmit = async () => {
    try {
      const res: any = await scheduleApi.create(buildPayload('PENDING_APPROVAL'));
      showToast('Schedule created successfully', 'success');
      setIsDirty(false);
      navigate(`/workflow-scheduler/${res.id}`);
    } catch (e: any) {
      showToast(e.message || 'Failed to submit schedule', 'error');
    }
  };

  const executionModeOptions = ['READ_ONLY', 'RECOMMEND_ONLY', 'APPROVAL_REQUIRED', 'LIMITED_EXECUTION'];

  const renderStepContent = () => {
    switch (currentStep) {
      case 0:
        return (
          <div className={styles.fieldStack}>
            <div>
              <label className={styles.fieldLabel}>Schedule Name <span className={styles.req}>*</span></label>
              <input type="text" className={styles.formControl} value={formData.schedule_name} onChange={e => handleChange('schedule_name', e.target.value)} />
            </div>
            <div>
              <label className={styles.fieldLabel}>Schedule Code</label>
              <input type="text" className={styles.formControl} value={formData.schedule_code} onChange={e => handleChange('schedule_code', e.target.value)} />
            </div>
            <div>
              <label className={styles.fieldLabel}>Workflow <span className={styles.req}>*</span></label>
              <select className={styles.formControl} value={formData.workflow_id} onChange={e => handleChange('workflow_id', e.target.value)}>
                <option value="">Select a workflow</option>
                {workflows.map(w => <option key={w.id} value={w.id}>{w.name || w.workflow_name}</option>)}
              </select>
            </div>
            {selectedWorkflow && (
              <div className={styles.section}>
                <p className={styles.infoLine}><strong>Name:</strong> {selectedWorkflow.name || selectedWorkflow.workflow_name}</p>
                <p className={styles.infoLine}><strong>Criticality:</strong> <span className={styles.tagChip}>{selectedWorkflow.criticality || 'Unknown'}</span></p>
                <p className={styles.infoLine}><strong>Owner:</strong> {selectedWorkflow.owner_name || 'System'}</p>
                <p className={styles.infoLine}><strong>Description:</strong> {selectedWorkflow.description}</p>
              </div>
            )}
          </div>
        );
      case 1:
        return (
          <div className={styles.fieldStack}>
            <div>
              <label className={styles.fieldLabel}>Agent</label>
              <select className={styles.formControl} value={formData.agent_id} onChange={e => handleChange('agent_id', e.target.value)}>
                <option value="">Select an agent</option>
                {agents.map(a => <option key={a.id} value={a.id}>{getAgentLabel(a)}</option>)}
              </select>
            </div>
            {selectedAgent && (
              <div className={styles.section}>
                <p className={styles.infoLine}><strong>Owner:</strong> {selectedAgent.owner_name}</p>
                <p className={styles.infoLine}><strong>Description:</strong> {selectedAgent.description}</p>
                <p className={styles.infoLine}><strong>Max Execution Mode:</strong> {selectedAgent.execution_mode || selectedAgent.max_execution_mode}</p>
              </div>
            )}
            <div>
              <label className={styles.fieldLabel}>Model</label>
              <select className={styles.formControl} value={formData.model_id} onChange={e => handleChange('model_id', e.target.value)}>
                <option value="">Select a model</option>
                {models.map(m => <option key={m.id} value={m.id}>{getModelLabel(m)}</option>)}
              </select>
            </div>
            <div>
              <label className={styles.fieldLabel}>Execution Mode</label>
              <select className={styles.formControl} value={formData.execution_mode} onChange={e => handleChange('execution_mode', e.target.value)}>
                {executionModeOptions.map(opt => <option key={opt} value={opt}>{opt}</option>)}
              </select>
            </div>
            <div>
              <label className={styles.fieldLabel}>Confidence Threshold (0-100)</label>
              <input type="number" min="0" max="100" className={styles.formControl} value={formData.confidence_threshold} onChange={e => handleChange('confidence_threshold', parseInt(e.target.value))} />
            </div>
          </div>
        );
      case 2:
        return (
          <div className={styles.fieldStack}>
            <BoundaryRuleEditor
              allowedTools={formData.allowed_tools_json}
              allowedDataSources={formData.allowed_data_sources_json}
              blockedOperations={formData.blocked_operations_json}
              onChange={handleChange}
              toolOptions={tools}
            />
            {hasWriteTool && (
              <ApprovalRequirementBanner approvalRequired={true} reasons={['Write-capable tool selected requires Governance Board approval']} />
            )}
            <div className={styles.formGrid2}>
              <div>
                <label className={styles.fieldLabel}>Max Records</label>
                <input type="number" className={styles.formControl} value={formData.max_records} onChange={e => handleChange('max_records', parseInt(e.target.value))} />
              </div>
              <div>
                <label className={styles.fieldLabel}>Max Runtime (seconds)</label>
                <input type="number" className={styles.formControl} value={formData.max_runtime_seconds} onChange={e => handleChange('max_runtime_seconds', parseInt(e.target.value))} />
              </div>
            </div>
          </div>
        );
      case 3:
        return (
          <div className={styles.fieldStack}>
            <div>
              <label className={styles.fieldLabel}>Schedule Type</label>
              <select className={styles.formControl} value={formData.schedule_type} onChange={e => handleChange('schedule_type', e.target.value)}>
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
                {cronError && <p className={styles.failText} style={{ marginTop: 4 }}>{cronError}</p>}
              </div>
            )}
            <div>
              <label className={styles.fieldLabel}>Timezone</label>
              <select className={styles.formControl} value={formData.timezone} onChange={e => handleChange('timezone', e.target.value)}>
                <option value="UTC">UTC</option>
                <option value="Asia/Kolkata">Asia/Kolkata</option>
                <option value="America/New_York">America/New_York</option>
                <option value="Europe/London">Europe/London</option>
              </select>
            </div>
            <div className={styles.formGrid2}>
              <div>
                <label className={styles.fieldLabel}>Start At</label>
                <input type="datetime-local" className={styles.formControl} value={formData.start_at} onChange={e => handleChange('start_at', e.target.value)} />
              </div>
              <div>
                <label className={styles.fieldLabel}>End At</label>
                <input type="datetime-local" className={styles.formControl} value={formData.end_at} onChange={e => handleChange('end_at', e.target.value)} />
              </div>
            </div>
            <div>
              <label className={styles.fieldLabel}>Concurrency Policy</label>
              <select className={styles.formControl} value={formData.concurrency_policy} onChange={e => handleChange('concurrency_policy', e.target.value)}>
                <option value="SKIP_IF_RUNNING">SKIP_IF_RUNNING (recommended)</option>
                <option value="QUEUE">QUEUE</option>
                <option value="ALLOW_PARALLEL">ALLOW_PARALLEL</option>
              </select>
            </div>
            <div className={styles.formGrid2}>
              <div>
                <label className={styles.fieldLabel}>Max Retries</label>
                <input type="number" min="0" max="5" className={styles.formControl} value={formData.retry_policy_json.max_retries} onChange={e => handleChange('retry_policy_json', { ...formData.retry_policy_json, max_retries: parseInt(e.target.value) })} />
              </div>
              <div>
                <label className={styles.fieldLabel}>Retry Delay (s)</label>
                <input type="number" min="60" max="3600" className={styles.formControl} value={formData.retry_policy_json.retry_delay_seconds} onChange={e => handleChange('retry_policy_json', { ...formData.retry_policy_json, retry_delay_seconds: parseInt(e.target.value) })} />
              </div>
            </div>
          </div>
        );
      case 4:
        return (
          <div className={styles.fieldStack}>
            <div>
              <label className={styles.fieldLabel}>Owner User <span className={styles.req}>*</span></label>
              <select className={styles.formControl} value={formData.owner_user_id} onChange={e => handleChange('owner_user_id', e.target.value)}>
                <option value="">Select an owner</option>
                {users.map(u => <option key={u.id} value={u.id}>{u.full_name || u.email}</option>)}
              </select>
            </div>
            <div>
              <label className={styles.fieldLabel}>Reviewer User</label>
              <select className={styles.formControl} value={formData.reviewer_user_id} onChange={e => handleChange('reviewer_user_id', e.target.value)}>
                <option value="">Select a reviewer</option>
                {users.map(u => <option key={u.id} value={u.id}>{u.full_name || u.email}</option>)}
              </select>
            </div>
            <div>
              <label className={styles.fieldLabel}>Approval Group {isApprovalRequired && <span className={styles.req}>*</span>}</label>
              <select className={styles.formControl} value={formData.approval_group_id} onChange={e => handleChange('approval_group_id', e.target.value)}>
                <option value="">Select a group</option>
                {approvalGroups.map(g => <option key={g.id} value={g.id}>{g.name}</option>)}
              </select>
            </div>
            <div>
              <label className={styles.fieldLabel}>Risk Level</label>
              <div className={styles.radioGroup}>
                {['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'].map(r => (
                  <label key={r} className={styles.radioOption}>
                    <input type="radio" name="risk_level" value={r} checked={formData.risk_level === r} onChange={e => handleChange('risk_level', e.target.value)} />
                    {r}
                  </label>
                ))}
              </div>
            </div>
            {(formData.risk_level === 'HIGH' || formData.risk_level === 'CRITICAL') && (
              <div>
                <label className={styles.fieldLabel}>SLA Hours <span className={styles.req}>*</span></label>
                <input type="number" className={styles.formControl} value={formData.sla_hours} onChange={e => handleChange('sla_hours', parseInt(e.target.value))} />
              </div>
            )}
            <ApprovalRequirementBanner approvalRequired={isApprovalRequired} reasons={approvalReasons} />
          </div>
        );
      case 5:
        return (
          <div className={styles.fieldStack}>
            <h3 className={styles.sectionHeading}>Review &amp; Submit</h3>
            <div className={styles.reviewGrid}>
              <div className={styles.section}>
                <h4 className={styles.subHeading}>Workflow</h4>
                <p className={styles.infoLine}>{selectedWorkflow?.name || selectedWorkflow?.workflow_name || 'Not selected'}</p>
              </div>
              <div className={styles.section}>
                <h4 className={styles.subHeading}>Agent</h4>
                <p className={styles.infoLine}>{selectedAgent ? getAgentLabel(selectedAgent) : 'Not selected'}</p>
                <p className={styles.subText}>Mode: {formData.execution_mode}</p>
              </div>
              <div className={styles.section}>
                <h4 className={styles.subHeading}>Schedule</h4>
                <p className={styles.infoLine}>{formData.schedule_type} {formData.cron_expression}</p>
              </div>
              <div className={styles.section}>
                <h4 className={styles.subHeading}>Governance</h4>
                <p className={styles.infoLine}>Risk: {formData.risk_level}</p>
                <p className={styles.infoLine}>Approval Required: {isApprovalRequired ? 'Yes' : 'No'}</p>
              </div>
            </div>
            <div className={styles.navRow} style={{ marginTop: 0 }}>
              <Button variant="secondary" onClick={handleSaveDraft} disabled={!canSaveDraft}>Save as Draft</Button>
              <Button variant="primary" onClick={handleSubmit}>Submit</Button>
            </div>
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div className={styles.page}>
      <button className={styles.clearBtn} onClick={() => navigate('/workflow-scheduler')} style={{ alignSelf: 'flex-start' }}>
        <ArrowLeft size={14} /> Back to Scheduler
      </button>
      <PageHeader
        title="Create Workflow Schedule"
        description="Configure a governed, automated execution schedule"
        actions={
          <Button variant="secondary" size="sm" onClick={handleSaveDraft} disabled={!canSaveDraft}>Save Draft</Button>
        }
      />

      <div className={styles.wizardLayout}>
        <div className={styles.wizardMain}>
          <WizardShell steps={steps} currentStep={currentStep} onStepClick={setCurrentStep} mode="tabbed">
            {renderStepContent()}
            <div className={styles.navRow}>
              <Button variant="secondary" onClick={() => setCurrentStep(prev => Math.max(0, prev - 1))} disabled={currentStep === 0}>
                Back
              </Button>
              {currentStep < steps.length - 1 && (
                <Button variant="primary" onClick={() => setCurrentStep(prev => Math.min(steps.length - 1, prev + 1))}>
                  Next
                </Button>
              )}
            </div>
          </WizardShell>
        </div>

        <div className={styles.wizardSide}>
          <div className={styles.wizardSideCard}>
            <h3 className={styles.subHeading}>Summary</h3>
            <div className={styles.metaItem}><span className={styles.metaLabel}>Risk Level</span><span className={styles.metaValue}>{formData.risk_level}</span></div>
            <div className={styles.metaItem}>
              <span className={styles.metaLabel}>Approval Required</span>
              <span className={styles.metaValue} style={isApprovalRequired ? { color: 'var(--color-warning)' } : undefined}>{isApprovalRequired ? 'Yes' : 'No'}</span>
            </div>
            <div className={styles.metaItem}><span className={styles.metaLabel}>Workflow</span><span className={styles.metaValue}>{selectedWorkflow?.name || selectedWorkflow?.workflow_name || 'Not selected'}</span></div>
            <div className={styles.metaItem}><span className={styles.metaLabel}>Agent</span><span className={styles.metaValue}>{selectedAgent ? getAgentLabel(selectedAgent) : 'Not selected'}</span></div>
            <div className={styles.metaItem}><span className={styles.metaLabel}>Execution Mode</span><span className={styles.metaValue}>{formData.execution_mode}</span></div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CreateScheduleWizard;

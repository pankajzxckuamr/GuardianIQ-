import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import WizardShell from '../components/common/WizardShell';
import { useAuth } from '../hooks/useAuth';
import { useToast } from '../hooks/useToast';
import { scheduleApi } from '../api/phase2Client';
import { ApprovalRequirementBanner } from '../components/phase2/ApprovalRequirementBanner';
import { CronExpressionBuilder } from '../components/phase2/CronExpressionBuilder';
import { BoundaryRuleEditor } from '../components/phase2/BoundaryRuleEditor';
import { PageHeader } from '../components/common/PageHeader';
import { Button } from '../components/common/Button';
import { ScreenGuide } from '../components/common/ScreenGuide';
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
  const { id } = useParams<{ id: string }>();

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
    owner_user_id: '',
    reviewer_user_id: '',
    approval_group_id: '',
    risk_level: 'LOW',
    sla_hours: '',
    notification_recipients_json: [],
  });

  const [workflows, setWorkflows] = useState<any[]>([]);
  const [agents, setAgents] = useState<any[]>([]);
  const [models, setModels] = useState<any[]>([]);
  const [tools, setTools] = useState<any[]>([]);
  const [dataSources, setDataSources] = useState<any[]>([]);
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
  const [backendErrors, setBackendErrors] = useState<any>({});
  const [isDirty, setIsDirty] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const fetchWithAuth = async (url: string) => {
    const token = storage.get<string>('guardianiq_access_token');
    const res = await fetch(url, { headers: { 'Authorization': `Bearer ${token}` } });
    const json = await res.json();
    return json.data?.items || json.data || [];
  };

  useEffect(() => {
    document.title = id ? 'Edit Schedule — GuardianIQ' : 'Create Schedule — GuardianIQ';
  }, [id]);

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

    if (id) {
      scheduleApi.getById(id)
        .then((res: any) => {
          const sched = res.data || res;
          if (sched.schedule_status !== 'DRAFT') {
            showToast('Only DRAFT schedules can be edited.', 'error');
            navigate(`/workflow-scheduler/${id}`);
            return;
          }
          const aa = sched.agent_assignments?.[0] || {};
          setFormData({
            workflow_id: sched.workflow_id || '',
            schedule_name: sched.schedule_name || '',
            schedule_code: sched.schedule_code || '',
            agent_id: aa.agent_id || '',
            model_id: aa.model_id || '',
            execution_mode: aa.execution_mode || 'READ_ONLY',
            confidence_threshold: aa.confidence_threshold || 80,
            allowed_tools_json: aa.allowed_tools_json || [],
            allowed_data_sources_json: aa.allowed_data_sources_json || [],
            blocked_operations_json: aa.blocked_operations_json || [],
            max_records: sched.metadata_json?.max_records || 100,
            max_runtime_seconds: sched.max_runtime_seconds || 3600,
            schedule_type: sched.schedule_type || 'MANUAL',
            cron_expression: sched.cron_expression || '',
            timezone: sched.timezone || 'UTC',
            start_at: sched.start_at || '',
            end_at: sched.end_at || '',
            concurrency_policy: sched.concurrency_policy || 'SKIP_IF_RUNNING',
            retry_policy_json: sched.retry_policy_json || { max_retries: 0, retry_delay_seconds: 60 },
            owner_user_id: sched.owner_user_id || '',
            reviewer_user_id: sched.metadata_json?.reviewer_user_id || '',
            approval_group_id: sched.approval_group_id || '',
            risk_level: sched.risk_level || 'LOW',
            sla_hours: sched.metadata_json?.sla_hours || '',
            notification_recipients_json: sched.metadata_json?.notification_recipients_json || [],
          });
        })
        .catch(() => showToast('Failed to load schedule for editing', 'error'));
    }
  }, [id]);

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

  const validateStep = (stepIndex: number): boolean => {
    if (stepIndex === 0) {
      const newErrors: any = {};
      let isValid = true;
      if (!formData.workflow_id) {
        showToast('Workflow is required.', 'error');
        isValid = false;
      }
      if (!formData.schedule_name) {
        newErrors.schedule_name = 'Schedule Name is required';
        isValid = false;
      }
      if (!formData.schedule_code) {
        newErrors.schedule_code = 'Schedule Code is required';
        isValid = false;
      } else if (!/^[A-Z0-9_]+$/.test(formData.schedule_code)) {
        newErrors.schedule_code = 'Code must contain only uppercase letters, numbers, and underscores';
        isValid = false;
      }
      if (selectedWorkflow && selectedWorkflow.status !== 'ACTIVE') {
        showToast('Selected workflow must be ACTIVE.', 'error');
        isValid = false;
      }
      
      setBackendErrors(newErrors);
      return isValid;
    }
    if (stepIndex === 1) {
      const newErrors: any = {};
      let isValid = true;
      if (!formData.agent_id) {
        newErrors.agent_id = 'Agent selection is required.';
        isValid = false;
      } else if (selectedAgent && selectedAgent.status && selectedAgent.status !== 'ACTIVE') {
        newErrors.agent_id = 'Selected agent must be ACTIVE.';
        isValid = false;
      }

      const selectedModel = models.find(m => m.id === formData.model_id);
      if (selectedModel && selectedModel.status && selectedModel.status !== 'ACTIVE') {
        newErrors.model_id = 'Selected model must be ACTIVE.';
        isValid = false;
      }

      const modes = ['READ_ONLY', 'RECOMMEND_ONLY', 'APPROVAL_REQUIRED', 'LIMITED_EXECUTION'];
      const maxMode = selectedAgent?.max_execution_mode || selectedAgent?.execution_mode || 'READ_ONLY';
      if (modes.indexOf(formData.execution_mode) > modes.indexOf(maxMode)) {
        newErrors.execution_mode = `Selected execution mode exceeds this agent's permitted boundary (${maxMode}).`;
        isValid = false;
      }
      setBackendErrors(newErrors);
      return isValid;
    }
    if (stepIndex === 2) {
      const newErrors: any = {};
      let isValid = true;
      if (formData.allowed_tools_json.length === 0) {
        newErrors.allowed_tools_json = 'At least one tool must be allowed.';
        isValid = false;
      }
      if (formData.allowed_data_sources_json.length === 0) {
        newErrors.allowed_data_sources_json = 'At least one data source must be allowed.';
        isValid = false;
      }
      const overlap = formData.allowed_tools_json.some((t: string) => formData.blocked_operations_json.includes(t));
      if (overlap) {
        newErrors.blocked_operations_json = 'A tool cannot be both allowed and blocked.';
        isValid = false;
      }
      setBackendErrors(newErrors);
      return isValid;
    }
    if (stepIndex === 3) {
      const newErrors: any = {};
      let isValid = true;
      const needsCron = ['DAILY', 'WEEKLY', 'CRON'].includes(formData.schedule_type);
      if (needsCron) {
        if (!formData.cron_expression) {
          newErrors.cron_expression = 'Cron expression is required for this schedule type.';
          isValid = false;
        } else if (cronError) {
          newErrors.cron_expression = 'Please fix the cron expression before proceeding.';
          isValid = false;
        }
      }
      
      if (formData.start_at) {
        const startDate = new Date(formData.start_at);
        if (startDate < new Date()) {
          newErrors.start_at = 'Start date cannot be in the past.';
          isValid = false;
        }
      }

      setBackendErrors(newErrors);
      return isValid;
    }
    if (stepIndex === 4) {
      const newErrors: any = {};
      let isValid = true;
      if (!formData.owner_user_id) {
        newErrors.owner_user_id = 'Owner User is required.';
        isValid = false;
      }
      if (isApprovalRequired && !formData.approval_group_id) {
        newErrors.approval_group_id = 'Approval Group is required due to risk level or write-capable tools.';
        isValid = false;
      }
      if ((formData.risk_level === 'HIGH' || formData.risk_level === 'CRITICAL') && (!formData.sla_hours || formData.sla_hours <= 0)) {
        newErrors.sla_hours = 'SLA Hours is required and must be greater than 0 for HIGH/CRITICAL risk levels.';
        isValid = false;
      }
      setBackendErrors(newErrors);
      return isValid;
    }
    
    setBackendErrors({});
    return true;
  };

  const handleNextStep = async () => {
    if (validateStep(currentStep)) {
      if (currentStep === 0) {
        setIsSubmitting(true);
        try {
          const res: any = await scheduleApi.validateUniqueness({
            schedule_name: formData.schedule_name,
            schedule_code: formData.schedule_code || undefined
          });
          if (!res.valid) {
            setBackendErrors(res.errors);
            const errors = Object.values(res.errors).join(", ");
            showToast(errors, 'error');
            setIsSubmitting(false);
            return;
          }
          setBackendErrors({});
        } catch (e: any) {
          showToast('Failed to validate schedule name/code uniqueness', 'error');
          setIsSubmitting(false);
          return;
        }
        setIsSubmitting(false);
      }
      setCurrentStep(prev => Math.min(steps.length - 1, prev + 1));
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
      metadata_json: {
        notification_recipients: formData.notification_recipients_json || []
      }
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
    setIsSubmitting(true);
    try {
      const payload = buildPayload('DRAFT');
      let res: any;
      if (id) {
        res = await scheduleApi.update(id, payload);
      } else {
        res = await scheduleApi.create(payload);
      }
      showToast('Draft saved successfully', 'success');
      setIsDirty(false);
      navigate(`/workflow-scheduler/${res.id || id}`);
    } catch (e: any) {
      showToast(e.message || 'Failed to save draft', 'error');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSubmit = async () => {
    setBackendErrors({});
    setIsSubmitting(true);
    try {
      const payload = buildPayload(isApprovalRequired ? 'PENDING_APPROVAL' : 'ACTIVE');
      let res: any;
      if (id) {
        res = await scheduleApi.update(id, payload);
      } else {
        res = await scheduleApi.create(payload);
      }
      showToast(id ? 'Schedule updated successfully' : 'Schedule created successfully', 'success');
      setIsDirty(false);
      navigate(`/workflow-scheduler/${res.id || id}`);
    } catch (e: any) {
      if (e.errors) {
        setBackendErrors(e.errors);
        showToast('Please fix the errors below.', 'error');
      } else {
        showToast(e.message || 'Failed to submit schedule', 'error');
      }
    } finally {
      setIsSubmitting(false);
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
              <input type="text" className={`${styles.formControl} ${backendErrors.schedule_name ? styles.errorControl : ''}`} value={formData.schedule_name} onChange={e => handleChange('schedule_name', e.target.value)} />
              {backendErrors.schedule_name && <span className={styles.errorText}>{backendErrors.schedule_name}</span>}
            </div>
            <div>
              <label className={styles.fieldLabel}>Schedule Code <span className={styles.req}>*</span></label>
              <input type="text" className={`${styles.formControl} ${backendErrors.schedule_code ? styles.errorControl : ''}`} value={formData.schedule_code} onChange={e => handleChange('schedule_code', e.target.value)} />
              {backendErrors.schedule_code && <span className={styles.errorText}>{backendErrors.schedule_code}</span>}
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
              <label className={styles.fieldLabel}>Agent <span className={styles.req}>*</span></label>
              <select className={`${styles.formControl} ${backendErrors.agent_id ? styles.errorControl : ''}`} value={formData.agent_id} onChange={e => handleChange('agent_id', e.target.value)}>
                <option value="">Select an agent</option>
                {agents.map(a => <option key={a.id} value={a.id}>{getAgentLabel(a)}</option>)}
              </select>
              {backendErrors.agent_id && <span className={styles.errorText}>{backendErrors.agent_id}</span>}
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
              <select className={`${styles.formControl} ${backendErrors.execution_mode ? styles.errorControl : ''}`} value={formData.execution_mode} onChange={e => handleChange('execution_mode', e.target.value)}>
                {executionModeOptions.map(opt => <option key={opt} value={opt}>{opt}</option>)}
              </select>
              {backendErrors.execution_mode && <span className={styles.errorText}>{backendErrors.execution_mode}</span>}
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
            {backendErrors.allowed_tools_json && <div className={styles.failText} style={{ marginBottom: 8, padding: 8, background: 'rgba(239, 68, 68, 0.1)', borderRadius: 4 }}>{backendErrors.allowed_tools_json}</div>}
            {backendErrors.allowed_data_sources_json && <div className={styles.failText} style={{ marginBottom: 8, padding: 8, background: 'rgba(239, 68, 68, 0.1)', borderRadius: 4 }}>{backendErrors.allowed_data_sources_json}</div>}
            {backendErrors.blocked_operations_json && <div className={styles.failText} style={{ marginBottom: 8, padding: 8, background: 'rgba(239, 68, 68, 0.1)', borderRadius: 4 }}>{backendErrors.blocked_operations_json}</div>}
            <BoundaryRuleEditor
              allowedTools={formData.allowed_tools_json}
              allowedDataSources={formData.allowed_data_sources_json}
              blockedOperations={formData.blocked_operations_json}
              onChange={handleChange}
              toolOptions={tools}
              dataSourceOptions={dataSources}
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
              <div onBlur={handleCronBlur} className={`${backendErrors.cron_expression ? styles.errorControl : ''}`} style={backendErrors.cron_expression ? { border: '1px solid var(--color-danger)', borderRadius: 6, padding: 8 } : {}}>
                <CronExpressionBuilder value={formData.cron_expression} onChange={v => handleChange('cron_expression', v)} timezone={formData.timezone} />
                {backendErrors.cron_expression && <span className={styles.errorText} style={{ marginTop: 4 }}>{backendErrors.cron_expression}</span>}
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
                <input type="datetime-local" className={`${styles.formControl} ${backendErrors.start_at ? styles.errorControl : ''}`} value={formData.start_at} onChange={e => handleChange('start_at', e.target.value)} />
                {backendErrors.start_at && <span className={styles.errorText}>{backendErrors.start_at}</span>}
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
              <select className={`${styles.formControl} ${backendErrors.owner_user_id ? styles.errorControl : ''}`} value={formData.owner_user_id} onChange={e => handleChange('owner_user_id', e.target.value)}>
                <option value="">Select an owner</option>
                {users.map(u => <option key={u.id} value={u.id}>{u.full_name || u.email}</option>)}
              </select>
              {backendErrors.owner_user_id && <span className={styles.errorText}>{backendErrors.owner_user_id}</span>}
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
              <select className={`${styles.formControl} ${backendErrors.approval_group_id ? styles.errorControl : ''}`} value={formData.approval_group_id} onChange={e => handleChange('approval_group_id', e.target.value)}>
                <option value="">Select a group</option>
                {approvalGroups.map(g => <option key={g.id} value={g.id}>{g.name}</option>)}
              </select>
              {backendErrors.approval_group_id && <span className={styles.errorText}>{backendErrors.approval_group_id}</span>}
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
                <input type="number" className={`${styles.formControl} ${backendErrors.sla_hours ? styles.errorControl : ''}`} value={formData.sla_hours} onChange={e => handleChange('sla_hours', parseInt(e.target.value))} />
                {backendErrors.sla_hours && <span className={styles.errorText}>{backendErrors.sla_hours}</span>}
              </div>
            )}
            <div>
              <label className={styles.fieldLabel}>Notification Recipients</label>
              <select multiple className={`${styles.formControl} ${styles.multiSelect}`} value={formData.notification_recipients_json} onChange={e => {
                const next = Array.from(e.target.selectedOptions, option => option.value);
                handleChange('notification_recipients_json', next);
              }}>
                {users.map(u => <option key={u.id} value={u.id}>{u.full_name || u.email}</option>)}
              </select>
              <p className={styles.subText}>Hold Cmd/Ctrl (or Shift) to select multiple. Owner and approvers are notified automatically.</p>
            </div>
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
            
            {Object.keys(backendErrors).length > 0 && (
              <div className={styles.failText} style={{ marginTop: '16px', padding: '12px', background: 'rgba(239, 68, 68, 0.1)', borderRadius: '4px' }}>
                <h4 style={{ margin: '0 0 8px 0', fontSize: '13px' }}>Validation Errors</h4>
                <ul style={{ margin: 0, paddingLeft: '20px', fontSize: '13px' }}>
                  {Object.entries(backendErrors).map(([field, err]: any) => (
                    <li key={field}><strong>{field}:</strong> {err}</li>
                  ))}
                </ul>
              </div>
            )}

            <div className={styles.navRow} style={{ marginTop: '20px' }}>
              <Button variant="secondary" onClick={handleSaveDraft} disabled={!canSaveDraft || isSubmitting}>
                {isSubmitting ? 'Saving...' : 'Save as Draft'}
              </Button>
              <Button variant="primary" onClick={handleSubmit} disabled={isSubmitting}>
                {isSubmitting ? 'Submitting...' : (isApprovalRequired ? 'Submit for Approval' : 'Create Schedule')}
              </Button>
            </div>
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div className={styles.page}>
      <button className={styles.clearBtn} onClick={() => window.history.state && window.history.state.idx > 0 ? navigate(-1) : navigate('/workflow-scheduler')} style={{ alignSelf: 'flex-start' }}>
        <ArrowLeft size={14} /> Back
      </button>
      <ScreenGuide
        id="create-schedule-wizard-guide"
        title="Create Schedule Wizard"
        description="Follow this 6-step process to safely configure and deploy a governed automation schedule."
      />
      <PageHeader
        title="Create Workflow Schedule"
        description="Configure a governed, automated execution schedule"
        actions={
          <Button variant="secondary" size="sm" onClick={handleSaveDraft} disabled={!canSaveDraft}>Save Draft</Button>
        }
      />

      <div className={styles.wizardLayout}>
        <div className={styles.wizardMain}>
          <WizardShell steps={steps} currentStep={currentStep} onStepClick={(stepIndex) => {
            if (stepIndex < currentStep) {
              setCurrentStep(stepIndex);
            }
          }} mode="tabbed">
            {renderStepContent()}
            {currentStep < steps.length - 1 && (
              <div className={styles.navRow}>
                <Button variant="secondary" onClick={() => setCurrentStep(prev => Math.max(0, prev - 1))} disabled={currentStep === 0 || isSubmitting}>
                  Back
                </Button>
                <Button variant="primary" onClick={handleNextStep} disabled={isSubmitting}>
                  {isSubmitting ? 'Validating...' : 'Next'}
                </Button>
              </div>
            )}
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

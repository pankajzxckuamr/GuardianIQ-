import React, { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';
import { useToast } from '../hooks/useToast';
import { BoundaryRuleEditor } from '../components/phase2/BoundaryRuleEditor';
import { AgentAssignmentPanel } from '../components/phase2/AgentAssignmentPanel';
import { PageHeader } from '../components/common/PageHeader';
import { RegistryDataTable } from '../components/common/RegistryDataTable';
import { Button } from '../components/common/Button';
import { ScreenGuide } from '../components/common/ScreenGuide';
import { Shield, Plus, X, AlertCircle, CheckCircle, RefreshCw, XCircle } from 'lucide-react';
import { storage } from '../utils/storage';
import styles from './phase2Shared.module.css';

const getAgentLabel = (agent: any) => agent?.agent_name || agent?.name || agent?.agent_code || 'Unknown agent';
const getModelLabel = (model: any) => model?.model_name || model?.name || model?.model_code || 'Unknown model';

const Drawer = ({ open, onClose, title, children }: any) => {
  if (!open) return null;
  return (
    <div className={styles.drawerOverlay}>
      <div className={styles.drawerBackdrop} onClick={onClose} />
      <div className={styles.drawerPanel}>
        <div className={styles.drawerHeader}>
          <h2 className={styles.drawerTitle}>{title}</h2>
          <button className={styles.iconBtnPlain} onClick={onClose} title="Close"><X size={20} /></button>
        </div>
        <div className={styles.drawerBody}>{children}</div>
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

  const [filterWorkflow, setFilterWorkflow] = useState('');
  const [filterAgent, setFilterAgent] = useState('');
  const [filterMode, setFilterMode] = useState('');
  const [filterApproval, setFilterApproval] = useState('');

  const [drawerMode, setDrawerMode] = useState<'EDIT' | 'READ' | 'CREATE' | null>(null);
  const [selectedAssignment, setSelectedAssignment] = useState<any | null>(null);

  const [formData, setFormData] = useState<any>({});
  const [validating, setValidating] = useState(false);
  const [validationResult, setValidationResult] = useState<any>(null);

  const [tools, setTools] = useState<any[]>([]);
  const [agents, setAgents] = useState<any[]>([]);
  const [models, setModels] = useState<any[]>([]);
  const [dataSources, setDataSources] = useState<any[]>([]);
  const [showConfirmDiff, setShowConfirmDiff] = useState(false);
  const [diffList, setDiffList] = useState<any[]>([]);

  useEffect(() => {
    document.title = 'Agent Assignments — GuardianIQ';
  }, []);

  const fetchWithAuth = async (url: string) => {
    const token = storage.get<string>('guardianiq_access_token');
    const res = await fetch(url, { headers: { 'Authorization': `Bearer ${token}` } });
    const json = await res.json();
    return json.data?.items || json.data || [];
  };

  const fetchAssignments = async () => {
    setLoading(true);
    setError(null);
    try {
      const items = await fetchWithAuth('/api/v1/workflow-scheduler/agent-assignments');
      setAssignments(items);
    } catch (e: any) {
      setError(e.message || 'Failed to load assignments');
      setAssignments([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAssignments();
    fetchWithAuth('/api/registry/tools?per_page=100').then(setTools).catch(() => {});
    fetchWithAuth('/api/registry/agents?per_page=100').then(setAgents).catch(() => {});
    fetchWithAuth('/api/registry/models?per_page=100').then(setModels).catch(() => {});
    fetchWithAuth('/api/registry/data-sources?per_page=100').then(setDataSources).catch(() => {});
    // eslint-disable-next-line react-hooks/exhaustive-deps
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
        status: item.status || 'ACTIVE',
      });
    } else {
      setSelectedAssignment(null);
      setFormData({
        agent_id: '', model_id: '', execution_mode: 'READ_ONLY', confidence_threshold: 80,
        allowed_tools_json: [], allowed_data_sources_json: [], blocked_operations_json: [],
        schedule_id: '', status: 'ACTIVE',
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
      const token = storage.get<string>('guardianiq_access_token');
      const res = await fetch('/api/v1/authorization/evaluate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({
          subject_type: 'USER',
          subject_user_id: null,
          object_type: 'agent_assignments',
          object_id: formData.id && formData.id !== 'new' ? formData.id : null,
          action: 'ASSIGN_AI_AGENT_TO_WORKFLOW',
          context_json: { ...formData },
        }),
      });
      const json = await res.json();
      setValidationResult(json.data);
    } catch (e) {
      setValidationResult({ allowed: false, error: 'Validation request failed' });
    } finally {
      setValidating(false);
    }
  };

  const getDiff = () => {
    if (!selectedAssignment) return [];
    const diffs: { field: string; prev: string; next: string }[] = [];

    if (selectedAssignment.agent_id !== formData.agent_id) {
      const prevAgent = agents.find(a => a.id === selectedAssignment.agent_id);
      const nextAgent = agents.find(a => a.id === formData.agent_id);
      diffs.push({
        field: 'Agent',
        prev: getAgentLabel(prevAgent),
        next: getAgentLabel(nextAgent)
      });
    }

    if (selectedAssignment.model_id !== formData.model_id) {
      const prevModel = models.find(m => m.id === selectedAssignment.model_id);
      const nextModel = models.find(m => m.id === formData.model_id);
      diffs.push({
        field: 'Model',
        prev: getModelLabel(prevModel),
        next: getModelLabel(nextModel)
      });
    }

    if (selectedAssignment.execution_mode !== formData.execution_mode) {
      diffs.push({
        field: 'Execution Mode',
        prev: selectedAssignment.execution_mode,
        next: formData.execution_mode
      });
    }

    if (selectedAssignment.confidence_threshold !== formData.confidence_threshold) {
      diffs.push({
        field: 'Confidence Threshold',
        prev: `${selectedAssignment.confidence_threshold}%`,
        next: `${formData.confidence_threshold}%`
      });
    }

    const prevTools = selectedAssignment.allowed_tools_json || [];
    const nextTools = formData.allowed_tools_json || [];
    if (JSON.stringify([...prevTools].sort()) !== JSON.stringify([...nextTools].sort())) {
      const getToolNames = (codes: string[]) => codes.map(c => tools.find(t => t.tool_code === c || t.id === c)?.tool_name || c).join(', ') || 'None';
      diffs.push({
        field: 'Allowed Tools',
        prev: getToolNames(prevTools),
        next: getToolNames(nextTools)
      });
    }

    const prevDataSources = selectedAssignment.allowed_data_sources_json || [];
    const nextDataSources = formData.allowed_data_sources_json || [];
    if (JSON.stringify([...prevDataSources].sort()) !== JSON.stringify([...nextDataSources].sort())) {
      const getDsNames = (codes: string[]) => codes.map(c => dataSources.find(ds => ds.source_code === c || ds.id === c)?.source_name || c).join(', ') || 'None';
      diffs.push({
        field: 'Allowed Data Sources',
        prev: getDsNames(prevDataSources),
        next: getDsNames(nextDataSources)
      });
    }

    const prevBlocked = selectedAssignment.blocked_operations_json || [];
    const nextBlocked = formData.blocked_operations_json || [];
    if (JSON.stringify([...prevBlocked].sort()) !== JSON.stringify([...nextBlocked].sort())) {
      diffs.push({
        field: 'Blocked Operations',
        prev: prevBlocked.join(', ') || 'None',
        next: nextBlocked.join(', ') || 'None'
      });
    }

    return diffs;
  };

  const handleSave = async () => {
    if (drawerMode === 'EDIT' && !showConfirmDiff) {
      const diffs = getDiff();
      if (diffs.length > 0) {
        setDiffList(diffs);
        setShowConfirmDiff(true);
        return;
      }
    }
    await confirmAndSave();
  };

  const confirmAndSave = async () => {
    setShowConfirmDiff(false);
    try {
      const token = storage.get<string>('guardianiq_access_token');
      const method = drawerMode === 'CREATE' ? 'POST' : 'PUT';
      const url = drawerMode === 'CREATE'
        ? `/api/v1/workflow-scheduler/schedules/${formData.schedule_id}/agent-assignments`
        : `/api/v1/workflow-scheduler/schedules/${formData.schedule_id}/agent-assignments/${formData.id}`;
      const res = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify(formData),
      });
      const json = await res.json();
      if (json.status !== 'success') throw new Error(json.message || 'Save failed');
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
      const token = storage.get<string>('guardianiq_access_token');
      const res = await fetch(`/api/v1/workflow-scheduler/schedules/${item.schedule_id}/agent-assignments/${item.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({ ...item, status: 'INACTIVE' }),
      });
      const json = await res.json();
      if (json.status !== 'success') throw new Error(json.message || 'Disable failed');
      showToast('Assignment disabled', 'success');
      fetchAssignments();
    } catch (e: any) {
      showToast(e.message || 'Failed to disable', 'error');
    }
  };

  const clearFilters = () => { setFilterWorkflow(''); setFilterAgent(''); setFilterMode(''); setFilterApproval(''); };
  const hasActiveFilters = !!filterWorkflow || !!filterAgent || !!filterMode || !!filterApproval;

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

  const hasWriteTool = tools.some(t => {
    const code = t.tool_code || t.id;
    const mode = t.access_mode || t.capability || '';
    return (formData.allowed_tools_json || []).some((entry: string) => entry === code || entry === t.id)
      && ['WRITE', 'EXECUTE', 'ADMIN'].includes(mode);
  });

  const columns = [
    { key: 'workflow_name', label: 'Workflow', render: (a: any) => <span>{a.workflow_name || a.workflow_id}</span> },
    { key: 'schedule_name', label: 'Schedule', render: (a: any) => <span className={styles.mutedCell}>{a.schedule_name || a.schedule_id}</span> },
    { key: 'agent_name', label: 'Agent', render: (a: any) => <span>{a.agent_name || a.agent_id}</span> },
    { key: 'execution_mode', label: 'Mode', render: (a: any) => <span className={`${styles.pill} ${styles.pillInfo}`}>{a.execution_mode}</span> },
    { key: 'allowed_tools_json', label: 'Tools', render: (a: any) => <span className={styles.mutedCell}>{a.allowed_tools_json?.length || 0} allowed</span> },
    { key: 'approval_required', label: 'Approval', render: (a: any) => a.approval_required ? <span className={`${styles.pill} ${styles.pillWarning}`}>YES</span> : <span className={`${styles.pill} ${styles.pillNeutral}`}>NO</span> },
    {
      key: 'actions',
      label: 'Actions',
      render: (a: any) => (
        <div className={styles.actions}>
          {a.status === 'ACTIVE' && canEdit && (
            <Button variant="secondary" size="sm" onClick={(e) => handleDisable(a, e as any)}>Disable</Button>
          )}
          {a.status === 'INACTIVE' && <span className={`${styles.pill} ${styles.pillNeutral}`}>DISABLED</span>}
        </div>
      ),
    },
  ];

  return (
    <div className={styles.page}>
      <div className={styles.breadcrumb}>Orchestration &gt; Agent Assignments</div>
      <PageHeader
        title="Agent Assignment Matrix"
        description="Global overview of AI agents assigned to governance workflows"
        actions={
          <>
            {canEdit && (
              <Button variant="primary" onClick={() => openDrawer('CREATE')} icon={<Plus size={16} />}>
                Add Assignment
              </Button>
            )}
            <ScreenGuide
              content={
                <div style={{ display: "flex", flexDirection: "column", gap: "12px", paddingRight: "4px" }}>
                  <h4 style={{ color: "#fbbf24", margin: "0 0 4px 0", fontSize: "0.85rem" }}>Agent Assignment Matrix</h4>
                  <p style={{ margin: 0 }}>Manage global AI agent assignments and their security boundaries across all automated workflows. Ensure appropriate constraints and approval requirements are in place.</p>
                </div>
              }
            />
          </>
        }
      />

      {/* Filters */}
      <div className={styles.filterBar}>
        <div className={styles.filterRow}>
          <div className={styles.filtersGroup}>
            <select className={styles.filterSelect} value={filterAgent} onChange={e => setFilterAgent(e.target.value)}>
              <option value="">All Agents</option>
              {agents.map(a => <option key={a.id} value={a.id}>{getAgentLabel(a)}</option>)}
            </select>
            <select className={styles.filterSelect} value={filterMode} onChange={e => setFilterMode(e.target.value)}>
              <option value="">All Modes</option>
              <option value="READ_ONLY">READ_ONLY</option>
              <option value="RECOMMEND_ONLY">RECOMMEND_ONLY</option>
              <option value="APPROVAL_REQUIRED">APPROVAL_REQUIRED</option>
              <option value="LIMITED_EXECUTION">LIMITED_EXECUTION</option>
            </select>
            <select className={styles.filterSelect} value={filterApproval} onChange={e => setFilterApproval(e.target.value)}>
              <option value="">All Approval</option>
              <option value="yes">Approval: Yes</option>
              <option value="no">Approval: No</option>
            </select>
          </div>
          {hasActiveFilters && (
            <button className={styles.clearBtn} onClick={clearFilters}>Clear Filters</button>
          )}
        </div>
      </div>

      {/* Table */}
      <div className={styles.tableContainer}>
        {error ? (
          <div className={styles.stateCard}>
            <AlertCircle size={36} className={styles.stateIcon} />
            <div className={styles.stateTitle}>Error Loading Assignments</div>
            <div className={styles.stateDesc}>{error}</div>
            <Button variant="secondary" size="sm" onClick={fetchAssignments} icon={<RefreshCw size={14} />}>Retry</Button>
          </div>
        ) : (
          <RegistryDataTable
            columns={columns}
            data={displayList}
            isLoading={loading}
            totalCount={displayList.length}
            page={1}
            pageSize={Math.max(displayList.length, 1)}
            onPageChange={() => {}}
            onRowClick={handleRowClick}
            emptyMessage={hasActiveFilters ? 'No agent assignments match your filters.' : 'No agent assignments found.'}
          />
        )}
      </div>

      <Drawer
        open={drawerMode !== null}
        onClose={closeDrawer}
        title={drawerMode === 'READ' ? 'Assignment Details' : drawerMode === 'EDIT' ? 'Edit Assignment' : 'Create Assignment'}
      >
        {drawerMode === 'READ' ? (
          <AgentAssignmentPanel assignment={selectedAssignment} readonly={true} />
        ) : (
          <>
            {drawerMode === 'CREATE' && (
              <div>
                <label className={styles.fieldLabel}>Schedule ID</label>
                <input className={styles.formControl} type="text" value={formData.schedule_id} onChange={e => handleFormChange('schedule_id', e.target.value)} placeholder="Enter schedule UUID..." />
              </div>
            )}

            <div className={styles.formGrid2}>
              <div>
                <label className={styles.fieldLabel}>Agent</label>
                <select className={styles.formControl} value={formData.agent_id} onChange={e => handleFormChange('agent_id', e.target.value)}>
                  <option value="">Select Agent</option>
                  {agents.map(a => <option key={a.id} value={a.id}>{getAgentLabel(a)}</option>)}
                </select>
              </div>
              <div>
                <label className={styles.fieldLabel}>Model</label>
                <select className={styles.formControl} value={formData.model_id} onChange={e => handleFormChange('model_id', e.target.value)}>
                  <option value="">Select Model</option>
                  {models.map(m => <option key={m.id} value={m.id}>{getModelLabel(m)}</option>)}
                </select>
              </div>
            </div>

            <div className={styles.formGrid2}>
              <div>
                <label className={styles.fieldLabel}>Execution Mode</label>
                <select className={styles.formControl} value={formData.execution_mode} onChange={e => handleFormChange('execution_mode', e.target.value)}>
                  <option value="READ_ONLY">READ_ONLY</option>
                  <option value="RECOMMEND_ONLY">RECOMMEND_ONLY</option>
                  <option value="APPROVAL_REQUIRED">APPROVAL_REQUIRED</option>
                  <option value="LIMITED_EXECUTION">LIMITED_EXECUTION</option>
                </select>
              </div>
              <div>
                <label className={styles.fieldLabel}>Confidence Threshold</label>
                <input className={styles.range} type="range" min="0" max="100" value={formData.confidence_threshold} onChange={e => handleFormChange('confidence_threshold', parseInt(e.target.value))} />
                <div className={styles.rangeValue}>{formData.confidence_threshold}%</div>
              </div>
            </div>

            <BoundaryRuleEditor
              allowedTools={formData.allowed_tools_json}
              allowedDataSources={formData.allowed_data_sources_json}
              blockedOperations={formData.blocked_operations_json}
              onChange={handleFormChange}
              toolOptions={tools}
              dataSourceOptions={dataSources}
            />

            {hasWriteTool && (
              <div className={styles.banner}>
                <AlertCircle size={16} /> This tool requires approval_required=true on the schedule. Ensure the schedule is configured correctly.
              </div>
            )}

            <div className={styles.section}>
              <div className={styles.validateHeader}>
                <h4 className={styles.subHeading}>Authorization Check</h4>
                <Button variant="secondary" size="sm" onClick={handleValidateBoundary} loading={validating} icon={<Shield size={14} />}>
                  Validate Boundary
                </Button>
              </div>
              {validationResult && (
                <div className={`${styles.validateResult} ${validationResult.allowed ? styles.validatePass : styles.validateFail}`}>
                  {validationResult.allowed ? <CheckCircle size={16} /> : <XCircle size={16} />}
                  {validationResult.allowed ? 'Boundary validation passed.' : 'Validation failed: Exceeds allowed limits.'}
                </div>
              )}
            </div>

            <div className={styles.drawerFooter}>
              <Button variant="secondary" onClick={closeDrawer}>Cancel</Button>
              <Button variant="primary" onClick={handleSave}>Save Assignment</Button>
            </div>
          </>
        )}
      </Drawer>

      {showConfirmDiff && (
        <div className={styles.drawerOverlay} style={{ zIndex: 1000 }}>
          <div className={styles.drawerBackdrop} onClick={() => setShowConfirmDiff(false)} />
          <div className={styles.drawerPanel} style={{ maxWidth: 500, height: 'auto', maxHeight: '80vh', borderRadius: '8px', overflow: 'hidden' }}>
            <div className={styles.drawerHeader}>
              <h2 className={styles.drawerTitle}>Confirm Assignment Changes</h2>
              <button className={styles.iconBtnPlain} onClick={() => setShowConfirmDiff(false)} title="Close"><X size={20} /></button>
            </div>
            <div className={styles.drawerBody} style={{ padding: '1.5rem', background: '#0b1329' }}>
              <p className={styles.subText} style={{ marginBottom: '1rem', color: '#94a3b8' }}>
                You are updating the agent assignment boundary configurations. The parent schedule status will revert to <strong>Pending Approval</strong>.
              </p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginBottom: '1.5rem' }}>
                {diffList.map((d: any, idx: number) => (
                  <div key={idx} style={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '6px', padding: '0.75rem' }}>
                    <div style={{ fontWeight: '600', fontSize: '0.85rem', color: '#38bdf8', marginBottom: '0.25rem' }}>{d.field}</div>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', fontSize: '0.8rem' }}>
                      <div style={{ color: '#ef4444', textDecoration: 'line-through' }}>
                        Prev: {d.prev}
                      </div>
                      <div style={{ color: '#10b981' }}>
                        New: {d.next}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              <div className={styles.drawerFooter} style={{ borderTop: '1px solid #334155', paddingTop: '1rem', display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
                <Button variant="secondary" onClick={() => setShowConfirmDiff(false)}>Cancel</Button>
                <Button variant="primary" onClick={confirmAndSave}>Confirm & Save</Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AgentAssignmentMatrix;

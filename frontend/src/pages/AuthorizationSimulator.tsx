import React, { useState, useEffect } from 'react';
import { useToast } from '../hooks/useToast';
import { Shield, CheckCircle, XCircle } from 'lucide-react';
import { storage } from '../utils/storage';
import { PageHeader } from '../components/common/PageHeader';
import { Button } from '../components/common/Button';
import { ScreenGuide } from '../components/common/ScreenGuide';
import { useNavigate } from 'react-router-dom';
import styles from './phase2Shared.module.css';

const ACTIONS = [
  'CREATE_WORKFLOW_SCHEDULE', 'VIEW_WORKFLOW_SCHEDULE', 'UPDATE_WORKFLOW_SCHEDULE',
  'SUBMIT_WORKFLOW_SCHEDULE', 'ACTIVATE_WORKFLOW_SCHEDULE', 'PAUSE_WORKFLOW_SCHEDULE',
  'RESUME_WORKFLOW_SCHEDULE', 'RETIRE_WORKFLOW_SCHEDULE', 'RUN_WORKFLOW_SCHEDULE',
  'VIEW_WORKFLOW_RUN', 'CANCEL_WORKFLOW_RUN', 'VIEW_WORKFLOW_RUN_OUTPUT',
  'ASSIGN_AI_AGENT_TO_WORKFLOW', 'EVALUATE_AUTHORIZATION',
];

export const AuthorizationSimulator: React.FC = () => {
  const { showToast } = useToast();
  const navigate = useNavigate();

  const [subjectType, setSubjectType] = useState('USER');
  const [subjectId, setSubjectId] = useState('');
  const [objectType, setObjectType] = useState('SCHEDULE');
  const [objectId, setObjectId] = useState('');
  const [actionId, setActionId] = useState('VIEW_WORKFLOW_SCHEDULE');

  const [envEmergency, setEnvEmergency] = useState(false);
  const [envDelegation, setEnvDelegation] = useState(false);

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  // Fetch real registered agents for subject selection
  const [agents, setAgents] = useState<any[]>([]);
  const [isCustomSubject, setIsCustomSubject] = useState(false);

  useEffect(() => {
    document.title = 'Authorization Simulator — GuardianIQ';
    const fetchAgents = async () => {
      try {
        const token = storage.get<string>('guardianiq_access_token');
        const res = await fetch('/api/v1/registry/agents?per_page=100', {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        const json = await res.json();
        const items = Array.isArray(json.data) ? json.data : (json.data?.items || []);
        setAgents(items);
        if (subjectType === 'AGENT' && items.length > 0 && !subjectId) {
          setSubjectId(items[0].id);
        }
      } catch {
        // Fallback gracefully
      }
    };
    fetchAgents();
  }, []);

  const getPayload = () => {
    const mappedObjectType =
      objectType === 'SCHEDULE' ? 'workflow_schedules' :
      objectType === 'RUN' ? 'workflow_runs' :
      objectType === 'OUTPUT' ? 'workflow_run_outputs' :
      objectType === 'ASSIGNMENT' ? 'agent_assignments' :
      objectType;

    return {
      subject_user_id: subjectType === 'USER' ? (subjectId || null) : null,
      subject_agent_id: subjectType === 'AGENT' ? (subjectId || null) : null,
      subject_type: subjectType,
      object_type: mappedObjectType,
      object_id: objectId || null,
      action: actionId,
      context_json: {
        emergency_flag: envEmergency,
        delegation_active: envDelegation,
      },
    };
  };

  const handleEvaluate = async () => {
    if (!subjectId || !objectId || !actionId) {
      showToast('Please fill out Subject, Object, and Action', 'error');
      return;
    }
    setLoading(true);
    try {
      const token = storage.get<string>('guardianiq_access_token');
      const payload = getPayload();
      const res = await fetch('/api/v1/authorization/evaluate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify(payload),
      });
      const json = await res.json();
      if (json.status !== 'success') throw new Error(json.message || 'Evaluation failed');
      
      // Map backend response structure to UI state
      setResult({
        allowed: json.data.allowed,
        rbac_passed: json.data.rbac_result?.allowed,
        abac_passed: json.data.abac_result?.allowed,
        relationship_passed: json.data.relationship_result?.allowed,
        failed_conditions: json.data.abac_result?.failed_conditions || json.data.deny_reasons || [],
      });
    } catch (e: any) {
      showToast(e.message || 'Simulation failed', 'error');
    } finally {
      setLoading(false);
    }
  };

  const copyPayload = () => {
    const payload = getPayload();
    navigator.clipboard.writeText(JSON.stringify(payload, null, 2));
    showToast('Payload copied to clipboard', 'success');
  };

  return (
    <div className={styles.page}>
      <div className={styles.breadcrumb}>
        <button className={styles.textBtn} onClick={() => navigate(-1)} style={{marginRight: '8px'}}>
          &lt; Back
        </button>
        Orchestration &gt; Authorization Simulator
      </div>
      <PageHeader
        title="Authorization Simulator"
        description="Evaluate RBAC and ABAC access decisions without granting or mutating permissions"
        actions={
          <ScreenGuide 
            content={
              <div style={{ display: "flex", flexDirection: "column", gap: "12px", paddingRight: "4px" }}>
                <h4 style={{ color: "#fbbf24", margin: "0 0 4px 0", fontSize: "0.85rem" }}>Authorization Simulator</h4>
                <p style={{ margin: 0 }}>Evaluate RBAC and ABAC access decisions for users and agents. This tool simulates policy evaluation without making any actual changes to permissions.</p>
              </div>
            }
          />
        }
      />

      <div className={styles.bannerInfo}>
        <Shield size={16} /> This tool evaluates authorization only. It does not grant access or mutate permissions.
      </div>

      <div className={styles.card}>
        <h3 className={styles.cardTitle}>Simulation Parameters</h3>

        <div className={styles.simGrid}>
          {/* Subject */}
          <div className={styles.section}>
            <h4 className={styles.sectionTitle}>Subject</h4>
            <div className={styles.fieldStack}>
              <div>
                <label className={styles.smallLabel}>Type</label>
                <select className={styles.formControl} value={subjectType} onChange={e => {
                  setSubjectType(e.target.value);
                  setIsCustomSubject(false);
                  if (e.target.value === 'AGENT' && agents.length > 0) {
                    setSubjectId(agents[0].id);
                  } else {
                    setSubjectId('');
                  }
                }}>
                  <option value="USER">User</option>
                  <option value="AGENT">AI Agent</option>
                </select>
              </div>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <label className={styles.smallLabel}>Target Subject</label>
                  {subjectType === 'AGENT' && (
                    <button
                      type="button"
                      onClick={() => setIsCustomSubject(!isCustomSubject)}
                      style={{ background: 'transparent', border: 'none', color: '#818cf8', fontSize: '0.7rem', cursor: 'pointer' }}
                    >
                      {isCustomSubject ? 'Select from Registry' : 'Enter Custom UUID'}
                    </button>
                  )}
                </div>
                {subjectType === 'AGENT' && !isCustomSubject ? (
                  <select
                    className={styles.formControl}
                    value={subjectId}
                    onChange={e => setSubjectId(e.target.value)}
                  >
                    <option value="" disabled>Select an AI Agent...</option>
                    {agents.map(a => (
                      <option key={a.id} value={a.id}>
                        {a.agent_name} ({a.risk_level || 'MEDIUM'})
                      </option>
                    ))}
                  </select>
                ) : (
                  <input
                    className={styles.formControl}
                    type="text"
                    value={subjectId}
                    onChange={e => setSubjectId(e.target.value)}
                    placeholder={`Enter ${subjectType === 'USER' ? 'User ID or Email' : 'Agent UUID'}...`}
                  />
                )}
              </div>
            </div>
          </div>

          {/* Object */}
          <div className={styles.section}>
            <h4 className={styles.sectionTitle}>Object</h4>
            <div className={styles.fieldStack}>
              <div>
                <label className={styles.smallLabel}>Type</label>
                <select className={styles.formControl} value={objectType} onChange={e => setObjectType(e.target.value)}>
                  <option value="SCHEDULE">Schedule</option>
                  <option value="RUN">Run</option>
                  <option value="OUTPUT">Output</option>
                  <option value="ASSIGNMENT">Agent Assignment</option>
                </select>
              </div>
              <div>
                <label className={styles.smallLabel}>Object Target ID</label>
                <input className={styles.formControl} type="text" value={objectId} onChange={e => setObjectId(e.target.value)} placeholder={`Enter ${objectType} UUID or identifier...`} />
              </div>
            </div>
          </div>

          {/* Action & Environment */}
          <div className={styles.section}>
            <h4 className={styles.sectionTitle}>Action &amp; Environment</h4>
            <div className={styles.fieldStack}>
              <div>
                <label className={styles.smallLabel}>Action Code</label>
                <select className={styles.formControl} value={actionId} onChange={e => setActionId(e.target.value)}>
                  {ACTIONS.map(a => <option key={a} value={a}>{a}</option>)}
                </select>
              </div>
              <label className={styles.checkboxLabel}>
                <input type="checkbox" checked={envEmergency} onChange={e => setEnvEmergency(e.target.checked)} />
                Emergency Flag Active
              </label>
              <label className={styles.checkboxLabel}>
                <input type="checkbox" checked={envDelegation} onChange={e => setEnvDelegation(e.target.checked)} />
                Delegation Active
              </label>
            </div>
          </div>
        </div>

        <div className={styles.formFooter}>
          <Button variant="primary" onClick={handleEvaluate} loading={loading} icon={<Shield size={16} />}>
            Evaluate Access
          </Button>
        </div>
      </div>

      {result && (
        <div>
          <div className={`${styles.resultBanner} ${result.allowed ? styles.resultAllow : styles.resultDeny}`}>
            <h3 className={`${styles.resultTitle} ${result.allowed ? styles.resultTitleAllow : styles.resultTitleDeny}`}>
              {result.allowed ? <CheckCircle size={28} /> : <XCircle size={28} />}
              {result.allowed ? 'ALLOW' : 'DENY'}
            </h3>
            <p className={styles.resultDesc}>
              {result.allowed ? 'Subject is authorized to perform this action.' : 'Subject lacks required permissions or fails ABAC conditions.'}
            </p>
          </div>

          <div className={styles.resultBody}>
            <div className={styles.checkGrid}>
              <div>
                <h4 className={styles.checkTitle}>RBAC Check</h4>
                <p className={result.rbac_passed ? styles.passText : styles.failText}>
                  {result.rbac_passed ? 'Passed (Roles matched)' : 'Failed (Missing roles)'}
                </p>
              </div>
              <div>
                <h4 className={styles.checkTitle}>ABAC Check</h4>
                <p className={result.abac_passed ? styles.passText : styles.failText}>
                  {result.abac_passed ? 'Passed (All conditions met)' : 'Failed (Conditions unmet)'}
                </p>
                {result.failed_conditions && result.failed_conditions.length > 0 && (
                  <ul className={styles.failList}>
                    {result.failed_conditions.map((fc: string, i: number) => <li key={i}>{fc}</li>)}
                  </ul>
                )}
              </div>
              <div>
                <h4 className={styles.checkTitle}>Relationship Check</h4>
                <p className={result.relationship_passed ? styles.passText : styles.naText}>
                  {result.relationship_passed ? 'Passed (Owner/Delegate)' : 'N/A or Failed'}
                </p>
              </div>
            </div>
            <div className={styles.resultFooter}>
              <button className={styles.textBtn} onClick={copyPayload}>Copy Request JSON</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AuthorizationSimulator;

import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { scheduleApi, runApi } from '../api/phase2Client';
import { WorkflowScheduleResponse, ApprovalResponse, HistoryResponse } from '../types/phase2';
import { ScheduleStatusBadge } from '../components/phase2/ScheduleStatusBadge';
import { RiskLevelBadge } from '../components/phase2/RiskLevelBadge';
import { ConfirmActionModal } from '../components/phase2/ConfirmActionModal';
import { AgentAssignmentPanel } from '../components/phase2/AgentAssignmentPanel';
import { AuditTimelinePanel } from '../components/phase2/AuditTimelinePanel';
import { useAuth } from '../hooks/useAuth';
import { useToast } from '../hooks/useToast';
import { Play, Pause, Archive, CheckCircle, RefreshCw } from 'lucide-react';

export const ScheduleDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const { currentUser } = useAuth();
  const { showToast } = useToast();
  const navigate = useNavigate();

  const [schedule, setSchedule] = useState<WorkflowScheduleResponse | null>(null);
  const [approvals, setApprovals] = useState<ApprovalResponse[]>([]);
  const [history, setHistory] = useState<HistoryResponse[]>([]);
  const [runs, setRuns] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'OVERVIEW' | 'AGENTS' | 'BOUNDARIES' | 'TIMING' | 'APPROVALS' | 'RUNS' | 'AUDIT' | 'HISTORY'>('OVERVIEW');

  // Modals
  const [confirmModal, setConfirmModal] = useState<{
    open: boolean;
    title: string;
    message: string;
    action: 'PAUSE' | 'RESUME' | 'RETIRE' | 'SUBMIT' | 'ACTIVATE' | null;
    requireReason: boolean;
  }>({ open: false, title: '', message: '', action: null, requireReason: false });

  const hasPerm = (p: string) => currentUser?.is_superuser || currentUser?.permissions?.includes(p);

  const fetchData = async () => {
    if (!id) return;
    setLoading(true);
    try {
      const [schedRes, appRes, histRes, runsRes] = await Promise.all([
        scheduleApi.getById(id),
        scheduleApi.getApprovals(id).catch(() => []),
        scheduleApi.getHistory(id).catch(() => []),
        runApi.list({ schedule_id: id, per_page: 5 }).catch(() => ({ items: [] }))
      ]);
      setSchedule(schedRes as WorkflowScheduleResponse);
      setApprovals(appRes as any);
      setHistory(histRes as any);
      setRuns((runsRes as any).items || []);
    } catch (e: any) {
      setError(e.message || 'Failed to load schedule');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  const handleAction = async (reason?: string) => {
    const action = confirmModal.action;
    if (!action || !id) return;

    try {
      if (action === 'PAUSE') await scheduleApi.pause(id);
      if (action === 'RESUME') await scheduleApi.resume(id);
      if (action === 'RETIRE') await scheduleApi.retire(id);
      if (action === 'SUBMIT') await scheduleApi.submit(id);
      if (action === 'ACTIVATE') await scheduleApi.activate(id);
      
      showToast(`Action ${action.toLowerCase()} completed successfully`, 'success');
      setConfirmModal({ ...confirmModal, open: false });
      fetchData();
    } catch (e: any) {
      showToast(e.message || `Failed to perform action`, 'error');
    }
  };

  const handleRunNow = async () => {
    if (!id) return;
    try {
      await scheduleApi.runNow(id);
      showToast('Run triggered successfully', 'success');
      fetchData();
    } catch (e: any) {
      showToast(e.message || 'Failed to trigger run', 'error');
    }
  };

  if (loading) return <div className="p-8 text-center text-gray-500">Loading schedule...</div>;
  if (error || !schedule) return <div className="p-8 text-center text-red-500">{error || 'Schedule not found'}</div>;

  return (
    <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8 space-y-6">
      {/* Header */}
      <div className="bg-white shadow sm:rounded-lg border border-gray-200 p-6">
        <div className="flex justify-between items-start">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold text-gray-900">{schedule.schedule_name}</h1>
              <ScheduleStatusBadge status={schedule.schedule_status} />
              <RiskLevelBadge riskLevel={schedule.risk_level} />
            </div>
            <p className="mt-1 text-sm text-gray-500 font-mono">{schedule.schedule_code}</p>
            <div className="mt-4 flex gap-6 text-sm text-gray-600">
              <div>Owner: <span className="font-medium text-gray-900">{schedule.owner_user_id}</span></div>
              <div>Next Run: <span className="font-medium text-gray-900">{schedule.next_run_at ? new Date(schedule.next_run_at).toLocaleString() : 'Manual only'} ({schedule.timezone})</span></div>
              <div>Last Run: <span className="font-medium text-gray-900">{schedule.last_run_at ? new Date(schedule.last_run_at).toLocaleString() : 'Never'}</span></div>
            </div>
          </div>
          <div className="flex flex-wrap gap-2 justify-end">
            {schedule.schedule_status === 'DRAFT' && hasPerm('CREATE_WORKFLOW_SCHEDULE') && (
              <button onClick={() => setConfirmModal({ open: true, title: 'Submit Schedule', message: 'Submit this schedule for approval or activation?', action: 'SUBMIT', requireReason: false })} className="px-3 py-2 border rounded-md text-sm font-medium bg-white text-indigo-600 border-indigo-200 hover:bg-indigo-50">Submit</button>
            )}
            {schedule.schedule_status === 'PENDING_APPROVAL' && hasPerm('ACTIVATE_WORKFLOW_SCHEDULE') && (
              <button onClick={() => navigate('/schedule-approvals')} className="px-3 py-2 border rounded-md text-sm font-medium bg-indigo-600 text-white hover:bg-indigo-700">Go to Approvals</button>
            )}
            {schedule.schedule_status === 'ACTIVE' && hasPerm('RUN_WORKFLOW_SCHEDULE') && (
              <button onClick={handleRunNow} className="inline-flex items-center px-3 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700"><Play className="mr-2 h-4 w-4" /> Run Now</button>
            )}
            {schedule.schedule_status === 'ACTIVE' && hasPerm('PAUSE_WORKFLOW_SCHEDULE') && (
              <button onClick={() => setConfirmModal({ open: true, title: 'Pause', message: 'Pause this schedule?', action: 'PAUSE', requireReason: false })} className="px-3 py-2 border rounded-md text-sm font-medium bg-white text-amber-600 border-amber-200 hover:bg-amber-50">Pause</button>
            )}
            {schedule.schedule_status === 'PAUSED' && hasPerm('RESUME_WORKFLOW_SCHEDULE') && (
              <button onClick={() => setConfirmModal({ open: true, title: 'Resume', message: 'Resume this schedule?', action: 'RESUME', requireReason: false })} className="px-3 py-2 border rounded-md text-sm font-medium bg-white text-green-600 border-green-200 hover:bg-green-50">Resume</button>
            )}
            {schedule.schedule_status !== 'RETIRED' && hasPerm('RETIRE_WORKFLOW_SCHEDULE') && (
              <button onClick={() => setConfirmModal({ open: true, title: 'Retire', message: 'Permanently retire schedule?', action: 'RETIRE', requireReason: true })} className="px-3 py-2 border rounded-md text-sm font-medium bg-white text-red-600 border-red-200 hover:bg-red-50">Retire</button>
            )}
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white shadow sm:rounded-lg border border-gray-200">
        <div className="border-b border-gray-200 overflow-x-auto">
          <nav className="-mb-px flex px-4 sm:px-6 gap-6" aria-label="Tabs">
            {['OVERVIEW', 'AGENTS', 'BOUNDARIES', 'TIMING', 'APPROVALS', 'RUNS', 'AUDIT', 'HISTORY'].map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab as any)}
                className={`${
                  activeTab === tab
                    ? 'border-indigo-500 text-indigo-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                } whitespace-nowrap py-4 border-b-2 font-medium text-sm`}
              >
                {tab.charAt(0) + tab.slice(1).toLowerCase()}
              </button>
            ))}
          </nav>
        </div>

        <div className="p-6">
          {activeTab === 'OVERVIEW' && (
            <div className="space-y-6">
              {schedule.schedule_status === 'PENDING_APPROVAL' && (
                <div className="bg-amber-50 border-l-4 border-amber-400 p-4">
                  <p className="text-amber-700 text-sm">This schedule is pending approval. <Link to="/schedule-approvals" className="font-semibold underline">View Queue</Link></p>
                </div>
              )}
              <dl className="grid grid-cols-1 gap-x-4 gap-y-6 sm:grid-cols-2">
                <div className="sm:col-span-1">
                  <dt className="text-sm font-medium text-gray-500">Workflow</dt>
                  <dd className="mt-1 text-sm text-gray-900">{schedule.workflow_id}</dd>
                </div>
                <div className="sm:col-span-1">
                  <dt className="text-sm font-medium text-gray-500">Health Status</dt>
                  <dd className="mt-1 text-sm font-medium">{schedule.health_status}</dd>
                </div>
              </dl>
              
              <div className="mt-8">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Recent Runs</h3>
                <div className="border border-gray-200 rounded-md overflow-hidden">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Run Code</th>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Status</th>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Duration</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200 text-sm">
                      {runs.map(r => (
                        <tr key={r.id}>
                          <td className="px-4 py-2 text-indigo-600"><Link to={`/workflow-runs/${r.id}`}>{r.run_code}</Link></td>
                          <td className="px-4 py-2">{r.run_status}</td>
                          <td className="px-4 py-2">{r.duration_ms ? `${(r.duration_ms/1000).toFixed(1)}s` : '-'}</td>
                        </tr>
                      ))}
                      {runs.length === 0 && <tr><td colSpan={3} className="px-4 py-4 text-center text-gray-500">No runs yet</td></tr>}
                    </tbody>
                  </table>
                </div>
                <div className="mt-2 text-right">
                  <button onClick={() => setActiveTab('RUNS')} className="text-sm text-indigo-600 hover:text-indigo-900">View all runs &rarr;</button>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'AGENTS' && (
            <div className="space-y-4">
              {schedule.agent_assignments?.map((aa, i) => (
                <AgentAssignmentPanel key={i} assignment={aa} readonly={true} />
              ))}
            </div>
          )}

          {activeTab === 'BOUNDARIES' && (
            <div className="space-y-6">
              <h3 className="text-sm font-medium text-gray-900">Configured Limits</h3>
              <ul className="list-disc pl-5 text-sm text-gray-600 space-y-2">
                <li>Max Runtime: {schedule.max_runtime_seconds}s</li>
                <li>Allowed Tools: {schedule.agent_assignments?.[0]?.allowed_tools_json?.join(', ') || 'None'}</li>
                <li>Blocked Ops: {schedule.agent_assignments?.[0]?.blocked_operations_json?.join(', ') || 'None'}</li>
              </ul>
            </div>
          )}

          {activeTab === 'TIMING' && (
            <dl className="grid grid-cols-1 gap-x-4 gap-y-6 sm:grid-cols-2">
              <div><dt className="text-sm font-medium text-gray-500">Type</dt><dd className="mt-1 text-sm text-gray-900">{schedule.schedule_type}</dd></div>
              <div><dt className="text-sm font-medium text-gray-500">Cron</dt><dd className="mt-1 text-sm text-gray-900">{schedule.cron_expression || '-'}</dd></div>
              <div><dt className="text-sm font-medium text-gray-500">Timezone</dt><dd className="mt-1 text-sm text-gray-900">{schedule.timezone}</dd></div>
              <div><dt className="text-sm font-medium text-gray-500">Concurrency Policy</dt><dd className="mt-1 text-sm text-gray-900">{schedule.concurrency_policy}</dd></div>
            </dl>
          )}

          {activeTab === 'APPROVALS' && (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200 border">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Type</th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Status</th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Approver</th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Reason</th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Date</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200 text-sm">
                  {approvals.map(a => (
                    <tr key={a.id}>
                      <td className="px-4 py-2">{a.approval_type}</td>
                      <td className="px-4 py-2">{a.approval_status}</td>
                      <td className="px-4 py-2">{a.approver_user_id || '-'}</td>
                      <td className="px-4 py-2">{a.decision_reason || '-'}</td>
                      <td className="px-4 py-2">{a.decided_at ? new Date(a.decided_at).toLocaleString() : '-'}</td>
                    </tr>
                  ))}
                  {approvals.length === 0 && <tr><td colSpan={5} className="px-4 py-4 text-center text-gray-500">No approval records found</td></tr>}
                </tbody>
              </table>
            </div>
          )}

          {activeTab === 'RUNS' && (
            <div className="text-center py-8">
              <p className="text-gray-500 mb-4">View full paginated runs for this schedule in the Run History page.</p>
              <button onClick={() => navigate(`/workflow-runs?search=${schedule.schedule_code}`)} className="text-indigo-600 hover:text-indigo-800 font-medium border border-indigo-600 rounded px-4 py-2">
                Open Run History
              </button>
            </div>
          )}

          {activeTab === 'AUDIT' && (
            <AuditTimelinePanel entityType="WORKFLOW_SCHEDULE" entityId={id || ''} />
          )}

          {activeTab === 'HISTORY' && (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200 border">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Type</th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Summary</th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">User</th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Date</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200 text-sm">
                  {history.map(h => (
                    <tr key={h.id}>
                      <td className="px-4 py-2">{h.change_type}</td>
                      <td className="px-4 py-2">{h.change_summary}</td>
                      <td className="px-4 py-2">{h.changed_by || 'System'}</td>
                      <td className="px-4 py-2">{new Date(h.created_at).toLocaleString()}</td>
                    </tr>
                  ))}
                  {history.length === 0 && <tr><td colSpan={4} className="px-4 py-4 text-center text-gray-500">No change history found</td></tr>}
                </tbody>
              </table>
            </div>
          )}

        </div>
      </div>

      <ConfirmActionModal
        open={confirmModal.open}
        title={confirmModal.title}
        message={confirmModal.message}
        requireReason={confirmModal.requireReason}
        onConfirm={handleAction}
        onCancel={() => setConfirmModal({ ...confirmModal, open: false })}
      />
    </div>
  );
};

export default ScheduleDetailPage;

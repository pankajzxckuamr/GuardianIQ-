import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { runApi } from '../api/phase2Client';
import { WorkflowRunResponse, WorkflowRunStepResponse, WorkflowRunOutputResponse } from '../types/phase2';
import { RiskLevelBadge } from '../components/phase2/RiskLevelBadge';
import { RunTimeline } from '../components/phase2/RunTimeline';
import { RunOutputViewer } from '../components/phase2/RunOutputViewer';
import { AuditTimelinePanel } from '../components/phase2/AuditTimelinePanel';
import { useAuth } from '../hooks/useAuth';
import { useToast } from '../hooks/useToast';
import { AlertCircle, Clock, CheckCircle, XCircle, PlayCircle, Download } from 'lucide-react';

const RunStatusBadge = ({ status }: { status: string }) => {
  const colors: any = {
    QUEUED: 'bg-gray-100 text-gray-800',
    RUNNING: 'bg-blue-100 text-blue-800',
    COMPLETED: 'bg-green-100 text-green-800',
    FAILED: 'bg-red-100 text-red-800',
    CANCELLED: 'bg-orange-100 text-orange-800',
  };
  return <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${colors[status] || 'bg-gray-100 text-gray-800'}`}>{status}</span>;
};

export const RunDetailPage: React.FC = () => {
  const { runId } = useParams<{ runId: string }>();
  const { currentUser } = useAuth();
  const { showToast } = useToast();

  const canViewRun = currentUser?.is_superuser || currentUser?.permissions?.includes('VIEW_WORKFLOW_RUN');
  const canViewOutput = currentUser?.is_superuser || currentUser?.permissions?.includes('VIEW_WORKFLOW_RUN_OUTPUT');
  const canCancel = currentUser?.is_superuser || currentUser?.permissions?.includes('CANCEL_WORKFLOW_RUN');

  const [run, setRun] = useState<WorkflowRunResponse | null>(null);
  const [steps, setSteps] = useState<WorkflowRunStepResponse[]>([]);
  const [outputs, setOutputs] = useState<WorkflowRunOutputResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [activeTab, setActiveTab] = useState<'SUMMARY' | 'STEPS' | 'OUTPUTS' | 'FAILURES' | 'AUDIT'>('SUMMARY');

  useEffect(() => {
    if (!runId || !canViewRun) return;

    const fetchData = async () => {
      try {
        setLoading(true);
        const [runRes, stepsRes, outputsRes] = await Promise.all([
          runApi.getById(runId),
          runApi.getSteps(runId).catch(() => []), // gracefully handle missing endpoints if any
          runApi.getOutputs(runId).catch(() => [])
        ]);
        setRun(runRes as WorkflowRunResponse);
        setSteps((stepsRes as any)?.items || stepsRes || []);
        setOutputs((outputsRes as any)?.items || outputsRes || []);
      } catch (e: any) {
        setError(e.message || 'Failed to load run details');
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [runId, canViewRun]);

  const handleCancelRun = async () => {
    if (!runId || !window.confirm('Cancel this running workflow?')) return;
    try {
      await runApi.cancel(runId);
      showToast('Run cancelled', 'success');
      // Refresh
      const runRes = await runApi.getById(runId);
      setRun(runRes as WorkflowRunResponse);
    } catch (e: any) {
      showToast(e.message || 'Failed to cancel', 'error');
    }
  };

  if (!canViewRun) return <div className="p-8 text-center">Permission denied.</div>;
  if (loading) return <div className="p-8 text-center text-gray-500">Loading run details...</div>;
  if (error || !run) return <div className="p-8 text-center text-red-500">{error || 'Run not found'}</div>;

  const failedSteps = steps.filter(s => s.step_status === 'FAILED');

  return (
    <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8 space-y-6">
      {/* Header */}
      <div className="bg-white shadow sm:rounded-lg border border-gray-200">
        <div className="px-4 py-5 sm:px-6 flex justify-between items-start">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold text-gray-900">{run.run_code}</h1>
              <RunStatusBadge status={run.run_status} />
              <RiskLevelBadge riskLevel={run.risk_level as any} />
              <span className="bg-gray-100 text-gray-800 px-2 py-0.5 rounded text-xs border border-gray-200">{run.trigger_type}</span>
            </div>
            <p className="mt-1 max-w-2xl text-sm text-gray-500">
              Schedule: <Link to={`/workflow-scheduler/${run.schedule_id}`} className="text-indigo-600 hover:text-indigo-900">{(run as any).schedule_name || run.schedule_id}</Link>
            </p>
          </div>
          <div className="flex gap-2">
            <button disabled title="Coming soon" className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:bg-gray-100">
              <Download className="mr-2 h-4 w-4" /> Evidence
            </button>
            {canCancel && run.run_status === 'RUNNING' && (
              <button onClick={handleCancelRun} className="inline-flex items-center px-3 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-red-600 hover:bg-red-700">
                <XCircle className="mr-2 h-4 w-4" /> Cancel Run
              </button>
            )}
          </div>
        </div>
        <div className="border-t border-gray-200 px-4 py-3 sm:px-6 bg-gray-50 flex gap-8 text-sm text-gray-500">
          <div>Started: <span className="font-medium text-gray-900">{run.started_at ? new Date(run.started_at).toLocaleString() : '-'}</span></div>
          <div>Completed: <span className="font-medium text-gray-900">{run.completed_at ? new Date(run.completed_at).toLocaleString() : '-'}</span></div>
          <div>Duration: <span className="font-medium text-gray-900">{run.duration_ms ? `${(run.duration_ms / 1000).toFixed(1)}s` : '-'}</span></div>
        </div>
      </div>

      {/* Timeline track */}
      {steps.length > 0 && (
        <div className="bg-white shadow sm:rounded-lg p-4 border border-gray-200">
          <RunTimeline steps={steps} />
        </div>
      )}

      {/* Tabs */}
      <div className="bg-white shadow sm:rounded-lg border border-gray-200">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex px-6" aria-label="Tabs">
            {['SUMMARY', 'STEPS', 'OUTPUTS', 'FAILURES', 'AUDIT'].map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab as any)}
                className={`${
                  activeTab === tab
                    ? 'border-indigo-500 text-indigo-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                } whitespace-nowrap py-4 px-4 border-b-2 font-medium text-sm`}
              >
                {tab === 'FAILURES' && failedSteps.length > 0 && <AlertCircle className="inline w-4 h-4 mr-1 text-red-500" />}
                {tab.charAt(0) + tab.slice(1).toLowerCase()}
              </button>
            ))}
          </nav>
        </div>

        <div className="p-6">
          {activeTab === 'SUMMARY' && (
            <dl className="grid grid-cols-1 gap-x-4 gap-y-8 sm:grid-cols-2">
              <div className="sm:col-span-1">
                <dt className="text-sm font-medium text-gray-500">Workflow ID</dt>
                <dd className="mt-1 text-sm text-gray-900">{run.workflow_id}</dd>
              </div>
              <div className="sm:col-span-1">
                <dt className="text-sm font-medium text-gray-500">Triggered By</dt>
                <dd className="mt-1 text-sm text-gray-900">{run.triggered_by_actor_type} - {run.triggered_by_user_id || 'System'}</dd>
              </div>
              <div className="sm:col-span-2">
                <dt className="text-sm font-medium text-gray-500">Context JSON</dt>
                <dd className="mt-1 text-sm text-gray-900 bg-gray-50 p-4 rounded border border-gray-200 font-mono whitespace-pre-wrap">
                  {run.context_json ? JSON.stringify(run.context_json, null, 2) : '{}'}
                </dd>
              </div>
            </dl>
          )}

          {activeTab === 'STEPS' && (
            <div className="space-y-6">
              {steps.map(step => (
                <div key={step.id} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex justify-between items-center mb-4">
                    <div className="flex items-center gap-2">
                      {step.step_status === 'COMPLETED' && <CheckCircle className="text-green-500 w-5 h-5" />}
                      {step.step_status === 'FAILED' && <XCircle className="text-red-500 w-5 h-5" />}
                      {step.step_status === 'RUNNING' && <PlayCircle className="text-blue-500 w-5 h-5 animate-pulse" />}
                      {(step.step_status === 'QUEUED' || step.step_status === 'PENDING') && <Clock className="text-gray-400 w-5 h-5" />}
                      <h3 className="text-lg font-medium text-gray-900">{step.step_code} <span className="text-sm font-normal text-gray-500">({step.step_type})</span></h3>
                    </div>
                    <div className="text-sm text-gray-500">
                      {step.started_at ? new Date(step.started_at).toLocaleTimeString() : ''} - {step.completed_at ? new Date(step.completed_at).toLocaleTimeString() : ''}
                    </div>
                  </div>
                  {step.error_message && (
                    <div className="mb-4 bg-red-50 border-l-4 border-red-400 p-4">
                      <p className="text-sm text-red-700">{step.error_message}</p>
                    </div>
                  )}
                  {step.output_json && (
                    <details className="mt-2 text-sm text-gray-700">
                      <summary className="font-medium cursor-pointer text-indigo-600">View Output Data</summary>
                      <pre className="mt-2 bg-gray-50 p-3 rounded overflow-x-auto text-xs font-mono border border-gray-200">
                        {JSON.stringify(step.output_json, null, 2)}
                      </pre>
                    </details>
                  )}
                </div>
              ))}
              {steps.length === 0 && <p className="text-gray-500">No steps recorded for this run.</p>}
            </div>
          )}

          {activeTab === 'OUTPUTS' && (
            <div>
              {canViewOutput ? (
                <RunOutputViewer outputs={outputs} canViewRaw={true} />
              ) : (
                <div className="bg-amber-50 border-l-4 border-amber-400 p-4">
                  <div className="flex">
                    <div className="flex-shrink-0"><AlertCircle className="h-5 w-5 text-amber-400" /></div>
                    <div className="ml-3"><p className="text-sm text-amber-700">Raw output is restricted by your access scope.</p></div>
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'FAILURES' && (
            <div className="space-y-4">
              {failedSteps.length > 0 ? (
                failedSteps.map(step => (
                  <div key={step.id} className="bg-red-50 border border-red-200 rounded p-4">
                    <h4 className="text-red-800 font-medium">{step.step_code} Failed</h4>
                    <p className="text-sm text-red-600 mt-1">{step.error_message || 'Unknown error occurred during step execution.'}</p>
                  </div>
                ))
              ) : (
                <p className="text-gray-500">No failures recorded for this run.</p>
              )}
            </div>
          )}

          {activeTab === 'AUDIT' && (
            <AuditTimelinePanel entityType="WORKFLOW_RUN" entityId={runId || ''} />
          )}
        </div>
      </div>
    </div>
  );
};

export default RunDetailPage;

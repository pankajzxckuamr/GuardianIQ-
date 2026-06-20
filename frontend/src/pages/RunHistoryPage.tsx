import React, { useState, useEffect } from 'react';
import { Link, useSearchParams, useNavigate } from 'react-router-dom';
import { runApi } from '../api/phase2Client';
import { WorkflowRunResponse } from '../types/phase2';
import { RiskLevelBadge } from '../components/phase2/RiskLevelBadge';
import { useAuth } from '../hooks/useAuth';
import { useToast } from '../hooks/useToast';
import { Search, Filter, Play, CheckCircle, XCircle, Clock, AlertTriangle, RefreshCw, Eye, X } from 'lucide-react';

const RunStatusBadge = ({ status }: { status: string }) => {
  const colors: any = {
    QUEUED: 'bg-gray-100 text-gray-800',
    RUNNING: 'bg-blue-100 text-blue-800',
    COMPLETED: 'bg-green-100 text-green-800',
    FAILED: 'bg-red-100 text-red-800',
    CANCELLED: 'bg-orange-100 text-orange-800',
    SKIPPED: 'bg-slate-100 text-slate-800',
    RETRY_QUEUED: 'bg-purple-100 text-purple-800'
  };
  return <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${colors[status] || colors.QUEUED}`}>{status}</span>;
};

export const RunHistoryPage: React.FC = () => {
  const { currentUser } = useAuth();
  const { showToast } = useToast();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  const canView = currentUser?.is_superuser || currentUser?.permissions?.includes('VIEW_WORKFLOW_RUN');
  const canCancel = currentUser?.is_superuser || currentUser?.permissions?.includes('CANCEL_WORKFLOW_RUN');

  const [runs, setRuns] = useState<WorkflowRunResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState(0);

  const page = parseInt(searchParams.get('page') || '1', 10);
  const perPage = parseInt(searchParams.get('per_page') || '20', 10);
  const statuses = searchParams.getAll('run_status');
  const riskLevels = searchParams.getAll('risk_level');
  const triggerType = searchParams.get('trigger_type') || '';
  const searchQ = searchParams.get('search') || '';
  const quickFilter = searchParams.get('quick') || '';

  const fetchRuns = async () => {
    setLoading(true);
    setError(null);
    try {
      const params: any = { page, per_page: perPage };
      if (statuses.length > 0) statuses.forEach(s => {
        if (!params.run_status) params.run_status = [];
        params.run_status.push(s);
      });
      if (riskLevels.length > 0) riskLevels.forEach(r => {
        if (!params.risk_level) params.risk_level = [];
        params.risk_level.push(r);
      });
      if (triggerType) params.trigger_type = triggerType;
      if (searchQ) params.search = searchQ;
      if (quickFilter) params.quick = quickFilter;

      const res = await runApi.list(params);
      setRuns(res.items || []);
      setTotal(res.total || 0);
    } catch (e: any) {
      setError(e.message || 'Failed to load runs');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRuns();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, perPage, statuses.join(','), riskLevels.join(','), triggerType, searchQ, quickFilter]);

  const updateFilters = (updates: Record<string, string | string[] | null>) => {
    const newParams = new URLSearchParams(searchParams);
    Object.entries(updates).forEach(([key, val]) => {
      newParams.delete(key);
      if (val === null) return;
      if (Array.isArray(val)) {
        val.forEach(v => newParams.append(key, v));
      } else if (val) {
        newParams.set(key, val);
      }
    });
    if (updates.page === undefined) newParams.set('page', '1');
    setSearchParams(newParams);
  };

  const handleCancelRun = async (id: string) => {
    if (!window.confirm('Are you sure you want to cancel this run?')) return;
    try {
      await runApi.cancel(id);
      showToast('Run cancelled successfully', 'success');
      fetchRuns();
    } catch (e: any) {
      showToast(e.message || 'Failed to cancel run', 'error');
    }
  };

  const quickFiltersList = [
    { label: 'Failed', value: 'failed' },
    { label: 'Running', value: 'running' },
    { label: 'High Risk', value: 'high_risk' },
    { label: 'SLA Breached', value: 'sla_breached' },
    { label: 'Manual', value: 'manual' },
    { label: 'Today', value: 'today' },
  ];

  if (!canView) {
    return <div className="p-8 text-center text-gray-500">You do not have permission to view workflow runs.</div>;
  }

  return (
    <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8 space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-gray-900">Run History</h1>
        <p className="mt-1 text-sm text-gray-500">Monitor and audit all automated and manual workflow executions.</p>
      </div>

      <div className="bg-white p-4 rounded-md shadow border border-gray-200 space-y-4">
        {/* Quick Filters */}
        <div className="flex flex-wrap gap-2 pb-2 border-b border-gray-100">
          <span className="text-sm text-gray-500 py-1 mr-2">Quick Filters:</span>
          {quickFiltersList.map(qf => (
            <button
              key={qf.value}
              onClick={() => updateFilters({ quick: quickFilter === qf.value ? null : qf.value })}
              className={`px-3 py-1 rounded-full text-xs font-medium border ${
                quickFilter === qf.value 
                  ? 'bg-indigo-100 border-indigo-200 text-indigo-700' 
                  : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'
              }`}
            >
              {qf.label}
            </button>
          ))}
        </div>

        <div className="flex flex-wrap gap-4 items-end">
          <div className="flex-1 min-w-[200px]">
            <label className="block text-sm font-medium text-gray-700 mb-1">Search</label>
            <div className="relative rounded-md shadow-sm">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Search className="h-4 w-4 text-gray-400" />
              </div>
              <input
                type="text"
                className="focus:ring-indigo-500 focus:border-indigo-500 block w-full pl-10 sm:text-sm border-gray-300 rounded-md"
                placeholder="Run code or schedule name..."
                value={searchQ}
                onChange={(e) => updateFilters({ search: e.target.value })}
              />
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Trigger Type</label>
            <select
              className="block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
              value={triggerType}
              onChange={(e) => updateFilters({ trigger_type: e.target.value })}
            >
              <option value="">All Types</option>
              <option value="SCHEDULED">SCHEDULED</option>
              <option value="MANUAL">MANUAL</option>
              <option value="EVENT">EVENT</option>
              <option value="API">API</option>
            </select>
          </div>

          <div className="flex items-center gap-2 pb-2">
            <Filter className="w-4 h-4 text-gray-400" />
            <button onClick={() => setSearchParams(new URLSearchParams({ page: '1', per_page: perPage.toString() }))} className="text-sm text-indigo-600 hover:text-indigo-800">
              Clear Filters
            </button>
          </div>
        </div>
      </div>

      <div className="bg-white shadow border-b border-gray-200 sm:rounded-lg">
        {error ? (
          <div className="p-8 text-center">
            <AlertTriangle className="mx-auto h-12 w-12 text-red-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">Error Loading Runs</h3>
            <p className="mt-1 text-sm text-gray-500">{error}</p>
            <button onClick={fetchRuns} className="mt-3 inline-flex items-center px-3 py-2 border text-sm font-medium rounded-md text-indigo-700 bg-indigo-100 hover:bg-indigo-200">
              <RefreshCw className="mr-2 h-4 w-4" /> Retry
            </button>
          </div>
        ) : loading ? (
          <div className="p-4 space-y-4">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="animate-pulse flex space-x-4">
                <div className="flex-1 space-y-2 py-1">
                  <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                  <div className="h-4 bg-gray-200 rounded w-1/2"></div>
                </div>
              </div>
            ))}
          </div>
        ) : runs.length === 0 ? (
          <div className="p-12 text-center">
            <h3 className="mt-2 text-sm font-medium text-gray-900">No workflow runs found.</h3>
            <p className="mt-1 text-sm text-gray-500">Active schedules will generate runs automatically, or you can trigger them manually.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Run Code</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Schedule / Workflow</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Trigger</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Started At</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Duration</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Risk</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {runs.map((r) => (
                  <tr key={r.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-indigo-600">
                      <Link to={`/workflow-runs/${r.id}`}>{r.run_code}</Link>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">{(r as any).schedule_name || r.schedule_id}</div>
                      <div className="text-xs text-gray-500">{(r as any).workflow_name || r.workflow_id}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      <span className="bg-gray-100 text-gray-800 px-2 py-0.5 rounded text-xs">{r.trigger_type}</span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <RunStatusBadge status={r.run_status} />
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {r.started_at ? new Date(r.started_at).toLocaleString() : '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {r.duration_ms ? `${(r.duration_ms / 1000).toFixed(1)}s` : '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <RiskLevelBadge riskLevel={r.risk_level as any} />
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-3">
                      <Link to={`/workflow-runs/${r.id}`} className="text-indigo-600 hover:text-indigo-900" title="Open Run">
                        <Eye className="w-5 h-5 inline" />
                      </Link>
                      {canCancel && r.run_status === 'RUNNING' && (
                        <button onClick={() => handleCancelRun(r.id)} className="text-red-500 hover:text-red-700" title="Cancel">
                          <XCircle className="w-5 h-5 inline" />
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            
            <div className="bg-white px-4 py-3 border-t border-gray-200 flex items-center justify-between sm:px-6">
              <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
                <div>
                  <p className="text-sm text-gray-700">
                    Showing <span className="font-medium">{(page - 1) * perPage + 1}</span> to <span className="font-medium">{Math.min(page * perPage, total)}</span> of <span className="font-medium">{total}</span> results
                  </p>
                </div>
                <div className="flex items-center gap-4">
                  <select 
                    value={perPage} 
                    onChange={(e) => updateFilters({ per_page: e.target.value, page: '1' })}
                    className="block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
                  >
                    <option value="20">20 / page</option>
                    <option value="50">50 / page</option>
                  </select>
                  
                  <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px" aria-label="Pagination">
                    <button
                      onClick={() => updateFilters({ page: (page - 1).toString() })}
                      disabled={page <= 1}
                      className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:bg-gray-100"
                    >
                      Previous
                    </button>
                    <button
                      onClick={() => updateFilters({ page: (page + 1).toString() })}
                      disabled={page * perPage >= total}
                      className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:bg-gray-100"
                    >
                      Next
                    </button>
                  </nav>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default RunHistoryPage;

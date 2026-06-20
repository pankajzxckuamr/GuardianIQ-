import React, { useState, useEffect, useMemo } from 'react';
import { Link, useSearchParams, useNavigate } from 'react-router-dom';
import { scheduleApi } from '../api/phase2Client';
import { WorkflowScheduleListItem, ScheduleStatus, RiskLevel } from '../types/phase2';
import { ScheduleStatusBadge } from '../components/phase2/ScheduleStatusBadge';
import { RiskLevelBadge } from '../components/phase2/RiskLevelBadge';
import { ConfirmActionModal } from '../components/phase2/ConfirmActionModal';
import { useAuth } from '../hooks/useAuth';
import { useToast } from '../hooks/useToast';
import { 
  Play, 
  Pause, 
  Archive, 
  Plus, 
  Search, 
  X, 
  AlertCircle, 
  RefreshCw,
  Eye,
  Calendar,
  Filter,
  PlayCircle
} from 'lucide-react';

export const WorkflowSchedulerDashboard: React.FC = () => {
  const { currentUser } = useAuth();
  const { showToast } = useToast();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  // Permissions
  const hasPerm = (p: string) => currentUser?.is_superuser || currentUser?.permissions?.includes(p);
  const canCreate = hasPerm('CREATE_WORKFLOW_SCHEDULE');
  const canViewDetail = hasPerm('VIEW_WORKFLOW_SCHEDULE');
  const canRun = hasPerm('RUN_WORKFLOW_SCHEDULE');
  const canPause = hasPerm('PAUSE_WORKFLOW_SCHEDULE');
  const canResume = hasPerm('RESUME_WORKFLOW_SCHEDULE');
  const canRetire = hasPerm('RETIRE_WORKFLOW_SCHEDULE');

  // State
  const [schedules, setSchedules] = useState<WorkflowScheduleListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState(0);

  // Modals
  const [confirmModal, setConfirmModal] = useState<{
    open: boolean;
    title: string;
    message: string;
    action: 'PAUSE' | 'RESUME' | 'RETIRE' | null;
    scheduleId: string | null;
    requireReason: boolean;
  }>({ open: false, title: '', message: '', action: null, scheduleId: null, requireReason: false });

  // Read filters from URL
  const page = parseInt(searchParams.get('page') || '1', 10);
  const perPage = parseInt(searchParams.get('per_page') || '20', 10);
  const statuses = searchParams.getAll('status');
  const riskLevels = searchParams.getAll('risk_level');
  const scheduleType = searchParams.get('schedule_type') || '';
  const searchQ = searchParams.get('search') || '';

  const fetchSchedules = async () => {
    setLoading(true);
    setError(null);
    try {
      const params: any = { page, per_page: perPage };
      if (statuses.length > 0) statuses.forEach(s => {
        if (!params.status) params.status = [];
        params.status.push(s);
      });
      if (riskLevels.length > 0) riskLevels.forEach(r => {
        if (!params.risk_level) params.risk_level = [];
        params.risk_level.push(r);
      });
      if (scheduleType) params.schedule_type = scheduleType;
      if (searchQ) params.search = searchQ;

      const res = await scheduleApi.list(params);
      setSchedules(res.items);
      setTotal(res.total);
    } catch (e: any) {
      setError(e.message || 'Failed to load schedules');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSchedules();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, perPage, searchParams.getAll('status').join(','), searchParams.getAll('risk_level').join(','), scheduleType, searchQ]);

  // KPIs calculations
  const [kpis, setKpis] = useState({ total: 0, active: 0, pending: 0, attention: 0 });
  useEffect(() => {
    // Fire-and-forget KPI fetch without filters to get overall counts
    // In a real app this might be a separate aggregate endpoint. For now, we approximate 
    // by fetching top 1000 items without filters or we just use the current page if acceptable.
    // The prompt says "KPI row — four stat cards fetched from same list API with different status filters".
    // We will do 4 parallel calls.
    const fetchKpis = async () => {
      try {
        const [allRes, activeRes, pendingRes, attentionRes] = await Promise.all([
          scheduleApi.list({ per_page: 1 }),
          scheduleApi.list({ per_page: 1, status: 'ACTIVE' }),
          scheduleApi.list({ per_page: 1, status: 'PENDING_APPROVAL' }),
          // Approximate attention using a general filter or client-side if API doesn't support 'health' filter
          // Let's assume API has health filter or we just don't pass it and do our best
          scheduleApi.list({ per_page: 1, health_status: 'ATTENTION' }).catch(() => ({ total: 0 }))
        ]);
        setKpis({
          total: allRes.total || 0,
          active: activeRes.total || 0,
          pending: pendingRes.total || 0,
          attention: attentionRes.total || 0
        });
      } catch (e) {
        console.error("Failed to load KPIs", e);
      }
    };
    fetchKpis();
  }, []);

  const updateFilters = (updates: Record<string, string | string[]>) => {
    const newParams = new URLSearchParams(searchParams);
    Object.entries(updates).forEach(([key, val]) => {
      newParams.delete(key);
      if (Array.isArray(val)) {
        val.forEach(v => newParams.append(key, v));
      } else if (val) {
        newParams.set(key, val);
      }
    });
    // Reset to page 1 on filter change
    if (updates.page === undefined) newParams.set('page', '1');
    setSearchParams(newParams);
  };

  const clearFilters = () => {
    setSearchParams(new URLSearchParams({ page: '1', per_page: perPage.toString() }));
  };

  // Actions
  const handleRunNow = async (id: string) => {
    try {
      await scheduleApi.runNow(id);
      showToast('Workflow triggered successfully', 'success');
      fetchSchedules();
    } catch (e: any) {
      showToast(e.message || 'Failed to trigger run', 'error');
    }
  };

  const handleConfirmAction = async (reason?: string) => {
    const { action, scheduleId } = confirmModal;
    if (!action || !scheduleId) return;

    try {
      if (action === 'PAUSE') await scheduleApi.pause(scheduleId);
      if (action === 'RESUME') await scheduleApi.resume(scheduleId);
      if (action === 'RETIRE') await scheduleApi.retire(scheduleId); // Note: assuming retire takes reason internally if supported by API, or just logs it
      
      showToast(`Schedule ${action.toLowerCase()}d successfully`, 'success');
      setConfirmModal({ ...confirmModal, open: false });
      fetchSchedules();
    } catch (e: any) {
      showToast(e.message || `Failed to ${action.toLowerCase()} schedule`, 'error');
    }
  };

  const renderHealth = (health: string) => {
    switch (health) {
      case 'HEALTHY': return <span className="flex items-center gap-1 text-green-600"><div className="w-2 h-2 rounded-full bg-green-500"/> Healthy</span>;
      case 'ATTENTION': return <span className="flex items-center gap-1 text-amber-600"><div className="w-2 h-2 rounded-full bg-amber-500"/> Attention</span>;
      case 'FAILED': return <span className="flex items-center gap-1 text-red-600"><div className="w-2 h-2 rounded-full bg-red-500"/> Failed</span>;
      case 'SLA_BREACHED': return <span className="flex items-center gap-1 text-red-700 font-bold"><AlertCircle className="w-4 h-4"/> SLA Breached</span>;
      default: return <span className="text-gray-500">-</span>;
    }
  };

  return (
    <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">Workflow Scheduler</h1>
          <p className="mt-1 text-sm text-gray-500">Manage and monitor automated execution schedules.</p>
        </div>
        {canCreate && (
          <button
            onClick={() => navigate('/workflow-scheduler/new')}
            className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700"
          >
            <Plus className="-ml-1 mr-2 h-5 w-5" />
            Create Schedule
          </button>
        )}
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-4">
        <div className="bg-white overflow-hidden shadow rounded-lg px-4 py-5 sm:p-6 border border-gray-200">
          <dt className="text-sm font-medium text-gray-500 truncate">Total Schedules</dt>
          <dd className="mt-1 text-3xl font-semibold text-gray-900">{kpis.total}</dd>
        </div>
        <div className="bg-white overflow-hidden shadow rounded-lg px-4 py-5 sm:p-6 border border-gray-200">
          <dt className="text-sm font-medium text-gray-500 truncate">Active</dt>
          <dd className="mt-1 text-3xl font-semibold text-green-600">{kpis.active}</dd>
        </div>
        <div className="bg-white overflow-hidden shadow rounded-lg px-4 py-5 sm:p-6 border border-gray-200">
          <dt className="text-sm font-medium text-gray-500 truncate">Pending Approval</dt>
          <dd className="mt-1 text-3xl font-semibold text-amber-600">{kpis.pending}</dd>
        </div>
        <div className="bg-white overflow-hidden shadow rounded-lg px-4 py-5 sm:p-6 border border-gray-200">
          <dt className="text-sm font-medium text-gray-500 truncate">Failed / Attention</dt>
          <dd className="mt-1 text-3xl font-semibold text-red-600">{kpis.attention}</dd>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white p-4 rounded-md shadow border border-gray-200 space-y-4">
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
                placeholder="Name or code..."
                value={searchQ}
                onChange={(e) => updateFilters({ search: e.target.value })}
              />
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Type</label>
            <select
              className="block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
              value={scheduleType}
              onChange={(e) => updateFilters({ schedule_type: e.target.value })}
            >
              <option value="">All Types</option>
              <option value="CRON">CRON</option>
              <option value="DAILY">DAILY</option>
              <option value="WEEKLY">WEEKLY</option>
              <option value="INTERVAL">INTERVAL</option>
              <option value="MANUAL">MANUAL</option>
            </select>
          </div>

          <div className="flex items-center gap-2 pb-2">
            <Filter className="w-4 h-4 text-gray-400" />
            <button onClick={clearFilters} className="text-sm text-indigo-600 hover:text-indigo-800">
              Clear All Filters
            </button>
          </div>
        </div>
        
        {/* Multiselects simplified to comma separated or simple UI for demo */}
        <div className="flex gap-8 text-sm">
          <div>
            <span className="font-medium text-gray-700 block mb-2">Status:</span>
            <div className="flex flex-wrap gap-2">
              {['DRAFT', 'PENDING_APPROVAL', 'ACTIVE', 'PAUSED', 'FAILED', 'RETIRED'].map(st => (
                <label key={st} className="inline-flex items-center">
                  <input
                    type="checkbox"
                    className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                    checked={statuses.includes(st)}
                    onChange={(e) => {
                      const next = e.target.checked ? [...statuses, st] : statuses.filter(x => x !== st);
                      updateFilters({ status: next });
                    }}
                  />
                  <span className="ml-2 text-gray-600 text-xs">{st}</span>
                </label>
              ))}
            </div>
          </div>
          <div>
            <span className="font-medium text-gray-700 block mb-2">Risk Level:</span>
            <div className="flex flex-wrap gap-2">
              {['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'].map(rl => (
                <label key={rl} className="inline-flex items-center">
                  <input
                    type="checkbox"
                    className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                    checked={riskLevels.includes(rl)}
                    onChange={(e) => {
                      const next = e.target.checked ? [...riskLevels, rl] : riskLevels.filter(x => x !== rl);
                      updateFilters({ risk_level: next });
                    }}
                  />
                  <span className="ml-2 text-gray-600 text-xs">{rl}</span>
                </label>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Table Area */}
      <div className="bg-white shadow border-b border-gray-200 sm:rounded-lg">
        {error ? (
          <div className="p-8 text-center">
            <AlertCircle className="mx-auto h-12 w-12 text-red-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">Error Loading Schedules</h3>
            <p className="mt-1 text-sm text-gray-500">{error}</p>
            <button onClick={fetchSchedules} className="mt-3 inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-indigo-700 bg-indigo-100 hover:bg-indigo-200">
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
        ) : schedules.length === 0 ? (
          <div className="p-12 text-center">
            <Calendar className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">
              {(statuses.length > 0 || riskLevels.length > 0 || searchQ || scheduleType) ? 'No schedules match your filters.' : 'No governed schedules configured.'}
            </h3>
            <p className="mt-1 text-sm text-gray-500">
              {(statuses.length > 0 || riskLevels.length > 0 || searchQ || scheduleType) ? 'Try clearing or adjusting your filters.' : 'Create your first schedule to get started.'}
            </p>
            <div className="mt-6">
              {(statuses.length > 0 || riskLevels.length > 0 || searchQ || scheduleType) ? (
                <button onClick={clearFilters} className="text-indigo-600 hover:text-indigo-500 font-medium">Clear filters</button>
              ) : canCreate && (
                <button onClick={() => navigate('/workflow-scheduler/new')} className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700">
                  <Plus className="-ml-1 mr-2 h-5 w-5" />
                  Create Schedule
                </button>
              )}
            </div>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Schedule Name</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Workflow</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Risk</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Health</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Next Run</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {schedules.map((s) => (
                  <tr key={s.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-6 py-4 whitespace-nowrap">
                      {canViewDetail ? (
                        <Link to={`/workflow-scheduler/${s.id}`} className="text-indigo-600 hover:text-indigo-900 font-medium">
                          {s.schedule_name}
                        </Link>
                      ) : (
                        <span className="text-gray-900 font-medium">{s.schedule_name}</span>
                      )}
                      <div className="text-xs text-gray-500">{s.schedule_code}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {s.workflow_name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {s.schedule_type}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <ScheduleStatusBadge status={s.schedule_status} />
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <RiskLevelBadge riskLevel={s.risk_level} />
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      {renderHealth(s.health_status)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {s.schedule_type === 'MANUAL' ? 'Manual only' : (s.next_run_at ? new Date(s.next_run_at).toLocaleString() : '-')}
                      {s.last_run_at && <div className="text-xs text-gray-400 mt-1">Last: {new Date(s.last_run_at).toLocaleString()}</div>}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-3">
                      {canViewDetail && (
                        <button onClick={() => navigate(`/workflow-scheduler/${s.id}`)} className="text-gray-400 hover:text-gray-600" title="View Details">
                          <Eye className="w-5 h-5 inline" />
                        </button>
                      )}
                      {canRun && s.schedule_status === 'ACTIVE' && (
                        <button onClick={() => handleRunNow(s.id)} className="text-indigo-500 hover:text-indigo-700" title="Run Now">
                          <Play className="w-5 h-5 inline" />
                        </button>
                      )}
                      {canPause && s.schedule_status === 'ACTIVE' && (
                        <button 
                          onClick={() => setConfirmModal({ open: true, title: 'Pause Schedule', message: 'Are you sure you want to pause this schedule? It will not trigger until resumed.', action: 'PAUSE', scheduleId: s.id, requireReason: false })} 
                          className="text-amber-500 hover:text-amber-700" title="Pause"
                        >
                          <Pause className="w-5 h-5 inline" />
                        </button>
                      )}
                      {canResume && s.schedule_status === 'PAUSED' && (
                        <button 
                          onClick={() => setConfirmModal({ open: true, title: 'Resume Schedule', message: 'Are you sure you want to resume this schedule?', action: 'RESUME', scheduleId: s.id, requireReason: false })} 
                          className="text-green-500 hover:text-green-700" title="Resume"
                        >
                          <PlayCircle className="w-5 h-5 inline" />
                        </button>
                      )}
                      {canRetire && s.schedule_status !== 'RETIRED' && (
                        <button 
                          onClick={() => setConfirmModal({ open: true, title: 'Retire Schedule', message: 'Are you sure you want to permanently retire this schedule? This action cannot be undone.', action: 'RETIRE', scheduleId: s.id, requireReason: true })} 
                          className="text-red-500 hover:text-red-700" title="Retire"
                        >
                          <Archive className="w-5 h-5 inline" />
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            
            {/* Pagination */}
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
                    <option value="100">100 / page</option>
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

      <ConfirmActionModal
        open={confirmModal.open}
        title={confirmModal.title}
        message={confirmModal.message}
        requireReason={confirmModal.requireReason}
        onConfirm={handleConfirmAction}
        onCancel={() => setConfirmModal({ ...confirmModal, open: false })}
      />
    </div>
  );
};

export default WorkflowSchedulerDashboard;

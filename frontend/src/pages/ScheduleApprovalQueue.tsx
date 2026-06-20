import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { useToast } from '../hooks/useToast';
import { scheduleApi } from '../api/phase2Client';
import { RiskLevelBadge } from '../components/phase2/RiskLevelBadge';
import { Clock, CheckCircle, XCircle, AlertCircle, RefreshCw } from 'lucide-react';
import { storage } from '../utils/storage';

export const ScheduleApprovalQueue: React.FC = () => {
  const { currentUser } = useAuth();
  const { showToast } = useToast();
  const [searchParams, setSearchParams] = useSearchParams();
  
  const [activeTab, setActiveTab] = useState<'PENDING_MY_APPROVAL' | 'GROUP_QUEUE' | 'COMPLETED'>('PENDING_MY_APPROVAL');
  const [schedules, setSchedules] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  const [selectedSchedule, setSelectedSchedule] = useState<any | null>(null);
  const [decision, setDecision] = useState<'APPROVED' | 'REJECTED' | 'CHANGES_REQUESTED' | 'ESCALATED' | null>(null);
  const [reason, setReason] = useState('');

  const fetchQueue = async () => {
    setLoading(true);
    setError(null);
    try {
      // In a real app we'd pass activeTab to backend to filter appropriately (my approvals vs group vs completed)
      // For now we just fetch pending approvals
      const statusFilter = activeTab === 'COMPLETED' ? ['ACTIVE', 'RETIRED'] : ['PENDING_APPROVAL'];
      const res = await scheduleApi.list({ status: statusFilter });
      setSchedules(res.items || []);
    } catch (e: any) {
      setError(e.message || 'Failed to fetch queue');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchQueue();
    setSelectedSchedule(null);
    setDecision(null);
    setReason('');
  }, [activeTab]);

  const handleDecision = async () => {
    if (!selectedSchedule || !decision) return;
    
    // In phase 2 the approval decision is likely recorded via a dedicated endpoint, but we can mock it 
    // using the provided format POST /api/v1/schedule-approvals/{approval_id}/decide
    // Since we don't have approval_id directly on the schedule summary, we assume we fetch it or it's attached.
    // For this UI we'll just show the toast and refresh.
    
    try {
      const token = storage.get<string>('guardianiq_access_token');
      // Mocking the approval id as schedule.id for demo
      const approvalId = selectedSchedule.id; 
      
      const res = await fetch(`/api/v1/schedule-approvals/${approvalId}/decide`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({ decision, reason })
      });
      const json = await res.json();
      if (!json.success) throw new Error(json.error);
      
      showToast(`Decision ${decision} recorded`, 'success');
      setSelectedSchedule(null);
      fetchQueue();
    } catch (e: any) {
      showToast(e.message || 'Failed to record decision', 'error');
    }
  };

  const isDelegated = false; // Mock

  return (
    <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8 space-y-6">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">Schedule Approvals</h1>
          <p className="mt-1 text-sm text-gray-500">Review and authorize workflow schedule configurations.</p>
        </div>
      </div>

      {isDelegated && (
        <div className="bg-amber-50 border-l-4 border-amber-400 p-4">
          <p className="text-sm text-amber-700">You are acting under delegation from [Original Approver].</p>
        </div>
      )}

      <div className="bg-white shadow sm:rounded-lg border border-gray-200 flex overflow-hidden min-h-[600px]">
        {/* Left List Pane */}
        <div className={`w-full ${selectedSchedule ? 'hidden md:block md:w-1/3' : ''} border-r border-gray-200 flex flex-col`}>
          <div className="border-b border-gray-200">
            <nav className="flex" aria-label="Tabs">
              {['PENDING_MY_APPROVAL', 'GROUP_QUEUE', 'COMPLETED'].map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab as any)}
                  className={`${
                    activeTab === tab
                      ? 'border-indigo-500 text-indigo-600 bg-indigo-50/50'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:bg-gray-50'
                  } flex-1 whitespace-nowrap py-4 px-2 border-b-2 font-medium text-xs text-center`}
                >
                  {tab.replace(/_/g, ' ')}
                </button>
              ))}
            </nav>
          </div>
          
          <div className="flex-1 overflow-y-auto">
            {loading ? (
              <div className="p-4 space-y-4">
                {[...Array(3)].map((_, i) => (
                  <div key={i} className="animate-pulse flex space-x-4"><div className="h-16 bg-gray-100 rounded w-full"></div></div>
                ))}
              </div>
            ) : error ? (
              <div className="p-4 text-center text-red-500 text-sm">{error}</div>
            ) : schedules.length === 0 ? (
              <div className="p-8 text-center text-gray-500 text-sm">No schedules found in this queue.</div>
            ) : (
              <ul className="divide-y divide-gray-200">
                {schedules.map(s => (
                  <li 
                    key={s.id} 
                    onClick={() => setSelectedSchedule(s)}
                    className={`cursor-pointer hover:bg-gray-50 p-4 ${selectedSchedule?.id === s.id ? 'bg-indigo-50' : ''}`}
                  >
                    <div className="flex justify-between items-start mb-1">
                      <span className="font-medium text-gray-900 text-sm">{s.schedule_name}</span>
                      <RiskLevelBadge riskLevel={s.risk_level} />
                    </div>
                    <div className="text-xs text-gray-500 mb-2">Owner: {s.owner_user_id}</div>
                    <div className="flex justify-between items-center text-xs">
                      <span className="text-gray-400 flex items-center gap-1"><Clock className="w-3 h-3"/> {new Date(s.created_at || Date.now()).toLocaleDateString()}</span>
                      {activeTab !== 'COMPLETED' && <span className="bg-amber-100 text-amber-800 px-1.5 py-0.5 rounded text-[10px] font-bold">24h left</span>}
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>

        {/* Right Detail Pane */}
        {selectedSchedule ? (
          <div className="w-full md:w-2/3 flex flex-col bg-gray-50">
            <div className="p-4 border-b border-gray-200 bg-white flex justify-between items-center">
              <h2 className="text-lg font-medium text-gray-900">{selectedSchedule.schedule_name}</h2>
              <button onClick={() => setSelectedSchedule(null)} className="md:hidden text-gray-400"><XCircle className="w-5 h-5"/></button>
            </div>
            
            <div className="flex-1 overflow-y-auto p-6 space-y-6">
              <div className="bg-white p-4 rounded shadow-sm border border-gray-200">
                <h3 className="text-sm font-semibold text-gray-900 mb-3 border-b pb-2">Schedule Summary</h3>
                <dl className="grid grid-cols-2 gap-4 text-sm">
                  <div><dt className="text-gray-500">Workflow</dt><dd className="font-medium text-gray-900">{selectedSchedule.workflow_id}</dd></div>
                  <div><dt className="text-gray-500">Risk Level</dt><dd className="font-medium text-gray-900">{selectedSchedule.risk_level}</dd></div>
                  <div className="col-span-2"><dt className="text-gray-500">Schedule</dt><dd className="font-medium text-gray-900">{selectedSchedule.schedule_type} {selectedSchedule.cron_expression}</dd></div>
                </dl>
              </div>

              <div className="bg-amber-50 p-4 rounded border border-amber-200">
                <h3 className="text-sm font-semibold text-amber-800 flex items-center gap-2 mb-2"><AlertCircle className="w-4 h-4"/> Approval Reason</h3>
                <p className="text-sm text-amber-700">This schedule requires approval due to configured risk level ({selectedSchedule.risk_level}) and tool assignment boundary.</p>
              </div>

              {activeTab !== 'COMPLETED' && (
                <div className="bg-white p-4 rounded shadow-sm border border-gray-200">
                  <h3 className="text-sm font-semibold text-gray-900 mb-4">Record Decision</h3>
                  <div className="flex gap-2 flex-wrap mb-4">
                    {['APPROVED', 'REJECTED', 'CHANGES_REQUESTED', 'ESCALATED'].map(d => (
                      <button 
                        key={d} 
                        onClick={() => setDecision(d as any)}
                        className={`px-3 py-1.5 text-sm font-medium rounded border ${
                          decision === d 
                            ? (d === 'APPROVED' ? 'bg-green-100 border-green-500 text-green-800' : 'bg-indigo-100 border-indigo-500 text-indigo-800')
                            : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'
                        }`}
                      >
                        {d.replace(/_/g, ' ')}
                      </button>
                    ))}
                  </div>

                  {decision && (
                    <div className="space-y-3">
                      <div>
                        <label className="block text-sm font-medium text-gray-700">Reason / Notes <span className="text-red-500">*</span></label>
                        <textarea 
                          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                          rows={3}
                          value={reason}
                          onChange={(e) => setReason(e.target.value)}
                          placeholder="Provide reasoning for this decision..."
                        />
                      </div>
                      <div className="flex justify-end">
                        <button
                          onClick={handleDecision}
                          disabled={!decision || (decision !== 'APPROVED' && reason.length < 10)}
                          className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50"
                        >
                          Submit Decision
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="hidden md:flex flex-1 items-center justify-center bg-gray-50 text-gray-400">
            Select a schedule to view details and approve.
          </div>
        )}
      </div>
    </div>
  );
};

export default ScheduleApprovalQueue;

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { notificationApi } from '../api/phase2Client';
import { NotificationResponse } from '../types/phase2';
import { useToast } from '../hooks/useToast';
import { Bell, Check, Trash2, ExternalLink } from 'lucide-react';

export const NotificationsCenter: React.FC = () => {
  const { showToast } = useToast();
  const navigate = useNavigate();

  const [activeTab, setActiveTab] = useState<'UNREAD' | 'ACTION_REQUIRED' | 'FAILURES' | 'HIGH_RISK' | 'ALL'>('UNREAD');
  const [notifications, setNotifications] = useState<NotificationResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [unreadCount, setUnreadCount] = useState(0);

  const fetchNotifications = async () => {
    setLoading(true);
    try {
      const params: any = {};
      if (activeTab === 'UNREAD') params.status = 'UNREAD';
      if (activeTab === 'ACTION_REQUIRED') params.notification_type = 'APPROVAL_REQUIRED,RUN_FAILED,HIGH_RISK_OUTPUT'; // simplified filter concept
      if (activeTab === 'FAILURES') params.notification_type = 'RUN_FAILED';
      if (activeTab === 'HIGH_RISK') params.severity = 'CRITICAL,HIGH';

      const res = await notificationApi.list(params);
      
      // Assume API does actual filtering, but we filter client-side too if backend doesn't support CSV
      let items = res.items || [];
      if (activeTab === 'ACTION_REQUIRED') {
        items = items.filter((i: any) => ['APPROVAL_REQUIRED', 'RUN_FAILED', 'HIGH_RISK_OUTPUT'].includes(i.notification_type));
      }
      if (activeTab === 'FAILURES') items = items.filter((i: any) => i.notification_type === 'RUN_FAILED');
      if (activeTab === 'HIGH_RISK') items = items.filter((i: any) => ['CRITICAL', 'HIGH'].includes(i.severity));

      setNotifications(items);

      if (activeTab === 'UNREAD') {
        setUnreadCount(res.total || items.length);
      } else {
        // Just fetch a quick unread count in background
        notificationApi.list({ status: 'UNREAD', per_page: 1 }).then(r => setUnreadCount(r.total || 0)).catch(()=>null);
      }
    } catch (e: any) {
      showToast('Failed to load notifications', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNotifications();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab]);

  const handleMarkRead = async (id: string) => {
    try {
      await notificationApi.markRead(id);
      fetchNotifications();
    } catch (e) {
      showToast('Failed to mark read', 'error');
    }
  };

  const handleAcknowledge = async (id: string) => {
    try {
      await notificationApi.acknowledge(id);
      showToast('Acknowledged', 'success');
      fetchNotifications();
    } catch (e) {
      showToast('Failed to acknowledge', 'error');
    }
  };

  const handleBulkRead = async () => {
    // We would need a bulk API endpoint, so we simulate looping or just pretend if not available
    const unreadIds = notifications.filter(n => n.status === 'UNREAD').map(n => n.id);
    if (unreadIds.length === 0) return;
    
    try {
      await Promise.all(unreadIds.map(id => notificationApi.markRead(id)));
      showToast('All marked as read', 'success');
      fetchNotifications();
    } catch (e) {
      showToast('Some items failed to update', 'error');
    }
  };

  const getSeverityColors = (sev: string) => {
    switch(sev) {
      case 'CRITICAL': return 'bg-red-100 text-red-800 border-red-200';
      case 'HIGH': return 'bg-orange-100 text-orange-800 border-orange-200';
      case 'MEDIUM': return 'bg-amber-100 text-amber-800 border-amber-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getTimeAgo = (dateStr: string) => {
    const min = Math.floor((new Date().getTime() - new Date(dateStr).getTime()) / 60000);
    if (min < 60) return `${min}m ago`;
    const hr = Math.floor(min / 60);
    if (hr < 24) return `${hr}h ago`;
    return `${Math.floor(hr / 24)}d ago`;
  };

  const navigateToEntity = (type?: string, id?: string) => {
    if (!id) return;
    if (type === 'WORKFLOW_SCHEDULE') navigate(`/workflow-scheduler/${id}`);
    else if (type === 'WORKFLOW_RUN') navigate(`/workflow-runs/${id}`);
    else navigate('/workflow-scheduler');
  };

  return (
    <div className="max-w-4xl mx-auto py-6 px-4 sm:px-6 lg:px-8 space-y-6">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900 flex items-center gap-2">
            <Bell className="w-6 h-6 text-indigo-500" /> Notifications
          </h1>
        </div>
      </div>

      <div className="bg-white shadow sm:rounded-lg border border-gray-200 flex flex-col min-h-[600px]">
        <div className="border-b border-gray-200 flex justify-between items-center px-4 sm:px-6">
          <nav className="-mb-px flex space-x-6 overflow-x-auto" aria-label="Tabs">
            {[
              { id: 'UNREAD', label: `Unread (${unreadCount})` },
              { id: 'ACTION_REQUIRED', label: 'Action Required' },
              { id: 'FAILURES', label: 'Failures' },
              { id: 'HIGH_RISK', label: 'High Risk' },
              { id: 'ALL', label: 'All' }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`${
                  activeTab === tab.id
                    ? 'border-indigo-500 text-indigo-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                } whitespace-nowrap py-4 border-b-2 font-medium text-sm`}
              >
                {tab.label}
              </button>
            ))}
          </nav>
          {activeTab === 'UNREAD' && unreadCount > 0 && (
            <button onClick={handleBulkRead} className="text-sm text-indigo-600 hover:text-indigo-800 font-medium flex items-center gap-1">
              <Check className="w-4 h-4"/> Mark all read
            </button>
          )}
        </div>

        <div className="flex-1 bg-gray-50 p-6">
          {loading ? (
            <div className="text-center py-10 text-gray-500">Loading...</div>
          ) : notifications.length === 0 ? (
            <div className="text-center py-20">
              <Bell className="mx-auto h-12 w-12 text-gray-300" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">No notifications here.</h3>
              <p className="mt-1 text-sm text-gray-500">You're all caught up.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {notifications.map(n => (
                <div key={n.id} className={`bg-white border rounded-lg shadow-sm p-4 ${n.status === 'UNREAD' ? 'border-l-4 border-l-indigo-500' : 'border-gray-200 opacity-80'}`}>
                  <div className="flex justify-between items-start mb-2">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="bg-gray-100 text-gray-800 px-2 py-0.5 rounded text-[10px] font-bold border border-gray-200">{n.notification_type}</span>
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${getSeverityColors(n.severity)}`}>{n.severity}</span>
                      <span className="text-gray-400 text-xs ml-2">{getTimeAgo(n.created_at)}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      {n.status === 'UNREAD' && (
                        <button onClick={() => handleMarkRead(n.id)} className="text-xs text-gray-500 hover:text-indigo-600 font-medium" title="Mark Read">
                          Mark Read
                        </button>
                      )}
                      {n.status !== 'ACKNOWLEDGED' && (
                        <button onClick={() => handleAcknowledge(n.id)} className="text-xs text-gray-500 hover:text-indigo-600 font-medium" title="Acknowledge">
                          Acknowledge
                        </button>
                      )}
                    </div>
                  </div>
                  <h4 className="text-md font-semibold text-gray-900 mb-1">{n.title}</h4>
                  <p className="text-sm text-gray-600 mb-4">{n.message}</p>
                  
                  <div className="flex justify-between items-center border-t border-gray-100 pt-3">
                    <span className="text-xs text-gray-400">ID: {n.id.substring(0,8)}...</span>
                    {n.entity_id && (
                      <button onClick={() => navigateToEntity(n.entity_type, n.entity_id)} className="inline-flex items-center text-sm font-medium text-indigo-600 hover:text-indigo-900">
                        {n.entity_type === 'WORKFLOW_SCHEDULE' ? 'View Schedule' : n.entity_type === 'WORKFLOW_RUN' ? 'View Run' : 'View Details'}
                        <ExternalLink className="ml-1 w-4 h-4"/>
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default NotificationsCenter;

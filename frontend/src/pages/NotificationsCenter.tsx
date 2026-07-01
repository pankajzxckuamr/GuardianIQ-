import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { notificationApi } from '../api/phase2Client';
import { NotificationResponse } from '../types/phase2';
import { useToast } from '../hooks/useToast';
import { PageHeader } from '../components/common/PageHeader';
import { ScreenGuide } from '../components/common/ScreenGuide';
import { Button } from '../components/common/Button';
import { Bell, Check, ExternalLink } from 'lucide-react';
import styles from './phase2Shared.module.css';
import '../components/common/RegistryDataTable.css';

type Tab = 'UNREAD' | 'ACTION_REQUIRED' | 'FAILURES' | 'HIGH_RISK' | 'ALL';

const severityPillClass = (sev: string): string => {
  switch (sev) {
    case 'CRITICAL': return styles.pillDanger;
    case 'HIGH': return styles.pillOrange;
    case 'MEDIUM': return styles.pillWarning;
    default: return styles.pillNeutral;
  }
};

export const NotificationsCenter: React.FC = () => {
  const { showToast } = useToast();
  const navigate = useNavigate();

  const [activeTab, setActiveTab] = useState<Tab>('UNREAD');
  const [notifications, setNotifications] = useState<NotificationResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [unreadCount, setUnreadCount] = useState(0);
  const [page, setPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const pageSize = 10;

  useEffect(() => {
    document.title = 'Notifications — GuardianIQ';
  }, []);

  const fetchNotifications = async () => {
    setLoading(true);
    try {
      const params: any = {
        page,
        per_page: pageSize
      };
      if (activeTab === 'UNREAD') params.status = 'UNREAD';
      if (activeTab === 'ACTION_REQUIRED') params.notification_type = 'APPROVAL_REQUIRED,RUN_FAILED,HIGH_RISK_OUTPUT';
      if (activeTab === 'FAILURES') params.notification_type = 'RUN_FAILED';
      if (activeTab === 'HIGH_RISK') params.severity = 'CRITICAL,HIGH';

      const res: any = await notificationApi.list(params);

      let items = res.items || [];
      if (activeTab === 'ACTION_REQUIRED') {
        items = items.filter((i: any) => ['APPROVAL_REQUIRED', 'RUN_FAILED', 'HIGH_RISK_OUTPUT'].includes(i.notification_type));
      }
      if (activeTab === 'FAILURES') items = items.filter((i: any) => i.notification_type === 'RUN_FAILED');
      if (activeTab === 'HIGH_RISK') items = items.filter((i: any) => ['CRITICAL', 'HIGH'].includes(i.severity));

      // Handle safety fallback if user action emptied current page but items still exist
      if (items.length === 0 && page > 1 && res.total > 0) {
        setPage(Math.ceil(res.total / pageSize) || 1);
        return;
      }

      setNotifications(items);
      setTotalCount(res.total || items.length);

      if (activeTab === 'UNREAD') {
        setUnreadCount(res.total || items.length);
      } else {
        notificationApi.list({ status: 'UNREAD', per_page: 1 }).then((r: any) => setUnreadCount(r.total || 0)).catch(() => null);
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
  }, [activeTab, page]);

  const handleTabChange = (tabId: Tab) => {
    setActiveTab(tabId);
    setPage(1);
  };

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

  const TABS: { id: Tab; label: string }[] = [
    { id: 'UNREAD', label: `Unread (${unreadCount})` },
    { id: 'ACTION_REQUIRED', label: 'Action Required' },
    { id: 'FAILURES', label: 'Failures' },
    { id: 'HIGH_RISK', label: 'High Risk' },
    { id: 'ALL', label: 'All' },
  ];

  return (
    <div className={styles.page}>
      <div className={styles.breadcrumb}>Orchestration &gt; Notifications</div>
      <PageHeader
        title="Notifications"
        description="Stay on top of approvals, failures, and high-risk workflow events"
        actions={
          <ScreenGuide
            content={
              <div style={{ display: "flex", flexDirection: "column", gap: "12px", paddingRight: "4px" }}>
                <h4 style={{ color: "#fbbf24", margin: "0 0 4px 0", fontSize: "0.85rem" }}>Notifications</h4>
                <p style={{ margin: 0 }}>View alerts for workflow events, such as failed runs, tasks awaiting approval, or high-risk actions. Click on an alert to investigate further.</p>
              </div>
            }
          />
        }
      />

      <div className={styles.listPane}>
        <div className={styles.tabsBar}>
          <nav className={styles.tabsNav}>
            {TABS.map(tab => (
              <button
                key={tab.id}
                className={`${styles.tabLink} ${activeTab === tab.id ? styles.activeTab : ''}`}
                onClick={() => handleTabChange(tab.id)}
              >
                {tab.label}
              </button>
            ))}
          </nav>
          {activeTab === 'UNREAD' && unreadCount > 0 && (
            <button className={styles.textBtn} onClick={handleBulkRead}>
              <Check size={14} /> Mark all read
            </button>
          )}
        </div>

        {loading ? (
          <div style={{ padding: '2.5rem', textAlign: 'center' }}>
            <div className={styles.stateDesc}>Loading...</div>
          </div>
        ) : notifications.length === 0 ? (
          <div className={styles.stateCard} style={{ border: 'none', background: 'transparent' }}>
            <Bell size={36} style={{ color: 'var(--text-muted)' }} />
            <div className={styles.stateTitle}>No notifications here.</div>
            <div className={styles.stateDesc}>You're all caught up.</div>
          </div>
        ) : (
          <>
            <div className={styles.notifList}>
              {notifications.map(n => (
                <div key={n.id} className={`${styles.notifCard} ${n.status === 'UNREAD' ? styles.notifUnread : styles.notifRead}`}>
                  <div className={styles.notifHeader}>
                    <div className={styles.notifMeta}>
                      <span className={styles.tagChipNeutral}>{n.notification_type}</span>
                      <span className={`${styles.pill} ${severityPillClass(n.severity)}`}>{n.severity}</span>
                      <span className={styles.notifTime}>{getTimeAgo(n.created_at)}</span>
                    </div>
                    <div className={styles.notifActions}>
                      {n.status === 'UNREAD' && (
                        <button className={styles.textBtn} onClick={() => handleMarkRead(n.id)}>Mark Read</button>
                      )}
                      {n.status !== 'ACKNOWLEDGED' && (
                        <button className={styles.textBtn} onClick={() => handleAcknowledge(n.id)}>Acknowledge</button>
                      )}
                    </div>
                  </div>
                  <h4 className={styles.notifTitle}>{n.title}</h4>
                  <p className={styles.notifMessage}>{n.message}</p>
                  <div className={styles.notifFooter}>
                    <span className={styles.notifId}>ID: {n.id.substring(0, 8)}...</span>
                    {n.entity_id && (
                      <button className={styles.textBtn} onClick={() => navigateToEntity(n.entity_type, n.entity_id)}>
                        {n.entity_type === 'WORKFLOW_SCHEDULE' ? 'View Schedule' : n.entity_type === 'WORKFLOW_RUN' ? 'View Run' : 'View Details'}
                        <ExternalLink size={14} />
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>

            {/* Pagination Controls */}
            {totalCount > 0 && (
              <div className="registry-pagination-bar" style={{ margin: '0 1.5rem 1.5rem 1.5rem', background: 'rgba(30, 41, 59, 0.2)' }}>
                <div className="registry-pagination-info">
                  Showing <span className="highlight">{totalCount === 0 ? 0 : (page - 1) * pageSize + 1}–{Math.min(page * pageSize, totalCount)}</span> of{" "}
                  <span className="highlight">{totalCount}</span> records
                </div>
                <div className="registry-pagination-actions">
                  <Button
                    variant="secondary"
                    size="sm"
                    disabled={page <= 1}
                    onClick={() => setPage(p => Math.max(1, p - 1))}
                  >
                    Previous
                  </Button>
                  <span className="registry-page-num">
                    Page {page} of {Math.ceil(totalCount / pageSize) || 1}
                  </span>
                  <Button
                    variant="secondary"
                    size="sm"
                    disabled={page >= (Math.ceil(totalCount / pageSize) || 1)}
                    onClick={() => setPage(p => Math.min(Math.ceil(totalCount / pageSize) || 1, p + 1))}
                  >
                    Next
                  </Button>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default NotificationsCenter;

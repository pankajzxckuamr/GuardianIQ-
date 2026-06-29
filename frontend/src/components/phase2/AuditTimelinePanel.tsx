import React, { useEffect, useState } from 'react';
import styles from '../../pages/phase2Shared.module.css';
import { auditApi } from '../../api/phase2Client';
import { AuditTimelineEvent } from '../../types/phase2';
import { Check, X, Play, Pause, Plus, FileText, Archive, Clock } from 'lucide-react';

interface Props {
  entityType: string;
  entityId: string;
}

export const AuditTimelinePanel: React.FC<Props> = ({ entityType, entityId }) => {
  const [events, setEvents] = useState<AuditTimelineEvent[]>([]);

  useEffect(() => {
    auditApi.getTimeline(entityType, entityId)
      .then(res => {
        setEvents((res as any).items || []);
      })
      .catch(console.error);
  }, [entityType, entityId]);

  const getDotClass = (action: string) => {
    const act = action?.toUpperCase();
    if (['CREATE', 'SUBMIT', 'APPROVE', 'ACTIVATE', 'RESUME'].includes(act)) {
      return `${styles.auditDot} ${styles.success}`;
    }
    if (['REJECT', 'PAUSE', 'RETIRE', 'DELETE'].includes(act)) {
      return `${styles.auditDot} ${styles.danger}`;
    }
    if (['UPDATE'].includes(act)) {
      return `${styles.auditDot} ${styles.warning}`;
    }
    return `${styles.auditDot} ${styles.info}`;
  };

  const renderDotIcon = (action: string) => {
    const act = action?.toUpperCase();
    if (act === 'CREATE') return <Plus size={14} />;
    if (act === 'SUBMIT') return <FileText size={14} />;
    if (act === 'APPROVE' || act === 'ACTIVATE' || act === 'RESUME') return <Check size={14} />;
    if (act === 'REJECT') return <X size={14} />;
    if (act === 'PAUSE') return <Pause size={14} />;
    if (act === 'RETIRE') return <Archive size={14} />;
    if (act === 'RUN') return <Play size={14} />;
    return <Clock size={14} />;
  };

  if (events.length === 0) {
    return <p className={styles.stateDesc}>No audit history found.</p>;
  }

  return (
    <div className={styles.auditList}>
      {events.map((ev, idx) => (
        <div key={ev.id} className={styles.auditItem}>
          <div className={styles.auditDotCol}>
            <span className={getDotClass(ev.action_type)}>
              {renderDotIcon(ev.action_type)}
            </span>
            {idx !== events.length - 1 && <span className={styles.auditLine} />}
          </div>
          <div className={styles.auditContent}>
            <div className={styles.auditBody}>
              <div style={{ fontWeight: '600', marginBottom: '4px' }}>{ev.event_code}</div>
              <span className={styles.auditSummary}>{ev.event_summary}</span>
              {ev.event_payload && (
                <details className={styles.detailsToggle} style={{ marginTop: '8px' }}>
                  <summary>Event Payload</summary>
                  <pre className={styles.codeBlock} style={{ marginTop: '4px' }}>
                    {JSON.stringify(ev.event_payload, null, 2)}
                  </pre>
                </details>
              )}
              <div className={styles.auditMeta} style={{ marginTop: '8px' }}>
                <span className={styles.auditActor}>by {ev.actor_name || 'System'}</span>
              </div>
            </div>
            <span className={styles.auditTime}>{new Date(ev.created_at).toLocaleString()}</span>
          </div>
        </div>
      ))}
    </div>
  );
};


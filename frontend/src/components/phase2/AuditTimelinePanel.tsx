import React, { useEffect, useState } from 'react';
import styles from '../../pages/phase2Shared.module.css';

interface Props {
  entityType: string;
  entityId: string;
}

export const AuditTimelinePanel: React.FC<Props> = ({ entityType, entityId }) => {
  const [events, setEvents] = useState<any[]>([]);

  useEffect(() => {
    fetch(`/api/v1/audit/events?entity_type=${entityType}&entity_id=${entityId}`)
      .then(r => r.json())
      .then(d => {
        if (d.success) setEvents(d.data.items || []);
      })
      .catch(console.error);
  }, [entityType, entityId]);

  if (events.length === 0) {
    return <p className={styles.stateDesc}>No audit history found.</p>;
  }

  return (
    <div className={styles.auditList}>
      {events.map((ev, idx) => (
        <div key={ev.id} className={styles.auditItem}>
          <div className={styles.auditDotCol}>
            <span className={styles.auditDot}>{ev.action_type?.charAt(0) || 'E'}</span>
            {idx !== events.length - 1 && <span className={styles.auditLine} />}
          </div>
          <div className={styles.auditContent}>
            <span className={styles.auditSummary}>{ev.event_summary}</span>
            <span className={styles.auditTime}>{new Date(ev.created_at).toLocaleString()}</span>
          </div>
        </div>
      ))}
    </div>
  );
};

import React, { useEffect, useState } from 'react';
import styles from '../../pages/phase2Shared.module.css';
import { auditApi } from '../../api/phase2Client';
import { Check, Play, Pause, Plus, FileText, Clock, ShieldAlert, Eye } from 'lucide-react';
import { Badge } from '../common/Badge';

interface Props {
  entityType?: string;
  entityId?: string;
  events?: any[];
  onEventClick?: (event: any) => void;
}

export const AuditTimelinePanel: React.FC<Props> = ({
  entityType,
  entityId,
  events: propEvents,
  onEventClick
}) => {
  const [internalEvents, setInternalEvents] = useState<any[]>([]);

  useEffect(() => {
    if (!propEvents && entityType && entityId) {
      auditApi.getTimeline(entityType, entityId)
        .then(res => {
          setInternalEvents((res as any).items || (res as any).events || []);
        })
        .catch(console.error);
    }
  }, [entityType, entityId, propEvents]);

  const displayEvents = propEvents || internalEvents;

  const getDotClass = (actionOrType: string) => {
    const act = (actionOrType || '').toUpperCase();
    if (['CREATE', 'SUBMIT', 'APPROVE', 'ACTIVATE', 'RESUME', 'WORKFLOW_RUN_STARTED', 'WORKFLOW_RUN_COMPLETED', 'RELATIONSHIP_CREATED'].some(k => act.includes(k))) {
      return `${styles.auditDot} ${styles.success}`;
    }
    if (['REJECT', 'PAUSE', 'RETIRE', 'DELETE', 'BLOCKED', 'VIOLATION', 'FAILED', 'RELATIONSHIP_REVOKED'].some(k => act.includes(k))) {
      return `${styles.auditDot} ${styles.danger}`;
    }
    if (['UPDATE', 'SUSPEND'].some(k => act.includes(k))) {
      return `${styles.auditDot} ${styles.warning}`;
    }
    return `${styles.auditDot} ${styles.info}`;
  };

  const renderDotIcon = (actionOrType: string) => {
    const act = (actionOrType || '').toUpperCase();
    if (act.includes('CREATE')) return <Plus size={14} />;
    if (act.includes('SUBMIT') || act.includes('PAYLOAD')) return <FileText size={14} />;
    if (act.includes('APPROVE') || act.includes('ACTIVATE') || act.includes('COMPLETED')) return <Check size={14} />;
    if (act.includes('REJECT') || act.includes('BLOCKED') || act.includes('VIOLATION') || act.includes('REVOKED')) return <ShieldAlert size={14} />;
    if (act.includes('PAUSE')) return <Pause size={14} />;
    if (act.includes('RUN') || act.includes('STARTED')) return <Play size={14} />;
    return <Clock size={14} />;
  };

  if (!displayEvents || displayEvents.length === 0) {
    return <p className={styles.stateDesc}>No audit timeline events found.</p>;
  }

  return (
    <div className={styles.auditList}>
      {displayEvents.map((ev: any, idx: number) => {
        const eventCode = ev.event_type || ev.event_code || "GOVERNANCE_EVENT";
        const actionType = ev.action_type || ev.event_category || eventCode;
        const summary = ev.event_summary || ev.summary || `${eventCode} executed cleanly`;
        const actorName = ev.actor_name || ev.actor_json?.user_id || "System";
        const occurredAt = ev.occurred_at || ev.recorded_at || ev.created_at || new Date().toISOString();
        const payload = ev.payload_json || ev.event_payload;
        const riskLevel = ev.risk_context_json?.risk_level || ev.risk_level;

        return (
          <div
            key={ev.event_id || ev.id || idx}
            className={styles.auditItem}
            style={{ cursor: onEventClick ? 'pointer' : 'default' }}
            onClick={() => onEventClick && onEventClick(ev)}
          >
            <div className={styles.auditDotCol}>
              <span className={getDotClass(actionType)}>
                {renderDotIcon(actionType)}
              </span>
              {idx !== displayEvents.length - 1 && <span className={styles.auditLine} />}
            </div>
            <div className={styles.auditContent}>
              <div className={styles.auditBody}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '0.5rem', marginBottom: '4px' }}>
                  <span style={{ fontFamily: 'monospace', fontWeight: '700', fontSize: '0.9rem', color: 'var(--text-primary)' }}>
                    {eventCode}
                  </span>
                  {riskLevel && (
                    <Badge
                      label={riskLevel}
                      variant={riskLevel === 'HIGH' || riskLevel === 'CRITICAL' ? 'danger' : riskLevel === 'MEDIUM' ? 'warning' : 'success'}
                      dot
                    />
                  )}
                </div>

                <div className={styles.auditSummary} style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                  {summary}
                </div>

                {ev.source_service && (
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                    Source: <span style={{ fontFamily: 'monospace' }}>{ev.source_service}</span>
                  </div>
                )}

                {payload && (
                  <details
                    className={styles.detailsToggle}
                    style={{ marginTop: '8px' }}
                    onClick={(e) => e.stopPropagation()}
                  >
                    <summary>View Event Data Payload</summary>
                    <pre className={styles.codeBlock} style={{ marginTop: '4px' }}>
                      {JSON.stringify(payload, null, 2)}
                    </pre>
                  </details>
                )}

                <div className={styles.auditMeta} style={{ marginTop: '8px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <span className={styles.auditActor} style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    by {actorName}
                  </span>
                  {onEventClick && (
                    <span style={{ fontSize: '0.75rem', color: 'var(--accent-secondary)', display: 'flex', alignItems: 'center', gap: '2px' }}>
                      Inspect <Eye size={12} />
                    </span>
                  )}
                </div>
              </div>
              <span className={styles.auditTime} style={{ fontSize: '0.75rem', whiteSpace: 'nowrap' }}>
                {new Date(occurredAt).toLocaleString()}
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
};

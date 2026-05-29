/* src/components/registry/AuditTrailViewer.tsx */

import React, { useEffect, useState } from "react";
import * as registryService from "../../services/registry/registryService";
import styles from "./AuditTrailViewer.module.css";
import { ChevronDown, ChevronRight, Clock, User } from "lucide-react";

interface AuditTrailViewerProps {
  entityType: string;
  entityId: string;
}

interface AuditEvent {
  id: string;
  entity_type: string;
  entity_id: string;
  event_type: string;
  changed_by: string;
  changed_by_name?: string;
  changed_by_email?: string;
  before_json?: Record<string, any> | null;
  after_json?: Record<string, any> | null;
  change_summary?: string;
  created_at: string;
}

export const AuditTrailViewer: React.FC<AuditTrailViewerProps> = ({
  entityType,
  entityId
}) => {
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Pagination State
  const [page, setPage] = useState(1);
  const [hasNext, setHasNext] = useState(false);
  
  // Toggle Expandable Rows by ID
  const [expandedIds, setExpandedIds] = useState<Record<string, boolean>>({});

  const fetchAuditTrail = async (targetPage: number, append = false) => {
    if (append) {
      setLoadingMore(true);
    } else {
      setLoading(true);
      setError(null);
    }

    try {
      const res = await registryService.getAuditTrail(entityType, entityId, {
        page: targetPage,
        page_size: 10
      });

      if (res.data) {
        const rawData = res.data as any;
        const newItems = rawData.items || [];
        setEvents(prev => append ? [...prev, ...newItems] : newItems);
        setPage(rawData.page || targetPage);
        setHasNext(!!rawData.has_next);
      }
    } catch (err: any) {
      console.error("Failed to load audit trail:", err);
      setError(err.message || "Failed to load audit logs.");
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  };

  useEffect(() => {
    fetchAuditTrail(1, false);
    setExpandedIds({});
  }, [entityType, entityId]);

  const handleLoadMore = () => {
    if (hasNext && !loadingMore) {
      fetchAuditTrail(page + 1, true);
    }
  };

  const toggleExpand = (id: string) => {
    setExpandedIds(prev => ({
      ...prev,
      [id]: !prev[id]
    }));
  };

  const formatTimestamp = (ts: string) => {
    if (!ts) return "-";
    try {
      const d = new Date(ts);
      return d.toLocaleString(undefined, {
        month: "short",
        day: "numeric",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit"
      });
    } catch {
      return ts;
    }
  };

  const getEventBadgeClass = (eventType: string) => {
    const et = eventType.toUpperCase();
    if (et === "CREATED") return styles.badgeCreated;
    if (et === "UPDATED") return styles.badgeUpdated;
    if (et === "STATUS_CHANGED") return styles.badgeStatusChanged;
    if (et === "DELETED") return styles.badgeDeleted;
    if (et === "RELATIONSHIP_ADDED" || et === "RELATIONSHIP_REMOVED") return styles.badgeRelationship;
    return styles.badgeGeneric;
  };

  const formatEventLabel = (type: string) => {
    return type.replace("_", " ");
  };

  return (
    <div className={styles.viewer}>
      <h4 className={styles.viewerTitle}>Governance Audit Timeline</h4>

      {error && <div className={styles.alertError}>{error}</div>}

      {loading && (
        <div className={styles.skeletonTimeline}>
          <div className={styles.skeletonItem}></div>
          <div className={styles.skeletonItem}></div>
        </div>
      )}

      {!loading && !error && (
        <div className={styles.timeline}>
          {events.length > 0 ? (
            <>
              <div className={styles.timelineTrack}></div>
              {events.map((event) => {
                const isExpanded = !!expandedIds[event.id];
                const hasBefore = !!event.before_json && Object.keys(event.before_json).length > 0;
                const hasAfter = !!event.after_json && Object.keys(event.after_json).length > 0;
                const canExpand = hasBefore || hasAfter;

                return (
                  <div
                    key={event.id}
                    className={`${styles.timelineNode} ${canExpand ? styles.clickableNode : ""}`}
                    onClick={() => canExpand && toggleExpand(event.id)}
                  >
                    {/* Circle Bullet Icon on Track */}
                    <div className={`${styles.timelineBullet} ${getEventBadgeClass(event.event_type)}`}>
                      <Clock size={12} />
                    </div>

                    <div className={styles.timelineContent}>
                      {/* Node Header Row */}
                      <div className={styles.nodeHeader}>
                        <div className={styles.badgeGroup}>
                          <span className={`${styles.eventBadge} ${getEventBadgeClass(event.event_type)}`}>
                            {formatEventLabel(event.event_type)}
                          </span>
                          <span className={styles.timestamp}>{formatTimestamp(event.created_at)}</span>
                        </div>
                        {canExpand && (
                          <div className={styles.expandIndicator}>
                            {isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                          </div>
                        )}
                      </div>

                      {/* Summary Block */}
                      <p className={styles.summaryText}>{event.change_summary || "Audit log entry generated"}</p>

                      {/* Operator Identity Block */}
                      <div className={styles.operatorBlock}>
                        <User size={12} className={styles.operatorIcon} />
                        <span className={styles.operatorLabel}>Modified by:</span>
                        <span className={styles.operatorName}>
                          {event.changed_by_name || "System Automated"}
                        </span>
                        {event.changed_by_email && (
                          <span className={styles.operatorEmail}>({event.changed_by_email})</span>
                        )}
                      </div>

                      {/* Expandable Diffs Comparison Section */}
                      {isExpanded && canExpand && (
                        <div
                          className={styles.diffPanel}
                          onClick={(e) => e.stopPropagation()} // Stop click bubbling from closing panel
                        >
                          <h6 className={styles.diffTitle}>JSON State Comparison</h6>
                          <div className={styles.diffGrid}>
                            {hasBefore && (
                              <div className={styles.diffCol}>
                                <div className={styles.diffColLabel}>Before State</div>
                                <pre className={styles.preCode}>
                                  {JSON.stringify(event.before_json, null, 2)}
                                </pre>
                              </div>
                            )}
                            {hasAfter && (
                              <div className={styles.diffCol}>
                                <div className={styles.diffColLabel}>After State</div>
                                <pre className={styles.preCode}>
                                  {JSON.stringify(event.after_json, null, 2)}
                                </pre>
                              </div>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </>
          ) : (
            <div className={styles.emptyState}>No audit history yet.</div>
          )}
        </div>
      )}

      {/* Load More Button */}
      {hasNext && (
        <div className={styles.loadMoreContainer}>
          <button
            type="button"
            onClick={handleLoadMore}
            disabled={loadingMore}
            className={styles.loadMoreBtn}
          >
            {loadingMore ? "Loading Logs..." : "Load More Logs"}
          </button>
        </div>
      )}
    </div>
  );
};

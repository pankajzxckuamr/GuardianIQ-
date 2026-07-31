/* src/pages/DeadLetterReviewPage.tsx */
import React, { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../hooks/useToast";
import { fetchDeadLetterEvents, retryDeadLetterEvent, DeadLetterEvent } from "../services/audit/auditService";
import { RetryActionButton } from "../components/common/RetryActionButton";
import styles from "./DeadLetterReviewPage.module.css";

export const DeadLetterReviewPage: React.FC = () => {
  const { token } = useAuth();
  const { showToast } = useToast();
  const [items, setItems] = useState<DeadLetterEvent[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<"ALL" | "UNRESOLVED" | "RESOLVED">("UNRESOLVED");
  const [search, setSearch] = useState<string>("");

  const loadData = async () => {
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      const data = await fetchDeadLetterEvents(token);
      setItems(data);
    } catch (err: any) {
      setError(err?.message || "Failed to load dead letter queue events");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [token]);

  const handleRetry = async (id: string) => {
    if (!token) return;
    const updated = await retryDeadLetterEvent(token, id);
    setItems((prev) => prev.map((item) => (item.id === id ? { ...item, status: "RESOLVED", resolved_at: updated.resolved_at } : item)));
    showToast("Dead letter event successfully re-queued for processing", "success");
  };

  const filteredItems = items.filter((item) => {
    if (statusFilter !== "ALL" && item.status !== statusFilter) return false;
    if (search) {
      const term = search.toLowerCase();
      return (
        item.failure_reason.toLowerCase().includes(term) ||
        item.event_id.toLowerCase().includes(term) ||
        item.id.toLowerCase().includes(term)
      );
    }
    return true;
  });

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div>
          <h1 className={styles.title}>Dead Letter Queue (DLQ) Review</h1>
          <p className={styles.description}>
            Inspect failed background consumer events and trigger manual re-queuing
          </p>
        </div>
        <button
          type="button"
          onClick={loadData}
          disabled={loading}
          style={{
            padding: "0.5rem 1rem",
            backgroundColor: "#1e293b",
            color: "#f8fafc",
            border: "1px solid #334155",
            borderRadius: "0.375rem",
            cursor: "pointer",
            fontSize: "0.875rem"
          }}
        >
          {loading ? "Refreshing..." : "Refresh Queue"}
        </button>
      </div>

      <div className={styles.controls}>
        <div className={styles.filterTabs}>
          <button
            type="button"
            className={`${styles.tab} ${statusFilter === "UNRESOLVED" ? styles.activeTab : ""}`}
            onClick={() => setStatusFilter("UNRESOLVED")}
          >
            Unresolved ({items.filter((i) => i.status === "UNRESOLVED").length})
          </button>
          <button
            type="button"
            className={`${styles.tab} ${statusFilter === "RESOLVED" ? styles.activeTab : ""}`}
            onClick={() => setStatusFilter("RESOLVED")}
          >
            Resolved ({items.filter((i) => i.status === "RESOLVED").length})
          </button>
          <button
            type="button"
            className={`${styles.tab} ${statusFilter === "ALL" ? styles.activeTab : ""}`}
            onClick={() => setStatusFilter("ALL")}
          >
            All ({items.length})
          </button>
        </div>

        <input
          type="text"
          placeholder="Filter by ID or reason..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className={styles.searchInput}
        />
      </div>

      {error && (
        <div style={{ padding: "1rem", backgroundColor: "rgba(239,68,68,0.15)", border: "1px solid #ef4444", borderRadius: "0.5rem", color: "#f87171" }}>
          {error}
        </div>
      )}

      {loading ? (
        <div className={styles.emptyState}>
          <div style={{ width: "2rem", height: "2rem", border: "2px solid #3b82f6", borderTopColor: "transparent", borderRadius: "50%", animation: "spin 0.8s linear infinite", margin: "0 auto 1rem" }} />
          <p>Loading dead letter events...</p>
        </div>
      ) : filteredItems.length === 0 ? (
        <div className={styles.emptyState}>
          <p style={{ fontSize: "1.125rem", color: "#cbd5e1", marginBottom: "0.5rem" }}>
            No governance dead letter events found
          </p>
          <p style={{ fontSize: "0.875rem", color: "#64748b" }}>
            {statusFilter === "UNRESOLVED"
              ? "All consumer dispatches are operating cleanly with zero failed items."
              : "No dead letter items match your selected filters."}
          </p>
        </div>
      ) : (
        <div className={styles.tableWrapper}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th>DLQ Record ID</th>
                <th>Event ID</th>
                <th>Failure Rationale</th>
                <th>Failed At</th>
                <th>Retries</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredItems.map((item) => (
                <tr key={item.id}>
                  <td>
                    <span className={styles.codeText}>{item.id.substring(0, 8)}...</span>
                  </td>
                  <td>
                    <span className={styles.codeText}>{item.event_id.substring(0, 8)}...</span>
                  </td>
                  <td style={{ maxWidth: "20rem" }}>
                    <div style={{ color: "#f1f5f9", fontWeight: 500 }}>{item.failure_reason}</div>
                  </td>
                  <td>{new Date(item.failed_at).toLocaleString()}</td>
                  <td>
                    <span className={styles.attemptsBadge}>{item.retry_attempts} retries</span>
                  </td>
                  <td>
                    {item.status === "UNRESOLVED" ? (
                      <span className={styles.unresolvedBadge}>UNRESOLVED</span>
                    ) : (
                      <span className={styles.resolvedBadge}>RESOLVED</span>
                    )}
                  </td>
                  <td>
                    {item.status === "UNRESOLVED" ? (
                      <RetryActionButton
                        onRetry={() => handleRetry(item.id)}
                        label="Retry"
                        loadingLabel="Retrying..."
                      />
                    ) : (
                      <span style={{ fontSize: "0.75rem", color: "#64748b" }}>Resolved</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default DeadLetterReviewPage;

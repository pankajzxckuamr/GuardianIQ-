import React, { useState, useEffect } from "react";
import { Activity, Clock } from "lucide-react";
import serverClient from "../../services/shared/apiClient";
import styles from "./EnforcementHistoryTab.module.css";

interface EnforcementHistoryTabProps {
  agentId: string;
}

interface EnforcementLog {
  id: string;
  event_type: string;
  decision?: string;
  operation?: string;
  occurred_at: string;
  correlation_id?: string;
  reason?: string;
}

export const EnforcementHistoryTab: React.FC<EnforcementHistoryTabProps> = ({ agentId }) => {
  const [logs, setLogs] = useState<EnforcementLog[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadLogs();
  }, [agentId]);

  const loadLogs = async () => {
    setLoading(true);
    try {
      const res = await serverClient.get<any>(
        `/api/v1/events?subject_type=AGENT&subject_id=${agentId}&page_size=20`
      );
      const items = res?.events || res?.data?.events || res?.items || res?.data?.items || (Array.isArray(res) ? res : []);
      const formatted: EnforcementLog[] = items.map((ev: any) => ({
        id: ev.event_id || ev.id,
        event_type: ev.event_type,
        decision: (ev.payload_json || {}).decision || (ev.event_type.includes("BLOCKED") || ev.event_type.includes("DENIED") ? "DENY" : "ALLOW"),
        operation: (ev.payload_json || {}).operation || "EXECUTE",
        occurred_at: ev.occurred_at,
        correlation_id: ev.correlation_id,
        reason: (ev.payload_json || {}).reason,
      }));
      setLogs(formatted);
    } catch {
      setLogs([]);
    } finally {
      setLoading(false);
    }
  };

  const getDecisionBadge = (decision: string) => {
    switch (decision) {
      case "ALLOW":
      case "ALLOW_WITH_OBLIGATIONS":
        return <span className="text-xs px-2 py-0.5 rounded font-mono font-medium bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300">ALLOW</span>;
      case "DENY":
        return <span className="text-xs px-2 py-0.5 rounded font-mono font-medium bg-rose-50 text-rose-700 dark:bg-rose-950/40 dark:text-rose-300">DENY</span>;
      case "REQUIRE_APPROVAL":
        return <span className="text-xs px-2 py-0.5 rounded font-mono font-medium bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-300">REQUIRE_APPROVAL</span>;
      case "ESCALATE":
        return <span className="text-xs px-2 py-0.5 rounded font-mono font-medium bg-purple-50 text-purple-700 dark:bg-purple-950/40 dark:text-purple-300">ESCALATE</span>;
      default:
        return <span className="text-xs px-2 py-0.5 rounded font-mono font-medium bg-slate-100 text-slate-700">{decision}</span>;
    }
  };

  return (
    <div className={styles.container}>
      <div>
        <h4 className="text-sm font-semibold text-slate-900 dark:text-white flex items-center gap-2">
          <Activity className="w-4 h-4 text-indigo-500" /> Live Enforcement & Evaluation Trace
        </h4>
        <p className="text-xs text-slate-500 mt-0.5">
          Recent runtime authorization requests, AST rule evaluations, and boundary enforcement actions.
        </p>
      </div>

      {loading ? (
        <div className="py-8 text-center text-xs text-slate-400">Loading enforcement trace...</div>
      ) : logs.length === 0 ? (
        <div className="py-8 text-center text-xs text-slate-400 border border-dashed border-slate-200 dark:border-slate-800 rounded-xl">
          <Activity className="w-8 h-8 mx-auto text-slate-300 dark:text-slate-700 mb-1" />
          No runtime enforcement events recorded yet.
        </div>
      ) : (
        <div className={styles.tableWrapper}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th className={styles.th}>Timestamp</th>
                <th className={styles.th}>Event Type</th>
                <th className={styles.th}>Operation</th>
                <th className={styles.th}>Decision</th>
                <th className={styles.th}>Correlation ID</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log) => (
                <tr key={log.id}>
                  <td className={styles.td}>
                    <div className="text-xs text-slate-500 flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {new Date(log.occurred_at).toLocaleTimeString()}
                    </div>
                  </td>
                  <td className={styles.td}>
                    <span className="font-mono text-xs font-semibold text-slate-900 dark:text-white">
                      {log.event_type}
                    </span>
                  </td>
                  <td className={styles.td}>
                    <span className="font-mono text-xs text-slate-600 dark:text-slate-300">
                      {log.operation}
                    </span>
                  </td>
                  <td className={styles.td}>
                    {getDecisionBadge(log.decision || "ALLOW")}
                    {log.reason && (
                      <div className="text-[11px] text-rose-500 mt-0.5">{log.reason}</div>
                    )}
                  </td>
                  <td className={styles.td}>
                    <span className="font-mono text-[11px] text-slate-400">
                      {log.correlation_id ? `${log.correlation_id.slice(0, 8)}...` : "—"}
                    </span>
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

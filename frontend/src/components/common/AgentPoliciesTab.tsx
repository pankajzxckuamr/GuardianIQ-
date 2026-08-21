import React, { useState, useEffect } from "react";
import { ShieldCheck, CheckCircle2, Link2, ExternalLink } from "lucide-react";
import serverClient from "../../services/shared/apiClient";
import styles from "./AgentPoliciesTab.module.css";

interface AgentPoliciesTabProps {
  agentId: string;
}

interface BoundPolicy {
  id: string;
  policy_id: string;
  policy_name?: string;
  target_type: string;
  priority: number;
  is_mandatory: boolean;
  version_strategy: string;
  status: string;
}

export const AgentPoliciesTab: React.FC<AgentPoliciesTabProps> = ({ agentId }) => {
  const [policies, setPolicies] = useState<BoundPolicy[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadPolicies();
  }, [agentId]);

  const loadPolicies = async () => {
    setLoading(true);
    try {
      const res = await serverClient.get<any>(
        `/api/v1/policy-bindings/effective?target_type=AGENT&target_id=${agentId}`
      );
      setPolicies(Array.isArray(res) ? res : (res?.data || []));
    } catch {
      setPolicies([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.container}>
      <div className="flex items-center justify-between">
        <div>
          <h4 className="text-sm font-semibold text-slate-900 dark:text-white flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-indigo-500" /> Active Compliance Policies
          </h4>
          <p className="text-xs text-slate-500 mt-0.5">
            Effective direct, workflow-inherited, and tenant-mandatory policies governing this agent.
          </p>
        </div>
      </div>

      {loading ? (
        <div className="py-8 text-center text-xs text-slate-400">Loading bound policies...</div>
      ) : policies.length === 0 ? (
        <div className="py-8 text-center text-xs text-slate-400 border border-dashed border-slate-200 dark:border-slate-800 rounded-xl">
          <ShieldCheck className="w-8 h-8 mx-auto text-slate-300 dark:text-slate-700 mb-1" />
          No compliance policies bound to this agent.
        </div>
      ) : (
        <div className={styles.tableWrapper}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th className={styles.th}>Precedence</th>
                <th className={styles.th}>Policy ID</th>
                <th className={styles.th}>Priority</th>
                <th className={styles.th}>Mandatory</th>
                <th className={styles.th}>Version Strategy</th>
                <th className={styles.th}>Status</th>
              </tr>
            </thead>
            <tbody>
              {policies.map((p, idx) => (
                <tr key={p.id || idx}>
                  <td className={styles.td}>
                    <span className="inline-flex items-center justify-center w-5 h-5 rounded-full bg-indigo-50 text-indigo-600 dark:bg-indigo-950/60 dark:text-indigo-400 text-xs font-bold font-mono">
                      {idx + 1}
                    </span>
                  </td>
                  <td className={styles.td}>
                    <div className="font-mono text-xs text-slate-900 dark:text-white font-medium">{p.policy_id}</div>
                  </td>
                  <td className={styles.td}>
                    <span className="font-mono text-xs font-semibold">{p.priority}</span>
                  </td>
                  <td className={styles.td}>
                    {p.is_mandatory ? (
                      <span className="inline-flex items-center gap-1 text-xs text-amber-600 dark:text-amber-400 font-medium">
                        <CheckCircle2 className="w-3.5 h-3.5" /> Mandatory
                      </span>
                    ) : (
                      <span className="text-xs text-slate-400">Optional</span>
                    )}
                  </td>
                  <td className={styles.td}>
                    <span className="font-mono text-xs">{p.version_strategy}</span>
                  </td>
                  <td className={styles.td}>
                    <span className="text-xs px-2 py-0.5 rounded-full font-medium bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300">
                      {p.status}
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

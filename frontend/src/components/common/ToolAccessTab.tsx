import React, { useState, useEffect } from "react";
import { Wrench, Shield, CheckCircle2, AlertCircle, Plus, Trash2 } from "lucide-react";
import serverClient from "../../services/shared/apiClient";
import styles from "./ToolAccessTab.module.css";

interface ToolAccessTabProps {
  agentId: string;
}

interface ToolBinding {
  id: string;
  tool_id: string;
  tool_name: string;
  tool_code: string;
  access_mode: string;
  capabilities: string[];
  status: string;
}

export const ToolAccessTab: React.FC<ToolAccessTabProps> = ({ agentId }) => {
  const [tools, setTools] = useState<ToolBinding[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadTools();
  }, [agentId]);

  const loadTools = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await serverClient.get<any>(
        `/api/registry/relationships?source_type=AGENT&source_id=${agentId}&relationship_type=USES_TOOL`
      );
      const rels = res?.items || res?.data?.items || (Array.isArray(res) ? res : []);
      const formatted: ToolBinding[] = rels.map((r: any) => ({
        id: r.id,
        tool_id: r.target_id,
        tool_name: r.target_name || `Tool ${r.target_id.slice(0, 8)}`,
        tool_code: r.target_code || "TOOL",
        access_mode: (r.metadata_json || {}).access_mode || "READ_WRITE",
        capabilities: (r.metadata_json || {}).capabilities || ["EXECUTE"],
        status: r.status || "ACTIVE",
      }));
      setTools(formatted);
    } catch {
      setTools([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.container}>
      <div className="flex items-center justify-between">
        <div>
          <h4 className="text-sm font-semibold text-slate-900 dark:text-white flex items-center gap-2">
            <Wrench className="w-4 h-4 text-indigo-500" /> Authorized Tool Capabilities
          </h4>
          <p className="text-xs text-slate-500 mt-0.5">
            Tools bound to this agent under USES_TOOL relationship with enforced access boundaries.
          </p>
        </div>
      </div>

      {loading ? (
        <div className="py-8 text-center text-xs text-slate-400">Loading authorized tools...</div>
      ) : tools.length === 0 ? (
        <div className="py-8 text-center text-xs text-slate-400 border border-dashed border-slate-200 dark:border-slate-800 rounded-xl">
          <Wrench className="w-8 h-8 mx-auto text-slate-300 dark:text-slate-700 mb-1" />
          No tools authorized for this agent yet.
        </div>
      ) : (
        <div className={styles.tableWrapper}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th className={styles.th}>Tool Name / Code</th>
                <th className={styles.th}>Access Mode</th>
                <th className={styles.th}>Capabilities</th>
                <th className={styles.th}>Status</th>
              </tr>
            </thead>
            <tbody>
              {tools.map((t) => (
                <tr key={t.id}>
                  <td className={styles.td}>
                    <div className="font-semibold text-slate-900 dark:text-white">{t.tool_name}</div>
                    <div className="text-[11px] font-mono text-slate-400">{t.tool_id}</div>
                  </td>
                  <td className={styles.td}>
                    <span className={styles.modeBadge}>{t.access_mode}</span>
                  </td>
                  <td className={styles.td}>
                    <div className="flex flex-wrap gap-1">
                      {t.capabilities.map((c, i) => (
                        <span key={i} className="text-[10px] px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 font-mono">
                          {c}
                        </span>
                      ))}
                    </div>
                  </td>
                  <td className={styles.td}>
                    <span className="text-xs px-2 py-0.5 rounded-full font-medium bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300">
                      {t.status}
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

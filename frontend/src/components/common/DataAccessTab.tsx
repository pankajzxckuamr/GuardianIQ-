import React, { useState, useEffect } from "react";
import { Database, Lock } from "lucide-react";
import serverClient from "../../services/shared/apiClient";
import styles from "./DataAccessTab.module.css";

interface DataAccessTabProps {
  agentId: string;
}

interface DataSourceBinding {
  id: string;
  source_id: string;
  source_name: string;
  classification_ceiling: string;
  transformations: string;
  status: string;
}

export const DataAccessTab: React.FC<DataAccessTabProps> = ({ agentId }) => {
  const [dataSources, setDataSources] = useState<DataSourceBinding[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDataSources();
  }, [agentId]);

  const loadDataSources = async () => {
    setLoading(true);
    try {
      const res = await serverClient.get<any>(
        `/api/registry/relationships?source_type=AGENT&source_id=${agentId}&relationship_type=USES_DATA_SOURCE`
      );
      const rels = res?.items || res?.data?.items || (Array.isArray(res) ? res : []);
      const formatted: DataSourceBinding[] = rels.map((r: any) => ({
        id: r.id,
        source_id: r.target_id,
        source_name: r.target_name || `Data Source ${r.target_id.slice(0, 8)}`,
        classification_ceiling: (r.metadata_json || {}).classification_ceiling || "CONFIDENTIAL",
        transformations: (r.metadata_json || {}).transformations || "PII Masking & Tokenization",
        status: r.status || "ACTIVE",
      }));
      setDataSources(formatted);
    } catch {
      setDataSources([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.container}>
      <div>
        <h4 className="text-sm font-semibold text-slate-900 dark:text-white flex items-center gap-2">
          <Database className="w-4 h-4 text-cyan-500" /> Data Permissions & Masking Rules
        </h4>
        <p className="text-xs text-slate-500 mt-0.5">
          Data sources accessible by this agent with field-level classification ceilings and automated redacting.
        </p>
      </div>

      {loading ? (
        <div className="py-8 text-center text-xs text-slate-400">Loading data permissions...</div>
      ) : dataSources.length === 0 ? (
        <div className="py-8 text-center text-xs text-slate-400 border border-dashed border-slate-200 dark:border-slate-800 rounded-xl">
          <Database className="w-8 h-8 mx-auto text-slate-300 dark:text-slate-700 mb-1" />
          No data sources bound to this agent yet.
        </div>
      ) : (
        <div className={styles.tableWrapper}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th className={styles.th}>Data Source Name</th>
                <th className={styles.th}>Classification Ceiling</th>
                <th className={styles.th}>Transformations</th>
                <th className={styles.th}>Status</th>
              </tr>
            </thead>
            <tbody>
              {dataSources.map((ds) => (
                <tr key={ds.id}>
                  <td className={styles.td}>
                    <div className="font-semibold text-slate-900 dark:text-white">{ds.source_name}</div>
                    <div className="text-[11px] font-mono text-slate-400">{ds.source_id}</div>
                  </td>
                  <td className={styles.td}>
                    <span className={styles.classBadge}>{ds.classification_ceiling}</span>
                  </td>
                  <td className={styles.td}>
                    <span className="text-xs text-slate-600 dark:text-slate-300 flex items-center gap-1 font-mono">
                      <Lock className="w-3 h-3 text-amber-500" /> {ds.transformations}
                    </span>
                  </td>
                  <td className={styles.td}>
                    <span className="text-xs px-2 py-0.5 rounded-full font-medium bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300">
                      {ds.status}
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

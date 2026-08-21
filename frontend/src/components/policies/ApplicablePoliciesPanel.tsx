import React, { useState } from "react";
import { Search, ShieldCheck, ArrowRight, AlertCircle, Layers, CheckCircle2 } from "lucide-react";
import type { EffectiveBinding, TargetType } from "../../types/policy";
import { fetchEffectiveBindings } from "../../services/policies/policyService";
import styles from "../../pages/PoliciesPage.module.css";

export const ApplicablePoliciesPanel: React.FC = () => {
  const [targetType, setTargetType] = useState<TargetType>("AGENT");
  const [targetId, setTargetId] = useState<string>("");
  const [bindings, setBindings] = useState<EffectiveBinding[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [hasResolved, setHasResolved] = useState<boolean>(false);

  const handleResolve = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!targetId.trim()) {
      setError("Please enter a valid target ID (UUID or code).");
      return;
    }

    setIsLoading(true);
    setError(null);
    try {
      const res = await fetchEffectiveBindings(targetType, targetId.trim());
      setBindings(res.data || []);
      setHasResolved(true);
    } catch (err: any) {
      setError(err.message || "Failed to resolve effective policy bindings.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
      {/* Search Header / Inspector */}
      <div style={{
        background: "var(--bg-tertiary, #151d30)",
        border: "1px solid var(--card-border, rgba(99, 102, 241, 0.2))",
        borderRadius: "12px",
        padding: "20px",
        display: "flex",
        flexDirection: "column",
        gap: "12px"
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: "8px", fontWeight: 700, fontSize: "1rem", color: "var(--text-primary, #f8fafc)" }}>
          <ShieldCheck className="w-5 h-5 text-indigo-400" />
          <span>Effective Policy Inspector & Binding Resolver</span>
        </div>
        <p style={{ fontSize: "0.8rem", color: "var(--text-secondary, #94a3b8)", margin: 0 }}>
          Resolve the complete authoritative hierarchy of direct, workflow-inherited, and tenant-mandatory policies applicable to any runtime target.
        </p>

        <form onSubmit={handleResolve} style={{ display: "flex", flexWrap: "wrap", gap: "12px", alignItems: "flex-end", marginTop: "4px" }}>
          <div style={{ width: "200px" }}>
            <label className={styles.formLabel}>Target Entity Type</label>
            <select
              value={targetType}
              onChange={(e) => setTargetType(e.target.value as TargetType)}
              className={styles.formSelect}
            >
              <option value="AGENT">Agent</option>
              <option value="WORKFLOW">Workflow</option>
              <option value="TOOL">Tool</option>
              <option value="DATA_SOURCE">Data Source</option>
            </select>
          </div>

          <div style={{ flex: 1, minWidth: "260px" }}>
            <label className={styles.formLabel}>Target Entity ID (UUID or identifier)</label>
            <input
              type="text"
              required
              placeholder="e.g. 86b9f691-6bc8-44eb-ad43-257720e657bf"
              value={targetId}
              onChange={(e) => setTargetId(e.target.value)}
              className={styles.formInput}
              style={{ fontFamily: "monospace", fontSize: "0.85rem" }}
            />
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className={styles.primaryBtn}
            style={{ height: "40px", padding: "0 20px" }}
          >
            <Search size={16} />
            {isLoading ? "Resolving..." : "Resolve Policies"}
          </button>
        </form>

        {error && (
          <div style={{
            padding: "10px 14px",
            borderRadius: "8px",
            background: "rgba(239, 68, 68, 0.15)",
            border: "1px solid rgba(239, 68, 68, 0.3)",
            color: "#f87171",
            fontSize: "0.8rem",
            display: "flex",
            alignItems: "center",
            gap: "8px"
          }}>
            <AlertCircle size={16} />
            <span>{error}</span>
          </div>
        )}
      </div>

      {/* Results Table */}
      {hasResolved && (
        <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "8px", fontWeight: 700, fontSize: "0.9rem", color: "var(--text-primary, #f8fafc)" }}>
            <Layers size={18} className="text-indigo-400" />
            <span>Resolved Effective Policies ({bindings.length})</span>
          </div>

          <div className={styles.tableWrapper}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th className={styles.th}>Precedence</th>
                  <th className={styles.th}>Policy ID</th>
                  <th className={styles.th}>Inheritance Target</th>
                  <th className={styles.th}>Priority Rank</th>
                  <th className={styles.th}>Mandatory</th>
                  <th className={styles.th}>Version Strategy</th>
                  <th className={styles.th}>Status</th>
                </tr>
              </thead>
              <tbody>
                {bindings.length === 0 ? (
                  <tr>
                    <td colSpan={7} style={{ padding: "48px 16px", textAlign: "center", color: "var(--text-muted, #64748b)" }}>
                      No active direct or inherited policies apply to this target.
                    </td>
                  </tr>
                ) : (
                  bindings.map((b, idx) => (
                    <tr key={b.id || idx} className={styles.row}>
                      <td className={styles.td}>
                        <span style={{
                          display: "inline-flex",
                          alignItems: "center",
                          justifyContent: "center",
                          width: "24px",
                          height: "24px",
                          borderRadius: "50%",
                          background: "rgba(99, 102, 241, 0.2)",
                          color: "#818cf8",
                          fontWeight: 700,
                          fontSize: "0.75rem"
                        }}>
                          #{idx + 1}
                        </span>
                      </td>
                      <td className={styles.td} style={{ fontFamily: "monospace", fontSize: "0.8rem", color: "var(--text-primary, #f8fafc)" }}>
                        {b.policy_id}
                      </td>
                      <td className={styles.td}>
                        <span style={{ fontWeight: 600 }}>{b.target_type}</span>:{" "}
                        <span style={{ fontFamily: "monospace", fontSize: "0.8rem", color: "var(--text-secondary, #94a3b8)" }}>
                          {b.target_id === "*" ? "GLOBAL (*)" : b.target_id}
                        </span>
                      </td>
                      <td className={styles.td} style={{ fontWeight: 700 }}>{b.priority}</td>
                      <td className={styles.td}>
                        {b.is_mandatory ? (
                          <span style={{
                            display: "inline-flex",
                            alignItems: "center",
                            gap: "4px",
                            padding: "2px 8px",
                            borderRadius: "4px",
                            fontSize: "0.75rem",
                            fontWeight: 600,
                            background: "rgba(16, 185, 129, 0.15)",
                            color: "#34d399",
                            border: "1px solid rgba(16, 185, 129, 0.3)"
                          }}>
                            <CheckCircle2 size={12} /> MANDATORY
                          </span>
                        ) : (
                          <span style={{ color: "var(--text-muted, #64748b)", fontSize: "0.75rem" }}>OPTIONAL</span>
                        )}
                      </td>
                      <td className={styles.td} style={{ fontSize: "0.8rem" }}>{b.version_strategy}</td>
                      <td className={styles.td}>
                        <span style={{
                          display: "inline-flex",
                          padding: "2px 8px",
                          borderRadius: "4px",
                          fontSize: "0.75rem",
                          fontWeight: 600,
                          background: b.status === "ACTIVE" ? "rgba(16, 185, 129, 0.15)" : "rgba(245, 158, 11, 0.15)",
                          color: b.status === "ACTIVE" ? "#34d399" : "#fbbf24"
                        }}>
                          {b.status}
                        </span>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

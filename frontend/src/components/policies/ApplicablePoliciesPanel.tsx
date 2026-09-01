import React, { useState, useEffect } from "react";
import { Search, ShieldCheck, AlertCircle, Layers, CheckCircle2 } from "lucide-react";
import type { EffectiveBinding, TargetType, Policy } from "../../types/policy";
import { fetchEffectiveBindings, fetchPolicies } from "../../services/policies/policyService";
import { listAgents, listTools, listDataSources, listWorkflows, listModels } from "../../services/registry/registryService";
import type { AIAgent, Tool, DataSource, Workflow, AIModel } from "../../services/registry/registryTypes";
import styles from "../../pages/PoliciesPage.module.css";

export const ApplicablePoliciesPanel: React.FC = () => {
  const [targetType, setTargetType] = useState<TargetType>("AGENT");
  const [targetId, setTargetId] = useState<string>("");
  const [isCustomTarget, setIsCustomTarget] = useState<boolean>(false);
  const [bindings, setBindings] = useState<EffectiveBinding[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [hasResolved, setHasResolved] = useState<boolean>(false);

  // Asset lists
  const [policies, setPolicies] = useState<Policy[]>([]);
  const [agents, setAgents] = useState<AIAgent[]>([]);
  const [tools, setTools] = useState<Tool[]>([]);
  const [dataSources, setDataSources] = useState<DataSource[]>([]);
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [models, setModels] = useState<AIModel[]>([]);

  useEffect(() => {
    loadAssets();
  }, []);

  const loadAssets = async () => {
    try {
      const [policiesRes, agentsRes, toolsRes, dsRes, wfRes, modelsRes] = await Promise.allSettled([
        fetchPolicies(),
        listAgents({ per_page: 100 }),
        listTools({ per_page: 100 }),
        listDataSources({ per_page: 100 }),
        listWorkflows({ per_page: 100 }),
        listModels({ per_page: 100 }),
      ]);

      if (policiesRes.status === "fulfilled" && policiesRes.value?.data) {
        const raw = policiesRes.value.data as any;
        setPolicies(Array.isArray(raw) ? raw : raw.items || []);
      }

      if (agentsRes.status === "fulfilled" && agentsRes.value?.data) {
        const raw = agentsRes.value.data as any;
        const items = Array.isArray(raw) ? raw : raw.items || [];
        setAgents(items);
        if (items.length > 0 && !targetId) {
          setTargetId(items[0].id);
        }
      }

      if (toolsRes.status === "fulfilled" && toolsRes.value?.data) {
        const raw = toolsRes.value.data as any;
        setTools(Array.isArray(raw) ? raw : raw.items || []);
      }

      if (dsRes.status === "fulfilled" && dsRes.value?.data) {
        const raw = dsRes.value.data as any;
        setDataSources(Array.isArray(raw) ? raw : raw.items || []);
      }

      if (wfRes.status === "fulfilled" && wfRes.value?.data) {
        const raw = wfRes.value.data as any;
        setWorkflows(Array.isArray(raw) ? raw : raw.items || []);
      }

      if (modelsRes.status === "fulfilled" && modelsRes.value?.data) {
        const raw = modelsRes.value.data as any;
        setModels(Array.isArray(raw) ? raw : raw.items || []);
      }
    } catch {
      // Non-blocking
    }
  };

  // Build lookup maps for names
  const assetNamesMap: Record<string, string> = {
    "*": "Global (All Targets)",
  };
  agents.forEach((a) => { assetNamesMap[a.id] = a.agent_name; });
  tools.forEach((t) => { assetNamesMap[t.id] = t.tool_name; });
  dataSources.forEach((d) => { assetNamesMap[d.id] = d.source_name; });
  workflows.forEach((w) => { assetNamesMap[w.id] = w.workflow_name; });
  models.forEach((m) => { assetNamesMap[m.id] = m.model_name; });

  const policiesMap: Record<string, Policy> = {};
  policies.forEach((p) => { policiesMap[p.id] = p; });

  const handleTargetTypeChange = (newType: TargetType) => {
    setTargetType(newType);
    setIsCustomTarget(false);
    if (newType === "AGENT" && agents.length > 0) {
      setTargetId(agents[0].id);
    } else if (newType === "TOOL" && tools.length > 0) {
      setTargetId(tools[0].id);
    } else if (newType === "DATA_SOURCE" && dataSources.length > 0) {
      setTargetId(dataSources[0].id);
    } else if (newType === "WORKFLOW" && workflows.length > 0) {
      setTargetId(workflows[0].id);
    } else if (newType === "MODEL" && models.length > 0) {
      setTargetId(models[0].id);
    } else {
      setTargetId("");
    }
  };

  const handleResolve = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!targetId.trim()) {
      setError("Please select or enter a valid target ID.");
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
          <span>Effective Policy Inspector &amp; Binding Resolver</span>
        </div>
        <p style={{ fontSize: "0.8rem", color: "var(--text-secondary, #94a3b8)", margin: 0 }}>
          Resolve the complete authoritative hierarchy of direct, workflow-inherited, and tenant-mandatory policies applicable to any runtime target.
        </p>

        <form onSubmit={handleResolve} style={{ display: "flex", flexWrap: "wrap", gap: "12px", alignItems: "flex-end", marginTop: "4px" }}>
          <div style={{ width: "180px" }}>
            <label className={styles.formLabel}>Target Entity Type</label>
            <select
              value={targetType}
              onChange={(e) => handleTargetTypeChange(e.target.value as TargetType)}
              className={styles.formSelect}
            >
              <option value="AGENT">Agent</option>
              <option value="WORKFLOW">Workflow</option>
              <option value="TOOL">Tool</option>
              <option value="DATA_SOURCE">Data Source</option>
              <option value="MODEL">AI Model</option>
            </select>
          </div>

          <div style={{ flex: 1, minWidth: "280px" }}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "4px" }}>
              <label className={styles.formLabel} style={{ margin: 0 }}>Target Entity Asset</label>
              <button
                type="button"
                onClick={() => setIsCustomTarget(!isCustomTarget)}
                style={{ background: "transparent", border: "none", color: "#818cf8", fontSize: "0.7rem", cursor: "pointer" }}
              >
                {isCustomTarget ? "Select from Registry" : "Enter Custom UUID"}
              </button>
            </div>

            {isCustomTarget ? (
              <input
                type="text"
                required
                placeholder="Enter target UUID..."
                value={targetId}
                onChange={(e) => setTargetId(e.target.value)}
                className={styles.formInput}
                style={{ fontFamily: "monospace", fontSize: "0.85rem" }}
              />
            ) : targetType === "AGENT" ? (
              <select
                required
                value={targetId}
                onChange={(e) => setTargetId(e.target.value)}
                className={styles.formSelect}
              >
                <option value="" disabled>Select an Agent...</option>
                {agents.map((a) => (
                  <option key={a.id} value={a.id}>
                    {a.agent_name} ({a.risk_level || "MEDIUM"} Risk)
                  </option>
                ))}
              </select>
            ) : targetType === "TOOL" ? (
              <select
                required
                value={targetId}
                onChange={(e) => setTargetId(e.target.value)}
                className={styles.formSelect}
              >
                <option value="" disabled>Select a Tool...</option>
                {tools.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.tool_name} ({t.access_mode || "EXECUTE"})
                  </option>
                ))}
              </select>
            ) : targetType === "DATA_SOURCE" ? (
              <select
                required
                value={targetId}
                onChange={(e) => setTargetId(e.target.value)}
                className={styles.formSelect}
              >
                <option value="" disabled>Select a Data Source...</option>
                {dataSources.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.source_name} ({(d as any).sensitivity_level || d.classification || "INTERNAL"})
                  </option>
                ))}
              </select>
            ) : targetType === "WORKFLOW" ? (
              <select
                required
                value={targetId}
                onChange={(e) => setTargetId(e.target.value)}
                className={styles.formSelect}
              >
                <option value="" disabled>Select a Workflow...</option>
                {workflows.map((w) => (
                  <option key={w.id} value={w.id}>
                    {w.workflow_name} ({w.business_criticality || "STANDARD"})
                  </option>
                ))}
              </select>
            ) : targetType === "MODEL" ? (
              <select
                required
                value={targetId}
                onChange={(e) => setTargetId(e.target.value)}
                className={styles.formSelect}
              >
                <option value="" disabled>Select an AI Model...</option>
                {models.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.model_name} ({m.model_type || "LLM"})
                  </option>
                ))}
              </select>
            ) : (
              <input
                type="text"
                required
                placeholder="Enter target UUID..."
                value={targetId}
                onChange={(e) => setTargetId(e.target.value)}
                className={styles.formInput}
              />
            )}
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
                  <th className={styles.th}>Policy</th>
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
                  bindings.map((b, idx) => {
                    const matchedPolicy = policiesMap[b.policy_id];
                    const policyDisplayName = matchedPolicy?.name || b.policy_name || b.policy_id.slice(0, 8) + "...";
                    const policyCodeDisplay = matchedPolicy?.policy_code || b.policy_code || b.policy_id;
                    const targetDisplayName = assetNamesMap[b.target_id] || (b.target_id === "*" ? "Global (All Entities)" : b.target_id);

                    return (
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
                        <td className={styles.td}>
                          <div style={{ fontWeight: 600, fontSize: "0.85rem", color: "var(--text-primary, #f8fafc)" }}>
                            {policyDisplayName}
                          </div>
                          <div style={{ fontFamily: "monospace", fontSize: "0.75rem", color: "var(--text-muted, #64748b)", marginTop: "2px" }}>
                            {policyCodeDisplay}
                          </div>
                        </td>
                        <td className={styles.td}>
                          <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                            <span style={{
                              padding: "1px 6px",
                              borderRadius: "4px",
                              fontSize: "0.7rem",
                              fontWeight: 700,
                              background: "rgba(99, 102, 241, 0.15)",
                              color: "#818cf8",
                              border: "1px solid rgba(99, 102, 241, 0.25)"
                            }}>
                              {b.target_type}
                            </span>
                            <span style={{ fontWeight: 600, fontSize: "0.85rem", color: "var(--text-primary, #f8fafc)" }}>
                              {targetDisplayName}
                            </span>
                          </div>
                          {b.target_id !== "*" && (
                            <div style={{ fontFamily: "monospace", fontSize: "0.7rem", color: "var(--text-muted, #64748b)", marginTop: "2px" }}>
                              {b.target_id}
                            </div>
                          )}
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
                            color: b.status === "ACTIVE" ? "#34d399" : "#fbbf24",
                            border: `1px solid ${b.status === "ACTIVE" ? "rgba(16, 185, 129, 0.3)" : "rgba(245, 158, 11, 0.3)"}`
                          }}>
                            {b.status}
                          </span>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};


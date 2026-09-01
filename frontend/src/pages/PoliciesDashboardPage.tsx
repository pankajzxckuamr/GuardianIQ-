import React, { useState, useEffect } from "react";
import { PageHeader } from "../components/common/PageHeader";
import { ShieldCheck, Layers, Link2, PlusCircle, AlertCircle, Sparkles, X, Trash2, Plus, Search } from "lucide-react";
import { PolicyListTable } from "../components/policies/PolicyListTable";
import { PolicyDetailView } from "../components/policies/PolicyDetailView";
import { AttachPolicyDrawer } from "../components/policies/AttachPolicyDrawer";
import { ApplicablePoliciesPanel } from "../components/policies/ApplicablePoliciesPanel";
import {
  fetchPolicies,
  fetchPolicyBindings,
  createPolicy,
  revokePolicyBinding,
} from "../services/policies/policyService";
import { listAgents, listTools, listDataSources, listWorkflows } from "../services/registry/registryService";
import type { Policy, PolicyBinding, PolicyCategory, EnforcementMode, PolicyRule } from "../types/policy";
import styles from "./PoliciesPage.module.css";

export const PoliciesDashboardPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<"policies" | "bindings" | "resolver">("policies");
  const [policies, setPolicies] = useState<Policy[]>([]);
  const [bindings, setBindings] = useState<PolicyBinding[]>([]);
  const [assetNamesMap, setAssetNamesMap] = useState<Record<string, string>>({});
  const [selectedPolicy, setSelectedPolicy] = useState<Policy | null>(null);
  const [isAttachDrawerOpen, setIsAttachDrawerOpen] = useState<boolean>(false);
  const [attachTargetPolicy, setAttachTargetPolicy] = useState<Policy | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Create Policy Modal state
  const [isCreateModalOpen, setIsCreateModalOpen] = useState<boolean>(false);
  const [newPolicyCode, setNewPolicyCode] = useState("");
  const [newPolicyName, setNewPolicyName] = useState("");
  const [newPolicyDesc, setNewPolicyDesc] = useState("");
  const [newPolicyCategory, setNewPolicyCategory] = useState<PolicyCategory>("GENERAL");
  const [newPolicyMode, setNewPolicyMode] = useState<EnforcementMode>("BLOCKING");
  const [newPolicyPriority, setNewPolicyPriority] = useState<number>(100);
  const [initialRules, setInitialRules] = useState<Array<{
    rule_code: string;
    name: string;
    description?: string;
    rule_type: string;
    target_type: string;
    condition_expression: string;
    action: "ALLOW" | "DENY" | "MODIFY" | "REQUIRE_APPROVAL" | "ESCALATE";
    severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  }>>([]);
  const [isCreating, setIsCreating] = useState<boolean>(false);

  // Bindings tab search & pagination state
  const [bindingsPage, setBindingsPage] = useState<number>(1);
  const [bindingsSearch, setBindingsSearch] = useState<string>("");
  const [bindingsTargetFilter, setBindingsTargetFilter] = useState<string>("ALL");
  const bindingsPageSize = 10;

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [policiesRes, bindingsRes, agentsRes, toolsRes, dsRes, wfRes] = await Promise.allSettled([
        fetchPolicies(),
        fetchPolicyBindings(),
        listAgents({ per_page: 100 }),
        listTools({ per_page: 100 }),
        listDataSources({ per_page: 100 }),
        listWorkflows({ per_page: 100 }),
      ]);

      const loadedPolicies: Policy[] = policiesRes.status === "fulfilled" && policiesRes.value?.data ? policiesRes.value.data : [];
      loadedPolicies.sort((a, b) => new Date(b.created_at || 0).getTime() - new Date(a.created_at || 0).getTime());
      setPolicies(loadedPolicies);

      const loadedBindings: PolicyBinding[] = bindingsRes.status === "fulfilled" && bindingsRes.value?.data ? bindingsRes.value.data : [];
      loadedBindings.sort((a, b) => new Date(b.created_at || 0).getTime() - new Date(a.created_at || 0).getTime());
      setBindings(loadedBindings);

      // Build Asset Name Lookup Map
      const namesMap: Record<string, string> = {};
      if (agentsRes.status === "fulfilled" && agentsRes.value?.data) {
        const items = Array.isArray(agentsRes.value.data) ? agentsRes.value.data : (agentsRes.value.data as any).items || [];
        items.forEach((a: any) => { namesMap[a.id] = a.agent_name; });
      }
      if (toolsRes.status === "fulfilled" && toolsRes.value?.data) {
        const items = Array.isArray(toolsRes.value.data) ? toolsRes.value.data : (toolsRes.value.data as any).items || [];
        items.forEach((t: any) => { namesMap[t.id] = t.tool_name; });
      }
      if (dsRes.status === "fulfilled" && dsRes.value?.data) {
        const items = Array.isArray(dsRes.value.data) ? dsRes.value.data : (dsRes.value.data as any).items || [];
        items.forEach((d: any) => { namesMap[d.id] = d.source_name; });
      }
      if (wfRes.status === "fulfilled" && wfRes.value?.data) {
        const items = Array.isArray(wfRes.value.data) ? wfRes.value.data : (wfRes.value.data as any).items || [];
        items.forEach((w: any) => { namesMap[w.id] = w.workflow_name; });
      }
      setAssetNamesMap(namesMap);
    } catch (err: any) {
      setError(err.message || "Failed to load governance policies");
    } finally {
      setIsLoading(false);
    }
  };

  const handleAddRuleRow = () => {
    const nextOrder = initialRules.length + 1;
    const prefix = newPolicyCode ? newPolicyCode.replace(/^POL-/, "") : "RULE";
    setInitialRules([
      ...initialRules,
      {
        rule_code: `RULE-${prefix}-${String(nextOrder).padStart(3, "0")}`,
        name: "",
        description: "",
        rule_type: "GENERAL",
        target_type: "AGENT",
        condition_expression: "true",
        action: "DENY",
        severity: "HIGH",
      },
    ]);
  };

  const handleUpdateRuleRow = (index: number, field: string, value: any) => {
    setInitialRules((prev) =>
      prev.map((r, idx) => (idx === index ? { ...r, [field]: value } : r))
    );
  };

  const handleRemoveRuleRow = (index: number) => {
    setInitialRules((prev) => prev.filter((_, idx) => idx !== index));
  };

  const handleCreatePolicySubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsCreating(true);
    setError(null);
    try {
      const cleanedRules: PolicyRule[] = initialRules
        .filter((r) => r.rule_code.trim() && r.name.trim())
        .map((r, idx) => ({
          rule_code: r.rule_code.trim().toUpperCase(),
          name: r.name.trim(),
          description: r.description?.trim() || "",
          rule_type: r.rule_type,
          target_type: r.target_type,
          target_id: "*",
          condition_expression: r.condition_expression.trim() || "true",
          condition_json: {},
          action: r.action,
          severity: r.severity,
          execution_order: idx + 1,
          is_active: true,
        }));

      await createPolicy({
        policy_code: newPolicyCode.trim().toUpperCase(),
        name: newPolicyName.trim(),
        description: newPolicyDesc.trim() || undefined,
        category: newPolicyCategory,
        enforcement_mode: newPolicyMode,
        priority: Number(newPolicyPriority),
        initial_rules: cleanedRules.length > 0 ? cleanedRules : undefined,
      });

      setIsCreateModalOpen(false);
      setNewPolicyCode("");
      setNewPolicyName("");
      setNewPolicyDesc("");
      setNewPolicyPriority(100);
      setInitialRules([]);
      await loadData();
    } catch (err: any) {
      setError(err.message || "Failed to create policy");
    } finally {
      setIsCreating(false);
    }
  };

  const handleRevokeBinding = async (bindingId: string) => {
    if (!window.confirm("Are you sure you want to revoke this policy binding?")) return;
    try {
      await revokePolicyBinding(bindingId);
      await loadData();
    } catch (err: any) {
      setError(err.message || "Failed to revoke policy binding");
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "24px", paddingBottom: "48px" }}>
      {/* Top Header */}
      <PageHeader
        title="Policy & Binding Administration"
        description="Define enterprise governance policies, manage authoritative target bindings, and inspect effective runtime compliance."
        actions={
          <div style={{ display: "flex", gap: "10px" }}>
            <button
              onClick={() => {
                setAttachTargetPolicy(null);
                setIsAttachDrawerOpen(true);
              }}
              className={styles.secondaryBtn}
            >
              <Link2 size={16} /> Attach Policy
            </button>
            <button
              onClick={() => {
                setNewPolicyCode("");
                setNewPolicyName("");
                setNewPolicyDesc("");
                setNewPolicyPriority(100);
                setInitialRules([]);
                setIsCreateModalOpen(true);
              }}
              className={styles.primaryBtn}
            >
              <PlusCircle size={16} /> Create Policy
            </button>
          </div>
        }
      />

      {/* Top Summary Stats */}
      <div className={styles.statsGrid}>
        <div className={styles.statCard}>
          <div className={styles.statHeader}>
            <span className={styles.statLabel}>Active Policies</span>
            <ShieldCheck className="w-5 h-5 text-indigo-400" />
          </div>
          <div className={styles.statValue}>{policies.length}</div>
          <div className={styles.statSubtext}>Enforced across boundary gateway</div>
        </div>

        <div className={styles.statCard}>
          <div className={styles.statHeader}>
            <span className={styles.statLabel}>Total Bindings</span>
            <Link2 className="w-5 h-5 text-emerald-400" />
          </div>
          <div className={styles.statValue}>{bindings.length}</div>
          <div className={styles.statSubtext}>Direct &amp; inherited target attachments</div>
        </div>

        <div className={styles.statCard}>
          <div className={styles.statHeader}>
            <span className={styles.statLabel}>Enforcement Strategy</span>
            <Sparkles className="w-5 h-5 text-purple-400" />
          </div>
          <div className={styles.statValue} style={{ fontSize: "1.3rem", color: "#a855f7" }}>
            Multi-Layered
          </div>
          <div className={styles.statSubtext}>AST Rules &amp; Decision Combiner</div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className={styles.tabsNav}>
        <button
          onClick={() => {
            setActiveTab("policies");
            setSelectedPolicy(null);
          }}
          className={`${styles.tabBtn} ${activeTab === "policies" ? styles.activeTabBtn : ""}`}
        >
          <ShieldCheck size={16} /> Policies Registry ({policies.length})
        </button>
        <button
          onClick={() => {
            setActiveTab("bindings");
            setSelectedPolicy(null);
          }}
          className={`${styles.tabBtn} ${activeTab === "bindings" ? styles.activeTabBtn : ""}`}
        >
          <Link2 size={16} /> Policy Bindings ({bindings.length})
        </button>
        <button
          onClick={() => {
            setActiveTab("resolver");
            setSelectedPolicy(null);
          }}
          className={`${styles.tabBtn} ${activeTab === "resolver" ? styles.activeTabBtn : ""}`}
        >
          <Layers size={16} /> Applicable Policies Inspector
        </button>
      </div>

      {/* Error Banner */}
      {error && (
        <div style={{
          padding: "12px 16px",
          borderRadius: "8px",
          background: "rgba(239, 68, 68, 0.15)",
          border: "1px solid rgba(239, 68, 68, 0.3)",
          color: "#f87171",
          fontSize: "0.85rem",
          display: "flex",
          alignItems: "center",
          gap: "8px"
        }}>
          <AlertCircle size={18} />
          <span>{error}</span>
        </div>
      )}

      {/* Main Tab Content */}
      <div>
        {activeTab === "policies" ? (
          selectedPolicy ? (
            <PolicyDetailView
              policy={selectedPolicy}
              onBack={() => setSelectedPolicy(null)}
              onAttachClick={(p) => {
                setAttachTargetPolicy(p);
                setIsAttachDrawerOpen(true);
              }}
              onRefresh={loadData}
            />
          ) : (
            <PolicyListTable
              policies={policies}
              isLoading={isLoading}
              onSelectPolicy={(p) => setSelectedPolicy(p)}
              onAttachPolicy={(p) => {
                setAttachTargetPolicy(p);
                setIsAttachDrawerOpen(true);
              }}
              onCreatePolicyClick={() => setIsCreateModalOpen(true)}
            />
          )
        ) : activeTab === "bindings" ? (
          /* Tab 2: Policy Bindings */
          (() => {
            const filteredBindings = bindings.filter((b) => {
              const matchedPolicy = policies.find((p) => p.id === b.policy_id);
              const targetName = assetNamesMap[b.target_id] || (b.target_id === "*" ? "GLOBAL (*)" : b.target_id);
              const searchLower = bindingsSearch.toLowerCase();
              const matchesSearch =
                !bindingsSearch ||
                (matchedPolicy?.name && matchedPolicy.name.toLowerCase().includes(searchLower)) ||
                (matchedPolicy?.policy_code && matchedPolicy.policy_code.toLowerCase().includes(searchLower)) ||
                b.target_type.toLowerCase().includes(searchLower) ||
                targetName.toLowerCase().includes(searchLower) ||
                b.target_id.toLowerCase().includes(searchLower);

              const matchesTarget =
                bindingsTargetFilter === "ALL" ||
                b.target_type.toUpperCase() === bindingsTargetFilter.toUpperCase();

              return matchesSearch && matchesTarget;
            });

            const totalBindings = filteredBindings.length;
            const totalBindingsPages = Math.ceil(totalBindings / bindingsPageSize) || 1;
            const startRecord = totalBindings === 0 ? 0 : (bindingsPage - 1) * bindingsPageSize + 1;
            const endRecord = Math.min(bindingsPage * bindingsPageSize, totalBindings);
            const paginatedBindings = filteredBindings.slice(
              (bindingsPage - 1) * bindingsPageSize,
              bindingsPage * bindingsPageSize
            );

            return (
              <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
                {/* Search & Filter Toolbar */}
                <div className={styles.toolbar}>
                  <div style={{ display: "flex", alignItems: "center", gap: "10px", flex: 1, flexWrap: "wrap" }}>
                    <div className={styles.searchBox}>
                      <Search size={16} style={{ color: "var(--text-muted, #64748b)" }} />
                      <input
                        type="text"
                        placeholder="Search bindings by policy, target entity, or ID..."
                        value={bindingsSearch}
                        onChange={(e) => {
                          setBindingsSearch(e.target.value);
                          setBindingsPage(1);
                        }}
                        className={styles.searchInput}
                      />
                    </div>

                    <select
                      value={bindingsTargetFilter}
                      onChange={(e) => {
                        setBindingsTargetFilter(e.target.value);
                        setBindingsPage(1);
                      }}
                      className={styles.filterSelect}
                    >
                      <option value="ALL">All Target Types</option>
                      <option value="AGENT">AI Agents (AGENT)</option>
                      <option value="MODEL">AI Models (MODEL)</option>
                      <option value="TOOL">Tools (TOOL)</option>
                      <option value="DATA_SOURCE">Data Sources (DATA_SOURCE)</option>
                      <option value="WORKFLOW">Workflows (WORKFLOW)</option>
                      <option value="DEPARTMENT">Departments (DEPARTMENT)</option>
                      <option value="GLOBAL">Global (*)</option>
                    </select>
                  </div>
                </div>

                <div className={styles.tableWrapper}>
                  <table className={styles.table}>
                    <thead>
                      <tr>
                        <th className={styles.th}>Policy</th>
                        <th className={styles.th}>Target Type</th>
                        <th className={styles.th}>Target Entity</th>
                        <th className={styles.th}>Scope</th>
                        <th className={styles.th}>Priority</th>
                        <th className={styles.th}>Mandatory</th>
                        <th className={styles.th}>Strategy</th>
                        <th className={styles.th}>Status</th>
                        <th className={styles.th} style={{ textAlign: "right" }}>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {paginatedBindings.length === 0 ? (
                        <tr>
                          <td colSpan={9} style={{ padding: "48px 16px", textAlign: "center", color: "var(--text-muted, #64748b)" }}>
                            No policy bindings found matching your filters.
                          </td>
                        </tr>
                      ) : (
                        paginatedBindings.map((b) => {
                          const matchedPolicy = policies.find((p) => p.id === b.policy_id);
                          const targetName = assetNamesMap[b.target_id] || (b.target_id === "*" ? "GLOBAL (*)" : b.target_id);

                          return (
                            <tr key={b.id} className={styles.row}>
                              <td className={styles.td}>
                                <div style={{ fontWeight: 600, fontSize: "0.85rem", color: "var(--text-primary, #f8fafc)" }}>
                                  {matchedPolicy?.name || b.policy_id.slice(0, 8) + "..."}
                                </div>
                                <div style={{ fontFamily: "monospace", fontSize: "0.75rem", color: "var(--text-muted, #64748b)" }}>
                                  {matchedPolicy?.policy_code || b.policy_id}
                                </div>
                              </td>
                              <td className={styles.td} style={{ fontWeight: 600 }}>{b.target_type}</td>
                              <td className={styles.td}>
                                <div style={{ fontWeight: 600, fontSize: "0.85rem", color: "var(--text-primary, #f8fafc)" }}>
                                  {targetName}
                                </div>
                                {b.target_id !== "*" && (
                                  <div style={{ fontFamily: "monospace", fontSize: "0.7rem", color: "var(--text-muted, #64748b)" }}>
                                    {b.target_id}
                                  </div>
                                )}
                              </td>
                              <td className={styles.td}>{b.binding_scope || "DIRECT"}</td>
                              <td className={styles.td} style={{ fontWeight: 700 }}>{b.priority}</td>
                              <td className={styles.td}>
                                {b.is_mandatory ? (
                                  <span style={{ color: "#34d399", fontWeight: 600, fontSize: "0.75rem" }}>YES</span>
                                ) : (
                                  <span style={{ color: "var(--text-muted, #64748b)", fontSize: "0.75rem" }}>NO</span>
                                )}
                              </td>
                              <td className={styles.td} style={{ fontSize: "0.75rem" }}>{b.version_strategy}</td>
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
                              <td className={styles.td} style={{ textAlign: "right" }}>
                                <button
                                  onClick={() => handleRevokeBinding(b.id)}
                                  style={{
                                    background: "rgba(239, 68, 68, 0.1)",
                                    border: "1px solid rgba(239, 68, 68, 0.3)",
                                    color: "#f87171",
                                    padding: "4px 8px",
                                    borderRadius: "4px",
                                    fontSize: "0.75rem",
                                    cursor: "pointer"
                                  }}
                                >
                                  Revoke
                                </button>
                              </td>
                            </tr>
                          );
                        })
                      )}
                    </tbody>
                  </table>
                </div>

                {/* Bindings Pagination Controls */}
                {totalBindings > 0 && (
                  <div style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    padding: "12px 16px",
                    background: "rgba(15, 23, 42, 0.6)",
                    border: "1px solid rgba(255, 255, 255, 0.08)",
                    borderRadius: "8px",
                    fontSize: "0.85rem",
                    color: "var(--text-secondary, #94a3b8)"
                  }}>
                    <div>
                      Showing <strong style={{ color: "#fff" }}>{startRecord}-{endRecord}</strong> of <strong style={{ color: "#fff" }}>{totalBindings}</strong> bindings
                    </div>
                    <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                      <span>Page <strong style={{ color: "#fff" }}>{bindingsPage}</strong> of <strong style={{ color: "#fff" }}>{totalBindingsPages}</strong></span>
                      <div style={{ display: "flex", gap: "6px" }}>
                        <button
                          type="button"
                          disabled={bindingsPage <= 1}
                          onClick={() => setBindingsPage((prev) => Math.max(1, prev - 1))}
                          style={{
                            padding: "4px 12px",
                            borderRadius: "6px",
                            border: "1px solid rgba(255, 255, 255, 0.1)",
                            background: bindingsPage <= 1 ? "rgba(255, 255, 255, 0.02)" : "rgba(255, 255, 255, 0.08)",
                            color: bindingsPage <= 1 ? "#475569" : "#fff",
                            cursor: bindingsPage <= 1 ? "not-allowed" : "pointer",
                            fontSize: "0.8rem",
                            fontWeight: 600
                          }}
                        >
                          Previous
                        </button>
                        <button
                          type="button"
                          disabled={bindingsPage >= totalBindingsPages}
                          onClick={() => setBindingsPage((prev) => Math.min(totalBindingsPages, prev + 1))}
                          style={{
                            padding: "4px 12px",
                            borderRadius: "6px",
                            border: "1px solid rgba(255, 255, 255, 0.1)",
                            background: bindingsPage >= totalBindingsPages ? "rgba(255, 255, 255, 0.02)" : "rgba(255, 255, 255, 0.08)",
                            color: bindingsPage >= totalBindingsPages ? "#475569" : "#fff",
                            cursor: bindingsPage >= totalBindingsPages ? "not-allowed" : "pointer",
                            fontSize: "0.8rem",
                            fontWeight: 600
                          }}
                        >
                          Next
                        </button>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            );
          })()
        ) : (
          /* Tab 3: Applicable Policies Inspector */
          <ApplicablePoliciesPanel />
        )}
      </div>

      {/* Attach Policy Modal */}
      <AttachPolicyDrawer
        isOpen={isAttachDrawerOpen}
        onClose={() => setIsAttachDrawerOpen(false)}
        policy={attachTargetPolicy}
        policies={policies}
        onSuccess={loadData}
      />

      {/* Create Policy Centered Modal with Rules Builder */}
      {isCreateModalOpen && (
        <div className={styles.modalBackdrop} onClick={(e) => e.target === e.currentTarget && setIsCreateModalOpen(false)}>
          <div className={styles.modalContent} style={{ maxWidth: "780px" }}>
            <div className={styles.modalHeader}>
              <div className={styles.modalTitle}>
                <PlusCircle size={20} className="text-indigo-400" />
                <span>Create New Governance Policy</span>
              </div>
              <button onClick={() => setIsCreateModalOpen(false)} className={styles.modalCloseBtn}>
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleCreatePolicySubmit}>
              <div className={styles.modalBody} style={{ maxHeight: "70vh", overflowY: "auto" }}>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 2fr", gap: "12px" }}>
                  <div className={styles.formGroup}>
                    <label className={styles.formLabel}>Policy Code</label>
                    <input
                      type="text"
                      required
                      placeholder="Enter policy code (e.g. POL-CODE-001)..."
                      value={newPolicyCode}
                      onChange={(e) => setNewPolicyCode(e.target.value.toUpperCase())}
                      className={styles.formInput}
                    />
                  </div>

                  <div className={styles.formGroup}>
                    <label className={styles.formLabel}>Policy Name</label>
                    <input
                      type="text"
                      required
                      placeholder="Enter policy name..."
                      value={newPolicyName}
                      onChange={(e) => setNewPolicyName(e.target.value)}
                      className={styles.formInput}
                    />
                  </div>
                </div>

                <div className={styles.formGroup}>
                  <label className={styles.formLabel}>Description</label>
                  <textarea
                    rows={2}
                    placeholder="Describe policy intent and constraints..."
                    value={newPolicyDesc}
                    onChange={(e) => setNewPolicyDesc(e.target.value)}
                    className={styles.formTextarea}
                  />
                </div>

                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "12px" }}>
                  <div className={styles.formGroup}>
                    <label className={styles.formLabel}>Category</label>
                    <select
                      value={newPolicyCategory}
                      onChange={(e) => setNewPolicyCategory(e.target.value as PolicyCategory)}
                      className={styles.formSelect}
                    >
                      <option value="GENERAL">General</option>
                      <option value="ACCESS_CONTROL">Access Control</option>
                      <option value="DATA_PROTECTION">Data Protection</option>
                      <option value="FINANCIAL_SAFETY">Financial Safety</option>
                      <option value="OPERATIONAL_SAFETY">Operational Safety</option>
                      <option value="MODEL_SAFETY">Model Safety</option>
                    </select>
                  </div>

                  <div className={styles.formGroup}>
                    <label className={styles.formLabel}>Enforcement Mode</label>
                    <select
                      value={newPolicyMode}
                      onChange={(e) => setNewPolicyMode(e.target.value as EnforcementMode)}
                      className={styles.formSelect}
                    >
                      <option value="BLOCKING">BLOCKING</option>
                      <option value="MONITORING">MONITORING</option>
                      <option value="SHADOW">SHADOW</option>
                    </select>
                  </div>

                  <div className={styles.formGroup}>
                    <label className={styles.formLabel}>Priority (1-1000)</label>
                    <input
                      type="number"
                      min="1"
                      max="1000"
                      value={newPolicyPriority}
                      onChange={(e) => setNewPolicyPriority(parseInt(e.target.value) || 100)}
                      className={styles.formInput}
                    />
                  </div>
                </div>

                {/* Section: Initial Governance Rules */}
                <div style={{
                  marginTop: "8px",
                  padding: "16px",
                  borderRadius: "10px",
                  background: "rgba(15, 23, 42, 0.6)",
                  border: "1px solid rgba(99, 102, 241, 0.2)",
                  display: "flex",
                  flexDirection: "column",
                  gap: "12px",
                }}>
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                    <div>
                      <div style={{ fontSize: "0.875rem", fontWeight: 700, color: "var(--text-primary, #f8fafc)" }}>
                        Initial Governance Rules ({initialRules.length})
                      </div>
                      <div style={{ fontSize: "0.75rem", color: "var(--text-secondary, #94a3b8)" }}>
                        Define rule statements to be evaluated when enforcing this policy.
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={handleAddRuleRow}
                      style={{
                        display: "inline-flex",
                        alignItems: "center",
                        gap: "6px",
                        padding: "6px 12px",
                        borderRadius: "6px",
                        fontSize: "0.75rem",
                        fontWeight: 600,
                        background: "rgba(99, 102, 241, 0.2)",
                        border: "1px solid rgba(99, 102, 241, 0.4)",
                        color: "#a5b4fc",
                        cursor: "pointer",
                      }}
                    >
                      <Plus size={14} /> Add Rule
                    </button>
                  </div>

                  {initialRules.length === 0 ? (
                    <div style={{
                      padding: "16px",
                      textAlign: "center",
                      color: "var(--text-muted, #64748b)",
                      fontSize: "0.8rem",
                      border: "1px dashed rgba(255, 255, 255, 0.1)",
                      borderRadius: "8px",
                    }}>
                      No initial rules added. Click <strong>"+ Add Rule"</strong> to add rules to version 1.
                    </div>
                  ) : (
                    <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                      {initialRules.map((rule, idx) => (
                        <div
                          key={idx}
                          style={{
                            padding: "12px",
                            borderRadius: "8px",
                            background: "rgba(10, 14, 23, 0.8)",
                            border: "1px solid rgba(99, 102, 241, 0.2)",
                            display: "flex",
                            flexDirection: "column",
                            gap: "8px",
                          }}
                        >
                          <div style={{ display: "grid", gridTemplateColumns: "1fr 2fr 1fr 1fr auto", gap: "8px", alignItems: "center" }}>
                            <div>
                              <label style={{ fontSize: "0.7rem", color: "var(--text-muted, #64748b)" }}>Rule Code</label>
                              <input
                                type="text"
                                required
                                value={rule.rule_code}
                                onChange={(e) => handleUpdateRuleRow(idx, "rule_code", e.target.value.toUpperCase())}
                                className={styles.formInput}
                                style={{ padding: "4px 8px", fontSize: "0.75rem", fontFamily: "monospace" }}
                              />
                            </div>
                            <div>
                              <label style={{ fontSize: "0.7rem", color: "var(--text-muted, #64748b)" }}>Rule Name</label>
                              <input
                                type="text"
                                required
                                placeholder="Enter rule name..."
                                value={rule.name}
                                onChange={(e) => handleUpdateRuleRow(idx, "name", e.target.value)}
                                className={styles.formInput}
                                style={{ padding: "4px 8px", fontSize: "0.75rem" }}
                              />
                            </div>
                            <div>
                              <label style={{ fontSize: "0.7rem", color: "var(--text-muted, #64748b)" }}>Action</label>
                              <select
                                value={rule.action}
                                onChange={(e) => handleUpdateRuleRow(idx, "action", e.target.value)}
                                className={styles.formSelect}
                                style={{ padding: "4px 8px", fontSize: "0.75rem" }}
                              >
                                <option value="DENY">DENY</option>
                                <option value="REQUIRE_APPROVAL">REQUIRE_APPROVAL</option>
                                <option value="ALLOW">ALLOW</option>
                                <option value="MODIFY">MODIFY</option>
                                <option value="ESCALATE">ESCALATE</option>
                              </select>
                            </div>
                            <div>
                              <label style={{ fontSize: "0.7rem", color: "var(--text-muted, #64748b)" }}>Severity</label>
                              <select
                                value={rule.severity}
                                onChange={(e) => handleUpdateRuleRow(idx, "severity", e.target.value)}
                                className={styles.formSelect}
                                style={{ padding: "4px 8px", fontSize: "0.75rem" }}
                              >
                                <option value="LOW">LOW</option>
                                <option value="MEDIUM">MEDIUM</option>
                                <option value="HIGH">HIGH</option>
                                <option value="CRITICAL">CRITICAL</option>
                              </select>
                            </div>
                            <button
                              type="button"
                              onClick={() => handleRemoveRuleRow(idx)}
                              style={{
                                background: "rgba(239, 68, 68, 0.15)",
                                border: "1px solid rgba(239, 68, 68, 0.3)",
                                color: "#f87171",
                                padding: "6px",
                                borderRadius: "6px",
                                cursor: "pointer",
                                marginTop: "14px",
                              }}
                              title="Delete Rule"
                            >
                              <Trash2 size={14} />
                            </button>
                          </div>

                          <div style={{ display: "grid", gridTemplateColumns: "1fr 2fr", gap: "8px" }}>
                            <div>
                              <label style={{ fontSize: "0.7rem", color: "var(--text-muted, #64748b)" }}>Target Type</label>
                              <select
                                value={rule.target_type}
                                onChange={(e) => handleUpdateRuleRow(idx, "target_type", e.target.value)}
                                className={styles.formSelect}
                                style={{ padding: "4px 8px", fontSize: "0.75rem" }}
                              >
                                <option value="AGENT">AGENT</option>
                                <option value="TOOL">TOOL</option>
                                <option value="DATA_SOURCE">DATA_SOURCE</option>
                                <option value="WORKFLOW">WORKFLOW</option>
                                <option value="MODEL">MODEL</option>
                              </select>
                            </div>
                            <div>
                              <label style={{ fontSize: "0.7rem", color: "var(--text-muted, #64748b)" }}>Condition Expression</label>
                              <input
                                type="text"
                                placeholder="Enter boolean expression (e.g. agent.risk_level in ['HIGH', 'CRITICAL'])..."
                                value={rule.condition_expression}
                                onChange={(e) => handleUpdateRuleRow(idx, "condition_expression", e.target.value)}
                                className={styles.formInput}
                                style={{ padding: "4px 8px", fontSize: "0.75rem", fontFamily: "monospace", color: "#a5b4fc" }}
                              />
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              <div className={styles.modalFooter}>
                <button type="button" onClick={() => setIsCreateModalOpen(false)} className={styles.cancelBtn}>
                  Cancel
                </button>
                <button type="submit" disabled={isCreating} className={styles.primaryBtn}>
                  {isCreating ? "Creating Policy..." : "Create Policy"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default PoliciesDashboardPage;

import React, { useState, useEffect } from "react";
import { PageHeader } from "../components/common/PageHeader";
import { ShieldCheck, Layers, Link2, PlusCircle, AlertCircle, Sparkles, CheckCircle2, X } from "lucide-react";
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
import type { Policy, PolicyBinding, PolicyCategory, EnforcementMode } from "../types/policy";
import styles from "./PoliciesPage.module.css";

export const PoliciesDashboardPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<"policies" | "bindings" | "resolver">("policies");
  const [policies, setPolicies] = useState<Policy[]>([]);
  const [bindings, setBindings] = useState<PolicyBinding[]>([]);
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
  const [isCreating, setIsCreating] = useState<boolean>(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [policiesRes, bindingsRes] = await Promise.all([
        fetchPolicies(),
        fetchPolicyBindings(),
      ]);
      setPolicies(policiesRes.data || []);
      setBindings(bindingsRes.data || []);
    } catch (err: any) {
      setError(err.message || "Failed to load governance policies");
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreatePolicySubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsCreating(true);
    try {
      await createPolicy({
        policy_code: newPolicyCode.trim().toUpperCase(),
        name: newPolicyName.trim(),
        description: newPolicyDesc.trim(),
        category: newPolicyCategory,
        enforcement_mode: newPolicyMode,
        priority: Number(newPolicyPriority),
      });
      setIsCreateModalOpen(false);
      setNewPolicyCode("");
      setNewPolicyName("");
      setNewPolicyDesc("");
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
      await revokePolicyBinding(bindingId, "Revoked from UI Binding Manager");
      await loadData();
    } catch (err: any) {
      setError(err.message || "Failed to revoke binding");
    }
  };

  const openAttachDrawer = (policy?: Policy) => {
    setAttachTargetPolicy(policy || null);
    setIsAttachDrawerOpen(true);
  };

  return (
    <div className={styles.container}>
      <PageHeader
        title="Policy & Binding Administration"
        description="Define enterprise governance policies, manage authoritative target bindings, and inspect effective runtime compliance."
        actions={
          <div style={{ display: "flex", gap: "10px" }}>
            <button
              onClick={() => openAttachDrawer()}
              className={styles.primaryBtn}
              style={{ background: "rgba(99, 102, 241, 0.2)", border: "1px solid rgba(99, 102, 241, 0.4)" }}
            >
              <Link2 size={16} /> Attach Policy
            </button>
            <button onClick={() => setIsCreateModalOpen(true)} className={styles.primaryBtn}>
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
          <div className={styles.statSubtext}>Direct & inherited target attachments</div>
        </div>

        <div className={styles.statCard}>
          <div className={styles.statHeader}>
            <span className={styles.statLabel}>Enforcement Strategy</span>
            <Sparkles className="w-5 h-5 text-purple-400" />
          </div>
          <div className={styles.statValue} style={{ fontSize: "1.3rem", color: "#a855f7" }}>
            Multi-Layered
          </div>
          <div className={styles.statSubtext}>AST Rules & Decision Combiner</div>
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
          <AlertCircle size={16} />
          <span>{error}</span>
        </div>
      )}

      {/* Main Content Area */}
      <div className={styles.cardSection}>
        {selectedPolicy ? (
          <PolicyDetailView
            policy={selectedPolicy}
            onBack={() => setSelectedPolicy(null)}
            onAttachClick={(p) => openAttachDrawer(p)}
            onRefresh={loadData}
          />
        ) : activeTab === "policies" ? (
          <PolicyListTable
            policies={policies}
            isLoading={isLoading}
            onSelectPolicy={(p) => setSelectedPolicy(p)}
            onAttachPolicy={(p) => openAttachDrawer(p)}
            onCreatePolicyClick={() => setIsCreateModalOpen(true)}
          />
        ) : activeTab === "bindings" ? (
          /* Tab 2: Policy Bindings Manager */
          <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <p style={{ fontSize: "0.8rem", color: "var(--text-secondary, #94a3b8)", margin: 0 }}>
                Authoritative bindings mapping policies to agents, tools, workflows, data sources, and tenants.
              </p>
              <button onClick={() => openAttachDrawer()} className={styles.primaryBtn}>
                <PlusCircle size={16} /> Attach Policy
              </button>
            </div>

            <div className={styles.tableWrapper}>
              <table className={styles.table}>
                <thead>
                  <tr>
                    <th className={styles.th}>Policy ID</th>
                    <th className={styles.th}>Target Type</th>
                    <th className={styles.th}>Target ID</th>
                    <th className={styles.th}>Scope</th>
                    <th className={styles.th}>Priority</th>
                    <th className={styles.th}>Mandatory</th>
                    <th className={styles.th}>Strategy</th>
                    <th className={styles.th}>Status</th>
                    <th className={styles.th} style={{ textAlign: "right" }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {bindings.length === 0 ? (
                    <tr>
                      <td colSpan={9} style={{ padding: "48px 16px", textAlign: "center", color: "var(--text-muted, #64748b)" }}>
                        No policy bindings registered yet.
                      </td>
                    </tr>
                  ) : (
                    bindings.map((b) => (
                      <tr key={b.id} className={styles.row}>
                        <td className={styles.td} style={{ fontFamily: "monospace", fontSize: "0.75rem" }}>
                          {b.policy_id.slice(0, 8)}...
                        </td>
                        <td className={styles.td} style={{ fontWeight: 600 }}>{b.target_type}</td>
                        <td className={styles.td} style={{ fontFamily: "monospace", color: "var(--text-secondary, #94a3b8)" }}>
                          {b.target_id === "*" ? "GLOBAL (*)" : b.target_id.slice(0, 12) + "..."}
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
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
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

      {/* Create Policy Centered Modal */}
      {isCreateModalOpen && (
        <div className={styles.modalBackdrop} onClick={(e) => e.target === e.currentTarget && setIsCreateModalOpen(false)}>
          <div className={styles.modalContent}>
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
              <div className={styles.modalBody}>
                <div className={styles.formGroup}>
                  <label className={styles.formLabel}>Policy Code (Unique Identifier)</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. POL-FIN-001"
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
                    placeholder="e.g. Financial Safety & Transfer Limit Policy"
                    value={newPolicyName}
                    onChange={(e) => setNewPolicyName(e.target.value)}
                    className={styles.formInput}
                  />
                </div>

                <div className={styles.formGroup}>
                  <label className={styles.formLabel}>Description</label>
                  <textarea
                    rows={3}
                    placeholder="Describe policy intent and constraints..."
                    value={newPolicyDesc}
                    onChange={(e) => setNewPolicyDesc(e.target.value)}
                    className={styles.formTextarea}
                  />
                </div>

                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
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
                </div>

                <div className={styles.formGroup}>
                  <label className={styles.formLabel}>Default Priority (1-1000)</label>
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

              <div className={styles.modalFooter}>
                <button type="button" onClick={() => setIsCreateModalOpen(false)} className={styles.cancelBtn}>
                  Cancel
                </button>
                <button type="submit" disabled={isCreating} className={styles.primaryBtn}>
                  {isCreating ? "Creating..." : "Create Policy"}
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

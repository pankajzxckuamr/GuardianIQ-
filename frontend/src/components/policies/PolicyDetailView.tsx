import React, { useState, useEffect } from "react";
import { ArrowLeft, CheckCircle2, History, Layers, PlusCircle, Plus, Trash2, X, AlertCircle } from "lucide-react";
import type { Policy, PolicyVersion, PolicyRule } from "../../types/policy";
import { fetchPolicyVersions, activatePolicyVersion, createDraftVersion } from "../../services/policies/policyService";
import styles from "../../pages/PoliciesPage.module.css";

interface PolicyDetailViewProps {
  policy: Policy;
  onBack: () => void;
  onAttachClick: (policy: Policy) => void;
  onRefresh: () => void;
}

export const PolicyDetailView: React.FC<PolicyDetailViewProps> = ({
  policy,
  onBack,
  onAttachClick,
  onRefresh,
}) => {
  const [versions, setVersions] = useState<PolicyVersion[]>([]);
  const [selectedVersion, setSelectedVersion] = useState<PolicyVersion | null>(null);
  const [isLoadingVersions, setIsLoadingVersions] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  // New Draft Version Modal State
  const [isVersionModalOpen, setIsVersionModalOpen] = useState(false);
  const [changelog, setChangelog] = useState("");
  const [versionRules, setVersionRules] = useState<Array<{
    rule_code: string;
    name: string;
    description?: string;
    rule_type: string;
    target_type: string;
    condition_expression: string;
    action: "ALLOW" | "DENY" | "MODIFY" | "REQUIRE_APPROVAL" | "ESCALATE";
    severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  }>>([]);
  const [isSubmittingVersion, setIsSubmittingVersion] = useState(false);
  const [versionModalError, setVersionModalError] = useState<string | null>(null);

  useEffect(() => {
    loadVersions();
  }, [policy.id]);

  const loadVersions = async () => {
    setIsLoadingVersions(true);
    setActionError(null);
    try {
      const res = await fetchPolicyVersions(policy.id);
      setVersions(res.data || []);
      const active = (res.data || []).find((v) => v.status === "ACTIVE") || (res.data || [])[0] || null;
      setSelectedVersion(active);
    } catch (err: any) {
      setActionError(err.message || "Failed to load policy versions");
    } finally {
      setIsLoadingVersions(false);
    }
  };

  const handleActivateVersion = async (versionId: string) => {
    try {
      await activatePolicyVersion(policy.id, versionId);
      await loadVersions();
      onRefresh();
    } catch (err: any) {
      setActionError(err.message || "Failed to activate version");
    }
  };

  const handleAddRuleRow = () => {
    const nextOrder = versionRules.length + 1;
    const prefix = policy.policy_code ? policy.policy_code.replace(/^POL-/, "") : "RULE";
    setVersionRules([
      ...versionRules,
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
    setVersionRules((prev) =>
      prev.map((r, idx) => (idx === index ? { ...r, [field]: value } : r))
    );
  };

  const handleRemoveRuleRow = (index: number) => {
    setVersionRules((prev) => prev.filter((_, idx) => idx !== index));
  };

  const handleCreateVersionSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmittingVersion(true);
    setVersionModalError(null);
    try {
      const cleanedRules: PolicyRule[] = versionRules
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

      await createDraftVersion(policy.id, {
        changelog: changelog.trim() || `Draft version ${versions.length + 1}`,
        rules: cleanedRules.length > 0 ? cleanedRules : undefined,
      });

      setIsVersionModalOpen(false);
      setChangelog("");
      setVersionRules([]);
      await loadVersions();
      onRefresh();
    } catch (err: any) {
      setVersionModalError(err.message || "Failed to create draft version");
    } finally {
      setIsSubmittingVersion(false);
    }
  };

  const getActionBadge = (action: string) => {
    switch (action) {
      case "ALLOW":
        return <span style={{ fontSize: "0.75rem", padding: "2px 6px", borderRadius: "4px", background: "rgba(16, 185, 129, 0.15)", color: "#34d399", fontWeight: 600 }}>ALLOW</span>;
      case "DENY":
        return <span style={{ fontSize: "0.75rem", padding: "2px 6px", borderRadius: "4px", background: "rgba(239, 68, 68, 0.15)", color: "#f87171", fontWeight: 600 }}>DENY</span>;
      case "REQUIRE_APPROVAL":
        return <span style={{ fontSize: "0.75rem", padding: "2px 6px", borderRadius: "4px", background: "rgba(245, 158, 11, 0.15)", color: "#fbbf24", fontWeight: 600 }}>REQUIRE_APPROVAL</span>;
      case "ESCALATE":
        return <span style={{ fontSize: "0.75rem", padding: "2px 6px", borderRadius: "4px", background: "rgba(168, 85, 247, 0.15)", color: "#c084fc", fontWeight: 600 }}>ESCALATE</span>;
      default:
        return <span style={{ fontSize: "0.75rem", padding: "2px 6px", borderRadius: "4px", background: "rgba(255, 255, 255, 0.06)", color: "var(--text-secondary, #94a3b8)" }}>{action}</span>;
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
      {/* Top Header Navigation */}
      <div style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        paddingBottom: "16px",
        borderBottom: "1px solid var(--card-border, rgba(99, 102, 241, 0.2))",
        flexWrap: "wrap",
        gap: "12px"
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <button
            onClick={onBack}
            className={styles.cancelBtn}
            style={{ padding: "6px 10px", display: "flex", alignItems: "center" }}
            title="Back to List"
          >
            <ArrowLeft size={16} />
          </button>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <h2 style={{ fontSize: "1.25rem", fontWeight: 700, color: "var(--text-primary, #f8fafc)", margin: 0 }}>
                {policy.name}
              </h2>
              <span style={{
                fontSize: "0.75rem",
                fontFamily: "monospace",
                padding: "2px 6px",
                borderRadius: "4px",
                background: "rgba(255, 255, 255, 0.06)",
                color: "var(--text-secondary, #94a3b8)"
              }}>
                {policy.policy_code}
              </span>
            </div>
            <p style={{ fontSize: "0.8rem", color: "var(--text-secondary, #94a3b8)", margin: "4px 0 0 0" }}>
              {policy.description || "No description provided."}
            </p>
          </div>
        </div>

        <div style={{ display: "flex", gap: "10px" }}>
          <button
            onClick={() => {
              setChangelog("");
              setVersionRules([]);
              setVersionModalError(null);
              setIsVersionModalOpen(true);
            }}
            className={styles.primaryBtn}
            style={{ background: "rgba(99, 102, 241, 0.15)", border: "1px solid rgba(99, 102, 241, 0.35)", color: "#a5b4fc" }}
          >
            <PlusCircle size={16} /> New Draft Version
          </button>
          <button onClick={() => onAttachClick(policy)} className={styles.primaryBtn}>
            <PlusCircle size={16} /> Attach Policy to Entity
          </button>
        </div>
      </div>

      {actionError && (
        <div style={{
          padding: "10px 14px",
          borderRadius: "8px",
          background: "rgba(239, 68, 68, 0.15)",
          border: "1px solid rgba(239, 68, 68, 0.3)",
          color: "#f87171",
          fontSize: "0.8rem"
        }}>
          {actionError}
        </div>
      )}

      {/* Main Grid: Versions vs Rules */}
      <div style={{ display: "grid", gridTemplateColumns: "320px 1fr", gap: "20px" }}>
        {/* Left: Version History */}
        <div style={{
          background: "var(--bg-tertiary, #151d30)",
          border: "1px solid var(--card-border, rgba(99, 102, 241, 0.2))",
          borderRadius: "12px",
          padding: "16px",
          display: "flex",
          flexDirection: "column",
          gap: "12px"
        }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px", fontWeight: 700, fontSize: "0.85rem", color: "var(--text-primary, #f8fafc)" }}>
              <History size={16} className="text-indigo-400" /> Version History
            </div>
            <button
              onClick={() => {
                setChangelog("");
                setVersionRules([]);
                setVersionModalError(null);
                setIsVersionModalOpen(true);
              }}
              style={{
                background: "transparent",
                border: "none",
                color: "#818cf8",
                fontSize: "0.75rem",
                fontWeight: 600,
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                gap: "4px",
              }}
            >
              <Plus size={12} /> Add
            </button>
          </div>

          {isLoadingVersions ? (
            <div style={{ padding: "24px 0", textAlign: "center", color: "var(--text-muted, #64748b)", fontSize: "0.8rem" }}>
              Loading versions...
            </div>
          ) : versions.length === 0 ? (
            <div style={{ padding: "24px 0", textAlign: "center", color: "var(--text-muted, #64748b)", fontSize: "0.8rem" }}>
              No version history available.
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
              {versions.map((v) => (
                <div
                  key={v.id}
                  onClick={() => setSelectedVersion(v)}
                  style={{
                    padding: "10px 12px",
                    borderRadius: "8px",
                    border: selectedVersion?.id === v.id ? "1px solid rgba(99, 102, 241, 0.5)" : "1px solid rgba(255, 255, 255, 0.05)",
                    background: selectedVersion?.id === v.id ? "rgba(99, 102, 241, 0.12)" : "rgba(255, 255, 255, 0.02)",
                    cursor: "pointer",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between"
                  }}
                >
                  <div>
                    <div style={{ fontWeight: 600, fontSize: "0.85rem", color: "var(--text-primary, #f8fafc)" }}>
                      v{v.version_number}
                    </div>
                    <div style={{ fontSize: "0.75rem", color: "var(--text-muted, #64748b)" }}>
                      {v.rules?.length || v.rules_count || 0} rules defined
                    </div>
                  </div>

                  <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                    <span style={{
                      fontSize: "0.7rem",
                      padding: "2px 6px",
                      borderRadius: "4px",
                      fontWeight: 600,
                      background: v.status === "ACTIVE" ? "rgba(16, 185, 129, 0.15)" : "rgba(255, 255, 255, 0.05)",
                      color: v.status === "ACTIVE" ? "#34d399" : "var(--text-secondary, #94a3b8)"
                    }}>
                      {v.status}
                    </span>
                    {v.status !== "ACTIVE" && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleActivateVersion(v.id);
                        }}
                        style={{
                          fontSize: "0.7rem",
                          padding: "2px 6px",
                          borderRadius: "4px",
                          background: "rgba(99, 102, 241, 0.2)",
                          border: "1px solid rgba(99, 102, 241, 0.3)",
                          color: "#818cf8",
                          cursor: "pointer"
                        }}
                      >
                        Activate
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Right: Active Version Rules AST */}
        <div style={{
          background: "var(--bg-tertiary, #151d30)",
          border: "1px solid var(--card-border, rgba(99, 102, 241, 0.2))",
          borderRadius: "12px",
          padding: "20px",
          display: "flex",
          flexDirection: "column",
          gap: "16px"
        }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px", fontWeight: 700, fontSize: "0.95rem", color: "var(--text-primary, #f8fafc)" }}>
              <Layers size={18} className="text-indigo-400" />
              <span>Rules in Version {selectedVersion?.version_number || 1}</span>
            </div>
            {selectedVersion?.status === "ACTIVE" && (
              <span style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "4px",
                padding: "2px 8px",
                borderRadius: "4px",
                fontSize: "0.75rem",
                fontWeight: 600,
                background: "rgba(16, 185, 129, 0.15)",
                color: "#34d399"
              }}>
                <CheckCircle2 size={12} /> Active Version
              </span>
            )}
          </div>

          {!selectedVersion || !selectedVersion.rules || selectedVersion.rules.length === 0 ? (
            <div style={{ padding: "48px 0", textAlign: "center", color: "var(--text-muted, #64748b)" }}>
              No rules configured for this policy version.
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              {selectedVersion.rules.map((rule, idx) => (
                <div
                  key={rule.id || idx}
                  style={{
                    padding: "14px",
                    borderRadius: "8px",
                    border: "1px solid rgba(255, 255, 255, 0.06)",
                    background: "rgba(15, 23, 42, 0.6)",
                    display: "flex",
                    flexDirection: "column",
                    gap: "8px"
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                      <span style={{ fontWeight: 600, fontSize: "0.85rem", color: "var(--text-primary, #f8fafc)" }}>
                        {rule.name}
                      </span>
                      <span style={{ fontSize: "0.75rem", fontFamily: "monospace", color: "var(--text-secondary, #94a3b8)" }}>
                        ({rule.rule_code})
                      </span>
                    </div>
                    <div>{getActionBadge(rule.action)}</div>
                  </div>

                  <div style={{
                    padding: "8px 12px",
                    borderRadius: "6px",
                    background: "#0a0e17",
                    border: "1px solid rgba(255, 255, 255, 0.05)",
                    fontFamily: "monospace",
                    fontSize: "0.8rem",
                    color: "#a5b4fc"
                  }}>
                    {rule.condition_expression || "true"}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* New Draft Version Modal with Rules Builder */}
      {isVersionModalOpen && (
        <div className={styles.modalBackdrop} onClick={(e) => e.target === e.currentTarget && setIsVersionModalOpen(false)}>
          <div className={styles.modalContent} style={{ maxWidth: "780px" }}>
            <div className={styles.modalHeader}>
              <div className={styles.modalTitle}>
                <PlusCircle size={20} className="text-indigo-400" />
                <span>Create New Draft Version for {policy.policy_code}</span>
              </div>
              <button onClick={() => setIsVersionModalOpen(false)} className={styles.modalCloseBtn}>
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleCreateVersionSubmit}>
              <div className={styles.modalBody} style={{ maxHeight: "70vh", overflowY: "auto" }}>
                {versionModalError && (
                  <div style={{
                    padding: "10px 14px",
                    borderRadius: "8px",
                    background: "rgba(239, 68, 68, 0.15)",
                    border: "1px solid rgba(239, 68, 68, 0.3)",
                    color: "#f87171",
                    fontSize: "0.825rem",
                    display: "flex",
                    alignItems: "center",
                    gap: "8px"
                  }}>
                    <AlertCircle size={16} />
                    <span>{versionModalError}</span>
                  </div>
                )}

                <div className={styles.formGroup}>
                  <label className={styles.formLabel}>Changelog / Version Notes</label>
                  <input
                    type="text"
                    required
                    placeholder="Enter version change description..."
                    value={changelog}
                    onChange={(e) => setChangelog(e.target.value)}
                    className={styles.formInput}
                  />
                </div>

                {/* Section: Rules for this Version */}
                <div style={{
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
                        Rules in this Version ({versionRules.length})
                      </div>
                      <div style={{ fontSize: "0.75rem", color: "var(--text-secondary, #94a3b8)" }}>
                        Define rule statements to be evaluated in this version snapshot.
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

                  {versionRules.length === 0 ? (
                    <div style={{
                      padding: "16px",
                      textAlign: "center",
                      color: "var(--text-muted, #64748b)",
                      fontSize: "0.8rem",
                      border: "1px dashed rgba(255, 255, 255, 0.1)",
                      borderRadius: "8px",
                    }}>
                      No rules added yet. Click <strong>"+ Add Rule"</strong> to define rules.
                    </div>
                  ) : (
                    <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                      {versionRules.map((rule, idx) => (
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
                <button type="button" onClick={() => setIsVersionModalOpen(false)} className={styles.cancelBtn}>
                  Cancel
                </button>
                <button type="submit" disabled={isSubmittingVersion} className={styles.primaryBtn}>
                  {isSubmittingVersion ? "Creating Version..." : "Create Draft Version"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

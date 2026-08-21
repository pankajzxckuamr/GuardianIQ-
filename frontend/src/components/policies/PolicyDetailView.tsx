import React, { useState, useEffect } from "react";
import { ArrowLeft, Shield, CheckCircle2, History, AlertTriangle, Layers, Play, PlusCircle } from "lucide-react";
import type { Policy, PolicyVersion, PolicyRule } from "../../types/policy";
import { fetchPolicyVersions, activatePolicyVersion } from "../../services/policies/policyService";
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

        <button onClick={() => onAttachClick(policy)} className={styles.primaryBtn}>
          <PlusCircle size={16} /> Attach Policy to Entity
        </button>
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
          <div style={{ display: "flex", alignItems: "center", gap: "8px", fontWeight: 700, fontSize: "0.85rem", color: "var(--text-primary, #f8fafc)" }}>
            <History size={16} className="text-indigo-400" /> Version History
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
                      {v.rules?.length || 0} rules defined
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
    </div>
  );
};

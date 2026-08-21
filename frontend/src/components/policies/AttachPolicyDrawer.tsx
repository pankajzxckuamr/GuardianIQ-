import React, { useState } from "react";
import { X, Link2, AlertCircle, CheckCircle2, ShieldCheck } from "lucide-react";
import type { Policy, TargetType, VersionStrategy } from "../../types/policy";
import { createPolicyBinding } from "../../services/policies/policyService";
import styles from "../../pages/PoliciesPage.module.css";

interface AttachPolicyDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  policy: Policy | null;
  policies: Policy[];
  onSuccess: () => void;
}

export const AttachPolicyDrawer: React.FC<AttachPolicyDrawerProps> = ({
  isOpen,
  onClose,
  policy,
  policies,
  onSuccess,
}) => {
  const [selectedPolicyId, setSelectedPolicyId] = useState<string>(policy?.id || "");
  const [targetType, setTargetType] = useState<TargetType>("AGENT");
  const [targetId, setTargetId] = useState<string>("");
  const [bindingScope, setBindingScope] = useState<string>("DIRECT");
  const [priority, setPriority] = useState<number>(100);
  const [isMandatory, setIsMandatory] = useState<boolean>(true);
  const [versionStrategy, setVersionStrategy] = useState<VersionStrategy>("LATEST");
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  React.useEffect(() => {
    if (policy) {
      setSelectedPolicyId(policy.id);
    } else if (policies.length > 0 && !selectedPolicyId) {
      setSelectedPolicyId(policies[0].id);
    }
  }, [policy, policies]);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedPolicyId) {
      setErrorMessage("Please select a policy to attach.");
      return;
    }
    if (!targetId.trim()) {
      setErrorMessage("Target ID is required.");
      return;
    }

    setIsSubmitting(true);
    setErrorMessage(null);
    setSuccessMessage(null);

    try {
      await createPolicyBinding({
        policy_id: selectedPolicyId,
        target_type: targetType,
        target_id: targetId.trim(),
        binding_scope: bindingScope,
        priority: Number(priority),
        is_mandatory: isMandatory,
        version_strategy: versionStrategy,
      });

      setSuccessMessage("Policy bound successfully to target!");
      setTimeout(() => {
        onSuccess();
        onClose();
      }, 1000);
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to attach policy binding.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className={styles.modalBackdrop} onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className={styles.modalContent}>
        {/* Modal Header */}
        <div className={styles.modalHeader}>
          <div className={styles.modalTitle}>
            <Link2 className="w-5 h-5 text-indigo-400" />
            <span>Attach Policy to Target Entity</span>
          </div>
          <button onClick={onClose} className={styles.modalCloseBtn} title="Close">
            <X size={20} />
          </button>
        </div>

        {/* Modal Form Body */}
        <form onSubmit={handleSubmit}>
          <div className={styles.modalBody}>
            {errorMessage && (
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
                <span>{errorMessage}</span>
              </div>
            )}

            {successMessage && (
              <div style={{
                padding: "10px 14px",
                borderRadius: "8px",
                background: "rgba(16, 185, 129, 0.15)",
                border: "1px solid rgba(16, 185, 129, 0.3)",
                color: "#34d399",
                fontSize: "0.825rem",
                display: "flex",
                alignItems: "center",
                gap: "8px"
              }}>
                <CheckCircle2 size={16} />
                <span>{successMessage}</span>
              </div>
            )}

            {/* Policy Selection */}
            <div className={styles.formGroup}>
              <label className={styles.formLabel}>Governance Policy</label>
              <select
                value={selectedPolicyId}
                onChange={(e) => setSelectedPolicyId(e.target.value)}
                className={styles.formSelect}
              >
                {policies.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name} ({p.policy_code})
                  </option>
                ))}
              </select>
            </div>

            {/* Target Type */}
            <div className={styles.formGroup}>
              <label className={styles.formLabel}>Target Entity Type</label>
              <select
                value={targetType}
                onChange={(e) => setTargetType(e.target.value as TargetType)}
                className={styles.formSelect}
              >
                <option value="AGENT">Agent (Direct Boundary Binding)</option>
                <option value="WORKFLOW">Workflow (Inherited by Execution Agents)</option>
                <option value="TOOL">Tool (Pre-execution Enforcement)</option>
                <option value="DATA_SOURCE">Data Source (Data Access Rules)</option>
                <option value="TENANT">Tenant (Mandatory Baseline)</option>
              </select>
            </div>

            {/* Target ID */}
            <div className={styles.formGroup}>
              <label className={styles.formLabel}>Target Entity ID / Code / UUID</label>
              <input
                type="text"
                required
                placeholder="e.g. 550e8400-e29b-41d4-a716-446655440000 or *"
                value={targetId}
                onChange={(e) => setTargetId(e.target.value)}
                className={styles.formInput}
              />
              <span className={styles.formHelp}>
                Enter the UUID/identifier of the target or * for tenant-wide global binding.
              </span>
            </div>

            {/* Version Strategy */}
            <div className={styles.formGroup}>
              <label className={styles.formLabel}>Version Resolution Strategy</label>
              <select
                value={versionStrategy}
                onChange={(e) => setVersionStrategy(e.target.value as VersionStrategy)}
                className={styles.formSelect}
              >
                <option value="LATEST">LATEST (Auto-track active version)</option>
                <option value="PINNED_VERSION">PINNED_VERSION (Pin to specific snapshot)</option>
              </select>
            </div>

            {/* Priority & Binding Scope */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
              <div className={styles.formGroup}>
                <label className={styles.formLabel}>Priority (1-1000)</label>
                <input
                  type="number"
                  min="1"
                  max="1000"
                  value={priority}
                  onChange={(e) => setPriority(parseInt(e.target.value) || 100)}
                  className={styles.formInput}
                />
              </div>

              <div className={styles.formGroup}>
                <label className={styles.formLabel}>Binding Scope</label>
                <input
                  type="text"
                  value={bindingScope}
                  onChange={(e) => setBindingScope(e.target.value)}
                  className={styles.formInput}
                />
              </div>
            </div>

            {/* Mandatory Switch */}
            <div style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              padding: "12px 14px",
              background: "var(--bg-tertiary, #151d30)",
              border: "1px solid var(--card-border, rgba(99, 102, 241, 0.2))",
              borderRadius: "8px"
            }}>
              <div>
                <div style={{ fontSize: "0.85rem", fontWeight: 600, color: "var(--text-primary, #f8fafc)" }}>
                  Mandatory Policy Flag
                </div>
                <div style={{ fontSize: "0.75rem", color: "var(--text-secondary, #94a3b8)" }}>
                  Mandatory policies cannot be overridden by lower-priority bindings.
                </div>
              </div>
              <input
                type="checkbox"
                checked={isMandatory}
                onChange={(e) => setIsMandatory(e.target.checked)}
                style={{ width: "18px", height: "18px", accentColor: "#6366f1", cursor: "pointer" }}
              />
            </div>
          </div>

          {/* Modal Footer */}
          <div className={styles.modalFooter}>
            <button type="button" onClick={onClose} className={styles.cancelBtn}>
              Cancel
            </button>
            <button type="submit" disabled={isSubmitting} className={styles.primaryBtn}>
              {isSubmitting ? "Binding..." : "Attach Policy"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

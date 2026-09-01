import React, { useState, useEffect } from "react";
import { X, Link2, AlertCircle, CheckCircle2 } from "lucide-react";
import type { Policy, TargetType, VersionStrategy } from "../../types/policy";
import { createPolicyBinding } from "../../services/policies/policyService";
import { listAgents, listTools, listDataSources, listWorkflows, listModels } from "../../services/registry/registryService";
import type { AIAgent, Tool, DataSource, Workflow, AIModel } from "../../services/registry/registryTypes";
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
  const [isCustomTarget, setIsCustomTarget] = useState<boolean>(false);
  const [bindingScope, setBindingScope] = useState<string>("DIRECT");
  const [priority, setPriority] = useState<number>(100);
  const [isMandatory, setIsMandatory] = useState<boolean>(true);
  const [versionStrategy, setVersionStrategy] = useState<VersionStrategy>("LATEST");
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Asset lists for dynamic dropdowns
  const [agents, setAgents] = useState<AIAgent[]>([]);
  const [tools, setTools] = useState<Tool[]>([]);
  const [dataSources, setDataSources] = useState<DataSource[]>([]);
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [models, setModels] = useState<AIModel[]>([]);

  useEffect(() => {
    if (isOpen) {
      loadAssets();
    }
  }, [isOpen]);

  const loadAssets = async () => {
    try {
      const [agentsRes, toolsRes, dsRes, wfRes, modelsRes] = await Promise.allSettled([
        listAgents({ per_page: 100 }),
        listTools({ per_page: 100 }),
        listDataSources({ per_page: 100 }),
        listWorkflows({ per_page: 100 }),
        listModels({ per_page: 100 }),
      ]);

      if (agentsRes.status === "fulfilled" && agentsRes.value?.data) {
        const raw = agentsRes.value.data as any;
        const items = Array.isArray(raw) ? raw : raw.items || [];
        setAgents(items);
        if (targetType === "AGENT" && items.length > 0 && !targetId) {
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

  useEffect(() => {
    if (policy) {
      setSelectedPolicyId(policy.id);
    } else if (policies.length > 0 && !selectedPolicyId) {
      setSelectedPolicyId(policies[0].id);
    }
  }, [policy, policies]);

  // When target type changes, auto-select the first matching asset
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
    } else if (newType === "TENANT") {
      setTargetId("*");
    } else {
      setTargetId("");
    }
  };

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedPolicyId) {
      setErrorMessage("Please select a policy to attach.");
      return;
    }
    if (!targetId.trim()) {
      setErrorMessage("Please select or enter a Target ID.");
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
                onChange={(e) => handleTargetTypeChange(e.target.value as TargetType)}
                className={styles.formSelect}
              >
                <option value="AGENT">Agent (Direct Boundary Binding)</option>
                <option value="WORKFLOW">Workflow (Inherited by Execution Agents)</option>
                <option value="TOOL">Tool (Pre-execution Enforcement)</option>
                <option value="DATA_SOURCE">Data Source (Data Access Rules)</option>
                <option value="MODEL">AI Model (Model Guardrail Binding)</option>
                <option value="TENANT">Tenant (Mandatory Global Baseline)</option>
              </select>
            </div>

            {/* Target Entity Selector */}
            <div className={styles.formGroup}>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                <label className={styles.formLabel}>
                  {targetType === "TENANT" ? "Target Scope" : "Target Entity Asset"}
                </label>
                {targetType !== "TENANT" && (
                  <button
                    type="button"
                    onClick={() => setIsCustomTarget(!isCustomTarget)}
                    style={{ background: "transparent", border: "none", color: "#818cf8", fontSize: "0.7rem", cursor: "pointer" }}
                  >
                    {isCustomTarget ? "Select from Registry" : "Enter Custom UUID / *"}
                  </button>
                )}
              </div>

              {targetType === "TENANT" ? (
                <input
                  type="text"
                  disabled
                  value="* (All Tenant Entities)"
                  className={styles.formInput}
                  style={{ opacity: 0.8 }}
                />
              ) : isCustomTarget ? (
                <input
                  type="text"
                  required
                  placeholder="Enter target UUID or * for wildcard..."
                  value={targetId}
                  onChange={(e) => setTargetId(e.target.value)}
                  className={styles.formInput}
                  style={{ fontFamily: "monospace" }}
                />
              ) : targetType === "AGENT" ? (
                <select
                  required
                  value={targetId}
                  onChange={(e) => setTargetId(e.target.value)}
                  className={styles.formSelect}
                >
                  <option value="" disabled>Select an Agent...</option>
                  <option value="*">* Global (All Agents)</option>
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
                  <option value="*">* Global (All Tools)</option>
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
                  <option value="*">* Global (All Data Sources)</option>
                  {dataSources.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.source_name} ({d.classification || "INTERNAL"})
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
                  <option value="*">* Global (All Workflows)</option>
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
                  <option value="*">* Global (All AI Models)</option>
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
                <select
                  value={bindingScope}
                  onChange={(e) => setBindingScope(e.target.value)}
                  className={styles.formSelect}
                >
                  <option value="DIRECT">DIRECT</option>
                  <option value="INHERITED">INHERITED</option>
                  <option value="TENANT_MANDATORY">TENANT_MANDATORY</option>
                </select>
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

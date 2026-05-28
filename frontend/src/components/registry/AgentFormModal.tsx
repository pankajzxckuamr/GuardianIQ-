/* src/components/registry/AgentFormModal.tsx */

import React, { useEffect, useState } from "react";
import { Modal } from "../common/Modal";
import { useToast } from "../../hooks/useToast";
import * as registryService from "../../services/registry/registryService";
import { EntityStatus } from "../../services/registry/registryTypes";
import styles from "./AgentFormModal.module.css";

interface AgentFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  agentId?: string | null;
  onSuccess: () => void;
}

export const AgentFormModal: React.FC<AgentFormModalProps> = ({
  isOpen,
  onClose,
  agentId,
  onSuccess
}) => {
  const { showToast } = useToast();
  const [activeTab, setActiveTab] = useState<"details" | "relationships" | "audit">("details");

  // Lookups data
  const [users, setUsers] = useState<{ id: string; full_name: string; email: string }[]>([]);
  const [departments, setDepartments] = useState<{ id: string; department_name: string; department_code: string }[]>([]);

  // Form State
  const [formData, setFormData] = useState({
    agent_code: "",
    agent_name: "",
    agent_type: "",
    execution_mode: "",
    description: "",
    confidence_threshold: 80,
    capabilities_json: "",
    owner_user_id: "",
    department_id: "",
    risk_level: "",
    status: EntityStatus.DRAFT
  });

  const [loading, setLoading] = useState(false);
  const [isCapabilitiesJsonValid, setIsCapabilitiesJsonValid] = useState(true);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [generalError, setGeneralError] = useState<string | null>(null);

  const isEditMode = !!agentId;

  // Load Lookups on mount
  useEffect(() => {
    async function loadLookups() {
      try {
        const [usersRes, deptsRes] = await Promise.all([
          registryService.getUsersLookup(),
          registryService.getDepartmentsLookup()
        ]);
        if (usersRes.data) setUsers(usersRes.data);
        if (deptsRes.data) setDepartments(deptsRes.data);
      } catch (err) {
        console.error("Failed to load lookups:", err);
      }
    }
    if (isOpen) {
      loadLookups();
    }
  }, [isOpen]);

  // Load Agent Data in Edit Mode
  useEffect(() => {
    async function loadAgent() {
      if (!agentId) return;
      setLoading(true);
      setGeneralError(null);
      try {
        const res = await registryService.getAgent(agentId);
        if (res.data) {
          const a = res.data;
          setFormData({
            agent_code: a.agent_code || (a as any).code || "",
            agent_name: a.agent_name || "",
            agent_type: a.agent_type || "",
            execution_mode: a.execution_mode || "",
            description: a.description || "",
            confidence_threshold: (a as any).confidence_threshold ?? 80,
            capabilities_json: (a as any).capabilities_json 
              ? typeof (a as any).capabilities_json === "string"
                ? (a as any).capabilities_json
                : JSON.stringify((a as any).capabilities_json, null, 2)
              : "",
            owner_user_id: (a as any).owner_user_id || "",
            department_id: a.department_id || "",
            risk_level: a.risk_level || "",
            status: a.status || EntityStatus.DRAFT
          });
        }
      } catch (err: any) {
        setGeneralError(err.message || "Failed to load agent data.");
      } finally {
        setLoading(false);
      }
    }

    if (isOpen) {
      if (agentId) {
        loadAgent();
        setActiveTab("details");
      } else {
        // Reset form for create mode
        setFormData({
          agent_code: "",
          agent_name: "",
          agent_type: "",
          execution_mode: "",
          description: "",
          confidence_threshold: 80,
          capabilities_json: "",
          owner_user_id: "",
          department_id: "",
          risk_level: "",
          status: EntityStatus.DRAFT
        });
        setFieldErrors({});
        setGeneralError(null);
        setActiveTab("details");
      }
    }
  }, [isOpen, agentId]);

  // Validate capabilities_json
  useEffect(() => {
    if (!formData.capabilities_json.trim()) {
      setIsCapabilitiesJsonValid(true);
      return;
    }
    try {
      JSON.parse(formData.capabilities_json);
      setIsCapabilitiesJsonValid(true);
    } catch {
      setIsCapabilitiesJsonValid(false);
    }
  }, [formData.capabilities_json]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ 
      ...prev, 
      [name]: name === "confidence_threshold" ? (parseInt(value, 10) || 0) : value 
    }));
    // Clear field error
    if (fieldErrors[name]) {
      setFieldErrors((prev) => {
        const copy = { ...prev };
        delete copy[name];
        return copy;
      });
    }
  };

  const handleApiError = (err: any) => {
    const message = err.message || "An error occurred";
    setGeneralError(message);

    const newFieldErrors: Record<string, string> = {};

    // Parse FastAPI flat error messages
    if (message.includes("Validation Error:")) {
      const errorContent = message.substring(message.indexOf("Validation Error:") + 17).trim();
      const parts = errorContent.split(", ");
      parts.forEach((part: string) => {
        const colonIndex = part.indexOf(":");
        if (colonIndex !== -1) {
          const fullField = part.substring(0, colonIndex).trim(); // "body.agent_code"
          const msg = part.substring(colonIndex + 1).trim(); // "field required"
          const fieldName = fullField.replace("body.", "").trim();
          newFieldErrors[fieldName] = msg;
        }
      });
    }

    // Parse structured details array
    if (err.details && Array.isArray(err.details)) {
      err.details.forEach((d: any) => {
        const fieldName = d.field || (d.loc && d.loc[d.loc.length - 1]);
        if (fieldName) {
          newFieldErrors[String(fieldName)] = d.message || d.msg || "Invalid value";
        }
      });
    }

    setFieldErrors(newFieldErrors);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isCapabilitiesJsonValid) {
      showToast("Capabilities must be a valid JSON array or object", "error");
      return;
    }

    setLoading(true);
    setGeneralError(null);
    setFieldErrors({});

    const payload = {
      ...formData,
      capabilities_json: formData.capabilities_json.trim() ? JSON.parse(formData.capabilities_json) : null
    };

    try {
      if (isEditMode && agentId) {
        await registryService.updateAgent(agentId, payload);
      } else {
        await registryService.createAgent(payload);
      }
      showToast("Agent saved successfully", "success");
      onSuccess();
      onClose();
    } catch (err: any) {
      handleApiError(err);
      showToast("Failed to save agent", "error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={isEditMode ? `Edit Agent: ${formData.agent_name}` : "Register New AI Agent"}
      size="lg"
    >
      <div className={styles.container}>
        {/* Tab Headers */}
        {isEditMode && (
          <div className={styles.tabsHeader}>
            <button
              type="button"
              className={`${styles.tabBtn} ${activeTab === "details" ? styles.activeTab : ""}`}
              onClick={() => setActiveTab("details")}
            >
              Details
            </button>
            <button
              type="button"
              className={`${styles.tabBtn} ${activeTab === "relationships" ? styles.activeTab : ""}`}
              onClick={() => setActiveTab("relationships")}
            >
              Relationships
            </button>
            <button
              type="button"
              className={`${styles.tabBtn} ${activeTab === "audit" ? styles.activeTab : ""}`}
              onClick={() => setActiveTab("audit")}
            >
              Audit Trail
            </button>
          </div>
        )}

        {/* General Alert */}
        {generalError && <div className={styles.generalAlert}>{generalError}</div>}

        {/* Tab Contents */}
        <div className={styles.tabsContent}>
          {activeTab === "details" && (
            <form onSubmit={handleSubmit} className={styles.form}>
              
              {/* Custom UX blocked mode banner */}
              {formData.execution_mode === "BLOCKED" && (
                <div className={styles.blockedWarningBanner}>
                  ⚠️ BLOCKED mode prevents this agent from executing any actions.
                </div>
              )}

              <div className={styles.formGrid}>
                {/* Agent Code */}
                <div className={styles.formGroup}>
                  <label htmlFor="agent_code" className={styles.label}>
                    Agent Code <span className={styles.required}>*</span>
                  </label>
                  <input
                    type="text"
                    id="agent_code"
                    name="agent_code"
                    value={formData.agent_code}
                    onChange={handleChange}
                    disabled={isEditMode || loading}
                    className={`${styles.input} ${fieldErrors.agent_code ? styles.inputError : ""}`}
                    required
                  />
                  {fieldErrors.agent_code && (
                    <span className={styles.fieldErrorText}>{fieldErrors.agent_code}</span>
                  )}
                </div>

                {/* Agent Name */}
                <div className={styles.formGroup}>
                  <label htmlFor="agent_name" className={styles.label}>
                    Agent Name <span className={styles.required}>*</span>
                  </label>
                  <input
                    type="text"
                    id="agent_name"
                    name="agent_name"
                    value={formData.agent_name}
                    onChange={handleChange}
                    disabled={loading}
                    className={`${styles.input} ${fieldErrors.agent_name ? styles.inputError : ""}`}
                    required
                  />
                  {fieldErrors.agent_name && (
                    <span className={styles.fieldErrorText}>{fieldErrors.agent_name}</span>
                  )}
                </div>

                {/* Agent Type */}
                <div className={styles.formGroup}>
                  <label htmlFor="agent_type" className={styles.label}>
                    Agent Type <span className={styles.required}>*</span>
                  </label>
                  <select
                    id="agent_type"
                    name="agent_type"
                    value={formData.agent_type}
                    onChange={handleChange}
                    disabled={loading}
                    className={`${styles.select} ${fieldErrors.agent_type ? styles.inputError : ""}`}
                    required
                  >
                    <option value="">-- Select Type --</option>
                    <option value="RECOMMENDATION">RECOMMENDATION</option>
                    <option value="TRIAGE">TRIAGE</option>
                    <option value="EXTRACTION">EXTRACTION</option>
                    <option value="EXECUTION">EXECUTION</option>
                    <option value="MONITORING">MONITORING</option>
                  </select>
                  {fieldErrors.agent_type && (
                    <span className={styles.fieldErrorText}>{fieldErrors.agent_type}</span>
                  )}
                </div>

                {/* Execution Mode */}
                <div className={styles.formGroup}>
                  <label htmlFor="execution_mode" className={styles.label}>
                    Execution Mode <span className={styles.required}>*</span>
                  </label>
                  <select
                    id="execution_mode"
                    name="execution_mode"
                    value={formData.execution_mode}
                    onChange={handleChange}
                    disabled={loading}
                    className={`${styles.select} ${fieldErrors.execution_mode ? styles.inputError : ""}`}
                    required
                  >
                    <option value="">-- Select Mode --</option>
                    <option value="READ_ONLY">READ_ONLY</option>
                    <option value="RECOMMEND_ONLY">RECOMMEND_ONLY</option>
                    <option value="APPROVAL_REQUIRED">APPROVAL_REQUIRED</option>
                    <option value="LIMITED_EXECUTION">LIMITED_EXECUTION</option>
                    <option value="BLOCKED">BLOCKED</option>
                  </select>
                  {fieldErrors.execution_mode && (
                    <span className={styles.fieldErrorText}>{fieldErrors.execution_mode}</span>
                  )}
                </div>

                {/* Confidence Threshold */}
                <div className={styles.formGroup}>
                  <label htmlFor="confidence_threshold" className={styles.label}>
                    Confidence Threshold (%)
                  </label>
                  <input
                    type="number"
                    id="confidence_threshold"
                    name="confidence_threshold"
                    value={formData.confidence_threshold}
                    onChange={handleChange}
                    disabled={loading}
                    min={0}
                    max={100}
                    className={styles.input}
                  />
                </div>

                {/* Risk Level */}
                <div className={styles.formGroup}>
                  <label htmlFor="risk_level" className={styles.label}>
                    Risk Level <span className={styles.required}>*</span>
                  </label>
                  <select
                    id="risk_level"
                    name="risk_level"
                    value={formData.risk_level}
                    onChange={handleChange}
                    disabled={loading}
                    className={`${styles.select} ${fieldErrors.risk_level ? styles.inputError : ""}`}
                    required
                  >
                    <option value="">-- Select Risk Level --</option>
                    <option value="LOW">LOW</option>
                    <option value="MEDIUM">MEDIUM</option>
                    <option value="HIGH">HIGH</option>
                    <option value="CRITICAL">CRITICAL</option>
                  </select>
                  {fieldErrors.risk_level && (
                    <span className={styles.fieldErrorText}>{fieldErrors.risk_level}</span>
                  )}
                </div>

                {/* Owner User */}
                <div className={styles.formGroup}>
                  <label htmlFor="owner_user_id" className={styles.label}>Owner User</label>
                  <select
                    id="owner_user_id"
                    name="owner_user_id"
                    value={formData.owner_user_id}
                    onChange={handleChange}
                    disabled={loading}
                    className={styles.select}
                  >
                    <option value="">-- Select Owner --</option>
                    {users.map((u) => (
                      <option key={u.id} value={u.id}>
                        {u.full_name} ({u.email})
                      </option>
                    ))}
                  </select>
                </div>

                {/* Department */}
                <div className={styles.formGroup}>
                  <label htmlFor="department_id" className={styles.label}>Department</label>
                  <select
                    id="department_id"
                    name="department_id"
                    value={formData.department_id}
                    onChange={handleChange}
                    disabled={loading}
                    className={styles.select}
                  >
                    <option value="">-- Select Department --</option>
                    {departments.map((d) => (
                      <option key={d.id} value={d.id}>
                        {d.department_name} ({d.department_code})
                      </option>
                    ))}
                  </select>
                </div>

                {/* Status (Edit mode only) */}
                {isEditMode && (
                  <div className={styles.formGroup}>
                    <label htmlFor="status" className={styles.label}>Entity Status</label>
                    <select
                      id="status"
                      name="status"
                      value={formData.status}
                      onChange={handleChange}
                      disabled={loading}
                      className={styles.select}
                    >
                      <option value="DRAFT">DRAFT</option>
                      <option value="ACTIVE">ACTIVE</option>
                      <option value="INACTIVE">INACTIVE</option>
                      <option value="SUSPENDED">SUSPENDED</option>
                      <option value="RETIRED">RETIRED</option>
                      <option value="ARCHIVED">ARCHIVED</option>
                    </select>
                  </div>
                )}
              </div>

              {/* Description */}
              <div className={styles.formGroupFull}>
                <label htmlFor="description" className={styles.label}>Description</label>
                <textarea
                  id="description"
                  name="description"
                  value={formData.description}
                  onChange={handleChange}
                  disabled={loading}
                  rows={3}
                  className={styles.textarea}
                />
              </div>

              {/* Capabilities JSON */}
              <div className={styles.formGroupFull}>
                <label htmlFor="capabilities_json" className={styles.label}>
                  Capabilities JSON
                </label>
                <textarea
                  id="capabilities_json"
                  name="capabilities_json"
                  value={formData.capabilities_json}
                  onChange={handleChange}
                  disabled={loading}
                  rows={4}
                  placeholder='{ "can_write": true, "integrations": ["slack"] }'
                  className={`${styles.textarea} ${styles.jsonTextarea} ${!isCapabilitiesJsonValid ? styles.invalidJson : ""}`}
                />
                {!isCapabilitiesJsonValid && (
                  <span className={styles.fieldErrorText}>Invalid JSON format. Please correct before submitting.</span>
                )}
              </div>

              {/* Form Actions */}
              <div className={styles.formActions}>
                <button
                  type="button"
                  onClick={onClose}
                  disabled={loading}
                  className={styles.cancelBtn}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading || !isCapabilitiesJsonValid}
                  className={styles.submitBtn}
                >
                  {loading ? "Saving..." : "Save Agent"}
                </button>
              </div>
            </form>
          )}

          {activeTab === "relationships" && (
            <div className={styles.placeholderTab}>
              Relationships viewer coming in Day 9
            </div>
          )}

          {activeTab === "audit" && (
            <div className={styles.placeholderTab}>
              Audit trail coming in Day 9
            </div>
          )}
        </div>
      </div>
    </Modal>
  );
};

/* src/components/registry/ModelFormModal.tsx */

import React, { useEffect, useState } from "react";
import { Modal } from "../common/Modal";
import { useToast } from "../../hooks/useToast";
import * as registryService from "../../services/registry/registryService";
import { EntityStatus } from "../../services/registry/registryTypes";
import { RelationshipViewer } from "./RelationshipViewer";
import { AuditTrailViewer } from "./AuditTrailViewer";
import { ConfirmDeleteModal } from "../common/ConfirmDeleteModal";
import styles from "./ModelFormModal.module.css";

interface ModelFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  modelId?: string | null;
  onSuccess: () => void;
}

export const ModelFormModal: React.FC<ModelFormModalProps> = ({
  isOpen,
  onClose,
  modelId,
  onSuccess
}) => {
  const { showToast } = useToast();
  const [activeTab, setActiveTab] = useState<"details" | "relationships" | "audit">("details");
  
  // Lookups data
  const [users, setUsers] = useState<{ id: string; full_name: string; email: string }[]>([]);
  const [departments, setDepartments] = useState<{ id: string; department_name: string; department_code: string }[]>([]);
  const [loadingLookups, setLoadingLookups] = useState(false);

  // Form State
  const [formData, setFormData] = useState({
    model_code: "",
    model_name: "",
    model_type: "",
    provider: "",
    version: "",
    purpose: "",
    owner_user_id: "",
    department_id: "",
    risk_level: "",
    deployment_environment: "",
    status: EntityStatus.DRAFT,
    metadata_json: ""
  });

  const [loading, setLoading] = useState(false);
  const [isMetadataJsonValid, setIsMetadataJsonValid] = useState(true);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [generalError, setGeneralError] = useState<string | null>(null);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  const isEditMode = !!modelId;

  // Reset form when modal opens or closes
  useEffect(() => {
    if (!isOpen) {
      setFormData({
        model_code: "",
        model_name: "",
        model_type: "",
        provider: "",
        version: "",
        purpose: "",
        owner_user_id: "",
        department_id: "",
        risk_level: "",
        deployment_environment: "",
        status: EntityStatus.DRAFT,
        metadata_json: ""
      });
      setFieldErrors({});
      setGeneralError(null);
      setActiveTab("details");
    }
  }, [isOpen]);

  // Load Lookups on mount
  useEffect(() => {
    async function loadLookups() {
      setLoadingLookups(true);
      try {
        const [usersRes, deptsRes] = await Promise.all([
          registryService.getUsersLookup(),
          registryService.getDepartmentsLookup()
        ]);
        if (usersRes.data) setUsers(usersRes.data);
        if (deptsRes.data) setDepartments(deptsRes.data);
      } catch (err) {
        console.error("Failed to load form lookups:", err);
      } finally {
        setLoadingLookups(false);
      }
    }
    if (isOpen) {
      loadLookups();
    }
  }, [isOpen]);

  // Load Model Data in Edit Mode
  useEffect(() => {
    async function loadModel() {
      if (!modelId) return;
      setLoading(true);
      setGeneralError(null);
      try {
        const res = await registryService.getModel(modelId);
        if (res.data) {
          const m = res.data;
          setFormData({
            model_code: m.model_code || (m as any).code || "",
            model_name: m.model_name || "",
            model_type: m.model_type || "",
            provider: (m as any).provider || "",
            version: m.model_version || (m as any).version || "",
            purpose: (m as any).purpose || m.description || "",
            owner_user_id: (m as any).owner_user_id || "",
            department_id: m.department_id || "",
            risk_level: m.risk_level || "",
            deployment_environment: (m as any).deployment_environment || "",
            status: m.status || EntityStatus.DRAFT,
            metadata_json: (m as any).metadata_json 
              ? typeof (m as any).metadata_json === "string" 
                ? (m as any).metadata_json 
                : JSON.stringify((m as any).metadata_json, null, 2)
              : ""
          });
        }
      } catch (err: any) {
        setGeneralError(err.message || "Failed to load model data.");
      } finally {
        setLoading(false);
      }
    }

    if (isOpen) {
      if (modelId) {
        loadModel();
        setActiveTab("details");
      } else {
        // Reset form for create mode
        setFormData({
          model_code: "",
          model_name: "",
          model_type: "",
          provider: "",
          version: "",
          purpose: "",
          owner_user_id: "",
          department_id: "",
          risk_level: "",
          deployment_environment: "",
          status: EntityStatus.DRAFT,
          metadata_json: ""
        });
        setFieldErrors({});
        setGeneralError(null);
        setActiveTab("details");
      }
    }
  }, [isOpen, modelId]);

  // Validate metadata_json
  useEffect(() => {
    if (!formData.metadata_json.trim()) {
      setIsMetadataJsonValid(true);
      return;
    }
    try {
      JSON.parse(formData.metadata_json);
      setIsMetadataJsonValid(true);
    } catch {
      setIsMetadataJsonValid(false);
    }
  }, [formData.metadata_json]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    // Clear field-level error when user starts typing
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

    // 1. Try parsing FastAPI standard flat string format:
    // "Validation Error: body.model_code: field required, body.model_name: field required"
    if (message.includes("Validation Error:")) {
      const errorContent = message.substring(message.indexOf("Validation Error:") + 17).trim();
      const parts = errorContent.split(", ");
      parts.forEach((part: string) => {
        const colonIndex = part.indexOf(":");
        if (colonIndex !== -1) {
          const fullField = part.substring(0, colonIndex).trim(); // "body.model_code"
          const msg = part.substring(colonIndex + 1).trim(); // "field required"
          let fieldName = fullField.replace("body.", "").trim(); // "model_code"
          
          // Map API validation errors to form fields
          if (fieldName === "description") fieldName = "purpose";
          if (fieldName === "model_version") fieldName = "version";
          if (fieldName === "code") fieldName = "model_code";
          
          newFieldErrors[fieldName] = msg;
        }
      });
    }

    // 2. Try parsing standard structured details array
    if (err.details && Array.isArray(err.details)) {
      err.details.forEach((d: any) => {
        let fieldName = d.field || (d.loc && d.loc[d.loc.length - 1]);
        if (fieldName) {
          fieldName = String(fieldName);
          
          // Map API validation errors to form fields
          if (fieldName === "description") fieldName = "purpose";
          if (fieldName === "model_version") fieldName = "version";
          if (fieldName === "code") fieldName = "model_code";
          
          newFieldErrors[fieldName] = d.message || d.msg || "Invalid value";
        }
      });
    }

    setFieldErrors(newFieldErrors);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isMetadataJsonValid) {
      showToast("Metadata must be a valid JSON object", "error");
      return;
    }

    setLoading(true);
    setGeneralError(null);
    setFieldErrors({});

    // Build payload matching backend expectation
    const payload = {
      ...formData,
      metadata_json: formData.metadata_json.trim() ? JSON.parse(formData.metadata_json) : null
    };

    try {
      if (isEditMode && modelId) {
        await registryService.updateModel(modelId, payload);
      } else {
        await registryService.createModel(payload);
      }
      showToast("Model saved successfully", "success");
      onSuccess();
      onClose();
    } catch (err: any) {
      handleApiError(err);
      showToast("Failed to save model", "error");
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!modelId) return;
    setIsDeleting(true);
    try {
      await registryService.deleteModel(modelId);
      showToast("Model deleted successfully", "success");
      setIsDeleteModalOpen(false);
      onSuccess();
      onClose();
    } catch (err: any) {
      showToast(err.message || "Failed to delete model", "error");
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={isEditMode ? `Edit Model: ${formData.model_name}` : "Register New AI Model"}
      size="lg"
    >
      <div className={styles.container}>
        {/* Form Tab Headers */}
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
              <div className={styles.formGrid}>
                {/* Model Code */}
                <div className={styles.formGroup}>
                  <label htmlFor="model_code" className={styles.label}>
                    Model Code <span className={styles.required}>*</span>
                  </label>
                  <input
                    type="text"
                    id="model_code"
                    name="model_code"
                    value={formData.model_code}
                    onChange={handleChange}
                    disabled={isEditMode || loading}
                    className={`${styles.input} ${fieldErrors.model_code ? styles.inputError : ""}`}
                    required
                  />
                  {fieldErrors.model_code && (
                    <span className={styles.fieldErrorText}>{fieldErrors.model_code}</span>
                  )}
                </div>

                {/* Model Name */}
                <div className={styles.formGroup}>
                  <label htmlFor="model_name" className={styles.label}>
                    Model Name <span className={styles.required}>*</span>
                  </label>
                  <input
                    type="text"
                    id="model_name"
                    name="model_name"
                    value={formData.model_name}
                    onChange={handleChange}
                    disabled={loading}
                    className={`${styles.input} ${fieldErrors.model_name ? styles.inputError : ""}`}
                    required
                  />
                  {fieldErrors.model_name && (
                    <span className={styles.fieldErrorText}>{fieldErrors.model_name}</span>
                  )}
                </div>

                {/* Model Type */}
                <div className={styles.formGroup}>
                  <label htmlFor="model_type" className={styles.label}>
                    Model Type <span className={styles.required}>*</span>
                  </label>
                  <select
                    id="model_type"
                    name="model_type"
                    value={formData.model_type}
                    onChange={handleChange}
                    disabled={loading}
                    className={`${styles.select} ${fieldErrors.model_type ? styles.inputError : ""}`}
                    required
                  >
                    <option value="">-- Select Type --</option>
                    <option value="LLM">LLM</option>
                    <option value="ML">ML</option>
                    <option value="CLASSIFIER">CLASSIFIER</option>
                    <option value="EMBEDDING">EMBEDDING</option>
                    <option value="RULE_BASED">RULE_BASED</option>
                    <option value="FORECASTING">FORECASTING</option>
                    <option value="OPTIMIZATION">OPTIMIZATION</option>
                  </select>
                  {fieldErrors.model_type && (
                    <span className={styles.fieldErrorText}>{fieldErrors.model_type}</span>
                  )}
                </div>

                {/* Provider */}
                <div className={styles.formGroup}>
                  <label htmlFor="provider" className={styles.label}>Provider</label>
                  <input
                    type="text"
                    id="provider"
                    name="provider"
                    value={formData.provider}
                    onChange={handleChange}
                    disabled={loading}
                    placeholder="e.g. OpenAI, Anthropic, Custom"
                    className={styles.input}
                  />
                </div>

                {/* Version */}
                <div className={styles.formGroup}>
                  <label htmlFor="version" className={styles.label}>Version</label>
                  <input
                    type="text"
                    id="version"
                    name="version"
                    value={formData.version}
                    onChange={handleChange}
                    disabled={loading}
                    placeholder="e.g. 1.0.0"
                    className={styles.input}
                  />
                </div>

                {/* Owner User */}
                <div className={styles.formGroup}>
                  <label htmlFor="owner_user_id" className={styles.label}>Owner User</label>
                  <select
                    id="owner_user_id"
                    name="owner_user_id"
                    value={formData.owner_user_id}
                    onChange={handleChange}
                    disabled={loading || loadingLookups}
                    className={styles.select}
                  >
                    {loadingLookups ? (
                      <option value="">Loading owners...</option>
                    ) : (
                      <>
                        <option value="">-- Select Owner --</option>
                        {users.map((u) => (
                          <option key={u.id} value={u.id}>
                            {u.full_name} ({u.email})
                          </option>
                        ))}
                      </>
                    )}
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
                    disabled={loading || loadingLookups}
                    className={styles.select}
                  >
                    {loadingLookups ? (
                      <option value="">Loading departments...</option>
                    ) : (
                      <>
                        <option value="">-- Select Department --</option>
                        {departments.map((d) => (
                          <option key={d.id} value={d.id}>
                            {d.department_name} ({d.department_code})
                          </option>
                        ))}
                      </>
                    )}
                  </select>
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

                {/* Deployment Environment */}
                <div className={styles.formGroup}>
                  <label htmlFor="deployment_environment" className={styles.label}>Deployment Environment</label>
                  <select
                    id="deployment_environment"
                    name="deployment_environment"
                    value={formData.deployment_environment}
                    onChange={handleChange}
                    disabled={loading}
                    className={styles.select}
                  >
                    <option value="">-- Select Env --</option>
                    <option value="DEV">DEV</option>
                    <option value="TEST">TEST</option>
                    <option value="PROD">PROD</option>
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

              {/* Purpose (Required Textarea) */}
              <div className={styles.formGroupFull}>
                <label htmlFor="purpose" className={styles.label}>
                  Purpose / Description <span className={styles.required}>*</span>
                </label>
                <textarea
                  id="purpose"
                  name="purpose"
                  value={formData.purpose}
                  onChange={handleChange}
                  disabled={loading}
                  rows={3}
                  className={`${styles.textarea} ${fieldErrors.purpose ? styles.inputError : ""}`}
                  required
                />
                {fieldErrors.purpose && (
                  <span className={styles.fieldErrorText}>{fieldErrors.purpose}</span>
                )}
              </div>

              {/* Metadata JSON (Validate valid JSON) */}
              <div className={styles.formGroupFull}>
                <label htmlFor="metadata_json" className={styles.label}>
                  Metadata JSON
                </label>
                <textarea
                  id="metadata_json"
                  name="metadata_json"
                  value={formData.metadata_json}
                  onChange={handleChange}
                  disabled={loading}
                  rows={4}
                  placeholder='{ "key": "value" }'
                  className={`${styles.textarea} ${styles.jsonTextarea} ${!isMetadataJsonValid ? styles.invalidJson : ""}`}
                />
                {!isMetadataJsonValid && (
                  <span className={styles.fieldErrorText}>Invalid JSON formatting. Please correct before submitting.</span>
                )}
              </div>

              {/* Form Actions */}
              <div className={styles.formActions}>
                {isEditMode && (
                  <button
                    type="button"
                    onClick={() => setIsDeleteModalOpen(true)}
                    disabled={loading}
                    className={styles.deleteBtn}
                  >
                    Delete
                  </button>
                )}
                <div className={styles.rightActions}>
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
                    disabled={loading || !isMetadataJsonValid}
                    className={styles.submitBtn}
                  >
                    {loading ? "Saving..." : "Save Model"}
                  </button>
                </div>
              </div>
            </form>
          )}

          {activeTab === "relationships" && (
            <RelationshipViewer entityType="MODEL" entityId={modelId!} />
          )}

          {activeTab === "audit" && (
            <AuditTrailViewer entityType="MODEL" entityId={modelId!} />
          )}
        </div>
      </div>
      
      {isEditMode && (
        <ConfirmDeleteModal
          isOpen={isDeleteModalOpen}
          onClose={() => setIsDeleteModalOpen(false)}
          onConfirm={handleDelete}
          entityName={formData.model_name || formData.model_code || 'Model'}
          entityType="Model"
          isDeleting={isDeleting}
        />
      )}
    </Modal>
  );
};

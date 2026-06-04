/* src/components/registry/ModelFormModal.tsx */

import React, { useEffect, useState } from "react";
import { Modal } from "../common/Modal";
import { useToast } from "../../hooks/useToast";
import * as registryService from "../../services/registry/registryService";
import { EntityStatus } from "../../services/registry/registryTypes";
import { RelationshipViewer } from "./RelationshipViewer";
import { AuditTrailViewer } from "./AuditTrailViewer";
import { ConfirmDeleteModal } from "../common/ConfirmDeleteModal";
import WizardShell from "../common/WizardShell";
import styles from "./ModelFormModal.module.css";

const FieldInfo: React.FC<{ tooltip: string }> = ({ tooltip }) => (
  <span title={tooltip} style={{ cursor: "help", marginLeft: "4px", color: "#888", fontSize: "0.85em", fontWeight: "normal" }}>(?)</span>
);

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
  const [currentWizardStep, setCurrentWizardStep] = useState(0);

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
    metadata_json: "",
    provider_type: "",
    provider_name: "",
    provider_owner_department: "",
    provider_developed_by: "",
    provider_training_data: "",
    provider_fine_tuned_from: "",
    provider_hosting: "",
    provider_security: "",
    provider_approved_usage: "",
    provider_restricted_usage: "",
    provider_model_card: "",
    provider_evaluation: "",
    provider_responsible_person: ""
  });

  const [loading, setLoading] = useState(false);
  const [isMetadataJsonValid, setIsMetadataJsonValid] = useState(true);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [generalError, setGeneralError] = useState<string | null>(null);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  const isEditMode = !!modelId;

  const wizardSteps = [
    { label: "Core parameters" },
    { label: "Governance & alignment" },
    { label: "Description & metadata" }
  ];

  const validateAndAdvance = (targetStep: number) => {
    if (isEditMode) {
      setCurrentWizardStep(targetStep);
      return;
    }
    
    // In create (strict) mode, validate before advancing
    if (targetStep > currentWizardStep) {
      if (currentWizardStep === 0) {
        if (!formData.model_code || !formData.model_name || !formData.model_type) {
          showToast("Please fill in all required fields for Core parameters", "error");
          return;
        }
      }
      if (currentWizardStep === 1) {
        if (!formData.risk_level) {
          showToast("Please fill in all required fields for Governance & alignment", "error");
          return;
        }
      }
    }
    setCurrentWizardStep(targetStep);
  };

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
        metadata_json: "",
        provider_type: "",
        provider_name: "",
        provider_owner_department: "",
        provider_developed_by: "",
        provider_training_data: "",
        provider_fine_tuned_from: "",
        provider_hosting: "",
        provider_security: "",
        provider_approved_usage: "",
        provider_restricted_usage: "",
        provider_model_card: "",
        provider_evaluation: "",
        provider_responsible_person: ""
      });
      setFieldErrors({});
      setGeneralError(null);
      setActiveTab("details");
      setCurrentWizardStep(0);
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
              : "",
            provider_type: (m as any).provider_type || (m as any).metadata_json?.provider_type || "",
            provider_name: (m as any).provider_name || (m as any).metadata_json?.provider_name || "",
            provider_owner_department: (m as any).metadata_json?.provider_owner_department || "",
            provider_developed_by: (m as any).metadata_json?.provider_developed_by || "",
            provider_training_data: (m as any).metadata_json?.provider_training_data || "",
            provider_fine_tuned_from: (m as any).metadata_json?.provider_fine_tuned_from || "",
            provider_hosting: (m as any).metadata_json?.provider_hosting || "",
            provider_security: (m as any).metadata_json?.provider_security || "",
            provider_approved_usage: (m as any).metadata_json?.provider_approved_usage || "",
            provider_restricted_usage: (m as any).metadata_json?.provider_restricted_usage || "",
            provider_model_card: (m as any).metadata_json?.provider_model_card || "",
            provider_evaluation: (m as any).metadata_json?.provider_evaluation || "",
            provider_responsible_person: (m as any).metadata_json?.provider_responsible_person || ""
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
        setCurrentWizardStep(0);
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
          metadata_json: "",
          provider_type: "",
          provider_name: "",
          provider_owner_department: "",
          provider_developed_by: "",
          provider_training_data: "",
          provider_fine_tuned_from: "",
          provider_hosting: "",
          provider_security: "",
          provider_approved_usage: "",
          provider_restricted_usage: "",
          provider_model_card: "",
          provider_evaluation: "",
          provider_responsible_person: ""
        });
        setFieldErrors({});
        setGeneralError(null);
        setActiveTab("details");
        setCurrentWizardStep(0);
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

    // Build metadata json
    let parsedMetadata = {};
    if (formData.metadata_json.trim()) {
      parsedMetadata = JSON.parse(formData.metadata_json);
    }
    
    // Inject provider details into metadata_json
    parsedMetadata = {
      ...parsedMetadata,
      provider_type: formData.provider_type,
      provider_name: formData.provider_name,
      ...(formData.provider_type === "Internal Custom" || formData.provider_type === "Client-owned Model" ? {
        provider_owner_department: formData.provider_owner_department,
        provider_developed_by: formData.provider_developed_by,
        provider_training_data: formData.provider_training_data,
        provider_fine_tuned_from: formData.provider_fine_tuned_from,
        provider_hosting: formData.provider_hosting,
        provider_security: formData.provider_security,
        provider_approved_usage: formData.provider_approved_usage,
        provider_restricted_usage: formData.provider_restricted_usage,
        provider_model_card: formData.provider_model_card,
        provider_evaluation: formData.provider_evaluation,
        provider_responsible_person: formData.provider_responsible_person
      } : {})
    };

    const payload = {
      ...formData,
      metadata_json: parsedMetadata
    };
    // Clean up temporary flat fields
    delete (payload as any).provider_type;
    delete (payload as any).provider_name;
    delete (payload as any).provider_owner_department;
    delete (payload as any).provider_developed_by;
    delete (payload as any).provider_training_data;
    delete (payload as any).provider_fine_tuned_from;
    delete (payload as any).provider_hosting;
    delete (payload as any).provider_security;
    delete (payload as any).provider_approved_usage;
    delete (payload as any).provider_restricted_usage;
    delete (payload as any).provider_model_card;
    delete (payload as any).provider_evaluation;
    delete (payload as any).provider_responsible_person;

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
              <WizardShell
                steps={wizardSteps}
                currentStep={currentWizardStep}
                onStepClick={validateAndAdvance}
                mode={isEditMode ? "tabbed" : "strict"}
              >
                {/* STEP 1: Core parameters */}
                {currentWizardStep === 0 && (
                  <div>
                    <div className={styles.formGrid}>
                      {/* Model Code */}
                      <div className={styles.formGroup}>
                        <label htmlFor="model_code" className={styles.label}>
                          Model Code <span className={styles.required}>*</span>
                          <FieldInfo tooltip="Unique identifier for this AI model." />
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
                          <FieldInfo tooltip="The common name used for this AI model." />
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

                      {/* Version */}
                      <div className={styles.formGroup}>
                        <label htmlFor="version" className={styles.label}>Version <FieldInfo tooltip="The specific version or release tag of the model." /></label>
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

                      {/* Model Type */}
                      <div className={styles.formGroup}>
                        <label htmlFor="model_type" className={styles.label}>
                          Model Type <span className={styles.required}>*</span>
                          <FieldInfo tooltip="The architectural category of the model." />
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
                    </div>

                    <div className={styles.formActions} style={{ marginTop: '1.5rem' }}>
                      <div className={styles.rightActions} style={{ width: '100%', justifyContent: 'flex-end' }}>
                        <button type="button" onClick={() => validateAndAdvance(1)} className={styles.submitBtn}>
                          Next
                        </button>
                      </div>
                    </div>
                  </div>
                )}

                {/* STEP 2: Governance & alignment */}
                {currentWizardStep === 1 && (
                  <div>
                    <div className={styles.formGrid}>
                      {/* Risk Level */}
                      <div className={styles.formGroup}>
                        <label htmlFor="risk_level" className={styles.label}>
                          Risk Level <span className={styles.required}>*</span>
                          <FieldInfo tooltip="The assessed risk level associated with using this model." />
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

                      {/* Department */}
                      <div className={styles.formGroup}>
                        <label htmlFor="department_id" className={styles.label}>Department <FieldInfo tooltip="The department that owns or manages this model." /></label>
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

                      {/* Deployment Environment */}
                      <div className={styles.formGroup}>
                        <label htmlFor="deployment_environment" className={styles.label}>Deployment Environment <FieldInfo tooltip="Where this model is currently deployed." /></label>
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
                          <label htmlFor="status" className={styles.label}>Entity Status <FieldInfo tooltip="The current lifecycle status of the model." /></label>
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

                    <div className={styles.formActions} style={{ marginTop: '1.5rem' }}>
                      <button type="button" onClick={() => setCurrentWizardStep(0)} className={styles.cancelBtn}>
                        Back
                      </button>
                      <div className={styles.rightActions}>
                        <button type="button" onClick={() => validateAndAdvance(2)} className={styles.submitBtn}>
                          Next
                        </button>
                      </div>
                    </div>
                  </div>
                )}

                {/* STEP 3: Description & metadata */}
                {currentWizardStep === 2 && (
                  <div>
                    {/* Purpose (Required Textarea) */}
                    <div className={styles.formGroupFull}>
                      <label htmlFor="purpose" className={styles.label}>
                        Purpose / Description <span className={styles.required}>*</span>
                        <FieldInfo tooltip="A detailed description of what the model does and its intended use." />
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

                    <div className={styles.formGrid}>
                      {/* Provider Type */}
                      <div className={styles.formGroup}>
                        <label htmlFor="provider_type" className={styles.label}>
                          Provider Type <span className={styles.required}>*</span>
                          <FieldInfo tooltip="The category of the model provider." />
                        </label>
                        <select
                          id="provider_type"
                          name="provider_type"
                          value={formData.provider_type}
                          onChange={handleChange}
                          disabled={loading}
                          className={`${styles.select} ${fieldErrors.provider_type ? styles.inputError : ""}`}
                          required
                        >
                          <option value="">-- Select Provider Type --</option>
                          <option value="Enterprise Vendor">Enterprise Vendor</option>
                          <option value="Open Source / Hub">Open Source / Hub</option>
                          <option value="Internal Custom">Internal Custom</option>
                          <option value="Fine-tuned Model">Fine-tuned Model</option>
                          <option value="Client-owned Model">Client-owned Model</option>
                          <option value="Partner-provided Model">Partner-provided Model</option>
                          <option value="Clinical / Domain-specific Provider">Clinical / Domain-specific Provider</option>
                          <option value="Other">Other</option>
                        </select>
                        {fieldErrors.provider_type && (
                          <span className={styles.fieldErrorText}>{fieldErrors.provider_type}</span>
                        )}
                      </div>

                      {/* Provider Name */}
                      <div className={styles.formGroup}>
                        <label htmlFor="provider_name" className={styles.label}>
                          Provider Name <span className={styles.required}>*</span>
                          <FieldInfo tooltip="The specific name of the provider or the custom model name." />
                        </label>
                        <input
                          type="text"
                          id="provider_name"
                          name="provider_name"
                          value={formData.provider_name}
                          onChange={handleChange}
                          disabled={loading}
                          placeholder="e.g. OpenAI Enterprise, Internal Client Model"
                          className={`${styles.input} ${fieldErrors.provider_name ? styles.inputError : ""}`}
                          required
                        />
                        {fieldErrors.provider_name && (
                          <span className={styles.fieldErrorText}>{fieldErrors.provider_name}</span>
                        )}
                      </div>

                      {/* Owner User */}
                      <div className={styles.formGroup}>
                        <label htmlFor="owner_user_id" className={styles.label}>Owner User <FieldInfo tooltip="The user primarily responsible for this model." /></label>
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
                    </div>

                    {/* Provider Details (Conditional) */}
                    {(formData.provider_type === "Internal Custom" || formData.provider_type === "Client-owned Model") && (
                      <div className={styles.formGroupFull} style={{ marginTop: '1rem', padding: '1rem', border: '1px solid #ccc', borderRadius: '4px' }}>
                        <h4 style={{ margin: '0 0 1rem 0' }}>Provider Details</h4>
                        <div className={styles.formGrid}>
                          <div className={styles.formGroup}>
                            <label htmlFor="provider_owner_department" className={styles.label}>Owner Department <FieldInfo tooltip="Department that owns the internal or custom model." /></label>
                            <input type="text" id="provider_owner_department" name="provider_owner_department" value={formData.provider_owner_department} onChange={handleChange} disabled={loading} className={styles.input} />
                          </div>
                          <div className={styles.formGroup}>
                            <label htmlFor="provider_developed_by" className={styles.label}>Developed By <FieldInfo tooltip="The team or entity that originally developed the model." /></label>
                            <input type="text" id="provider_developed_by" name="provider_developed_by" value={formData.provider_developed_by} onChange={handleChange} disabled={loading} className={styles.input} />
                          </div>
                          <div className={styles.formGroup}>
                            <label htmlFor="provider_training_data" className={styles.label}>Training Data Source <FieldInfo tooltip="Details about the dataset used to train the model." /></label>
                            <input type="text" id="provider_training_data" name="provider_training_data" value={formData.provider_training_data} onChange={handleChange} disabled={loading} className={styles.input} />
                          </div>
                          <div className={styles.formGroup}>
                            <label htmlFor="provider_fine_tuned_from" className={styles.label}>Fine-tuned From <FieldInfo tooltip="If applicable, the base model this was fine-tuned from." /></label>
                            <input type="text" id="provider_fine_tuned_from" name="provider_fine_tuned_from" value={formData.provider_fine_tuned_from} onChange={handleChange} disabled={loading} className={styles.input} />
                          </div>
                          <div className={styles.formGroup}>
                            <label htmlFor="provider_hosting" className={styles.label}>Hosting Environment <FieldInfo tooltip="Where the model is hosted (e.g. AWS, Azure, On-prem)." /></label>
                            <input type="text" id="provider_hosting" name="provider_hosting" value={formData.provider_hosting} onChange={handleChange} disabled={loading} className={styles.input} />
                          </div>
                          <div className={styles.formGroup}>
                            <label htmlFor="provider_security" className={styles.label}>Security Classification <FieldInfo tooltip="The security rating of the model." /></label>
                            <input type="text" id="provider_security" name="provider_security" value={formData.provider_security} onChange={handleChange} disabled={loading} className={styles.input} />
                          </div>
                          <div className={styles.formGroup}>
                            <label htmlFor="provider_approved_usage" className={styles.label}>Approved Usage <FieldInfo tooltip="Scenarios in which the model is explicitly approved to be used." /></label>
                            <input type="text" id="provider_approved_usage" name="provider_approved_usage" value={formData.provider_approved_usage} onChange={handleChange} disabled={loading} className={styles.input} />
                          </div>
                          <div className={styles.formGroup}>
                            <label htmlFor="provider_restricted_usage" className={styles.label}>Restricted Usage <FieldInfo tooltip="Scenarios in which the model must NOT be used." /></label>
                            <input type="text" id="provider_restricted_usage" name="provider_restricted_usage" value={formData.provider_restricted_usage} onChange={handleChange} disabled={loading} className={styles.input} />
                          </div>
                          <div className={styles.formGroup}>
                            <label htmlFor="provider_model_card" className={styles.label}>Model Card Available? <FieldInfo tooltip="Does the model have a documented Model Card?" /></label>
                            <select id="provider_model_card" name="provider_model_card" value={formData.provider_model_card} onChange={handleChange} disabled={loading} className={styles.select}>
                              <option value="">-- Select --</option>
                              <option value="Yes">Yes</option>
                              <option value="No">No</option>
                            </select>
                          </div>
                          <div className={styles.formGroup}>
                            <label htmlFor="provider_evaluation" className={styles.label}>Evaluation Completed? <FieldInfo tooltip="Has the model undergone a formal evaluation/testing process?" /></label>
                            <select id="provider_evaluation" name="provider_evaluation" value={formData.provider_evaluation} onChange={handleChange} disabled={loading} className={styles.select}>
                              <option value="">-- Select --</option>
                              <option value="Yes">Yes</option>
                              <option value="No">No</option>
                            </select>
                          </div>
                          <div className={styles.formGroup}>
                            <label htmlFor="provider_responsible_person" className={styles.label}>Responsible Person <FieldInfo tooltip="The individual accountable for this model." /></label>
                            <input type="text" id="provider_responsible_person" name="provider_responsible_person" value={formData.provider_responsible_person} onChange={handleChange} disabled={loading} className={styles.input} />
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Metadata JSON (Validate valid JSON) */}
                    <div className={styles.formGroupFull}>
                      <label htmlFor="metadata_json" className={styles.label}>
                        Metadata JSON <FieldInfo tooltip="Any additional structured configuration or details in JSON format." />
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

                    <div className={styles.formActions} style={{ marginTop: '1.5rem' }}>
                      <button type="button" onClick={() => setCurrentWizardStep(1)} className={styles.cancelBtn}>
                        Back
                      </button>

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
                  </div>
                )}
              </WizardShell>
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

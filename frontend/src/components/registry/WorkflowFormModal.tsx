/* src/components/registry/WorkflowFormModal.tsx */

import React, { useEffect, useState } from "react";
import { Modal } from "../common/Modal";
import { useToast } from "../../hooks/useToast";
import * as registryService from "../../services/registry/registryService";
import { EntityStatus } from "../../services/registry/registryTypes";
import { RelationshipViewer } from "./RelationshipViewer";
import { AuditTrailViewer } from "./AuditTrailViewer";
import { ConfirmDeleteModal } from "../common/ConfirmDeleteModal";
import WizardShell from "../common/WizardShell";
import WorkflowNodeCanvas, { WorkflowStep } from "./WorkflowNodeCanvas";
import styles from "./WorkflowFormModal.module.css";

const FieldInfo: React.FC<{ tooltip: string }> = ({ tooltip }) => (
  <span title={tooltip} style={{ cursor: "help", marginLeft: "4px", color: "#888", fontSize: "0.85em", fontWeight: "normal" }}>(?)</span>
);

interface WorkflowFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  workflowId?: string | null;
  onSuccess: () => void;
}

export const WorkflowFormModal: React.FC<WorkflowFormModalProps> = ({
  isOpen,
  onClose,
  workflowId,
  onSuccess
}) => {
  const { showToast } = useToast();
  const [activeTab, setActiveTab] = useState<"details" | "relationships" | "audit">("details");
  const [currentWizardStep, setCurrentWizardStep] = useState(0);

  // Lookups data
  const [users, setUsers] = useState<{ id: string; full_name: string; email: string }[]>([]);
  const [departments, setDepartments] = useState<{ id: string; department_name: string; department_code: string }[]>([]);

  // Form State
  const [formData, setFormData] = useState({
    workflow_code: "",
    workflow_name: "",
    workflow_type: "",
    department_id: "",
    owner_user_id: "",
    description: "",
    approval_required: false,
    business_criticality: "",
    status: EntityStatus.DRAFT,
    metadata_json: ""
  });

  // Steps Builder state
  const [steps, setSteps] = useState<WorkflowStep[]>([]);

  const [loading, setLoading] = useState(false);
  const [isMetadataJsonValid, setIsMetadataJsonValid] = useState(true);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [generalError, setGeneralError] = useState<string | null>(null);
  const [loadingLookups, setLoadingLookups] = useState(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  const isEditMode = !!workflowId;

  const wizardSteps = [
    { label: "Workflow identity" },
    { label: "Build steps" },
    { label: "Properties & metadata" }
  ];

  const validateAndAdvance = (targetStep: number) => {
    if (isEditMode) {
      setCurrentWizardStep(targetStep);
      return;
    }
    
    // In create (strict) mode, validate before advancing
    if (targetStep > currentWizardStep) {
      if (currentWizardStep === 0) {
        if (!formData.workflow_code || !formData.workflow_name || !formData.workflow_type || !formData.business_criticality) {
          showToast("Please fill in all required fields for Workflow identity", "error");
          return;
        }
      }
      // Step 1 -> 2 is fine. Step 2 -> 3 has no mandatory fields right now except maybe steps.
      if (currentWizardStep === 1) {
        if (steps.length === 0) {
           // Optionally warn, but we'll let it pass if they want empty workflows
        }
      }
    }
    setCurrentWizardStep(targetStep);
  };

  // Reset form when modal opens or closes
  useEffect(() => {
    if (!isOpen) {
      setFormData({
        workflow_code: "",
        workflow_name: "",
        workflow_type: "",
        department_id: "",
        owner_user_id: "",
        description: "",
        approval_required: false,
        business_criticality: "",
        status: EntityStatus.DRAFT,
        metadata_json: ""
      });
      setSteps([]);
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
        console.error("Failed to load lookups:", err);
      } finally {
        setLoadingLookups(false);
      }
    }
    if (isOpen) {
      loadLookups();
    }
  }, [isOpen]);

  // Load Workflow data in edit mode
  useEffect(() => {
    async function loadWorkflow() {
      if (!workflowId) return;
      setLoading(true);
      setGeneralError(null);
      try {
        const res = await registryService.getWorkflow(workflowId);
        if (res.data) {
          const w = res.data;
          setFormData({
            workflow_code: w.workflow_code || (w as any).code || "",
            workflow_name: w.workflow_name || "",
            workflow_type: w.workflow_type || "",
            department_id: w.department_id || "",
            owner_user_id: w.owner_user_id || "",
            description: w.description || "",
            approval_required: !!w.approval_required,
            business_criticality: w.business_criticality || "",
            status: w.status || EntityStatus.DRAFT,
            metadata_json: w.metadata_json
              ? typeof w.metadata_json === "string"
                ? w.metadata_json
                : JSON.stringify(w.metadata_json, null, 2)
              : ""
          });

          // Deserialize steps
          let parsedSteps: any[] = [];
          if (w.steps_json) {
            try {
              parsedSteps = typeof w.steps_json === "string"
                ? JSON.parse(w.steps_json)
                : w.steps_json;
            } catch (e) {
              console.error("Failed to parse steps_json:", e);
            }
          }
          setSteps(Array.isArray(parsedSteps) ? parsedSteps : []);
        }
      } catch (err: any) {
        setGeneralError(err.message || "Failed to load workflow data.");
      } finally {
        setLoading(false);
      }
    }

    if (isOpen) {
      if (workflowId) {
        loadWorkflow();
        setActiveTab("details");
        setCurrentWizardStep(0);
      } else {
        // Reset form for create mode
        setFormData({
          workflow_code: "",
          workflow_name: "",
          workflow_type: "",
          department_id: "",
          owner_user_id: "",
          description: "",
          approval_required: false,
          business_criticality: "",
          status: EntityStatus.DRAFT,
          metadata_json: ""
        });
        setSteps([]);
        setFieldErrors({});
        setGeneralError(null);
        setActiveTab("details");
        setCurrentWizardStep(0);
      }
    }
  }, [isOpen, workflowId]);

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
    const { name, value, type } = e.target;
    const val = type === "checkbox" ? (e.target as HTMLInputElement).checked : value;
    setFormData((prev) => ({ ...prev, [name]: val }));
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

    // Parse FastAPI flat errors
    if (message.includes("Validation Error:")) {
      const errorContent = message.substring(message.indexOf("Validation Error:") + 17).trim();
      const parts = errorContent.split(", ");
      parts.forEach((part: string) => {
        const colonIndex = part.indexOf(":");
        if (colonIndex !== -1) {
          const fullField = part.substring(0, colonIndex).trim();
          const msg = part.substring(colonIndex + 1).trim();
          let fieldName = fullField.replace("body.", "").trim();
          
          if (fieldName === "code") fieldName = "workflow_code";
          
          newFieldErrors[fieldName] = msg;
        }
      });
    }

    // Parse structured details array
    if (err.details && Array.isArray(err.details)) {
      err.details.forEach((d: any) => {
        let fieldName = d.field || (d.loc && d.loc[d.loc.length - 1]);
        if (fieldName) {
          fieldName = String(fieldName);
          
          if (fieldName === "code") fieldName = "workflow_code";
          
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

    const payload = {
      ...formData,
      steps_json: steps,
      metadata_json: formData.metadata_json.trim() ? JSON.parse(formData.metadata_json) : null
    };

    try {
      if (isEditMode && workflowId) {
        await registryService.updateWorkflow(workflowId, payload);
      } else {
        await registryService.createWorkflow(payload);
      }
      showToast("Workflow saved successfully", "success");
      onSuccess();
      onClose();
    } catch (err: any) {
      handleApiError(err);
      showToast("Failed to save workflow", "error");
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!workflowId) return;
    setIsDeleting(true);
    try {
      await registryService.deleteWorkflow(workflowId);
      showToast("Workflow deleted successfully", "success");
      setIsDeleteModalOpen(false);
      onSuccess();
      onClose();
    } catch (err: any) {
      showToast(err.message || "Failed to delete workflow", "error");
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={isEditMode ? `Edit Workflow: ${formData.workflow_name}` : "Register New Governance Workflow"}
      size="xl"
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
              <WizardShell
                steps={wizardSteps}
                currentStep={currentWizardStep}
                onStepClick={validateAndAdvance}
                mode={isEditMode ? "tabbed" : "strict"}
              >
                {/* STEP 1: Workflow identity */}
                {currentWizardStep === 0 && (
                  <div>
                    <div className={styles.formGrid}>
                      {/* Workflow Code */}
                      <div className={styles.formGroup}>
                        <label htmlFor="workflow_code" className={styles.label}>
                          Workflow Code <span className={styles.required}>*</span>
                          <FieldInfo tooltip="Unique identifier code for this workflow." />
                        </label>
                        <input
                          type="text"
                          id="workflow_code"
                          name="workflow_code"
                          value={formData.workflow_code}
                          onChange={handleChange}
                          disabled={isEditMode || loading}
                          className={`${styles.input} ${fieldErrors.workflow_code ? styles.inputError : ""}`}
                          required
                        />
                        {fieldErrors.workflow_code && (
                          <span className={styles.fieldErrorText}>{fieldErrors.workflow_code}</span>
                        )}
                      </div>

                      {/* Workflow Name */}
                      <div className={styles.formGroup}>
                        <label htmlFor="workflow_name" className={styles.label}>
                          Workflow Name <span className={styles.required}>*</span>
                          <FieldInfo tooltip="The common name of this workflow." />
                        </label>
                        <input
                          type="text"
                          id="workflow_name"
                          name="workflow_name"
                          value={formData.workflow_name}
                          onChange={handleChange}
                          disabled={loading}
                          className={`${styles.input} ${fieldErrors.workflow_name ? styles.inputError : ""}`}
                          required
                        />
                        {fieldErrors.workflow_name && (
                          <span className={styles.fieldErrorText}>{fieldErrors.workflow_name}</span>
                        )}
                      </div>

                      {/* Workflow Type */}
                      <div className={styles.formGroup}>
                        <label htmlFor="workflow_type" className={styles.label}>
                          Workflow Type <span className={styles.required}>*</span>
                          <FieldInfo tooltip="The functional category of this workflow." />
                        </label>
                        <select
                          id="workflow_type"
                          name="workflow_type"
                          value={formData.workflow_type}
                          onChange={handleChange}
                          disabled={loading}
                          className={`${styles.select} ${fieldErrors.workflow_type ? styles.inputError : ""}`}
                          required
                        >
                          <option value="">-- Select Type --</option>
                          <option value="ENQUIRY">ENQUIRY</option>
                          <option value="APPROVAL">APPROVAL</option>
                          <option value="CUSTOMER_SIGNAL">CUSTOMER_SIGNAL</option>
                          <option value="RISK_REVIEW">RISK_REVIEW</option>
                          <option value="OPERATIONAL_ACTION">OPERATIONAL_ACTION</option>
                        </select>
                        {fieldErrors.workflow_type && (
                          <span className={styles.fieldErrorText}>{fieldErrors.workflow_type}</span>
                        )}
                      </div>

                      {/* Department */}
                      <div className={styles.formGroup}>
                        <label htmlFor="department_id" className={styles.label}>Department <FieldInfo tooltip="The department that owns or manages this workflow." /></label>
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

                      {/* Business Criticality */}
                      <div className={styles.formGroup}>
                        <label htmlFor="business_criticality" className={styles.label}>
                          Business Criticality <span className={styles.required}>*</span>
                          <FieldInfo tooltip="The assessed business impact of this workflow." />
                        </label>
                        <select
                          id="business_criticality"
                          name="business_criticality"
                          value={formData.business_criticality}
                          onChange={handleChange}
                          disabled={loading}
                          className={`${styles.select} ${fieldErrors.business_criticality ? styles.inputError : ""}`}
                          required
                        >
                          <option value="">-- Select Criticality --</option>
                          <option value="LOW">LOW</option>
                          <option value="MEDIUM">MEDIUM</option>
                          <option value="HIGH">HIGH</option>
                          <option value="CRITICAL">CRITICAL</option>
                        </select>
                        {fieldErrors.business_criticality && (
                          <span className={styles.fieldErrorText}>{fieldErrors.business_criticality}</span>
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

                {/* STEP 2: Build steps */}
                {currentWizardStep === 1 && (
                  <div>
                    <div style={{ marginBottom: '1rem', color: '#94a3b8', fontSize: '14px' }}>
                      Design the workflow by adding nodes and connecting them. Changes are saved automatically.
                    </div>
                    <WorkflowNodeCanvas 
                      value={steps} 
                      onChange={setSteps} 
                    />

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

                {/* STEP 3: Properties & metadata */}
                {currentWizardStep === 2 && (
                  <div>
                    <div className={styles.formGrid}>
                      {/* Owner User */}
                      <div className={styles.formGroup}>
                        <label htmlFor="owner_user_id" className={styles.label}>Owner User <FieldInfo tooltip="The primary business owner of this workflow." /></label>
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

                      {/* Approval Required checkbox toggle */}
                      <div className={`${styles.formGroup} ${styles.checkboxGroup}`} style={{ display: 'flex', alignItems: 'center' }}>
                        <label htmlFor="approval_required" className={styles.checkboxLabel} style={{ marginBottom: 0 }}>
                          <input
                            type="checkbox"
                            id="approval_required"
                            name="approval_required"
                            checked={formData.approval_required}
                            onChange={handleChange}
                            disabled={loading}
                            className={styles.checkboxInput}
                          />
                          <span>Requires Governance Approval <FieldInfo tooltip="Whether explicit governance approval is required before execution." /></span>
                        </label>
                      </div>

                      {/* Status (Edit only) */}
                      {isEditMode && (
                        <div className={styles.formGroup}>
                          <label htmlFor="status" className={styles.label}>Entity Status <FieldInfo tooltip="The current active status of this workflow." /></label>
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
                    <div className={styles.formGroupFull} style={{ marginTop: '1rem' }}>
                      <label htmlFor="description" className={styles.label}>
                        Description <FieldInfo tooltip="A detailed description of what the workflow does." />
                      </label>
                      <textarea
                        id="description"
                        name="description"
                        value={formData.description}
                        onChange={handleChange}
                        disabled={loading}
                        rows={2}
                        className={styles.textarea}
                      />
                    </div>

                    {/* Metadata JSON */}
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
                        rows={3}
                        placeholder='{ "key": "value" }'
                        className={`${styles.textarea} ${styles.jsonTextarea} ${!isMetadataJsonValid ? styles.invalidJson : ""}`}
                      />
                      {!isMetadataJsonValid && (
                        <span className={styles.fieldErrorText}>Invalid JSON formatting. Please correct before submitting.</span>
                      )}
                    </div>

                    {/* Form Actions */}
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
                          {loading ? "Saving..." : "Save Workflow"}
                        </button>
                      </div>
                    </div>
                  </div>
                )}
              </WizardShell>
            </form>
          )}

          {activeTab === "relationships" && (
            <RelationshipViewer entityType="WORKFLOW" entityId={workflowId!} />
          )}

          {activeTab === "audit" && (
            <AuditTrailViewer entityType="WORKFLOW" entityId={workflowId!} />
          )}
        </div>
      </div>
      
      {isEditMode && (
        <ConfirmDeleteModal
          isOpen={isDeleteModalOpen}
          onClose={() => setIsDeleteModalOpen(false)}
          onConfirm={handleDelete}
          entityName={formData.workflow_name || formData.workflow_code || 'Workflow'}
          entityType="Workflow"
          isDeleting={isDeleting}
        />
      )}
    </Modal>
  );
};

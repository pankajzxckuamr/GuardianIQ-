/* src/components/registry/ToolFormModal.tsx */

import React, { useEffect, useState } from "react";
import { Modal } from "../common/Modal";
import { FieldInfo } from "../common/FieldInfo";
import { useToast } from "../../hooks/useToast";
import * as registryService from "../../services/registry/registryService";
import { EntityStatus } from "../../services/registry/registryTypes";
import { RelationshipViewer } from "./RelationshipViewer";
import { AuditTrailViewer } from "./AuditTrailViewer";
import { ConfirmDeleteModal } from "../common/ConfirmDeleteModal";
import WizardShell from "../common/WizardShell";
import { ObjectRelationshipPanel } from "./ObjectRelationshipPanel";
import { ResponsibilityPanel } from "./ResponsibilityPanel";
import styles from "./ToolFormModal.module.css";



interface ToolFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  toolId?: string | null;
  onSuccess: () => void;
  defaultUserId?: string | null;
}

export const ToolFormModal: React.FC<ToolFormModalProps> = ({
  isOpen,
  onClose,
  toolId,
  onSuccess,
  defaultUserId
}) => {
  const { showToast } = useToast();
  const [activeTab, setActiveTab] = useState<"details" | "relationships" | "audit">("details");
  const [currentWizardStep, setCurrentWizardStep] = useState(0);

  // Lookups data
  const [users, setUsers] = useState<{ id: string; full_name: string; email: string }[]>([]);

  // Form State
  const [formData, setFormData] = useState({
    tool_code: "",
    tool_name: "",
    tool_category: "",
    access_mode: "",
    sensitivity_level: "",
    allowed_operations_json: "",
    endpoint_reference: "",
    owner_user_id: "",
    status: EntityStatus.DRAFT,
    metadata_json: ""
  });

  const [loading, setLoading] = useState(false);
  const [isMetadataJsonValid, setIsMetadataJsonValid] = useState(true);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [generalError, setGeneralError] = useState<string | null>(null);
  const [loadingLookups, setLoadingLookups] = useState(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  const isEditMode = !!toolId;

  const wizardSteps = [
    { label: "Category & details" },
    { label: "Access & operations" },
    { label: "Ownership & tags" }
  ];

  const validateAndAdvance = (targetStep: number) => {
    if (isEditMode) {
      setCurrentWizardStep(targetStep);
      return;
    }
    
    // In create (strict) mode, validate before advancing
    if (targetStep > currentWizardStep) {
      if (currentWizardStep === 0) {
        if (!formData.tool_code || !formData.tool_name || !formData.tool_category) {
          showToast("Please fill in all required fields for Category & details", "error");
          return;
        }
      }
      if (currentWizardStep === 1) {
        if (!formData.access_mode || !formData.sensitivity_level) {
          showToast("Please fill in all required fields for Access & operations", "error");
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
        tool_code: "",
        tool_name: "",
        tool_category: "",
        access_mode: "",
        sensitivity_level: "",
        allowed_operations_json: "",
        endpoint_reference: "",
        owner_user_id: "",
        status: EntityStatus.DRAFT,
        metadata_json: ""
      });
      setFieldErrors({});
      setGeneralError(null);
      setActiveTab("details");
      setCurrentWizardStep(0);
    }
  }, [isOpen]);

  // Load users lookup
  useEffect(() => {
    async function loadLookups() {
      setLoadingLookups(true);
      try {
        const usersRes = await registryService.getUsersLookup();
        if (usersRes.data) setUsers(usersRes.data);
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

  // Load Tool data in edit mode
  useEffect(() => {
    async function loadTool() {
      if (!toolId) return;
      setLoading(true);
      setGeneralError(null);
      try {
        const res = await registryService.getTool(toolId);
        if (res.data) {
          const t = res.data;
          setFormData({
            tool_code: t.tool_code || (t as any).code || "",
            tool_name: t.tool_name || "",
            tool_category: t.tool_category || "",
            access_mode: t.access_mode || "",
            sensitivity_level: t.sensitivity_level || "",
            allowed_operations_json: t.allowed_operations_json
              ? Array.isArray(t.allowed_operations_json)
                ? t.allowed_operations_json.join(", ")
                : String(t.allowed_operations_json)
              : "",
            endpoint_reference: t.endpoint_reference || "",
            owner_user_id: t.owner_user_id || "",
            status: t.status || EntityStatus.DRAFT,
            metadata_json: t.metadata_json
              ? typeof t.metadata_json === "string"
                ? t.metadata_json
                : JSON.stringify(t.metadata_json, null, 2)
              : ""
          });
        }
      } catch (err: any) {
        setGeneralError(err.message || "Failed to load tool data.");
      } finally {
        setLoading(false);
      }
    }

    if (isOpen) {
      if (toolId) {
        loadTool();
        setActiveTab("details");
        setCurrentWizardStep(0);
      } else {
        // Reset form for create mode
        setFormData({
          tool_code: "",
          tool_name: "",
          tool_category: "",
          access_mode: "",
          sensitivity_level: "",
          allowed_operations_json: "",
          endpoint_reference: "",
          owner_user_id: defaultUserId || "",
          status: EntityStatus.DRAFT,
          metadata_json: ""
        });
        setFieldErrors({});
        setGeneralError(null);
        setActiveTab("details");
        setCurrentWizardStep(0);
      }
    }
  }, [isOpen, toolId, defaultUserId]);

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
          const fullField = part.substring(0, colonIndex).trim(); // "body.tool_code"
          const msg = part.substring(colonIndex + 1).trim(); // "field required"
          let fieldName = fullField.replace("body.", "").trim();
          
          if (fieldName === "code") fieldName = "tool_code";
          
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
          
          if (fieldName === "code") fieldName = "tool_code";
          
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

    // Parse operations array from comma-separated string
    const opsArray = formData.allowed_operations_json
      .split(",")
      .map((op) => op.trim())
      .filter((op) => op !== "");

    const payload = {
      ...formData,
      allowed_operations_json: opsArray,
      metadata_json: formData.metadata_json.trim() ? JSON.parse(formData.metadata_json) : null
    };

    try {
      if (isEditMode && toolId) {
        await registryService.updateTool(toolId, payload);
      } else {
        await registryService.createTool(payload);
      }
      showToast("Tool saved successfully", "success");
      onSuccess();
      onClose();
    } catch (err: any) {
      handleApiError(err);
      showToast("Failed to save tool", "error");
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!toolId) return;
    setIsDeleting(true);
    try {
      await registryService.deleteTool(toolId);
      showToast("Tool deleted successfully", "success");
      setIsDeleteModalOpen(false);
      onSuccess();
      onClose();
    } catch (err: any) {
      showToast(err.message || "Failed to delete tool", "error");
    } finally {
      setIsDeleting(false);
    }
  };

  const showWarning = formData.access_mode === "ADMIN" || formData.access_mode === "EXECUTE";

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={isEditMode ? `Edit Tool: ${formData.tool_name}` : "Register New Tool"}
      hintText={
        <div style={{ display: "flex", flexDirection: "column", gap: "12px", paddingRight: "4px" }}>
          <p style={{ margin: 0 }}>Register external tools, databases, or APIs that AI agents can connect to.</p>
          
          {currentWizardStep === 0 && (
            <div>
              <h4 style={{ color: "#fbbf24", margin: "0 0 4px 0", fontSize: "0.85rem" }}>Category & Details</h4>
              <ul style={{ margin: 0, paddingLeft: "16px" }}>
                <li><strong>Tool Code & Name:</strong> Identifiers for the tool (e.g., <code>JIRA_CONN</code>, <em>Jira API</em>).</li>
                <li><strong>Tool Category:</strong> Select the functional group (e.g., <em>TICKETING</em>, <em>CRM</em>, <em>DATABASE</em>).</li>
              </ul>
            </div>
          )}

          {currentWizardStep === 1 && (
            <div>
              <h4 style={{ color: "#fbbf24", margin: "0 0 4px 0", fontSize: "0.85rem" }}>Access & Operations</h4>
              <ul style={{ margin: 0, paddingLeft: "16px" }}>
                <li><strong>Access Mode:</strong> Privilege level granted (e.g., <em>READ_ONLY</em> vs. <em>ADMIN</em>).</li>
                <li><strong>Sensitivity Level:</strong> Risk profile of the data this tool handles (e.g., <em>HIGH</em>).</li>
                <li><strong>Endpoint Reference:</strong> System locator or internal URL (no secrets).</li>
                <li><strong>Allowed Operations:</strong> Exact actions permitted (e.g., <code>read_records, update_ticket</code>).</li>
              </ul>
            </div>
          )}

          {currentWizardStep === 2 && (
            <div>
              <h4 style={{ color: "#fbbf24", margin: "0 0 4px 0", fontSize: "0.85rem" }}>Ownership & Tags</h4>
              <ul style={{ margin: 0, paddingLeft: "16px" }}>
                <li><strong>Owner User:</strong> The person responsible for the tool connection.</li>
                <li><strong>Metadata JSON:</strong> Store custom tag bindings or extra config.</li>
              </ul>
            </div>
          )}
        </div>
      }
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
              
              {/* Custom privilege mode warning banner */}
              {showWarning && (
                <div className={styles.privilegeWarningBanner}>
                  ⚠️ High-privilege access mode. Ensure governance approval.
                </div>
              )}

              <WizardShell
                steps={wizardSteps}
                currentStep={currentWizardStep}
                onStepClick={validateAndAdvance}
                mode={isEditMode ? "tabbed" : "strict"}
              >
                {/* STEP 1: Category & details */}
                {currentWizardStep === 0 && (
                  <div>
                    <div className={styles.formGrid}>
                      {/* Tool Code */}
                      <div className={styles.formGroup}>
                        <label htmlFor="tool_code" className={styles.label}>
                          Tool Code <span className={styles.required}>*</span>
                          <FieldInfo tooltip="Unique identifier code for this tool." />
                        </label>
                        <input
                          type="text"
                          id="tool_code"
                          name="tool_code"
                          value={formData.tool_code}
                          onChange={handleChange}
                          disabled={isEditMode || loading}
                          className={`${styles.input} ${fieldErrors.tool_code ? styles.inputError : ""}`}
                          required
                        />
                        {fieldErrors.tool_code && (
                          <span className={styles.fieldErrorText}>{fieldErrors.tool_code}</span>
                        )}
                      </div>

                      {/* Tool Name */}
                      <div className={styles.formGroup}>
                        <label htmlFor="tool_name" className={styles.label}>
                          Tool Name <span className={styles.required}>*</span>
                          <FieldInfo tooltip="The common name of this tool or connector." />
                        </label>
                        <input
                          type="text"
                          id="tool_name"
                          name="tool_name"
                          value={formData.tool_name}
                          onChange={handleChange}
                          disabled={loading}
                          className={`${styles.input} ${fieldErrors.tool_name ? styles.inputError : ""}`}
                          required
                        />
                        {fieldErrors.tool_name && (
                          <span className={styles.fieldErrorText}>{fieldErrors.tool_name}</span>
                        )}
                      </div>

                      {/* Tool Category */}
                      <div className={styles.formGroup}>
                        <label htmlFor="tool_category" className={styles.label}>
                          Tool Category <span className={styles.required}>*</span>
                          <FieldInfo tooltip="The functional category or class of this tool." />
                        </label>
                        <select
                          id="tool_category"
                          name="tool_category"
                          value={formData.tool_category}
                          onChange={handleChange}
                          disabled={loading}
                          className={`${styles.select} ${fieldErrors.tool_category ? styles.inputError : ""}`}
                          required
                        >
                          <option value="">-- Select Category --</option>
                          <option value="ERP">ERP</option>
                          <option value="CRM">CRM</option>
                          <option value="EMAIL">EMAIL</option>
                          <option value="TICKETING">TICKETING</option>
                          <option value="DATABASE">DATABASE</option>
                          <option value="LLM">LLM</option>
                          <option value="FILE">FILE</option>
                          <option value="WEBHOOK">WEBHOOK</option>
                        </select>
                        {fieldErrors.tool_category && (
                          <span className={styles.fieldErrorText}>{fieldErrors.tool_category}</span>
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

                {/* STEP 2: Access & operations */}
                {currentWizardStep === 1 && (
                  <div>
                    <div className={styles.formGrid}>
                      {/* Access Mode */}
                      <div className={styles.formGroup}>
                        <label htmlFor="access_mode" className={styles.label}>
                          Access Mode <span className={styles.required}>*</span>
                          <FieldInfo tooltip="The level of access or privilege this tool is granted." />
                        </label>
                        <select
                          id="access_mode"
                          name="access_mode"
                          value={formData.access_mode}
                          onChange={handleChange}
                          disabled={loading}
                          className={`${styles.select} ${fieldErrors.access_mode ? styles.inputError : ""}`}
                          required
                        >
                          <option value="">-- Select Mode --</option>
                          <option value="READ_ONLY">READ_ONLY</option>
                          <option value="WRITE">WRITE</option>
                          <option value="EXECUTE">EXECUTE</option>
                          <option value="ADMIN">ADMIN</option>
                        </select>
                        {fieldErrors.access_mode && (
                          <span className={styles.fieldErrorText}>{fieldErrors.access_mode}</span>
                        )}
                      </div>

                      {/* Sensitivity Level */}
                      <div className={styles.formGroup}>
                        <label htmlFor="sensitivity_level" className={styles.label}>
                          Sensitivity <span className={styles.required}>*</span>
                          <FieldInfo tooltip="The sensitivity of the data this tool processes." />
                        </label>
                        <select
                          id="sensitivity_level"
                          name="sensitivity_level"
                          value={formData.sensitivity_level}
                          onChange={handleChange}
                          disabled={loading}
                          className={`${styles.select} ${fieldErrors.sensitivity_level ? styles.inputError : ""}`}
                          required
                        >
                          <option value="">-- Select Sensitivity --</option>
                          <option value="LOW">LOW</option>
                          <option value="MEDIUM">MEDIUM</option>
                          <option value="HIGH">HIGH</option>
                          <option value="CRITICAL">CRITICAL</option>
                        </select>
                        {fieldErrors.sensitivity_level && (
                          <span className={styles.fieldErrorText}>{fieldErrors.sensitivity_level}</span>
                        )}
                      </div>

                      {/* Endpoint Reference */}
                      <div className={styles.formGroup}>
                        <label htmlFor="endpoint_reference" className={styles.label}>
                          Endpoint Reference <FieldInfo tooltip="A system reference or URL endpoint (no secrets)." />
                        </label>
                        <input
                          type="text"
                          id="endpoint_reference"
                          name="endpoint_reference"
                          value={formData.endpoint_reference}
                          onChange={handleChange}
                          disabled={loading}
                          placeholder="System identifier"
                          className={styles.input}
                        />
                        <span className={styles.fieldHelpText}>System reference only. No passwords or tokens.</span>
                      </div>
                    </div>

                    {/* Allowed Operations (Tag-style input) */}
                    <div className={styles.formGroupFull}>
                      <label htmlFor="allowed_operations_json" className={styles.label}>
                        Allowed Operations <FieldInfo tooltip="Specific operations this tool is allowed to perform." />
                      </label>
                      <input
                        type="text"
                        id="allowed_operations_json"
                        name="allowed_operations_json"
                        value={formData.allowed_operations_json}
                        onChange={handleChange}
                        disabled={loading}
                        placeholder="Enter comma-separated operations (e.g. read_records, execute)..."
                        className={styles.input}
                      />
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

                {/* STEP 3: Ownership & tags */}
                {currentWizardStep === 2 && (
                  <div>
                    <div className={styles.formGrid}>
                      {/* Owner User */}
                      <div className={styles.formGroup}>
                        <label htmlFor="owner_user_id" className={styles.label}>Owner User <FieldInfo tooltip="The user primarily responsible for this tool." /></label>
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

                      {/* Status (Edit only) */}
                      {isEditMode && (
                        <div className={styles.formGroup}>
                          <label htmlFor="status" className={styles.label}>Entity Status <FieldInfo tooltip="The current active status of this tool." /></label>
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
                          {loading ? "Saving..." : "Save Tool"}
                        </button>
                      </div>
                    </div>
                  </div>
                )}
              </WizardShell>
            </form>
          )}

          {activeTab === "relationships" && toolId && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
              <ObjectRelationshipPanel objectType="TOOL" objectId={toolId} />
              <hr style={{ border: 'none', borderTop: '1px solid rgba(255,255,255,0.1)' }} />
              <ResponsibilityPanel objectType="TOOL" objectId={toolId} />
              <hr style={{ border: 'none', borderTop: '1px solid rgba(255,255,255,0.1)' }} />
              <div>
                <h4 style={{ color: '#fff', marginBottom: '1rem' }}>Impact Graph</h4>
                <RelationshipViewer entityType="TOOL" entityId={toolId} />
              </div>
            </div>
          )}

          {activeTab === "audit" && (
            <AuditTrailViewer entityType="TOOL" entityId={toolId!} />
          )}
        </div>
      </div>
      
      {isEditMode && (
        <ConfirmDeleteModal
          isOpen={isDeleteModalOpen}
          onClose={() => setIsDeleteModalOpen(false)}
          onConfirm={handleDelete}
          entityName={formData.tool_name || formData.tool_code || 'Tool'}
          entityType="Tool"
          isDeleting={isDeleting}
        />
      )}
    </Modal>
  );
};

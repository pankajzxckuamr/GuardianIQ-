/* src/components/registry/DataSourceFormModal.tsx */

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
import styles from "./DataSourceFormModal.module.css";



interface DataSourceFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  sourceId?: string | null;
  onSuccess: () => void;
  defaultDepartmentId?: string | null;
  defaultUserId?: string | null;
}

export const DataSourceFormModal: React.FC<DataSourceFormModalProps> = ({
  isOpen,
  onClose,
  sourceId,
  onSuccess,
  defaultDepartmentId,
  defaultUserId
}) => {
  const { showToast } = useToast();
  const [activeTab, setActiveTab] = useState<"details" | "relationships" | "audit">("details");
  const [currentWizardStep, setCurrentWizardStep] = useState(0);

  // Lookups data
  const [users, setUsers] = useState<{ id: string; full_name: string; email: string }[]>([]);
  const [departments, setDepartments] = useState<{ id: string; department_name: string; department_code: string }[]>([]);

  // Form State
  const [formData, setFormData] = useState({
    source_code: "",
    source_name: "",
    source_type: "",
    owner_user_id: "",
    department_id: "",
    classification: "",
    sensitivity_level: "",
    region: "",
    contains_pii: false,
    retention_policy: "",
    connection_reference: "",
    status: EntityStatus.ACTIVE,
    metadata_json: ""
  });

  const [loading, setLoading] = useState(false);
  const [isMetadataJsonValid, setIsMetadataJsonValid] = useState(true);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [generalError, setGeneralError] = useState<string | null>(null);
  const [loadingLookups, setLoadingLookups] = useState(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [testingConnection, setTestingConnection] = useState(false);
  const [connectionTestResult, setConnectionTestResult] = useState<{ success: boolean; message: string } | null>(null);

  const isEditMode = !!sourceId;

  const wizardSteps = [
    { label: "Identity & classification" },
    { label: "Connection properties" }
  ];

  const validateAndAdvance = (targetStep: number) => {
    if (isEditMode) {
      setCurrentWizardStep(targetStep);
      return;
    }
    
    // In create (strict) mode, validate before advancing
    if (targetStep > currentWizardStep) {
      if (currentWizardStep === 0) {
        if (!formData.source_code || !formData.source_name || !formData.source_type || !formData.classification || !formData.sensitivity_level) {
          showToast("Please fill in all required fields for Identity & classification", "error");
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
        source_code: "",
        source_name: "",
        source_type: "",
        owner_user_id: "",
        department_id: "",
        classification: "",
        sensitivity_level: "",
        region: "",
        contains_pii: false,
        retention_policy: "",
        connection_reference: "",
        status: EntityStatus.ACTIVE,
        metadata_json: ""
      });
      setFieldErrors({});
      setGeneralError(null);
      setActiveTab("details");
      setCurrentWizardStep(0);
      setTestingConnection(false);
      setConnectionTestResult(null);
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

  // Load Data Source Data in Edit Mode
  useEffect(() => {
    async function loadDataSource() {
      if (!sourceId) return;
      setLoading(true);
      setGeneralError(null);
      try {
        const res = await registryService.getDataSource(sourceId);
        if (res.data) {
          const ds = res.data;
          setFormData({
            source_code: (ds as any).source_code || "",
            source_name: ds.source_name || "",
            source_type: ds.source_type || "",
            owner_user_id: (ds as any).owner_user_id || "",
            department_id: (ds as any).department_id || "",
            classification: ds.classification || "",
            sensitivity_level: (ds as any).sensitivity_level || ds.sensitivity || "",
            region: (ds as any).region || "",
            contains_pii: !!(ds as any).contains_pii,
            retention_policy: (ds as any).retention_policy || "",
            connection_reference: (ds as any).connection_reference || "",
            status: ds.status || EntityStatus.ACTIVE,
            metadata_json: (ds as any).metadata_json 
              ? typeof (ds as any).metadata_json === "string" 
                ? (ds as any).metadata_json 
                : JSON.stringify((ds as any).metadata_json, null, 2)
              : ""
          });
        }
      } catch (err: any) {
        setGeneralError(err.message || "Failed to load data source data.");
      } finally {
        setLoading(false);
      }
    }

    if (isOpen) {
      if (sourceId) {
        loadDataSource();
        setActiveTab("details");
        setCurrentWizardStep(0);
        // Reset form for create mode
        setFormData({
          source_code: "",
          source_name: "",
          source_type: "",
          owner_user_id: defaultUserId || "",
          department_id: defaultDepartmentId || "",
          classification: "",
          sensitivity_level: "",
          region: "",
          contains_pii: false,
          retention_policy: "",
          connection_reference: "",
          status: EntityStatus.ACTIVE,
          metadata_json: ""
        });
        setFieldErrors({});
        setGeneralError(null);
        setActiveTab("details");
        setCurrentWizardStep(0);
      }
    }
  }, [isOpen, sourceId, defaultDepartmentId, defaultUserId]);

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

    if (name === "connection_reference") {
      setConnectionTestResult(null);
    }

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

    if (message.includes("Validation Error:")) {
      const errorContent = message.substring(message.indexOf("Validation Error:") + 17).trim();
      const parts = errorContent.split(", ");
      parts.forEach((part: string) => {
        const colonIndex = part.indexOf(":");
        if (colonIndex !== -1) {
          const fullField = part.substring(0, colonIndex).trim();
          const msg = part.substring(colonIndex + 1).trim();
          let fieldName = fullField.replace("body.", "").trim();
          
          if (fieldName === "sensitivity") fieldName = "sensitivity_level";
          if (fieldName === "code") fieldName = "source_code";
          
          newFieldErrors[fieldName] = msg;
        }
      });
    }

    if (err.details && Array.isArray(err.details)) {
      err.details.forEach((d: any) => {
        let fieldName = d.field || (d.loc && d.loc[d.loc.length - 1]);
        if (fieldName) {
          fieldName = String(fieldName);
          
          if (fieldName === "sensitivity") fieldName = "sensitivity_level";
          if (fieldName === "code") fieldName = "source_code";
          
          newFieldErrors[fieldName] = d.message || d.msg || "Invalid value";
        }
      });
    }
    setFieldErrors(newFieldErrors);
  };

  const handleTestConnection = async () => {
    if (!formData.connection_reference || !formData.connection_reference.trim()) return;
    setTestingConnection(true);
    setConnectionTestResult(null);
    try {
      const res = await registryService.testDataSourceConnection(formData.connection_reference);
      if (res.data) {
        setConnectionTestResult({
          success: res.data.success,
          message: res.data.message
        });
      } else {
        setConnectionTestResult({
          success: false,
          message: res.message || "Failed to receive response from connection tester."
        });
      }
    } catch (err: any) {
      setConnectionTestResult({
        success: false,
        message: err.message || "An error occurred while testing connection."
      });
    } finally {
      setTestingConnection(false);
    }
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
      owner_user_id: formData.owner_user_id || null,
      department_id: formData.department_id || null,
      metadata_json: formData.metadata_json.trim() ? JSON.parse(formData.metadata_json) : null
    };

    try {
      if (isEditMode && sourceId) {
        await registryService.updateDataSource(sourceId, payload);
      } else {
        await registryService.createDataSource(payload);
      }
      showToast("Data Source saved successfully", "success");
      onSuccess();
      onClose();
    } catch (err: any) {
      handleApiError(err);
      showToast("Failed to save data source", "error");
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!sourceId) return;
    setIsDeleting(true);
    try {
      await registryService.deleteDataSource(sourceId);
      showToast("Data Source deleted successfully", "success");
      setIsDeleteModalOpen(false);
      onSuccess();
      onClose();
    } catch (err: any) {
      showToast(err.message || "Failed to delete data source", "error");
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={isEditMode ? `Edit Data Source: ${formData.source_name}` : "Register New Data Source"}
      hintText={
        <div style={{ display: "flex", flexDirection: "column", gap: "12px", paddingRight: "4px" }}>
          <p style={{ margin: 0 }}>Configure external data connections and integrations to register them securely.</p>
          
          {currentWizardStep === 0 && (
            <div>
              <h4 style={{ color: "#fbbf24", margin: "0 0 4px 0", fontSize: "0.85rem" }}>Identity & Classification</h4>
              <ul style={{ margin: 0, paddingLeft: "16px" }}>
                <li><strong>Source Code & Name:</strong> Identifier and common name (e.g., <code>CRM_PROD</code>, <em>Sales CRM</em>).</li>
                <li><strong>Source Type:</strong> Format or platform (e.g., <em>DATABASE</em>, <em>API</em>).</li>
                <li><strong>Classification & Sensitivity:</strong> Data classification (e.g., <em>CONFIDENTIAL</em>) and sensitivity tier (e.g., <em>HIGH</em>).</li>
                <li><strong>Department & Region:</strong> Owning department and geographic location (e.g., <em>us-east-1</em>).</li>
              </ul>
            </div>
          )}

          {currentWizardStep === 1 && (
            <div>
              <h4 style={{ color: "#fbbf24", margin: "0 0 4px 0", fontSize: "0.85rem" }}>Connection Properties</h4>
              <ul style={{ margin: 0, paddingLeft: "16px" }}>
                <li><strong>Connection Reference:</strong> Technical locator (e.g., <code>postgres://db.local:5432</code>). Do not include secrets!</li>
                <li><strong>Technical Owner:</strong> The user responsible for this connection.</li>
                <li><strong>Retention Policy:</strong> Data lifespan (e.g., <em>7 years</em>).</li>
                <li><strong>Contains PII:</strong> Check if this source handles Personally Identifiable Information.</li>
                <li><strong>Metadata JSON:</strong> Store custom structured configuration.</li>
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

        {generalError && <div className={styles.generalAlert}>{generalError}</div>}

        <div className={styles.tabsContent}>
          {activeTab === "details" && (
            <form onSubmit={handleSubmit} className={styles.form}>
              <WizardShell
                steps={wizardSteps}
                currentStep={currentWizardStep}
                onStepClick={validateAndAdvance}
                mode={isEditMode ? "tabbed" : "strict"}
              >
                {/* STEP 1: Identity & classification */}
                {currentWizardStep === 0 && (
                  <div>
                    <div className={styles.formGrid}>
                      {/* Source Code */}
                      <div className={styles.formGroup}>
                        <label htmlFor="source_code" className={styles.label}>
                          Source Code <span className={styles.required}>*</span>
                          <FieldInfo tooltip="Unique identifier for this data source." />
                        </label>
                        <input
                          type="text"
                          id="source_code"
                          name="source_code"
                          value={formData.source_code}
                          onChange={handleChange}
                          disabled={isEditMode || loading}
                          placeholder="e.g. WH_ANALYTICS"
                          className={`${styles.input} ${fieldErrors.source_code ? styles.inputError : ""}`}
                          required
                        />
                        {fieldErrors.source_code && (
                          <span className={styles.fieldErrorText}>{fieldErrors.source_code}</span>
                        )}
                      </div>

                      {/* Source Name */}
                      <div className={styles.formGroup}>
                        <label htmlFor="source_name" className={styles.label}>
                          Source Name <span className={styles.required}>*</span>
                          <FieldInfo tooltip="The common name used for this data source." />
                        </label>
                        <input
                          type="text"
                          id="source_name"
                          name="source_name"
                          value={formData.source_name}
                          onChange={handleChange}
                          disabled={loading}
                          className={`${styles.input} ${fieldErrors.source_name ? styles.inputError : ""}`}
                          required
                        />
                        {fieldErrors.source_name && (
                          <span className={styles.fieldErrorText}>{fieldErrors.source_name}</span>
                        )}
                      </div>

                      {/* Source Type */}
                      <div className={styles.formGroup}>
                        <label htmlFor="source_type" className={styles.label}>
                          Source Type <span className={styles.required}>*</span>
                          <FieldInfo tooltip="The technical category or format of this data source." />
                        </label>
                        <select
                          id="source_type"
                          name="source_type"
                          value={formData.source_type}
                          onChange={handleChange}
                          disabled={loading}
                          className={`${styles.select} ${fieldErrors.source_type ? styles.inputError : ""}`}
                          required
                        >
                          <option value="">-- Select Type --</option>
                          <option value="DATABASE">DATABASE</option>
                          <option value="API">API</option>
                          <option value="FILE">FILE</option>
                          <option value="CRM">CRM</option>
                          <option value="ERP">ERP</option>
                          <option value="DATA_LAKE">DATA LAKE</option>
                          <option value="EMAIL">EMAIL</option>
                          <option value="WEBFORM">WEBFORM</option>
                        </select>
                        {fieldErrors.source_type && (
                          <span className={styles.fieldErrorText}>{fieldErrors.source_type}</span>
                        )}
                      </div>

                      {/* Classification */}
                      <div className={styles.formGroup}>
                        <label htmlFor="classification" className={styles.label}>
                          Classification <span className={styles.required}>*</span>
                          <FieldInfo tooltip="The general data classification policy category." />
                        </label>
                        <select
                          id="classification"
                          name="classification"
                          value={formData.classification}
                          onChange={handleChange}
                          disabled={loading}
                          className={`${styles.select} ${fieldErrors.classification ? styles.inputError : ""}`}
                          required
                        >
                          <option value="">-- Select Classification --</option>
                          <option value="PUBLIC">🟢 PUBLIC</option>
                          <option value="INTERNAL">🔵 INTERNAL</option>
                          <option value="CONFIDENTIAL">🟡 CONFIDENTIAL</option>
                          <option value="RESTRICTED">🔴 RESTRICTED</option>
                        </select>
                        {fieldErrors.classification && (
                          <span className={styles.fieldErrorText}>{fieldErrors.classification}</span>
                        )}
                      </div>

                      {/* Sensitivity Level */}
                      <div className={styles.formGroup}>
                        <label htmlFor="sensitivity_level" className={styles.label}>
                          Sensitivity Level <span className={styles.required}>*</span>
                          <FieldInfo tooltip="The assessed sensitivity level of the data contained." />
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

                      {/* Department */}
                      <div className={styles.formGroup}>
                        <label htmlFor="department_id" className={styles.label}>Department <FieldInfo tooltip="The department that owns or manages this data source." /></label>
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

                      {/* Region */}
                      <div className={styles.formGroup}>
                        <label htmlFor="region" className={styles.label}>Region <FieldInfo tooltip="The geographic or cloud region where this data source resides." /></label>
                        <input
                          type="text"
                          id="region"
                          name="region"
                          value={formData.region}
                          onChange={handleChange}
                          disabled={loading}
                          placeholder="e.g. us-east-1, eu-west-1"
                          className={styles.input}
                        />
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

                {/* STEP 2: Connection properties */}
                {currentWizardStep === 1 && (
                  <div>
                    <div className={styles.formGroupFull}>
                      <label htmlFor="connection_reference" className={styles.label}>Connection Reference <FieldInfo tooltip="A technical reference string for connecting to this source (no secrets)." /></label>
                      <div className={styles.connectionInputGroup}>
                        <input
                          type="text"
                          id="connection_reference"
                          name="connection_reference"
                          value={formData.connection_reference}
                          onChange={handleChange}
                          disabled={loading || testingConnection}
                          placeholder="e.g. postgres://db.local:5432/analytics"
                          className={styles.input}
                        />
                        <button
                          type="button"
                          onClick={handleTestConnection}
                          disabled={loading || testingConnection || !formData.connection_reference.trim()}
                          className={styles.testConnectionBtn}
                        >
                          {testingConnection ? "Testing..." : "Test Connection"}
                        </button>
                      </div>
                      <span className={styles.helperText}>
                        System reference only — no tokens or passwords
                      </span>
                      {connectionTestResult && (
                        <div className={`${styles.testResultAlert} ${connectionTestResult.success ? styles.testSuccessAlert : styles.testErrorAlert}`}>
                          {connectionTestResult.success ? "✅ " : "❌ "}
                          {connectionTestResult.message}
                        </div>
                      )}
                    </div>

                    <div className={styles.formGrid}>
                      {/* Technical Owner */}
                      <div className={styles.formGroup}>
                        <label htmlFor="owner_user_id" className={styles.label}>Technical Owner <FieldInfo tooltip="The user acting as the technical owner of this data source." /></label>
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

                      {/* Retention Policy */}
                      <div className={styles.formGroup}>
                        <label htmlFor="retention_policy" className={styles.label}>Retention Policy <FieldInfo tooltip="The policy defining how long data is kept in this source." /></label>
                        <input
                          type="text"
                          id="retention_policy"
                          name="retention_policy"
                          value={formData.retention_policy}
                          onChange={handleChange}
                          disabled={loading}
                          placeholder="e.g. 7 years, indefinite"
                          className={styles.input}
                        />
                      </div>
                      
                      {/* Status (Edit mode only) */}
                      {isEditMode && (
                        <div className={styles.formGroup}>
                          <label htmlFor="status" className={styles.label}>Entity Status <FieldInfo tooltip="The current lifecycle status of the data source." /></label>
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

                    {/* Contains PII Toggle & Warning */}
                    <div className={styles.formGroupFull} style={{ marginTop: '1rem', marginBottom: '1rem' }}>
                      <label className={styles.checkboxLabel}>
                        <input
                          type="checkbox"
                          name="contains_pii"
                          checked={formData.contains_pii}
                          onChange={handleChange}
                          disabled={loading}
                          className={styles.checkbox}
                        />
                        <span className={styles.checkboxText}>This Data Source contains PII (Personally Identifiable Information)</span>
                      </label>

                      {formData.contains_pii && (
                        <div className={styles.piiWarning}>
                          ⚠️ Contains PII. Ensure DPA compliance.
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

                    {/* Actions */}
                    <div className={styles.formActions} style={{ marginTop: '1.5rem' }}>
                      <button type="button" onClick={() => setCurrentWizardStep(0)} className={styles.cancelBtn}>
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
                          {loading ? "Saving..." : "Save Data Source"}
                        </button>
                      </div>
                    </div>
                  </div>
                )}
              </WizardShell>
            </form>
          )}

          {activeTab === "relationships" && sourceId && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
              <ObjectRelationshipPanel objectType="DATA_SOURCE" objectId={sourceId} />
              <hr style={{ border: 'none', borderTop: '1px solid rgba(255,255,255,0.1)' }} />
              <ResponsibilityPanel objectType="DATA_SOURCE" objectId={sourceId} />
              <hr style={{ border: 'none', borderTop: '1px solid rgba(255,255,255,0.1)' }} />
              <div>
                <h4 style={{ color: '#fff', marginBottom: '1rem' }}>Impact Graph</h4>
                <RelationshipViewer entityType="DATA_SOURCE" entityId={sourceId} />
              </div>
            </div>
          )}

          {activeTab === "audit" && (
            <AuditTrailViewer entityType="DATA_SOURCE" entityId={sourceId!} />
          )}
        </div>
      </div>
      
      {isEditMode && (
        <ConfirmDeleteModal
          isOpen={isDeleteModalOpen}
          onClose={() => setIsDeleteModalOpen(false)}
          onConfirm={handleDelete}
          entityName={formData.source_name || formData.source_code || 'Data Source'}
          entityType="Data Source"
          isDeleting={isDeleting}
        />
      )}
    </Modal>
  );
};

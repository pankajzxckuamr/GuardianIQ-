/* src/components/registry/DepartmentFormModal.tsx */

import React, { useEffect, useState } from "react";
import { Modal } from "../common/Modal";
import { FieldInfo } from "../common/FieldInfo";
import { useToast } from "../../hooks/useToast";
import * as registryService from "../../services/registry/registryService";
import { EntityStatus } from "../../services/registry/registryTypes";
import { RelationshipViewer } from "./RelationshipViewer";
import { AuditTrailViewer } from "./AuditTrailViewer";
import { ConfirmDeleteModal } from "../common/ConfirmDeleteModal";
import styles from "./DepartmentFormModal.module.css";



interface DepartmentFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  deptId?: string | null;
  onSuccess: () => void;
}

export const DepartmentFormModal: React.FC<DepartmentFormModalProps> = ({
  isOpen,
  onClose,
  deptId,
  onSuccess
}) => {
  const { showToast } = useToast();
  const [activeTab, setActiveTab] = useState<"details" | "relationships" | "audit">("details");
  
  // Lookups data
  const [users, setUsers] = useState<{ id: string; full_name: string; email: string }[]>([]);
  const [departments, setDepartments] = useState<{ id: string; department_name: string; department_code: string }[]>([]);

  // Form State
  const [formData, setFormData] = useState({
    department_code: "",
    department_name: "",
    parent_department_id: "",
    business_owner_user_id: "",
    escalation_owner_user_id: "",
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

  const isEditMode = !!deptId;

  // Reset form when modal opens or closes
  useEffect(() => {
    if (!isOpen) {
      setFormData({
        department_code: "",
        department_name: "",
        parent_department_id: "",
        business_owner_user_id: "",
        escalation_owner_user_id: "",
        status: EntityStatus.ACTIVE,
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

  // Load Department Data in Edit Mode
  useEffect(() => {
    async function loadDepartment() {
      if (!deptId) return;
      setLoading(true);
      setGeneralError(null);
      try {
        const res = await registryService.getDepartment(deptId);
        if (res.data) {
          const d = res.data;
          setFormData({
            department_code: d.department_code || "",
            department_name: d.department_name || "",
            parent_department_id: (d as any).parent_department_id || "",
            business_owner_user_id: (d as any).business_owner_user_id || "",
            escalation_owner_user_id: (d as any).escalation_owner_user_id || "",
            status: d.status || EntityStatus.ACTIVE,
            metadata_json: (d as any).metadata_json 
              ? typeof (d as any).metadata_json === "string" 
                ? (d as any).metadata_json 
                : JSON.stringify((d as any).metadata_json, null, 2)
              : ""
          });
        }
      } catch (err: any) {
        setGeneralError(err.message || "Failed to load department data.");
      } finally {
        setLoading(false);
      }
    }

    if (isOpen) {
      if (deptId) {
        loadDepartment();
        setActiveTab("details");
      } else {
        // Reset form for create mode
        setFormData({
          department_code: "",
          department_name: "",
          parent_department_id: "",
          business_owner_user_id: "",
          escalation_owner_user_id: "",
          status: EntityStatus.ACTIVE,
          metadata_json: ""
        });
        setFieldErrors({});
        setGeneralError(null);
        setActiveTab("details");
      }
    }
  }, [isOpen, deptId]);

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

    if (message.includes("Validation Error:")) {
      const errorContent = message.substring(message.indexOf("Validation Error:") + 17).trim();
      const parts = errorContent.split(", ");
      parts.forEach((part: string) => {
        const colonIndex = part.indexOf(":");
        if (colonIndex !== -1) {
          const fullField = part.substring(0, colonIndex).trim();
          const msg = part.substring(colonIndex + 1).trim();
          let fieldName = fullField.replace("body.", "").trim();
          
          if (fieldName === "code") fieldName = "department_code";
          
          newFieldErrors[fieldName] = msg;
        }
      });
    }

    if (err.details && Array.isArray(err.details)) {
      err.details.forEach((d: any) => {
        let fieldName = d.field || (d.loc && d.loc[d.loc.length - 1]);
        if (fieldName) {
          fieldName = String(fieldName);
          
          if (fieldName === "code") fieldName = "department_code";
          
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
      parent_department_id: formData.parent_department_id || null,
      business_owner_user_id: formData.business_owner_user_id || null,
      escalation_owner_user_id: formData.escalation_owner_user_id || null,
      metadata_json: formData.metadata_json.trim() ? JSON.parse(formData.metadata_json) : null
    };

    try {
      if (isEditMode && deptId) {
        await registryService.updateDepartment(deptId, payload);
      } else {
        await registryService.createDepartment(payload);
      }
      showToast("Department saved successfully", "success");
      onSuccess();
      onClose();
    } catch (err: any) {
      handleApiError(err);
      showToast("Failed to save department", "error");
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!deptId) return;
    setIsDeleting(true);
    try {
      await registryService.deleteDepartment(deptId);
      showToast("Department deleted successfully", "success");
      setIsDeleteModalOpen(false);
      onSuccess();
      onClose();
    } catch (err: any) {
      showToast(err.message || "Failed to delete department", "error");
    } finally {
      setIsDeleting(false);
    }
  };

  // Exclude self from parent lookup to prevent circular loops
  const filteredDepartments = departments.filter((d) => !isEditMode || d.id !== deptId);

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={isEditMode ? `Edit Department: ${formData.department_name}` : "Register New Department"}
      hintText={
        <div style={{ display: "flex", flexDirection: "column", gap: "12px", paddingRight: "4px" }}>
          <p style={{ margin: 0 }}>Organize your enterprise structure by defining departments and assigning leaders.</p>
          <div>
            <h4 style={{ color: "#fbbf24", margin: "0 0 4px 0", fontSize: "0.85rem" }}>Department Details</h4>
            <ul style={{ margin: 0, paddingLeft: "16px" }}>
              <li><strong>Department Code & Name:</strong> Identifiers for the department (e.g., <code>LEGAL_01</code>, <em>Legal & Compliance</em>).</li>
              <li><strong>Parent Department:</strong> Link to a parent for hierarchical org structures.</li>
            </ul>
          </div>
          <div>
            <h4 style={{ color: "#fbbf24", margin: "0 0 4px 0", fontSize: "0.85rem" }}>Leadership & Tags</h4>
            <ul style={{ margin: 0, paddingLeft: "16px" }}>
              <li><strong>Business Owner:</strong> Primary leader/owner of this department's assets.</li>
              <li><strong>Escalation Owner:</strong> Contact person for critical escalations.</li>
              <li><strong>Metadata JSON:</strong> Additional structured fields or external IDs.</li>
            </ul>
          </div>
        </div>
      }
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

        {generalError && <div className={styles.generalAlert}>{generalError}</div>}

        <div className={styles.tabsContent}>
          {activeTab === "details" && (
            <form onSubmit={handleSubmit} className={styles.form}>
              <div className={styles.formGrid}>
            {/* Department Code */}
            <div className={styles.formGroup}>
              <label htmlFor="department_code" className={styles.label}>
                Department Code <span className={styles.required}>*</span>
                <FieldInfo tooltip="Unique identifier code for this department." />
              </label>
              <input
                type="text"
                id="department_code"
                name="department_code"
                value={formData.department_code}
                onChange={handleChange}
                disabled={isEditMode || loading}
                placeholder="e.g. MARKETING"
                className={`${styles.input} ${fieldErrors.department_code ? styles.inputError : ""}`}
                required
              />
              {fieldErrors.department_code && (
                <span className={styles.fieldErrorText}>{fieldErrors.department_code}</span>
              )}
            </div>

            {/* Department Name */}
            <div className={styles.formGroup}>
              <label htmlFor="department_name" className={styles.label}>
                Department Name <span className={styles.required}>*</span>
                <FieldInfo tooltip="The common name of this department." />
              </label>
              <input
                type="text"
                id="department_name"
                name="department_name"
                value={formData.department_name}
                onChange={handleChange}
                disabled={loading}
                className={`${styles.input} ${fieldErrors.department_name ? styles.inputError : ""}`}
                required
              />
              {fieldErrors.department_name && (
                <span className={styles.fieldErrorText}>{fieldErrors.department_name}</span>
              )}
            </div>

             {/* Parent Department */}
            <div className={styles.formGroup}>
              <label htmlFor="parent_department_id" className={styles.label}>Parent Department <FieldInfo tooltip="The parent department in the organizational hierarchy." /></label>
              <select
                id="parent_department_id"
                name="parent_department_id"
                value={formData.parent_department_id}
                onChange={handleChange}
                disabled={loading || loadingLookups}
                className={styles.select}
              >
                {loadingLookups ? (
                  <option value="">Loading departments...</option>
                ) : (
                  <>
                    <option value="">-- No Parent (Root) --</option>
                    {filteredDepartments.map((d) => (
                      <option key={d.id} value={d.id}>
                        {d.department_name} ({d.department_code})
                      </option>
                    ))}
                  </>
                )}
              </select>
            </div>

            {/* Business Owner */}
            <div className={styles.formGroup}>
              <label htmlFor="business_owner_user_id" className={styles.label}>Business Owner <FieldInfo tooltip="The primary business owner or leader of this department." /></label>
              <select
                id="business_owner_user_id"
                name="business_owner_user_id"
                value={formData.business_owner_user_id}
                onChange={handleChange}
                disabled={loading || loadingLookups}
                className={styles.select}
              >
                {loadingLookups ? (
                  <option value="">Loading owners...</option>
                ) : (
                  <>
                    <option value="">-- Select Business Owner --</option>
                    {users.map((u) => (
                      <option key={u.id} value={u.id}>
                        {u.full_name} ({u.email})
                      </option>
                    ))}
                  </>
                )}
              </select>
            </div>

            {/* Escalation Owner */}
            <div className={styles.formGroup}>
              <label htmlFor="escalation_owner_user_id" className={styles.label}>Escalation Owner <FieldInfo tooltip="The user to contact for critical escalations regarding this department's assets." /></label>
              <select
                id="escalation_owner_user_id"
                name="escalation_owner_user_id"
                value={formData.escalation_owner_user_id}
                onChange={handleChange}
                disabled={loading || loadingLookups}
                className={styles.select}
              >
                {loadingLookups ? (
                  <option value="">Loading owners...</option>
                ) : (
                  <>
                    <option value="">-- Select Escalation Owner --</option>
                    {users.map((u) => (
                      <option key={u.id} value={u.id}>
                        {u.full_name} ({u.email})
                      </option>
                    ))}
                  </>
                )}
              </select>
            </div>

            {/* Status (Edit mode only) */}
            {isEditMode && (
              <div className={styles.formGroup}>
                <label htmlFor="status" className={styles.label}>Entity Status <FieldInfo tooltip="The current active status of this department." /></label>
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

          {/* Actions */}
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
                {loading ? "Saving..." : "Save Department"}
              </button>
            </div>
          </div>
            </form>
          )}

          {activeTab === "relationships" && (
            <RelationshipViewer entityType="DEPARTMENT" entityId={deptId!} />
          )}

          {activeTab === "audit" && (
            <AuditTrailViewer entityType="DEPARTMENT" entityId={deptId!} />
          )}
        </div>
      </div>
      
      {isEditMode && (
        <ConfirmDeleteModal
          isOpen={isDeleteModalOpen}
          onClose={() => setIsDeleteModalOpen(false)}
          onConfirm={handleDelete}
          entityName={formData.department_name || formData.department_code || 'Department'}
          entityType="Department"
          isDeleting={isDeleting}
        />
      )}
    </Modal>
  );
};

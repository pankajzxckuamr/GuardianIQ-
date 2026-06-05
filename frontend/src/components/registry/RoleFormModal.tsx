/* src/components/registry/RoleFormModal.tsx */

import React, { useEffect, useState } from "react";
import { Modal } from "../common/Modal";
import { useToast } from "../../hooks/useToast";
import * as registryService from "../../services/registry/registryService";
import { EntityStatus } from "../../services/registry/registryTypes";
import { ConfirmDeleteModal } from "../common/ConfirmDeleteModal";
import styles from "./RoleFormModal.module.css";

const FieldInfo: React.FC<{ tooltip: string }> = ({ tooltip }) => (
  <span title={tooltip} style={{ cursor: "help", marginLeft: "4px", color: "#888", fontSize: "0.85em", fontWeight: "normal" }}>(?)</span>
);

interface RoleFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  roleId?: string | null;
  onSuccess: () => void;
}

export const RoleFormModal: React.FC<RoleFormModalProps> = ({
  isOpen,
  onClose,
  roleId,
  onSuccess
}) => {
  const { showToast } = useToast();

  // Form State
  const [formData, setFormData] = useState({
    role_code: "",
    role_name: "",
    role_type: "",
    permissions_json: "{}",
    status: EntityStatus.ACTIVE
  });

  const [loading, setLoading] = useState(false);
  const [isPermissionsJsonValid, setIsPermissionsJsonValid] = useState(true);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [generalError, setGeneralError] = useState<string | null>(null);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  const isEditMode = !!roleId;

  // Reset form when modal opens or closes
  useEffect(() => {
    if (!isOpen) {
      setFormData({
        role_code: "",
        role_name: "",
        role_type: "",
        permissions_json: "{}",
        status: EntityStatus.ACTIVE
      });
      setFieldErrors({});
      setGeneralError(null);
    }
  }, [isOpen]);

  // Load Role Data in Edit Mode
  useEffect(() => {
    async function loadRole() {
      if (!roleId) return;
      setLoading(true);
      setGeneralError(null);
      try {
        const res = await registryService.getRole(roleId);
        if (res.data) {
          const r = res.data;
          setFormData({
            role_code: r.role_code || "",
            role_name: r.role_name || "",
            role_type: (r as any).role_type || "",
            permissions_json: (r as any).permissions_json 
              ? typeof (r as any).permissions_json === "string" 
                ? (r as any).permissions_json 
                : JSON.stringify((r as any).permissions_json, null, 2)
              : "{}",
            status: r.status || EntityStatus.ACTIVE
          });
        }
      } catch (err: any) {
        setGeneralError(err.message || "Failed to load role data.");
      } finally {
        setLoading(false);
      }
    }

    if (isOpen) {
      if (roleId) {
        loadRole();
      } else {
        // Reset form for create mode
        setFormData({
          role_code: "",
          role_name: "",
          role_type: "",
          permissions_json: "{}",
          status: EntityStatus.ACTIVE
        });
        setFieldErrors({});
        setGeneralError(null);
      }
    }
  }, [isOpen, roleId]);

  // Validate permissions_json
  useEffect(() => {
    if (!formData.permissions_json.trim()) {
      setIsPermissionsJsonValid(true);
      return;
    }
    try {
      JSON.parse(formData.permissions_json);
      setIsPermissionsJsonValid(true);
    } catch {
      setIsPermissionsJsonValid(false);
    }
  }, [formData.permissions_json]);

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
          
          if (fieldName === "code") fieldName = "role_code";
          
          newFieldErrors[fieldName] = msg;
        }
      });
    }

    if (err.details && Array.isArray(err.details)) {
      err.details.forEach((d: any) => {
        let fieldName = d.field || (d.loc && d.loc[d.loc.length - 1]);
        if (fieldName) {
          fieldName = String(fieldName);
          
          if (fieldName === "code") fieldName = "role_code";
          
          newFieldErrors[fieldName] = d.message || d.msg || "Invalid value";
        }
      });
    }
    setFieldErrors(newFieldErrors);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isPermissionsJsonValid) {
      showToast("Permissions must be a valid JSON object", "error");
      return;
    }

    setLoading(true);
    setGeneralError(null);
    setFieldErrors({});

    const payload = {
      ...formData,
      permissions_json: formData.permissions_json.trim() ? JSON.parse(formData.permissions_json) : {}
    };

    try {
      if (isEditMode && roleId) {
        await registryService.updateRole(roleId, payload);
      } else {
        await registryService.createRole(payload);
      }
      showToast("Role saved successfully", "success");
      onSuccess();
      onClose();
    } catch (err: any) {
      handleApiError(err);
      showToast("Failed to save role", "error");
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!roleId) return;
    setIsDeleting(true);
    try {
      await registryService.deleteRole(roleId);
      showToast("Role deleted successfully", "success");
      setIsDeleteModalOpen(false);
      onSuccess();
      onClose();
    } catch (err: any) {
      showToast(err.message || "Failed to delete role", "error");
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={isEditMode ? `Edit Role: ${formData.role_name}` : "Register New Role"}
      size="xl"
    >
      <div className={styles.container}>
        {generalError && <div className={styles.generalAlert}>{generalError}</div>}

        <form onSubmit={handleSubmit} className={styles.form}>
          <div className={styles.formGrid}>
            {/* Role Code */}
            <div className={styles.formGroup}>
              <label htmlFor="role_code" className={styles.label}>
                Role Code <span className={styles.required}>*</span>
                <FieldInfo tooltip="Unique identifier code for this role." />
              </label>
              <input
                type="text"
                id="role_code"
                name="role_code"
                value={formData.role_code}
                onChange={handleChange}
                disabled={isEditMode || loading}
                placeholder="e.g. AUDITOR"
                className={`${styles.input} ${fieldErrors.role_code ? styles.inputError : ""}`}
                required
              />
              {fieldErrors.role_code && (
                <span className={styles.fieldErrorText}>{fieldErrors.role_code}</span>
              )}
            </div>

            {/* Role Name */}
            <div className={styles.formGroup}>
              <label htmlFor="role_name" className={styles.label}>
                Role Name <span className={styles.required}>*</span>
                <FieldInfo tooltip="The common name of this governance role." />
              </label>
              <input
                type="text"
                id="role_name"
                name="role_name"
                value={formData.role_name}
                onChange={handleChange}
                disabled={loading}
                className={`${styles.input} ${fieldErrors.role_name ? styles.inputError : ""}`}
                required
              />
              {fieldErrors.role_name && (
                <span className={styles.fieldErrorText}>{fieldErrors.role_name}</span>
              )}
            </div>

            {/* Role Type */}
            <div className={styles.formGroup}>
              <label htmlFor="role_type" className={styles.label}>
                Role Type <span className={styles.required}>*</span>
                <FieldInfo tooltip="The functional category of this role." />
              </label>
              <select
                id="role_type"
                name="role_type"
                value={formData.role_type}
                onChange={handleChange}
                disabled={loading}
                className={`${styles.select} ${fieldErrors.role_type ? styles.inputError : ""}`}
                required
              >
                <option value="">-- Select Type --</option>
                <option value="SYSTEM">SYSTEM</option>
                <option value="BUSINESS">BUSINESS</option>
                <option value="GOVERNANCE">GOVERNANCE</option>
              </select>
              {fieldErrors.role_type && (
                <span className={styles.fieldErrorText}>{fieldErrors.role_type}</span>
              )}
            </div>

            {/* Status (Edit mode only) */}
            {isEditMode && (
              <div className={styles.formGroup}>
                <label htmlFor="status" className={styles.label}>Entity Status <FieldInfo tooltip="The current active status of this role." /></label>
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

          {/* Permissions JSON Textarea */}
          <div className={styles.formGroupFull}>
            <label htmlFor="permissions_json" className={styles.label}>
              Permissions Specifications (JSON) <span className={styles.required}>*</span>
              <FieldInfo tooltip="The detailed JSON configuration mapping permissions to this role." />
            </label>
            <textarea
              id="permissions_json"
              name="permissions_json"
              value={formData.permissions_json}
              onChange={handleChange}
              disabled={loading}
              rows={5}
              className={`${styles.textarea} ${styles.jsonTextarea} ${!isPermissionsJsonValid ? styles.invalidJson : ""}`}
              required
            />
            {!isPermissionsJsonValid && (
              <span className={styles.fieldErrorText}>Invalid JSON formatting. Please verify structure before saving.</span>
            )}
            
            {/* Warning Note Box */}
            <div className={styles.warningNote}>
              ⚠️ Coordinate with SA/TL before editing permissions.
            </div>
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
                disabled={loading || !isPermissionsJsonValid}
                className={styles.submitBtn}
              >
                {loading ? "Saving..." : "Save Role"}
              </button>
            </div>
          </div>
        </form>
      </div>

      {isEditMode && (
        <ConfirmDeleteModal
          isOpen={isDeleteModalOpen}
          onClose={() => setIsDeleteModalOpen(false)}
          onConfirm={handleDelete}
          entityName={formData.role_name || formData.role_code || 'Role'}
          entityType="Role"
          isDeleting={isDeleting}
        />
      )}
    </Modal>
  );
};

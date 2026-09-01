/* src/components/registry/UserFormModal.tsx */

import React, { useEffect, useState } from "react";
import { Modal } from "../common/Modal";
import { FieldInfo } from "../common/FieldInfo";
import { useToast } from "../../hooks/useToast";
import * as registryService from "../../services/registry/registryService";
import { EntityStatus } from "../../services/registry/registryTypes";
import { ConfirmDeleteModal } from "../common/ConfirmDeleteModal";
import styles from "./UserFormModal.module.css";



interface UserFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  userId?: string | null;
  onSuccess: () => void;
  defaultDepartmentId?: string | null;
  defaultRoleId?: string | null;
}

export const UserFormModal: React.FC<UserFormModalProps> = ({
  isOpen,
  onClose,
  userId,
  onSuccess,
  defaultDepartmentId,
  defaultRoleId
}) => {
  const { showToast } = useToast();

  // Lookups data
  const [departments, setDepartments] = useState<{ id: string; department_name: string; department_code: string }[]>([]);
  const [roles, setRoles] = useState<{ id: string; role_name: string; role_code: string }[]>([]);

  // Form State
  const [formData, setFormData] = useState({
    email: "",
    full_name: "",
    department_id: "",
    role_id: "",
    approval_limit_level: "",
    status: EntityStatus.ACTIVE
  });

  const [loading, setLoading] = useState(false);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [generalError, setGeneralError] = useState<string | null>(null);
  const [loadingLookups, setLoadingLookups] = useState(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  const isEditMode = !!userId;

  // Reset form when modal opens or closes
  useEffect(() => {
    if (!isOpen) {
      setFormData({
        email: "",
        full_name: "",
        department_id: "",
        role_id: "",
        approval_limit_level: "",
        status: EntityStatus.ACTIVE
      });
      setFieldErrors({});
      setGeneralError(null);
    }
  }, [isOpen]);

  // Load Lookups on mount
  useEffect(() => {
    async function loadLookups() {
      setLoadingLookups(true);
      try {
        const [deptsRes, rolesRes] = await Promise.all([
          registryService.getDepartmentsLookup(),
          registryService.getRolesLookup()
        ]);
        if (deptsRes.data) setDepartments(deptsRes.data);
        if (rolesRes.data) setRoles(rolesRes.data);
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

  // Load User Data in Edit Mode
  useEffect(() => {
    async function loadUser() {
      if (!userId) return;
      setLoading(true);
      setGeneralError(null);
      try {
        const res = await registryService.getUser(userId);
        if (res.data) {
          const u = res.data;
          setFormData({
            email: u.email || "",
            full_name: u.full_name || "",
            department_id: (u as any).department_id || "",
            role_id: (u as any).role_id || "",
            approval_limit_level: (u as any).approval_limit_level || "",
            status: u.status || EntityStatus.ACTIVE
          });
        }
      } catch (err: any) {
        setGeneralError(err.message || "Failed to load user data.");
      } finally {
        setLoading(false);
      }
    }

    if (isOpen) {
      if (userId) {
        loadUser();
      } else {
        // Reset form for create mode
        setFormData({
          email: "",
          full_name: "",
          department_id: defaultDepartmentId || "",
          role_id: defaultRoleId || "",
          approval_limit_level: "",
          status: EntityStatus.ACTIVE
        });
        setFieldErrors({});
        setGeneralError(null);
      }
    }
  }, [isOpen, userId, defaultDepartmentId, defaultRoleId]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
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
          const fieldName = fullField.replace("body.", "").trim();
          newFieldErrors[fieldName] = msg;
        }
      });
    }

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
    setLoading(true);
    setGeneralError(null);
    setFieldErrors({});

    const payload = {
      ...formData,
      department_id: formData.department_id || null,
      role_id: formData.role_id || null,
      approval_limit_level: formData.approval_limit_level || null
    };

    try {
      if (isEditMode && userId) {
        await registryService.updateUser(userId, payload);
      } else {
        await registryService.createUser(payload);
      }
      showToast("User saved successfully", "success");
      onSuccess();
      onClose();
    } catch (err: any) {
      handleApiError(err);
      showToast("Failed to save user", "error");
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!userId) return;
    setIsDeleting(true);
    try {
      await registryService.deleteUser(userId);
      showToast("User deleted successfully", "success");
      setIsDeleteModalOpen(false);
      onSuccess();
      onClose();
    } catch (err: any) {
      showToast(err.message || "Failed to delete user", "error");
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={isEditMode ? `Edit User: ${formData.full_name}` : "Register New User"}
      hintText={
        <div style={{ display: "flex", flexDirection: "column", gap: "12px", paddingRight: "4px" }}>
          <p style={{ margin: 0 }}>Manage user identities, their associated departments, and access clearances.</p>
          <div>
            <h4 style={{ color: "#fbbf24", margin: "0 0 4px 0", fontSize: "0.85rem" }}>Identity Details</h4>
            <ul style={{ margin: 0, paddingLeft: "16px" }}>
              <li><strong>Email Address & Full Name:</strong> Primary contact and legal/preferred name.</li>
            </ul>
          </div>
          <div>
            <h4 style={{ color: "#fbbf24", margin: "0 0 4px 0", fontSize: "0.85rem" }}>Assignments & Clearances</h4>
            <ul style={{ margin: 0, paddingLeft: "16px" }}>
              <li><strong>Department:</strong> Link the user to their respective department.</li>
              <li><strong>Governance Role:</strong> Assign an RBAC role governing their platform access.</li>
              <li><strong>Approval Limit Clearance:</strong> Financial/Operational bounds (e.g., <em>LEVEL 1 (Up to $10,000)</em>).</li>
              <li><strong>Entity Status:</strong> Toggle whether the user's access is active, suspended, or retired.</li>
            </ul>
          </div>
        </div>
      }
      size="lg"
    >
      <div className={styles.container}>
        {generalError && <div className={styles.generalAlert}>{generalError}</div>}

        <form onSubmit={handleSubmit} className={styles.form}>
          <div className={styles.formGrid}>
            {/* Email Address */}
            <div className={styles.formGroup}>
              <label htmlFor="email" className={styles.label}>
                Email Address <span className={styles.required}>*</span>
                <FieldInfo tooltip="Primary email address for this user." />
              </label>
              <input
                type="email"
                id="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                disabled={isEditMode || loading}
                placeholder="Enter corporate email address..."
                className={`${styles.input} ${fieldErrors.email ? styles.inputError : ""}`}
                required
              />
              {fieldErrors.email && (
                <span className={styles.fieldErrorText}>{fieldErrors.email}</span>
              )}
            </div>

            {/* Full Name */}
            <div className={styles.formGroup}>
              <label htmlFor="full_name" className={styles.label}>
                Full Name <span className={styles.required}>*</span>
                <FieldInfo tooltip="Full legal or preferred name of the user." />
              </label>
              <input
                type="text"
                id="full_name"
                name="full_name"
                value={formData.full_name}
                onChange={handleChange}
                disabled={loading}
                className={`${styles.input} ${fieldErrors.full_name ? styles.inputError : ""}`}
                required
              />
              {fieldErrors.full_name && (
                <span className={styles.fieldErrorText}>{fieldErrors.full_name}</span>
              )}
            </div>

            {/* Department */}
            <div className={styles.formGroup}>
              <label htmlFor="department_id" className={styles.label}>
                Department <span className={styles.required}>*</span>
                <FieldInfo tooltip="The department this user belongs to." />
              </label>
              <select
                id="department_id"
                name="department_id"
                value={formData.department_id}
                onChange={handleChange}
                disabled={loading || loadingLookups}
                className={styles.select}
                required
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

            {/* Role */}
            <div className={styles.formGroup}>
              <label htmlFor="role_id" className={styles.label}>
                Governance Role <span className={styles.required}>*</span>
                <FieldInfo tooltip="The governance role assigned to this user." />
              </label>
              <select
                id="role_id"
                name="role_id"
                value={formData.role_id}
                onChange={handleChange}
                disabled={loading || loadingLookups}
                className={styles.select}
                required
              >
                {loadingLookups ? (
                  <option value="">Loading roles...</option>
                ) : (
                  <>
                    <option value="">-- Select Role --</option>
                    {roles.map((r) => (
                      <option key={r.id} value={r.id}>
                        {r.role_name} ({r.role_code})
                      </option>
                    ))}
                  </>
                )}
              </select>
            </div>

            {/* Approval Limit Level */}
            <div className={styles.formGroup}>
              <label htmlFor="approval_limit_level" className={styles.label}>Approval Limit Clearance <FieldInfo tooltip="The financial or operational approval limit granted to this user." /></label>
              <select
                id="approval_limit_level"
                name="approval_limit_level"
                value={formData.approval_limit_level}
                onChange={handleChange}
                disabled={loading}
                className={styles.select}
              >
                <option value="">-- No Clearance Level --</option>
                <option value="LEVEL_1">LEVEL 1 (Up to $10,000)</option>
                <option value="LEVEL_2">LEVEL 2 (Up to $50,000)</option>
                <option value="LEVEL_3">LEVEL 3 (Up to $250,000)</option>
                <option value="LEVEL_4">LEVEL 4 (Unlimited Clearance)</option>
              </select>
            </div>

            {/* Status (Edit mode only) */}
            {isEditMode && (
              <div className={styles.formGroup}>
                <label htmlFor="status" className={styles.label}>Entity Status <FieldInfo tooltip="The current active status of this user." /></label>
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
                disabled={loading}
                className={styles.submitBtn}
              >
                {loading ? "Saving..." : "Save User"}
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
          entityName={formData.full_name || formData.email || 'User'}
          entityType="User"
          isDeleting={isDeleting}
        />
      )}
    </Modal>
  );
};

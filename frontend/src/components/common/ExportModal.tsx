/* src/components/common/ExportModal.tsx */
import React, { useState } from "react";
import styles from "./ExportModal.module.css";

export interface ExportModalFormData {
  subject_type?: string;
  subject_id?: string;
  correlation_id?: string;
  start_date?: string;
  end_date?: string;
  event_type?: string;
  classification?: string;
  export_format: "JSON" | "CSV";
  reason?: string;
}

export interface ExportModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: ExportModalFormData) => Promise<void>;
}

export const ExportModal: React.FC<ExportModalProps> = ({
  isOpen,
  onClose,
  onSubmit
}) => {
  const [formData, setFormData] = useState<ExportModalFormData>({
    export_format: "JSON",
    classification: "ALL",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>
  ) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await onSubmit(formData);
      onClose();
    } catch (err: any) {
      setError(err?.message || "Failed to submit export request");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.overlay}>
      <div className={styles.modal} role="dialog" aria-modal="true">
        <div className={styles.header}>
          <h2 className={styles.title}>Generate Audit Export Package</h2>
          <button type="button" onClick={onClose} className={styles.closeButton}>
            ✕
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className={styles.body}>
            {error && <div className={styles.errorBanner}>{error}</div>}

            <div className={styles.formGrid}>
              <div className={styles.field}>
                <label className={styles.label}>Subject Entity Type</label>
                <input
                  type="text"
                  name="subject_type"
                  placeholder="e.g. policies, workflows"
                  value={formData.subject_type || ""}
                  onChange={handleChange}
                  className={styles.input}
                />
              </div>

              <div className={styles.field}>
                <label className={styles.label}>Subject Entity ID</label>
                <input
                  type="text"
                  name="subject_id"
                  placeholder="UUID string"
                  value={formData.subject_id || ""}
                  onChange={handleChange}
                  className={styles.input}
                />
              </div>

              <div className={`${styles.field} ${styles.fullWidth}`}>
                <label className={styles.label}>Correlation ID</label>
                <input
                  type="text"
                  name="correlation_id"
                  placeholder="Trace Correlation UUID"
                  value={formData.correlation_id || ""}
                  onChange={handleChange}
                  className={styles.input}
                />
              </div>

              <div className={styles.field}>
                <label className={styles.label}>Start Date</label>
                <input
                  type="datetime-local"
                  name="start_date"
                  value={formData.start_date || ""}
                  onChange={handleChange}
                  className={styles.input}
                />
              </div>

              <div className={styles.field}>
                <label className={styles.label}>End Date</label>
                <input
                  type="datetime-local"
                  name="end_date"
                  value={formData.end_date || ""}
                  onChange={handleChange}
                  className={styles.input}
                />
              </div>

              <div className={styles.field}>
                <label className={styles.label}>Event Type</label>
                <input
                  type="text"
                  name="event_type"
                  placeholder="e.g. WORKFLOW_RUN_STARTED"
                  value={formData.event_type || ""}
                  onChange={handleChange}
                  className={styles.input}
                />
              </div>

              <div className={styles.field}>
                <label className={styles.label}>Classification Level</label>
                <select
                  name="classification"
                  value={formData.classification || "ALL"}
                  onChange={handleChange}
                  className={styles.select}
                >
                  <option value="ALL">All Classifications</option>
                  <option value="PUBLIC">PUBLIC</option>
                  <option value="INTERNAL">INTERNAL</option>
                  <option value="CONFIDENTIAL">CONFIDENTIAL</option>
                  <option value="RESTRICTED">RESTRICTED</option>
                </select>
              </div>

              <div className={styles.field}>
                <label className={styles.label}>Export Format</label>
                <select
                  name="export_format"
                  value={formData.export_format}
                  onChange={handleChange}
                  className={styles.select}
                >
                  <option value="JSON">Canonical JSON Package</option>
                  <option value="CSV">Flat CSV Export</option>
                </select>
              </div>

              <div className={`${styles.field} ${styles.fullWidth}`}>
                <label className={styles.label}>Justification / Audit Reason</label>
                <textarea
                  name="reason"
                  rows={2}
                  placeholder="Compliance review, internal audit, incident analysis..."
                  value={formData.reason || ""}
                  onChange={handleChange}
                  className={styles.textarea}
                />
              </div>
            </div>
          </div>

          <div className={styles.footer}>
            <button
              type="button"
              onClick={onClose}
              className={styles.cancelButton}
              disabled={loading}
            >
              Cancel
            </button>
            <button
              type="submit"
              className={styles.submitButton}
              disabled={loading}
            >
              {loading ? "Generating Package..." : "Generate Compliance Export"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

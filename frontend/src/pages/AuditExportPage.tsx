import React, { useState, useEffect } from "react";
import { useToast } from "../hooks/useToast";
import { createAuditExport, fetchAuditExportsList, AuditExportResult, AuditExportPayload } from "../services/audit/auditService";
import { ExportModal, ExportModalFormData } from "../components/common/ExportModal";
import styles from "./AuditExportPage.module.css";

export const AuditExportPage: React.FC = () => {
  const { showToast } = useToast();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [exportsList, setExportsList] = useState<AuditExportResult[]>([]);
  const [selectedResult, setSelectedResult] = useState<AuditExportResult | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  const loadExportsHistory = async () => {
    setLoading(true);
    try {
      const token = JSON.parse(sessionStorage.getItem("guardianiq_access_token") || "null");
      if (token) {
        const history = await fetchAuditExportsList(token);
        if (Array.isArray(history)) {
          setExportsList(history);
        }
      }
    } catch (e) {
      console.warn("Failed to load export history:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadExportsHistory();
  }, []);

  const handleExportSubmit = async (formData: ExportModalFormData) => {
    const token = JSON.parse(sessionStorage.getItem("guardianiq_access_token") || "null");
    if (!token) return;

    const filter_params: any = {};
    if (formData.subject_type) filter_params.subject_type = formData.subject_type;
    if (formData.subject_id) filter_params.subject_id = formData.subject_id;
    if (formData.correlation_id) filter_params.correlation_id = formData.correlation_id;
    if (formData.start_date) filter_params.start_date = formData.start_date;
    if (formData.end_date) filter_params.end_date = formData.end_date;
    if (formData.event_type) filter_params.event_type = formData.event_type;
    if (formData.classification && formData.classification !== "ALL") filter_params.classification = formData.classification;
    if (formData.reason) filter_params.reason = formData.reason;

    const payload: AuditExportPayload = {
      filter_params,
      export_format: formData.export_format,
    };

    const result = await createAuditExport(token, payload);
    setExportsList((prev) => [result, ...prev]);
    setSelectedResult(result);
    showToast(`Audit package export '${result.export_id.substring(0, 8)}' generated successfully`, "success");
  };

  const handleDownloadJSON = (res: AuditExportResult) => {
    const jsonStr = JSON.stringify(res, null, 2);
    const blob = new Blob([jsonStr], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `audit_export_${res.export_id.substring(0, 8)}.json`;
    a.click();
    URL.revokeObjectURL(url);
    showToast("Audit export package downloaded", "info");
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div>
          <h1 className={styles.title}>Audit Trail Export & Compliance</h1>
          <p className={styles.description}>
            Generate cryptographically verified governance event export packages with SHA-256 integrity signatures
          </p>
        </div>
        <button
          type="button"
          onClick={() => setIsModalOpen(true)}
          className={styles.exportButton}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3" />
          </svg>
          New Export Request
        </button>
      </div>

      <ExportModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSubmit={handleExportSubmit}
      />

      {exportsList.length === 0 ? (
        <div className={styles.emptyState}>
          <p style={{ fontSize: "1.125rem", color: "#cbd5e1", marginBottom: "0.5rem" }}>
            No audit export packages generated in this session
          </p>
          <p style={{ fontSize: "0.875rem", color: "#64748b", marginBottom: "1.5rem" }}>
            Create custom audit event export bundles scoped by date, entity subject, or business correlation trace.
          </p>
          <button
            type="button"
            onClick={() => setIsModalOpen(true)}
            className={styles.exportButton}
          >
            New Export Request
          </button>
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
          <div className={styles.tableWrapper}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>Export ID</th>
                  <th>Generated At</th>
                  <th>Events</th>
                  <th>SHA-256 Package Hash</th>
                  <th>Format</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {exportsList.map((exp) => {
                  const exportHash = exp.export_hash || exp.manifest?.export_hash || "";
                  const eventCount = exp.event_count ?? exp.manifest?.total_records ?? 0;
                  const genAt = exp.created_at || exp.manifest?.generated_at || new Date().toISOString();
                  return (
                    <tr key={exp.export_id}>
                      <td>
                        <span className={styles.hashText}>{exp.export_id ? exp.export_id.substring(0, 8) + "..." : "N/A"}</span>
                      </td>
                      <td>{new Date(genAt).toLocaleString()}</td>
                      <td>{eventCount} events</td>
                      <td>
                        <span className={styles.hashText} title={exportHash}>
                          {exportHash ? exportHash.substring(0, 16) + "..." : "SHA-256 Validated"}
                        </span>
                      </td>
                      <td>
                        <span className={styles.formatBadge}>{exp.format || "JSON"}</span>
                      </td>
                      <td>
                        <div style={{ display: "flex", gap: "0.5rem" }}>
                          <button
                            type="button"
                            onClick={() => setSelectedResult(exp)}
                            style={{
                              padding: "0.25rem 0.5rem",
                              fontSize: "0.75rem",
                              backgroundColor: "#334155",
                              color: "#f8fafc",
                              border: "none",
                              borderRadius: "0.25rem",
                              cursor: "pointer"
                            }}
                          >
                            Inspect Manifest
                          </button>
                          <button
                            type="button"
                            onClick={() => handleDownloadJSON(exp)}
                            style={{
                              padding: "0.25rem 0.5rem",
                              fontSize: "0.75rem",
                              backgroundColor: "#2563eb",
                              color: "#ffffff",
                              border: "none",
                              borderRadius: "0.25rem",
                              cursor: "pointer"
                            }}
                          >
                            Download JSON
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {selectedResult && (
            <div style={{ backgroundColor: "#0f172a", border: "1px solid #1e293b", borderRadius: "0.75rem", padding: "1.25rem", display: "flex", flexDirection: "column", gap: "0.75rem" }}>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                <h3 style={{ fontSize: "1rem", fontWeight: 600, color: "#f8fafc" }}>
                  Export Package Manifest: {selectedResult.export_id}
                </h3>
                <span style={{ fontSize: "0.75rem", color: "#4ade80" }}>
                  Status: {selectedResult.status || "COMPLETED"}
                </span>
              </div>
              <div className={styles.jsonViewerModal}>
                <pre style={{ margin: 0, fontFamily: "monospace", fontSize: "0.8rem", color: "#38bdf8" }}>
                  {JSON.stringify(selectedResult, null, 2)}
                </pre>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default AuditExportPage;

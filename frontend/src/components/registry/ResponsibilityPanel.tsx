import React, { useEffect, useState } from "react";
import { Badge } from "../common/Badge";
import { RegistryDataTable } from "../common/RegistryDataTable";
import { Button } from "../common/Button";
import { Modal } from "../common/Modal";
import * as registryService from "../../services/registry/registryService";
import { UserPlus } from "lucide-react";
import { useToast } from "../../hooks/useToast";
import styles from "./ResponsibilityPanel.module.css";

interface ResponsibilityPanelProps {
  objectType: string;
  objectId: string;
}

const mapToBackendType = (type: string): string => {
  const t = (type || "").toUpperCase();
  if (t === "AGENT" || t === "AGENTS" || t === "AI_AGENT" || t === "AI_AGENTS") return "AGENT";
  if (t === "MODEL" || t === "MODELS" || t === "AI_MODEL" || t === "AI_MODELS") return "MODEL";
  if (t === "TOOL" || t === "TOOLS") return "TOOL";
  if (t === "WORKFLOW" || t === "WORKFLOWS") return "WORKFLOW";
  if (t === "DATA_SOURCE" || t === "DATA_SOURCES" || t === "DATASOURCE" || t === "DATASOURCES") return "DATA_SOURCE";
  if (t === "DEPARTMENT" || t === "DEPARTMENTS") return "DEPARTMENT";
  if (t === "USER" || t === "USERS") return "USER";
  if (t === "ROLE" || t === "ROLES") return "ROLE";
  return (type || "").toUpperCase();
};

export const ResponsibilityPanel: React.FC<ResponsibilityPanelProps> = ({ objectType, objectId }) => {
  const [responsibilities, setResponsibilities] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const { showToast } = useToast();

  // Modal & Form State
  const [isAssignModalOpen, setIsAssignModalOpen] = useState(false);
  const [users, setUsers] = useState<{ id: string; full_name: string; email: string }[]>([]);
  const [respTypes, setRespTypes] = useState<string[]>(["OWNER", "REVIEWER", "APPROVER", "AUDITOR"]);
  const [selectedUserId, setSelectedUserId] = useState("");
  const [respType, setRespType] = useState("");
  const [isPrimary, setIsPrimary] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [generalError, setGeneralError] = useState<string | null>(null);

  const loadResponsibilities = async () => {
    setLoading(true);
    try {
      const backendType = mapToBackendType(objectType);
      const res = await registryService.getResponsibilities(backendType, objectId);
      setResponsibilities(res?.data || (Array.isArray(res) ? res : []));
    } catch (err: any) {
      showToast(err.message || "Failed to load responsibilities", "error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (objectId) {
      loadResponsibilities();
    }
  }, [objectId, objectType]);

  // Load modal lookups when modal is opened
  useEffect(() => {
    async function loadModalLookups() {
      if (isAssignModalOpen) {
        try {
          const [usersRes, typesRes] = await Promise.all([
            registryService.getUsersLookup(),
            registryService.getResponsibilityTypes()
          ]);
          if (usersRes.data) {
            setUsers(usersRes.data);
          }
          if (typesRes.data && typesRes.data.length > 0) {
            setRespTypes(typesRes.data);
          }
        } catch (err) {
          console.error("Failed to load responsibility assignment lookups:", err);
        }
      }
    }
    loadModalLookups();
  }, [isAssignModalOpen]);

  const handleAssignClick = () => {
    setGeneralError(null);
    setSelectedUserId("");
    setRespType("");
    setIsPrimary(false);
    setIsAssignModalOpen(true);
  };

  const handleAssignSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedUserId || !respType) {
      setGeneralError("Please select a user and responsibility type.");
      return;
    }
    setSubmitting(true);
    setGeneralError(null);
    try {
      const backendType = mapToBackendType(objectType);
      const payload = {
        object_type: backendType,
        object_id: objectId,
        actor_type: "USER" as const,
        actor_id: selectedUserId,
        responsibility_type: respType,
        is_primary: isPrimary
      };
      const res = await registryService.assignResponsibility(payload);
      if (res.status === "success") {
        showToast("Responsibility assigned successfully", "success");
        setIsAssignModalOpen(false);
        loadResponsibilities();
      } else {
        setGeneralError(res.message || "Failed to assign responsibility");
      }
    } catch (err: any) {
      setGeneralError(err.message || "An unexpected error occurred (ABAC checks may have failed)");
    } finally {
      setSubmitting(false);
    }
  };

  const columns = [
    {
      key: "responsibility_type",
      label: "Responsibility Type",
      render: (row: any) => <Badge variant={row.is_primary ? "info" : "neutral"} label={row.responsibility_type} />
    },
    {
      key: "actor_type",
      label: "Actor Type",
      render: (row: any) => row.actor_type || "-"
    },
    {
      key: "actor_id",
      label: "Assigned User / Actor",
      render: (row: any) => row.actor_name || row.actor_id || "-"
    },
    {
      key: "is_primary",
      label: "Primary",
      render: (row: any) => row.is_primary ? "Yes" : "No"
    },
    {
      key: "status",
      label: "Status",
      render: (row: any) => <Badge variant={row.status === 'ACTIVE' ? 'success' : 'neutral'} label={row.status} />
    }
  ];

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h4 className={styles.title}>Governance Responsibilities</h4>
        <Button variant="secondary" size="sm" onClick={handleAssignClick}>
          <UserPlus size={16} style={{ marginRight: '8px' }} />
          Assign Responsibility
        </Button>
      </div>

      <RegistryDataTable
        data={responsibilities}
        columns={columns}
        isLoading={loading}
        totalCount={responsibilities.length}
        page={1}
        pageSize={100}
        onPageChange={() => {}}
        emptyMessage="This object has no assigned responsibilities."
      />

      {isAssignModalOpen && (
        <Modal
          isOpen={isAssignModalOpen}
          onClose={() => setIsAssignModalOpen(false)}
          title="Assign Governance Responsibility"
          size="md"
        >
          <form onSubmit={handleAssignSubmit} className={styles.form}>
            {generalError && (
              <div className={styles.errorMessage}>
                {generalError}
              </div>
            )}

            <div className={styles.formGroup}>
              <label className={styles.label}>
                Select User <span className={styles.required}>*</span>
              </label>
              <select
                value={selectedUserId}
                onChange={(e) => setSelectedUserId(e.target.value)}
                required
                className={styles.select}
              >
                <option value="">-- Choose User --</option>
                {users.map(u => (
                  <option key={u.id} value={u.id}>{u.full_name} ({u.email})</option>
                ))}
              </select>
            </div>

            <div className={styles.formGroup}>
              <label className={styles.label}>
                Responsibility Type <span className={styles.required}>*</span>
              </label>
              <select
                value={respType}
                onChange={(e) => setRespType(e.target.value)}
                required
                className={styles.select}
              >
                <option value="">-- Choose Type --</option>
                {respTypes.map(t => (
                  <option key={t} value={t}>{t}</option>
                ))}
              </select>
            </div>

            <div className={styles.checkboxContainer}>
              <input
                type="checkbox"
                id="isPrimary"
                checked={isPrimary}
                onChange={(e) => setIsPrimary(e.target.checked)}
                className={styles.checkbox}
              />
              <label htmlFor="isPrimary" className={styles.checkboxLabel}>
                Primary Assignment (Revokes existing primary owner if OWNER)
              </label>
            </div>

            <div className={styles.modalActions}>
              <Button variant="secondary" type="button" onClick={() => setIsAssignModalOpen(false)} disabled={submitting}>
                Cancel
              </Button>
              <Button variant="primary" type="submit" disabled={submitting}>
                {submitting ? "Assigning..." : "Assign"}
              </Button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
};

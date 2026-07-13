import React, { useEffect, useState } from "react";
import { Badge } from "../common/Badge";
import { RegistryDataTable } from "../common/RegistryDataTable";
import { Button } from "../common/Button";
import { Modal } from "../common/Modal";
import * as registryService from "../../services/registry/registryService";
import { UserPlus } from "lucide-react";
import { useToast } from "../../hooks/useToast";

interface ResponsibilityPanelProps {
  objectType: string;
  objectId: string;
}

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
      const res = await registryService.getResponsibilities(objectType, objectId);
      setResponsibilities(res.data || []);
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
      const payload = {
        object_type: objectType,
        object_id: objectId,
        actor_type: "USER" as const,
        actor_id: selectedUserId,
        responsibility_type: respType,
        is_primary: isPrimary
      };
      const res = await registryService.assignResponsibility(payload);
      if (res.success) {
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
      label: "Actor ID",
      render: (row: any) => row.actor_id || "-"
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
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <h4 style={{ margin: 0, color: '#fff', fontSize: '1.1rem' }}>Governance Responsibilities</h4>
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
          <form onSubmit={handleAssignSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px', padding: '8px 0' }}>
            {generalError && (
              <div style={{ background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.2)', color: '#ef4444', padding: '12px', borderRadius: '6px', fontSize: '0.875rem' }}>
                {generalError}
              </div>
            )}

            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <label style={{ fontSize: '0.85rem', color: '#ccc', fontWeight: 500 }}>
                Select User <span style={{ color: '#ef4444' }}>*</span>
              </label>
              <select
                value={selectedUserId}
                onChange={(e) => setSelectedUserId(e.target.value)}
                required
                style={{ background: '#1e1f22', border: '1px solid rgba(255, 255, 255, 0.1)', color: '#fff', padding: '8px 12px', borderRadius: '6px', outline: 'none' }}
              >
                <option value="">-- Choose User --</option>
                {users.map(u => (
                  <option key={u.id} value={u.id}>{u.full_name} ({u.email})</option>
                ))}
              </select>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <label style={{ fontSize: '0.85rem', color: '#ccc', fontWeight: 500 }}>
                Responsibility Type <span style={{ color: '#ef4444' }}>*</span>
              </label>
              <select
                value={respType}
                onChange={(e) => setRespType(e.target.value)}
                required
                style={{ background: '#1e1f22', border: '1px solid rgba(255, 255, 255, 0.1)', color: '#fff', padding: '8px 12px', borderRadius: '6px', outline: 'none' }}
              >
                <option value="">-- Choose Type --</option>
                {respTypes.map(t => (
                  <option key={t} value={t}>{t}</option>
                ))}
              </select>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '4px' }}>
              <input
                type="checkbox"
                id="isPrimary"
                checked={isPrimary}
                onChange={(e) => setIsPrimary(e.target.checked)}
                style={{ width: '16px', height: '16px', accentColor: '#22c55e', cursor: 'pointer' }}
              />
              <label htmlFor="isPrimary" style={{ fontSize: '0.85rem', color: '#ccc', cursor: 'pointer' }}>
                Primary Assignment (Revokes existing primary owner if OWNER)
              </label>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', marginTop: '16px' }}>
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

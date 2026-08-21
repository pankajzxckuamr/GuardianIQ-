import React, { useEffect, useState } from "react";
import { Badge } from "../common/Badge";
import { RegistryDataTable } from "../common/RegistryDataTable";
import { Button } from "../common/Button";
import { AddRelationshipModal } from "./AddRelationshipModal";
import * as registryService from "../../services/registry/registryService";
import { Trash2, PauseCircle, CheckCircle, PlayCircle, Plus } from "lucide-react";
import { useToast } from "../../hooks/useToast";
import styles from "./ObjectRelationshipPanel.module.css";

interface ObjectRelationshipPanelProps {
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

export const ObjectRelationshipPanel: React.FC<ObjectRelationshipPanelProps> = ({ objectType, objectId }) => {
  const [relationships, setRelationships] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const { showToast } = useToast();

  const loadRelationships = async () => {
    setLoading(true);
    try {
      const backendType = mapToBackendType(objectType);
      const res = await registryService.listRelationships({ source_type: backendType, source_id: objectId, per_page: 100 });
      setRelationships(res?.data?.items || res?.items || (Array.isArray(res?.data) ? res.data : []));
    } catch (err: any) {
      showToast(err.message || "Failed to load relationships", "error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (objectId) {
      loadRelationships();
    }
  }, [objectId, objectType]);

  const handleAction = async (id: string, action: string) => {
    try {
      let res: any;
      if (action === 'revoke') {
        const reason = window.prompt("Please enter mandatory revocation reason:");
        if (reason === null) return;
        if (!reason.trim()) {
          showToast("Revocation reason is mandatory", "error");
          return;
        }
        res = await registryService.revokeRelationship(id, reason);
      } else if (action === 'suspend') {
        const reason = window.prompt("Please enter mandatory suspension reason:");
        if (reason === null) return;
        if (!reason.trim()) {
          showToast("Suspension reason is mandatory", "error");
          return;
        }
        res = await registryService.suspendRelationship(id, reason);
      } else if (action === 'approve') {
        res = await registryService.approveRelationship(id);
      } else if (action === 'activate') {
        res = await registryService.activateRelationship(id);
      }
      
      const reqIdText = res?.request_id ? ` (Request ID: ${res.request_id})` : '';
      showToast(`Relationship ${action}d successfully${reqIdText}`, "success");
      loadRelationships();
    } catch (err: any) {
      showToast(err.message || `Failed to ${action} relationship`, "error");
    }
  };

  const columns = [
    {
      key: "relationship_type",
      label: "Relationship Type",
      render: (row: any) => <Badge variant="info" label={row.relationship_type} />
    },
    {
      key: "target_type",
      label: "Target Type",
      render: (row: any) => <Badge variant="neutral" label={row.target_type} />
    },
    {
      key: "status",
      label: "Status",
      render: (row: any) => <Badge variant={row.status === 'ACTIVE' ? 'success' : 'neutral'} label={row.status} />
    },
    {
      key: "actions",
      label: "Actions",
      render: (row: any) => (
        <div className={styles.actions}>
          {row.status === 'PROPOSED' && (
            <Button variant="ghost" size="sm" onClick={() => handleAction(row.id, 'approve')} title="Approve" className={styles.actionBtn}>
              <CheckCircle size={16} />
            </Button>
          )}
          {row.status === 'PENDING_APPROVAL' && (
            <Button variant="ghost" size="sm" onClick={() => handleAction(row.id, 'activate')} title="Activate" className={styles.actionBtn}>
              <PlayCircle size={16} />
            </Button>
          )}
          {row.status === 'ACTIVE' && (
            <Button variant="ghost" size="sm" onClick={() => handleAction(row.id, 'suspend')} title="Suspend" className={styles.actionBtn}>
              <PauseCircle size={16} />
            </Button>
          )}
          <Button variant="ghost" size="sm" onClick={() => handleAction(row.id, 'revoke')} title="Revoke" className={`${styles.actionBtn} ${styles.actionBtnRevoke}`}>
            <Trash2 size={16} />
          </Button>
        </div>
      )
    }
  ];

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h4 className={styles.title}>Direct Relationships</h4>
        <Button variant="primary" size="sm" onClick={() => setIsAddModalOpen(true)}>
          <Plus size={16} style={{ marginRight: '8px' }} />
          Add Relationship
        </Button>
      </div>

      <RegistryDataTable
        data={relationships}
        columns={columns}
        isLoading={loading}
        totalCount={relationships.length}
        page={1}
        pageSize={100}
        onPageChange={() => {}}
        emptyMessage="This object has no direct relationships."
      />

      {isAddModalOpen && (
        <AddRelationshipModal
          isOpen={isAddModalOpen}
          onClose={() => setIsAddModalOpen(false)}
          sourceEntityType={objectType}
          sourceEntityId={objectId}
          onSuccess={() => {
            setIsAddModalOpen(false);
            loadRelationships();
          }}
        />
      )}
    </div>
  );
};

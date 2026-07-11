import React, { useEffect, useState } from "react";
import { Badge } from "../common/Badge";
import { RegistryDataTable } from "../common/RegistryDataTable";
import { Button } from "../common/Button";
import { AddRelationshipModal } from "./AddRelationshipModal";
import * as registryService from "../../services/registry/registryService";
import { Trash2, PauseCircle, CheckCircle, PlayCircle, Plus } from "lucide-react";
import { useToast } from "../../hooks/useToast";

interface ObjectRelationshipPanelProps {
  objectType: string;
  objectId: string;
}

export const ObjectRelationshipPanel: React.FC<ObjectRelationshipPanelProps> = ({ objectType, objectId }) => {
  const [relationships, setRelationships] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const { showToast } = useToast();

  const loadRelationships = async () => {
    setLoading(true);
    try {
      const res = await registryService.listRelationships({ source_type: objectType, source_id: objectId, per_page: 100 });
      setRelationships(res.data?.items || []);
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
      if (action === 'revoke') {
        await registryService.revokeRelationship(id, "User requested revocation");
      } else if (action === 'suspend') {
        await registryService.suspendRelationship(id, "User requested suspension");
      } else if (action === 'approve') {
        await registryService.approveRelationship(id);
      } else if (action === 'activate') {
        await registryService.activateRelationship(id);
      }
      showToast(`Relationship ${action}d successfully`, "success");
      loadRelationships();
    } catch (err: any) {
      showToast(err.message || `Failed to ${action} relationship`, "error");
    }
  };

  const columns = [
    {
      header: "Relationship Type",
      accessor: (row: any) => <Badge variant="info" label={row.relationship_type} />
    },
    {
      header: "Target Type",
      accessor: (row: any) => <Badge variant="neutral" label={row.target_type} />
    },
    {
      header: "Status",
      accessor: (row: any) => <Badge variant={row.status === 'ACTIVE' ? 'success' : 'neutral'} label={row.status} />
    },
    {
      header: "Actions",
      accessor: (row: any) => (
        <div style={{ display: 'flex', gap: '8px' }}>
          {row.status === 'PROPOSED' && (
            <Button variant="ghost" size="sm" onClick={() => handleAction(row.id, 'approve')} title="Approve">
              <CheckCircle size={16} />
            </Button>
          )}
          {row.status === 'PENDING_APPROVAL' && (
            <Button variant="ghost" size="sm" onClick={() => handleAction(row.id, 'activate')} title="Activate">
              <PlayCircle size={16} />
            </Button>
          )}
          {row.status === 'ACTIVE' && (
            <Button variant="ghost" size="sm" onClick={() => handleAction(row.id, 'suspend')} title="Suspend">
              <PauseCircle size={16} />
            </Button>
          )}
          <Button variant="ghost" size="sm" onClick={() => handleAction(row.id, 'revoke')} title="Revoke" style={{ color: '#ef4444' }}>
            <Trash2 size={16} />
          </Button>
        </div>
      )
    }
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <h4 style={{ margin: 0, color: '#fff', fontSize: '1.1rem' }}>Direct Relationships</h4>
        <Button variant="primary" size="sm" onClick={() => setIsAddModalOpen(true)}>
          <Plus size={16} style={{ marginRight: '8px' }} />
          Add Relationship
        </Button>
      </div>

      <RegistryDataTable
        data={relationships}
        columns={columns}
        loading={loading}
        emptyStateTitle="No relationships"
        emptyStateDesc="This object has no direct relationships."
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

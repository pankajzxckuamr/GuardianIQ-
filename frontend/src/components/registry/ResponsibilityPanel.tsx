import React, { useEffect, useState } from "react";
import { Badge } from "../common/Badge";
import { RegistryDataTable } from "../common/RegistryDataTable";
import { Button } from "../common/Button";
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

  const handleAssignMock = async () => {
    // In a full implementation this would open a modal to select a user and role
    // For MVP, we'll just show a toast or assign a mock responsibility
    showToast("Assign responsibility UI not fully implemented in MVP", "info");
  };

  const columns = [
    {
      header: "Responsibility Type",
      accessor: (row: any) => <Badge variant={row.is_primary ? "info" : "neutral"} label={row.responsibility_type} />
    },
    {
      header: "Actor Type",
      accessor: "actor_type"
    },
    {
      header: "Actor ID",
      accessor: "actor_id"
    },
    {
      header: "Primary",
      accessor: (row: any) => row.is_primary ? "Yes" : "No"
    },
    {
      header: "Status",
      accessor: (row: any) => <Badge variant={row.status === 'ACTIVE' ? 'success' : 'neutral'} label={row.status} />
    }
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <h4 style={{ margin: 0, color: '#fff', fontSize: '1.1rem' }}>Governance Responsibilities</h4>
        <Button variant="secondary" size="sm" onClick={handleAssignMock}>
          <UserPlus size={16} style={{ marginRight: '8px' }} />
          Assign Responsibility
        </Button>
      </div>

      <RegistryDataTable
        data={responsibilities}
        columns={columns}
        loading={loading}
        emptyStateTitle="No responsibilities"
        emptyStateDesc="This object has no assigned responsibilities."
      />
    </div>
  );
};

/* src/components/registry/RelationshipViewer.tsx */

import React, { useEffect, useState } from "react";
import { useAuth } from "../../hooks/useAuth";
import { useToast } from "../../hooks/useToast";
import * as registryService from "../../services/registry/registryService";
import { AddRelationshipModal } from "./AddRelationshipModal";
import styles from "./RelationshipViewer.module.css";
import { Trash2, Plus, ArrowRight } from "lucide-react";

interface RelationshipViewerProps {
  entityType: string;
  entityId: string;
}

interface RelationshipItem {
  id: string;
  relationship_type: string;
  other_entity_type: string;
  other_entity_id: string;
  other_entity_name: string;
  status: string;
}

export const RelationshipViewer: React.FC<RelationshipViewerProps> = ({
  entityType,
  entityId
}) => {
  const { currentUser } = useAuth();
  const { showToast } = useToast();

  const [outgoing, setOutgoing] = useState<RelationshipItem[]>([]);
  const [incoming, setIncoming] = useState<RelationshipItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);

  // Check RBAC permissions for administration
  const isAdmin = currentUser?.is_superuser || 
    currentUser?.roles?.some(role => ["admin", "super_admin"].includes(role.toLowerCase()));

  const fetchRelationships = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await registryService.listRelationships(entityType, entityId);
      if (res.data) {
        const rawData = res.data as any;
        setOutgoing(rawData.outgoing || []);
        setIncoming(rawData.incoming || []);
      }
    } catch (err: any) {
      console.error("Failed to load relationships:", err);
      setError(err.message || "Failed to load relationships.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRelationships();
  }, [entityType, entityId]);

  const handleDelete = async (id: string) => {
    if (!window.confirm("Are you sure you want to remove this relationship link?")) {
      return;
    }
    try {
      await registryService.deleteRelationship(id);
      showToast("Relationship removed successfully", "success");
      fetchRelationships();
    } catch (err: any) {
      showToast(err.message || "Failed to remove relationship", "error");
    }
  };

  const getEntityBadgeClass = (type: string) => {
    const t = type.toUpperCase();
    if (t === "MODEL") return styles.badgeModel;
    if (t === "AGENT") return styles.badgeAgent;
    if (t === "TOOL") return styles.badgeTool;
    if (t === "WORKFLOW") return styles.badgeWorkflow;
    if (t === "DATA_SOURCE") return styles.badgeDataSource;
    if (t === "DEPARTMENT") return styles.badgeDepartment;
    if (t === "USER") return styles.badgeUser;
    if (t === "ROLE") return styles.badgeRole;
    return styles.badgeGeneric;
  };

  const getStatusBadgeClass = (status: string) => {
    const s = status.toUpperCase();
    if (s === "ACTIVE") return styles.statusActive;
    if (s === "DRAFT") return styles.statusDraft;
    if (s === "INACTIVE") return styles.statusInactive;
    return styles.statusGeneric;
  };

  const formatEntityLabel = (type: string) => {
    return type.replace("_", " ");
  };

  const renderRelationshipRow = (item: RelationshipItem, direction: "outgoing" | "incoming") => {
    const isOutgoing = direction === "outgoing";
    
    // Parse types and display friendly names
    const sourceLabel = isOutgoing ? `Current ${formatEntityLabel(entityType)}` : item.other_entity_name;
    const sourceType = isOutgoing ? entityType : item.other_entity_type;
    
    const targetLabel = isOutgoing ? item.other_entity_name : `Current ${formatEntityLabel(entityType)}`;
    const targetType = isOutgoing ? item.other_entity_type : entityType;

    return (
      <div key={item.id} className={styles.relationshipRow}>
        <div className={styles.connectionFlow}>
          {/* Source Entity */}
          <div className={styles.entityNode}>
            <span className={`${styles.entityBadge} ${getEntityBadgeClass(sourceType)}`}>
              {sourceType}
            </span>
            <span className={styles.entityName} title={sourceLabel}>{sourceLabel}</span>
          </div>

          {/* Trace Line & Relationship Pill */}
          <div className={styles.traceConnector}>
            <div className={styles.traceLine}></div>
            <span className={styles.relationshipPill} title={item.relationship_type}>
              {item.relationship_type}
            </span>
            <ArrowRight className={styles.traceArrow} size={14} />
          </div>

          {/* Target Entity */}
          <div className={styles.entityNode}>
            <span className={`${styles.entityBadge} ${getEntityBadgeClass(targetType)}`}>
              {targetType}
            </span>
            <span className={styles.entityName} title={targetLabel}>{targetLabel}</span>
          </div>
        </div>

        {/* Status and Actions */}
        <div className={styles.rowActions}>
          <span className={`${styles.statusBadge} ${getStatusBadgeClass(item.status)}`}>
            {item.status}
          </span>
          {isAdmin && (
            <button
              type="button"
              onClick={() => handleDelete(item.id)}
              className={styles.removeBtn}
              title="Remove relationship link"
            >
              <Trash2 size={14} />
              <span>Remove</span>
            </button>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className={styles.viewer}>
      <div className={styles.viewerHeader}>
        <h4 className={styles.viewerTitle}>Entity Linkages</h4>
        <button
          type="button"
          onClick={() => setIsAddModalOpen(true)}
          className={styles.addLinkBtn}
        >
          <Plus size={14} style={{ marginRight: "0.25rem" }} />
          <span>Add Link</span>
        </button>
      </div>

      {error && <div className={styles.alertError}>{error}</div>}

      {loading && (
        <div className={styles.skeletonContainer}>
          <div className={styles.skeletonRow}></div>
          <div className={styles.skeletonRow}></div>
        </div>
      )}

      {!loading && !error && (
        <div className={styles.sectionsContainer}>
          {/* Outgoing Section */}
          <div className={styles.sectionBlock}>
            <h5 className={styles.sectionHeading}>Outgoing Links</h5>
            <div className={styles.linksList}>
              {outgoing.length > 0 ? (
                outgoing.map(item => renderRelationshipRow(item, "outgoing"))
              ) : (
                <div className={styles.emptyState}>No outgoing links established for this entity.</div>
              )}
            </div>
          </div>

          {/* Incoming Section */}
          <div className={styles.sectionBlock}>
            <h5 className={styles.sectionHeading}>Incoming Links</h5>
            <div className={styles.linksList}>
              {incoming.length > 0 ? (
                incoming.map(item => renderRelationshipRow(item, "incoming"))
              ) : (
                <div className={styles.emptyState}>No incoming linkages target this entity yet.</div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Add Link Dialogue Form Modal */}
      <AddRelationshipModal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        sourceEntityType={entityType}
        sourceEntityId={entityId}
        onSuccess={fetchRelationships}
      />
    </div>
  );
};

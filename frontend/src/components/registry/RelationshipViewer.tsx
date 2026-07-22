/* src/components/registry/RelationshipViewer.tsx */

import React, { useEffect, useState, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../hooks/useAuth";
import { useToast } from "../../hooks/useToast";
import * as registryService from "../../services/registry/registryService";
import { AddRelationshipModal } from "./AddRelationshipModal";
import styles from "./RelationshipViewer.module.css";
import { Trash2, Plus, ArrowRight } from "lucide-react";
import { 
  ReactFlow, 
  Background, 
  Controls, 
  MarkerType, 
  Node, 
  Edge,
  Handle,
  Position
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

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
  other_entity_status?: string;
  other_entity_risk?: string;
}

const getEntityBadgeClass = (type: string) => {
  const t = type.toUpperCase();
  if (t === "MODEL" || t === "MODELS" || t === "AI_MODEL" || t === "AI_MODELS") return styles.badgeModel;
  if (t === "AGENT" || t === "AGENTS") return styles.badgeAgent;
  if (t === "TOOL" || t === "TOOLS") return styles.badgeTool;
  if (t === "WORKFLOW" || t === "WORKFLOWS") return styles.badgeWorkflow;
  if (t === "DATA_SOURCE" || t === "DATA_SOURCES") return styles.badgeDataSource;
  if (t === "DEPARTMENT" || t === "DEPARTMENTS") return styles.badgeDepartment;
  if (t === "USER" || t === "USERS") return styles.badgeUser;
  if (t === "ROLE" || t === "ROLES") return styles.badgeRole;
  return styles.badgeGeneric;
};

const formatEntityLabel = (type: string) => {
  return type.replace("_", " ");
};

const getRiskBadgeStyle = (risk: string) => {
  const r = (risk || "").toUpperCase();
  if (r === "CRITICAL" || r === "HIGH") return { background: "#ef4444", color: "#fff" }; // red
  if (r === "MEDIUM") return { background: "#eab308", color: "#000" }; // yellow
  return { background: "#10b981", color: "#fff" }; // green (LOW)
};

const getStatusBadgeStyle = (status: string) => {
  const s = (status || "").toUpperCase();
  if (s === "ACTIVE") return { background: "#10b981", color: "#fff" }; // green
  if (s === "DRAFT" || s === "PROPOSED" || s === "PENDING_APPROVAL") return { background: "#eab308", color: "#000" }; // yellow
  return { background: "#94a3b8", color: "#fff" }; // grey
};

// Custom Nodes for Graph View
const CentralNode = ({ data }: any) => (
  <div className={`${styles.graphNode} ${styles.graphNodeCentral}`} style={{ display: "flex", flexDirection: "column", gap: "6px", padding: "10px", borderRadius: "8px", background: "#0b1329", border: "2px solid #3b82f6", minWidth: "160px" }}>
    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", width: "100%", gap: "4px" }}>
      <span className={`${styles.entityBadge} ${data.badgeClass}`}>{data.typeText}</span>
      <div style={{ display: "flex", gap: "2px" }}>
        <span style={{ fontSize: "9px", padding: "1px 3px", borderRadius: "2px", fontWeight: 600, ...getStatusBadgeStyle(data.status) }}>{data.status}</span>
        <span style={{ fontSize: "9px", padding: "1px 3px", borderRadius: "2px", fontWeight: 600, ...getRiskBadgeStyle(data.risk) }}>{data.risk}</span>
      </div>
    </div>
    <span className={styles.graphNodeName} title={data.label} style={{ color: "#fff", fontWeight: 500 }}>{data.label}</span>
    <Handle type="target" position={Position.Left} style={{ opacity: 0 }} />
    <Handle type="source" position={Position.Right} style={{ opacity: 0 }} />
  </div>
);

const PeripheralNode = ({ data }: any) => (
  <div className={styles.graphNode} onClick={() => data.onClick(data.entityType, data.entityId)} style={{ display: "flex", flexDirection: "column", gap: "6px", padding: "10px", borderRadius: "8px", background: "#0f172a", border: "1px solid rgba(255, 255, 255, 0.1)", cursor: "pointer", minWidth: "160px" }}>
    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", width: "100%", gap: "4px" }}>
      <span className={`${styles.entityBadge} ${data.badgeClass}`}>{data.typeText}</span>
      <div style={{ display: "flex", gap: "2px" }}>
        <span style={{ fontSize: "9px", padding: "1px 3px", borderRadius: "2px", fontWeight: 600, ...getStatusBadgeStyle(data.status) }}>{data.status}</span>
        <span style={{ fontSize: "9px", padding: "1px 3px", borderRadius: "2px", fontWeight: 600, ...getRiskBadgeStyle(data.risk) }}>{data.risk}</span>
      </div>
    </div>
    <span className={styles.graphNodeName} title={data.label} style={{ color: "rgba(255,255,255,0.95)" }}>{data.label}</span>
    <Handle type="target" position={Position.Left} style={{ opacity: 0 }} />
    <Handle type="source" position={Position.Right} style={{ opacity: 0 }} />
  </div>
);

const nodeTypes = {
  central: CentralNode,
  peripheral: PeripheralNode
};

export const RelationshipViewer: React.FC<RelationshipViewerProps> = ({
  entityType,
  entityId
}) => {
  const { currentUser } = useAuth();
  const { showToast } = useToast();
  const navigate = useNavigate();

  const [outgoing, setOutgoing] = useState<RelationshipItem[]>([]);
  const [incoming, setIncoming] = useState<RelationshipItem[]>([]);
  const [graphData, setGraphData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [viewMode, setViewMode] = useState<"list" | "graph">("list");
  const [depth, setDepth] = useState<number>(2);

  // Check RBAC permissions for administration
  const isAdmin = currentUser?.is_superuser || 
    currentUser?.roles?.some(role => ["admin", "super_admin"].includes(role.toLowerCase()));

  const mapToBackendType = (type: string): string => {
    const t = type.toUpperCase();
    if (t === "AGENT" || t === "AGENTS") return "agents";
    if (t === "MODEL" || t === "AI_MODELS" || t === "AI_MODEL") return "ai_models";
    if (t === "TOOL" || t === "TOOLS") return "tools";
    if (t === "WORKFLOW" || t === "WORKFLOWS") return "workflows";
    if (t === "DATA_SOURCE" || t === "DATA_SOURCES") return "data_sources";
    if (t === "DEPARTMENT" || t === "DEPARTMENTS") return "departments";
    if (t === "USER" || t === "USERS") return "users";
    if (t === "ROLE" || t === "ROLES") return "roles";
    return type.toLowerCase();
  };

  const fetchRelationships = async () => {
    setLoading(true);
    setError(null);
    try {
      const backendType = mapToBackendType(entityType);
      const res = await registryService.getRelationshipGraph(backendType, entityId, depth);
      if (res.data) {
        const rawData = res.data as any;
        setGraphData(rawData);
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
  }, [entityType, entityId, depth]);

  const handleDelete = async (id: string) => {
    const reason = window.prompt("Please enter mandatory revocation reason:");
    if (reason === null) return;
    if (!reason.trim()) {
      showToast("Revocation reason is mandatory", "error");
      return;
    }
    try {
      await registryService.revokeRelationship(id, reason);
      showToast("Relationship removed successfully", "success");
      fetchRelationships();
    } catch (err: any) {
      showToast(err.message || "Failed to remove relationship", "error");
    }
  };

  const getStatusBadgeClass = (status: string) => {
    const s = status.toUpperCase();
    if (s === "ACTIVE") return styles.statusActive;
    if (s === "DRAFT") return styles.statusDraft;
    if (s === "INACTIVE") return styles.statusInactive;
    return styles.statusGeneric;
  };

  const handleNodeClick = (type: string, id: string) => {
    const t = type.toUpperCase();
    let basePath = "";
    
    if (t === "MODEL" || t === "MODELS" || t === "AI_MODELS" || t === "AI_MODEL") {
      basePath = "models";
    } else if (t === "AGENT" || t === "AGENTS") {
      basePath = "agents";
    } else if (t === "TOOL" || t === "TOOLS") {
      basePath = "tools";
    } else if (t === "WORKFLOW" || t === "WORKFLOWS") {
      basePath = "workflows";
    } else if (t === "DATA_SOURCE" || t === "DATA_SOURCES" || t === "DATASOURCE") {
      basePath = "data-sources";
    } else if (t === "DEPARTMENT" || t === "DEPARTMENTS") {
      basePath = "departments";
    } else if (t === "USER" || t === "USERS" || t === "ROLE" || t === "ROLES") {
      basePath = "users-roles";
    } else {
      basePath = type.toLowerCase().replace("_", "-");
      if (!basePath.endsWith("s")) basePath += "s";
    }
    
    navigate(`/registry/${basePath}?view=${id}`);
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

  // Prepare graph data
  const { graphNodes, graphEdges } = useMemo(() => {
    if (viewMode !== 'graph') return { graphNodes: [], graphEdges: [] };

    const nodes: Node[] = [];
    const edges: Edge[] = [];

    // Central Node
    nodes.push({
      id: "central",
      type: "central",
      position: { x: 400, y: 250 },
      data: { 
        label: graphData?.root?.name || `Current ${formatEntityLabel(entityType)}`, 
        badgeClass: getEntityBadgeClass(entityType), 
        typeText: entityType,
        status: graphData?.root?.status || "ACTIVE",
        risk: graphData?.root?.risk || "LOW"
      }
    });

    const getEdgeColorAndStyle = (status: string) => {
      const s = (status || "").toUpperCase();
      if (s === "ACTIVE") return { color: "#10b981", animated: true, dash: "0" };
      if (s === "PROPOSED" || s === "PENDING_APPROVAL") return { color: "#eab308", animated: true, dash: "5,5" };
      return { color: "#94a3b8", animated: false, dash: "5,5" };
    };

    // Incoming Nodes (left side)
    const incomingYStart = Math.max(250 - (incoming.length * 50), 50);
    incoming.forEach((item, index) => {
      const nodeId = `in_${item.id}`;
      nodes.push({
        id: nodeId,
        type: "peripheral",
        position: { x: 50, y: incomingYStart + (index * 120) },
        data: { 
          label: item.other_entity_name, 
          badgeClass: getEntityBadgeClass(item.other_entity_type), 
          typeText: item.other_entity_type,
          entityId: item.other_entity_id,
          entityType: item.other_entity_type,
          onClick: handleNodeClick,
          status: item.other_entity_status || "ACTIVE",
          risk: item.other_entity_risk || "LOW",
          relationshipStatus: item.status
        }
      });
      const edgeConf = getEdgeColorAndStyle(item.status);
      edges.push({
        id: `e_${nodeId}_central`,
        source: nodeId,
        target: "central",
        label: item.relationship_type,
        animated: edgeConf.animated,
        style: { stroke: edgeConf.color, strokeWidth: 2, strokeDasharray: edgeConf.dash },
        markerEnd: { type: MarkerType.ArrowClosed, color: edgeConf.color },
        labelStyle: { fill: '#fff', fontWeight: 600, fontSize: 11 },
        labelBgStyle: { fill: '#0b1120', stroke: '#1e293b', strokeWidth: 1 }
      });
    });

    // Outgoing Nodes (right side)
    const outgoingYStart = Math.max(250 - (outgoing.length * 50), 50);
    outgoing.forEach((item, index) => {
      const nodeId = `out_${item.id}`;
      nodes.push({
        id: nodeId,
        type: "peripheral",
        position: { x: 750, y: outgoingYStart + (index * 120) },
        data: { 
          label: item.other_entity_name, 
          badgeClass: getEntityBadgeClass(item.other_entity_type), 
          typeText: item.other_entity_type,
          entityId: item.other_entity_id,
          entityType: item.other_entity_type,
          onClick: handleNodeClick,
          status: item.other_entity_status || "ACTIVE",
          risk: item.other_entity_risk || "LOW",
          relationshipStatus: item.status
        }
      });
      const edgeConf = getEdgeColorAndStyle(item.status);
      edges.push({
        id: `e_central_${nodeId}`,
        source: "central",
        target: nodeId,
        label: item.relationship_type,
        animated: edgeConf.animated,
        style: { stroke: edgeConf.color, strokeWidth: 2, strokeDasharray: edgeConf.dash },
        markerEnd: { type: MarkerType.ArrowClosed, color: edgeConf.color },
        labelStyle: { fill: '#fff', fontWeight: 600, fontSize: 11 },
        labelBgStyle: { fill: '#0b1120', stroke: '#1e293b', strokeWidth: 1 }
      });
    });

    return { graphNodes: nodes, graphEdges: edges };
  }, [viewMode, incoming, outgoing, entityType, graphData]);

  return (
    <div className={styles.viewer}>
      <div className={styles.viewerHeader}>
        <h4 className={styles.viewerTitle}>Entity Linkages</h4>
        <div className={styles.headerActions} style={{ display: 'flex', alignItems: 'center' }}>
          {/* Depth Control */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginRight: '1rem' }}>
            <span style={{ fontSize: '0.85rem', color: 'rgba(255, 255, 255, 0.6)' }}>Depth:</span>
            <select
              value={depth}
              onChange={(e) => setDepth(Number(e.target.value))}
              style={{ padding: '0.25rem 0.5rem', borderRadius: '4px', background: 'rgba(0,0,0,0.2)', border: '1px solid rgba(255,255,255,0.1)', color: '#fff', cursor: 'pointer' }}
            >
              <option value={1}>1 Hop</option>
              <option value={2}>2 Hops</option>
              <option value={3}>3 Hops</option>
              <option value={4}>4 Hops</option>
              <option value={5}>5 Hops</option>
            </select>
          </div>

          {/* Segmented Control */}
          <div className={styles.viewToggle} style={{ marginRight: '1rem' }}>
            <button 
              type="button" 
              className={`${styles.viewToggleBtn} ${viewMode === 'list' ? styles.active : ''}`}
              onClick={() => setViewMode('list')}
            >
              List
            </button>
            <button 
              type="button" 
              className={`${styles.viewToggleBtn} ${viewMode === 'graph' ? styles.active : ''}`}
              onClick={() => setViewMode('graph')}
            >
              Graph
            </button>
          </div>
          <button
            type="button"
            onClick={() => setIsAddModalOpen(true)}
            className={styles.addLinkBtn}
          >
            <Plus size={14} style={{ marginRight: "0.25rem" }} />
            <span>Add Link</span>
          </button>
        </div>
      </div>

      {error && <div className={styles.alertError}>{error}</div>}

      {loading && (
        <div className={styles.skeletonContainer}>
          <div className={styles.skeletonRow}></div>
          <div className={styles.skeletonRow}></div>
        </div>
      )}

      {!loading && !error && viewMode === "list" && (
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

      {!loading && !error && viewMode === "graph" && (
        <div className={styles.graphContainer}>
          <ReactFlow
            nodes={graphNodes}
            edges={graphEdges}
            nodeTypes={nodeTypes}
            fitView
            fitViewOptions={{ padding: 0.2 }}
            nodesDraggable={false}
            nodesConnectable={false}
            elementsSelectable={false}
          >
            <Background color="#1e293b" gap={16} />
            <Controls />
          </ReactFlow>
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

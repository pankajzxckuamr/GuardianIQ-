/* src/components/registry/RegisterAllWizardModal.tsx */

import React, { useState, useEffect, useMemo } from "react";
import { Modal } from "../common/Modal";
import { useToast } from "../../hooks/useToast";
import * as registryService from "../../services/registry/registryService";
import { 
  Building2, 
  Shield, 
  User as UserIcon, 
  Database, 
  Brain, 
  Cpu, 
  Plug, 
  GitBranch, 
  Link2, 
  CheckCircle2
} from "lucide-react";
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

import styles from "./RegisterAllWizardModal.module.css";

// Import Form Modals
// import { DepartmentFormModal } from "./DepartmentFormModal";
// import { RoleFormModal } from "./RoleFormModal";
// import { UserFormModal } from "./UserFormModal";
// import { DataSourceFormModal } from "./DataSourceFormModal";
// import { ModelFormModal } from "./ModelFormModal";
// import { AgentFormModal } from "./AgentFormModal";
// import { ToolFormModal } from "./ToolFormModal";
// import { WorkflowFormModal } from "./WorkflowFormModal";

interface RegisterAllWizardModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

const STEPS = [
  { key: "department", label: "Department", icon: Building2, desc: "Specify the department responsible for these assets." },
  { key: "role", label: "Roles", icon: Shield, desc: "Select or register the target role configuration." },
  { key: "user", label: "User", icon: UserIcon, desc: "Onboard the owner/approver for the assets." },
  { key: "data_source", label: "Data Source", icon: Database, desc: "Link the data pipelines and database schemas." },
  { key: "model", label: "AI Model", icon: Brain, desc: "Select or register the AI ML classification or LLM model." },
  { key: "agent", label: "AI Agent", icon: Cpu, desc: "Onboard the triage, execution, or monitoring agent." },
  { key: "tool", label: "Tools", icon: Plug, desc: "Link external webhook API operations or connectors." },
  { key: "relationships", label: "Relationships", icon: Link2, desc: "Review the automatically mapped connections." },
  { key: "workflow", label: "Workflows", icon: GitBranch, desc: "Name and save this entire interaction chain." }
];

const getEntityBadgeClass = (type: string) => {
  const t = type.toUpperCase();
  if (t === "MODEL") return "#a855f7";
  if (t === "AGENT") return "#ec4899";
  if (t === "TOOL") return "#eab308";
  if (t === "WORKFLOW") return "#3b82f6";
  if (t === "DATA_SOURCE") return "#14b8a6";
  if (t === "DEPARTMENT") return "#6366f1";
  if (t === "USER") return "#f97316";
  if (t === "ROLE") return "#8b5cf6";
  return "#64748b";
};

const CustomNode = ({ data }: any) => (
  <div style={{
    background: '#1e293b',
    border: `2px solid ${getEntityBadgeClass(data.typeText)}`,
    borderRadius: '8px',
    padding: '10px 15px',
    color: 'white',
    fontSize: '12px',
    fontWeight: 'bold',
    minWidth: '150px',
    textAlign: 'center',
    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.5)'
  }}>
    <div style={{ color: getEntityBadgeClass(data.typeText), fontSize: '10px', marginBottom: '4px', textTransform: 'uppercase' }}>
      {data.typeText}
    </div>
    <div title={data.label}>{data.label}</div>
    <Handle type="target" position={Position.Left} style={{ opacity: 0 }} />
    <Handle type="source" position={Position.Right} style={{ opacity: 0 }} />
  </div>
);

const nodeTypes = {
  custom: CustomNode,
};

export const RegisterAllWizardModal: React.FC<RegisterAllWizardModalProps> = ({
  isOpen,
  onClose,
  onSuccess
}) => {
  const { showToast } = useToast();
  const [activeStepIdx, setActiveStepIdx] = useState(0);

  // Wizard state: Selected entity IDs
  const [selectedIds, setSelectedIds] = useState<Record<string, string>>({
    department: "",
    role: "",
    user: "",
    data_source: "",
    model: "",
    agent: "",
    tool: "",
    workflow: ""
  });

  const [sessionName, setSessionName] = useState("");
  const [savingSession, setSavingSession] = useState(false);

  // Lists of lookups
  const [lookups, setLookups] = useState<Record<string, any[]>>({
    department: [],
    role: [],
    user: [],
    data_source: [],
    model: [],
    agent: [],
    tool: [],
    workflow: []
  });
  const [loadingLookups, setLoadingLookups] = useState<Record<string, boolean>>({});
  // const [activeCreateModal, setActiveCreateModal] = useState<string | null>(null);
  const [approverId, setApproverId] = useState("");

  const fetchLookup = async (key: string) => {
    setLoadingLookups(prev => ({ ...prev, [key]: true }));
    try {
      let data: any[] = [];
      if (key === "department") {
        const res = await registryService.getDepartmentsLookup();
        data = res.data || [];
      } else if (key === "role") {
        const res = await registryService.getRolesLookup();
        data = res.data || [];
      } else if (key === "user") {
        const res = await registryService.getUsersLookup();
        data = res.data || [];
      } else if (key === "data_source") {
        const res = await registryService.listDataSources({ page_size: 100 });
        data = res.data?.items || [];
      } else if (key === "model") {
        const res = await registryService.listModels({ page_size: 100 });
        data = res.data?.items || [];
      } else if (key === "agent") {
        const res = await registryService.listAgents({ page_size: 100 });
        data = res.data?.items || [];
      } else if (key === "tool") {
        const res = await registryService.listTools({ page_size: 100 });
        data = res.data?.items || [];
      } else if (key === "workflow") {
        const res = await registryService.listWorkflows({ page_size: 100 });
        data = res.data?.items || [];
      }
      setLookups(prev => ({ ...prev, [key]: data }));
    } catch (err) {
      console.error(`Failed to load lookup for ${key}:`, err);
    } finally {
      setLoadingLookups(prev => ({ ...prev, [key]: false }));
    }
  };

  useEffect(() => {
    if (isOpen) {
      STEPS.forEach(s => {
        if (s.key !== "relationships" && s.key !== "workflow") {
          fetchLookup(s.key);
        }
      });
      setSelectedIds({
        department: "",
        role: "",
        user: "",
        data_source: "",
        model: "",
        agent: "",
        tool: "",
        workflow: ""
      });
      setSessionName("");
      setActiveStepIdx(0);
    }
  }, [isOpen]);

  const activeStep = STEPS[activeStepIdx];

  const isStepCompleted = (stepKey: string) => {
    if (stepKey === "relationships" || stepKey === "workflow") return true; 
    return !!selectedIds[stepKey];
  };

  const isActiveStepValid = () => {
    if (activeStep.key === "relationships" || activeStep.key === "workflow") return true;
    return !!selectedIds[activeStep.key];
  };

  const isStepLocked = (idx: number) => {
    for (let i = 0; i < idx; i++) {
      if (!isStepCompleted(STEPS[i].key)) {
        return true;
      }
    }
    return false;
  };

  const handleStepClick = (idx: number) => {
    if (!isStepLocked(idx)) {
      setActiveStepIdx(idx);
    } else {
      showToast("Please complete preceding steps first.", "info");
    }
  };

  const handleNext = () => {
    if (isActiveStepValid()) {
      if (activeStepIdx < STEPS.length - 1) {
        setActiveStepIdx(prev => prev + 1);
      }
    }
  };

  const handleBack = () => {
    if (activeStepIdx > 0) {
      setActiveStepIdx(prev => prev - 1);
    }
  };

  // const handleModalSuccess = async (stepKey: string) => {
  //   const previousItems = lookups[stepKey] || [];
  //   const previousIds = new Set(previousItems.map(item => item.id));

  //   await fetchLookup(stepKey);

  //   setTimeout(() => {
  //     setLookups(currentLookups => {
  //       const list = currentLookups[stepKey] || [];
  //       const newlyAdded = list.find(item => !previousIds.has(item.id));
  //       if (newlyAdded) {
  //         setSelectedIds(prev => ({ ...prev, [stepKey]: newlyAdded.id }));
  //         showToast(`Newly registered ${STEPS.find(s => s.key === stepKey)?.label} selected automatically!`, "success");
  //       }
  //       return currentLookups;
  //     });
  //   }, 100);
  // };

  const getEntityName = (type: string, id: string) => {
    const key = type.toLowerCase() === "data_source" ? "data_source" : type.toLowerCase();
    const list = lookups[key] || [];
    const item = list.find(i => i.id === id);
    if (!item) return "Unknown";
    return item.department_name || item.role_name || item.full_name || item.source_name || item.model_name || item.agent_name || item.tool_name || item.workflow_name || "Unknown";
  };

  const handleSaveSession = async () => {
    if (!sessionName.trim()) {
      showToast("Please enter a name for this workflow session.", "info");
      return;
    }

    setSavingSession(true);
    try {
      if (!approverId) {
        showToast("Please select an approver.", "info");
        setSavingSession(false);
        return;
      }
      
      const wfPayload = {
        workflow_code: `WF-${Date.now().toString().slice(-6)}`,
        workflow_name: sessionName,
        workflow_type: "OPERATIONAL_ACTION",
        department_id: selectedIds.department || null,
        owner_user_id: selectedIds.user || null,
        approver_user_id: approverId,
        description: `Guided onboarding session: ${sessionName}`,
        approval_required: true,
        business_criticality: "HIGH",
        status: "DRAFT",
        metadata_json: {}
      };
      
      const wfRes = await registryService.createWorkflow(wfPayload);
      const newWfId = wfRes.data.id;

      const payload = {
        name: sessionName,
        department_id: selectedIds.department || null,
        role_id: selectedIds.role || null,
        user_id: selectedIds.user || null,
        data_source_id: selectedIds.data_source || null,
        model_id: selectedIds.model || null,
        agent_id: selectedIds.agent || null,
        tool_id: selectedIds.tool || null,
        workflow_id: newWfId
      };

      // Also create auto-mapped relationships
      const createRel = async (sourceType: string, sourceId: string, relType: string, targetType: string, targetId: string) => {
        if(sourceId && targetId) {
          try {
            await registryService.createRelationship({
              source_entity_type: sourceType,
              source_entity_id: sourceId,
              relationship_type: relType,
              target_entity_type: targetType,
              target_entity_id: targetId
            });
          } catch (err: any) {
            if (err.message && err.message.toLowerCase().includes("duplicate")) {
              console.log(`Relationship ${sourceType} -> ${targetType} already exists, continuing.`);
            } else {
              throw err;
            }
          }
        }
      };

      await createRel("DEPARTMENT", selectedIds.department, "HAS", "ROLE", selectedIds.role);
      await createRel("ROLE", selectedIds.role, "HAS", "USER", selectedIds.user);
      await createRel("USER", selectedIds.user, "OWNS", "WORKFLOW", newWfId);
      await createRel("WORKFLOW", newWfId, "USES", "AGENT", selectedIds.agent);
      await createRel("AGENT", selectedIds.agent, "USES", "MODEL", selectedIds.model);
      await createRel("AGENT", selectedIds.agent, "USES", "TOOL", selectedIds.tool);
      if(selectedIds.data_source) {
        await createRel("MODEL", selectedIds.model, "USES", "DATA_SOURCE", selectedIds.data_source);
      }

      const res = await registryService.createRegisterAll(payload);
      if (res.data) {
        showToast("Workflow and relationships saved successfully!", "success");
        onSuccess();
        onClose();
      }
    } catch (err: any) {
      showToast(err.message || "Failed to save workflow.", "error");
    } finally {
      setSavingSession(false);
    }
  };

  // Generate Graph Data
  const { graphNodes, graphEdges } = useMemo(() => {
    const nodes: Node[] = [];
    const edges: Edge[] = [];
    
    let xOffset = 50;
    const yCenter = 150;
    
    const addNodeAndEdge = (typeText: string, id: string, sourceNodeId: string | null = null, edgeLabel: string = "USES") => {
      if (!id) return null;
      const nodeId = `node_${typeText}`;
      nodes.push({
        id: nodeId,
        type: "custom",
        position: { x: xOffset, y: yCenter },
        data: { label: getEntityName(typeText, id), typeText }
      });
      xOffset += 250;
      
      if (sourceNodeId) {
        edges.push({
          id: `e_${sourceNodeId}_${nodeId}`,
          source: sourceNodeId,
          target: nodeId,
          label: edgeLabel,
          animated: true,
          style: { stroke: '#0ea5e9', strokeWidth: 2 },
          markerEnd: { type: MarkerType.ArrowClosed, color: '#0ea5e9' },
          labelStyle: { fill: '#fff', fontWeight: 600, fontSize: 11 },
          labelBgStyle: { fill: '#0b1120', stroke: '#1e293b', strokeWidth: 1 }
        });
      }
      return nodeId;
    };

    const deptId = addNodeAndEdge("DEPARTMENT", selectedIds.department);
    const roleId = addNodeAndEdge("ROLE", selectedIds.role, deptId, "HAS");
    const userId = addNodeAndEdge("USER", selectedIds.user, roleId, "HAS");
    const agentId = addNodeAndEdge("AGENT", selectedIds.agent, userId, "OWNS");
    
    if (agentId) {
      // Split model and tool
      if (selectedIds.model) {
        const modelNodeId = `node_MODEL`;
        nodes.push({
          id: modelNodeId,
          type: "custom",
          position: { x: xOffset, y: yCenter - 80 },
          data: { label: getEntityName("MODEL", selectedIds.model), typeText: "MODEL" }
        });
        edges.push({
          id: `e_${agentId}_${modelNodeId}`,
          source: agentId,
          target: modelNodeId,
          label: "USES",
          animated: true,
          style: { stroke: '#0ea5e9', strokeWidth: 2 },
          markerEnd: { type: MarkerType.ArrowClosed, color: '#0ea5e9' },
          labelStyle: { fill: '#fff', fontWeight: 600, fontSize: 11 },
          labelBgStyle: { fill: '#0b1120', stroke: '#1e293b', strokeWidth: 1 }
        });
        
        if (selectedIds.data_source) {
          const dsNodeId = `node_DATA_SOURCE`;
          nodes.push({
            id: dsNodeId,
            type: "custom",
            position: { x: xOffset + 250, y: yCenter - 80 },
            data: { label: getEntityName("DATA_SOURCE", selectedIds.data_source), typeText: "DATA_SOURCE" }
          });
          edges.push({
            id: `e_${modelNodeId}_${dsNodeId}`,
            source: modelNodeId,
            target: dsNodeId,
            label: "READS",
            animated: true,
            style: { stroke: '#0ea5e9', strokeWidth: 2 },
            markerEnd: { type: MarkerType.ArrowClosed, color: '#0ea5e9' },
            labelStyle: { fill: '#fff', fontWeight: 600, fontSize: 11 },
            labelBgStyle: { fill: '#0b1120', stroke: '#1e293b', strokeWidth: 1 }
          });
        }
      }
      
      if (selectedIds.tool) {
        const toolNodeId = `node_TOOL`;
        nodes.push({
          id: toolNodeId,
          type: "custom",
          position: { x: xOffset, y: yCenter + 80 },
          data: { label: getEntityName("TOOL", selectedIds.tool), typeText: "TOOL" }
        });
        edges.push({
          id: `e_${agentId}_${toolNodeId}`,
          source: agentId,
          target: toolNodeId,
          label: "EXECUTES",
          animated: true,
          style: { stroke: '#0ea5e9', strokeWidth: 2 },
          markerEnd: { type: MarkerType.ArrowClosed, color: '#0ea5e9' },
          labelStyle: { fill: '#fff', fontWeight: 600, fontSize: 11 },
          labelBgStyle: { fill: '#0b1120', stroke: '#1e293b', strokeWidth: 1 }
        });
      }
    }

    return { graphNodes: nodes, graphEdges: edges };
  }, [selectedIds, lookups]);

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Guided Registry Onboarding (Register All)"
      size="xl"
    >
      <div className={styles.container}>
        <div className={styles.stepperHeader}>
          {STEPS.map((s, idx) => {
            const StepIcon = s.icon;
            const completed = isStepCompleted(s.key);
            const active = idx === activeStepIdx;
            const locked = isStepLocked(idx);

            let nodeClass = styles.stepNode;
            if (completed) nodeClass += ` ${styles.stepCompleted}`;
            if (active) nodeClass += ` ${styles.stepActive}`;
            if (locked) nodeClass += ` ${styles.stepLocked}`;

            return (
              <React.Fragment key={s.key}>
                {idx > 0 && (
                  <div 
                    className={`${styles.stepConnector} ${!locked ? styles.stepConnectorActive : ""}`} 
                  />
                )}
                <button
                  type="button"
                  className={nodeClass}
                  onClick={() => handleStepClick(idx)}
                  disabled={locked}
                  title={s.label}
                >
                  <div className={styles.stepIconWrapper}>
                    <StepIcon size={18} />
                  </div>
                  <span className={styles.stepLabel}>{s.label}</span>
                </button>
              </React.Fragment>
            );
          })}
        </div>

        <div className={styles.stepCard}>
          <div className={styles.stepTitleSection}>
            <h3 className={styles.stepTitle}>{activeStep.label}</h3>
            <p className={styles.stepDescription}>{activeStep.desc}</p>
          </div>

          {activeStep.key !== "relationships" && activeStep.key !== "workflow" ? (
            <div className={styles.splitContainer}>
              <div className={`${styles.optionColumn} ${selectedIds[activeStep.key] ? styles.optionColumnActive : ""}`}>
                <h4 className={styles.optionColumnTitle}>Choose Existing</h4>
                <div className={styles.selectWrapper}>
                  <select
                    className={styles.selectInput}
                    value={selectedIds[activeStep.key]}
                    onChange={(e) => setSelectedIds(prev => ({ ...prev, [activeStep.key]: e.target.value }))}
                    disabled={loadingLookups[activeStep.key]}
                  >
                    <option value="">-- Select {activeStep.label} --</option>
                    {lookups[activeStep.key]?.map((item: any) => {
                      const name = item.department_name || item.role_name || item.full_name || item.source_name || item.model_name || item.agent_name || item.tool_name || item.workflow_name || "Unnamed";
                      const code = item.department_code || item.role_code || item.email || item.source_code || item.model_code || item.agent_code || item.tool_code || item.workflow_code || "";
                      return (
                        <option key={item.id} value={item.id}>
                          {name} {code ? `(${code})` : ""}
                        </option>
                      );
                    })}
                  </select>
                </div>
                {selectedIds[activeStep.key] && (
                  <div className={styles.selectionStatusInfo}>
                    <CheckCircle2 size={16} />
                    <span>Selected: {getEntityName(activeStep.key, selectedIds[activeStep.key])}</span>
                  </div>
                )}
              </div>

              {/* <div className={styles.optionColumn}>
                <h4 className={styles.optionColumnTitle}>Register New</h4>
                <button
                  type="button"
                  className={styles.createButton}
                  onClick={() => setActiveCreateModal(activeStep.key)}
                >
                  <Plus size={16} />
                  <span>Register {activeStep.label}</span>
                </button>
              </div> */}
            </div>
          ) : activeStep.key === "relationships" ? (
            <div style={{ width: '100%', height: '350px', background: '#0b1120', borderRadius: '8px', border: '1px solid #1e293b' }}>
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
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              <div style={{ width: '100%', height: '200px', background: '#0b1120', borderRadius: '8px', border: '1px solid #1e293b' }}>
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
                </ReactFlow>
              </div>
              <div className={styles.saveInputGroup} style={{ maxWidth: '400px', margin: '0 auto', width: '100%' }}>
                <label style={{ fontSize: "0.82rem", fontWeight: "600", marginBottom: "8px", display: "block" }}> Workflow Session Name <span style={{ color: "#ef4444" }}>*</span></label>
                <input
                  type="text"
                  className={styles.saveInput}
                  placeholder="Enter onboarding session name..."
                  value={sessionName}
                  onChange={(e) => setSessionName(e.target.value)}
                  style={{ width: "100%", padding: "10px", borderRadius: "6px", border: "1px solid #334155", background: "#1e293b", color: "white", marginBottom: "16px" }}
                />
                
                <label style={{ fontSize: "0.82rem", fontWeight: "600", marginBottom: "8px", display: "block" }}> Assigned Approver <span style={{ color: "#ef4444" }}>*</span></label>
                <select
                  className={styles.selectInput}
                  value={approverId}
                  onChange={(e) => setApproverId(e.target.value)}
                  disabled={loadingLookups["user"]}
                  style={{ width: "100%", padding: "10px", borderRadius: "6px", border: "1px solid #334155", background: "#1e293b", color: "white" }}
                >
                  <option value="">-- Select Approver --</option>
                  {lookups["user"]?.map((item: any) => (
                    <option key={item.id} value={item.id}>
                      {item.full_name} ({item.email})
                    </option>
                  ))}
                </select>
              </div>
            </div>
          )}

          <div className={styles.stepperControls}>
            <button
              type="button"
              className={styles.backBtn}
              onClick={handleBack}
              disabled={activeStepIdx === 0}
            >
              Back
            </button>

            {activeStep.key !== "workflow" ? (
              <button
                type="button"
                className={styles.nextBtn}
                onClick={handleNext}
                disabled={!isActiveStepValid()}
              >
                Next
              </button>
            ) : (
              <button
                type="button"
                className={styles.nextBtn}
                onClick={handleSaveSession}
                disabled={savingSession || !sessionName.trim()}
                style={{ background: "#10b981" }}
              >
                {savingSession ? "Saving..." : "Save & Complete Workflow"}
              </button>
            )}
          </div>
        </div>
      </div>
    </Modal>
  );
};

export default RegisterAllWizardModal;

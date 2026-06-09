/* src/components/registry/RegisterAllWizardModal.tsx */

import React, { useState, useEffect } from "react";
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
  Plus, 
  CheckCircle2, 
  Trash2 
} from "lucide-react";
import styles from "./RegisterAllWizardModal.module.css";

// Import Form Modals
import { DepartmentFormModal } from "./DepartmentFormModal";
import { RoleFormModal } from "./RoleFormModal";
import { UserFormModal } from "./UserFormModal";
import { DataSourceFormModal } from "./DataSourceFormModal";
import { ModelFormModal } from "./ModelFormModal";
import { AgentFormModal } from "./AgentFormModal";
import { ToolFormModal } from "./ToolFormModal";
import { WorkflowFormModal } from "./WorkflowFormModal";

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
  { key: "workflow", label: "Workflows", icon: GitBranch, desc: "Assemble the execution workflow steps." },
  { key: "relationships", label: "Relationships", icon: Link2, desc: "Map connections between your selected assets." }
];

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

  // Wizard state: Session name
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

  // Control for individual create modals
  const [activeCreateModal, setActiveCreateModal] = useState<string | null>(null);

  // State to track relationships created during this session
  const [createdRels, setCreatedRels] = useState<any[]>([]);
  const [relSourceType, setRelSourceType] = useState("");
  const [relType, setRelType] = useState("USES");
  const [relTargetType, setRelTargetType] = useState("");
  const [addingRel, setAddingRel] = useState(false);

  // Load active lists for the dropdowns
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

  // Load initial lookups
  useEffect(() => {
    if (isOpen) {
      STEPS.forEach(s => {
        if (s.key !== "relationships") {
          fetchLookup(s.key);
        }
      });
      // Reset state
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
      setCreatedRels([]);
      setSessionName("");
      setActiveStepIdx(0);
    }
  }, [isOpen]);

  const activeStep = STEPS[activeStepIdx];

  // Check if a step is completed
  const isStepCompleted = (stepKey: string) => {
    if (stepKey === "relationships") return true; // Optional/always complete
    return !!selectedIds[stepKey];
  };

  // Check if we can proceed/if active step is valid
  const isActiveStepValid = () => {
    if (activeStep.key === "relationships") return true;
    return !!selectedIds[activeStep.key];
  };

  // Determine if a specific step index is locked
  const isStepLocked = (idx: number) => {
    // A step is locked if any preceding step is not completed
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

  // Handle successful registration from creation modals
  const handleModalSuccess = async (stepKey: string) => {
    const previousItems = lookups[stepKey] || [];
    const previousIds = new Set(previousItems.map(item => item.id));

    // Reload list
    await fetchLookup(stepKey);

    // Find the newly added element
    setTimeout(() => {
      setLookups(currentLookups => {
        const list = currentLookups[stepKey] || [];
        const newlyAdded = list.find(item => !previousIds.has(item.id));
        if (newlyAdded) {
          setSelectedIds(prev => ({ ...prev, [stepKey]: newlyAdded.id }));
          showToast(`Newly registered ${STEPS.find(s => s.key === stepKey)?.label} selected automatically!`, "success");
        }
        return currentLookups;
      });
    }, 100);
  };

  // Handle relationship creation
  const handleAddRelationship = async () => {
    if (!relSourceType || !relTargetType || !relType) {
      showToast("Please select all fields to map relationship.", "info");
      return;
    }

    const sourceId = selectedIds[relSourceType.toLowerCase()];
    const targetId = selectedIds[relTargetType.toLowerCase()];

    if (!sourceId || !targetId) {
      showToast("One of the selected assets is invalid.", "error");
      return;
    }

    if (sourceId === targetId) {
      showToast("Cannot link an entity to itself.", "info");
      return;
    }

    setAddingRel(true);
    try {
      const payload = {
        source_entity_type: relSourceType,
        source_entity_id: sourceId,
        relationship_type: relType,
        target_entity_type: relTargetType,
        target_entity_id: targetId
      };
      const res = await registryService.createRelationship(payload);
      if (res.data) {
        const sourceName = getEntityName(relSourceType, sourceId);
        const targetName = getEntityName(relTargetType, targetId);

        setCreatedRels(prev => [
          ...prev,
          {
            id: res.data.id,
            sourceType: relSourceType,
            sourceId,
            sourceName,
            type: relType,
            targetType: relTargetType,
            targetId,
            targetName
          }
        ]);
        showToast("Relationship mapped successfully!", "success");
        setRelSourceType("");
        setRelTargetType("");
      }
    } catch (err: any) {
      showToast(err.message || "Failed to create relationship.", "error");
    } finally {
      setAddingRel(false);
    }
  };

  const handleRemoveRelationship = async (relId: string) => {
    try {
      await registryService.deleteRelationship(relId);
      setCreatedRels(prev => prev.filter(r => r.id !== relId));
      showToast("Relationship removed.", "success");
    } catch (err: any) {
      showToast(err.message || "Failed to delete relationship.", "error");
    }
  };

  // Get name of selected entity
  const getEntityName = (type: string, id: string) => {
    const key = type.toLowerCase() === "data_source" ? "data_source" : type.toLowerCase();
    const list = lookups[key] || [];
    const item = list.find(i => i.id === id);
    if (!item) return "Unknown";
    return item.department_name || item.role_name || item.full_name || item.source_name || item.model_name || item.agent_name || item.tool_name || item.workflow_name || "Unknown";
  };

  // Complete guided onboarding session
  const handleSaveSession = async () => {
    if (!sessionName.trim()) {
      showToast("Please enter a name for this onboarding session.", "info");
      return;
    }

    setSavingSession(true);
    try {
      const payload = {
        name: sessionName,
        department_id: selectedIds.department || null,
        role_id: selectedIds.role || null,
        user_id: selectedIds.user || null,
        data_source_id: selectedIds.data_source || null,
        model_id: selectedIds.model || null,
        agent_id: selectedIds.agent || null,
        tool_id: selectedIds.tool || null,
        workflow_id: selectedIds.workflow || null
      };

      const res = await registryService.createRegisterAll(payload);
      if (res.data) {
        showToast("Guided onboarding session saved successfully!", "success");
        onSuccess();
        onClose();
      }
    } catch (err: any) {
      showToast(err.message || "Failed to save session.", "error");
    } finally {
      setSavingSession(false);
    }
  };

  // Relationship dropdown options filtered by selection status
  const relSourceOptions = [
    { key: "DEPARTMENT", label: "Department", value: selectedIds.department },
    { key: "ROLE", label: "Role", value: selectedIds.role },
    { key: "USER", label: "User", value: selectedIds.user },
    { key: "DATA_SOURCE", label: "Data Source", value: selectedIds.data_source },
    { key: "MODEL", label: "AI Model", value: selectedIds.model },
    { key: "AGENT", label: "AI Agent", value: selectedIds.agent },
    { key: "TOOL", label: "Tool", value: selectedIds.tool },
    { key: "WORKFLOW", label: "Workflow", value: selectedIds.workflow }
  ].filter(o => !!o.value);

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Guided Registry Onboarding (Register All)"
      size="xl"
    >
      <div className={styles.container}>
        {/* Progress Stepper icons */}
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

        {/* Step Card Content */}
        <div className={styles.stepCard}>
          <div className={styles.stepTitleSection}>
            <h3 className={styles.stepTitle}>{activeStep.label}</h3>
            <p className={styles.stepDescription}>{activeStep.desc}</p>
          </div>

          {activeStep.key !== "relationships" ? (
            /* Standard Stepper Step - Choose Existing or Create New */
            <div className={styles.splitContainer}>
              {/* Option A: Select Existing */}
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

              {/* Option B: Create New */}
              <div className={styles.optionColumn}>
                <h4 className={styles.optionColumnTitle}>Register New</h4>
                <button
                  type="button"
                  className={styles.createButton}
                  onClick={() => setActiveCreateModal(activeStep.key)}
                >
                  <Plus size={16} />
                  <span>Register {activeStep.label}</span>
                </button>
              </div>
            </div>
          ) : (
            /* Relationships and Saving Step */
            <div className={styles.relationshipContainer}>
              <div className={styles.splitContainer}>
                {/* Column A: Map Relationship Form */}
                <div className={styles.optionColumn} style={{ justifyContent: "flex-start", gap: "10px" }}>
                  <h4 className={styles.optionColumnTitle}>Link Assets</h4>
                  
                  <div style={{ width: "100%", display: "flex", flexDirection: "column", gap: "6px" }}>
                    <label style={{ fontSize: "0.8rem", fontWeight: "600" }}>Source Asset</label>
                    <select
                      className={styles.selectInput}
                      value={relSourceType}
                      onChange={(e) => setRelSourceType(e.target.value)}
                    >
                      <option value="">-- Choose Source --</option>
                      {relSourceOptions.map(opt => (
                        <option key={opt.key} value={opt.key}>{opt.label}</option>
                      ))}
                    </select>
                  </div>

                  <div style={{ width: "100%", display: "flex", flexDirection: "column", gap: "6px" }}>
                    <label style={{ fontSize: "0.8rem", fontWeight: "600" }}>Relationship Type</label>
                    <select
                      className={styles.selectInput}
                      value={relType}
                      onChange={(e) => setRelType(e.target.value)}
                    >
                      <option value="USES">USES</option>
                      <option value="OWNS">OWNS</option>
                      <option value="EXECUTES">EXECUTES</option>
                      <option value="GOVERNED_BY">GOVERNED_BY</option>
                      <option value="CONNECTED_TO">CONNECTED_TO</option>
                    </select>
                  </div>

                  <div style={{ width: "100%", display: "flex", flexDirection: "column", gap: "6px" }}>
                    <label style={{ fontSize: "0.8rem", fontWeight: "600" }}>Target Asset</label>
                    <select
                      className={styles.selectInput}
                      value={relTargetType}
                      onChange={(e) => setRelTargetType(e.target.value)}
                    >
                      <option value="">-- Choose Target --</option>
                      {relSourceOptions.map(opt => (
                        <option key={opt.key} value={opt.key}>{opt.label}</option>
                      ))}
                    </select>
                  </div>

                  <button
                    type="button"
                    className={styles.createButton}
                    onClick={handleAddRelationship}
                    disabled={addingRel || !relSourceType || !relTargetType}
                    style={{ width: "100%", marginTop: "10px", justifyContent: "center" }}
                  >
                    {addingRel ? "Mapping..." : "+ Map Relationship"}
                  </button>
                </div>

                {/* Column B: Created Relationships List */}
                <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                  <h4 style={{ fontSize: "0.95rem", fontWeight: "600" }}>Relationships Formed</h4>
                  <div className={styles.relationshipList}>
                    {createdRels.length === 0 ? (
                      <div className={styles.noRelationshipsText}>
                        No relationships established yet. You can create links above or click Next to save.
                      </div>
                    ) : (
                      createdRels.map(rel => (
                        <div key={rel.id} className={styles.relationshipRow}>
                          <div className={styles.relationshipText}>
                            <span className={styles.entityBadge}>{rel.sourceType}</span>
                            <span>{rel.sourceName}</span>
                            <span className={styles.relTypeBadge}>{rel.type}</span>
                            <span className={styles.entityBadge}>{rel.targetType}</span>
                            <span>{rel.targetName}</span>
                          </div>
                          <button
                            type="button"
                            className={styles.removeRelBtn}
                            onClick={() => handleRemoveRelationship(rel.id)}
                            title="Remove Relationship"
                          >
                            <Trash2 size={14} />
                          </button>
                        </div>
                      ))
                    )}
                  </div>

                  {/* Save Session Section */}
                  <div className={styles.saveInputGroup}>
                    <label style={{ fontSize: "0.82rem", fontWeight: "600" }}> guided onboarding Session Name <span style={{ color: "#ef4444" }}>*</span></label>
                    <input
                      type="text"
                      className={styles.saveInput}
                      placeholder="e.g. Clinical NLP Pipeline Onboarding"
                      value={sessionName}
                      onChange={(e) => setSessionName(e.target.value)}
                    />
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Stepper Controls */}
          <div className={styles.stepperControls}>
            <button
              type="button"
              className={styles.backBtn}
              onClick={handleBack}
              disabled={activeStepIdx === 0}
            >
              Back
            </button>

            {activeStep.key !== "relationships" ? (
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
                {savingSession ? "Saving..." : "Save & Complete Onboarding"}
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Embedded Creation Modals */}
      <DepartmentFormModal
        isOpen={activeCreateModal === "department"}
        onClose={() => setActiveCreateModal(null)}
        deptId={null}
        onSuccess={() => handleModalSuccess("department")}
      />
      <RoleFormModal
        isOpen={activeCreateModal === "role"}
        onClose={() => setActiveCreateModal(null)}
        roleId={null}
        onSuccess={() => handleModalSuccess("role")}
      />
      <UserFormModal
        isOpen={activeCreateModal === "user"}
        onClose={() => setActiveCreateModal(null)}
        userId={null}
        onSuccess={() => handleModalSuccess("user")}
        defaultDepartmentId={selectedIds.department || null}
        defaultRoleId={selectedIds.role || null}
      />
      <DataSourceFormModal
        isOpen={activeCreateModal === "data_source"}
        onClose={() => setActiveCreateModal(null)}
        sourceId={null}
        onSuccess={() => handleModalSuccess("data_source")}
        defaultDepartmentId={selectedIds.department || null}
        defaultUserId={selectedIds.user || null}
      />
      <ModelFormModal
        isOpen={activeCreateModal === "model"}
        onClose={() => setActiveCreateModal(null)}
        modelId={null}
        onSuccess={() => handleModalSuccess("model")}
        defaultDepartmentId={selectedIds.department || null}
        defaultUserId={selectedIds.user || null}
      />
      <AgentFormModal
        isOpen={activeCreateModal === "agent"}
        onClose={() => setActiveCreateModal(null)}
        agentId={null}
        onSuccess={() => handleModalSuccess("agent")}
        defaultDepartmentId={selectedIds.department || null}
        defaultUserId={selectedIds.user || null}
      />
      <ToolFormModal
        isOpen={activeCreateModal === "tool"}
        onClose={() => setActiveCreateModal(null)}
        toolId={null}
        onSuccess={() => handleModalSuccess("tool")}
        defaultUserId={selectedIds.user || null}
      />
      <WorkflowFormModal
        isOpen={activeCreateModal === "workflow"}
        onClose={() => setActiveCreateModal(null)}
        workflowId={null}
        onSuccess={() => handleModalSuccess("workflow")}
        defaultDepartmentId={selectedIds.department || null}
        defaultUserId={selectedIds.user || null}
      />
    </Modal>
  );
};

/* src/components/registry/AddRelationshipModal.tsx */

import React, { useEffect, useState } from "react";
import { Modal } from "../common/Modal";
import { useToast } from "../../hooks/useToast";
import * as registryService from "../../services/registry/registryService";
import WizardShell from "../common/WizardShell";
import styles from "./AddRelationshipModal.module.css";

import { FieldInfo } from "../common/FieldInfo";

interface AddRelationshipModalProps {
  isOpen: boolean;
  onClose: () => void;
  sourceEntityType: string;
  sourceEntityId: string;
  onSuccess: () => void;
}

// Map the strict backend ALLOWED_RELATIONSHIPS combinations
const PERMITTED_COMBINATIONS: Record<string, { rel: string; target: string }[]> = {
  MODEL: [
    { rel: "USES", target: "DATA_SOURCE" },
    { rel: "USES", target: "TOOL" }
  ],
  AGENT: [
    { rel: "USES", target: "TOOL" },
    { rel: "USES", target: "MODEL" },
    { rel: "EXECUTES", target: "WORKFLOW" }
  ],
  WORKFLOW: [
    { rel: "USES", target: "DATA_SOURCE" },
    { rel: "USES", target: "TOOL" },
    { rel: "GOVERNED_BY", target: "DEPARTMENT" }
  ],
  USER: [
    { rel: "OWNS", target: "ROLE" }
  ],
  DEPARTMENT: [
    { rel: "GOVERNED_BY", target: "USER" }
  ]
};

const NORMALIZE_TYPE: Record<string, string> = {
  AGENTS: "AGENT",
  MODELS: "MODEL",
  WORKFLOWS: "WORKFLOW",
  TOOLS: "TOOL",
  DATA_SOURCES: "DATA_SOURCE",
  DEPARTMENTS: "DEPARTMENT",
  USERS: "USER",
  ROLES: "ROLE"
};

export const AddRelationshipModal: React.FC<AddRelationshipModalProps> = ({
  isOpen,
  onClose,
  sourceEntityType,
  sourceEntityId,
  onSuccess
}) => {
  const { showToast } = useToast();
  
  // Normalize plural type to singular (e.g., 'agents' -> 'AGENT')
  const normalizedSourceType = NORMALIZE_TYPE[sourceEntityType.toUpperCase()] || sourceEntityType.toUpperCase();
  
  // Available combinations based on source type
  const allowedOptions = PERMITTED_COMBINATIONS[normalizedSourceType] || [];
  
  // Form State
  const [currentWizardStep, setCurrentWizardStep] = useState(0);
  
  // Step 1 State
  const [relationshipType, setRelationshipType] = useState("");
  const [targetEntityType, setTargetEntityType] = useState("");
  const [targetEntityId, setTargetEntityId] = useState("");
  
  // Step 2 State
  const [relationshipScope, setRelationshipScope] = useState("");
  const [responsibilityType, setResponsibilityType] = useState("");
  const [effectiveFrom, setEffectiveFrom] = useState("");
  const [effectiveTo, setEffectiveTo] = useState("");
  
  // Step 3 State
  const [metadataJson, setMetadataJson] = useState("");
  const [isMetadataJsonValid, setIsMetadataJsonValid] = useState(true);
  
  // Lookups lists
  const [targetsList, setTargetsList] = useState<{ id: string; label: string }[]>([]);
  const [loadingTargets, setLoadingTargets] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [generalError, setGeneralError] = useState<string | null>(null);

  // Derive target entity type list from combinations
  const targetTypes = Array.from(new Set(allowedOptions.map(opt => opt.target)));

  // Derive relationship type choices based on selected target type
  const relTypes = allowedOptions
    .filter(opt => !targetEntityType || opt.target === targetEntityType)
    .map(opt => opt.rel);

  const wizardSteps = [
    { label: "Identity & Action" },
    { label: "Attributes & Lifespans" },
    { label: "Configurations & Review" }
  ];

  const validateAndAdvance = (targetStep: number) => {
    if (targetStep > currentWizardStep) {
      if (currentWizardStep === 0) {
        if (!relationshipType || !targetEntityType || !targetEntityId) {
          showToast("Please fill in all required target and action fields", "error");
          return;
        }
      }
      if (currentWizardStep === 1) {
        if (effectiveFrom && effectiveTo && new Date(effectiveFrom) >= new Date(effectiveTo)) {
          showToast("Effective To date must be after Effective From date", "error");
          return;
        }
      }
    }
    setCurrentWizardStep(targetStep);
  };

  // Validate metadataJson valid JSON
  useEffect(() => {
    if (!metadataJson.trim()) {
      setIsMetadataJsonValid(true);
      return;
    }
    try {
      JSON.parse(metadataJson);
      setIsMetadataJsonValid(true);
    } catch {
      setIsMetadataJsonValid(false);
    }
  }, [metadataJson]);

  // Handle Target Entity Type Change
  useEffect(() => {
    if (isOpen) {
      if (allowedOptions.length > 0) {
        // Pre-select target type if only one option exists
        const targets = Array.from(new Set(allowedOptions.map(opt => opt.target)));
        if (targets.length === 1) {
          setTargetEntityType(targets[0]);
        }
      }
    }
  }, [isOpen, sourceEntityType]);

  // Handle Relationship Type pre-selection
  useEffect(() => {
    if (targetEntityType) {
      const filteredRels = allowedOptions.filter(opt => opt.target === targetEntityType);
      if (filteredRels.length === 1) {
        setRelationshipType(filteredRels[0].rel);
      } else {
        setRelationshipType("");
      }
      setTargetEntityId("");
      fetchTargetEntities(targetEntityType);
    } else {
      setRelationshipType("");
      setTargetEntityId("");
      setTargetsList([]);
    }
  }, [targetEntityType]);

  const fetchTargetEntities = async (type: string) => {
    setLoadingTargets(true);
    setTargetsList([]);
    try {
      const tType = type.toUpperCase();
      let listData: { id: string; label: string }[] = [];
      
      if (tType === "USER") {
        const res = await registryService.getUsersLookup();
        if (res.data) listData = res.data.map(u => ({ id: u.id, label: `${u.full_name} (${u.email})` }));
      } else if (tType === "DEPARTMENT") {
        const res = await registryService.getDepartmentsLookup();
        if (res.data) listData = res.data.map(d => ({ id: d.id, label: `${d.department_name} (${d.department_code})` }));
      } else if (tType === "ROLE") {
        const res = await registryService.getRolesLookup();
        if (res.data) listData = res.data.map(r => ({ id: r.id, label: `${r.role_name} (${r.role_code})` }));
      } else if (tType === "MODEL") {
        const res = await registryService.listModels({ per_page: 100 });
        if (res.data?.items) listData = res.data.items.map(m => ({ id: m.id, label: `${m.model_name}${m.model_version ? ` (v${m.model_version})` : ''}` }));
      } else if (tType === "AGENT") {
        const res = await registryService.listAgents({ per_page: 100 });
        if (res.data?.items) listData = res.data.items.map(a => ({ id: a.id, label: `${a.agent_name} (${a.agent_type})` }));
      } else if (tType === "TOOL") {
        const res = await registryService.listTools({ per_page: 100 });
        if (res.data?.items) listData = res.data.items.map(t => ({ id: t.id, label: `${t.tool_name} (${t.tool_category})` }));
      } else if (tType === "WORKFLOW") {
        const res = await registryService.listWorkflows({ per_page: 100 });
        if (res.data?.items) listData = res.data.items.map(w => ({ id: w.id, label: `${w.workflow_name} (${w.workflow_type})` }));
      } else if (tType === "DATA_SOURCE") {
        const res = await registryService.listDataSources({ per_page: 100 });
        if (res.data?.items) listData = res.data.items.map(s => ({ id: s.id, label: `${s.source_name} [${s.classification}]` }));
      }

      // Self-exclusion just in case we link same entity type
      setTargetsList(listData.filter(item => item.id !== sourceEntityId));
    } catch (err: any) {
      console.error(`Failed to load target entities for ${type}:`, err);
      showToast(`Failed to load target entities for ${type}`, "error");
    } finally {
      setLoadingTargets(false);
    }
  };

  const mapToBackendType = (type: string): string => {
    const t = type.toUpperCase();
    if (t === "AGENT" || t === "AGENTS") return "agents";
    if (t === "MODEL" || t === "AI_MODELS") return "ai_models";
    if (t === "TOOL" || t === "TOOLS") return "tools";
    if (t === "WORKFLOW" || t === "WORKFLOWS") return "workflows";
    if (t === "DATA_SOURCE" || t === "DATA_SOURCES") return "data_sources";
    if (t === "DEPARTMENT" || t === "DEPARTMENTS") return "departments";
    if (t === "USER" || t === "USERS") return "users";
    return type.toLowerCase();
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!relationshipType || !targetEntityType || !targetEntityId) {
      showToast("Please fill in all required relationship fields", "error");
      return;
    }
    if (!isMetadataJsonValid) {
      showToast("Please fix the metadata JSON configuration", "error");
      return;
    }

    setSubmitting(true);
    setGeneralError(null);

    const payload = {
      source_type: mapToBackendType(sourceEntityType),
      source_id: sourceEntityId,
      target_type: mapToBackendType(targetEntityType),
      target_id: targetEntityId,
      relationship_type: relationshipType.toLowerCase(),
      relationship_scope: relationshipScope || null,
      responsibility_type: responsibilityType || null,
      effective_from: effectiveFrom ? new Date(effectiveFrom).toISOString() : null,
      effective_to: effectiveTo ? new Date(effectiveTo).toISOString() : null,
      metadata_json: metadataJson ? JSON.parse(metadataJson) : null
    };

    try {
      const res = await registryService.createRelationship(payload);
      const reqIdText = res?.request_id ? ` (Request ID: ${res.request_id})` : '';
      showToast(`Relationship connection established${reqIdText}`, "success");
      onSuccess();
      onClose();
    } catch (err: any) {
      setGeneralError(err.message || "Failed to create relationship link.");
      showToast(err.message || "Failed to establish link", "error");
    } finally {
      setSubmitting(false);
    }
  };

  const formatEntityLabel = (type: string) => {
    return type.replace("_", " ");
  };

  // Reset form when modal state closes/opens
  useEffect(() => {
    if (!isOpen) {
      setRelationshipType("");
      setTargetEntityType("");
      setTargetEntityId("");
      setTargetsList([]);
      setRelationshipScope("");
      setResponsibilityType("");
      setEffectiveFrom("");
      setEffectiveTo("");
      setMetadataJson("");
      setIsMetadataJsonValid(true);
      setCurrentWizardStep(0);
      setGeneralError(null);
    }
  }, [isOpen]);

  const hasAllowedLinkages = allowedOptions.length > 0;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={`Create Connection Link`}
      size="lg"
    >
      <div className={styles.container}>
        {generalError && <div className={styles.generalAlert}>{generalError}</div>}

        {!hasAllowedLinkages ? (
          <div className={styles.noticeBlock}>
            <p>
              ⚠️ **Target-Only Governance Entity**:
              The selected entity type <strong>{formatEntityLabel(sourceEntityType)}</strong> does not support outgoing links. 
            </p>
            <p className={styles.subNotice}>
              To establish linkages, please configure them from their source elements, such as connecting AI Models to this {formatEntityLabel(sourceEntityType).toLowerCase()}.
            </p>
            <div className={styles.formActions}>
              <button type="button" onClick={onClose} className={styles.cancelBtn}>
                Close
              </button>
            </div>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className={styles.form}>
            <WizardShell
              steps={wizardSteps}
              currentStep={currentWizardStep}
              onStepClick={validateAndAdvance}
              mode="strict"
            >
              {/* STEP 1: Identity & Action */}
              {currentWizardStep === 0 && (
                <div>
                  <p className={styles.infoText}>
                    Select target entity and relationship action to link from this <strong>{formatEntityLabel(sourceEntityType)}</strong>.
                  </p>

                  {/* Target Entity Type */}
                  <div className={styles.formGroup}>
                    <label htmlFor="targetEntityType" className={styles.label}>
                      Target Entity Type <span className={styles.required}>*</span>
                      <FieldInfo 
                        tooltip="The type of entity you want to connect to." 
                        format="Selection list of permitted entities"
                        example="DATA_SOURCE"
                      />
                    </label>
                    <select
                      id="targetEntityType"
                      value={targetEntityType}
                      onChange={(e) => setTargetEntityType(e.target.value)}
                      disabled={submitting}
                      className={styles.select}
                      required
                    >
                      <option value="">-- Choose Target Type --</option>
                      {targetTypes.map((type) => (
                        <option key={type} value={type}>
                          {type}
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Relationship Type */}
                  <div className={styles.formGroup}>
                    <label htmlFor="relationshipType" className={styles.label}>
                      Relationship Action <span className={styles.required}>*</span>
                      <FieldInfo 
                        tooltip="The nature of the relationship." 
                        format="Permitted relationship combination verb"
                        example="USES"
                      />
                    </label>
                    <select
                      id="relationshipType"
                      value={relationshipType}
                      onChange={(e) => setRelationshipType(e.target.value)}
                      disabled={submitting || !targetEntityType}
                      className={styles.select}
                      required
                    >
                      <option value="">-- Choose Relationship --</option>
                      {relTypes.map((rel) => (
                        <option key={rel} value={rel}>
                          {rel}
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Target Entity Search */}
                  <div className={styles.formGroup}>
                    <label htmlFor="targetEntityId" className={styles.label}>
                      Target Entity <span className={styles.required}>*</span>
                      <FieldInfo 
                        tooltip="The specific entity you are connecting to." 
                        format="Asset registry name lookup"
                        example="Primary Customer Database"
                      />
                    </label>
                    <select
                      id="targetEntityId"
                      value={targetEntityId}
                      onChange={(e) => setTargetEntityId(e.target.value)}
                      disabled={submitting || !targetEntityType || loadingTargets}
                      className={styles.select}
                      required
                    >
                      {loadingTargets ? (
                        <option value="">Loading targets list...</option>
                      ) : targetsList.length > 0 ? (
                        <>
                          <option value="">-- Choose Target Record --</option>
                          {targetsList.map((item) => (
                            <option key={item.id} value={item.id}>
                              {item.label}
                            </option>
                          ))}
                        </>
                      ) : (
                        <option value="">-- No valid targets found --</option>
                      )}
                    </select>
                  </div>

                  <div className={styles.formActions} style={{ marginTop: "1.5rem" }}>
                    <button type="button" onClick={onClose} className={styles.cancelBtn}>
                      Cancel
                    </button>
                    <button
                      type="button"
                      onClick={() => validateAndAdvance(1)}
                      disabled={!targetEntityId || !relationshipType}
                      className={styles.submitBtn}
                    >
                      Next
                    </button>
                  </div>
                </div>
              )}

              {/* STEP 2: Attributes & Lifespans */}
              {currentWizardStep === 1 && (
                <div>
                  <p className={styles.infoText}>
                    Configure constraints, responsibility ownership, and dates for this connection.
                  </p>

                  {/* Scope */}
                  <div className={styles.formGroup}>
                    <label htmlFor="relationshipScope" className={styles.label}>
                      Scope Context
                      <FieldInfo 
                        tooltip="Optional context boundary string defining connection range." 
                        format="Sub-boundary lookup key"
                        example="WORKFLOW:WF-001"
                      />
                    </label>
                    <input
                      type="text"
                      id="relationshipScope"
                      value={relationshipScope}
                      onChange={(e) => setRelationshipScope(e.target.value)}
                      placeholder="e.g. WORKFLOW:WF-001"
                      className={styles.input}
                    />
                  </div>

                  {/* Responsibility Type */}
                  <div className={styles.formGroup}>
                    <label htmlFor="responsibilityType" className={styles.label}>
                      Responsibility Type
                      <FieldInfo 
                        tooltip="Assign specific responsibility ownership." 
                        format="Responsibility role enum"
                        example="OWNER"
                      />
                    </label>
                    <select
                      id="responsibilityType"
                      value={responsibilityType}
                      onChange={(e) => setResponsibilityType(e.target.value)}
                      className={styles.select}
                    >
                      <option value="">-- Choose Responsibility (Optional) --</option>
                      <option value="OWNER">OWNER</option>
                      <option value="REVIEWER">REVIEWER</option>
                      <option value="APPROVER">APPROVER</option>
                      <option value="AUDITOR">AUDITOR</option>
                    </select>
                  </div>

                  {/* Effective Dates */}
                  <div className={styles.formGrid} style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
                    <div className={styles.formGroup}>
                      <label htmlFor="effectiveFrom" className={styles.label}>
                        Effective From Date
                        <FieldInfo 
                          tooltip="Starting date when this link becomes valid." 
                          format="Local datetime picker"
                        />
                      </label>
                      <input
                        type="datetime-local"
                        id="effectiveFrom"
                        value={effectiveFrom}
                        onChange={(e) => setEffectiveFrom(e.target.value)}
                        className={styles.input}
                      />
                    </div>

                    <div className={styles.formGroup}>
                      <label htmlFor="effectiveTo" className={styles.label}>
                        Effective To Date
                        <FieldInfo 
                          tooltip="Ending date when this link ceases validity." 
                          format="Local datetime picker"
                        />
                      </label>
                      <input
                        type="datetime-local"
                        id="effectiveTo"
                        value={effectiveTo}
                        onChange={(e) => setEffectiveTo(e.target.value)}
                        className={styles.input}
                      />
                    </div>
                  </div>

                  <div className={styles.formActions} style={{ marginTop: "1.5rem" }}>
                    <button type="button" onClick={() => setCurrentWizardStep(0)} className={styles.cancelBtn}>
                      Back
                    </button>
                    <button
                      type="button"
                      onClick={() => validateAndAdvance(2)}
                      className={styles.submitBtn}
                    >
                      Next
                    </button>
                  </div>
                </div>
              )}

              {/* STEP 3: Configurations & Review */}
              {currentWizardStep === 2 && (
                <div>
                  <p className={styles.infoText}>
                    Provide optional metadata configuration and review before establishing connection.
                  </p>

                  {/* Metadata JSON */}
                  <div className={styles.formGroup}>
                    <label htmlFor="metadataJson" className={styles.label}>
                      Metadata JSON
                      <FieldInfo 
                        tooltip="Additional structured configuration properties." 
                        format="Valid JSON payload string"
                        example='{"access_mode": "READ_ONLY"}'
                      />
                    </label>
                    <textarea
                      id="metadataJson"
                      value={metadataJson}
                      onChange={(e) => setMetadataJson(e.target.value)}
                      placeholder='{ "access_mode": "READ_ONLY" }'
                      rows={4}
                      className={`${styles.textarea} ${!isMetadataJsonValid ? styles.invalidJson : ""}`}
                      style={{ fontFamily: "monospace", width: '100%', padding: '0.5rem', background: 'rgba(0,0,0,0.2)', border: !isMetadataJsonValid ? '1px solid #ef4444' : '1px solid rgba(255,255,255,0.1)', color: '#fff', borderRadius: '4px' }}
                    />
                    {!isMetadataJsonValid && (
                      <span style={{ color: "#ef4444", fontSize: "0.8rem", marginTop: "4px", display: "block" }}>
                        Invalid JSON formatting.
                      </span>
                    )}
                  </div>

                  {/* Review Box */}
                  <div style={{ marginTop: "1rem", background: "rgba(255, 255, 255, 0.03)", padding: "1rem", borderRadius: "6px", border: "1px solid rgba(255,255,255,0.05)" }}>
                    <h5 style={{ margin: "0 0 0.5rem 0", color: "#fff", fontWeight: 600 }}>Connection Review</h5>
                    <div style={{ fontSize: "0.85rem", display: "grid", gap: "0.25rem", color: "rgba(255,255,255,0.7)" }}>
                      <div><strong>Source:</strong> {sourceEntityType} ({sourceEntityId})</div>
                      <div><strong>Target:</strong> {targetEntityType} ({targetsList.find(t => t.id === targetEntityId)?.label || targetEntityId})</div>
                      <div><strong>Action:</strong> {relationshipType}</div>
                      {relationshipScope && <div><strong>Scope:</strong> {relationshipScope}</div>}
                      {responsibilityType && <div><strong>Responsibility:</strong> {responsibilityType}</div>}
                      {effectiveFrom && <div><strong>Effective From:</strong> {effectiveFrom}</div>}
                      {effectiveTo && <div><strong>Effective To:</strong> {effectiveTo}</div>}
                    </div>
                  </div>

                  <div className={styles.formActions} style={{ marginTop: "1.5rem" }}>
                    <button type="button" onClick={() => setCurrentWizardStep(1)} className={styles.cancelBtn}>
                      Back
                    </button>
                    <button
                      type="submit"
                      disabled={submitting || !isMetadataJsonValid}
                      className={styles.submitBtn}
                    >
                      {submitting ? "Linking..." : "Establish Link"}
                    </button>
                  </div>
                </div>
              )}
            </WizardShell>
          </form>
        )}
      </div>
    </Modal>
  );
};

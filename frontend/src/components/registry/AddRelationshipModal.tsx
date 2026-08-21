/* src/components/registry/AddRelationshipModal.tsx */

import React, { useEffect, useState } from "react";
import { Modal } from "../common/Modal";
import { useToast } from "../../hooks/useToast";
import * as registryService from "../../services/registry/registryService";
import WizardShell from "../common/WizardShell";
import styles from "./AddRelationshipModal.module.css";
import { FieldInfo } from "../common/FieldInfo";
import { Calendar, Clock, Sparkles, ShieldCheck, ArrowRight } from "lucide-react";

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
    { rel: "USES_DATA_SOURCE", target: "DATA_SOURCE" },
    { rel: "USES_TOOL", target: "TOOL" }
  ],
  AGENT: [
    { rel: "USES_TOOL", target: "TOOL" },
    { rel: "USES_MODEL", target: "MODEL" },
    { rel: "PARTICIPATES_IN_WORKFLOW", target: "WORKFLOW" }
  ],
  WORKFLOW: [
    { rel: "USES_DATA_SOURCE", target: "DATA_SOURCE" },
    { rel: "USES_TOOL", target: "TOOL" },
    { rel: "GOVERNED_BY", target: "DEPARTMENT" }
  ],
  USER: [
    { rel: "MEMBER_OF", target: "DEPARTMENT" },
    { rel: "BELONGS_TO", target: "ROLE" }
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

// Helper for formatting date to datetime-local input string format YYYY-MM-DDTHH:mm
const toLocalISOString = (d: Date) => {
  const pad = (n: number) => n.toString().padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
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

  // Quick Preset Helper Functions for Date Pickers
  const handleSetFromNow = () => {
    setEffectiveFrom(toLocalISOString(new Date()));
  };

  const handleSetToPlusDays = (days: number) => {
    const start = effectiveFrom ? new Date(effectiveFrom) : new Date();
    const future = new Date(start.getTime() + days * 24 * 60 * 60 * 1000);
    setEffectiveTo(toLocalISOString(future));
  };

  const handleClearToDate = () => {
    setEffectiveTo("");
  };

  // Calculate lifespan duration text helper
  const getDurationText = () => {
    if (!effectiveFrom && !effectiveTo) {
      return "♾️ Permanent Link (Valid indefinitely with no start/end date restriction)";
    }
    if (effectiveFrom && !effectiveTo) {
      return `▶️ Active starting from ${new Date(effectiveFrom).toLocaleDateString()} (No expiration set)`;
    }
    if (effectiveFrom && effectiveTo) {
      const start = new Date(effectiveFrom);
      const end = new Date(effectiveTo);
      const diffMs = end.getTime() - start.getTime();
      if (diffMs <= 0) return "⚠️ Effective To date must be after Effective From date";
      const diffDays = Math.round(diffMs / (1000 * 60 * 60 * 24));
      return `⏱️ Active Lifespan: ${diffDays} day${diffDays === 1 ? '' : 's'} (${start.toLocaleDateString()} ➔ ${end.toLocaleDateString()})`;
    }
    if (!effectiveFrom && effectiveTo) {
      return `⏹️ Active until ${new Date(effectiveTo).toLocaleDateString()}`;
    }
    return "";
  };

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
    if (t === "AGENT" || t === "AGENTS" || t === "AI_AGENT" || t === "AI_AGENTS") return "AGENT";
    if (t === "MODEL" || t === "MODELS" || t === "AI_MODEL" || t === "AI_MODELS") return "MODEL";
    if (t === "TOOL" || t === "TOOLS") return "TOOL";
    if (t === "WORKFLOW" || t === "WORKFLOWS") return "WORKFLOW";
    if (t === "DATA_SOURCE" || t === "DATA_SOURCES" || t === "DATASOURCE" || t === "DATASOURCES") return "DATA_SOURCE";
    if (t === "DEPARTMENT" || t === "DEPARTMENTS") return "DEPARTMENT";
    if (t === "USER" || t === "USERS") return "USER";
    if (t === "ROLE" || t === "ROLES") return "ROLE";
    return type.toUpperCase();
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
      relationship_type: relationshipType.toUpperCase(),
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
                <div className={styles.stepCard}>
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

                  <div className={styles.formActions}>
                    <button type="button" onClick={onClose} className={styles.cancelBtn}>
                      Cancel
                    </button>
                    <button
                      type="button"
                      onClick={() => validateAndAdvance(1)}
                      disabled={!targetEntityId || !relationshipType}
                      className={styles.submitBtn}
                    >
                      Next <ArrowRight size={16} />
                    </button>
                  </div>
                </div>
              )}

              {/* STEP 2: Attributes & Lifespans */}
              {currentWizardStep === 1 && (
                <div className={styles.stepCard}>
                  <p className={styles.infoText}>
                    Configure constraints, responsibility ownership, and validity lifespans for this connection.
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
                      placeholder="e.g. WORKFLOW:WF-001 or REGION:EU-EAST"
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

                  {/* Effective Dates with Modern Picker Helpers */}
                  <div className={styles.formGrid}>
                    {/* Effective From */}
                    <div className={styles.formGroup}>
                      <label htmlFor="effectiveFrom" className={styles.label}>
                        <Calendar size={15} style={{ color: "#38bdf8" }} />
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
                      <div className={styles.presetsBar}>
                        <span className={styles.presetLabel}>Quick Set:</span>
                        <button type="button" onClick={handleSetFromNow} className={styles.presetBtn}>
                          <Clock size={12} /> Set Now
                        </button>
                      </div>
                    </div>

                    {/* Effective To */}
                    <div className={styles.formGroup}>
                      <label htmlFor="effectiveTo" className={styles.label}>
                        <Calendar size={15} style={{ color: "#f43f5e" }} />
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
                      <div className={styles.presetsBar}>
                        <span className={styles.presetLabel}>Presets:</span>
                        <button type="button" onClick={() => handleSetToPlusDays(30)} className={styles.presetBtn}>
                          +30 Days
                        </button>
                        <button type="button" onClick={() => handleSetToPlusDays(90)} className={styles.presetBtn}>
                          +90 Days
                        </button>
                        <button type="button" onClick={() => handleSetToPlusDays(365)} className={styles.presetBtn}>
                          +1 Year
                        </button>
                        {effectiveTo && (
                          <button type="button" onClick={handleClearToDate} className={styles.presetBtn} style={{ color: "#ef4444" }}>
                            Clear
                          </button>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Calculated Duration Indicator */}
                  <div className={styles.durationCard}>
                    <span>{getDurationText()}</span>
                  </div>

                  <div className={styles.formActions}>
                    <button type="button" onClick={() => setCurrentWizardStep(0)} className={styles.cancelBtn}>
                      Back
                    </button>
                    <button
                      type="button"
                      onClick={() => validateAndAdvance(2)}
                      className={styles.submitBtn}
                    >
                      Next <ArrowRight size={16} />
                    </button>
                  </div>
                </div>
              )}

              {/* STEP 3: Configurations & Review */}
              {currentWizardStep === 2 && (
                <div className={styles.stepCard}>
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
                      style={{ fontFamily: "monospace" }}
                    />
                    {!isMetadataJsonValid && (
                      <span style={{ color: "#ef4444", fontSize: "0.8rem", marginTop: "4px", display: "block" }}>
                        Invalid JSON formatting.
                      </span>
                    )}
                  </div>

                  {/* Review Box */}
                  <div className={styles.reviewCard}>
                    <h5 className={styles.reviewTitle}>Connection Link Summary</h5>
                    <div className={styles.reviewGrid}>
                      <div className={styles.reviewItem}><strong>Source:</strong> {sourceEntityType}</div>
                      <div className={styles.reviewItem}><strong>Target:</strong> {targetEntityType}</div>
                      <div className={styles.reviewItem}><strong>Action:</strong> {relationshipType}</div>
                      <div className={styles.reviewItem}><strong>Scope:</strong> {relationshipScope || "DEFAULT"}</div>
                      <div className={styles.reviewItem}><strong>Responsibility:</strong> {responsibilityType || "UNASSIGNED"}</div>
                      <div className={styles.reviewItem}><strong>Effective From:</strong> {effectiveFrom ? new Date(effectiveFrom).toLocaleString() : "IMMEDIATE"}</div>
                      <div className={styles.reviewItem}><strong>Effective To:</strong> {effectiveTo ? new Date(effectiveTo).toLocaleString() : "NO EXPIRATION"}</div>
                    </div>
                  </div>

                  <div className={styles.formActions}>
                    <button type="button" onClick={() => setCurrentWizardStep(1)} className={styles.cancelBtn}>
                      Back
                    </button>
                    <button
                      type="submit"
                      disabled={submitting || !isMetadataJsonValid}
                      className={styles.submitBtn}
                    >
                      <Sparkles size={16} />
                      {submitting ? "Linking..." : "Establish Connection"}
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

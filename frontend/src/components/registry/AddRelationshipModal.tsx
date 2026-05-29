/* src/components/registry/AddRelationshipModal.tsx */

import React, { useEffect, useState } from "react";
import { Modal } from "../common/Modal";
import { useToast } from "../../hooks/useToast";
import * as registryService from "../../services/registry/registryService";
import styles from "./AddRelationshipModal.module.css";

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

export const AddRelationshipModal: React.FC<AddRelationshipModalProps> = ({
  isOpen,
  onClose,
  sourceEntityType,
  sourceEntityId,
  onSuccess
}) => {
  const { showToast } = useToast();
  
  // Available combinations based on source type
  const allowedOptions = PERMITTED_COMBINATIONS[sourceEntityType.toUpperCase()] || [];
  
  // Form State
  const [relationshipType, setRelationshipType] = useState("");
  const [targetEntityType, setTargetEntityType] = useState("");
  const [targetEntityId, setTargetEntityId] = useState("");
  
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
        if (res.data?.items) listData = res.data.items.map(m => ({ id: m.id, label: `${m.model_name} (v${m.model_version})` }));
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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!relationshipType || !targetEntityType || !targetEntityId) {
      showToast("Please fill in all required relationship fields", "error");
      return;
    }

    setSubmitting(true);
    setGeneralError(null);

    const payload = {
      source_entity_type: sourceEntityType.toUpperCase(),
      source_entity_id: sourceEntityId,
      target_entity_type: targetEntityType.toUpperCase(),
      target_entity_id: targetEntityId,
      relationship_type: relationshipType,
      metadata_json: null
    };

    try {
      await registryService.createRelationship(payload);
      showToast("Relationship connection established", "success");
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
      setGeneralError(null);
    }
  }, [isOpen]);

  const hasAllowedLinkages = allowedOptions.length > 0;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={`Create Connection Link`}
      size="md"
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
            <p className={styles.infoText}>
              Establish a validated connection from this <strong>{formatEntityLabel(sourceEntityType)}</strong> to another asset.
            </p>

            {/* Target Entity Type */}
            <div className={styles.formGroup}>
              <label htmlFor="targetEntityType" className={styles.label}>
                Target Entity Type <span className={styles.required}>*</span>
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

            {/* Actions */}
            <div className={styles.formActions}>
              <button
                type="button"
                onClick={onClose}
                disabled={submitting}
                className={styles.cancelBtn}
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={submitting || !targetEntityId || !relationshipType}
                className={styles.submitBtn}
              >
                {submitting ? "Linking..." : "Establish Link"}
              </button>
            </div>
          </form>
        )}
      </div>
    </Modal>
  );
};

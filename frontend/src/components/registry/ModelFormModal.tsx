/* src/components/registry/ModelFormModal.tsx */

import React, { useEffect, useState } from "react";
import { Modal } from "../common/Modal";
import { FieldInfo } from "../common/FieldInfo";
import { useToast } from "../../hooks/useToast";
import * as registryService from "../../services/registry/registryService";
import { EntityStatus } from "../../services/registry/registryTypes";
import { RelationshipViewer } from "./RelationshipViewer";
import { AuditTrailViewer } from "./AuditTrailViewer";
import { ConfirmDeleteModal } from "../common/ConfirmDeleteModal";
import WizardShell from "../common/WizardShell";
import styles from "./ModelFormModal.module.css";

const PROVIDER_TYPES = [
  "Enterprise Vendor",
  "Open Source / Hub",
  "Internal Custom",
  "Fine-tuned Model",
  "Client-owned Model",
  "Partner-provided Model",
  "Clinical / Domain-specific Provider",
  "Other"
];

const PROVIDER_NAMES = [
  "OpenAI Enterprise",
  "Anthropic",
  "AWS Bedrock",
  "Azure OpenAI",
  "Google Vertex AI",
  "Hugging Face Hub",
  "Meta",
  "Mistral",
  "Cohere",
  "Internal Innovant",
  "Client Internal Model",
  "Custom"
];

const PROVIDER_MODELS: Record<string, Record<string, string[]>> = {
  "OpenAI Enterprise": {
    LLM: ["gpt-4o", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"],
    ML: ["openai-linear-regression-v1", "openai-xgboost-tabular"],
    CLASSIFIER: ["gpt-4o-moderation", "moderation-latest", "openai-sentiment-classifier"],
    EMBEDDING: ["text-embedding-3-small", "text-embedding-3-large", "text-embedding-ada-002"],
    RULE_BASED: ["openai-safety-guardrails-v1", "openai-content-rules"],
    FORECASTING: ["openai-time-series-forecaster"],
    OPTIMIZATION: ["openai-hyperparameter-tuner"]
  },
  "Anthropic": {
    LLM: ["claude-3-5-sonnet", "claude-3-opus", "claude-3-haiku", "claude-2.1"],
    ML: ["anthropic-tabular-predictor-v1"],
    CLASSIFIER: ["claude-moderation-classifier", "claude-sentiment-v2"],
    EMBEDDING: ["claude-embeddings-v1"],
    RULE_BASED: ["anthropic-constitution-rules-v2"],
    FORECASTING: ["anthropic-time-series-v1"],
    OPTIMIZATION: ["anthropic-prompt-optimizer"]
  },
  "AWS Bedrock": {
    LLM: ["meta.llama3-70b-instruct", "anthropic.claude-3-sonnet", "cohere.command-r-v1", "amazon.titan-text-express"],
    ML: ["amazon.sagemaker-xgboost-v1", "amazon.sagemaker-linear-learner"],
    CLASSIFIER: ["amazon.titan-image-moderator", "amazon.titan-classifier"],
    EMBEDDING: ["amazon.titan-embed-text-v1", "cohere.embed-english-v3", "cohere.embed-multilingual-v3"],
    RULE_BASED: ["aws-guardrails-for-bedrock-v1"],
    FORECASTING: ["amazon.forecast-time-series-v2"],
    OPTIMIZATION: ["amazon.sagemaker-hyperparameter-tuning"]
  },
  "Azure OpenAI": {
    LLM: ["gpt-4o", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"],
    ML: ["azure-automl-tabular-regression", "azure-xgboost-model"],
    CLASSIFIER: ["azure-content-safety-classifier", "azure-text-classifier"],
    EMBEDDING: ["text-embedding-3-small", "text-embedding-3-large", "text-embedding-ada-002"],
    RULE_BASED: ["azure-openai-system-prompt-guardrails"],
    FORECASTING: ["azure-machine-learning-forecasting"],
    OPTIMIZATION: ["azure-ml-tuning-optimizer"]
  },
  "Google Vertex AI": {
    LLM: ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-1.0-pro", "palm2-text-bison"],
    ML: ["vertex-automl-tabular-regression", "vertex-tabular-classification"],
    CLASSIFIER: ["vertex-safety-classifier-v1", "vertex-sentiment-analyzer"],
    EMBEDDING: ["text-embedding-gecko", "text-multilingual-embedding-gecko"],
    RULE_BASED: ["vertex-ai-search-grounding-guardrails"],
    FORECASTING: ["vertex-automl-forecasting-model"],
    OPTIMIZATION: ["vertex-ai-vizier-tuner"]
  },
  "Hugging Face Hub": {
    LLM: ["meta-llama/Meta-Llama-3-8B-Instruct", "mistralai/Mistral-7B-Instruct-v0.3", "microsoft/Phi-3-mini-4k-instruct"],
    ML: ["scikit-learn/random-forest-iris", "xgboost/credit-risk-model"],
    CLASSIFIER: ["distilbert-base-uncased-finetuned-sst-2-english", "cardiffnlp/twitter-roberta-base-sentiment"],
    EMBEDDING: ["sentence-transformers/all-MiniLM-L6-v2", "BAAI/bge-large-en-v1.5"],
    RULE_BASED: ["huggingface/regex-ner-pipeline-v1"],
    FORECASTING: ["huggingface/prophet-time-series-model", "amazon/chronos-t5-small"],
    OPTIMIZATION: ["huggingface/optuna-hyperparameter-optimizer"]
  },
  "Meta": {
    LLM: ["llama-3-8b", "llama-3-70b", "llama-2-13b-chat"],
    ML: ["meta-xgboost-recommendation-v1"],
    CLASSIFIER: ["llama-guard-2", "llama-guard-1", "meta-sentiment-roberta"],
    EMBEDDING: ["llama-embeddings-v1"],
    RULE_BASED: ["meta-llama-guardrails-constitution"],
    FORECASTING: ["meta-prophet-forecasting-v1"],
    OPTIMIZATION: ["meta-optuna-hyperparameter-tuning"]
  },
  "Mistral": {
    LLM: ["mistral-large", "mistral-medium", "mistral-small", "open-mixtral-8x22b", "open-codestral-7b"],
    ML: ["mistral-tabular-regressor-v1"],
    CLASSIFIER: ["mistral-moderation-classifier-v1"],
    EMBEDDING: ["mistral-embed-v1"],
    RULE_BASED: ["mistral-safety-guardrails-v1"],
    FORECASTING: ["mistral-demand-forecaster-v1"],
    OPTIMIZATION: ["mistral-vizier-optimizer"]
  },
  "Cohere": {
    LLM: ["command-r-plus", "command-r", "command-light"],
    ML: ["cohere-tabular-churn-model-v2"],
    CLASSIFIER: ["cohere-classify-v3", "cohere-sentiment-analyzer"],
    EMBEDDING: ["embed-english-v3.0", "embed-multilingual-v3.0", "embed-english-light-v3.0"],
    RULE_BASED: ["cohere-safety-guardrails-v2"],
    FORECASTING: ["cohere-demand-forecasting-v1"],
    OPTIMIZATION: ["cohere-hyperparameter-optimizer"]
  },
  "Internal Innovant": {
    LLM: ["innovant-core-llm", "innovant-chat-v2"],
    ML: ["innovant-tabular-churn-predictor", "innovant-anomaly-detector"],
    CLASSIFIER: ["innovant-risk-classifier-v1", "innovant-enquiry-classifier-v2"],
    EMBEDDING: ["innovant-semantic-embed-v1"],
    RULE_BASED: ["innovant-policy-decision-rules"],
    FORECASTING: ["innovant-demand-forecaster-v3"],
    OPTIMIZATION: ["innovant-routing-optimizer-v2"]
  },
  "Client Internal Model": {
    LLM: ["client-internal-llm-v1"],
    ML: ["client-propensity-model-v2"],
    CLASSIFIER: ["client-support-ticket-classifier"],
    EMBEDDING: ["client-custom-embedding-v1"],
    RULE_BASED: ["client-business-validation-rules"],
    FORECASTING: ["client-inventory-forecaster"],
    OPTIMIZATION: ["client-supply-chain-optimizer"]
  }
};



interface ModelFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  modelId?: string | null;
  onSuccess: () => void;
  defaultDepartmentId?: string | null;
  defaultUserId?: string | null;
}

export const ModelFormModal: React.FC<ModelFormModalProps> = ({
  isOpen,
  onClose,
  modelId,
  onSuccess,
  defaultDepartmentId,
  defaultUserId
}) => {
  const { showToast } = useToast();
  const [activeTab, setActiveTab] = useState<"details" | "relationships" | "audit">("details");
  const [currentWizardStep, setCurrentWizardStep] = useState(0);

  // Lookups data
  const [users, setUsers] = useState<{ id: string; full_name: string; email: string }[]>([]);
  const [departments, setDepartments] = useState<{ id: string; department_name: string; department_code: string }[]>([]);
  const [loadingLookups, setLoadingLookups] = useState(false);

  // Form State
  const [formData, setFormData] = useState({
    model_code: "",
    model_name: "",
    model_type: "",
    provider: "",
    version: "",
    purpose: "",
    owner_user_id: "",
    department_id: "",
    risk_level: "",
    deployment_environment: "",
    status: EntityStatus.DRAFT,
    metadata_json: "",
    provider_type: "",
    provider_name: "",
    custom_provider_name: "",
    provider_owner_department: "",
    provider_developed_by: "",
    provider_training_data: "",
    provider_fine_tuned_from: "",
    provider_hosting: "",
    provider_security: "",
    provider_approved_usage: "",
    provider_restricted_usage: "",
    provider_model_card: "",
    provider_evaluation: "",
    provider_responsible_person: ""
  });

  const [loading, setLoading] = useState(false);
  const [isMetadataJsonValid, setIsMetadataJsonValid] = useState(true);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [generalError, setGeneralError] = useState<string | null>(null);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  const isEditMode = !!modelId;

  // Auto-generate model code when model name changes in non-custom mode
  useEffect(() => {
    const isCustomMode = formData.provider_type === "Internal Custom" && formData.provider_name === "Custom";
    if (!isCustomMode) {
      if (formData.model_name) {
        const sanitizedCode = formData.model_name
          .toUpperCase()
          .replace(/[^A-Z0-9]/g, "_")
          .replace(/_+/g, "_")
          .replace(/(^_|_$)/g, "");
        setFormData(prev => ({
          ...prev,
          model_code: isEditMode ? prev.model_code : sanitizedCode
        }));
      } else {
        setFormData(prev => ({
          ...prev,
          model_code: isEditMode ? prev.model_code : ""
        }));
      }
    }
  }, [formData.model_name, formData.provider_type, formData.provider_name, isEditMode]);

  const wizardSteps = [
    { label: "Core parameters" },
    { label: "Governance & alignment" },
    { label: "Description & metadata" }
  ];

  const validateAndAdvance = (targetStep: number) => {
    if (isEditMode) {
      setCurrentWizardStep(targetStep);
      return;
    }
    
    // In create (strict) mode, validate before advancing
    if (targetStep > currentWizardStep) {
      if (currentWizardStep === 0) {
        const isCustomMode = formData.provider_type === "Internal Custom" && formData.provider_name === "Custom";
        if (isCustomMode) {
          if (!formData.model_code.trim() || !formData.model_name.trim()) {
            showToast("Please fill in all required fields for Core parameters", "error");
            return;
          }
        } else {
          if (
            !formData.provider_type.trim() ||
            !formData.provider_name.trim() ||
            !formData.model_type.trim() ||
            !formData.model_name.trim()
          ) {
            showToast("Please fill in all required fields for Core parameters", "error");
            return;
          }
        }
      }
      if (currentWizardStep === 1) {
        if (!formData.risk_level) {
          showToast("Please fill in all required fields for Governance & alignment", "error");
          return;
        }
      }
    }
    setCurrentWizardStep(targetStep);
  };

  // Reset form when modal opens or closes
  useEffect(() => {
    if (!isOpen) {
      setFormData({
        model_code: "",
        model_name: "",
        model_type: "",
        provider: "",
        version: "",
        purpose: "",
        owner_user_id: "",
        department_id: "",
        risk_level: "",
        deployment_environment: "",
        status: EntityStatus.DRAFT,
        metadata_json: "",
        provider_type: "",
        provider_name: "",
        custom_provider_name: "",
        provider_owner_department: "",
        provider_developed_by: "",
        provider_training_data: "",
        provider_fine_tuned_from: "",
        provider_hosting: "",
        provider_security: "",
        provider_approved_usage: "",
        provider_restricted_usage: "",
        provider_model_card: "",
        provider_evaluation: "",
        provider_responsible_person: ""
      });
      setFieldErrors({});
      setGeneralError(null);
      setActiveTab("details");
      setCurrentWizardStep(0);
    }
  }, [isOpen]);

  // Load Lookups on mount
  useEffect(() => {
    async function loadLookups() {
      setLoadingLookups(true);
      try {
        const [usersRes, deptsRes] = await Promise.all([
          registryService.getUsersLookup(),
          registryService.getDepartmentsLookup()
        ]);
        if (usersRes.data) setUsers(usersRes.data);
        if (deptsRes.data) setDepartments(deptsRes.data);
      } catch (err) {
        console.error("Failed to load form lookups:", err);
      } finally {
        setLoadingLookups(false);
      }
    }
    if (isOpen) {
      loadLookups();
    }
  }, [isOpen]);

  // Load Model Data in Edit Mode
  useEffect(() => {
    async function loadModel() {
      if (!modelId) return;
      setLoading(true);
      setGeneralError(null);
      try {
        const res = await registryService.getModel(modelId);
        if (res.data) {
          const m = res.data;
          const retrievedName = (m as any).provider_name || (m as any).metadata_json?.provider_name || "";
          const isStandardName = PROVIDER_NAMES.includes(retrievedName);
          setFormData({
            model_code: m.model_code || (m as any).code || "",
            model_name: m.model_name || "",
            model_type: m.model_type || "",
            provider: (m as any).provider || "",
            version: m.model_version || (m as any).version || "",
            purpose: (m as any).purpose || m.description || "",
            owner_user_id: (m as any).owner_user_id || "",
            department_id: m.department_id || "",
            risk_level: m.risk_level || "",
            deployment_environment: (m as any).deployment_environment || "",
            status: m.status || EntityStatus.DRAFT,
            metadata_json: (m as any).metadata_json 
              ? typeof (m as any).metadata_json === "string" 
                ? (m as any).metadata_json 
                : JSON.stringify((m as any).metadata_json, null, 2)
              : "",
            provider_type: (m as any).provider_type || (m as any).metadata_json?.provider_type || "",
            provider_name: retrievedName ? (isStandardName ? retrievedName : "Custom") : "",
            custom_provider_name: retrievedName ? (isStandardName ? "" : retrievedName) : "",
            provider_owner_department: (m as any).metadata_json?.provider_owner_department || "",
            provider_developed_by: (m as any).metadata_json?.provider_developed_by || "",
            provider_training_data: (m as any).metadata_json?.provider_training_data || "",
            provider_fine_tuned_from: (m as any).metadata_json?.provider_fine_tuned_from || "",
            provider_hosting: (m as any).metadata_json?.provider_hosting || "",
            provider_security: (m as any).metadata_json?.provider_security || "",
            provider_approved_usage: (m as any).metadata_json?.provider_approved_usage || "",
            provider_restricted_usage: (m as any).metadata_json?.provider_restricted_usage || "",
            provider_model_card: (m as any).metadata_json?.provider_model_card || "",
            provider_evaluation: (m as any).metadata_json?.provider_evaluation || "",
            provider_responsible_person: (m as any).metadata_json?.provider_responsible_person || ""
          });
        }
      } catch (err: any) {
        setGeneralError(err.message || "Failed to load model data.");
      } finally {
        setLoading(false);
      }
    }

    if (isOpen) {
      if (modelId) {
        loadModel();
        setActiveTab("details");
        setCurrentWizardStep(0);
      } else {
        // Reset form for create mode
        setFormData({
          model_code: "",
          model_name: "",
          model_type: "",
          provider: "",
          version: "",
          purpose: "",
          owner_user_id: defaultUserId || "",
          department_id: defaultDepartmentId || "",
          risk_level: "",
          deployment_environment: "",
          status: EntityStatus.DRAFT,
          metadata_json: "",
          provider_type: "",
          provider_name: "",
          custom_provider_name: "",
          provider_owner_department: "",
          provider_developed_by: "",
          provider_training_data: "",
          provider_fine_tuned_from: "",
          provider_hosting: "",
          provider_security: "",
          provider_approved_usage: "",
          provider_restricted_usage: "",
          provider_model_card: "",
          provider_evaluation: "",
          provider_responsible_person: ""
        });
        setFieldErrors({});
        setGeneralError(null);
        setActiveTab("details");
        setCurrentWizardStep(0);
      }
    }
  }, [isOpen, modelId, defaultDepartmentId, defaultUserId]);

  // Validate metadata_json
  useEffect(() => {
    if (!formData.metadata_json.trim()) {
      setIsMetadataJsonValid(true);
      return;
    }
    try {
      JSON.parse(formData.metadata_json);
      setIsMetadataJsonValid(true);
    } catch {
      setIsMetadataJsonValid(false);
    }
  }, [formData.metadata_json]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    // Clear field-level error when user starts typing
    if (fieldErrors[name]) {
      setFieldErrors((prev) => {
        const copy = { ...prev };
        delete copy[name];
        return copy;
      });
    }
  };

  const handleApiError = (err: any) => {
    const message = err.message || "An error occurred";
    setGeneralError(message);

    const newFieldErrors: Record<string, string> = {};

    // 1. Try parsing FastAPI standard flat string format:
    // "Validation Error: body.model_code: field required, body.model_name: field required"
    if (message.includes("Validation Error:")) {
      const errorContent = message.substring(message.indexOf("Validation Error:") + 17).trim();
      const parts = errorContent.split(", ");
      parts.forEach((part: string) => {
        const colonIndex = part.indexOf(":");
        if (colonIndex !== -1) {
          const fullField = part.substring(0, colonIndex).trim(); // "body.model_code"
          const msg = part.substring(colonIndex + 1).trim(); // "field required"
          let fieldName = fullField.replace("body.", "").trim(); // "model_code"
          
          // Map API validation errors to form fields
          if (fieldName === "description") fieldName = "purpose";
          if (fieldName === "model_version") fieldName = "version";
          if (fieldName === "code") fieldName = "model_code";
          
          newFieldErrors[fieldName] = msg;
        }
      });
    }

    // 2. Try parsing standard structured details array
    if (err.details && Array.isArray(err.details)) {
      err.details.forEach((d: any) => {
        let fieldName = d.field || (d.loc && d.loc[d.loc.length - 1]);
        if (fieldName) {
          fieldName = String(fieldName);
          
          // Map API validation errors to form fields
          if (fieldName === "description") fieldName = "purpose";
          if (fieldName === "model_version") fieldName = "version";
          if (fieldName === "code") fieldName = "model_code";
          
          newFieldErrors[fieldName] = d.message || d.msg || "Invalid value";
        }
      });
    }

    setFieldErrors(newFieldErrors);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isMetadataJsonValid) {
      showToast("Metadata must be a valid JSON object", "error");
      return;
    }

    setLoading(true);
    setGeneralError(null);
    setFieldErrors({});

    // Build metadata json
    let parsedMetadata = {};
    if (formData.metadata_json.trim()) {
      parsedMetadata = JSON.parse(formData.metadata_json);
    }
    
    // Inject provider details into metadata_json
    parsedMetadata = {
      ...parsedMetadata,
      provider_type: formData.provider_type,
      provider_name: formData.provider_name,
      ...(formData.provider_type === "Internal Custom" || formData.provider_type === "Client-owned Model" ? {
        provider_owner_department: formData.provider_owner_department,
        provider_developed_by: formData.provider_developed_by,
        provider_training_data: formData.provider_training_data,
        provider_fine_tuned_from: formData.provider_fine_tuned_from,
        provider_hosting: formData.provider_hosting,
        provider_security: formData.provider_security,
        provider_approved_usage: formData.provider_approved_usage,
        provider_restricted_usage: formData.provider_restricted_usage,
        provider_model_card: formData.provider_model_card,
        provider_evaluation: formData.provider_evaluation,
        provider_responsible_person: formData.provider_responsible_person
      } : {})
    };

    let finalModelCode = formData.model_code;
    const isCustomMode = formData.provider_type === "Internal Custom" && formData.provider_name === "Custom";
    if (!isEditMode && !isCustomMode && formData.model_name) {
      const suffix = Math.random().toString(36).substring(2, 6).toUpperCase();
      finalModelCode = `${formData.model_code}_${suffix}`;
    }

    const payload = {
      ...formData,
      model_code: finalModelCode,
      metadata_json: parsedMetadata
    };
    // Clean up temporary flat fields
    delete (payload as any).provider_type;
    delete (payload as any).provider_name;
    delete (payload as any).custom_provider_name;
    delete (payload as any).provider_owner_department;
    delete (payload as any).provider_developed_by;
    delete (payload as any).provider_training_data;
    delete (payload as any).provider_fine_tuned_from;
    delete (payload as any).provider_hosting;
    delete (payload as any).provider_security;
    delete (payload as any).provider_approved_usage;
    delete (payload as any).provider_restricted_usage;
    delete (payload as any).provider_model_card;
    delete (payload as any).provider_evaluation;
    delete (payload as any).provider_responsible_person;

    try {
      if (isEditMode && modelId) {
        await registryService.updateModel(modelId, payload);
      } else {
        await registryService.createModel(payload);
      }
      showToast("Model saved successfully", "success");
      onSuccess();
      onClose();
    } catch (err: any) {
      handleApiError(err);
      showToast("Failed to save model", "error");
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!modelId) return;
    setIsDeleting(true);
    try {
      await registryService.deleteModel(modelId);
      showToast("Model deleted successfully", "success");
      setIsDeleteModalOpen(false);
      onSuccess();
      onClose();
    } catch (err: any) {
      showToast(err.message || "Failed to delete model", "error");
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={isEditMode ? `Edit Model: ${formData.model_name}` : "Register New Model"}
      hintText={
        <div style={{ display: "flex", flexDirection: "column", gap: "12px", paddingRight: "4px" }}>
          <p style={{ margin: 0 }}>Register and configure core parameters, provider details, and governance alignments for AI models.</p>
          
          {currentWizardStep === 0 && (
            <div>
              <h4 style={{ color: "#fbbf24", margin: "0 0 4px 0", fontSize: "0.85rem" }}>Core Parameters</h4>
              <ul style={{ margin: 0, paddingLeft: "16px" }}>
                <li><strong>Provider Type & Name:</strong> Select the source of the model (e.g., <em>Enterprise Vendor</em> &gt; <em>OpenAI Enterprise</em> or <em>Custom</em>).</li>
                <li><strong>Model Type:</strong> The architectural category (e.g., <em>LLM</em>, <em>EMBEDDING</em>).</li>
                <li><strong>Model / Model Name:</strong> The specific model version (e.g., <code>gpt-4o</code>).</li>
                <li><strong>Model Code:</strong> A unique identifier (auto-generated or custom).</li>
                
                {formData.provider_type === "Internal Custom" && (
                  <>
                    <li><strong>Version:</strong> The version of your custom model (e.g., <code>1.0.1</code>).</li>
                    <li><strong>Hosting Environment & Dept:</strong> Where it runs and which department owns it.</li>
                    <li><strong>Security & Usage:</strong> Classification (e.g., <em>High</em>) and approved usage scenario.</li>
                    <li><strong>Evaluation & Responsibility:</strong> Track if eval is done and who the responsible person is.</li>
                  </>
                )}
              </ul>
            </div>
          )}

          {currentWizardStep === 1 && (
            <div>
              <h4 style={{ color: "#fbbf24", margin: "0 0 4px 0", fontSize: "0.85rem" }}>Governance & Alignment</h4>
              <ul style={{ margin: 0, paddingLeft: "16px" }}>
                <li><strong>Risk Level:</strong> Set the risk tier (e.g., <em>High</em>, <em>Medium</em>, <em>Low</em>) for oversight.</li>
                <li><strong>Deployment Environment:</strong> Where the model operates (e.g., <em>Production</em>, <em>Staging</em>).</li>
                <li><strong>Status:</strong> The operational state (e.g., <em>Active</em>, <em>Deprecated</em>).</li>
              </ul>
            </div>
          )}

          {currentWizardStep === 2 && (
            <div>
              <h4 style={{ color: "#fbbf24", margin: "0 0 4px 0", fontSize: "0.85rem" }}>Description & Metadata</h4>
              <ul style={{ margin: 0, paddingLeft: "16px" }}>
                <li><strong>Purpose:</strong> A clear description of what the model is used for.</li>
                <li><strong>Metadata (JSON):</strong> Optional technical details like context window or hosting specs.</li>
              </ul>
            </div>
          )}
        </div>
      }
      size="xl"
    >
      <div className={styles.container}>
        {/* Form Tab Headers */}
        {isEditMode && (
          <div className={styles.tabsHeader}>
            <button
              type="button"
              className={`${styles.tabBtn} ${activeTab === "details" ? styles.activeTab : ""}`}
              onClick={() => setActiveTab("details")}
            >
              Details
            </button>
            <button
              type="button"
              className={`${styles.tabBtn} ${activeTab === "relationships" ? styles.activeTab : ""}`}
              onClick={() => setActiveTab("relationships")}
            >
              Relationships
            </button>
            <button
              type="button"
              className={`${styles.tabBtn} ${activeTab === "audit" ? styles.activeTab : ""}`}
              onClick={() => setActiveTab("audit")}
            >
              Audit Trail
            </button>
          </div>
        )}

        {/* General Alert */}
        {generalError && <div className={styles.generalAlert}>{generalError}</div>}

        {/* Tab Contents */}
        <div className={styles.tabsContent}>
          {activeTab === "details" && (
            <form onSubmit={handleSubmit} className={styles.form}>
              <WizardShell
                steps={wizardSteps}
                currentStep={currentWizardStep}
                onStepClick={validateAndAdvance}
                mode={isEditMode ? "tabbed" : "strict"}
              >
                {/* STEP 1: Core parameters */}
                {currentWizardStep === 0 && (() => {
                  const isCustomMode = formData.provider_type === "Internal Custom" && formData.provider_name === "Custom";
                  const modelsList = PROVIDER_MODELS[formData.provider_name]?.[formData.model_type] || [];
                  return (
                    <div>
                      <div className={styles.formGrid}>
                        {/* Provider Type */}
                        <div className={styles.formGroup}>
                          <label htmlFor="provider_type" className={styles.label}>
                            Provider Type <span className={styles.required}>*</span>
                            <FieldInfo tooltip="The category of the model provider." />
                          </label>
                          <select
                            id="provider_type"
                            name="provider_type"
                            value={formData.provider_type}
                            onChange={handleChange}
                            disabled={loading}
                            className={`${styles.select} ${fieldErrors.provider_type ? styles.inputError : ""}`}
                            required
                          >
                            <option value="">-- Select Provider Type --</option>
                            {PROVIDER_TYPES.map(type => (
                              <option key={type} value={type}>{type}</option>
                            ))}
                          </select>
                          {fieldErrors.provider_type && (
                            <span className={styles.fieldErrorText}>{fieldErrors.provider_type}</span>
                          )}
                        </div>

                        {/* Provider Name */}
                        <div className={styles.formGroup}>
                          <label htmlFor="provider_name" className={styles.label}>
                            Provider Name <span className={styles.required}>*</span>
                            <FieldInfo tooltip="The specific name of the provider." />
                          </label>
                          <select
                            id="provider_name"
                            name="provider_name"
                            value={formData.provider_name}
                            onChange={handleChange}
                            disabled={loading}
                            className={`${styles.select} ${fieldErrors.provider_name ? styles.inputError : ""}`}
                            required
                          >
                            <option value="">-- Select Provider Name --</option>
                            {PROVIDER_NAMES.map(name => (
                              <option key={name} value={name}>{name}</option>
                            ))}
                          </select>
                          {fieldErrors.provider_name && (
                            <span className={styles.fieldErrorText}>{fieldErrors.provider_name}</span>
                          )}
                        </div>

                        {/* Model Type */}
                        <div className={styles.formGroup}>
                          <label htmlFor="model_type" className={styles.label}>
                            Model Type <span className={styles.required}>*</span>
                            <FieldInfo tooltip="The architectural category of the model." />
                          </label>
                          <select
                            id="model_type"
                            name="model_type"
                            value={formData.model_type}
                            onChange={handleChange}
                            disabled={loading}
                            className={`${styles.select} ${fieldErrors.model_type ? styles.inputError : ""}`}
                            required
                          >
                            <option value="">-- Select Type --</option>
                            <option value="LLM">LLM</option>
                            <option value="ML">ML</option>
                            <option value="CLASSIFIER">CLASSIFIER</option>
                            <option value="EMBEDDING">EMBEDDING</option>
                            <option value="RULE_BASED">RULE_BASED</option>
                            <option value="FORECASTING">FORECASTING</option>
                            <option value="OPTIMIZATION">OPTIMIZATION</option>
                          </select>
                          {fieldErrors.model_type && (
                            <span className={styles.fieldErrorText}>{fieldErrors.model_type}</span>
                          )}
                        </div>

                        {/* Render standard model list / name selector if NOT custom mode */}
                        {!isCustomMode && (
                          modelsList.length > 0 ? (
                            <div className={styles.formGroup}>
                              <label htmlFor="model_name" className={styles.label}>
                                Model <span className={styles.required}>*</span>
                                <FieldInfo tooltip="Select from a list of models provided by the selected provider." />
                              </label>
                              <select
                                id="model_name"
                                name="model_name"
                                value={formData.model_name}
                                onChange={handleChange}
                                disabled={loading}
                                className={`${styles.select} ${fieldErrors.model_name ? styles.inputError : ""}`}
                                required
                              >
                                <option value="">-- Select Model --</option>
                                {modelsList.map(mName => (
                                  <option key={mName} value={mName}>{mName}</option>
                                ))}
                              </select>
                              {fieldErrors.model_name && (
                                <span className={styles.fieldErrorText}>{fieldErrors.model_name}</span>
                              )}
                            </div>
                          ) : (
                            <div className={styles.formGroup}>
                              <label htmlFor="model_name" className={styles.label}>
                                Model Name <span className={styles.required}>*</span>
                                <FieldInfo tooltip="The common name used for this AI model." />
                              </label>
                              <input
                                type="text"
                                id="model_name"
                                name="model_name"
                                value={formData.model_name}
                                onChange={handleChange}
                                disabled={loading}
                                placeholder="e.g. gpt-4o"
                                className={`${styles.input} ${fieldErrors.model_name ? styles.inputError : ""}`}
                                required
                              />
                              {fieldErrors.model_name && (
                                <span className={styles.fieldErrorText}>{fieldErrors.model_name}</span>
                              )}
                            </div>
                          )
                        )}

                        {/* If Custom Mode, render custom fields in-order */}
                        {isCustomMode && (
                          <>
                            {/* Model Code */}
                            <div className={styles.formGroup}>
                              <label htmlFor="model_code" className={styles.label}>
                                Model Code <span className={styles.required}>*</span>
                                <FieldInfo tooltip="Unique identifier for this AI model." />
                              </label>
                              <input
                                type="text"
                                id="model_code"
                                name="model_code"
                                value={formData.model_code}
                                onChange={handleChange}
                                disabled={isEditMode || loading}
                                className={`${styles.input} ${fieldErrors.model_code ? styles.inputError : ""}`}
                                required
                              />
                              {fieldErrors.model_code && (
                                <span className={styles.fieldErrorText}>{fieldErrors.model_code}</span>
                              )}
                            </div>

                            {/* Model Name */}
                            <div className={styles.formGroup}>
                              <label htmlFor="model_name" className={styles.label}>
                                Model Name <span className={styles.required}>*</span>
                                <FieldInfo tooltip="The common name used for this AI model." />
                              </label>
                              <input
                                type="text"
                                id="model_name"
                                name="model_name"
                                value={formData.model_name}
                                onChange={handleChange}
                                disabled={loading}
                                className={`${styles.input} ${fieldErrors.model_name ? styles.inputError : ""}`}
                                required
                              />
                              {fieldErrors.model_name && (
                                <span className={styles.fieldErrorText}>{fieldErrors.model_name}</span>
                              )}
                            </div>

                            {/* Version */}
                            <div className={styles.formGroup}>
                              <label htmlFor="version" className={styles.label}>Version <FieldInfo tooltip="The specific version or release tag of the model." /></label>
                              <input
                                type="text"
                                id="version"
                                name="version"
                                value={formData.version}
                                onChange={handleChange}
                                disabled={loading}
                                placeholder="e.g. 1.0.0"
                                className={styles.input}
                              />
                            </div>

                            {/* Model Owner Department */}
                            <div className={styles.formGroup}>
                              <label htmlFor="provider_owner_department" className={styles.label}>Model Owner Department <FieldInfo tooltip="Department that owns the internal or custom model." /></label>
                              <input type="text" id="provider_owner_department" name="provider_owner_department" value={formData.provider_owner_department} onChange={handleChange} disabled={loading} className={styles.input} />
                            </div>

                            {/* Model Developed By */}
                            <div className={styles.formGroup}>
                              <label htmlFor="provider_developed_by" className={styles.label}>Model Developed By <FieldInfo tooltip="The team or entity that originally developed the model." /></label>
                              <input type="text" id="provider_developed_by" name="provider_developed_by" value={formData.provider_developed_by} onChange={handleChange} disabled={loading} className={styles.input} />
                            </div>

                            {/* Training Data Source */}
                            <div className={styles.formGroup}>
                              <label htmlFor="provider_training_data" className={styles.label}>Training Data Source <FieldInfo tooltip="Details about the dataset used to train the model." /></label>
                              <input type="text" id="provider_training_data" name="provider_training_data" value={formData.provider_training_data} onChange={handleChange} disabled={loading} className={styles.input} />
                            </div>

                            {/* Fine-tuned From */}
                            <div className={styles.formGroup}>
                              <label htmlFor="provider_fine_tuned_from" className={styles.label}>Fine-tuned From <FieldInfo tooltip="If applicable, the base model this was fine-tuned from." /></label>
                              <input type="text" id="provider_fine_tuned_from" name="provider_fine_tuned_from" value={formData.provider_fine_tuned_from} onChange={handleChange} disabled={loading} className={styles.input} />
                            </div>

                            {/* Hosting Environment */}
                            <div className={styles.formGroup}>
                              <label htmlFor="provider_hosting" className={styles.label}>Hosting Environment <FieldInfo tooltip="Where the model is hosted (e.g. AWS, Azure, On-prem)." /></label>
                              <input type="text" id="provider_hosting" name="provider_hosting" value={formData.provider_hosting} onChange={handleChange} disabled={loading} className={styles.input} />
                            </div>

                            {/* Security Classification */}
                            <div className={styles.formGroup}>
                              <label htmlFor="provider_security" className={styles.label}>Security Classification <FieldInfo tooltip="The security rating of the model." /></label>
                              <input type="text" id="provider_security" name="provider_security" value={formData.provider_security} onChange={handleChange} disabled={loading} className={styles.input} />
                            </div>

                            {/* Approved Usage */}
                            <div className={styles.formGroup}>
                              <label htmlFor="provider_approved_usage" className={styles.label}>Approved Usage <FieldInfo tooltip="Scenarios in which the model is explicitly approved to be used." /></label>
                              <input type="text" id="provider_approved_usage" name="provider_approved_usage" value={formData.provider_approved_usage} onChange={handleChange} disabled={loading} className={styles.input} />
                            </div>

                            {/* Restricted Usage */}
                            <div className={styles.formGroup}>
                              <label htmlFor="provider_restricted_usage" className={styles.label}>Restricted Usage <FieldInfo tooltip="Scenarios in which the model must NOT be used." /></label>
                              <input type="text" id="provider_restricted_usage" name="provider_restricted_usage" value={formData.provider_restricted_usage} onChange={handleChange} disabled={loading} className={styles.input} />
                            </div>

                            {/* Model Card Available? */}
                            <div className={styles.formGroup}>
                              <label htmlFor="provider_model_card" className={styles.label}>Model Card Available? <FieldInfo tooltip="Does the model have a documented Model Card?" /></label>
                              <select id="provider_model_card" name="provider_model_card" value={formData.provider_model_card} onChange={handleChange} disabled={loading} className={styles.select}>
                                <option value="">-- Select --</option>
                                <option value="Yes">Yes</option>
                                <option value="No">No</option>
                              </select>
                            </div>

                            {/* Evaluation Completed? */}
                            <div className={styles.formGroup}>
                              <label htmlFor="provider_evaluation" className={styles.label}>Evaluation Completed? <FieldInfo tooltip="Has the model undergone a formal evaluation/testing process?" /></label>
                              <select id="provider_evaluation" name="provider_evaluation" value={formData.provider_evaluation} onChange={handleChange} disabled={loading} className={styles.select}>
                                <option value="">-- Select --</option>
                                <option value="Yes">Yes</option>
                                <option value="No">No</option>
                              </select>
                            </div>

                            {/* Responsible Person */}
                            <div className={styles.formGroup}>
                              <label htmlFor="provider_responsible_person" className={styles.label}>Responsible Person <FieldInfo tooltip="The individual accountable for this model." /></label>
                              <input type="text" id="provider_responsible_person" name="provider_responsible_person" value={formData.provider_responsible_person} onChange={handleChange} disabled={loading} className={styles.input} />
                            </div>
                          </>
                        )}
                      </div>

                      <div className={styles.formActions} style={{ marginTop: '1.5rem' }}>
                        <div className={styles.rightActions} style={{ width: '100%', justifyContent: 'flex-end' }}>
                          <button type="button" onClick={() => validateAndAdvance(1)} className={styles.submitBtn}>
                            Next
                          </button>
                        </div>
                      </div>
                    </div>
                  );
                })()}

                {/* STEP 2: Governance & alignment */}
                {currentWizardStep === 1 && (
                  <div>
                    <div className={styles.formGrid}>
                      {/* Risk Level */}
                      <div className={styles.formGroup}>
                        <label htmlFor="risk_level" className={styles.label}>
                          Risk Level <span className={styles.required}>*</span>
                          <FieldInfo tooltip="The assessed risk level associated with using this model." />
                        </label>
                        <select
                          id="risk_level"
                          name="risk_level"
                          value={formData.risk_level}
                          onChange={handleChange}
                          disabled={loading}
                          className={`${styles.select} ${fieldErrors.risk_level ? styles.inputError : ""}`}
                          required
                        >
                          <option value="">-- Select Risk Level --</option>
                          <option value="LOW">LOW</option>
                          <option value="MEDIUM">MEDIUM</option>
                          <option value="HIGH">HIGH</option>
                          <option value="CRITICAL">CRITICAL</option>
                        </select>
                        {fieldErrors.risk_level && (
                          <span className={styles.fieldErrorText}>{fieldErrors.risk_level}</span>
                        )}
                      </div>

                      {/* Department */}
                      <div className={styles.formGroup}>
                        <label htmlFor="department_id" className={styles.label}>Department <FieldInfo tooltip="The department that owns or manages this model." /></label>
                        <select
                          id="department_id"
                          name="department_id"
                          value={formData.department_id}
                          onChange={handleChange}
                          disabled={loading || loadingLookups}
                          className={styles.select}
                        >
                          {loadingLookups ? (
                            <option value="">Loading departments...</option>
                          ) : (
                            <>
                              <option value="">-- Select Department --</option>
                              {departments.map((d) => (
                                <option key={d.id} value={d.id}>
                                  {d.department_name} ({d.department_code})
                                </option>
                              ))}
                            </>
                          )}
                        </select>
                      </div>

                      {/* Deployment Environment */}
                      <div className={styles.formGroup}>
                        <label htmlFor="deployment_environment" className={styles.label}>Deployment Environment <FieldInfo tooltip="Where this model is currently deployed." /></label>
                        <select
                          id="deployment_environment"
                          name="deployment_environment"
                          value={formData.deployment_environment}
                          onChange={handleChange}
                          disabled={loading}
                          className={styles.select}
                        >
                          <option value="">-- Select Env --</option>
                          <option value="DEV">DEV</option>
                          <option value="TEST">TEST</option>
                          <option value="PROD">PROD</option>
                        </select>
                      </div>

                      {/* Status (Edit mode only) */}
                      {isEditMode && (
                        <div className={styles.formGroup}>
                          <label htmlFor="status" className={styles.label}>Entity Status <FieldInfo tooltip="The current lifecycle status of the model." /></label>
                          <select
                            id="status"
                            name="status"
                            value={formData.status}
                            onChange={handleChange}
                            disabled={loading}
                            className={styles.select}
                          >
                            <option value="DRAFT">DRAFT</option>
                            <option value="ACTIVE">ACTIVE</option>
                            <option value="INACTIVE">INACTIVE</option>
                            <option value="SUSPENDED">SUSPENDED</option>
                            <option value="RETIRED">RETIRED</option>
                            <option value="ARCHIVED">ARCHIVED</option>
                          </select>
                        </div>
                      )}
                    </div>

                    <div className={styles.formActions} style={{ marginTop: '1.5rem' }}>
                      <button type="button" onClick={() => setCurrentWizardStep(0)} className={styles.cancelBtn}>
                        Back
                      </button>
                      <div className={styles.rightActions}>
                        <button type="button" onClick={() => validateAndAdvance(2)} className={styles.submitBtn}>
                          Next
                        </button>
                      </div>
                    </div>
                  </div>
                )}

                {/* STEP 3: Description & metadata */}
                {currentWizardStep === 2 && (
                  <div>
                    {/* Purpose (Required Textarea) */}
                    <div className={styles.formGroupFull}>
                      <label htmlFor="purpose" className={styles.label}>
                        Purpose / Description <span className={styles.required}>*</span>
                        <FieldInfo tooltip="A detailed description of what the model does and its intended use." />
                      </label>
                      <textarea
                        id="purpose"
                        name="purpose"
                        value={formData.purpose}
                        onChange={handleChange}
                        disabled={loading}
                        rows={3}
                        className={`${styles.textarea} ${fieldErrors.purpose ? styles.inputError : ""}`}
                        required
                      />
                      {fieldErrors.purpose && (
                        <span className={styles.fieldErrorText}>{fieldErrors.purpose}</span>
                      )}
                    </div>

                    <div className={styles.formGrid}>
                      {/* Owner User */}
                      <div className={styles.formGroup}>
                        <label htmlFor="owner_user_id" className={styles.label}>Owner User <FieldInfo tooltip="The user primarily responsible for this model." /></label>
                        <select
                          id="owner_user_id"
                          name="owner_user_id"
                          value={formData.owner_user_id}
                          onChange={handleChange}
                          disabled={loading || loadingLookups}
                          className={styles.select}
                        >
                          {loadingLookups ? (
                            <option value="">Loading owners...</option>
                          ) : (
                            <>
                              <option value="">-- Select Owner --</option>
                              {users.map((u) => (
                                <option key={u.id} value={u.id}>
                                  {u.full_name} ({u.email})
                                </option>
                              ))}
                            </>
                          )}
                        </select>
                      </div>
                    </div>

                    {/* Metadata JSON (Validate valid JSON) */}
                    <div className={styles.formGroupFull}>
                      <label htmlFor="metadata_json" className={styles.label}>
                        Metadata JSON <FieldInfo tooltip="Any additional structured configuration or details in JSON format." />
                      </label>
                      <textarea
                        id="metadata_json"
                        name="metadata_json"
                        value={formData.metadata_json}
                        onChange={handleChange}
                        disabled={loading}
                        rows={4}
                        placeholder='{ "key": "value" }'
                        className={`${styles.textarea} ${styles.jsonTextarea} ${!isMetadataJsonValid ? styles.invalidJson : ""}`}
                      />
                      {!isMetadataJsonValid && (
                        <span className={styles.fieldErrorText}>Invalid JSON formatting. Please correct before submitting.</span>
                      )}
                    </div>

                    <div className={styles.formActions} style={{ marginTop: '1.5rem' }}>
                      <button type="button" onClick={() => setCurrentWizardStep(1)} className={styles.cancelBtn}>
                        Back
                      </button>

                      {isEditMode && (
                        <button
                          type="button"
                          onClick={() => setIsDeleteModalOpen(true)}
                          disabled={loading}
                          className={styles.deleteBtn}
                        >
                          Delete
                        </button>
                      )}

                      <div className={styles.rightActions}>
                        <button
                          type="button"
                          onClick={onClose}
                          disabled={loading}
                          className={styles.cancelBtn}
                        >
                          Cancel
                        </button>
                        <button
                          type="submit"
                          disabled={loading || !isMetadataJsonValid}
                          className={styles.submitBtn}
                        >
                          {loading ? "Saving..." : "Save Model"}
                        </button>
                      </div>
                    </div>
                  </div>
                )}
              </WizardShell>
            </form>
          )}

          {activeTab === "relationships" && (
            <RelationshipViewer entityType="MODEL" entityId={modelId!} />
          )}

          {activeTab === "audit" && (
            <AuditTrailViewer entityType="MODEL" entityId={modelId!} />
          )}
        </div>
      </div>
      
      {isEditMode && (
        <ConfirmDeleteModal
          isOpen={isDeleteModalOpen}
          onClose={() => setIsDeleteModalOpen(false)}
          onConfirm={handleDelete}
          entityName={formData.model_name || formData.model_code || 'Model'}
          entityType="Model"
          isDeleting={isDeleting}
        />
      )}
    </Modal>
  );
};

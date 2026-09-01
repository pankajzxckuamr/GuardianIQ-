import React, { useState, useEffect } from "react";
import { PageHeader } from "../components/common/PageHeader";
import {
  Play,
  ShieldAlert,
  AlertTriangle,
  Layers,
  CheckCircle2,
  XCircle,
  Sparkles,
  RefreshCw,
  Cpu,
  Wrench,
  Database,
  Bot,
  RotateCcw,
} from "lucide-react";
import { simulateEnforcement, SimulationResult, SimulationPayload } from "../services/enforcement/enforcementService";
import { listAgents, listTools, listDataSources, listModels } from "../services/registry/registryService";
import type { AIAgent, Tool, DataSource, AIModel } from "../services/registry/registryTypes";
import styles from "./PoliciesPage.module.css";

export const EnforcementSimulationPage: React.FC = () => {
  // Registry Asset Lists
  const [agentsList, setAgentsList] = useState<AIAgent[]>([]);
  const [toolsList, setToolsList] = useState<Tool[]>([]);
  const [dataSourcesList, setDataSourcesList] = useState<DataSource[]>([]);
  const [modelsList, setModelsList] = useState<AIModel[]>([]);

  // Form State - Default to clean, empty placeholder states
  const [agentId, setAgentId] = useState("");
  const [isCustomAgent, setIsCustomAgent] = useState(false);

  const [operation, setOperation] = useState("");
  const [role, setRole] = useState("OPERATOR");
  const [environment, setEnvironment] = useState("PRODUCTION");

  const [toolId, setToolId] = useState("");
  const [isCustomTool, setIsCustomTool] = useState(false);
  const [toolParams, setToolParams] = useState("");

  const [dataSourceId, setDataSourceId] = useState("");
  const [isCustomDataSource, setIsCustomDataSource] = useState(false);
  const [columns, setColumns] = useState("");

  const [modelId, setModelId] = useState("");
  const [isCustomModel, setIsCustomModel] = useState(false);

  const [activeScenario, setActiveScenario] = useState<string | null>(null);

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<SimulationResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Fetch registered assets on mount without overwriting empty form inputs
  useEffect(() => {
    loadRegistryAssets();
  }, []);

  const loadRegistryAssets = async () => {
    try {
      const [agentsRes, toolsRes, dataSourcesRes, modelsRes] = await Promise.allSettled([
        listAgents({ per_page: 100 }),
        listTools({ per_page: 100 }),
        listDataSources({ per_page: 100 }),
        listModels({ per_page: 100 }),
      ]);

      if (agentsRes.status === "fulfilled" && agentsRes.value?.data) {
        const raw = agentsRes.value.data as any;
        const items = Array.isArray(raw) ? raw : raw.items || [];
        setAgentsList(items);
      }

      if (toolsRes.status === "fulfilled" && toolsRes.value?.data) {
        const raw = toolsRes.value.data as any;
        const items = Array.isArray(raw) ? raw : raw.items || [];
        setToolsList(items);
      }

      if (dataSourcesRes.status === "fulfilled" && dataSourcesRes.value?.data) {
        const raw = dataSourcesRes.value.data as any;
        const items = Array.isArray(raw) ? raw : raw.items || [];
        setDataSourcesList(items);
      }

      if (modelsRes.status === "fulfilled" && modelsRes.value?.data) {
        const raw = modelsRes.value.data as any;
        const items = Array.isArray(raw) ? raw : raw.items || [];
        setModelsList(items);
      }
    } catch {
      // Non-blocking fallback
    }
  };

  // Selected tool's allowed operations helper
  const selectedTool = toolsList.find((t) => t.id === toolId);
  const allowedToolOps: string[] = Array.isArray(selectedTool?.allowed_operations_json)
    ? (selectedTool.allowed_operations_json as string[])
    : [];

  // Reset form to pure empty placeholder state
  const handleResetForm = () => {
    setActiveScenario(null);
    setAgentId("");
    setIsCustomAgent(false);
    setOperation("");
    setRole("OPERATOR");
    setEnvironment("PRODUCTION");
    setToolId("");
    setIsCustomTool(false);
    setToolParams("");
    setDataSourceId("");
    setIsCustomDataSource(false);
    setColumns("");
    setModelId("");
    setIsCustomModel(false);
    setResult(null);
    setError(null);
  };

  // Pre-set Scenarios - Only populated when user explicitly selects one
  const loadScenario = (type: string) => {
    setActiveScenario(type);
    setResult(null);
    setError(null);

    switch (type) {
      case "SAFE_READ": {
        const dqs = agentsList.find((a) => a.agent_name.toLowerCase().includes("dataquality") || a.agent_name.toLowerCase().includes("compliance") || a.id === "06453af4-8a9b-4641-b1a6-2a43532cbef4") || agentsList[0];
        const lineageTool = toolsList.find((t) => t.tool_name.toLowerCase().includes("lineage") || t.id === "1ec4d1e8-6e26-458f-b40e-d09f27621105") || toolsList[0];
        if (dqs) setAgentId(dqs.id);
        setIsCustomAgent(false);
        setOperation("fetch_dependency_graph");
        setRole("ANALYST");
        setEnvironment("PRODUCTION");
        if (lineageTool) setToolId(lineageTool.id);
        setIsCustomTool(false);
        setToolParams("{}");
        setDataSourceId("");
        setIsCustomDataSource(false);
        setColumns("");
        setModelId("");
        setIsCustomModel(false);
        break;
      }
      case "DATA_MASKING_PII": {
        const onboardAgent = agentsList.find((a) => a.agent_name.toLowerCase().includes("onboarding") || a.id === "857aeb22-e2e9-4ac5-be89-a3851e5548c7") || agentsList[0];
        const workdayDs = dataSourcesList.find((d) => d.source_name.toLowerCase().includes("workday") || d.source_name.toLowerCase().includes("employee") || d.id === "eb5741c2-d609-4eed-b8a8-eca945d1d865") || dataSourcesList[0];
        if (onboardAgent) setAgentId(onboardAgent.id);
        setIsCustomAgent(false);
        setOperation("read_employee_data");
        setRole("SUPPORT_AGENT");
        setEnvironment("PRODUCTION");
        setToolId("");
        setIsCustomTool(false);
        setToolParams("");
        if (workdayDs) setDataSourceId(workdayDs.id);
        setIsCustomDataSource(false);
        setColumns("name, email, department");
        setModelId("");
        setIsCustomModel(false);
        break;
      }
      case "HIGH_VALUE_APPROVAL": {
        const refundAgent = agentsList.find((a) => a.agent_name.toLowerCase().includes("refund") || a.id === "fd3dccb8-2359-42f9-b617-99b4aa3c370e") || agentsList[0];
        const stripeTool = toolsList.find((t) => t.tool_name.toLowerCase().includes("stripe") || t.id === "8c81de00-14a5-4e83-bb6a-99fb28949f4b") || toolsList[0];
        if (refundAgent) setAgentId(refundAgent.id);
        setIsCustomAgent(false);
        setOperation("create_refund");
        setRole("OPERATOR");
        setEnvironment("PRODUCTION");
        if (stripeTool) setToolId(stripeTool.id);
        setIsCustomTool(false);
        setToolParams('{"amount": 5000, "currency": "USD"}');
        setDataSourceId("");
        setIsCustomDataSource(false);
        setColumns("");
        setModelId("");
        setIsCustomModel(false);
        break;
      }
      case "TOOL_WRITE_UNAUTHORIZED": {
        const dqs = agentsList.find((a) => a.agent_name.toLowerCase().includes("dataquality") || a.id === "06453af4-8a9b-4641-b1a6-2a43532cbef4") || agentsList[0];
        const freezeTool = toolsList.find((t) => t.tool_name.toLowerCase().includes("banking") || t.tool_name.toLowerCase().includes("freeze") || t.id === "fd3eeb81-03de-467b-b0bf-daf1ad8ee6fb") || toolsList[0];
        if (dqs) setAgentId(dqs.id);
        setIsCustomAgent(false);
        setOperation("freeze_account");
        setRole("OPERATOR");
        setEnvironment("PRODUCTION");
        if (freezeTool) setToolId(freezeTool.id);
        setIsCustomTool(false);
        setToolParams('{"account_number": "ACC-998811", "reason": "Suspected Fraud"}');
        setDataSourceId("");
        setIsCustomDataSource(false);
        setColumns("");
        setModelId("");
        setIsCustomModel(false);
        break;
      }
    }
  };

  const handleSimulate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!agentId.trim()) {
      setError("Please select or enter an Agent ID.");
      return;
    }

    if (!operation.trim()) {
      setError("Please enter or select a governed operation.");
      return;
    }

    setLoading(true);
    setError(null);

    let parsedParams = {};
    if (toolParams.trim()) {
      try {
        parsedParams = JSON.parse(toolParams);
      } catch {
        setError("Tool parameters must be valid JSON.");
        setLoading(false);
        return;
      }
    }

    const payload: SimulationPayload = {
      agent_id: agentId.trim(),
      operation: operation.trim(),
      role: role.trim() || undefined,
      environment: environment.trim() || undefined,
      tool_id: toolId.trim() || undefined,
      tool_parameters: Object.keys(parsedParams).length > 0 ? parsedParams : undefined,
      data_source_id: dataSourceId.trim() || undefined,
      requested_columns: columns.trim() ? columns.split(",").map((c) => c.trim()) : undefined,
      model_id: modelId.trim() || undefined,
    };

    try {
      const res = await simulateEnforcement(payload);
      setResult(res.data);
    } catch (err: any) {
      setError(err.message || "Failed to execute simulation.");
    } finally {
      setLoading(false);
    }
  };

  const getDecisionBadge = (decision: string) => {
    switch (decision) {
      case "ALLOW":
        return (
          <div style={{
            display: "flex",
            alignItems: "center",
            gap: "12px",
            padding: "16px",
            background: "rgba(16, 185, 129, 0.15)",
            border: "1px solid rgba(16, 185, 129, 0.3)",
            borderRadius: "12px",
            color: "#34d399"
          }}>
            <CheckCircle2 size={32} />
            <div>
              <div style={{ fontSize: "1.1rem", fontWeight: 700 }}>DECISION: ALLOW</div>
              <div style={{ fontSize: "0.8rem", color: "#a7f3d0" }}>
                Target execution fully permitted with zero boundary violations.
              </div>
            </div>
          </div>
        );
      case "ALLOW_WITH_OBLIGATIONS":
        return (
          <div style={{
            display: "flex",
            alignItems: "center",
            gap: "12px",
            padding: "16px",
            background: "rgba(6, 182, 212, 0.15)",
            border: "1px solid rgba(6, 182, 212, 0.3)",
            borderRadius: "12px",
            color: "#38bdf8"
          }}>
            <Sparkles size={32} />
            <div>
              <div style={{ fontSize: "1.1rem", fontWeight: 700 }}>DECISION: ALLOW WITH OBLIGATIONS</div>
              <div style={{ fontSize: "0.8rem", color: "#bae6fd" }}>
                Execution permitted subject to dynamic transformation (e.g. data masking or auditing).
              </div>
            </div>
          </div>
        );
      case "REQUIRE_APPROVAL":
        return (
          <div style={{
            display: "flex",
            alignItems: "center",
            gap: "12px",
            padding: "16px",
            background: "rgba(245, 158, 11, 0.15)",
            border: "1px solid rgba(245, 158, 11, 0.3)",
            borderRadius: "12px",
            color: "#fbbf24"
          }}>
            <AlertTriangle size={32} />
            <div>
              <div style={{ fontSize: "1.1rem", fontWeight: 700 }}>DECISION: REQUIRE_APPROVAL</div>
              <div style={{ fontSize: "0.8rem", color: "#fde68a" }}>
                Execution paused. Human-in-the-loop sign-off required before target invocation.
              </div>
            </div>
          </div>
        );
      case "DENY":
        return (
          <div style={{
            display: "flex",
            alignItems: "center",
            gap: "12px",
            padding: "16px",
            background: "rgba(239, 68, 68, 0.15)",
            border: "1px solid rgba(239, 68, 68, 0.3)",
            borderRadius: "12px",
            color: "#f87171"
          }}>
            <XCircle size={32} />
            <div>
              <div style={{ fontSize: "1.1rem", fontWeight: 700 }}>DECISION: DENY</div>
              <div style={{ fontSize: "0.8rem", color: "#fca5a5" }}>
                Target execution blocked at boundary gateway.
              </div>
            </div>
          </div>
        );
      default:
        return (
          <div style={{
            display: "flex",
            alignItems: "center",
            gap: "12px",
            padding: "16px",
            background: "rgba(255, 255, 255, 0.05)",
            border: "1px solid rgba(255, 255, 255, 0.1)",
            borderRadius: "12px",
            color: "var(--text-primary, #f8fafc)"
          }}>
            <ShieldAlert size={32} />
            <div>
              <div style={{ fontSize: "1.1rem", fontWeight: 700 }}>DECISION: {decision}</div>
            </div>
          </div>
        );
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "24px", paddingBottom: "48px" }}>
      <PageHeader
        title="Runtime Enforcement Simulator"
        description="Simulate multi-layered governance checks across hard boundaries, tool permissions, data classifications, and dynamic AST rules with zero target side-effects."
      />

      {/* Preset Scenarios Strip */}
      <div style={{
        background: "var(--bg-tertiary, #151d30)",
        border: "1px solid var(--card-border, rgba(99, 102, 241, 0.2))",
        borderRadius: "12px",
        padding: "16px 20px",
        display: "flex",
        flexDirection: "column",
        gap: "12px"
      }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "8px", fontWeight: 700, fontSize: "0.85rem", color: "var(--text-secondary, #94a3b8)" }}>
            <Sparkles className="w-4 h-4 text-indigo-400" />
            <span>PRE-CONFIGURED SIMULATION SCENARIOS</span>
          </div>

          {activeScenario && (
            <button
              type="button"
              onClick={handleResetForm}
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "6px",
                padding: "4px 10px",
                borderRadius: "6px",
                fontSize: "0.75rem",
                background: "rgba(239, 68, 68, 0.1)",
                border: "1px solid rgba(239, 68, 68, 0.3)",
                color: "#f87171",
                cursor: "pointer"
              }}
            >
              <RotateCcw size={12} /> Clear Scenario / Reset Fields
            </button>
          )}
        </div>

        <div style={{ display: "flex", gap: "10px", flexWrap: "wrap" }}>
          <button
            type="button"
            onClick={() => loadScenario("SAFE_READ")}
            style={{
              padding: "8px 14px",
              borderRadius: "8px",
              fontSize: "0.8rem",
              fontWeight: 600,
              background: activeScenario === "SAFE_READ" ? "rgba(99, 102, 241, 0.3)" : "rgba(99, 102, 241, 0.12)",
              border: activeScenario === "SAFE_READ" ? "1px solid #818cf8" : "1px solid rgba(99, 102, 241, 0.3)",
              color: activeScenario === "SAFE_READ" ? "#ffffff" : "#a5b4fc",
              cursor: "pointer"
            }}
          >
            Standard Safe READ
          </button>
          <button
            type="button"
            onClick={() => loadScenario("DATA_MASKING_PII")}
            style={{
              padding: "8px 14px",
              borderRadius: "8px",
              fontSize: "0.8rem",
              fontWeight: 600,
              background: activeScenario === "DATA_MASKING_PII" ? "rgba(6, 182, 212, 0.3)" : "rgba(6, 182, 212, 0.12)",
              border: activeScenario === "DATA_MASKING_PII" ? "1px solid #22d3ee" : "1px solid rgba(6, 182, 212, 0.3)",
              color: activeScenario === "DATA_MASKING_PII" ? "#ffffff" : "#67e8f9",
              cursor: "pointer"
            }}
          >
            PII Data Masking
          </button>
          <button
            type="button"
            onClick={() => loadScenario("HIGH_VALUE_APPROVAL")}
            style={{
              padding: "8px 14px",
              borderRadius: "8px",
              fontSize: "0.8rem",
              fontWeight: 600,
              background: activeScenario === "HIGH_VALUE_APPROVAL" ? "rgba(245, 158, 11, 0.3)" : "rgba(245, 158, 11, 0.12)",
              border: activeScenario === "HIGH_VALUE_APPROVAL" ? "1px solid #fbbf24" : "1px solid rgba(245, 158, 11, 0.3)",
              color: activeScenario === "HIGH_VALUE_APPROVAL" ? "#ffffff" : "#fde047",
              cursor: "pointer"
            }}
          >
            High-Value Threshold (Approval Required)
          </button>
          <button
            type="button"
            onClick={() => loadScenario("TOOL_WRITE_UNAUTHORIZED")}
            style={{
              padding: "8px 14px",
              borderRadius: "8px",
              fontSize: "0.8rem",
              fontWeight: 600,
              background: activeScenario === "TOOL_WRITE_UNAUTHORIZED" ? "rgba(239, 68, 68, 0.3)" : "rgba(239, 68, 68, 0.12)",
              border: activeScenario === "TOOL_WRITE_UNAUTHORIZED" ? "1px solid #f87171" : "1px solid rgba(239, 68, 68, 0.3)",
              color: activeScenario === "TOOL_WRITE_UNAUTHORIZED" ? "#ffffff" : "#fca5a5",
              cursor: "pointer"
            }}
          >
            Unauthorized Tool WRITE (Denial)
          </button>
        </div>
      </div>

      {/* Simulator Form & Results Grid */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1.3fr", gap: "20px", alignItems: "start" }}>
        {/* Left Column: Request Builder */}
        <div className={styles.cardSection}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px", fontWeight: 700, fontSize: "0.95rem", color: "var(--text-primary, #f8fafc)" }}>
              <Play className="w-4 h-4 text-indigo-400" /> Runtime Request Builder
            </div>
            {(agentId || operation || toolId || toolParams || dataSourceId || columns || modelId) && (
              <button
                type="button"
                onClick={handleResetForm}
                style={{
                  background: "transparent",
                  border: "none",
                  color: "var(--text-muted, #64748b)",
                  fontSize: "0.75rem",
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  gap: "4px"
                }}
              >
                <RotateCcw size={12} /> Clear all
              </button>
            )}
          </div>

          <form onSubmit={handleSimulate} style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
            {/* Agent Selector */}
            <div className={styles.formGroup}>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                <label className={styles.formLabel} style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                  <Bot size={14} className="text-indigo-400" /> Target AI Agent <span style={{ color: "#ef4444" }}>*</span>
                </label>
                <button
                  type="button"
                  onClick={() => setIsCustomAgent(!isCustomAgent)}
                  style={{ background: "transparent", border: "none", color: "#818cf8", fontSize: "0.7rem", cursor: "pointer" }}
                >
                  {isCustomAgent ? "Pick from Registry" : "Enter Custom UUID"}
                </button>
              </div>

              {isCustomAgent ? (
                <input
                  type="text"
                  required
                  placeholder="Enter Agent UUID..."
                  value={agentId}
                  onChange={(e) => setAgentId(e.target.value)}
                  className={styles.formInput}
                  style={{ fontFamily: "monospace", fontSize: "0.8rem" }}
                />
              ) : (
                <select
                  required
                  value={agentId}
                  onChange={(e) => setAgentId(e.target.value)}
                  className={styles.formSelect}
                  style={{ fontSize: "0.85rem" }}
                >
                  <option value="">Select an AI Agent...</option>
                  {agentsList.map((a) => (
                    <option key={a.id} value={a.id}>
                      {a.agent_name} ({a.risk_level || "MEDIUM"} Risk)
                    </option>
                  ))}
                </select>
              )}
            </div>

            {/* Governed Operation & Environment */}
            <div style={{ display: "grid", gridTemplateColumns: "1.2fr 1fr", gap: "12px" }}>
              <div className={styles.formGroup}>
                <label className={styles.formLabel}>
                  Governed Operation <span style={{ color: "#ef4444" }}>*</span>
                </label>
                {allowedToolOps.length > 0 ? (
                  <select
                    required
                    value={operation}
                    onChange={(e) => setOperation(e.target.value)}
                    className={styles.formSelect}
                    style={{ fontSize: "0.85rem" }}
                  >
                    <option value="">Select an operation...</option>
                    {allowedToolOps.map((op) => (
                      <option key={op} value={op}>{op}</option>
                    ))}
                  </select>
                ) : (
                  <input
                    type="text"
                    required
                    placeholder="Enter operation (e.g. execute, read_records)..."
                    value={operation}
                    onChange={(e) => setOperation(e.target.value)}
                    className={styles.formInput}
                    style={{ fontFamily: "monospace", fontSize: "0.8rem" }}
                  />
                )}
              </div>
              <div className={styles.formGroup}>
                <label className={styles.formLabel}>Environment</label>
                <select
                  value={environment}
                  onChange={(e) => setEnvironment(e.target.value)}
                  className={styles.formSelect}
                >
                  <option value="PRODUCTION">PRODUCTION</option>
                  <option value="STAGING">STAGING</option>
                  <option value="DEVELOPMENT">DEVELOPMENT</option>
                </select>
              </div>
            </div>

            {/* Tool Selector */}
            <div className={styles.formGroup}>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                <label className={styles.formLabel} style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                  <Wrench size={14} className="text-indigo-400" /> Tool Target (optional)
                </label>
                <button
                  type="button"
                  onClick={() => setIsCustomTool(!isCustomTool)}
                  style={{ background: "transparent", border: "none", color: "#818cf8", fontSize: "0.7rem", cursor: "pointer" }}
                >
                  {isCustomTool ? "Pick from Registry" : "Enter Custom UUID"}
                </button>
              </div>

              {isCustomTool ? (
                <input
                  type="text"
                  placeholder="Enter Tool UUID..."
                  value={toolId}
                  onChange={(e) => setToolId(e.target.value)}
                  className={styles.formInput}
                  style={{ fontFamily: "monospace", fontSize: "0.8rem" }}
                />
              ) : (
                <select
                  value={toolId}
                  onChange={(e) => {
                    const newToolId = e.target.value;
                    setToolId(newToolId);
                    const sel = toolsList.find((t) => t.id === newToolId);
                    if (sel && Array.isArray(sel.allowed_operations_json) && sel.allowed_operations_json.length > 0) {
                      setOperation((sel.allowed_operations_json as string[])[0]);
                    }
                  }}
                  className={styles.formSelect}
                  style={{ fontSize: "0.85rem" }}
                >
                  <option value="">None (No Tool Invocation)</option>
                  {toolsList.map((t) => (
                    <option key={t.id} value={t.id}>
                      {t.tool_name} ({t.access_mode || "EXECUTE"})
                    </option>
                  ))}
                </select>
              )}
            </div>

            {/* Tool Parameters */}
            <div className={styles.formGroup}>
              <label className={styles.formLabel}>Tool Parameters (JSON)</label>
              <textarea
                rows={2}
                placeholder='Enter JSON parameters: { "amount": 5000, "currency": "USD" }'
                value={toolParams}
                onChange={(e) => setToolParams(e.target.value)}
                className={styles.formTextarea}
                style={{ fontFamily: "monospace", fontSize: "0.8rem" }}
              />
            </div>

            {/* Data Source Selector */}
            <div className={styles.formGroup}>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                <label className={styles.formLabel} style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                  <Database size={14} className="text-indigo-400" /> Data Source (optional)
                </label>
                <button
                  type="button"
                  onClick={() => setIsCustomDataSource(!isCustomDataSource)}
                  style={{ background: "transparent", border: "none", color: "#818cf8", fontSize: "0.7rem", cursor: "pointer" }}
                >
                  {isCustomDataSource ? "Pick from Registry" : "Enter Custom UUID"}
                </button>
              </div>

              {isCustomDataSource ? (
                <input
                  type="text"
                  placeholder="Enter Data Source UUID..."
                  value={dataSourceId}
                  onChange={(e) => setDataSourceId(e.target.value)}
                  className={styles.formInput}
                  style={{ fontFamily: "monospace", fontSize: "0.8rem" }}
                />
              ) : (
                <select
                  value={dataSourceId}
                  onChange={(e) => setDataSourceId(e.target.value)}
                  className={styles.formSelect}
                  style={{ fontSize: "0.85rem" }}
                >
                  <option value="">None (No Data Source Access)</option>
                  {dataSourcesList.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.source_name} ({d.classification || "INTERNAL"})
                    </option>
                  ))}
                </select>
              )}
            </div>

            {/* Columns */}
            <div className={styles.formGroup}>
              <label className={styles.formLabel}>Requested Columns (comma-separated)</label>
              <input
                type="text"
                placeholder="Enter columns to request (e.g. name, email, ssn)..."
                value={columns}
                onChange={(e) => setColumns(e.target.value)}
                className={styles.formInput}
                style={{ fontFamily: "monospace", fontSize: "0.8rem" }}
              />
            </div>

            {/* Model Selector */}
            <div className={styles.formGroup}>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                <label className={styles.formLabel} style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                  <Cpu size={14} className="text-indigo-400" /> AI Model (optional)
                </label>
                <button
                  type="button"
                  onClick={() => setIsCustomModel(!isCustomModel)}
                  style={{ background: "transparent", border: "none", color: "#818cf8", fontSize: "0.7rem", cursor: "pointer" }}
                >
                  {isCustomModel ? "Pick from Registry" : "Enter Custom UUID"}
                </button>
              </div>

              {isCustomModel ? (
                <input
                  type="text"
                  placeholder="Enter Model UUID..."
                  value={modelId}
                  onChange={(e) => setModelId(e.target.value)}
                  className={styles.formInput}
                  style={{ fontFamily: "monospace", fontSize: "0.8rem" }}
                />
              ) : (
                <select
                  value={modelId}
                  onChange={(e) => setModelId(e.target.value)}
                  className={styles.formSelect}
                  style={{ fontSize: "0.85rem" }}
                >
                  <option value="">None (No Model Invocation)</option>
                  {modelsList.map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.model_name} ({m.provider_name || m.model_type || "Model"})
                    </option>
                  ))}
                </select>
              )}
            </div>

            {error && (
              <div style={{
                padding: "10px 14px",
                borderRadius: "8px",
                background: "rgba(239, 68, 68, 0.15)",
                border: "1px solid rgba(239, 68, 68, 0.3)",
                color: "#f87171",
                fontSize: "0.8rem"
              }}>
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className={styles.primaryBtn}
              style={{ width: "100%", justifyContent: "center", marginTop: "8px" }}
            >
              {loading ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" /> Evaluating Simulation...
                </>
              ) : (
                <>
                  <Play className="w-4 h-4" /> Run Non-Authoritative Simulation
                </>
              )}
            </button>
          </form>
        </div>

        {/* Right Column: Simulation Output & Decision Trace */}
        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          {!result ? (
            <div className={styles.cardSection} style={{ padding: "64px 24px", textAlign: "center", alignItems: "center" }}>
              <Layers size={48} style={{ color: "var(--text-muted, #64748b)", marginBottom: "16px" }} />
              <div style={{ fontSize: "0.95rem", color: "var(--text-secondary, #94a3b8)", maxWidth: "340px" }}>
                Select an agent and optional targets on the left, or pick a scenario above to simulate runtime governance evaluation.
              </div>
            </div>
          ) : (
            <>
              {/* Overall Outcome Card */}
              {getDecisionBadge(result.decision)}

              {/* Layer-by-Layer Verification Breakdown */}
              <div className={styles.cardSection}>
                <div style={{ fontSize: "0.875rem", fontWeight: 700, color: "var(--text-primary, #f8fafc)", marginBottom: "12px" }}>
                  Layer-by-Layer Verification Breakdown
                </div>

                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
                  {/* Layer 1: Boundary */}
                  <div style={{
                    padding: "12px",
                    borderRadius: "8px",
                    background: "rgba(10, 14, 23, 0.6)",
                    border: "1px solid rgba(255, 255, 255, 0.05)"
                  }}>
                    <div style={{ fontSize: "0.75rem", color: "var(--text-secondary, #94a3b8)", marginBottom: "4px" }}>
                      1. Hard Boundaries
                    </div>
                    <div style={{ fontWeight: 700, fontSize: "0.85rem", color: result.trace?.boundary_check?.permitted !== false ? "#34d399" : "#f87171" }}>
                      {result.trace?.boundary_check?.permitted !== false ? "PASSED" : "FAILED / VIOLATED"}
                    </div>
                    <div style={{ fontSize: "0.7rem", color: "var(--text-muted, #64748b)", marginTop: "4px" }}>
                      Kill-switch, max autonomy level, environment check
                    </div>
                  </div>

                  {/* Layer 2: Tool Guard */}
                  <div style={{
                    padding: "12px",
                    borderRadius: "8px",
                    background: "rgba(10, 14, 23, 0.6)",
                    border: "1px solid rgba(255, 255, 255, 0.05)"
                  }}>
                    <div style={{ fontSize: "0.75rem", color: "var(--text-secondary, #94a3b8)", marginBottom: "4px" }}>
                      2. Tool Guard
                    </div>
                    <div style={{
                      fontWeight: 700,
                      fontSize: "0.85rem",
                      color: !result.trace?.tool_guard?.evaluated
                        ? "var(--text-muted, #64748b)"
                        : result.trace?.tool_guard?.permitted
                        ? "#34d399"
                        : "#f87171"
                    }}>
                      {!result.trace?.tool_guard?.evaluated ? "SKIPPED (No Tool)" : (result.trace?.tool_guard?.decision || "ALLOW")}
                    </div>
                    <div style={{ fontSize: "0.7rem", color: "var(--text-muted, #64748b)", marginTop: "4px" }}>
                      Tool permission &amp; operation scope verification
                    </div>
                  </div>

                  {/* Layer 3: Data Guard */}
                  <div style={{
                    padding: "12px",
                    borderRadius: "8px",
                    background: "rgba(10, 14, 23, 0.6)",
                    border: "1px solid rgba(255, 255, 255, 0.05)"
                  }}>
                    <div style={{ fontSize: "0.75rem", color: "var(--text-secondary, #94a3b8)", marginBottom: "4px" }}>
                      3. Data Guard
                    </div>
                    <div style={{
                      fontWeight: 700,
                      fontSize: "0.85rem",
                      color: !result.trace?.data_guard?.evaluated
                        ? "var(--text-muted, #64748b)"
                        : result.trace?.data_guard?.permitted
                        ? "#34d399"
                        : "#f87171"
                    }}>
                      {!result.trace?.data_guard?.evaluated ? "SKIPPED (No Data Source)" : (result.trace?.data_guard?.decision || "ALLOW")}
                    </div>
                    <div style={{ fontSize: "0.7rem", color: "var(--text-muted, #64748b)", marginTop: "4px" }}>
                      Classification ceiling &amp; field masking
                    </div>
                  </div>

                  {/* Layer 4: Combiner */}
                  <div style={{
                    padding: "12px",
                    borderRadius: "8px",
                    background: "rgba(10, 14, 23, 0.6)",
                    border: "1px solid rgba(255, 255, 255, 0.05)"
                  }}>
                    <div style={{ fontSize: "0.75rem", color: "var(--text-secondary, #94a3b8)", marginBottom: "4px" }}>
                      4. Policy Combiner
                    </div>
                    <div style={{ fontWeight: 700, fontSize: "0.85rem", color: "#818cf8" }}>
                      {result.trace?.combiner?.combined_decision || result.decision}
                    </div>
                    <div style={{ fontSize: "0.7rem", color: "var(--text-muted, #64748b)", marginTop: "4px" }}>
                      Precedence resolution: DENY &gt; APPROVAL &gt; ALLOW
                    </div>
                  </div>
                </div>
              </div>

              {/* Obligations & Remediation Breakdown */}
              <div className={styles.cardSection}>
                <div style={{ fontSize: "0.875rem", fontWeight: 700, color: "var(--text-primary, #f8fafc)", marginBottom: "8px" }}>
                  Obligations &amp; Remediation Details
                </div>

                {(!result.violations || result.violations.length === 0) &&
                 (!result.obligations || result.obligations.length === 0) &&
                 (!result.remediation_hints || result.remediation_hints.length === 0) &&
                 !result.remediation_hint ? (
                  <div style={{ fontSize: "0.8rem", color: "#34d399" }}>
                    ✓ No active violations or remediation required.
                  </div>
                ) : (
                  <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                    {result.violations && result.violations.length > 0 && (
                      <div>
                        <div style={{ fontSize: "0.75rem", fontWeight: 600, color: "#f87171", marginBottom: "4px" }}>Violations:</div>
                        <ul style={{ margin: 0, paddingLeft: "16px", color: "#fca5a5", fontSize: "0.75rem" }}>
                          {result.violations.map((v, i) => (
                            <li key={i}>{typeof v === "object" ? JSON.stringify(v) : v}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {result.reasons && result.reasons.length > 0 && (
                      <div>
                        <div style={{ fontSize: "0.75rem", fontWeight: 600, color: "#fbbf24", marginBottom: "4px" }}>Decision Reasons:</div>
                        <ul style={{ margin: 0, paddingLeft: "16px", color: "#fde68a", fontSize: "0.75rem" }}>
                          {result.reasons.map((r, i) => (
                            <li key={i}>{r}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {result.obligations && result.obligations.length > 0 && (
                      <div>
                        <div style={{ fontSize: "0.75rem", fontWeight: 600, color: "#38bdf8", marginBottom: "4px" }}>Runtime Obligations:</div>
                        <ul style={{ margin: 0, paddingLeft: "16px", color: "#bae6fd", fontSize: "0.75rem" }}>
                          {result.obligations.map((o, i) => (
                            <li key={i}>{JSON.stringify(o)}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {result.remediation_hints && result.remediation_hints.length > 0 && (
                      <div>
                        <div style={{ fontSize: "0.75rem", fontWeight: 600, color: "#a5b4fc", marginBottom: "4px" }}>Remediation Hints:</div>
                        <ul style={{ margin: 0, paddingLeft: "16px", color: "#c7d2fe", fontSize: "0.75rem" }}>
                          {result.remediation_hints.map((h, i) => (
                            <li key={i}>{h}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {result.remediation_hint && (
                      <div style={{
                        padding: "10px 12px",
                        borderRadius: "8px",
                        background: "rgba(99, 102, 241, 0.12)",
                        border: "1px solid rgba(99, 102, 241, 0.25)",
                        fontSize: "0.8rem",
                        color: "#c7d2fe"
                      }}>
                        <strong>Remediation Hint:</strong> {result.remediation_hint}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default EnforcementSimulationPage;

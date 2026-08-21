import React, { useState } from "react";
import { PageHeader } from "../components/common/PageHeader";
import {
  Play,
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  Layers,
  Database,
  Wrench,
  Cpu,
  CheckCircle2,
  XCircle,
  HelpCircle,
  Sparkles,
  RefreshCw,
  Copy,
  Info,
} from "lucide-react";
import { simulateEnforcement, SimulationResult, SimulationPayload } from "../services/enforcement/enforcementService";
import styles from "./PoliciesPage.module.css";

export const EnforcementSimulationPage: React.FC = () => {
  const [agentId, setAgentId] = useState("550e8400-e29b-41d4-a716-446655440000");
  const [operation, setOperation] = useState("execute_trade");
  const [role, setRole] = useState("OPERATOR");
  const [environment, setEnvironment] = useState("PRODUCTION");
  const [toolId, setToolId] = useState("");
  const [toolParams, setToolParams] = useState('{"amount": 25000, "currency": "USD"}');
  const [dataSourceId, setDataSourceId] = useState("");
  const [columns, setColumns] = useState("account_number, balance, ssn");
  const [modelId, setModelId] = useState("");

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<SimulationResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Pre-set Scenarios
  const loadScenario = (type: string) => {
    switch (type) {
      case "SAFE_READ":
        setAgentId("550e8400-e29b-41d4-a716-446655440000");
        setOperation("read_market_summary");
        setRole("ANALYST");
        setEnvironment("PRODUCTION");
        setToolId("");
        setToolParams("{}");
        setDataSourceId("");
        setColumns("");
        setModelId("");
        break;
      case "TOOL_WRITE_UNAUTHORIZED":
        setAgentId("550e8400-e29b-41d4-a716-446655440000");
        setOperation("execute_order");
        setRole("OPERATOR");
        setEnvironment("PRODUCTION");
        setToolId("tool-trading-engine-01");
        setToolParams('{"action": "BUY", "shares": 500}');
        setDataSourceId("");
        setColumns("");
        break;
      case "DATA_MASKING_PII":
        setAgentId("550e8400-e29b-41d4-a716-446655440000");
        setOperation("generate_customer_statement");
        setRole("SUPPORT_AGENT");
        setEnvironment("PRODUCTION");
        setToolId("");
        setToolParams("{}");
        setDataSourceId("ds-customer-db");
        setColumns("customer_name, email, ssn, credit_card");
        break;
      case "HIGH_VALUE_APPROVAL":
        setAgentId("550e8400-e29b-41d4-a716-446655440000");
        setOperation("transfer_funds");
        setRole("FINANCE_AGENT");
        setEnvironment("PRODUCTION");
        setToolId("tool-wire-transfer");
        setToolParams('{"amount": 500000, "beneficiary": "Acme Corp"}');
        setDataSourceId("");
        setColumns("");
        break;
    }
  };

  const handleSimulate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!agentId.trim()) {
      setError("Agent ID is required.");
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
              <div style={{ fontSize: "1.1rem", fontWeight: 700 }}>DECISION: ALLOW_WITH_OBLIGATIONS</div>
              <div style={{ fontSize: "0.8rem", color: "#bae6fd" }}>
                Permitted conditionally with mandatory runtime data transformations or logging obligations.
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
                Execution paused pending human reviewer authorization.
              </div>
            </div>
          </div>
        );
      case "ESCALATE":
        return (
          <div style={{
            display: "flex",
            alignItems: "center",
            gap: "12px",
            padding: "16px",
            background: "rgba(168, 85, 247, 0.15)",
            border: "1px solid rgba(168, 85, 247, 0.3)",
            borderRadius: "12px",
            color: "#c084fc"
          }}>
            <ShieldAlert size={32} />
            <div>
              <div style={{ fontSize: "1.1rem", fontWeight: 700 }}>DECISION: ESCALATE</div>
              <div style={{ fontSize: "0.8rem", color: "#e9d5ff" }}>
                High-criticality risk triggered security escalation routing.
              </div>
            </div>
          </div>
        );
      case "DENY":
      default:
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
    }
  };

  return (
    <div className={styles.container}>
      <PageHeader
        title="Runtime Enforcement Simulator"
        description="Simulate multi-layered governance checks across hard boundaries, tool permissions, data classifications, and dynamic AST rules with zero target side-effects."
      />

      {/* Pre-set Scenarios Toolbar */}
      <div className={styles.cardSection}>
        <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "8px" }}>
          <Sparkles className="w-4 h-4 text-indigo-400" />
          <span style={{ fontSize: "0.75rem", fontWeight: 700, textTransform: "uppercase", color: "var(--text-secondary, #94a3b8)", letterSpacing: "0.05em" }}>
            Pre-configured Simulation Scenarios
          </span>
        </div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: "10px" }}>
          <button
            type="button"
            onClick={() => loadScenario("SAFE_READ")}
            style={{
              padding: "8px 14px",
              borderRadius: "8px",
              fontSize: "0.8rem",
              fontWeight: 600,
              background: "rgba(99, 102, 241, 0.12)",
              border: "1px solid rgba(99, 102, 241, 0.3)",
              color: "#a5b4fc",
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
              background: "rgba(6, 182, 212, 0.12)",
              border: "1px solid rgba(6, 182, 212, 0.3)",
              color: "#67e8f9",
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
              background: "rgba(245, 158, 11, 0.12)",
              border: "1px solid rgba(245, 158, 11, 0.3)",
              color: "#fcd34d",
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
              background: "rgba(239, 68, 68, 0.12)",
              border: "1px solid rgba(239, 68, 68, 0.3)",
              color: "#fca5a5",
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
          <div style={{ display: "flex", alignItems: "center", gap: "8px", fontWeight: 700, fontSize: "0.95rem", color: "var(--text-primary, #f8fafc)" }}>
            <Play className="w-4 h-4 text-indigo-400" /> Runtime Request Builder
          </div>

          <form onSubmit={handleSimulate} style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
            <div className={styles.formGroup}>
              <label className={styles.formLabel}>Agent ID (UUID)</label>
              <input
                type="text"
                required
                value={agentId}
                onChange={(e) => setAgentId(e.target.value)}
                className={styles.formInput}
                style={{ fontFamily: "monospace", fontSize: "0.8rem" }}
              />
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
              <div className={styles.formGroup}>
                <label className={styles.formLabel}>Governed Operation</label>
                <input
                  type="text"
                  required
                  value={operation}
                  onChange={(e) => setOperation(e.target.value)}
                  className={styles.formInput}
                  style={{ fontFamily: "monospace", fontSize: "0.8rem" }}
                />
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

            <div className={styles.formGroup}>
              <label className={styles.formLabel}>Tool Target ID (optional)</label>
              <input
                type="text"
                placeholder="e.g. tool-wire-transfer"
                value={toolId}
                onChange={(e) => setToolId(e.target.value)}
                className={styles.formInput}
                style={{ fontFamily: "monospace", fontSize: "0.8rem" }}
              />
            </div>

            <div className={styles.formGroup}>
              <label className={styles.formLabel}>Tool Parameters (JSON)</label>
              <textarea
                rows={3}
                value={toolParams}
                onChange={(e) => setToolParams(e.target.value)}
                className={styles.formTextarea}
                style={{ fontFamily: "monospace", fontSize: "0.8rem" }}
              />
            </div>

            <div className={styles.formGroup}>
              <label className={styles.formLabel}>Data Source ID (optional)</label>
              <input
                type="text"
                placeholder="e.g. ds-customer-db"
                value={dataSourceId}
                onChange={(e) => setDataSourceId(e.target.value)}
                className={styles.formInput}
                style={{ fontFamily: "monospace", fontSize: "0.8rem" }}
              />
            </div>

            <div className={styles.formGroup}>
              <label className={styles.formLabel}>Requested Columns (comma-separated)</label>
              <input
                type="text"
                placeholder="ssn, balance, email"
                value={columns}
                onChange={(e) => setColumns(e.target.value)}
                className={styles.formInput}
                style={{ fontFamily: "monospace", fontSize: "0.8rem" }}
              />
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
                Configure request parameters and click <strong>Run Simulation</strong> to inspect multi-layer boundary evaluation.
              </div>
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
              {/* Authoritative Combined Decision */}
              {getDecisionBadge(result.decision)}

              {/* Multi-Layer Evaluation Cards */}
              <div className={styles.cardSection}>
                <div style={{ fontSize: "0.9rem", fontWeight: 700, color: "var(--text-primary, #f8fafc)", marginBottom: "8px" }}>
                  Layer-by-Layer Verification Breakdown
                </div>

                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
                  {/* Layer 1: Boundary Check */}
                  <div style={{
                    padding: "14px",
                    borderRadius: "10px",
                    background: "var(--bg-tertiary, #151d30)",
                    border: "1px solid var(--card-border, rgba(99, 102, 241, 0.2))"
                  }}>
                    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "6px" }}>
                      <span style={{ fontSize: "0.75rem", fontWeight: 700, color: "var(--text-secondary, #94a3b8)" }}>
                        1. Hard Boundaries
                      </span>
                      {result.trace?.boundary_check?.passed ? (
                        <CheckCircle2 size={16} className="text-emerald-400" />
                      ) : (
                        <XCircle size={16} className="text-rose-400" />
                      )}
                    </div>
                    <div style={{ fontSize: "0.85rem", fontWeight: 600, color: "var(--text-primary, #f8fafc)" }}>
                      {result.trace?.boundary_check?.decision || "PASSED"}
                    </div>
                    <div style={{ fontSize: "0.75rem", color: "var(--text-muted, #64748b)", marginTop: "4px" }}>
                      Kill-switch, max autonomy level, environment check
                    </div>
                  </div>

                  {/* Layer 2: Tool Guard */}
                  <div style={{
                    padding: "14px",
                    borderRadius: "10px",
                    background: "var(--bg-tertiary, #151d30)",
                    border: "1px solid var(--card-border, rgba(99, 102, 241, 0.2))"
                  }}>
                    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "6px" }}>
                      <span style={{ fontSize: "0.75rem", fontWeight: 700, color: "var(--text-secondary, #94a3b8)" }}>
                        2. Tool Guard
                      </span>
                      {result.trace?.tool_guard?.passed ? (
                        <CheckCircle2 size={16} className="text-emerald-400" />
                      ) : (
                        <XCircle size={16} className="text-rose-400" />
                      )}
                    </div>
                    <div style={{ fontSize: "0.85rem", fontWeight: 600, color: "var(--text-primary, #f8fafc)" }}>
                      {result.trace?.tool_guard?.decision || "ALLOW"}
                    </div>
                    <div style={{ fontSize: "0.75rem", color: "var(--text-muted, #64748b)", marginTop: "4px" }}>
                      Tool permission & operation scope verification
                    </div>
                  </div>

                  {/* Layer 3: Data Guard */}
                  <div style={{
                    padding: "14px",
                    borderRadius: "10px",
                    background: "var(--bg-tertiary, #151d30)",
                    border: "1px solid var(--card-border, rgba(99, 102, 241, 0.2))"
                  }}>
                    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "6px" }}>
                      <span style={{ fontSize: "0.75rem", fontWeight: 700, color: "var(--text-secondary, #94a3b8)" }}>
                        3. Data Guard
                      </span>
                      {result.trace?.data_guard?.passed ? (
                        <CheckCircle2 size={16} className="text-emerald-400" />
                      ) : (
                        <XCircle size={16} className="text-rose-400" />
                      )}
                    </div>
                    <div style={{ fontSize: "0.85rem", fontWeight: 600, color: "var(--text-primary, #f8fafc)" }}>
                      {result.trace?.data_guard?.decision || "ALLOW"}
                    </div>
                    <div style={{ fontSize: "0.75rem", color: "var(--text-muted, #64748b)", marginTop: "4px" }}>
                      Classification ceiling & field masking
                    </div>
                  </div>

                  {/* Layer 4: Policy Combiner */}
                  <div style={{
                    padding: "14px",
                    borderRadius: "10px",
                    background: "var(--bg-tertiary, #151d30)",
                    border: "1px solid var(--card-border, rgba(99, 102, 241, 0.2))"
                  }}>
                    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "6px" }}>
                      <span style={{ fontSize: "0.75rem", fontWeight: 700, color: "var(--text-secondary, #94a3b8)" }}>
                        4. Policy Combiner
                      </span>
                      <ShieldCheck size={16} className="text-indigo-400" />
                    </div>
                    <div style={{ fontSize: "0.85rem", fontWeight: 600, color: "var(--text-primary, #f8fafc)" }}>
                      {result.decision}
                    </div>
                    <div style={{ fontSize: "0.75rem", color: "var(--text-muted, #64748b)", marginTop: "4px" }}>
                      Precedence resolution: DENY &gt; APPROVAL &gt; ALLOW
                    </div>
                  </div>
                </div>
              </div>

              {/* Obligations & Remediation Hints */}
              {(result.obligations?.length || result.violations?.length || result.remediation_hint) && (
                <div className={styles.cardSection}>
                  <div style={{ fontSize: "0.9rem", fontWeight: 700, color: "var(--text-primary, #f8fafc)" }}>
                    Obligations & Remediation Details
                  </div>

                  {result.violations && result.violations.length > 0 && (
                    <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                      <span style={{ fontSize: "0.75rem", fontWeight: 600, color: "#f87171" }}>Violations:</span>
                      {result.violations.map((v: string, i: number) => (
                        <div key={i} style={{ fontSize: "0.8rem", color: "#fca5a5", display: "flex", gap: "6px" }}>
                          • <span>{v}</span>
                        </div>
                      ))}
                    </div>
                  )}

                  {result.obligations && result.obligations.length > 0 && (
                    <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                      <span style={{ fontSize: "0.75rem", fontWeight: 600, color: "#38bdf8" }}>Runtime Obligations:</span>
                      {result.obligations.map((o: any, i: number) => (
                        <div key={i} style={{ fontSize: "0.8rem", color: "#bae6fd", display: "flex", gap: "6px" }}>
                          • <span>{typeof o === "string" ? o : JSON.stringify(o)}</span>
                        </div>
                      ))}
                    </div>
                  )}

                  {result.remediation_hint && (
                    <div style={{
                      padding: "12px",
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
          )}
        </div>
      </div>
    </div>
  );
};

export default EnforcementSimulationPage;

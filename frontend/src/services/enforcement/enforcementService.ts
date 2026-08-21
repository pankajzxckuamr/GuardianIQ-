/* src/services/enforcement/enforcementService.ts */
import serverClient from "../shared/apiClient";
import type { ApiResponse } from "../registry/registryTypes";

export interface SimulationPayload {
  agent_id: string;
  actor_id?: string;
  role?: string;
  workflow_id?: string;
  model_id?: string;
  operation?: string;
  tool_id?: string;
  tool_name?: string;
  tool_parameters?: Record<string, any>;
  data_source_id?: string;
  table_name?: string;
  columns?: string[];
  data_operation?: string;
  environment?: string;
  facts?: Record<string, any>;
}

export interface RuleDetail {
  rule_id: string;
  rule_code?: string;
  rule_name?: string;
  matched: boolean;
  decision: string;
  reason?: string;
  severity?: string;
}

export interface SimulationTrace {
  boundary_check?: {
    evaluated: boolean;
    permitted?: boolean;
    reasons?: string[];
    max_autonomy?: string;
    kill_switch_active?: boolean;
  };
  tool_guard?: {
    evaluated: boolean;
    permitted?: boolean;
    reason?: string;
    tool_id?: string;
    access_mode?: string;
  };
  data_guard?: {
    evaluated: boolean;
    permitted?: boolean;
    reason?: string;
    data_source_id?: string;
    transformations?: Record<string, string>;
  };
  model_guard?: {
    evaluated: boolean;
    permitted?: boolean;
    reason?: string;
    model_id?: string;
  };
  policy_engine?: {
    evaluated: boolean;
    policies_evaluated_count?: number;
    matched_rules?: RuleDetail[];
    reasons?: string[];
  };
  combiner?: {
    combined_decision: string;
    precedence_applied: string;
  };
}

export interface SimulationResult {
  request_id: string;
  correlation_id: string;
  decision: "ALLOW" | "ALLOW_WITH_OBLIGATIONS" | "REQUIRE_APPROVAL" | "ESCALATE" | "DENY";
  execution_permitted: boolean;
  reasons: string[];
  obligations: string[];
  violations: Array<{ code?: string; message?: string } | string>;
  remediation_hints: string[];
  trace: SimulationTrace;
}

export async function simulateEnforcement(
  payload: SimulationPayload
): Promise<ApiResponse<SimulationResult>> {
  const res = await serverClient.post<any>("/api/v1/enforce/simulate", payload);
  return {
    status: "success",
    request_id: res.request_id || "",
    data: res.data,
    message: res.message || "Simulation evaluated successfully",
  };
}

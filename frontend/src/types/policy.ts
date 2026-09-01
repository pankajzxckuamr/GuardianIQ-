export type PolicyStatus = "DRAFT" | "ACTIVE" | "SUSPENDED" | "RETIRED";
export type PolicyCategory = "GENERAL" | "ACCESS_CONTROL" | "DATA_PROTECTION" | "FINANCIAL_SAFETY" | "OPERATIONAL_SAFETY" | "MODEL_SAFETY";
export type EnforcementMode = "BLOCKING" | "MONITORING" | "SHADOW";
export type TargetType = "AGENT" | "TOOL" | "DATA_SOURCE" | "WORKFLOW" | "MODEL" | "DEPARTMENT" | "TENANT";
export type VersionStrategy = "LATEST" | "PINNED_VERSION";

export interface PolicyRule {
  id?: string;
  rule_code: string;
  name: string;
  description?: string;
  rule_type: string;
  target_type: string;
  target_id?: string;
  condition_expression?: string;
  condition_json?: Record<string, any>;
  action: "ALLOW" | "DENY" | "MODIFY" | "REQUIRE_APPROVAL" | "ESCALATE";
  severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  execution_order: number;
  is_active: boolean;
}

export interface PolicyVersion {
  id: string;
  version_number: number;
  status: "DRAFT" | "ACTIVE" | "SUPERSEDED" | "RETIRED";
  changelog?: string;
  rules_count?: number;
  activated_at?: string;
  created_at?: string;
  rules?: PolicyRule[];
}

export interface Policy {
  id: string;
  policy_code: string;
  name: string;
  description?: string;
  category: PolicyCategory;
  enforcement_mode: EnforcementMode;
  priority: number;
  status: PolicyStatus;
  created_at?: string;
  active_version?: PolicyVersion;
  versions?: PolicyVersion[];
}

export interface PolicyBinding {
  id: string;
  policy_id: string;
  policy_name?: string;
  policy_code?: string;
  target_type: TargetType;
  target_id: string;
  target_name?: string;
  binding_scope?: string;
  priority: number;
  is_mandatory: boolean;
  version_strategy: VersionStrategy;
  pinned_policy_version_id?: string;
  status: "ACTIVE" | "SUSPENDED" | "REVOKED";
  created_at?: string;
}

export interface EffectiveBinding {
  id: string;
  policy_id: string;
  policy_name?: string;
  policy_code?: string;
  target_type: TargetType;
  target_id: string;
  target_name?: string;
  priority: number;
  is_mandatory: boolean;
  version_strategy: VersionStrategy;
  pinned_policy_version_id?: string;
  status: string;
  source?: "DIRECT" | "INHERITED";
}

export interface PolicyCreatePayload {
  policy_code: string;
  name: string;
  description?: string;
  category: PolicyCategory;
  enforcement_mode: EnforcementMode;
  priority: number;
  initial_rules?: PolicyRule[];
}

export interface PolicyBindingCreatePayload {
  policy_id: string;
  target_type: TargetType;
  target_id: string;
  binding_scope?: string;
  priority: number;
  is_mandatory: boolean;
  version_strategy: VersionStrategy;
  pinned_policy_version_id?: string;
}

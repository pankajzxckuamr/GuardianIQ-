/**
 * GuardianIQ Policy Engine & Runtime Boundary Enforcement Enums and Contracts
 * Frozen as part of Phase 5 MVP Scope (Prompt 1.2)
 */

export enum PolicyStatus {
  DRAFT = 'DRAFT',
  ACTIVE = 'ACTIVE',
  PAUSED = 'PAUSED',
  ARCHIVED = 'ARCHIVED',
  RETIRED = 'RETIRED',
}

export enum VersionStatus {
  DRAFT = 'DRAFT',
  ACTIVE = 'ACTIVE',
  DEPRECATED = 'DEPRECATED',
  ARCHIVED = 'ARCHIVED',
}

export enum BindingStatus {
  ACTIVE = 'ACTIVE',
  INACTIVE = 'INACTIVE',
  SUSPENDED = 'SUSPENDED',
}

export enum Decision {
  ALLOW = 'ALLOW',
  DENY = 'DENY',
  MODIFY = 'MODIFY',
  REQUIRE_APPROVAL = 'REQUIRE_APPROVAL',
  ESCALATE = 'ESCALATE',
  ALLOW_WITH_OBLIGATIONS = 'ALLOW_WITH_OBLIGATIONS',
}

export enum TargetType {
  AGENT = 'AGENT',
  TOOL = 'TOOL',
  DATA_SOURCE = 'DATA_SOURCE',
  WORKFLOW = 'WORKFLOW',
  MODEL = 'MODEL',
}

export enum VersionStrategy {
  LATEST = 'LATEST',
  PINNED = 'PINNED',
  STRICT_LATEST = 'STRICT_LATEST',
}

export enum AutonomyLevel {
  FULL_AUTONOMY = 'FULL_AUTONOMY',
  HUMAN_IN_THE_LOOP = 'HUMAN_IN_THE_LOOP',
  HUMAN_SUPERVISED = 'HUMAN_SUPERVISED',
  STRICT_OVERSIGHT = 'STRICT_OVERSIGHT',
}

export enum AccessMode {
  READ_ONLY = 'READ_ONLY',
  WRITE = 'WRITE',
  EXECUTE = 'EXECUTE',
  ADMIN = 'ADMIN',
  READ_WRITE = 'READ_WRITE',
}

export enum DataOperation {
  READ = 'READ',
  WRITE = 'WRITE',
  EXPORT = 'EXPORT',
  TRANSFORM = 'TRANSFORM',
  DELETE = 'DELETE',
  AGGREGATE = 'AGGREGATE',
}

export enum EnforcementMode {
  BLOCKING = 'BLOCKING',
  MONITORING = 'MONITORING',
  WARN = 'WARN',
  DRY_RUN = 'DRY_RUN',
}

export enum DataClassification {
  PUBLIC = 'PUBLIC',
  INTERNAL = 'INTERNAL',
  CONFIDENTIAL = 'CONFIDENTIAL',
  RESTRICTED = 'RESTRICTED',
}

export enum SensitivityLevel {
  LOW = 'LOW',
  MEDIUM = 'MEDIUM',
  HIGH = 'HIGH',
  CRITICAL = 'CRITICAL',
}

export interface ActorContext {
  user_id?: string;
  role?: string;
  department?: string;
  ip_address?: string;
  metadata?: Record<string, any>;
}

export interface AgentContext {
  agent_id: string;
  name?: string;
  agent_type?: string;
  autonomy_level?: AutonomyLevel;
  owner_user_id?: string;
  metadata?: Record<string, any>;
}

export interface WorkflowContext {
  workflow_id?: string;
  workflow_run_id?: string;
  step_id?: string;
  workflow_type?: string;
  metadata?: Record<string, any>;
}

export interface ModelContext {
  model_id?: string;
  name?: string;
  model_type?: string;
  provider?: string;
  metadata?: Record<string, any>;
}

export interface ToolContext {
  tool_id?: string;
  tool_name?: string;
  category?: string;
  parameters?: Record<string, any>;
  access_mode?: AccessMode;
}

export interface DataRequestContext {
  data_source_id: string;
  table_name?: string;
  columns?: string[];
  operation?: DataOperation;
  classification?: DataClassification;
  sensitivity_level?: SensitivityLevel;
  record_count?: number;
  query?: string;
  filter_criteria?: Record<string, any>;
}

export interface GovernedRuntimeRequest {
  request_id?: string; // UUID
  correlation_id?: string; // UUID
  actor?: ActorContext;
  agent?: AgentContext;
  workflow?: WorkflowContext;
  model?: ModelContext;
  operation?: string;
  tool?: ToolContext;
  data_requests?: DataRequestContext[];
  facts?: Record<string, any>;
  idempotency_key?: string;
  enforcement_mode?: EnforcementMode;
}

export interface RuleEvaluationDetail {
  rule_id: string;
  rule_name: string;
  rule_type: string;
  matched: boolean;
  decision: Decision;
  reason?: string;
  evaluation_order?: number;
}

export interface PolicyEvaluationResult {
  policy_id: string;
  policy_name: string;
  policy_version_id?: string;
  version_number?: number;
  decision: Decision;
  reason?: string;
  rule_evaluations?: RuleEvaluationDetail[];
}

export interface ApprovalRequirement {
  approval_type: string;
  tier_1_role?: string;
  tier_2_role?: string;
  reason: string;
  timeout_minutes: number;
  metadata?: Record<string, any>;
}

export interface ViolationDetail {
  policy_id?: string;
  rule_id?: string;
  violation_code: string;
  message: string;
  severity: string;
  target_type?: TargetType;
  target_id?: string;
}

export interface GovernedRuntimeResponse {
  request_id: string; // UUID
  correlation_id: string; // UUID
  decision: Decision;
  reasons: string[];
  enforced_at: string;
  modified_payload?: Record<string, any>;
  approval_requirements?: ApprovalRequirement[];
  violations: ViolationDetail[];
  policy_evaluations: PolicyEvaluationResult[];
  execution_permitted: boolean;
}

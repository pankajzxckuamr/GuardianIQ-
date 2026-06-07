/* src/services/registry/registryTypes.ts */

export enum EntityStatus {
  DRAFT = "DRAFT",
  PENDING_APPROVAL = "PENDING_APPROVAL",
  REJECTED = "REJECTED",
  ACTIVE = "ACTIVE",
  INACTIVE = "INACTIVE",
  SUSPENDED = "SUSPENDED",
  RETIRED = "RETIRED",
  ARCHIVED = "ARCHIVED"
}

export type RiskLevel = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

export type SensitivityLevel = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

export type DataClassification = "PUBLIC" | "INTERNAL" | "CONFIDENTIAL" | "RESTRICTED";

export type ModelType = "LLM" | "ML" | "CLASSIFIER" | "EMBEDDING" | "RULE_BASED" | "FORECASTING" | "OPTIMIZATION";

export type AgentType = "RECOMMENDATION" | "TRIAGE" | "EXTRACTION" | "EXECUTION" | "MONITORING";

export type ExecutionMode = "READ_ONLY" | "RECOMMEND_ONLY" | "APPROVAL_REQUIRED" | "LIMITED_EXECUTION" | "BLOCKED";

export type ToolCategory = "ERP" | "CRM" | "EMAIL" | "TICKETING" | "DATABASE" | "LLM" | "FILE" | "WEBHOOK";

export type AccessMode = "READ_ONLY" | "WRITE" | "EXECUTE" | "ADMIN";

export type WorkflowType = "ENQUIRY" | "APPROVAL" | "CUSTOMER_SIGNAL" | "RISK_REVIEW" | "OPERATIONAL_ACTION" | "AI_AGENT_PIPELINE";

export type SourceType = "DATABASE" | "API" | "FILE" | "CRM" | "ERP" | "DATA_LAKE" | "EMAIL" | "WEBFORM";

export type RelationshipType = "USES" | "OWNS" | "EXECUTES" | "APPROVES" | "GOVERNED_BY" | "CONNECTED_TO" | "CONSUMES" | "PRODUCES";

export interface AIModel {
  id: string;
  model_code?: string;
  model_name: string;
  model_version: string;
  model_type: ModelType;
  description?: string;
  status: EntityStatus;
  risk_level: RiskLevel;
  department_id?: string;
  created_at: string;
  updated_at: string;
  owner_name?: string;
  provider_name?: string;
}

export interface AIAgent {
  id: string;
  agent_code?: string;
  agent_name: string;
  agent_type: AgentType;
  execution_mode: ExecutionMode;
  description?: string;
  status: EntityStatus;
  risk_level: RiskLevel;
  department_id?: string;
  created_at: string;
  updated_at: string;
  owner_name?: string;
  provider_name?: string;
}

export interface Tool {
  id: string;
  tool_code?: string;
  tool_name: string;
  tool_category: ToolCategory;
  access_mode?: AccessMode;
  sensitivity_level?: SensitivityLevel;
  allowed_operations_json?: any;
  endpoint_reference?: string;
  owner_user_id?: string;
  description?: string;
  status: EntityStatus;
  metadata_json?: any;
  created_at: string;
  updated_at: string;
  owner_name?: string;
  provider_name?: string;
}

export interface Workflow {
  id: string;
  workflow_code?: string;
  workflow_name: string;
  workflow_type: WorkflowType;
  department_id?: string;
  owner_user_id?: string;
  approver_user_id?: string;
  description?: string;
  approval_required?: boolean;
  business_criticality?: string;
  steps_json?: any;
  status: EntityStatus;
  metadata_json?: any;
  created_at: string;
  updated_at: string;
  owner_name?: string;
  approver_name?: string;
  approver_email?: string;
}

export interface GuardianUser {
  id: string;
  full_name: string;
  email: string;
  status: EntityStatus;
  created_at: string;
  updated_at: string;
}

export interface RegistryRole {
  id: string;
  role_name: string;
  role_code: string;
  description?: string;
  status: EntityStatus;
  created_at: string;
  updated_at: string;
}

export interface RegistryDepartment {
  id: string;
  department_name: string;
  department_code: string;
  description?: string;
  status: EntityStatus;
  created_at: string;
  updated_at: string;
}

export interface DataSource {
  id: string;
  source_name: string;
  source_type: SourceType;
  classification: DataClassification;
  sensitivity: SensitivityLevel;
  status: EntityStatus;
  created_at: string;
  updated_at: string;
}

export interface RegistryRelationship {
  id: string;
  source_id: string;
  source_type: string;
  target_id: string;
  target_type: string;
  relationship_type: RelationshipType;
  created_at: string;
}

export interface RegistryAuditEvent {
  id: string;
  entity_id: string;
  entity_type: string;
  action: string;
  performed_by: string;
  timestamp: string;
  details?: string;
}

export interface PaginationMeta {
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface ListResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface ApiResponse<T> {
  status: string;
  request_id: string;
  data: T;
  message: string;
}

export interface RegistrySummary {
  models_count: number;
  agents_count: number;
  tools_count: number;
  workflows_count: number;
  users_count: number;
  departments_count: number;
  data_sources_count: number;
}

export interface SearchResults {
  models: AIModel[];
  agents: AIAgent[];
  tools: Tool[];
  workflows: Workflow[];
  data_sources: DataSource[];
}

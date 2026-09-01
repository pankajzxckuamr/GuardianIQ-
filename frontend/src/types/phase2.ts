export type ScheduleStatus = 'DRAFT' | 'PENDING_APPROVAL' | 'ACTIVE' | 'PAUSED' | 'FAILED' | 'RETIRED';
export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
export type RunStatus = 'QUEUED' | 'RUNNING' | 'COMPLETED' | 'FAILED' | 'CANCELLED' | 'SKIPPED' | 'RETRY_QUEUED';

export interface WorkflowScheduleListItem {
  id: string;
  schedule_code: string;
  schedule_name: string;
  workflow_name: string;
  schedule_type: string;
  schedule_status: ScheduleStatus;
  risk_level: RiskLevel;
  owner_name: string;
  next_run_at?: string;
  last_run_at?: string;
  approval_required: boolean;
  health_status: 'HEALTHY' | 'ATTENTION' | 'FAILED' | 'SLA_BREACHED';
}

export interface WorkflowScheduleResponse {
  id: string;
  schedule_code: string;
  schedule_name: string;
  workflow_id: string;
  schedule_type: string;
  cron_expression?: string;
  timezone: string;
  start_at?: string;
  end_at?: string;
  next_run_at?: string;
  last_run_at?: string;
  concurrency_policy: string;
  max_runtime_seconds: number;
  retry_policy_json?: any;
  owner_user_id: string;
  owner_department_id?: string;
  approval_required: boolean;
  approval_group_id?: string;
  risk_level: RiskLevel;
  schedule_status: ScheduleStatus;
  agent_assignments: AgentAssignmentResponse[];
  created_at: string;
  updated_at: string;
  version_no: number;
  health_status?: string;
  workflow_name?: string;
  owner_name?: string;
  is_overdue?: boolean;
}

export interface AgentAssignmentResponse {
  id?: string;
  schedule_id?: string;
  agent_id: string;
  agent_name?: string;
  model_id?: string;
  model_name?: string;
  assignment_role: string;
  execution_mode: string;
  confidence_threshold?: number;
  allowed_tools_json?: string[];
  allowed_data_sources_json?: string[];
  blocked_operations_json?: string[];
  boundary_rules_json?: any;
  status: string;
}

export interface WorkflowRunResponse {
  id: string;
  tenant_id: string;
  schedule_id: string;
  workflow_id: string;
  run_code: string;
  trigger_type: string;
  triggered_by_user_id?: string;
  triggered_by_actor_type: string;
  run_status: RunStatus;
  risk_level: string;
  started_at?: string;
  completed_at?: string;
  duration_ms?: number;
  context_json?: any;
  workflow_name?: string;
  triggered_by_name?: string;
  error_message?: string;
}

export interface WorkflowRunStepResponse {
  id: string;
  run_id: string;
  step_code: string;
  step_order: number;
  step_type: string;
  step_status: string;
  started_at?: string;
  completed_at?: string;
  duration_ms?: number;
  error_message?: string;
  error_detail?: any;
  input_json?: any;
  output_json?: any;
}

export interface WorkflowRunOutputResponse {
  id: string;
  run_id: string;
  output_type: string;
  output_content: string;
  risk_level: string;
  severity?: string;
  risk_score?: number;
  requires_review: boolean;
  is_approved?: boolean;
}

export interface NotificationResponse {
  id: string;
  recipient_user_id: string;
  notification_type: string;
  title: string;
  message: string;
  severity: string;
  entity_type?: string;
  entity_id?: string;
  status: string;
  read_at?: string;
  acknowledged_at?: string;
  created_at: string;
}

export interface ApprovalResponse {
  id: string;
  schedule_id: string;
  approval_type: string;
  approval_status: string;
  decision_reason?: string;
  decided_at?: string;
  submitted_by?: string;
  approver_user_id?: string;
  approver_name?: string;
  approver_email?: string;
  decided_by?: string;
  decided_by_name?: string;
  decided_by_email?: string;
  department_name?: string;
  department_code?: string;
  approval_layer?: number;
  skip_reason?: string;
  created_at: string;
}

export interface HistoryResponse {
  id: string;
  schedule_id: string;
  change_type: string;
  change_summary?: string;
  before_json?: any;
  after_json?: any;
  changed_by?: string;
  changed_by_name?: string;
  created_at: string;
}

export interface AuditTimelineEvent {
  id: string;
  action_type: string;
  event_summary: string;
  actor_name: string;
  created_at: string;
}


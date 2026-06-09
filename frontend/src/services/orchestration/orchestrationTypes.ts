export interface ExecutionFinding {
  id: string;
  execution_id: string;
  severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  description: string;
  recommendation_text?: string;
  created_at: string;
}

export interface ExecutionEventLog {
  id: string;
  execution_id: string;
  event_type: string;
  details?: string;
  timestamp: string;
}

export interface WorkflowExecution {
  id: string;
  workflow_id: string;
  workflow_name?: string;
  status: "PENDING" | "RUNNING" | "COMPLETED" | "FAILED" | "AWAITING_APPROVAL" | "REJECTED" | "REVOKED";
  is_dry_run: boolean;
  started_at: string;
  completed_at?: string;
  completed_steps?: number;
  total_steps?: number;
}

export interface ExecutionDetails extends WorkflowExecution {
  logs?: ExecutionEventLog[];
  findings?: ExecutionFinding[];
}

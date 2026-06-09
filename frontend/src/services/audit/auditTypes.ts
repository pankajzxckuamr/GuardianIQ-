/* src/services/audit/auditTypes.ts */

export interface AuditEvent {
  id: string;
  event_type: string;
  actor_id?: string;
  actor_username?: string;
  tenant_id?: string;
  resource_type?: string;
  resource_id?: string;
  ip_address?: string;
  user_agent?: string;
  status: "success" | "failure";
  detail?: string;
  created_at: string;
}

export interface AuditQueryParams {
  page?: number;
  per_page?: number;
  event_type?: string;
  actor_id?: string;
  created_after?: string;
}

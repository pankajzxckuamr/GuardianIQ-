/* src/services/audit/auditService.ts */
import type { AuditEvent, AuditQueryParams } from "./auditTypes";
import type { PaginatedResponse } from "../../types/api";
import { generateRequestId } from "../shared/requestId";
import { parseErrorResponse } from "../shared/serviceErrors";

const AUDIT_BASE = "/api/audit";

function auditHeaders(token: string): HeadersInit {
  return {
    "Content-Type": "application/json",
    "X-Request-ID": generateRequestId(),
    "Authorization": `Bearer ${token}`,
  };
}

export async function fetchAuditEvents(
  token: string,
  params: AuditQueryParams = {}
): Promise<PaginatedResponse<AuditEvent>> {
  const query = new URLSearchParams();
  if (params.page) query.set("page", String(params.page));
  if (params.per_page) query.set("per_page", String(params.per_page));
  if (params.event_type) query.set("event_type", params.event_type);
  if (params.actor_id) query.set("actor_id", params.actor_id);
  if (params.created_after) query.set("created_after", params.created_after);

  const res = await fetch(`${AUDIT_BASE}/events?${query.toString()}`, {
    headers: auditHeaders(token),
    credentials: "include",
  });
  if (!res.ok) throw await parseErrorResponse(res);
  const body = await res.json();
  return body.data ?? body;
}

export interface GovernanceEventFilterParams {
  page?: number;
  pageSize?: number;
  event_type?: string;
  event_category?: string;
  classification?: string;
  search?: string;
  start_date?: string;
  end_date?: string;
}

export async function fetchGovernanceEvents(
  token: string,
  params: GovernanceEventFilterParams = {}
) {
  const query = new URLSearchParams();
  if (params.page) query.set("page", String(params.page));
  if (params.pageSize) query.set("page_size", String(params.pageSize));
  if (params.event_type) query.set("event_type", params.event_type);
  if (params.event_category) query.set("event_category", params.event_category);
  if (params.classification) query.set("classification", params.classification);
  if (params.search) query.set("event_type", params.search);

  const res = await fetch(`/api/v1/events?${query.toString()}`, {
    headers: auditHeaders(token),
    credentials: "include",
  });
  if (!res.ok) throw await parseErrorResponse(res);
  const body = await res.json();
  return body.data ?? body;
}

export async function fetchGovernanceEventById(token: string, eventId: string) {
  const res = await fetch(`/api/v1/events/${eventId}`, {
    headers: auditHeaders(token),
    credentials: "include",
  });
  if (!res.ok) throw await parseErrorResponse(res);
  const body = await res.json();
  return body.data ?? body;
}

export async function fetchSubjectTimeline(token: string, entityType: string, entityId: string) {
  const res = await fetch(`/api/v1/audit/timeline/${entityType}/${entityId}`, {
    headers: auditHeaders(token),
    credentials: "include",
  });
  if (!res.ok) throw await parseErrorResponse(res);
  const body = await res.json();
  return body.data ?? body;
}

export async function fetchCorrelationTimeline(token: string, correlationId: string) {
  const res = await fetch(`/api/v1/events/correlation/${correlationId}`, {
    headers: auditHeaders(token),
    credentials: "include",
  });
  if (!res.ok) throw await parseErrorResponse(res);
  const body = await res.json();
  return body.data ?? body;
}

export interface DeadLetterEvent {
  id: string;
  outbox_id: string;
  event_id: string;
  tenant_id: string;
  failure_reason: string;
  failed_at: string;
  retry_attempts: number;
  status: "UNRESOLVED" | "RESOLVED";
  resolved_at?: string;
  resolved_by?: string;
}

export async function fetchDeadLetterEvents(token: string): Promise<DeadLetterEvent[]> {
  const res = await fetch("/api/v1/events/dead-letter", {
    headers: auditHeaders(token),
    credentials: "include",
  });
  if (!res.ok) throw await parseErrorResponse(res);
  const body = await res.json();
  const data = body.data ?? body;
  return Array.isArray(data) ? data : [];
}

export async function retryDeadLetterEvent(token: string, deadLetterId: string): Promise<DeadLetterEvent> {
  const res = await fetch(`/api/v1/events/dead-letter/${deadLetterId}/retry`, {
    method: "POST",
    headers: auditHeaders(token),
    credentials: "include",
  });
  if (!res.ok) throw await parseErrorResponse(res);
  const body = await res.json();
  return body.data ?? body;
}

export interface AuditExportFilterParams {
  subject_type?: string;
  subject_id?: string;
  correlation_id?: string;
  start_date?: string;
  end_date?: string;
  event_type?: string;
  classification?: string;
  reason?: string;
}

export interface AuditExportPayload {
  filter_params?: AuditExportFilterParams;
  export_format?: "JSON" | "CSV";
}

export interface AuditExportResult {
  export_id: string;
  tenant_id?: string;
  requested_by?: string;
  status?: string;
  format?: string;
  event_count?: number;
  export_hash?: string;
  file_reference?: string;
  created_at?: string;
  manifest?: {
    manifest_version?: string;
    export_format?: string;
    generated_at?: string;
    total_records?: number;
    event_count?: number;
    export_hash?: string;
    scope_json?: any;
    event_ids?: string[];
    [key: string]: any;
  };
  events?: any[];
  [key: string]: any;
}

export async function fetchAuditExportsList(token: string): Promise<AuditExportResult[]> {
  const res = await fetch("/api/v1/audit/export", {
    headers: auditHeaders(token),
    credentials: "include",
  });
  if (!res.ok) throw await parseErrorResponse(res);
  const body = await res.json();
  return body.data ?? body;
}

export async function createAuditExport(token: string, payload: AuditExportPayload): Promise<AuditExportResult> {
  const query = new URLSearchParams();
  if (payload.export_format) query.set("export_format", payload.export_format);

  const res = await fetch(`/api/v1/audit/export?${query.toString()}`, {
    method: "POST",
    headers: auditHeaders(token),
    credentials: "include",
    body: JSON.stringify(payload.filter_params || {})
  });
  if (!res.ok) throw await parseErrorResponse(res);
  const body = await res.json();
  return body.data ?? body;
}

export async function getAuditExportStatus(token: string, exportId: string): Promise<AuditExportResult> {
  const res = await fetch(`/api/v1/audit/export/${exportId}`, {
    headers: auditHeaders(token),
    credentials: "include",
  });
  if (!res.ok) throw await parseErrorResponse(res);
  const body = await res.json();
  return body.data ?? body;
}

export interface EventMetrics {
  tenant_id: string;
  total_events_count: number;
  events_by_category: Record<string, number>;
  events_by_type: Record<string, number>;
  policy_violations_count: number;
  sla_breaches_count: number;
  blocked_agent_actions_count: number;
  outbox_lag_seconds: number;
  dead_letter_count: number;
  generated_at: string;
}

export async function fetchEventMetrics(token: string): Promise<EventMetrics> {
  const res = await fetch("/api/v1/events/metrics", {
    headers: auditHeaders(token),
    credentials: "include",
  });
  if (!res.ok) throw await parseErrorResponse(res);
  const body = await res.json();
  return body.data ?? body;
}

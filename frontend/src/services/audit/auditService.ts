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

  const res = await fetch(`${AUDIT_BASE}/events?${query.toString()}`, {
    headers: auditHeaders(token),
    credentials: "include",
  });
  if (!res.ok) throw await parseErrorResponse(res);
  const body = await res.json();
  return body.data ?? body;
}

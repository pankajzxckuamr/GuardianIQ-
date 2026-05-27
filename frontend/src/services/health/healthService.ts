/* src/services/health/healthService.ts */
import type { HealthStatus, DbHealthStatus } from "./healthTypes";
import { generateRequestId } from "../shared/requestId";
import { parseErrorResponse } from "../shared/serviceErrors";

const HEALTH_BASE = "/api/health";

function healthHeaders(): HeadersInit {
  return {
    "Content-Type": "application/json",
    "X-Request-ID": generateRequestId(),
  };
}

export async function fetchApiHealth(): Promise<HealthStatus> {
  const res = await fetch(`${HEALTH_BASE}`, { headers: healthHeaders() });
  if (!res.ok) throw await parseErrorResponse(res);
  const body = await res.json();
  return body.data ?? body;
}

export async function fetchDbHealth(): Promise<DbHealthStatus> {
  const res = await fetch(`${HEALTH_BASE}/db`, { headers: healthHeaders() });
  if (!res.ok) throw await parseErrorResponse(res);
  const body = await res.json();
  return body.data ?? body;
}

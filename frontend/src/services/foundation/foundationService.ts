/* src/services/foundation/foundationService.ts */
import type { FoundationMetadata } from "./foundationTypes";
import { generateRequestId } from "../shared/requestId";
import { parseErrorResponse } from "../shared/serviceErrors";

const FOUNDATION_BASE = "/api/foundation";

function foundationHeaders(token?: string): HeadersInit {
  const h: Record<string, string> = {
    "Content-Type": "application/json",
    "X-Request-ID": generateRequestId(),
  };
  if (token) h["Authorization"] = `Bearer ${token}`;
  return h;
}

export async function fetchFoundationMetadata(token: string): Promise<FoundationMetadata> {
  const res = await fetch(`${FOUNDATION_BASE}/metadata`, {
    headers: foundationHeaders(token),
    credentials: "include",
  });
  if (!res.ok) throw await parseErrorResponse(res);
  const body = await res.json();
  return body.data ?? body;
}

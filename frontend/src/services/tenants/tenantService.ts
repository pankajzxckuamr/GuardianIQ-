/* src/services/tenants/tenantService.ts */
import type { TenantRecord, CreateTenantPayload } from "./tenantTypes";
import type { PaginatedResponse } from "../../types/api";
import { generateRequestId } from "../shared/requestId";
import { parseErrorResponse } from "../shared/serviceErrors";

const TENANT_BASE = "/api/tenants";

function tenantHeaders(token: string): HeadersInit {
  return {
    "Content-Type": "application/json",
    "X-Request-ID": generateRequestId(),
    "Authorization": `Bearer ${token}`,
  };
}

function mapTenant(raw: Record<string, unknown>): TenantRecord {
  return {
    id: String(raw.id ?? ""),
    name: String(raw.name ?? ""),
    slug: String(raw.slug ?? ""),
    is_active: Boolean(raw.is_active),
    created_at: String(raw.created_at ?? ""),
    updated_at: raw.updated_at ? String(raw.updated_at) : undefined,
    owner_id: raw.owner_id ? String(raw.owner_id) : undefined,
    plan: raw.plan ? String(raw.plan) : undefined,
  };
}

export async function fetchTenants(
  token: string,
  page = 1,
  perPage = 20
): Promise<PaginatedResponse<TenantRecord>> {
  const res = await fetch(`${TENANT_BASE}?page=${page}&per_page=${perPage}`, {
    headers: tenantHeaders(token),
    credentials: "include",
  });
  if (!res.ok) throw await parseErrorResponse(res);
  const body = await res.json();
  const data = body.data ?? body;
  return {
    ...data,
    items: (data.items ?? []).map(mapTenant),
  };
}

export async function createTenant(
  token: string,
  payload: CreateTenantPayload
): Promise<TenantRecord> {
  const res = await fetch(TENANT_BASE, {
    method: "POST",
    headers: tenantHeaders(token),
    credentials: "include",
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw await parseErrorResponse(res);
  const body = await res.json();
  return mapTenant(body.data ?? body);
}

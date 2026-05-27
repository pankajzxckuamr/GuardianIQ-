import { ApiError } from '@/types/api';
import {
  AuditEvent,
  AuditEventResponse,
  AuditListResponse,
  AuditQueryParams,
} from './auditTypes';

// -----------------------------------------------------------------------
// Private helpers — self-contained, no shared singleton
// -----------------------------------------------------------------------

const DEVICE_ID_KEY = 'giq_device_id';

function generateUUID(): string {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    return (c === 'x' ? r : (r & 0x3) | 0x8).toString(16);
  });
}

function getDeviceId(): string {
  let id = localStorage.getItem(DEVICE_ID_KEY);
  if (!id) {
    id = generateUUID();
    localStorage.setItem(DEVICE_ID_KEY, id);
  }
  return id;
}

/**
 * Normalizes backend snake_case AuditEventResponse to the camelCase AuditEvent
 * used across the frontend. Keeps both representations clean and decoupled.
 */
function normalize(raw: AuditEventResponse): AuditEvent {
  return {
    id: raw.id,
    eventType: raw.event_type,
    entityType: raw.entity_type,
    entityId: raw.entity_id,
    actorUserId: raw.actor_user_id,
    action: raw.action,
    eventMetadata: raw.event_metadata,
    createdAt: raw.created_at,
  };
}

/**
 * Serializes AuditQueryParams to a URLSearchParams string.
 * Omits undefined/null values so the backend does not receive empty params.
 */
function buildQueryString(params: AuditQueryParams): string {
  const qs = new URLSearchParams();

  if (params.page !== undefined)      qs.set('page',      String(params.page));
  if (params.page_size !== undefined) qs.set('page_size', String(params.page_size));
  if (params.actor_id !== undefined)  qs.set('actor_id',  String(params.actor_id));
  if (params.action)                  qs.set('action',    params.action);
  if (params.from_date)               qs.set('from_date', params.from_date);
  if (params.to_date)                 qs.set('to_date',   params.to_date);

  const str = qs.toString();
  return str ? `?${str}` : '';
}

/**
 * Private fetch helper for the audit service.
 * Injects X-Request-ID, X-Device-ID, and Authorization headers.
 * Unwraps the StandardResponse<T> envelope; throws a typed ApiError on failure.
 *
 * @param method - HTTP method
 * @param path - Full path including query string
 * @param token - Bearer token (required for all audit endpoints)
 */
async function makeRequest<T>(
  method: string,
  path: string,
  token: string
): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`,
    'X-Request-ID': generateUUID(),
    'X-Device-ID': getDeviceId(),
  };

  const response = await fetch(path, { method, headers });

  let body: {
    status: string;
    message: string;
    data: T | null;
    error_code?: string;
    detail?: Array<Record<string, unknown>>;
  };

  try {
    body = await response.json();
  } catch {
    const error: ApiError = {
      error_code: response.status.toString(),
      message: `Failed to parse response from ${path}`,
      detail: [],
    };
    throw error;
  }

  if (!response.ok || body.status === 'error') {
    const error: ApiError = {
      error_code: body.error_code ?? response.status.toString(),
      message: body.message ?? response.statusText,
      detail: body.detail ?? [],
    };

    // Dispatch global 401 event so AuthContext can clear state
    if (response.status === 401) {
      window.dispatchEvent(new Event('giq:unauthorized'));
    }

    throw error;
  }

  return body.data as T;
}

// -----------------------------------------------------------------------
// Public API
// -----------------------------------------------------------------------

/**
 * Fetches a paginated list of audit events from GET /api/audit.
 *
 * The backend currently returns `StandardResponse<list[AuditEventResponse]>`
 * without pagination metadata. We construct a client-side AuditListResponse
 * wrapper so callers always receive a consistent paginated shape.
 *
 * @param params - Optional filtering and pagination parameters
 * @param token  - JWT Bearer token (required)
 * @returns Normalized and paginated AuditListResponse
 * @throws {ApiError} On non-2xx or envelope error
 */
async function getAuditEvents(
  params: AuditQueryParams,
  token: string
): Promise<AuditListResponse> {
  const qs = buildQueryString(params);
  const raw = await makeRequest<AuditEventResponse[]>('GET', `/api/audit${qs}`, token);

  const items = raw.map(normalize);

  return {
    items,
    total: items.length,
    page: params.page ?? 1,
    page_size: params.page_size ?? items.length,
  };
}

/**
 * Fetches a single audit event by ID from GET /api/audit/:id.
 *
 * Note: The current backend route uses GET /api/audit (list only).
 * This function targets the conventional REST path /api/audit/:id which
 * should be available in a future backend update. Until then the caller
 * can filter the list result.
 *
 * @param id    - The numeric ID of the audit event
 * @param token - JWT Bearer token (required)
 * @returns A single normalized AuditEvent
 * @throws {ApiError} On non-2xx or envelope error
 */
async function getAuditEvent(id: string, token: string): Promise<AuditEvent> {
  const raw = await makeRequest<AuditEventResponse>(
    'GET',
    `/api/audit/${encodeURIComponent(id)}`,
    token
  );
  return normalize(raw);
}

export const auditService = {
  getAuditEvents,
  getAuditEvent,
};

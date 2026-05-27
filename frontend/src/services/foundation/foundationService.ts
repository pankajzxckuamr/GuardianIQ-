import { ApiError } from '@/types/api';
import { EnumMap, EnumResponse } from './foundationTypes';

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
 * Private fetch helper for the foundation service.
 * Injects X-Request-ID and X-Device-ID headers on every call.
 * Unwraps the StandardResponse envelope and throws a typed ApiError on non-2xx.
 *
 * @param method - HTTP method
 * @param path - Absolute path relative to the origin (e.g. "/api/foundation/enums")
 * @param token - Optional Bearer token for authenticated endpoints
 */
async function makeRequest<T>(
  method: string,
  path: string,
  token?: string
): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    'X-Request-ID': generateUUID(),
    'X-Device-ID': getDeviceId(),
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(path, { method, headers });

  let body: { status: string; message: string; data: T | null; error_code?: string; detail?: Array<Record<string, unknown>> };

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
    throw error;
  }

  return body.data as T;
}

// -----------------------------------------------------------------------
// Public API
// -----------------------------------------------------------------------

/**
 * Fetches all system enum definitions from GET /api/foundation/enums.
 * Returns the unwrapped enum map: { SourceType: [...], RiskLevel: [...], ... }
 *
 * @throws {ApiError} On non-2xx response or envelope error status
 */
async function getEnums(): Promise<EnumMap> {
  return makeRequest<EnumMap>('GET', '/api/foundation/enums');
}

export const foundationService = {
  getEnums,
};

import { HealthResponse } from './healthTypes';

// -----------------------------------------------------------------------
// Shared internals — not exported, keeps service self-contained
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

async function healthFetch(path: string): Promise<HealthResponse> {
  const response = await fetch(path, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
      'X-Request-ID': generateUUID(),
      'X-Device-ID': getDeviceId(),
    },
  });

  const body: HealthResponse = await response.json();
  return body;
}

// -----------------------------------------------------------------------
// Public API
// -----------------------------------------------------------------------

/**
 * Calls GET /api/health.
 * Returns the full StandardResponse envelope so callers can read status + request_id.
 */
async function getAppHealth(): Promise<HealthResponse> {
  return healthFetch('/api/health');
}

/**
 * Calls GET /api/health/db.
 * Backend returns HTTP 503 on failure, but still with a valid JSON body.
 */
async function getDbHealth(): Promise<HealthResponse> {
  return healthFetch('/api/health/db');
}

export const healthService = {
  getAppHealth,
  getDbHealth,
};

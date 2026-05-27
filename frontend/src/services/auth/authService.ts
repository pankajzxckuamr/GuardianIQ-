import { 
  LoginRequest, 
  LoginResponse, 
  UserProfile, 
  RefreshResponse, 
  LogoutResponse, 
  RoleItem, 
  PermissionItem 
} from './authTypes';
import { StandardResponse, ApiError } from '../../types/api';

// In-memory token storage (module-level). 
// Prevents sensitive tokens from being persisted to disk/localStorage.
let inMemoryAccessToken: string | null = null;

/**
 * Generates a standard UUID v4.
 */
function generateUUID(): string {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    const r = Math.random() * 16 | 0;
    const v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}

/**
 * Generates or retrieves a stable, non-sensitive device fingerprint.
 * Persisted to localStorage to remain stable across sessions.
 */
function getDeviceId(): string {
  const key = 'giq_device_id';
  let deviceId = localStorage.getItem(key);
  if (!deviceId) {
    deviceId = generateUUID();
    localStorage.setItem(key, deviceId);
  }
  return deviceId;
}

/**
 * A private helper for auth service requests to enforce constraints:
 * - Content-Type JSON
 * - Unique X-Request-ID
 * - Stable X-Device-ID
 * - Unwraps StandardResponse and throws ApiError on non-2xx
 */
async function makeRequest<T>(
  method: string, 
  path: string, 
  body?: any, 
  token?: string | null,
  isFormUrlEncoded?: boolean
): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': isFormUrlEncoded ? 'application/x-www-form-urlencoded' : 'application/json',
    'X-Request-ID': generateUUID(),
    'X-Device-ID': getDeviceId()
  };

  const authToken = token || inMemoryAccessToken;
  if (authToken) {
    headers['Authorization'] = `Bearer ${authToken}`;
  }

  const options: RequestInit = {
    method,
    headers,
  };

  if (body) {
    options.body = isFormUrlEncoded ? body.toString() : JSON.stringify(body);
  }

  const response = await fetch(path, options);
  
  let data: any;
  try {
    data = await response.json();
  } catch (err) {
    // Failed to parse JSON, handle via status below
  }

  if (!response.ok) {
    // Throw a structured ApiError
    const error: ApiError = {
      error_code: data?.error_code || response.status.toString(),
      message: data?.message || response.statusText,
      detail: data?.detail || []
    };
    throw error;
  }
  
  // Unwrap the StandardResponse envelope
  const standardResponse = data as StandardResponse<T>;
  return standardResponse.data as T;
}

/**
 * Decentralized Authentication Service singleton.
 * Owns all auth operations and avoids shared API clients.
 */
export const authService = {
  getDeviceId,
  
  async login(request: LoginRequest): Promise<LoginResponse> {
    const formData = new URLSearchParams();
    formData.append('grant_type', 'password');
    formData.append('username', request.email);
    if (request.password) {
      formData.append('password', request.password);
    }

    const response = await makeRequest<LoginResponse>('POST', '/api/auth/login', formData, null, true);
    if (response && response.access_token) {
      inMemoryAccessToken = response.access_token;
    }
    return response;
  },
  
  async getProfile(): Promise<UserProfile> {
    return makeRequest<UserProfile>('GET', '/api/auth/me');
  },
  
  async refresh(): Promise<RefreshResponse> {
    const response = await makeRequest<RefreshResponse>('POST', '/api/auth/refresh');
    if (response && response.access_token) {
      inMemoryAccessToken = response.access_token;
    }
    return response;
  },
  
  async logout(): Promise<LogoutResponse> {
    const response = await makeRequest<LogoutResponse>('POST', '/api/auth/logout');
    inMemoryAccessToken = null;
    return response;
  },
  
  async getRoles(): Promise<RoleItem[]> {
    return makeRequest<RoleItem[]>('GET', '/api/auth/roles');
  },
  
  async getPermissions(): Promise<PermissionItem[]> {
    return makeRequest<PermissionItem[]>('GET', '/api/auth/permissions');
  },
  
  getToken(): string | null {
    return inMemoryAccessToken;
  }
};

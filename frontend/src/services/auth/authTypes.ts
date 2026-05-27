export interface LoginRequest {
  email: string;
  password?: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface UserProfile {
  id: string;
  email: string;
  name: string;
  roles: string[];
  permissions: string[];
}

export interface RefreshRequest {
  refresh_token?: string;
}

export interface RefreshResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface LogoutResponse {
  message?: string;
}

export interface RoleItem {
  id: string;
  name: string;
  description?: string;
}

export interface PermissionItem {
  id: string;
  name: string;
  description?: string;
}

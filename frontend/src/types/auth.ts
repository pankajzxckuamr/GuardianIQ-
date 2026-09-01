/* src/types/auth.ts */

export interface User {
  id: string;
  username?: string;
  name?: string;
  email: string;
  full_name?: string;
  roles: string[];
  permissions: string[];
  approval_groups?: string[];
  department_id?: string;
  tenant_id?: string;
  is_active?: boolean;
  is_superuser?: boolean;
  created_at?: string;
}

export interface AuthState {
  currentUser: User | null;
  isAuthenticated: boolean;
  loading: boolean;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in?: number;
  needs_password_change?: boolean;
}

export interface RefreshRequest {
  refresh_token: string;
}

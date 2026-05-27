/**
 * The payload required to authenticate a user.
 */
export interface LoginRequest {
  /** The user's email address */
  email: string;
  /** The user's password */
  password: string;
}

/**
 * The response received after a successful login attempt.
 */
export interface LoginResponse {
  /** The JWT access token */
  access_token: string;
  /** The type of token (usually "Bearer") */
  token_type: string;
  /** The number of seconds until the token expires */
  expires_in: number;
}

/**
 * Represents a user's profile and permissions within the system.
 */
export interface UserProfile {
  /** Unique identifier for the user */
  id: string;
  /** The user's email address */
  email: string;
  /** The user's full name */
  name: string;
  /** The roles assigned to the user */
  roles: string[];
  /** The specific permissions granted to the user */
  permissions: string[];
}

/**
 * Represents the current authentication state of the application.
 */
export interface AuthState {
  /** The authenticated user's profile, or null if not authenticated */
  user: UserProfile | null;
  /** Indicates whether the user is currently authenticated */
  isAuthenticated: boolean;
  /** Indicates if an authentication request is currently in progress */
  isLoading: boolean;
}

/**
 * Enum of available system permissions matching the backend RBAC seed.
 */
export enum Permission {
  SUPER_ADMIN = "SUPER_ADMIN",
  GOVERNANCE_ADMIN = "GOVERNANCE_ADMIN",
  RISK_ANALYST = "RISK_ANALYST",
  DATA_STEWARD = "DATA_STEWARD",
  AI_ENGINEER = "AI_ENGINEER",
  BUSINESS_USER = "BUSINESS_USER",
  AUDITOR = "AUDITOR",
  VIEWER = "VIEWER"
}

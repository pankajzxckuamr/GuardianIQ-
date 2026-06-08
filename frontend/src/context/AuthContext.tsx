import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import type { AuthState } from "../types/auth.ts";
import { login as apiLogin, logout as apiLogout, fetchMe as apiFetchMe, refreshAccessToken } from "../services/auth/authService.ts";
import { storage } from "../utils/storage.ts";
import { getErrorMessage } from "../utils/errors.ts";

interface AuthContextProps extends AuthState {
  login: (username: string, password: string) => Promise<{ needsPasswordChange: boolean }>;
  logout: () => Promise<void>;
  refreshSession: () => Promise<void>;
  completeFirstLogin: (accessToken: string) => Promise<void>;
}

const AuthContext = createContext<AuthContextProps | undefined>(undefined);

const ACCESS_TOKEN_KEY = "guardianiq_access_token";
const REFRESH_TOKEN_KEY = "guardianiq_refresh_token";
const USER_CACHE_KEY = "guardianiq_user";

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [state, setState] = useState<AuthState>({
    currentUser: null,
    isAuthenticated: false,
    loading: true,
  });

  const setTokens = (access: string, refresh: string) => {
    storage.set(ACCESS_TOKEN_KEY, access);
    storage.set(REFRESH_TOKEN_KEY, refresh);
  };

  const clearTokens = () => {
    storage.remove(ACCESS_TOKEN_KEY);
    storage.remove(REFRESH_TOKEN_KEY);
  };

  const loadUser = async (accessToken: string) => {
    try {
      const user = await apiFetchMe(accessToken);
      storage.set(USER_CACHE_KEY, user);
      setState({ currentUser: user, isAuthenticated: true, loading: false });
    } catch (e) {
      console.error("Failed to fetch current user:", e);
      
      // Determine if it's an explicit 401/403 authentication error
      const isAuthError = e && typeof e === "object" && "status" in e && ((e as any).status === 401 || (e as any).status === 403);
      
      if (isAuthError) {
        clearTokens();
        storage.remove(USER_CACHE_KEY);
        setState({ currentUser: null, isAuthenticated: false, loading: false });
      } else {
        // Server is offline or network error. Try to restore last known cached session
        const cachedUser = storage.get<any>(USER_CACHE_KEY);
        if (cachedUser) {
          setState({ currentUser: cachedUser, isAuthenticated: true, loading: false });
        } else {
          // No cache exists, fall back to logging out
          clearTokens();
          setState({ currentUser: null, isAuthenticated: false, loading: false });
        }
      }
    }
  };

  // Initial session restoration
  useEffect(() => {
    const access = storage.get<string>(ACCESS_TOKEN_KEY);
    if (access) {
      loadUser(access);
    } else {
      setState((s) => ({ ...s, loading: false }));
    }
  }, []);

  const login = async (username: string, password: string): Promise<{ needsPasswordChange: boolean }> => {
    setState((s) => ({ ...s, loading: true }));
    try {
      const data = await apiLogin({ username, password });
      setTokens(data.access_token, data.refresh_token);
      
      if (data.needs_password_change) {
        setState((s) => ({ ...s, loading: false }));
        return { needsPasswordChange: true };
      }
      
      await loadUser(data.access_token);
      return { needsPasswordChange: false };
    } catch (e) {
      const msg = getErrorMessage(e);
      console.error("Login error:", msg);
      clearTokens();
      storage.remove(USER_CACHE_KEY);
      setState({ currentUser: null, isAuthenticated: false, loading: false });
      throw new Error(msg);
    }
  };

  const completeFirstLogin = async (accessToken: string) => {
    await loadUser(accessToken);
  };

  const logout = async () => {
    const token = storage.get<string>(ACCESS_TOKEN_KEY);
    if (token) {
      await apiLogout(token).catch(() => {}); // ignore errors
    }
    clearTokens();
    storage.remove(USER_CACHE_KEY);
    setState({ currentUser: null, isAuthenticated: false, loading: false });
  };

  const refreshSession = async () => {
    const refresh = storage.get<string>(REFRESH_TOKEN_KEY);
    if (!refresh) return;
    try {
      const newTokens = await refreshAccessToken({ refresh_token: refresh });
      setTokens(newTokens.access_token, newTokens.refresh_token);
      await loadUser(newTokens.access_token);
    } catch (e) {
      console.error("Refresh token error:", e);
      await logout();
    }
  };

  return (
    <AuthContext.Provider
      value={{
        ...state,
        login,
        logout,
        refreshSession,
        completeFirstLogin,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextProps => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};

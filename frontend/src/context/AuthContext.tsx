import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import type { AuthState } from "../types/auth.ts";
import { login as apiLogin, logout as apiLogout, fetchMe as apiFetchMe, refreshAccessToken } from "../services/auth/authService.ts";
import { storage } from "../utils/storage.ts";
import { getErrorMessage } from "../utils/errors.ts";

interface AuthContextProps extends AuthState {
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshSession: () => Promise<void>;
}

const AuthContext = createContext<AuthContextProps | undefined>(undefined);

const ACCESS_TOKEN_KEY = "guardianiq_access_token";
const REFRESH_TOKEN_KEY = "guardianiq_refresh_token";

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
      setState({ currentUser: user, isAuthenticated: true, loading: false });
    } catch (e) {
      console.error("Failed to fetch current user:", e);
      clearTokens();
      setState({ currentUser: null, isAuthenticated: false, loading: false });
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

  const login = async (username: string, password: string) => {
    setState((s) => ({ ...s, loading: true }));
    try {
      const data = await apiLogin({ username, password });
      setTokens(data.access_token, data.refresh_token);
      await loadUser(data.access_token);
    } catch (e) {
      const msg = getErrorMessage(e);
      console.error("Login error:", msg);
      clearTokens();
      setState({ currentUser: null, isAuthenticated: false, loading: false });
      throw new Error(msg);
    }
  };

  const logout = async () => {
    const token = storage.get<string>(ACCESS_TOKEN_KEY);
    if (token) {
      await apiLogout(token).catch(() => {}); // ignore errors
    }
    clearTokens();
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

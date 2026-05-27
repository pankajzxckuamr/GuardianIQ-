import React, { createContext, useState, useEffect, useCallback, ReactNode } from 'react';
import { useNavigate } from 'react-router-dom';
import { authService } from '../services/auth/authService';
import { UserProfile } from '../services/auth/authTypes';

export interface AuthContextType {
  user: UserProfile | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (email: string, password?: string) => Promise<void>;
  logout: () => Promise<void>;
  hasPermission: (permission: string) => boolean;
  hasRole: (role: string) => boolean;
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const loadProfile = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const profile = await authService.getProfile();
      setUser(profile);
      setIsAuthenticated(true);
    } catch (err: any) {
      // Clear session state if initial load fails (e.g., 401 Unauthorized)
      setUser(null);
      setIsAuthenticated(false);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadProfile();
  }, [loadProfile]);

  // Global handler for 401 errors from any API calls
  useEffect(() => {
    const handleUnauthorized = () => {
      setUser(null);
      setIsAuthenticated(false);
      navigate('/login');
    };

    // Standard pattern to listen for generic auth failures triggered by an API interceptor
    window.addEventListener('giq:unauthorized', handleUnauthorized);
    return () => window.removeEventListener('giq:unauthorized', handleUnauthorized);
  }, [navigate]);

  const login = async (email: string, password?: string) => {
    setIsLoading(true);
    setError(null);
    try {
      await authService.login({ email, password });
      const profile = await authService.getProfile();
      setUser(profile);
      setIsAuthenticated(true);
    } catch (err: any) {
      setError(err.message || 'Login failed');
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    setIsLoading(true);
    try {
      await authService.logout();
    } catch (err) {
      // Ignore failures during logout
    } finally {
      setUser(null);
      setIsAuthenticated(false);
      setIsLoading(false);
      navigate('/login');
    }
  };

  const hasPermission = useCallback(
    (permission: string) => {
      if (!user) return false;
      return user.permissions.includes(permission);
    },
    [user]
  );

  const hasRole = useCallback(
    (role: string) => {
      if (!user) return false;
      return user.roles.includes(role);
    },
    [user]
  );

  const value = {
    user,
    isAuthenticated,
    isLoading,
    error,
    login,
    logout,
    hasPermission,
    hasRole,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

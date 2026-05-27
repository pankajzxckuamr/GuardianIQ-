import { useContext, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext, AuthContextType } from '../context/AuthContext';

/**
 * Hook to access the Authentication Context.
 * Throws an error if used outside of the AuthProvider tree.
 */
export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

/**
 * Hook that requires authentication. 
 * Automatically redirects the user to /login if they are not authenticated.
 */
export function useRequireAuth(): AuthContextType {
  const auth = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!auth.isLoading && !auth.isAuthenticated) {
      navigate('/login', { replace: true });
    }
  }, [auth.isLoading, auth.isAuthenticated, navigate]);

  return auth;
}

/**
 * Convenience hook to check if the current user has a specific permission.
 */
export function usePermission(permission: string): boolean {
  const { hasPermission } = useAuth();
  return hasPermission(permission);
}

/**
 * Convenience hook to check if the current user has a specific role.
 */
export function useRole(role: string): boolean {
  const { hasRole } = useAuth();
  return hasRole(role);
}

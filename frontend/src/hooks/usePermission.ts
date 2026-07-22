import { useAuth } from './useAuth';

export function usePermission() {
  const { currentUser } = useAuth();

  const hasPermission = (permission: string): boolean => {
    if (!currentUser) return false;
    if (currentUser.roles.includes('ADMIN') || currentUser.roles.includes('SUPER_ADMIN') || currentUser.roles.includes('GOVERNANCE_ADMIN')) {
      return true;
    }
    return currentUser.permissions.includes(permission);
  };

  const hasRole = (role: string): boolean => {
    if (!currentUser) return false;
    return currentUser.roles.includes(role);
  };

  return {
    hasPermission,
    hasRole,
    roles: currentUser?.roles || [],
    permissions: currentUser?.permissions || [],
  };
}

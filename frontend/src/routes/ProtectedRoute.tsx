import React from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';

export interface ProtectedRouteProps {
  requiredPermission?: string;
  requiredRole?: string;
}

const Loader: React.FC = () => (
  <div className="flex-center" style={{ minHeight: '100vh', width: '100%' }}>
    <div>Loading application securely...</div>
  </div>
);

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ 
  requiredPermission, 
  requiredRole 
}) => {
  const { isAuthenticated, isLoading, hasPermission, hasRole } = useAuth();

  // Show a centered loading state while session is being verified
  if (isLoading) {
    return <Loader />;
  }

  // Redirect unauthenticated users to the login screen
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  // Verify fine-grained permissions if explicitly required for this route
  if (requiredPermission && !hasPermission(requiredPermission)) {
    return <Navigate to="/unauthorized" replace />;
  }

  // Verify specific role if explicitly required for this route
  if (requiredRole && !hasRole(requiredRole)) {
    return <Navigate to="/unauthorized" replace />;
  }

  // User is authenticated and authorized; render the nested child routes
  return <Outlet />;
};

/* src/routes/ProtectedRoute.tsx */
import React, { ReactNode } from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { Loader } from "../components/common/Loader";

interface ProtectedRouteProps {
  children: ReactNode;
  requiredRoles?: string[];
  requiredPermissions?: string[];
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  requiredRoles,
  requiredPermissions,
}) => {
  const { currentUser, isAuthenticated, loading } = useAuth();

  if (loading) {
    return <Loader fullScreen label="Restoring session..." />;
  }

  if (!isAuthenticated || !currentUser) {
    return <Navigate to="/login" replace />;
  }

  const hasRequiredRoles = requiredRoles
    ? requiredRoles.every((role) => currentUser.roles?.includes(role))
    : true;
  const hasRequiredPermissions = requiredPermissions
    ? requiredPermissions.every((perm) => currentUser.permissions?.includes(perm))
    : true;

  if (!hasRequiredRoles || !hasRequiredPermissions) {
    return <Navigate to="/unauthorized" replace />;
  }

  return <>{children}</>;
};

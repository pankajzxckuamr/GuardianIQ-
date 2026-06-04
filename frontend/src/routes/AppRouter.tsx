/* src/routes/AppRouter.tsx */
import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { LoginPage } from "../pages/LoginPage";
import { DashboardPage } from "../pages/DashboardPage";
import { FoundationHealthPage } from "../pages/FoundationHealthPage";
import { AuditPage } from "../pages/AuditPage";
import { TenantsPage } from "../pages/TenantsPage";
import { UnauthorizedPage } from "../pages/UnauthorizedPage";
import { NotFoundPage } from "../pages/NotFoundPage";
import { ProtectedRoute } from "./ProtectedRoute";
import { AppShell } from "../components/layout/AppShell";
import RegistryDashboardPage from "../pages/RegistryDashboardPage";
import { RegistryModelsPage } from "../pages/RegistryModelsPage";
import { RegistryAgentsPage } from "../pages/RegistryAgentsPage";
import { RegistryToolsPage } from "../pages/RegistryToolsPage";
import { RegistryWorkflowsPage } from "../pages/RegistryWorkflowsPage";
import { RegistryDepartmentsPage } from "../pages/RegistryDepartmentsPage";
import { RegistryUsersRolesPage } from "../pages/RegistryUsersRolesPage";
import { RegistryDataSourcesPage } from "../pages/RegistryDataSourcesPage";
import { RegistryRelationshipsPage } from "../pages/RegistryRelationshipsPage";
import { ExecutionDashboardPage } from "../pages/ExecutionDashboardPage";

export const AppRouter: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public auth page */}
        <Route path="/login" element={<LoginPage />} />
        
        {/* Public error pages */}
        <Route path="/unauthorized" element={<UnauthorizedPage />} />
        <Route path="/404" element={<NotFoundPage />} />

        {/* Protected layout routes */}
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <AppShell>
                <DashboardPage />
              </AppShell>
            </ProtectedRoute>
          }
        />
        <Route
          path="/health"
          element={
            <ProtectedRoute>
              <AppShell>
                <FoundationHealthPage />
              </AppShell>
            </ProtectedRoute>
          }
        />
        <Route
          path="/audit"
          element={
            <ProtectedRoute>
              <AppShell>
                <AuditPage />
              </AppShell>
            </ProtectedRoute>
          }
        />
        <Route
          path="/tenants"
          element={
            <ProtectedRoute>
              <AppShell>
                <TenantsPage />
              </AppShell>
            </ProtectedRoute>
          }
        />

        {/* Governance Registry Routes */}
        <Route
          path="/registry"
          element={
            <ProtectedRoute>
              <AppShell>
                <RegistryDashboardPage />
              </AppShell>
            </ProtectedRoute>
          }
        />
        <Route
          path="/registry/models"
          element={
            <ProtectedRoute>
              <AppShell>
                <RegistryModelsPage />
              </AppShell>
            </ProtectedRoute>
          }
        />
        <Route
          path="/registry/agents"
          element={
            <ProtectedRoute>
              <AppShell>
                <RegistryAgentsPage />
              </AppShell>
            </ProtectedRoute>
          }
        />
        <Route
          path="/registry/tools"
          element={
            <ProtectedRoute>
              <AppShell>
                <RegistryToolsPage />
              </AppShell>
            </ProtectedRoute>
          }
        />
        <Route
          path="/registry/workflows"
          element={
            <ProtectedRoute>
              <AppShell>
                <RegistryWorkflowsPage />
              </AppShell>
            </ProtectedRoute>
          }
        />
        <Route
          path="/registry/data-sources"
          element={
            <ProtectedRoute>
              <AppShell>
                <RegistryDataSourcesPage />
              </AppShell>
            </ProtectedRoute>
          }
        />
        <Route
          path="/registry/departments"
          element={
            <ProtectedRoute>
              <AppShell>
                <RegistryDepartmentsPage />
              </AppShell>
            </ProtectedRoute>
          }
        />
        <Route
          path="/registry/users-roles"
          element={
            <ProtectedRoute>
              <AppShell>
                <RegistryUsersRolesPage />
              </AppShell>
            </ProtectedRoute>
          }
        />
        <Route
          path="/registry/relationships"
          element={
            <ProtectedRoute>
              <AppShell>
                <RegistryRelationshipsPage />
              </AppShell>
            </ProtectedRoute>
          }
        />
        <Route
          path="/executions"
          element={
            <ProtectedRoute>
              <AppShell>
                <ExecutionDashboardPage />
              </AppShell>
            </ProtectedRoute>
          }
        />

        {/* Root Redirects */}
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="*" element={<Navigate to="/404" replace />} />
      </Routes>
    </BrowserRouter>
  );
};

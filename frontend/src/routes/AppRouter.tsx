/* src/routes/AppRouter.tsx */
import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { LoginPage } from "../pages/LoginPage";
import { DashboardPage } from "../pages/DashboardPage";
import { FoundationHealthPage } from "../pages/FoundationHealthPage";
import { AuditPage } from "../pages/AuditPage";
import { EventDetailPage } from "../pages/EventDetailPage";
import { SubjectTimelinePage } from "../pages/SubjectTimelinePage";
import { CorrelationTimelinePage } from "../pages/CorrelationTimelinePage";
import { DeadLetterReviewPage } from "../pages/DeadLetterReviewPage";
import { AuditExportPage } from "../pages/AuditExportPage";
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
import { RegisterAllPage } from "../pages/RegisterAllPage";
import { PoliciesDashboardPage } from "../pages/PoliciesDashboardPage";
import { RiskWorkspacePage } from "../pages/RiskWorkspacePage";
import { ApprovalHubPage } from "../pages/ApprovalHubPage";
import { AdminPanelPage } from "../pages/AdminPanelPage";
import { EnforcementSimulationPage } from "../pages/EnforcementSimulationPage";
import { EventSchemaRegistryPage } from "../pages/EventSchemaRegistryPage";
import { EventRetentionRulesPage } from "../pages/EventRetentionRulesPage";

const WorkflowSchedulerDashboard = React.lazy(() => import('../pages/WorkflowSchedulerDashboard'));
const CreateScheduleWizard = React.lazy(() => import('../pages/CreateScheduleWizard'));
const ScheduleDetailPage = React.lazy(() => import('../pages/ScheduleDetailPage'));
const RunHistoryPage = React.lazy(() => import('../pages/RunHistoryPage'));
const RunDetailPage = React.lazy(() => import('../pages/RunDetailPage'));
const AgentAssignmentMatrix = React.lazy(() => import('../pages/AgentAssignmentMatrix'));
const AuthorizationSimulator = React.lazy(() => import('../pages/AuthorizationSimulator'));
const ScheduleApprovalQueue = React.lazy(() => import('../pages/ScheduleApprovalQueue'));
const NotificationsCenter = React.lazy(() => import('../pages/NotificationsCenter'));

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
          path="/audit/events/:eventId"
          element={
            <ProtectedRoute>
              <AppShell>
                <EventDetailPage />
              </AppShell>
            </ProtectedRoute>
          }
        />
        <Route
          path="/audit/timeline/:entityType/:entityId"
          element={
            <ProtectedRoute>
              <AppShell>
                <SubjectTimelinePage />
              </AppShell>
            </ProtectedRoute>
          }
        />
        <Route
          path="/audit/events/correlation/:correlationId"
          element={
            <ProtectedRoute>
              <AppShell>
                <CorrelationTimelinePage />
              </AppShell>
            </ProtectedRoute>
          }
        />
        <Route
          path="/audit/dead-letter"
          element={
            <ProtectedRoute>
              <AppShell>
                <DeadLetterReviewPage />
              </AppShell>
            </ProtectedRoute>
          }
        />
        <Route
          path="/audit/export"
          element={
            <ProtectedRoute>
              <AppShell>
                <AuditExportPage />
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
        <Route
          path="/register-all"
          element={
            <ProtectedRoute>
              <AppShell>
                <RegisterAllPage />
              </AppShell>
            </ProtectedRoute>
          }
        />

        {/* Phase 2 Routes */}
        <Route path="/workflow-scheduler" element={<ProtectedRoute><AppShell><React.Suspense fallback={<div>Loading...</div>}><WorkflowSchedulerDashboard /></React.Suspense></AppShell></ProtectedRoute>} />
        <Route path="/workflow-scheduler/new" element={<ProtectedRoute><AppShell><React.Suspense fallback={<div>Loading...</div>}><CreateScheduleWizard /></React.Suspense></AppShell></ProtectedRoute>} />
        <Route path="/workflow-scheduler/:id/edit" element={<ProtectedRoute><AppShell><React.Suspense fallback={<div>Loading...</div>}><CreateScheduleWizard /></React.Suspense></AppShell></ProtectedRoute>} />
        <Route path="/workflow-scheduler/:id" element={<ProtectedRoute><AppShell><React.Suspense fallback={<div>Loading...</div>}><ScheduleDetailPage /></React.Suspense></AppShell></ProtectedRoute>} />
        <Route path="/workflow-runs" element={<ProtectedRoute><AppShell><React.Suspense fallback={<div>Loading...</div>}><RunHistoryPage /></React.Suspense></AppShell></ProtectedRoute>} />
        <Route path="/workflow-runs/:runId" element={<ProtectedRoute><AppShell><React.Suspense fallback={<div>Loading...</div>}><RunDetailPage /></React.Suspense></AppShell></ProtectedRoute>} />
        <Route path="/agent-assignments" element={<ProtectedRoute><AppShell><React.Suspense fallback={<div>Loading...</div>}><AgentAssignmentMatrix /></React.Suspense></AppShell></ProtectedRoute>} />
        <Route path="/authorization-simulator" element={<ProtectedRoute><AppShell><React.Suspense fallback={<div>Loading...</div>}><AuthorizationSimulator /></React.Suspense></AppShell></ProtectedRoute>} />
        <Route path="/schedule-approvals" element={<ProtectedRoute><AppShell><React.Suspense fallback={<div>Loading...</div>}><ScheduleApprovalQueue /></React.Suspense></AppShell></ProtectedRoute>} />
        <Route path="/workflow-notifications" element={<ProtectedRoute><AppShell><React.Suspense fallback={<div>Loading...</div>}><NotificationsCenter /></React.Suspense></AppShell></ProtectedRoute>} />

        {/* Phase 3 Workspace Routes */}
        <Route path="/policies" element={<ProtectedRoute><AppShell><PoliciesDashboardPage /></AppShell></ProtectedRoute>} />
        <Route path="/enforcement/simulate" element={<ProtectedRoute><AppShell><EnforcementSimulationPage /></AppShell></ProtectedRoute>} />
        <Route path="/risk" element={<ProtectedRoute><AppShell><RiskWorkspacePage /></AppShell></ProtectedRoute>} />
        <Route path="/approvals" element={<ProtectedRoute><AppShell><ApprovalHubPage /></AppShell></ProtectedRoute>} />
        <Route path="/admin" element={<ProtectedRoute><AppShell><AdminPanelPage /></AppShell></ProtectedRoute>} />
        <Route path="/admin/users" element={<ProtectedRoute><AppShell><AdminPanelPage /></AppShell></ProtectedRoute>} />
        <Route path="/admin/roles" element={<ProtectedRoute><AppShell><AdminPanelPage /></AppShell></ProtectedRoute>} />
        <Route path="/admin/settings" element={<ProtectedRoute><AppShell><AdminPanelPage /></AppShell></ProtectedRoute>} />
        <Route path="/admin/event-schemas" element={<ProtectedRoute><AppShell><EventSchemaRegistryPage /></AppShell></ProtectedRoute>} />
        <Route path="/admin/event-retention" element={<ProtectedRoute><AppShell><EventRetentionRulesPage /></AppShell></ProtectedRoute>} />

        {/* Root Redirects */}
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="*" element={<Navigate to="/404" replace />} />
      </Routes>
    </BrowserRouter>
  );
};

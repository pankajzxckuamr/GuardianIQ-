import React, { Suspense } from 'react';
import { createBrowserRouter, RouterProvider, useRouteError, Navigate, Outlet } from 'react-router-dom';
import { ProtectedRoute } from '@/routes/ProtectedRoute';
import { AuthProvider } from '@/context/AuthContext';

// ----------------------------------------------------------------------
// Lazy loaded UI Components (to be implemented later)
// ----------------------------------------------------------------------
const AuthenticatedLayout = React.lazy(() => import('@/components/layout/AuthenticatedLayout'));
const PublicLayout = React.lazy(() => import('@/components/layout/PublicLayout'));

// Lazy loaded Pages
const LoginPage = React.lazy(() => import('@/pages/LoginPage'));
const DashboardPage = React.lazy(() => import('@/pages/DashboardPage'));
const FoundationHealthPage = React.lazy(() => import('@/pages/FoundationHealthPage'));
const ProfilePage = React.lazy(() => import('@/pages/ProfilePage'));
const UnauthorizedPage = React.lazy(() => import('@/pages/UnauthorizedPage'));
const NotFoundPage = React.lazy(() => import('@/pages/NotFoundPage'));

// ----------------------------------------------------------------------
// Boundary Components
// ----------------------------------------------------------------------

const SuspenseFallback: React.FC = () => (
  <div className="flex-center" style={{ minHeight: '100vh' }}>
    <span>Loading module...</span>
  </div>
);

const RouterErrorBoundary: React.FC = () => {
  const error = useRouteError() as any;
  return (
    <div className="flex-center" style={{ minHeight: '100vh', flexDirection: 'column', gap: '1rem' }}>
      <h1 className="page-title" style={{ color: 'var(--color-danger)' }}>Critical Error</h1>
      <p className="page-subtitle">{error?.message || 'The application encountered an unexpected routing error.'}</p>
      <a href="/" style={{ color: 'var(--color-primary)' }}>Return Home</a>
    </div>
  );
};

// Placeholder root loader for future data prefetching integration
const rootLoader = async () => {
  return null;
};

const AuthProviderWrapper: React.FC = () => {
  return (
    <AuthProvider>
      <Outlet />
    </AuthProvider>
  );
};

// ----------------------------------------------------------------------
// Router Definition
// ----------------------------------------------------------------------

const router = createBrowserRouter([
  {
    path: '/',
    element: <AuthProviderWrapper />,
    errorElement: <RouterErrorBoundary />,
    loader: rootLoader,
    children: [
      {
        // Index redirect
        index: true,
        element: <Navigate to="/dashboard" replace />,
      },
      {
        // Public Route Layer
        element: (
          <Suspense fallback={<SuspenseFallback />}>
            <PublicLayout />
          </Suspense>
        ),
        children: [
          {
            path: 'login',
            element: (
              <Suspense fallback={<SuspenseFallback />}>
                <LoginPage />
              </Suspense>
            ),
          },
        ],
      },
      {
        // Authenticated Route Layer
        element: <ProtectedRoute />, // Validates session state before entering
        children: [
          {
            element: (
              <Suspense fallback={<SuspenseFallback />}>
                <AuthenticatedLayout />
              </Suspense>
            ),
            children: [
              {
                path: 'dashboard',
                element: (
                  <Suspense fallback={<SuspenseFallback />}>
                    <DashboardPage />
                  </Suspense>
                ),
              },
              {
                path: 'health',
                element: (
                  <Suspense fallback={<SuspenseFallback />}>
                    <FoundationHealthPage />
                  </Suspense>
                ),
              },
              {
                path: 'profile',
                element: (
                  <Suspense fallback={<SuspenseFallback />}>
                    <ProfilePage />
                  </Suspense>
                ),
              },
              {
                path: 'unauthorized',
                element: (
                  <Suspense fallback={<SuspenseFallback />}>
                    <UnauthorizedPage />
                  </Suspense>
                ),
              },
              {
                path: '*',
                element: (
                  <Suspense fallback={<SuspenseFallback />}>
                    <NotFoundPage />
                  </Suspense>
                ),
              },
            ],
          },
        ],
      },
    ],
  },
]);

export const AppRouter: React.FC = () => {
  return <RouterProvider router={router} />;
};

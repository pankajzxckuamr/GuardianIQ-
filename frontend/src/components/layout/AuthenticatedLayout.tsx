import React from 'react';
import { Outlet, useMatches } from 'react-router-dom';
import { Sidebar } from '@/components/layout/Sidebar';
import { Header } from '@/components/layout/Header';

// -----------------------------------------------------------------------
// Route handle type
// Consumers add a `handle` object to their route definition:
//   handle: { title: "Dashboard", breadcrumbs: [...] }
// -----------------------------------------------------------------------

interface RouteHandle {
  title?: string;
  breadcrumbs?: { label: string; href?: string }[];
}

interface RouteMatch {
  id: string;
  pathname: string;
  handle?: RouteHandle;
}

// -----------------------------------------------------------------------
// AuthenticatedLayout
// -----------------------------------------------------------------------

const AuthenticatedLayout: React.FC = () => {
  const matches = useMatches() as RouteMatch[];

  // Walk matched routes from deepest to shallowest, pick first handle with a title
  const activeMatch = [...matches].reverse().find((m) => m.handle?.title);
  const pageTitle = activeMatch?.handle?.title ?? 'GuardianIQ';
  const breadcrumbs = activeMatch?.handle?.breadcrumbs;

  return (
    <div className="app-layout">
      <Sidebar />

      <Header title={pageTitle} breadcrumbs={breadcrumbs} />

      <main className="app-content" id="main-content" tabIndex={-1}>
        <Outlet />
      </main>
    </div>
  );
};

export default AuthenticatedLayout;

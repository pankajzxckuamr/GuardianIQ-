import React, { useRef, useEffect } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';

// -----------------------------------------------------------------------
// Inline SVG icons (self-contained, no icon library dependency)
// -----------------------------------------------------------------------

const ShieldIcon: React.FC = () => (
  <svg viewBox="0 0 24 24" aria-hidden="true" width="18" height="18" fill="currentColor">
    <path d="M12 1L3 5v6c0 5.25 3.75 10.15 9 11.35C17.25 21.15 21 16.25 21 11V5L12 1zm-1 14l-3-3 1.41-1.41L11 12.17l4.59-4.58L17 9l-6 6z" />
  </svg>
);

const DashboardIcon: React.FC = () => (
  <svg viewBox="0 0 24 24" aria-hidden="true" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="3" width="7" height="7" />
    <rect x="14" y="3" width="7" height="7" />
    <rect x="14" y="14" width="7" height="7" />
    <rect x="3" y="14" width="7" height="7" />
  </svg>
);

const HeartbeatIcon: React.FC = () => (
  <svg viewBox="0 0 24 24" aria-hidden="true" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
  </svg>
);

const UserCircleIcon: React.FC = () => (
  <svg viewBox="0 0 24 24" aria-hidden="true" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
    <circle cx="12" cy="7" r="4" />
  </svg>
);

const SettingsIcon: React.FC = () => (
  <svg viewBox="0 0 24 24" aria-hidden="true" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="3" />
    <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
  </svg>
);

const LogoutIcon: React.FC = () => (
  <svg viewBox="0 0 24 24" aria-hidden="true" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
    <polyline points="16 17 21 12 16 7" />
    <line x1="21" y1="12" x2="9" y2="12" />
  </svg>
);

// -----------------------------------------------------------------------
// Helpers
// -----------------------------------------------------------------------

function getInitials(name: string): string {
  return name
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((n) => n[0].toUpperCase())
    .join('');
}

// -----------------------------------------------------------------------
// Sidebar Component
// -----------------------------------------------------------------------

export const Sidebar: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/login', { replace: true });
  };

  const initials = user && user.name ? getInitials(user.name) : '??';
  const primaryRole = user?.roles[0] ?? 'User';

  return (
    <aside className="app-sidebar" role="navigation" aria-label="Main navigation">
      {/* Logo */}
      <NavLink to="/dashboard" className="sidebar-logo" aria-label="GuardianIQ — go to dashboard">
        <div className="sidebar-logo__mark" aria-hidden="true">
          <ShieldIcon />
        </div>
        <span className="sidebar-logo__wordmark">
          Guardian<span>IQ</span>
        </span>
      </NavLink>

      {/* Navigation links */}
      <nav className="sidebar-nav" aria-label="Application pages">
        <NavLink
          to="/dashboard"
          className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}
          aria-current={undefined}
        >
          <span className="nav-link-icon"><DashboardIcon /></span>
          <span className="nav-link-label">Dashboard</span>
        </NavLink>

        <NavLink
          to="/health"
          className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}
        >
          <span className="nav-link-icon"><HeartbeatIcon /></span>
          <span className="nav-link-label">Health</span>
        </NavLink>

        <NavLink
          to="/profile"
          className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}
        >
          <span className="nav-link-icon"><UserCircleIcon /></span>
          <span className="nav-link-label">Profile</span>
        </NavLink>

        <div className="nav-separator" role="separator" />

        {/* Settings — disabled placeholder for future phases */}
        <span
          className="nav-link nav-link--disabled"
          aria-disabled="true"
          title="Settings — coming soon"
        >
          <span className="nav-link-icon"><SettingsIcon /></span>
          <span className="nav-link-label">Settings</span>
        </span>
      </nav>

      {/* User section at the bottom */}
      <div className="sidebar-user">
        <div className="sidebar-user__card">
          <div className="sidebar-user__avatar" aria-hidden="true">
            {initials}
          </div>
          <div className="sidebar-user__info">
            <div className="sidebar-user__name" title={user?.name}>
              {user?.name ?? 'Unknown User'}
            </div>
            <div className="sidebar-user__role">{primaryRole}</div>
          </div>
          <button
            className="sidebar-logout-btn"
            onClick={handleLogout}
            aria-label="Sign out"
            title="Sign out"
            type="button"
          >
            <LogoutIcon />
          </button>
        </div>
      </div>
    </aside>
  );
};

import React, { useState, useRef, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';

export interface HeaderBreadcrumb {
  label: string;
  href?: string;
}

export interface HeaderProps {
  title: string;
  breadcrumbs?: HeaderBreadcrumb[];
}

// -----------------------------------------------------------------------
// Inline SVG icons
// -----------------------------------------------------------------------

const BellIcon: React.FC = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
    <path d="M13.73 21a2 2 0 0 1-3.46 0" />
  </svg>
);

const ChevronDownIcon: React.FC = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <polyline points="6 9 12 15 18 9" />
  </svg>
);

const UserIcon: React.FC = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
    <circle cx="12" cy="7" r="4" />
  </svg>
);

const LogoutIcon: React.FC = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
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
// UserMenu subcomponent
// -----------------------------------------------------------------------

const UserMenu: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [isOpen, setIsOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  // Close dropdown on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    if (isOpen) document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [isOpen]);

  // Close on Escape
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setIsOpen(false);
    };
    if (isOpen) document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }, [isOpen]);

  const handleLogout = async () => {
    setIsOpen(false);
    await logout();
    navigate('/login', { replace: true });
  };

  const initials = user && user.name ? getInitials(user.name) : '??';

  return (
    <div className="user-menu" ref={menuRef}>
      <button
        type="button"
        className="user-menu__trigger"
        onClick={() => setIsOpen((prev) => !prev)}
        aria-haspopup="menu"
        aria-expanded={isOpen}
        aria-label="Open user menu"
      >
        <div className="user-menu__avatar" aria-hidden="true">{initials}</div>
        <span className="user-menu__name">{user?.name ?? 'User'}</span>
        <span className={`user-menu__chevron${isOpen ? ' user-menu__chevron--open' : ''}`}>
          <ChevronDownIcon />
        </span>
      </button>

      {isOpen && (
        <div
          className="user-menu__dropdown"
          role="menu"
          aria-label="User account menu"
        >
          {/* Identity header */}
          <div className="user-menu__dropdown-header">
            <div className="user-menu__dropdown-name">{user?.name}</div>
            <div className="user-menu__dropdown-email">{user?.email}</div>
          </div>

          {/* Menu items */}
          <Link
            to="/profile"
            className="user-menu__item"
            role="menuitem"
            onClick={() => setIsOpen(false)}
          >
            <UserIcon />
            Profile
          </Link>

          <div className="user-menu__separator" role="separator" />

          <button
            type="button"
            className="user-menu__item user-menu__item--danger"
            role="menuitem"
            onClick={handleLogout}
          >
            <LogoutIcon />
            Sign out
          </button>
        </div>
      )}
    </div>
  );
};

// -----------------------------------------------------------------------
// Header Component
// -----------------------------------------------------------------------

export const Header: React.FC<HeaderProps> = ({ title, breadcrumbs }) => {
  const hasBreadcrumbs = breadcrumbs && breadcrumbs.length > 0;

  return (
    <header className="app-header" role="banner">
      {/* Left: title + breadcrumbs */}
      <div className="header-title-area">
        {hasBreadcrumbs && (
          <ol className="header-breadcrumbs" aria-label="Breadcrumb">
            {breadcrumbs!.map((crumb, idx) => {
              const isLast = idx === breadcrumbs!.length - 1;
              return (
                <li key={idx} className="header-breadcrumb-item">
                  {!isLast && crumb.href ? (
                    <a href={crumb.href}>{crumb.label}</a>
                  ) : (
                    <span
                      className="header-breadcrumb-item__current"
                      aria-current={isLast ? 'page' : undefined}
                    >
                      {crumb.label}
                    </span>
                  )}
                  {!isLast && (
                    <span className="header-breadcrumb-item__sep" aria-hidden="true">›</span>
                  )}
                </li>
              );
            })}
          </ol>
        )}
        <h1 className="header-title">{title}</h1>
      </div>

      {/* Right: actions */}
      <div className="header-actions">
        <button
          type="button"
          className="header-icon-btn"
          aria-label="Notifications"
          title="Notifications"
        >
          <BellIcon />
        </button>

        <UserMenu />
      </div>
    </header>
  );
};

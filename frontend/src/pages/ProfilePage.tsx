import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import { authService } from '@/services/auth/authService';
import { UserProfile } from '@/services/auth/authTypes';
import { Badge } from '@/components/common/Badge';
import { PageHeader } from '@/components/common/PageHeader';
import '@/styles/pages/profile.css';

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

function truncateId(id: string, length = 24): string {
  return id.length > length ? `${id.slice(0, length)}…` : id;
}

function getDeviceId(): string {
  return localStorage.getItem('giq_device_id') ?? 'Unknown device';
}

// -----------------------------------------------------------------------
// Subcomponents
// -----------------------------------------------------------------------

const SkeletonBars: React.FC = () => (
  <div className="profile-skeleton">
    {[70, 50, 85, 40].map((w, i) => (
      <div key={i} className="profile-skeleton-bar" style={{ width: `${w}%` }} />
    ))}
  </div>
);

// -----------------------------------------------------------------------
// ProfilePage
// -----------------------------------------------------------------------

const ProfilePage: React.FC = () => {
  const { user: contextUser, logout } = useAuth();
  const navigate = useNavigate();

  const [profile, setProfile] = useState<UserProfile | null>(contextUser);
  const [isLoading, setIsLoading] = useState(!contextUser);
  const [fetchError, setFetchError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  // Always re-fetch from /api/auth/me on mount for fresh data
  const loadProfile = useCallback(async () => {
    setIsLoading(true);
    setFetchError(null);
    try {
      const fresh = await authService.getProfile();
      setProfile(fresh);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to load profile';
      setFetchError(msg);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadProfile();
  }, [loadProfile]);

  const handleCopyUserId = async () => {
    if (!profile) return;
    try {
      await navigator.clipboard.writeText(profile.id);
      showToast('User ID copied to clipboard', 'success');
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback: silently ignore clipboard failures
    }
  };

  const handleLogout = async () => {
    await logout();
    navigate('/login', { replace: true });
  };

  const initials = profile && profile.name ? getInitials(profile.name) : '??';
  const deviceId = getDeviceId();

  return (
    <main className="profile-page">
      <PageHeader
        title="Profile"
        subtitle="Your identity, roles and session details"
        breadcrumbs={[{ label: 'Dashboard', href: '/dashboard' }, { label: 'Profile' }]}
      />

      {fetchError && (
        <div
          role="alert"
          style={{
            padding: 'var(--space-3) var(--space-4)',
            background: 'rgba(226,75,74,0.08)',
            border: '1px solid rgba(226,75,74,0.25)',
            borderRadius: 'var(--border-radius-md)',
            color: 'var(--color-danger)',
            fontSize: '0.875rem',
            marginTop: 'var(--space-4)',
          }}
        >
          {fetchError} —{' '}
          <button
            type="button"
            onClick={() => void loadProfile()}
            style={{ color: 'inherit', textDecoration: 'underline', background: 'none', border: 'none', cursor: 'pointer' }}
          >
            Retry
          </button>
        </div>
      )}

      <div className="profile-grid">
        {/* ---- Left: Identity card ---- */}
        <div className="profile-identity-card">
          <div className="profile-identity-card__banner" aria-hidden="true" />
          <div className="profile-identity-card__body">
            <div className="profile-avatar" aria-hidden="true">{initials}</div>

            {isLoading ? (
              <SkeletonBars />
            ) : profile ? (
              <>
                <div className="profile-name">{profile.name}</div>
                <div className="profile-email">{profile.email}</div>

                <div className="profile-divider" />

                {/* User ID row */}
                <div className="profile-meta-row">
                  <span className="profile-meta-label">User ID</span>
                  <span className="profile-meta-value" title={profile.id}>
                    {truncateId(profile.id)}
                  </span>
                </div>
                <button
                  type="button"
                  className={`profile-copy-btn${copied ? ' profile-copy-btn--copied' : ''}`}
                  onClick={() => void handleCopyUserId()}
                  aria-label={copied ? 'User ID copied' : 'Copy user ID to clipboard'}
                >
                  {copied ? '✓ Copied!' : '⎘ Copy ID'}
                </button>

                <div className="profile-divider" />

                {/* Active session indicator */}
                <div
                  className="profile-session"
                  role="status"
                  aria-label="Active session"
                >
                  <span className="profile-session__dot" aria-hidden="true" />
                  <div>
                    <div className="profile-session__text">Active session</div>
                    <div className="profile-session__device" title={deviceId}>
                      {truncateId(deviceId, 20)}
                    </div>
                  </div>
                </div>

                {/* Logout */}
                <button
                  type="button"
                  className="profile-logout-btn"
                  onClick={() => void handleLogout()}
                >
                  Sign out of this account
                </button>
              </>
            ) : null}
          </div>
        </div>

        {/* ---- Right: Roles + Permissions ---- */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>

          {/* Roles */}
          <div className="profile-detail-card">
            <div className="profile-section-header">Assigned Roles</div>
            <div className="profile-section-body">
              {isLoading ? (
                <SkeletonBars />
              ) : profile && profile.roles.length > 0 ? (
                <div className="profile-badges-list" role="list" aria-label="Roles">
                  {profile.roles.map((role) => (
                    <span key={role} role="listitem">
                      <Badge variant="info">{role.replace(/_/g, ' ')}</Badge>
                    </span>
                  ))}
                </div>
              ) : (
                <span style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>
                  No roles assigned.
                </span>
              )}
            </div>
          </div>

          {/* Permissions */}
          <div className="profile-detail-card">
            <div className="profile-section-header">
              Granted Permissions
              {profile && (
                <span
                  style={{
                    marginLeft: 'var(--space-2)',
                    fontSize: '0.75rem',
                    color: 'var(--text-muted)',
                    fontWeight: 400,
                  }}
                >
                  ({profile.permissions.length})
                </span>
              )}
            </div>
            <div className="profile-section-body">
              {isLoading ? (
                <SkeletonBars />
              ) : profile && profile.permissions.length > 0 ? (
                <div className="profile-permissions-list" role="list" aria-label="Permissions">
                  {profile.permissions.map((perm) => (
                    <span key={perm} role="listitem">
                      <Badge variant="neutral" size="sm">
                        {perm.replace(/_/g, ' ').toLowerCase()}
                      </Badge>
                    </span>
                  ))}
                </div>
              ) : (
                <span style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>
                  No explicit permissions granted.
                </span>
              )}
            </div>
          </div>
        </div>
      </div>
    </main>
  );
};

export default ProfilePage;

import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import { Badge } from '@/components/common/Badge';

// -----------------------------------------------------------------------
// UnauthorizedPage
// -----------------------------------------------------------------------

const UnauthorizedPage: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  return (
    <main
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100%',
        padding: 'var(--space-8)',
      }}
    >
      <div
        className="card"
        style={{ maxWidth: 480, width: '100%', textAlign: 'center' }}
        role="main"
        aria-labelledby="unauth-heading"
      >
        {/* Icon */}
        <div
          aria-hidden="true"
          style={{
            width: 64,
            height: 64,
            borderRadius: 'var(--border-radius-lg)',
            background: 'rgba(226,75,74,0.08)',
            border: '1px solid rgba(226,75,74,0.2)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto var(--space-5)',
            fontSize: '1.75rem',
          }}
        >
          🔒
        </div>

        <h1
          id="unauth-heading"
          style={{
            fontSize: '1.375rem',
            fontWeight: 700,
            color: 'var(--text-primary)',
            marginBottom: 'var(--space-2)',
          }}
        >
          Access Restricted
        </h1>

        <p
          style={{
            fontSize: '0.9375rem',
            color: 'var(--text-muted)',
            lineHeight: 1.6,
            marginBottom: 'var(--space-5)',
          }}
        >
          You do not have permission to view this page.
          <br />
          Contact your administrator if you believe this is an error.
        </p>

        {/* Current roles display */}
        {user && user.roles.length > 0 && (
          <div
            style={{
              padding: 'var(--space-3) var(--space-4)',
              background: 'var(--bg-secondary)',
              borderRadius: 'var(--border-radius-md)',
              marginBottom: 'var(--space-5)',
            }}
          >
            <p
              style={{
                fontSize: '0.75rem',
                fontWeight: 600,
                textTransform: 'uppercase',
                letterSpacing: '0.06em',
                color: 'var(--text-muted)',
                marginBottom: 'var(--space-2)',
              }}
            >
              Your current roles
            </p>
            <div
              style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--space-2)', justifyContent: 'center' }}
              role="list"
              aria-label="Current roles"
            >
              {user.roles.map((role) => (
                <span key={role} role="listitem">
                  <Badge variant="neutral">{role.replace(/_/g, ' ')}</Badge>
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Actions */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
          <button
            type="button"
            className="btn btn--primary btn--md"
            onClick={() => navigate('/dashboard')}
          >
            ← Back to Dashboard
          </button>

          <a
            href="mailto:admin@guardianiq.internal?subject=Access%20Request"
            className="btn btn--ghost btn--md"
            style={{ textDecoration: 'none' }}
          >
            Contact Administrator
          </a>
        </div>
      </div>
    </main>
  );
};

export default UnauthorizedPage;

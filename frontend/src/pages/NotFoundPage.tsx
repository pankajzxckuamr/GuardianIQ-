import React from 'react';
import { useNavigate } from 'react-router-dom';

// -----------------------------------------------------------------------
// NotFoundPage — pure CSS/text "404" illustration, no external images
// -----------------------------------------------------------------------

const NotFoundPage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <main
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100%',
        padding: 'var(--space-8)',
        flexDirection: 'column',
        textAlign: 'center',
        gap: 'var(--space-6)',
      }}
      aria-labelledby="not-found-heading"
    >
      {/* CSS-only 404 illustration */}
      <div
        aria-hidden="true"
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 'var(--space-3)',
          userSelect: 'none',
        }}
      >
        {/* "4" left */}
        <span
          style={{
            fontSize: 'clamp(5rem, 14vw, 9rem)',
            fontWeight: 800,
            lineHeight: 1,
            color: 'var(--color-primary)',
            opacity: 0.15,
            fontFamily: 'var(--font-sans)',
            letterSpacing: '-0.04em',
          }}
        >
          4
        </span>

        {/* Central circle with icon */}
        <div
          style={{
            width: 'clamp(80px, 14vw, 130px)',
            height: 'clamp(80px, 14vw, 130px)',
            borderRadius: '50%',
            border: '3px solid var(--border-color)',
            background: 'var(--bg-secondary)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexShrink: 0,
            boxShadow: 'var(--shadow-md)',
          }}
        >
          <svg
            width="40%"
            height="40%"
            viewBox="0 0 24 24"
            fill="none"
            stroke="var(--text-muted)"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <circle cx="11" cy="11" r="8" />
            <line x1="21" y1="21" x2="16.65" y2="16.65" />
            <line x1="11" y1="8" x2="11" y2="14" />
            <circle cx="11" cy="16.5" r="0.5" fill="var(--text-muted)" stroke="none" />
          </svg>
        </div>

        {/* "4" right */}
        <span
          style={{
            fontSize: 'clamp(5rem, 14vw, 9rem)',
            fontWeight: 800,
            lineHeight: 1,
            color: 'var(--color-primary)',
            opacity: 0.15,
            fontFamily: 'var(--font-sans)',
            letterSpacing: '-0.04em',
          }}
        >
          4
        </span>
      </div>

      {/* Text content */}
      <div style={{ maxWidth: 420 }}>
        <h1
          id="not-found-heading"
          style={{
            fontSize: '1.5rem',
            fontWeight: 700,
            color: 'var(--text-primary)',
            marginBottom: 'var(--space-3)',
            letterSpacing: '-0.01em',
          }}
        >
          Page Not Found
        </h1>
        <p
          style={{
            fontSize: '0.9375rem',
            color: 'var(--text-muted)',
            lineHeight: 1.7,
            marginBottom: 'var(--space-6)',
          }}
        >
          The page you are looking for does not exist or has been moved.
          <br />
          Check the URL or navigate back to a known page.
        </p>

        <div style={{ display: 'flex', gap: 'var(--space-3)', justifyContent: 'center', flexWrap: 'wrap' }}>
          <button
            type="button"
            className="btn btn--primary btn--md"
            onClick={() => navigate('/dashboard')}
          >
            ← Back to Dashboard
          </button>
          <button
            type="button"
            className="btn btn--ghost btn--md"
            onClick={() => navigate(-1)}
          >
            Go Back
          </button>
        </div>
      </div>

      {/* Subtle path info */}
      <p
        style={{
          fontSize: '0.8125rem',
          color: 'var(--text-muted)',
          opacity: 0.6,
          fontFamily: 'var(--font-mono)',
        }}
        aria-live="polite"
      >
        {window.location.pathname}
      </p>
    </main>
  );
};

export default NotFoundPage;

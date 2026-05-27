import React, { useState, useEffect, useId } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import '@/styles/pages/login.css';

// -----------------------------------------------------------------------
// SVG icons (inline to avoid asset dependencies in Phase 0)
// -----------------------------------------------------------------------

const ShieldIcon: React.FC = () => (
  <svg viewBox="0 0 24 24" aria-hidden="true">
    <path d="M12 1L3 5v6c0 5.25 3.75 10.15 9 11.35C17.25 21.15 21 16.25 21 11V5L12 1zm-1 14l-3-3 1.41-1.41L11 12.17l4.59-4.58L17 9l-6 6z" />
  </svg>
);

const EyeIcon: React.FC = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
    <circle cx="12" cy="12" r="3" />
  </svg>
);

const EyeOffIcon: React.FC = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94" />
    <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19" />
    <line x1="1" y1="1" x2="23" y2="23" />
  </svg>
);

const AlertIcon: React.FC = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <circle cx="12" cy="12" r="10" />
    <line x1="12" y1="8" x2="12" y2="12" />
    <line x1="12" y1="16" x2="12.01" y2="16" />
  </svg>
);

// -----------------------------------------------------------------------
// LoginPage
// -----------------------------------------------------------------------

const LoginPage: React.FC = () => {
  const { login, isAuthenticated, isLoading: authLoading } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Stable IDs for aria associations
  const emailId = useId();
  const passwordId = useId();
  const errorId = useId();

  // Redirect immediately if already authenticated
  useEffect(() => {
    if (!authLoading && isAuthenticated) {
      navigate('/dashboard', { replace: true });
    }
  }, [isAuthenticated, authLoading, navigate]);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (isSubmitting) return;

    setErrorMessage(null);
    setIsSubmitting(true);

    try {
      await login(email, password);
      navigate('/dashboard', { replace: true });
    } catch (err: unknown) {
      const message =
        err instanceof Error
          ? err.message
          : typeof err === 'object' && err !== null && 'message' in err
          ? String((err as { message: unknown }).message)
          : 'Invalid email or password. Please try again.';
      setErrorMessage(message);
    } finally {
      setIsSubmitting(false);
    }
  };

  const hasError = errorMessage !== null;

  return (
    <main className="login-page" aria-labelledby="login-heading">
      <div className="login-card" role="region" aria-label="Sign in form">

        {/* Logo / Wordmark */}
        <div className="login-logo" aria-hidden="true">
          <div className="login-logo__mark">
            <ShieldIcon />
          </div>
          <span className="login-logo__wordmark">
            Guardian<span>IQ</span>
          </span>
        </div>

        {/* Heading */}
        <h1 id="login-heading" className="login-title">Sign in to your account</h1>
        <p className="login-subtitle">AI Governance Platform</p>

        {/* Banner error */}
        {hasError && (
          <div
            id={errorId}
            className="login-error-banner"
            role="alert"
            aria-live="assertive"
          >
            <AlertIcon />
            <span>{errorMessage}</span>
          </div>
        )}

        {/* Form */}
        <form
          className="login-form"
          onSubmit={handleSubmit}
          noValidate
          aria-describedby={hasError ? errorId : undefined}
        >
          {/* Email field */}
          <div className="login-field">
            <label htmlFor={emailId} className="login-label">
              Email address
            </label>
            <div className="login-input-wrapper">
              <input
                id={emailId}
                type="email"
                className={`login-input${hasError ? ' error' : ''}`}
                value={email}
                onChange={(e) => {
                  setEmail(e.target.value);
                  if (errorMessage) setErrorMessage(null);
                }}
                placeholder="you@organization.com"
                autoComplete="email"
                autoFocus
                required
                aria-required="true"
                aria-invalid={hasError}
                aria-describedby={hasError ? errorId : undefined}
                disabled={isSubmitting}
              />
            </div>
          </div>

          {/* Password field */}
          <div className="login-field">
            <label htmlFor={passwordId} className="login-label">
              Password
            </label>
            <div className="login-input-wrapper">
              <input
                id={passwordId}
                type={showPassword ? 'text' : 'password'}
                className={`login-input login-input--password${hasError ? ' error' : ''}`}
                value={password}
                onChange={(e) => {
                  setPassword(e.target.value);
                  if (errorMessage) setErrorMessage(null);
                }}
                placeholder="Enter your password"
                autoComplete="current-password"
                required
                aria-required="true"
                aria-invalid={hasError}
                disabled={isSubmitting}
              />
              <button
                type="button"
                className="login-pw-toggle"
                onClick={() => setShowPassword((prev) => !prev)}
                aria-label={showPassword ? 'Hide password' : 'Show password'}
                tabIndex={0}
              >
                {showPassword ? <EyeOffIcon /> : <EyeIcon />}
              </button>
            </div>
          </div>

          {/* Submit */}
          <button
            type="submit"
            className={`login-submit-btn${isSubmitting ? ' loading' : ''}`}
            disabled={isSubmitting || !email.trim() || !password}
            aria-busy={isSubmitting}
          >
            {isSubmitting ? (
              <>
                <span className="login-btn-spinner" aria-hidden="true" />
                <span>Signing in…</span>
              </>
            ) : (
              'Sign in'
            )}
          </button>
        </form>

        <p className="login-footer-note">
          GuardianIQ &mdash; Phase 0 &middot; Internal use only
        </p>
      </div>
    </main>
  );
};

export default LoginPage;

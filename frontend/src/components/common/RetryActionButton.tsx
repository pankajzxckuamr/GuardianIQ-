/* src/components/common/RetryActionButton.tsx */
import React, { useState } from "react";
import styles from "./RetryActionButton.module.css";

export interface RetryActionButtonProps {
  onRetry: () => Promise<void>;
  disabled?: boolean;
  label?: string;
  loadingLabel?: string;
  className?: string;
}

export const RetryActionButton: React.FC<RetryActionButtonProps> = ({
  onRetry,
  disabled = false,
  label = "Retry Dispatch",
  loadingLabel = "Retrying...",
  className = ""
}) => {
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleClick = async () => {
    if (loading || disabled) return;

    setLoading(true);
    setErrorMessage(null);

    try {
      await onRetry();
    } catch (err: any) {
      const msg = err?.detail || err?.message || "Failed to re-queue dead letter item";
      setErrorMessage(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: "inline-flex", flexDirection: "column", alignItems: "flex-start" }}>
      <button
        type="button"
        className={`${styles.retryButton} ${className}`}
        onClick={handleClick}
        disabled={disabled || loading}
        title={disabled ? "Retry unavailable" : "Re-queue item for consumer processing"}
      >
        {loading ? (
          <>
            <span className={styles.spinner} />
            <span>{loadingLabel}</span>
          </>
        ) : (
          <>
            <svg
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67" />
            </svg>
            <span>{label}</span>
          </>
        )}
      </button>

      {errorMessage && (
        <span className={styles.errorMessage} role="alert">
          {errorMessage}
        </span>
      )}
    </div>
  );
};

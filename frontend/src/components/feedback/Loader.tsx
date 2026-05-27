import React from 'react';
import ReactDOM from 'react-dom';

export interface LoaderProps {
  size?: 'sm' | 'md' | 'lg' | 'fullscreen';
  label?: string;
}

export const Loader: React.FC<LoaderProps> = ({ size = 'md', label = 'Loading…' }) => {
  const spinner = (
    <div
      className={`loader loader--${size}`}
      role="status"
      aria-live="polite"
    >
      <span className="loader__spinner" aria-hidden="true" />
      <span className="sr-only">{label}</span>
    </div>
  );

  if (size === 'fullscreen') {
    return ReactDOM.createPortal(
      <div className="loader-overlay">{spinner}</div>,
      document.body
    );
  }

  return spinner;
};

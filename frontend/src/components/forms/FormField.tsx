import React, { ReactNode } from 'react';

export interface FormFieldProps {
  label: string;
  error?: string;
  hint?: string;
  htmlFor?: string;
  children: ReactNode;
}

export const FormField: React.FC<FormFieldProps> = ({
  label,
  error,
  hint,
  htmlFor,
  children
}) => {
  return (
    <div className="giq-form-field">
      <label htmlFor={htmlFor} className="giq-form-label">
        {label}
      </label>
      <div className="giq-form-control">
        {children}
      </div>
      {error && <div className="giq-form-error">{error}</div>}
      {hint && !error && <div className="giq-form-hint">{hint}</div>}
    </div>
  );
};

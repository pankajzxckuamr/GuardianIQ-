/* src/components/common/FormField.tsx */
import React from "react";
import "./FormField.css";

interface FormFieldProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label: string;
  error?: string;
  helperText?: string;
}

export const FormField: React.FC<FormFieldProps> = ({
  label,
  error,
  helperText,
  className = "",
  id,
  ...rest
}) => {
  const fieldId = id || `field-${label.toLowerCase().replace(/\s+/g, "-")}`;
  return (
    <div className={`form-field ${error ? "form-field--error" : ""} ${className}`}>
      <label htmlFor={fieldId} className="form-field-label">
        {label}
      </label>
      <input
        id={fieldId}
        className="form-field-input"
        {...rest}
      />
      {error && <span className="form-field-error-msg">{error}</span>}
      {!error && helperText && <span className="form-field-helper-msg">{helperText}</span>}
    </div>
  );
};

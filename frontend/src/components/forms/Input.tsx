import React, { InputHTMLAttributes, forwardRef } from 'react';

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  hasError?: boolean;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, hasError, ...props }, ref) => {
    const inputClass = `giq-input ${hasError ? 'giq-input-error' : ''} ${className || ''}`.trim();
    return (
      <input
        ref={ref}
        className={inputClass}
        {...props}
      />
    );
  }
);

Input.displayName = 'Input';

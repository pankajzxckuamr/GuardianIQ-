import React, { forwardRef } from 'react';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
  icon?: React.ReactNode;
  children?: React.ReactNode;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = 'primary',
      size = 'md',
      isLoading = false,
      disabled = false,
      icon,
      children,
      className,
      type = 'button',
      ...rest
    },
    ref
  ) => {
    const classes = [
      'btn',
      `btn--${variant}`,
      `btn--${size}`,
      isLoading ? 'btn--loading' : '',
      className ?? '',
    ]
      .filter(Boolean)
      .join(' ');

    return (
      <button
        ref={ref}
        type={type}
        className={classes}
        disabled={disabled || isLoading}
        aria-busy={isLoading}
        aria-disabled={disabled || isLoading}
        {...rest}
      >
        {isLoading ? (
          <span className="btn__spinner" aria-hidden="true" />
        ) : (
          icon && <span className="btn__icon" aria-hidden="true">{icon}</span>
        )}
        {children && <span className="btn__label">{children}</span>}
      </button>
    );
  }
);

Button.displayName = 'Button';

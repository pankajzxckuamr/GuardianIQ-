import React from 'react';

export interface BadgeProps {
  variant: 'success' | 'warning' | 'danger' | 'info' | 'neutral';
  size?: 'sm' | 'md';
  children: React.ReactNode;
}

export const Badge: React.FC<BadgeProps> = ({ variant, size = 'md', children }) => {
  const classes = ['badge', `badge-${variant}`, size === 'sm' ? 'badge--sm' : '']
    .filter(Boolean)
    .join(' ');

  return <span className={classes}>{children}</span>;
};

import React from 'react';

// -----------------------------------------------------------------------
// Subcomponents
// -----------------------------------------------------------------------

interface CardHeaderProps {
  title: React.ReactNode;
  actions?: React.ReactNode;
  className?: string;
}

const CardHeader: React.FC<CardHeaderProps> = ({ title, actions, className }) => (
  <div className={['card__header', className].filter(Boolean).join(' ')}>
    <div className="card__header-title">{title}</div>
    {actions && <div className="card__header-actions">{actions}</div>}
  </div>
);

interface CardBodyProps {
  children: React.ReactNode;
  className?: string;
  /** Remove default padding (e.g. when rendering a full-bleed table) */
  noPadding?: boolean;
}

const CardBody: React.FC<CardBodyProps> = ({ children, className, noPadding }) => (
  <div
    className={['card__body', noPadding ? 'card__body--no-padding' : '', className]
      .filter(Boolean)
      .join(' ')}
  >
    {children}
  </div>
);

interface CardFooterProps {
  children: React.ReactNode;
  className?: string;
}

const CardFooter: React.FC<CardFooterProps> = ({ children, className }) => (
  <div className={['card__footer', className].filter(Boolean).join(' ')}>{children}</div>
);

// -----------------------------------------------------------------------
// Root Card component with attached subcomponents
// -----------------------------------------------------------------------

interface CardProps {
  children: React.ReactNode;
  className?: string;
}

type CardComponent = React.FC<CardProps> & {
  Header: typeof CardHeader;
  Body: typeof CardBody;
  Footer: typeof CardFooter;
};

const Card: CardComponent = ({ children, className }) => (
  <div className={['card', className].filter(Boolean).join(' ')}>{children}</div>
);

Card.Header = CardHeader;
Card.Body = CardBody;
Card.Footer = CardFooter;

export { Card };
export type { CardProps, CardHeaderProps, CardBodyProps, CardFooterProps };

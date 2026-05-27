import React from 'react';

export interface BreadcrumbItem {
  label: string;
  href?: string;
}

export interface PageHeaderProps {
  title: string;
  subtitle?: string;
  breadcrumbs?: BreadcrumbItem[];
  actions?: React.ReactNode;
}

export const PageHeader: React.FC<PageHeaderProps> = ({
  title,
  subtitle,
  breadcrumbs,
  actions,
}) => {
  return (
    <div className="page-header">
      {breadcrumbs && breadcrumbs.length > 0 && (
        <nav className="page-header__breadcrumbs" aria-label="Breadcrumb">
          <ol className="breadcrumb-list">
            {breadcrumbs.map((crumb, idx) => {
              const isLast = idx === breadcrumbs.length - 1;
              return (
                <li key={idx} className="breadcrumb-item">
                  {!isLast && crumb.href ? (
                    <a href={crumb.href} className="breadcrumb-item__link">
                      {crumb.label}
                    </a>
                  ) : (
                    <span
                      className="breadcrumb-item__current"
                      aria-current={isLast ? 'page' : undefined}
                    >
                      {crumb.label}
                    </span>
                  )}
                  {!isLast && (
                    <span className="breadcrumb-item__separator" aria-hidden="true">
                      /
                    </span>
                  )}
                </li>
              );
            })}
          </ol>
        </nav>
      )}

      <div className="page-header__row">
        <div className="page-header__text">
          <h1 className="page-title">{title}</h1>
          {subtitle && <p className="page-subtitle">{subtitle}</p>}
        </div>
        {actions && <div className="page-header__actions">{actions}</div>}
      </div>
    </div>
  );
};

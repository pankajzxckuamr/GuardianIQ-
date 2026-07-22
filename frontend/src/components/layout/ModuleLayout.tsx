import React from 'react';

interface ModuleLayoutProps {
  title: string;
  description?: string;
  actions?: React.ReactNode;
  filters?: React.ReactNode;
  children: React.ReactNode;
}

export const ModuleLayout: React.FC<ModuleLayoutProps> = ({
  title,
  description,
  actions,
  filters,
  children,
}) => {
  return (
    <div className="flex flex-col h-full space-y-6 p-6">
      {/* Header section */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between space-y-4 md:space-y-0">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900 dark:text-white">
            {title}
          </h1>
          {description && (
            <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
              {description}
            </p>
          )}
        </div>
        {actions && <div className="flex items-center space-x-3">{actions}</div>}
      </div>

      {/* Main content grid */}
      <div className="flex flex-col lg:flex-row gap-6 items-start">
        {filters && (
          <aside className="w-full lg:w-64 shrink-0 bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-5 shadow-sm">
            <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-4">
              Filters
            </h2>
            {filters}
          </aside>
        )}
        <main className="flex-1 w-full bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm overflow-hidden">
          {children}
        </main>
      </div>
    </div>
  );
};

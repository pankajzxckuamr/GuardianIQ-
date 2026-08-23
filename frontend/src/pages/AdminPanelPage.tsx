import React from "react";
import { ModuleLayout } from "../components/layout/ModuleLayout";
import { Settings, Database, ShieldAlert } from "lucide-react";
import { Link } from "react-router-dom";

export const AdminPanelPage: React.FC = () => {
  return (
    <ModuleLayout
      title="Administration Panel"
      description="Manage platform tenants, configure users & roles, and adjust compliance settings."
    >
      <div className="p-8 text-center space-y-6 max-w-lg mx-auto">
        <div className="inline-flex p-4 bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 rounded-full">
          <Settings className="h-12 w-12" />
        </div>
        <div className="space-y-2">
          <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Admin Settings & Configuration</h2>
          <p className="text-slate-500 dark:text-slate-400 text-sm">
            Access settings for multi-tenant isolation, enterprise user synchronizations, and system configurations.
          </p>
        </div>
      </div>
      
      <div className="p-8 max-w-4xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-6">
        <Link to="/admin/event-schemas" className="block bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-6 hover:shadow-md transition-all hover:-translate-y-1">
          <div className="flex items-center gap-4 mb-4">
            <div className="p-3 bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 rounded-lg">
              <Database className="h-6 w-6" />
            </div>
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white">Event Schema Registry</h3>
          </div>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Define and manage canonical event structures, validation schemas, and versioning for all governance events.
          </p>
        </Link>
        
        <Link to="/admin/event-retention" className="block bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-6 hover:shadow-md transition-all hover:-translate-y-1">
          <div className="flex items-center gap-4 mb-4">
            <div className="p-3 bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 rounded-lg">
              <ShieldAlert className="h-6 w-6" />
            </div>
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white">Retention Rules</h3>
          </div>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Configure data lifecycle policies, specify how long to keep event data, and set up archival rules.
          </p>
        </Link>
      </div>
    </ModuleLayout>
  );
};

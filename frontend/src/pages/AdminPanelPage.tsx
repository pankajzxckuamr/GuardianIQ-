import React from "react";
import { ModuleLayout } from "../components/layout/ModuleLayout";
import { Settings } from "lucide-react";

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
    </ModuleLayout>
  );
};

import React from "react";
import { ModuleLayout } from "../components/layout/ModuleLayout";
import { ShieldAlert } from "lucide-react";

export const RiskWorkspacePage: React.FC = () => {
  return (
    <ModuleLayout
      title="Risk Findings Workspace"
      description="Assess, classify, and mitigate risk across AI models and autonomous systems."
    >
      <div className="p-8 text-center space-y-6 max-w-lg mx-auto">
        <div className="inline-flex p-4 bg-red-50 dark:bg-red-950/30 text-red-600 dark:text-red-400 rounded-full">
          <ShieldAlert className="h-12 w-12" />
        </div>
        <div className="space-y-2">
          <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Risk Evaluation & Management</h2>
          <p className="text-slate-500 dark:text-slate-400 text-sm">
            Review security assessments, sensitive data leaks, and system vulnerability ratings.
          </p>
        </div>
        <div className="grid grid-cols-2 gap-4 text-left">
          <div className="p-4 bg-slate-50 dark:bg-slate-800/50 rounded-lg">
            <span className="block text-2xl font-bold text-slate-900 dark:text-white">LOW</span>
            <span className="text-xs text-slate-500">Overall Risk Level</span>
          </div>
          <div className="p-4 bg-slate-50 dark:bg-slate-800/50 rounded-lg">
            <span className="block text-2xl font-bold text-indigo-600 dark:text-indigo-400">18</span>
            <span className="text-xs text-slate-500">Scanned Assets</span>
          </div>
        </div>
      </div>
    </ModuleLayout>
  );
};

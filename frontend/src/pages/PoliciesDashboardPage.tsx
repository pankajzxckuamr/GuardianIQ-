import React from "react";
import { ModuleLayout } from "../components/layout/ModuleLayout";
import { ShieldCheck } from "lucide-react";

export const PoliciesDashboardPage: React.FC = () => {
  return (
    <ModuleLayout
      title="Policy Dashboard"
      description="Define, monitor, and enforce compliance policies across enterprise AI workflows."
    >
      <div className="p-8 text-center space-y-6 max-w-lg mx-auto">
        <div className="inline-flex p-4 bg-indigo-50 dark:bg-indigo-950/30 text-indigo-600 dark:text-indigo-400 rounded-full">
          <ShieldCheck className="h-12 w-12" />
        </div>
        <div className="space-y-2">
          <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Active Policies & Rules</h2>
          <p className="text-slate-500 dark:text-slate-400 text-sm">
            All running workflows are automatically evaluated against the active compliance constraints defined here.
          </p>
        </div>
        <div className="grid grid-cols-3 gap-4 text-left">
          <div className="p-4 bg-slate-50 dark:bg-slate-800/50 rounded-lg">
            <span className="block text-2xl font-bold text-slate-900 dark:text-white">12</span>
            <span className="text-xs text-slate-500">Active Policies</span>
          </div>
          <div className="p-4 bg-slate-50 dark:bg-slate-800/50 rounded-lg">
            <span className="block text-2xl font-bold text-emerald-600 dark:text-emerald-400">100%</span>
            <span className="text-xs text-slate-500">Compliance Rate</span>
          </div>
          <div className="p-4 bg-slate-50 dark:bg-slate-800/50 rounded-lg">
            <span className="block text-2xl font-bold text-amber-500">0</span>
            <span className="text-xs text-slate-500">Active Violations</span>
          </div>
        </div>
      </div>
    </ModuleLayout>
  );
};

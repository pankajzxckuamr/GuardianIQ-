import React from "react";
import { ModuleLayout } from "../components/layout/ModuleLayout";
import { Clock } from "lucide-react";

export const ApprovalHubPage: React.FC = () => {
  return (
    <ModuleLayout
      title="Approval Hub"
      description="Approve relationship requests, model activations, and governance delegations."
    >
      <div className="p-8 text-center space-y-6 max-w-lg mx-auto">
        <div className="inline-flex p-4 bg-amber-50 dark:bg-amber-950/30 text-amber-600 dark:text-amber-400 rounded-full">
          <Clock className="h-12 w-12" />
        </div>
        <div className="space-y-2">
          <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Pending Requests</h2>
          <p className="text-slate-500 dark:text-slate-400 text-sm">
            You have no pending governance approvals or state change requests.
          </p>
        </div>
      </div>
    </ModuleLayout>
  );
};

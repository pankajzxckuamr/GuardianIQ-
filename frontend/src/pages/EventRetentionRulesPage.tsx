import React, { useEffect, useState } from "react";
import { ModuleLayout } from "../components/layout/ModuleLayout";
import { ShieldAlert, Plus, Search, Clock, Edit2 } from "lucide-react";

interface RetentionRule {
  id: string;
  rule_name: string;
  event_category: string;
  classification: string;
  retention_days: number;
  archive_after_days: number;
  is_active: boolean;
}

export const EventRetentionRulesPage: React.FC = () => {
  const [rules, setRules] = useState<RetentionRule[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");

  useEffect(() => {
    const fetchRules = async () => {
      try {
        const tokenStr = sessionStorage.getItem("guardianiq_access_token");
        const token = tokenStr ? JSON.parse(tokenStr) : null;
        const response = await fetch("/api/v1/events/retention-rules", {
          headers: {
            Authorization: `Bearer ${token}`,
          }
        });
        const result = await response.json();
        if (result.success) {
          setRules(result.data);
        }
      } catch (e) {
        console.error("Failed to fetch rules", e);
      } finally {
        setLoading(false);
      }
    };
    fetchRules();
  }, []);

  const filteredRules = rules.filter(r => 
    r.rule_name.toLowerCase().includes(search.toLowerCase()) || 
    r.event_category.toLowerCase().includes(search.toLowerCase()) ||
    r.classification.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <ModuleLayout
      title="Retention Rules"
      description="Configure data lifecycle and retention policies for events."
    >
      <div className="space-y-6">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div className="relative max-w-md w-full">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400" />
            <input
              type="text"
              placeholder="Search retention rules..."
              className="w-full pl-10 pr-4 py-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none text-slate-900 dark:text-white"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <button className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors font-medium">
            <Plus className="h-5 w-5" />
            <span>New Rule</span>
          </button>
        </div>

        {loading ? (
          <div className="flex justify-center p-12">
            <div className="animate-spin h-8 w-8 border-4 border-blue-500 rounded-full border-t-transparent"></div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
            {filteredRules.map(rule => (
              <div key={rule.id} className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 overflow-hidden hover:shadow-lg transition-shadow duration-300">
                <div className="p-6">
                  <div className="flex justify-between items-start mb-4">
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 rounded-lg">
                        <ShieldAlert className="h-6 w-6" />
                      </div>
                      <div>
                        <h3 className="text-lg font-semibold text-slate-900 dark:text-white">{rule.rule_name}</h3>
                        <p className="text-sm text-slate-500 dark:text-slate-400">{rule.event_category}</p>
                      </div>
                    </div>
                    <button className="p-2 text-slate-400 hover:text-blue-600 dark:hover:text-blue-400 hover:bg-slate-50 dark:hover:bg-slate-700/50 rounded-lg transition-colors">
                      <Edit2 className="h-4 w-4" />
                    </button>
                  </div>
                  
                  <div className="space-y-4">
                    <div className="flex items-center justify-between py-2 border-b border-slate-100 dark:border-slate-700">
                      <span className="text-sm text-slate-500 dark:text-slate-400">Classification</span>
                      <span className="px-2.5 py-1 rounded-md text-xs font-medium bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300">
                        {rule.classification}
                      </span>
                    </div>
                    
                    <div className="flex items-center justify-between py-2 border-b border-slate-100 dark:border-slate-700">
                      <div className="flex items-center gap-2 text-sm text-slate-500 dark:text-slate-400">
                        <Clock className="h-4 w-4" />
                        <span>Archive After</span>
                      </div>
                      <span className="text-sm font-semibold text-slate-900 dark:text-white">{rule.archive_after_days} days</span>
                    </div>
                    
                    <div className="flex items-center justify-between py-2">
                      <div className="flex items-center gap-2 text-sm text-slate-500 dark:text-slate-400">
                        <ShieldAlert className="h-4 w-4" />
                        <span>Retention</span>
                      </div>
                      <span className="text-sm font-semibold text-red-600 dark:text-red-400">{rule.retention_days} days</span>
                    </div>
                  </div>
                </div>
                <div className={`px-6 py-3 border-t border-slate-200 dark:border-slate-700 flex items-center justify-between ${rule.is_active ? 'bg-emerald-50 dark:bg-emerald-900/10' : 'bg-slate-50 dark:bg-slate-900/50'}`}>
                  <span className={`text-sm font-medium ${rule.is_active ? 'text-emerald-700 dark:text-emerald-400' : 'text-slate-500 dark:text-slate-400'}`}>
                    {rule.is_active ? 'Status: Active' : 'Status: Inactive'}
                  </span>
                  <div className={`h-2.5 w-2.5 rounded-full ${rule.is_active ? 'bg-emerald-500' : 'bg-slate-400'}`}></div>
                </div>
              </div>
            ))}

            {filteredRules.length === 0 && (
              <div className="col-span-full text-center py-12 bg-slate-50 dark:bg-slate-800/50 rounded-xl border border-dashed border-slate-300 dark:border-slate-700">
                <ShieldAlert className="h-12 w-12 text-slate-400 mx-auto mb-4 opacity-50" />
                <h3 className="text-lg font-medium text-slate-900 dark:text-white">No rules found</h3>
                <p className="text-slate-500 dark:text-slate-400 mt-2">Adjust your search or create a new retention rule.</p>
              </div>
            )}
          </div>
        )}
      </div>
    </ModuleLayout>
  );
};

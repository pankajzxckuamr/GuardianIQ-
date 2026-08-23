import React, { useEffect, useState } from "react";
import { ModuleLayout } from "../components/layout/ModuleLayout";
import { Database, Plus, Search, Edit2 } from "lucide-react";

interface EventSchema {
  id: string;
  event_type: string;
  category: string;
  version: string;
  schema_payload: any;
  is_active: boolean;
  created_at: string;
}

export const EventSchemaRegistryPage: React.FC = () => {
  const [schemas, setSchemas] = useState<EventSchema[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");

  useEffect(() => {
    // In a real app we'd use our api client, but this simulates fetching
    const fetchSchemas = async () => {
      try {
        const tokenStr = sessionStorage.getItem("guardianiq_access_token");
        const token = tokenStr ? JSON.parse(tokenStr) : null;
        const response = await fetch("/api/v1/events/schemas", {
          headers: {
            Authorization: `Bearer ${token}`,
          }
        });
        const result = await response.json();
        if (result.success) {
          setSchemas(result.data);
        }
      } catch (e) {
        console.error("Failed to fetch schemas", e);
      } finally {
        setLoading(false);
      }
    };
    fetchSchemas();
  }, []);

  const filteredSchemas = schemas.filter(s => 
    s.event_type.toLowerCase().includes(search.toLowerCase()) || 
    s.category.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <ModuleLayout
      title="Event Schema Registry"
      description="Manage and version schemas for governance events."
    >
      <div className="space-y-6">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div className="relative max-w-md w-full">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400" />
            <input
              type="text"
              placeholder="Search schemas..."
              className="w-full pl-10 pr-4 py-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none text-slate-900 dark:text-white"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <button className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors font-medium">
            <Plus className="h-5 w-5" />
            <span>New Schema</span>
          </button>
        </div>

        {loading ? (
          <div className="flex justify-center p-12">
            <div className="animate-spin h-8 w-8 border-4 border-blue-500 rounded-full border-t-transparent"></div>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {filteredSchemas.map(schema => (
              <div key={schema.id} className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-6 hover:shadow-lg transition-shadow duration-300">
                <div className="flex justify-between items-start mb-4">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 rounded-lg">
                      <Database className="h-6 w-6" />
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold text-slate-900 dark:text-white">{schema.event_type}</h3>
                      <p className="text-sm text-slate-500 dark:text-slate-400">{schema.category} • v{schema.version}</p>
                    </div>
                  </div>
                  <button className="p-2 text-slate-400 hover:text-blue-600 dark:hover:text-blue-400 hover:bg-slate-50 dark:hover:bg-slate-700/50 rounded-lg transition-colors">
                    <Edit2 className="h-4 w-4" />
                  </button>
                </div>
                
                <div className="mt-4">
                  <div className="flex justify-between text-sm mb-2">
                    <span className="font-medium text-slate-700 dark:text-slate-300">Payload Schema</span>
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${schema.is_active ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400' : 'bg-slate-100 text-slate-700 dark:bg-slate-700 dark:text-slate-300'}`}>
                      {schema.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </div>
                  <div className="bg-slate-50 dark:bg-slate-900 rounded-lg p-4 font-mono text-xs text-slate-600 dark:text-slate-400 overflow-x-auto">
                    <pre>{JSON.stringify(schema.schema_payload, null, 2)}</pre>
                  </div>
                </div>
              </div>
            ))}

            {filteredSchemas.length === 0 && (
              <div className="col-span-full text-center py-12 bg-slate-50 dark:bg-slate-800/50 rounded-xl border border-dashed border-slate-300 dark:border-slate-700">
                <Database className="h-12 w-12 text-slate-400 mx-auto mb-4 opacity-50" />
                <h3 className="text-lg font-medium text-slate-900 dark:text-white">No schemas found</h3>
                <p className="text-slate-500 dark:text-slate-400 mt-2">Adjust your search or create a new schema.</p>
              </div>
            )}
          </div>
        )}
      </div>
    </ModuleLayout>
  );
};

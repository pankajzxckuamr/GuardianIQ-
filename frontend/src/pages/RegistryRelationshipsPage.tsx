/* src/pages/RegistryRelationshipsPage.tsx */

import React, { useEffect, useState } from "react";
import { PageHeader } from "../components/common/PageHeader";
import { RelationshipViewer } from "../components/registry/RelationshipViewer";
import * as registryService from "../services/registry/registryService";
import { Brain, Cpu, Plug, GitBranch, Database, Building2, Network } from "lucide-react";
import styles from "./RegistryRelationshipsPage.module.css";

interface EntitySelectItem {
  id: string;
  name: string;
  code: string;
}

export const RegistryRelationshipsPage: React.FC = () => {
  const [selectedCategory, setSelectedCategory] = useState<string>("MODEL");
  const [entities, setEntities] = useState<EntitySelectItem[]>([]);
  const [selectedEntityId, setSelectedEntityId] = useState<string>("");
  const [loadingEntities, setLoadingEntities] = useState(false);

  // Set page document title
  useEffect(() => {
    document.title = "Relationships Explorer — GuardianIQ Registry";
  }, []);

  const categories = [
    { type: "MODEL", label: "AI Models", icon: <Brain size={20} /> },
    { type: "AGENT", label: "AI Agents", icon: <Cpu size={20} /> },
    { type: "TOOL", label: "Tools & Connectors", icon: <Plug size={20} /> },
    { type: "WORKFLOW", label: "Workflows", icon: <GitBranch size={20} /> },
    { type: "DATA_SOURCE", label: "Data Sources", icon: <Database size={20} /> },
    { type: "DEPARTMENT", label: "Departments", icon: <Building2 size={20} /> }
  ];

  // Load entities when category changes
  useEffect(() => {
    async function loadEntities() {
      setLoadingEntities(true);
      setEntities([]);
      setSelectedEntityId("");
      try {
        let items: EntitySelectItem[] = [];
        if (selectedCategory === "MODEL") {
          const res = await registryService.listModels({ per_page: 100 });
          items = (res.data?.items || []).map((m: any) => ({
            id: m.id,
            name: m.model_name,
            code: m.model_code
          }));
        } else if (selectedCategory === "AGENT") {
          const res = await registryService.listAgents({ per_page: 100 });
          items = (res.data?.items || []).map((a: any) => ({
            id: a.id,
            name: a.agent_name,
            code: a.agent_code
          }));
        } else if (selectedCategory === "TOOL") {
          const res = await registryService.listTools({ per_page: 100 });
          items = (res.data?.items || []).map((t: any) => ({
            id: t.id,
            name: t.tool_name,
            code: t.tool_code
          }));
        } else if (selectedCategory === "WORKFLOW") {
          const res = await registryService.listWorkflows({ per_page: 100 });
          items = (res.data?.items || []).map((w: any) => ({
            id: w.id,
            name: w.workflow_name,
            code: w.workflow_code
          }));
        } else if (selectedCategory === "DATA_SOURCE") {
          const res = await registryService.listDataSources({ per_page: 100 });
          items = (res.data?.items || []).map((ds: any) => ({
            id: ds.id,
            name: ds.source_name,
            code: ds.source_code
          }));
        } else if (selectedCategory === "DEPARTMENT") {
          const res = await registryService.listDepartments({ per_page: 100 });
          items = (res.data?.items || []).map((d: any) => ({
            id: d.id,
            name: d.department_name,
            code: d.department_code
          }));
        }
        setEntities(items);
        if (items.length > 0) {
          setSelectedEntityId(items[0].id);
        }
      } catch (err) {
        console.error("Failed to load category entities for relationships:", err);
      } finally {
        setLoadingEntities(false);
      }
    }

    loadEntities();
  }, [selectedCategory]);

  return (
    <div className={styles.page}>
      {/* Text Breadcrumb */}
      <div className={styles.breadcrumb}>Registry &gt; Relationships Explorer</div>

      <PageHeader
        title="Registry Relationships Explorer"
        description="Visualize system connection trees, linkages, outgoing data targets, and incoming triggers"
      />

      <div className={styles.explorerPanel}>
        <h3 className={styles.panelTitle}>1. Select Target Category</h3>
        
        {/* Category Cards Selector Grid */}
        <div className={styles.categoryGrid}>
          {categories.map((cat) => (
            <div
              key={cat.type}
              onClick={() => setSelectedCategory(cat.type)}
              className={`${styles.categoryCard} ${selectedCategory === cat.type ? styles.categoryCardActive : ""}`}
            >
              <div className={styles.iconWrapper}>{cat.icon}</div>
              <span className={styles.cardTitle}>{cat.label}</span>
            </div>
          ))}
        </div>

        {/* Target Entity Select */}
        <div className={styles.selectorContainer}>
          <label htmlFor="entitySelect" className={styles.label}>
            2. Choose Active {categories.find(c => c.type === selectedCategory)?.label || "Asset"}
          </label>
          {loadingEntities ? (
            <div className={styles.loadingSpinner}>
              <span>Loading registered assets...</span>
            </div>
          ) : (
            <select
              id="entitySelect"
              value={selectedEntityId}
              onChange={(e) => setSelectedEntityId(e.target.value)}
              className={styles.select}
              disabled={entities.length === 0}
            >
              {entities.length === 0 ? (
                <option value="">No registered items found in this category</option>
              ) : (
                entities.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.name} ({item.code})
                  </option>
                ))
              )}
            </select>
          )}
        </div>
      </div>

      {/* Render RelationshipViewer once target is active */}
      <div className={styles.viewerContainer}>
        {selectedEntityId ? (
          <RelationshipViewer entityType={selectedCategory} entityId={selectedEntityId} />
        ) : (
          <div className={styles.emptyState}>
            <Network size={36} style={{ color: "rgba(255, 255, 255, 0.15)", marginBottom: "0.75rem" }} />
            <h4 className={styles.emptyTitle}>Select an Entity to Trace Links</h4>
            <p className={styles.emptyDesc}>
              Choose a governance category above and select an active registered item to load its linkage paths, dependency graphs, and relationships.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default RegistryRelationshipsPage;

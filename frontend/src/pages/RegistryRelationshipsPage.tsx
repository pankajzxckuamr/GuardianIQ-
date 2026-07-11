/* src/pages/RegistryRelationshipsPage.tsx */

import React, { useEffect, useState } from "react";
import { PageHeader } from "../components/common/PageHeader";
import { RelationshipViewer } from "../components/registry/RelationshipViewer";
import { RegistryDataTable } from "../components/common/RegistryDataTable";
import { Badge } from "../components/common/Badge";
import * as registryService from "../services/registry/registryService";
import { Brain, Cpu, Plug, GitBranch, Database, Building2, Network, List, Share2 } from "lucide-react";
import styles from "./RegistryRelationshipsPage.module.css";

interface EntitySelectItem {
  id: string;
  name: string;
  code: string;
}

export const RegistryRelationshipsPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<"LIST" | "EXPLORER">("LIST");
  
  // List View State
  const [relationships, setRelationships] = useState<any[]>([]);
  const [loadingList, setLoadingList] = useState(false);
  const [totalList, setTotalList] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  
  // Explorer View State
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

  // Load Relationships List
  useEffect(() => {
    if (activeTab !== "LIST") return;
    
    async function fetchList() {
      setLoadingList(true);
      try {
        const res = await registryService.listRelationships({ page, per_page: pageSize });
        setRelationships(res.data?.items || []);
        setTotalList(res.data?.total || 0);
      } catch (err) {
        console.error("Failed to load relationships list", err);
      } finally {
        setLoadingList(false);
      }
    }
    fetchList();
  }, [activeTab, page, pageSize]);

  // Load entities when category changes in Explorer
  useEffect(() => {
    if (activeTab !== "EXPLORER") return;

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
  }, [selectedCategory, activeTab]);

  const listColumns = [
    {
      header: "Type",
      accessor: (row: any) => <Badge variant="info" label={row.relationship_type} />
    },
    {
      header: "Source Type",
      accessor: (row: any) => <Badge variant="neutral" label={row.source_type} />
    },
    {
      header: "Target Type",
      accessor: (row: any) => <Badge variant="neutral" label={row.target_type} />
    },
    {
      header: "Status",
      accessor: (row: any) => <Badge variant={row.status === 'ACTIVE' ? 'success' : 'neutral'} label={row.status} />
    },
    {
      header: "Effective From",
      accessor: "effective_from"
    }
  ];

  return (
    <div className={styles.page}>
      {/* Text Breadcrumb */}
      <div className={styles.breadcrumb}>Registry &gt; Relationships Management</div>

      <PageHeader
        title="Registry Relationships"
        description="Manage and visualize system connection trees, linkages, outgoing data targets, and incoming triggers"
      />

      <div className={styles.tabsContainer} style={{ display: 'flex', gap: '1rem', marginBottom: '1.5rem', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '0.5rem' }}>
        <button 
          onClick={() => setActiveTab("LIST")}
          style={{ background: 'transparent', border: 'none', color: activeTab === 'LIST' ? '#fff' : 'rgba(255,255,255,0.6)', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.5rem 1rem', borderBottom: activeTab === 'LIST' ? '2px solid #3b82f6' : 'none' }}
        >
          <List size={18} /> Directory List
        </button>
        <button 
          onClick={() => setActiveTab("EXPLORER")}
          style={{ background: 'transparent', border: 'none', color: activeTab === 'EXPLORER' ? '#fff' : 'rgba(255,255,255,0.6)', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.5rem 1rem', borderBottom: activeTab === 'EXPLORER' ? '2px solid #3b82f6' : 'none' }}
        >
          <Share2 size={18} /> Graph Explorer
        </button>
      </div>

      {activeTab === "LIST" && (
        <RegistryDataTable
          data={relationships}
          columns={listColumns}
          loading={loadingList}
          totalCount={totalList}
          currentPage={page}
          pageSize={pageSize}
          onPageChange={setPage}
          onPageSizeChange={setPageSize}
          emptyStateTitle="No Relationships Found"
          emptyStateDesc="There are no active relationships matching your criteria."
        />
      )}

      {activeTab === "EXPLORER" && (
        <>
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
        </>
      )}
    </div>
  );
};

export default RegistryRelationshipsPage;


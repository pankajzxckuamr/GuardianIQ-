/* src/pages/RegistryRelationshipsPage.tsx */

import React, { useEffect, useState } from "react";
import { PageHeader } from "../components/common/PageHeader";
import { RelationshipViewer } from "../components/registry/RelationshipViewer";
import { RegistryDataTable } from "../components/common/RegistryDataTable";
import { Badge } from "../components/common/Badge";
import * as registryService from "../services/registry/registryService";
import { Brain, Cpu, Plug, GitBranch, Database, Building2, Network, List, Share2, CheckCircle, PlayCircle, PauseCircle, Trash2, AlertTriangle, ShieldAlert, ShieldCheck, Zap, Activity, Layers, Users, LayoutGrid } from "lucide-react";
import { useRegistryFilters } from "../hooks/useRegistryFilters";
import { useToast } from "../hooks/useToast";
import { useAuth } from "../hooks/useAuth";
import { Button } from "../components/common/Button";
import styles from "./RegistryRelationshipsPage.module.css";

interface EntitySelectItem {
  id: string;
  name: string;
  code: string;
}

export const RegistryRelationshipsPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<"LIST" | "EXPLORER" | "IMPACT">("LIST");
  const { showToast } = useToast();
  const { currentUser } = useAuth();
  
  // Filters & State mapping
  const { filters, setFilter, resetFilters, paginationProps } = useRegistryFilters("created_at");
  const [searchTerm, setSearchTerm] = useState(filters.search || "");
  const [relationships, setRelationships] = useState<any[]>([]);
  const [loadingList, setLoadingList] = useState(false);
  const [totalList, setTotalList] = useState(0);
  const [relationshipTypes, setRelationshipTypes] = useState<string[]>([]);
  
  // Explorer View State
  const [selectedCategory, setSelectedCategory] = useState<string>("MODEL");
  const [entities, setEntities] = useState<EntitySelectItem[]>([]);
  const [selectedEntityId, setSelectedEntityId] = useState<string>("");
  const [loadingEntities, setLoadingEntities] = useState(false);

  // Impact Analysis State
  const [loadingImpact, setLoadingImpact] = useState(false);
  const [changeType, setChangeType] = useState<string>("UPDATE");
  const [impactData, setImpactData] = useState<any>(null);
  const [impactViewMode, setImpactViewMode] = useState<"MATRIX" | "GRAPH">("MATRIX");

  const mapCategoryToBackendType = (cat: string) => {
    switch (cat) {
      case "MODEL": return "ai_models";
      case "AGENT": return "agents";
      case "TOOL": return "tools";
      case "WORKFLOW": return "workflows";
      case "DATA_SOURCE": return "data_sources";
      case "DEPARTMENT": return "departments";
      default: return cat.toLowerCase();
    }
  };

  const fetchImpact = async () => {
    if (!selectedEntityId) return;
    setLoadingImpact(true);
    setImpactData(null);
    try {
      const backendType = mapCategoryToBackendType(selectedCategory);
      const res = await registryService.getImpactAnalysis(backendType, selectedEntityId, changeType);
      if (res.data) {
        const dependents = res.data.impacted_dependents || [];
        const mappedDeps = dependents.map((dep: any) => ({
          id: dep.source_id,
          name: dep.other_entity_name || dep.source_id,
          type: dep.other_entity_type ? dep.other_entity_type.replace('_', ' ').toUpperCase() : 'UNKNOWN',
          relationship_type: dep.relationship_type,
          target_id: dep.target_id
        }));

        const direct_impacts = mappedDeps.filter((dep: any) => dep.target_id === selectedEntityId);
        const indirect_impacts = mappedDeps.filter((dep: any) => dep.target_id !== selectedEntityId);
        
        const totalCount = direct_impacts.length + indirect_impacts.length;
        let impact_level = "LOW";
        if (totalCount > 0) {
          if (changeType === "REVOKE") {
            impact_level = "HIGH";
          } else if (changeType === "SUSPEND") {
            impact_level = "MEDIUM";
          }
        }

        setImpactData({
          impact_level,
          direct_impact_count: direct_impacts.length,
          indirect_impact_count: indirect_impacts.length,
          direct_impacts,
          indirect_impacts
        });
      }
    } catch (err: any) {
      showToast(err.message || "Failed to run impact analysis", "error");
    } finally {
      setLoadingImpact(false);
    }
  };

  useEffect(() => {
    if (activeTab === "IMPACT" && selectedEntityId) {
      fetchImpact();
    }
  }, [activeTab, selectedEntityId, changeType]);

  // Set page document title
  useEffect(() => {
    document.title = "Relationships Explorer — GuardianIQ Registry";
  }, []);

  // Load relationship types for filtering options
  useEffect(() => {
    async function loadTypes() {
      try {
        const res = await registryService.getRelationshipTypes();
        if (res.data) setRelationshipTypes(res.data);
      } catch (err) {
        console.error("Failed to load relationship types lookup", err);
      }
    }
    loadTypes();
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
  const fetchList = async () => {
    if (activeTab !== "LIST") return;
    setLoadingList(true);
    try {
      const res = await registryService.listRelationships({
        page: filters.page,
        per_page: filters.pageSize,
        source_type: filters.source_type,
        target_type: filters.target_type,
        relationship_type: filters.relationship_type,
        status: filters.status,
        search: filters.search
      });
      setRelationships(res.data?.items || []);
      setTotalList(res.data?.total || 0);
    } catch (err) {
      console.error("Failed to load relationships list", err);
    } finally {
      setLoadingList(false);
    }
  };

  useEffect(() => {
    fetchList();
  }, [
    activeTab, 
    filters.page, 
    filters.pageSize, 
    filters.source_type, 
    filters.target_type, 
    filters.relationship_type, 
    filters.status,
    filters.search
  ]);

  // Debounce free text search input
  useEffect(() => {
    const delayDebounceFn = setTimeout(() => {
      setFilter("search", searchTerm);
    }, 400);
    return () => clearTimeout(delayDebounceFn);
  }, [searchTerm, setFilter]);

  // Load entities when category changes in Explorer or Impact tab
  useEffect(() => {
    if (activeTab !== "EXPLORER" && activeTab !== "IMPACT") return;

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

  const handleAction = async (id: string, action: string) => {
    try {
      let res: any;
      if (action === 'revoke') {
        const reason = window.prompt("Please enter mandatory revocation reason:");
        if (reason === null) return;
        if (!reason.trim()) {
          showToast("Revocation reason is mandatory", "error");
          return;
        }
        res = await registryService.revokeRelationship(id, reason);
      } else if (action === 'suspend') {
        const reason = window.prompt("Please enter mandatory suspension reason:");
        if (reason === null) return;
        if (!reason.trim()) {
          showToast("Suspension reason is mandatory", "error");
          return;
        }
        res = await registryService.suspendRelationship(id, reason);
      } else if (action === 'approve') {
        res = await registryService.approveRelationship(id);
      } else if (action === 'activate') {
        res = await registryService.activateRelationship(id);
      }
      
      const reqIdText = res?.request_id ? ` (Request ID: ${res.request_id})` : '';
      showToast(`Relationship ${action}d successfully${reqIdText}`, "success");
      fetchList();
    } catch (err: any) {
      showToast(err.message || `Failed to ${action} relationship`, "error");
    }
  };

  const listColumns = [
    {
      key: "relationship_type",
      label: "Type",
      render: (row: any) => <Badge variant="info" label={row.relationship_type} />
    },
    {
      key: "source_name",
      label: "Source Entity",
      render: (row: any) => (
        <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
          <span style={{ fontWeight: 500, color: "#fff" }}>{row.source_name || row.source_id}</span>
          <span style={{ fontSize: "0.75rem", color: "rgba(255, 255, 255, 0.45)" }}>{row.source_type}</span>
        </div>
      )
    },
    {
      key: "target_name",
      label: "Target Entity",
      render: (row: any) => (
        <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
          <span style={{ fontWeight: 500, color: "#fff" }}>{row.target_name || row.target_id}</span>
          <span style={{ fontSize: "0.75rem", color: "rgba(255, 255, 255, 0.45)" }}>{row.target_type}</span>
        </div>
      )
    },
    {
      key: "relationship_scope",
      label: "Scope",
      render: (row: any) => row.relationship_scope || "-"
    },
    {
      key: "responsibility_type",
      label: "Responsibility",
      render: (row: any) => (
        <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
          {row.responsibility_type ? (
            <Badge variant="warning" label={row.responsibility_type} />
          ) : (
            <span style={{ color: "rgba(255, 255, 255, 0.45)", fontSize: "0.85rem" }}>-</span>
          )}
          {row.responsible_user_name && (
            <span style={{ fontSize: "0.75rem", color: "#38bdf8", fontWeight: 500 }}>
              {row.responsible_user_name}
            </span>
          )}
        </div>
      )
    },
    {
      key: "status",
      label: "Status",
      render: (row: any) => {
        let variant: "success" | "neutral" | "warning" | "danger" | "info" = "neutral";
        if (row.status === "ACTIVE") variant = "success";
        else if (row.status === "PROPOSED" || row.status === "PENDING_APPROVAL") variant = "warning";
        else if (row.status === "SUSPENDED" || row.status === "REVOKED") variant = "danger";
        return <Badge variant={variant} label={row.status} />;
      }
    },
    {
      key: "actions",
      label: "Actions",
      render: (row: any) => {
        const isAdminOrOwner = currentUser?.is_superuser || 
          currentUser?.roles?.some(role => ["admin", "super_admin", "governance_manager"].includes(role.toLowerCase()));
        
        if (!isAdminOrOwner) return null;
        
        return (
          <div style={{ display: "flex", gap: "4px" }}>
            {row.status === 'PROPOSED' && (
              <Button variant="ghost" size="sm" onClick={() => handleAction(row.id, 'approve')} title="Approve" style={{ padding: "4px" }}>
                <CheckCircle size={16} />
              </Button>
            )}
            {row.status === 'PENDING_APPROVAL' && (
              <Button variant="ghost" size="sm" onClick={() => handleAction(row.id, 'activate')} title="Activate" style={{ padding: "4px" }}>
                <PlayCircle size={16} />
              </Button>
            )}
            {row.status === 'ACTIVE' && (
              <Button variant="ghost" size="sm" onClick={() => handleAction(row.id, 'suspend')} title="Suspend" style={{ padding: "4px" }}>
                <PauseCircle size={16} />
              </Button>
            )}
            <Button variant="ghost" size="sm" onClick={() => handleAction(row.id, 'revoke')} title="Revoke" style={{ padding: "4px", color: "#ef4444" }}>
              <Trash2 size={16} />
            </Button>
          </div>
        );
      }
    }
  ];

  return (
    <div className={styles.page}>
      {/* Dynamic Breadcrumbs */}
      <div className={styles.breadcrumb}>
        Registry &gt; Relationships Explorer
        {activeTab === "EXPLORER" && selectedCategory && (
          <> &gt; {selectedCategory}</>
        )}
        {activeTab === "EXPLORER" && selectedEntityId && (
          <> &gt; {entities.find(e => e.id === selectedEntityId)?.name || selectedEntityId}</>
        )}
        {activeTab === "IMPACT" && selectedCategory && (
          <> &gt; {selectedCategory}</>
        )}
        {activeTab === "IMPACT" && selectedEntityId && (
          <> &gt; {entities.find(e => e.id === selectedEntityId)?.name || selectedEntityId}</>
        )}
        &gt; {activeTab === "LIST" ? "Directory List" : activeTab === "EXPLORER" ? "Graph Explorer" : "Impact Analysis"}
      </div>

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
        <button 
          onClick={() => setActiveTab("IMPACT")}
          style={{ background: 'transparent', border: 'none', color: activeTab === 'IMPACT' ? '#fff' : 'rgba(255,255,255,0.6)', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.5rem 1rem', borderBottom: activeTab === 'IMPACT' ? '2px solid #3b82f6' : 'none' }}
        >
          <Network size={18} /> Impact Analysis
        </button>
      </div>

      {activeTab === "LIST" && (
        <>
          {/* Filter Bar */}
          <div className={styles.filterBar}>
            <div style={{ flex: 1, minWidth: '200px' }}>
              <input
                type="text"
                placeholder="Search by ID or Scope..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className={styles.filterInput}
              />
            </div>
            
            {/* Source Type */}
            <select
              value={filters.source_type || ""}
              onChange={(e) => setFilter("source_type", e.target.value)}
              className={styles.filterSelect}
            >
              <option value="">All Source Types</option>
              <option value="agents">AI Agent</option>
              <option value="ai_models">AI Model</option>
              <option value="tools">Tool</option>
              <option value="workflows">Workflow</option>
              <option value="data_sources">Data Source</option>
              <option value="departments">Department</option>
              <option value="users">User</option>
              <option value="roles">Role</option>
            </select>
            
            {/* Target Type */}
            <select
              value={filters.target_type || ""}
              onChange={(e) => setFilter("target_type", e.target.value)}
              className={styles.filterSelect}
            >
              <option value="">All Target Types</option>
              <option value="agents">AI Agent</option>
              <option value="ai_models">AI Model</option>
              <option value="tools">Tool</option>
              <option value="workflows">Workflow</option>
              <option value="data_sources">Data Source</option>
              <option value="departments">Department</option>
              <option value="users">User</option>
              <option value="roles">Role</option>
            </select>
            
            {/* Relationship Type */}
            <select
              value={filters.relationship_type || ""}
              onChange={(e) => setFilter("relationship_type", e.target.value)}
              className={styles.filterSelect}
            >
              <option value="">All Relationship Types</option>
              {relationshipTypes.map((type) => (
                <option key={type} value={type}>
                  {type}
                </option>
              ))}
            </select>
            
            {/* Status */}
            <select
              value={filters.status || ""}
              onChange={(e) => setFilter("status", e.target.value)}
              className={styles.filterSelect}
            >
              <option value="">All Statuses</option>
              <option value="PROPOSED">PROPOSED</option>
              <option value="PENDING_APPROVAL">PENDING_APPROVAL</option>
              <option value="ACTIVE">ACTIVE</option>
              <option value="SUSPENDED">SUSPENDED</option>
              <option value="REVOKED">REVOKED</option>
              <option value="EXPIRED">EXPIRED</option>
              <option value="ARCHIVED">ARCHIVED</option>
            </select>
            
            <button
              onClick={() => {
                setSearchTerm("");
                resetFilters();
              }}
              className={styles.resetBtn}
            >
              Reset
            </button>
          </div>
          
          <RegistryDataTable
            data={relationships}
            columns={listColumns}
            isLoading={loadingList}
            totalCount={totalList}
            page={filters.page}
            pageSize={filters.pageSize}
            onPageChange={paginationProps.onPageChange}
            emptyMessage="No Relationships Found. There are no active relationships matching your criteria."
          />
        </>
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

      {activeTab === "IMPACT" && (
        <>
          <div className={styles.explorerPanel}>
            <h3 className={styles.panelTitle}>1. Select Governance Asset to Evaluate</h3>
            
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
              <label htmlFor="entitySelectImpact" className={styles.label}>
                2. Choose Active {categories.find(c => c.type === selectedCategory)?.label || "Asset"}
              </label>
              {loadingEntities ? (
                <div className={styles.loadingSpinner}>
                  <span>Loading registered assets...</span>
                </div>
              ) : (
                <select
                  id="entitySelectImpact"
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

            {/* Proposed Change Type Select */}
            <div className={styles.selectorContainer} style={{ marginTop: "1rem" }}>
              <label htmlFor="changeTypeSelect" className={styles.label}>
                3. Proposed Operation / Action
              </label>
              <select
                id="changeTypeSelect"
                value={changeType}
                onChange={(e) => setChangeType(e.target.value)}
                className={styles.select}
              >
                <option value="UPDATE">UPDATE (Modify Configuration or Metadata)</option>
                <option value="SUSPEND">SUSPEND (Temporarily disable service)</option>
                <option value="REVOKE">REVOKE (Permanently decommission / delete)</option>
              </select>
            </div>
            
            <button
              onClick={fetchImpact}
              className={styles.resetBtn}
              style={{ marginTop: "1.5rem", width: "100%", padding: "0.75rem", backgroundColor: "#3b82f6", color: "#fff", fontWeight: "600", borderRadius: "0.375rem" }}
              disabled={!selectedEntityId || loadingImpact}
            >
              {loadingImpact ? "Calculating Downstream Impact..." : "Run Downstream Impact Analysis"}
            </button>
          </div>

          <div className={styles.viewerContainer}>
            {loadingImpact ? (
              <div style={{ textAlign: "center", padding: "3rem" }}>
                <Activity size={32} style={{ animation: "spin 1s linear infinite", color: "#3b82f6", marginBottom: "0.5rem" }} />
                <div style={{ color: "rgba(255,255,255,0.7)", fontWeight: 500 }}>Calculating blast radius and tracing downstream dependencies...</div>
              </div>
            ) : impactData ? (
              <div className={styles.impactDashboard}>
                {/* 1. Executive Metrics Grid */}
                <div className={styles.metricsGrid}>
                  {/* Risk Level Card */}
                  <div className={`${styles.metricCard} ${
                    impactData.impact_level === "HIGH" 
                      ? styles.metricCardHigh 
                      : impactData.impact_level === "MEDIUM" 
                        ? styles.metricCardMedium 
                        : styles.metricCardLow
                  }`}>
                    <div className={styles.metricHeader}>
                      <span className={styles.metricLabel}>Blast Radius Severity</span>
                      {impactData.impact_level === "HIGH" ? (
                        <AlertTriangle size={22} style={{ color: "#ef4444" }} />
                      ) : impactData.impact_level === "MEDIUM" ? (
                        <ShieldAlert size={22} style={{ color: "#f59e0b" }} />
                      ) : (
                        <ShieldCheck size={22} style={{ color: "#3b82f6" }} />
                      )}
                    </div>
                    <div className={styles.metricValue}>
                      {impactData.impact_level === "HIGH" ? "HIGH RISK" : impactData.impact_level === "MEDIUM" ? "MODERATE RISK" : "LOW IMPACT"}
                    </div>
                    <div className={styles.riskMeterBar}>
                      <div className={`${styles.riskMeterFill} ${
                        impactData.impact_level === "HIGH" 
                          ? styles.riskFillHigh 
                          : impactData.impact_level === "MEDIUM" 
                            ? styles.riskFillMedium 
                            : styles.riskFillLow
                      }`} style={{ width: impactData.impact_level === "HIGH" ? "90%" : impactData.impact_level === "MEDIUM" ? "55%" : "25%" }} />
                    </div>
                    <span style={{ fontSize: "0.8rem", color: "rgba(255,255,255,0.75)" }}>
                      Proposed <strong>{changeType}</strong> operation will affect downstream operational stability.
                    </span>
                  </div>

                  {/* Total Dependents at Risk Card */}
                  <div className={styles.metricCard}>
                    <div className={styles.metricHeader}>
                      <span className={styles.metricLabel}>Affected System Assets</span>
                      <Layers size={22} style={{ color: "#60a5fa" }} />
                    </div>
                    <div className={styles.metricValue}>
                      {impactData.direct_impact_count + impactData.indirect_impact_count} Assets
                    </div>
                    <div style={{ fontSize: "0.825rem", color: "rgba(255,255,255,0.6)", display: "flex", gap: "0.75rem" }}>
                      <span style={{ color: "#38bdf8" }}>● {impactData.direct_impact_count} Direct</span>
                      <span style={{ color: "#a855f7" }}>● {impactData.indirect_impact_count} Transitive Hops</span>
                    </div>
                  </div>

                  {/* Governance Recommendation Card */}
                  <div className={styles.metricCard}>
                    <div className={styles.metricHeader}>
                      <span className={styles.metricLabel}>Governance Recommendation</span>
                      <Zap size={22} style={{ color: "#eab308" }} />
                    </div>
                    <div style={{ fontSize: "0.875rem", fontWeight: 600, color: "#f8fafc" }}>
                      {changeType === "REVOKE" 
                        ? "⚠️ Decommissioning Approval Required" 
                        : changeType === "SUSPEND" 
                          ? "⏸️ Temporary Disruption Warning" 
                          : "ℹ️ Standard Metadata Update"}
                    </div>
                    <span style={{ fontSize: "0.8rem", color: "rgba(255,255,255,0.7)" }}>
                      {changeType === "REVOKE" 
                        ? "Deleting this asset breaks 1 or more active connections. Verify primary owner approval before executing." 
                        : "Review downstream dependency list below before confirming operation."}
                    </span>
                  </div>
                </div>

                {/* 2. Impact View Mode Switcher */}
                <div className={styles.impactViewToggle}>
                  <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                    <span style={{ fontSize: "0.95rem", fontWeight: 700, color: "#ffffff" }}>
                      Downstream Impact Breakdown
                    </span>
                  </div>
                  <div className={styles.viewButtons}>
                    <button
                      type="button"
                      onClick={() => setImpactViewMode("MATRIX")}
                      className={`${styles.viewBtn} ${impactViewMode === "MATRIX" ? styles.viewBtnActive : ""}`}
                    >
                      <LayoutGrid size={16} /> Risk Matrix
                    </button>
                    <button
                      type="button"
                      onClick={() => setImpactViewMode("GRAPH")}
                      className={`${styles.viewBtn} ${impactViewMode === "GRAPH" ? styles.viewBtnActive : ""}`}
                    >
                      <Share2 size={16} /> Visual Blast Radius Graph
                    </button>
                  </div>
                </div>

                {/* 3. View Render */}
                {impactViewMode === "GRAPH" ? (
                  <div style={{ minHeight: "500px", borderRadius: "10px", overflow: "hidden", border: "1px solid rgba(255,255,255,0.1)" }}>
                    <RelationshipViewer
                      entityType={mapCategoryToBackendType(selectedCategory)}
                      entityId={selectedEntityId}
                      initialDepth={5}
                      initialMode="GRAPH"
                    />
                  </div>
                ) : (
                  <div className={styles.dependentSection}>
                    {/* Direct Downstream Dependents */}
                    <div>
                      <h4 className={styles.sectionTitle}>
                        <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: "#ef4444", display: "inline-block" }}></span>
                        Direct Downstream Dependents ({impactData.direct_impacts?.length || 0})
                      </h4>
                      {impactData.direct_impacts?.length > 0 ? (
                        <div className={styles.dependentGrid}>
                          {impactData.direct_impacts.map((dep: any, idx: number) => (
                            <div key={idx} className={styles.dependentCard} style={{ borderColor: "rgba(239, 68, 68, 0.3)" }}>
                              <div className={styles.cardHeader}>
                                <div className={styles.assetBadge}>
                                  <div className={styles.assetIcon}>
                                    {dep.type.includes("AGENT") ? <Cpu size={18} /> : dep.type.includes("MODEL") ? <Brain size={18} /> : dep.type.includes("TOOL") ? <Plug size={18} /> : dep.type.includes("WORKFLOW") ? <GitBranch size={18} /> : <Database size={18} />}
                                  </div>
                                  <div>
                                    <div className={styles.assetName}>{dep.name || dep.id}</div>
                                    <div className={styles.assetType}>{dep.type}</div>
                                  </div>
                                </div>
                                <Badge variant="danger" label="Hop 1 Direct" />
                              </div>
                              <div className={styles.cardBody}>
                                <div><strong>Connection Action:</strong> {dep.relationship_type || "USES"}</div>
                                <div className={styles.ownerRow}>
                                  <Users size={13} /> Direct Asset Dependency
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p style={{ fontSize: "0.875rem", color: "rgba(255,255,255,0.45)", fontStyle: "italic" }}>No direct downstream dependents found.</p>
                      )}
                    </div>

                    {/* Indirect Downstream Dependents */}
                    <div style={{ marginTop: "1rem" }}>
                      <h4 className={styles.sectionTitle}>
                        <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: "#a855f7", display: "inline-block" }}></span>
                        Transitive Downstream Dependents ({impactData.indirect_impacts?.length || 0})
                      </h4>
                      {impactData.indirect_impacts?.length > 0 ? (
                        <div className={styles.dependentGrid}>
                          {impactData.indirect_impacts.map((dep: any, idx: number) => (
                            <div key={idx} className={styles.dependentCard} style={{ borderColor: "rgba(168, 85, 247, 0.3)" }}>
                              <div className={styles.cardHeader}>
                                <div className={styles.assetBadge}>
                                  <div className={styles.assetIcon} style={{ background: "rgba(168, 85, 247, 0.15)", color: "#c084fc" }}>
                                    {dep.type.includes("AGENT") ? <Cpu size={18} /> : dep.type.includes("MODEL") ? <Brain size={18} /> : dep.type.includes("TOOL") ? <Plug size={18} /> : dep.type.includes("WORKFLOW") ? <GitBranch size={18} /> : <Database size={18} />}
                                  </div>
                                  <div>
                                    <div className={styles.assetName}>{dep.name || dep.id}</div>
                                    <div className={styles.assetType}>{dep.type}</div>
                                  </div>
                                </div>
                                <Badge variant="neutral" label="Transitive Hop" />
                              </div>
                              <div className={styles.cardBody}>
                                <div><strong>Impact Path:</strong> Indirect Transitive Flow</div>
                                <div style={{ color: "#c084fc", fontSize: "0.8rem" }}>
                                  ● Multi-Hop Downstream Cascading Target
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p style={{ fontSize: "0.875rem", color: "rgba(255,255,255,0.45)", fontStyle: "italic" }}>No indirect downstream dependents found.</p>
                      )}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className={styles.emptyState}>
                <Network size={36} style={{ color: "rgba(255, 255, 255, 0.15)", marginBottom: "0.75rem" }} />
                <h4 className={styles.emptyTitle}>Run Downstream Impact Analysis</h4>
                <p className={styles.emptyDesc}>
                  Select a registered asset and choose a proposed action to assess downstream risk and evaluate all affected workflows, agents, and data targets.
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


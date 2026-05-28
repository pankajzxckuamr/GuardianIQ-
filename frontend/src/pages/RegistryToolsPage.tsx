/* src/pages/RegistryToolsPage.tsx */

import React, { useEffect, useState } from "react";
import { PageHeader } from "../components/common/PageHeader";
import { RegistryDataTable } from "../components/common/RegistryDataTable";
import { RegistryStatusBadge } from "../components/common/RegistryStatusBadge";
import { RiskBadge } from "../components/common/RiskBadge";
import { Button } from "../components/common/Button";
import { ToolFormModal } from "../components/registry/ToolFormModal";
import { useRegistryFilters } from "../hooks/useRegistryFilters";
import { useRegistryEntity } from "../hooks/useRegistryEntity";
import { useAuth } from "../hooks/useAuth";
import * as registryService from "../services/registry/registryService";
import styles from "./RegistryToolsPage.module.css";

export const RegistryToolsPage: React.FC = () => {
  const { currentUser } = useAuth();
  const { filters, setFilter, paginationProps } = useRegistryFilters("tool_name");

  // Debounced search
  const [searchTerm, setSearchTerm] = useState(filters.search);

  useEffect(() => {
    const delayDebounceFn = setTimeout(() => {
      setFilter("search", searchTerm);
    }, 400);
    return () => clearTimeout(delayDebounceFn);
  }, [searchTerm, setFilter]);

  // Query Tools using hooks
  const { data, isLoading, refetch } = useRegistryEntity(
    () => registryService.listTools({
      search: filters.search,
      status: filters.status,
      tool_category: filters.tool_category,
      access_mode: filters.access_mode,
      sensitivity_level: filters.sensitivity_level,
      page: filters.page,
      per_page: filters.pageSize,
      sort_by: filters.sortBy,
      sort_dir: filters.sortDir
    }),
    [
      filters.search,
      filters.status,
      filters.tool_category,
      filters.access_mode,
      filters.sensitivity_level,
      filters.page,
      filters.pageSize,
      filters.sortBy,
      filters.sortDir
    ]
  );

  // Modal Control
  const [modalOpen, setModalOpen] = useState(false);
  const [selectedToolId, setSelectedToolId] = useState<string | null>(null);

  // RBAC Permission Check
  const canRegister = currentUser?.is_superuser || 
    currentUser?.roles?.some(role => ["admin", "governance_manager", "super_admin"].includes(role.toLowerCase()));

  const handleRowClick = (row: any) => {
    setSelectedToolId(row.id);
    setModalOpen(true);
  };

  const handleRegisterClick = () => {
    setSelectedToolId(null);
    setModalOpen(true);
  };

  const handleSort = (key: string, dir: "asc" | "desc") => {
    setFilter("sortBy", key);
    setFilter("sortDir", dir);
  };

  const getAccessModeClass = (mode: string) => {
    if (mode === "ADMIN") return styles.accessModeAdmin;
    if (mode === "EXECUTE") return styles.accessModeExecute;
    if (mode === "WRITE") return styles.accessModeWrite;
    return styles.accessModeRead;
  };

  const columns = [
    { key: "tool_code", label: "Code" },
    { key: "tool_name", label: "Tool Name", sortable: true },
    { 
      key: "tool_category", 
      label: "Category",
      render: (row: any) => <span className={styles.categoryBadge}>{row.tool_category}</span>
    },
    { 
      key: "access_mode", 
      label: "Access Mode",
      render: (row: any) => (
        <span className={`${styles.accessModeBadge} ${getAccessModeClass(row.access_mode)}`}>
          {row.access_mode || "READ_ONLY"}
        </span>
      )
    },
    { 
      key: "sensitivity_level", 
      label: "Sensitivity",
      render: (row: any) => <RiskBadge level={row.sensitivity_level || "LOW"} />
    },
    { 
      key: "status", 
      label: "Status", 
      render: (row: any) => <RegistryStatusBadge status={row.status} /> 
    }
  ];

  return (
    <div className={styles.page}>
      <PageHeader
        title="Tools &amp; Connectors Registry"
        description="Govern corporate integrations, database connectors, ERP hooks, and execution access rights"
        actions={
          canRegister && (
            <Button variant="primary" onClick={handleRegisterClick}>
              + Register Tool
            </Button>
          )
        }
      />

      {/* Filter and Search Bar */}
      <div className={styles.filterBar}>
        <div className={styles.searchGroup}>
          <input
            type="text"
            placeholder="Search tools..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className={styles.searchInput}
          />
        </div>

        <div className={styles.filtersGroup}>
          {/* Status Select */}
          <select
            value={filters.status}
            onChange={(e) => setFilter("status", e.target.value)}
            className={styles.filterSelect}
          >
            <option value="">All Statuses</option>
            <option value="DRAFT">DRAFT</option>
            <option value="ACTIVE">ACTIVE</option>
            <option value="INACTIVE">INACTIVE</option>
            <option value="SUSPENDED">SUSPENDED</option>
            <option value="RETIRED">RETIRED</option>
            <option value="ARCHIVED">ARCHIVED</option>
          </select>

          {/* Category Select */}
          <select
            value={filters.tool_category || ""}
            onChange={(e) => setFilter("tool_category", e.target.value)}
            className={styles.filterSelect}
          >
            <option value="">All Categories</option>
            <option value="ERP">ERP</option>
            <option value="CRM">CRM</option>
            <option value="EMAIL">EMAIL</option>
            <option value="TICKETING">TICKETING</option>
            <option value="DATABASE">DATABASE</option>
            <option value="LLM">LLM</option>
            <option value="FILE">FILE</option>
            <option value="WEBHOOK">WEBHOOK</option>
          </select>

          {/* Access Mode Select */}
          <select
            value={filters.access_mode || ""}
            onChange={(e) => setFilter("access_mode", e.target.value)}
            className={styles.filterSelect}
          >
            <option value="">All Access Modes</option>
            <option value="READ_ONLY">READ_ONLY</option>
            <option value="WRITE">WRITE</option>
            <option value="EXECUTE">EXECUTE</option>
            <option value="ADMIN">ADMIN</option>
          </select>

          {/* Sensitivity Select */}
          <select
            value={filters.sensitivity_level || ""}
            onChange={(e) => setFilter("sensitivity_level", e.target.value)}
            className={styles.filterSelect}
          >
            <option value="">All Sensitivities</option>
            <option value="LOW">LOW</option>
            <option value="MEDIUM">MEDIUM</option>
            <option value="HIGH">HIGH</option>
            <option value="CRITICAL">CRITICAL</option>
          </select>
        </div>
      </div>

      {/* Main Table */}
      <div className={styles.tableContainer}>
        <RegistryDataTable
          columns={columns}
          data={data?.items || []}
          isLoading={isLoading}
          totalCount={data?.total || 0}
          page={paginationProps.page}
          pageSize={paginationProps.pageSize}
          onPageChange={paginationProps.onPageChange}
          onSort={handleSort}
          sortBy={filters.sortBy}
          sortDir={filters.sortDir}
          onRowClick={handleRowClick}
          emptyMessage="No registry tools found matching the search criteria."
        />
      </div>

      {/* Form Modal */}
      <ToolFormModal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        toolId={selectedToolId}
        onSuccess={refetch}
      />
    </div>
  );
};

export default RegistryToolsPage;

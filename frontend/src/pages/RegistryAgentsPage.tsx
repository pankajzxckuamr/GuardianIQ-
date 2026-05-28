/* src/pages/RegistryAgentsPage.tsx */

import React, { useEffect, useState } from "react";
import { PageHeader } from "../components/common/PageHeader";
import { RegistryDataTable } from "../components/common/RegistryDataTable";
import { RegistryStatusBadge } from "../components/common/RegistryStatusBadge";
import { RiskBadge } from "../components/common/RiskBadge";
import { Button } from "../components/common/Button";
import { AgentFormModal } from "../components/registry/AgentFormModal";
import { useRegistryFilters } from "../hooks/useRegistryFilters";
import { useRegistryEntity } from "../hooks/useRegistryEntity";
import { useAuth } from "../hooks/useAuth";
import * as registryService from "../services/registry/registryService";
import styles from "./RegistryAgentsPage.module.css";

export const RegistryAgentsPage: React.FC = () => {
  const { currentUser } = useAuth();
  const { filters, setFilter, paginationProps } = useRegistryFilters("agent_name");

  // Debounced search query
  const [searchTerm, setSearchTerm] = useState(filters.search);

  useEffect(() => {
    const delayDebounceFn = setTimeout(() => {
      setFilter("search", searchTerm);
    }, 400);
    return () => clearTimeout(delayDebounceFn);
  }, [searchTerm, setFilter]);

  // Query API using hooks
  const { data, isLoading, refetch } = useRegistryEntity(
    () => registryService.listAgents({
      search: filters.search,
      status: filters.status,
      agent_type: filters.agent_type,
      execution_mode: filters.execution_mode,
      page: filters.page,
      per_page: filters.pageSize,
      sort_by: filters.sortBy,
      sort_dir: filters.sortDir
    }),
    [
      filters.search,
      filters.status,
      filters.agent_type,
      filters.execution_mode,
      filters.page,
      filters.pageSize,
      filters.sortBy,
      filters.sortDir
    ]
  );

  // Form Modal control
  const [modalOpen, setModalOpen] = useState(false);
  const [selectedAgentId, setSelectedAgentId] = useState<string | null>(null);

  // Check RBAC permission (admin or governance_manager)
  const canRegister = currentUser?.is_superuser || 
    currentUser?.roles?.some(role => ["admin", "governance_manager", "super_admin"].includes(role.toLowerCase()));

  const handleRowClick = (row: any) => {
    setSelectedAgentId(row.id);
    setModalOpen(true);
  };

  const handleRegisterClick = () => {
    setSelectedAgentId(null);
    setModalOpen(true);
  };

  const handleSort = (key: string, dir: "asc" | "desc") => {
    setFilter("sortBy", key);
    setFilter("sortDir", dir);
  };

  const getExecutionModeClass = (mode: string) => {
    if (mode === "BLOCKED") return styles.executionModeBlocked;
    if (mode === "APPROVAL_REQUIRED") return styles.executionModeApproval;
    return styles.executionModeOther;
  };

  const columns = [
    { key: "agent_code", label: "Code" },
    { key: "agent_name", label: "Agent Name", sortable: true },
    { key: "agent_type", label: "Type" },
    { 
      key: "execution_mode", 
      label: "Execution Mode",
      render: (row: any) => (
        <span className={`${styles.modeBadge} ${getExecutionModeClass(row.execution_mode)}`}>
          {row.execution_mode}
        </span>
      )
    },
    { 
      key: "risk_level", 
      label: "Risk", 
      render: (row: any) => <RiskBadge level={row.risk_level} /> 
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
        title="AI Agent Registry"
        description="Govern autonomous agents, secure authorization scopes, and configure operational modes"
        actions={
          canRegister && (
            <Button variant="primary" onClick={handleRegisterClick}>
              + Register Agent
            </Button>
          )
        }
      />

      {/* Filter and Search options */}
      <div className={styles.filterBar}>
        <div className={styles.searchGroup}>
          <input
            type="text"
            placeholder="Search agents..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className={styles.searchInput}
          />
        </div>

        <div className={styles.filtersGroup}>
          {/* Status filter */}
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

          {/* Agent Type Filter */}
          <select
            value={filters.agent_type || ""}
            onChange={(e) => setFilter("agent_type", e.target.value)}
            className={styles.filterSelect}
          >
            <option value="">All Types</option>
            <option value="RECOMMENDATION">RECOMMENDATION</option>
            <option value="TRIAGE">TRIAGE</option>
            <option value="EXTRACTION">EXTRACTION</option>
            <option value="EXECUTION">EXECUTION</option>
            <option value="MONITORING">MONITORING</option>
          </select>

          {/* Execution Mode Filter */}
          <select
            value={filters.execution_mode || ""}
            onChange={(e) => setFilter("execution_mode", e.target.value)}
            className={styles.filterSelect}
          >
            <option value="">All Modes</option>
            <option value="READ_ONLY">READ_ONLY</option>
            <option value="RECOMMEND_ONLY">RECOMMEND_ONLY</option>
            <option value="APPROVAL_REQUIRED">APPROVAL_REQUIRED</option>
            <option value="LIMITED_EXECUTION">LIMITED_EXECUTION</option>
            <option value="BLOCKED">BLOCKED</option>
          </select>
        </div>
      </div>

      {/* Data Table */}
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
          emptyMessage="No AI Agents found matching the search criteria."
        />
      </div>

      {/* Agent Modal */}
      <AgentFormModal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        agentId={selectedAgentId}
        onSuccess={refetch}
      />
    </div>
  );
};

export default RegistryAgentsPage;

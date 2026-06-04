/* src/pages/RegistryModelsPage.tsx */

import React, { useEffect, useState } from "react";
import { PageHeader } from "../components/common/PageHeader";
import { RegistryDataTable } from "../components/common/RegistryDataTable";
import { RegistryStatusBadge } from "../components/common/RegistryStatusBadge";
import { RiskBadge } from "../components/common/RiskBadge";
import { Button } from "../components/common/Button";
import { ModelFormModal } from "../components/registry/ModelFormModal";
import { useRegistryFilters } from "../hooks/useRegistryFilters";
import { useRegistryEntity } from "../hooks/useRegistryEntity";
import { useAuth } from "../hooks/useAuth";
import * as registryService from "../services/registry/registryService";
import { useSearchParams } from "react-router-dom";
import styles from "./RegistryModelsPage.module.css";

const formatDate = (dateStr: string) => {
  if (!dateStr) return "-";
  try {
    const d = new Date(dateStr);
    return d.toLocaleDateString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric"
    });
  } catch {
    return dateStr;
  }
};

const cleanOwnerName = (name: string | undefined | null) => {
  if (!name) return "-";
  if (name.includes("(")) {
    return name.split("(")[0].trim();
  }
  if (name.includes("@")) {
    return name.split("@")[0].trim();
  }
  return name.trim();
};

export const RegistryModelsPage: React.FC = () => {
  const { currentUser } = useAuth();
  const { filters, setFilter, paginationProps } = useRegistryFilters("model_name");
  const [searchParams, setSearchParams] = useSearchParams();
  const viewId = searchParams.get("view");

  // Set document title
  useEffect(() => {
    document.title = "AI Models — GuardianIQ Registry";
  }, []);

  // Debounced search input state
  const [searchTerm, setSearchTerm] = useState(filters.search);

  useEffect(() => {
    const delayDebounceFn = setTimeout(() => {
      setFilter("search", searchTerm);
    }, 400);
    return () => clearTimeout(delayDebounceFn);
  }, [searchTerm, setFilter]);

  // Fetch model list dynamically
  const { data, isLoading, refetch } = useRegistryEntity(
    () => registryService.listModels({
      search: filters.search,
      status: filters.status,
      model_type: filters.model_type,
      risk_level: filters.risk_level,
      page: filters.page,
      per_page: filters.pageSize,
      sort_by: filters.sortBy,
      sort_dir: filters.sortDir
    }),
    [
      filters.search,
      filters.status,
      filters.model_type,
      filters.risk_level,
      filters.page,
      filters.pageSize,
      filters.sortBy,
      filters.sortDir
    ]
  );

  // Modal Control
  const [modalOpen, setModalOpen] = useState(false);
  const [selectedModelId, setSelectedModelId] = useState<string | null>(null);

  useEffect(() => {
    if (viewId) {
      setSelectedModelId(viewId);
      setModalOpen(true);
    }
  }, [viewId]);

  const handleClose = () => {
    setModalOpen(false);
    if (searchParams.has("view")) {
      const newParams = new URLSearchParams(searchParams);
      newParams.delete("view");
      setSearchParams(newParams);
    }
  };

  // Check RBAC permissions for register button
  const canRegister = currentUser?.is_superuser || 
    currentUser?.roles?.some(role => ["admin", "governance_manager", "super_admin"].includes(role.toLowerCase()));

  const handleRowClick = (row: any) => {
    setSelectedModelId(row.id);
    setModalOpen(true);
  };

  const handleRegisterClick = () => {
    setSelectedModelId(null);
    setModalOpen(true);
  };

  const handleSort = (key: string, dir: "asc" | "desc") => {
    setFilter("sortBy", key);
    setFilter("sortDir", dir);
  };

  const columns = [
    { key: "model_code", label: "Code" },
    { key: "model_name", label: "Model Name", sortable: true },
    { key: "provider_name", label: "Provider", render: (row: any) => row.provider_name || "-" },
    { key: "owner_name", label: "Owner", render: (row: any) => cleanOwnerName(row.owner_name) },
    { 
      key: "model_type", 
      label: "Type", 
      render: (row: any) => <span className={styles.typeBadge}>{row.model_type}</span> 
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
    },
    { 
      key: "created_at", 
      label: "Created", 
      sortable: true, 
      render: (row: any) => formatDate(row.created_at) 
    }
  ];

  return (
    <div className={styles.page}>
      <div className={styles.breadcrumb}>Registry &gt; AI Models</div>
      <PageHeader
        title="AI Model Registry"
        description="Govern AI models, standard classifications, and system risk ratings"
        actions={
          canRegister && (
            <Button variant="primary" onClick={handleRegisterClick}>
              + Register Model
            </Button>
          )
        }
      />

      {/* Registry Filter and Search Options */}
      <div className={styles.filterBar}>
        <div className={styles.searchGroup}>
          <input
            type="text"
            placeholder="Search models..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className={styles.searchInput}
          />
        </div>

        <div className={styles.filtersGroup}>
          {/* Status Dropdown */}
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

          {/* Model Type Dropdown */}
          <select
            value={filters.model_type || ""}
            onChange={(e) => setFilter("model_type", e.target.value)}
            className={styles.filterSelect}
          >
            <option value="">All Types</option>
            <option value="LLM">LLM</option>
            <option value="ML">ML</option>
            <option value="CLASSIFIER">CLASSIFIER</option>
            <option value="EMBEDDING">EMBEDDING</option>
            <option value="RULE_BASED">RULE_BASED</option>
            <option value="FORECASTING">FORECASTING</option>
            <option value="OPTIMIZATION">OPTIMIZATION</option>
          </select>

          {/* Risk Level Dropdown */}
          <select
            value={filters.risk_level || ""}
            onChange={(e) => setFilter("risk_level", e.target.value)}
            className={styles.filterSelect}
          >
            <option value="">All Risks</option>
            <option value="LOW">LOW</option>
            <option value="MEDIUM">MEDIUM</option>
            <option value="HIGH">HIGH</option>
            <option value="CRITICAL">CRITICAL</option>
          </select>
        </div>
      </div>

      {/* Main DataTable list */}
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
          emptyMessage="No AI Models found matching the search criteria."
        />
      </div>

      {/* Interactive Form Edit/Create Modal */}
      <ModelFormModal
        isOpen={modalOpen}
        onClose={handleClose}
        modelId={selectedModelId}
        onSuccess={refetch}
      />
    </div>
  );
};

export default RegistryModelsPage;

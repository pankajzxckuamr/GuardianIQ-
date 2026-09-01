/* src/pages/RegistryDataSourcesPage.tsx */

import React, { useEffect, useState } from "react";
import { PageHeader } from "../components/common/PageHeader";
import { RegistryDataTable } from "../components/common/RegistryDataTable";
import { RegistryStatusBadge } from "../components/common/RegistryStatusBadge";
import { Button } from "../components/common/Button";
import { DataSourceFormModal } from "../components/registry/DataSourceFormModal";
import { useRegistryFilters } from "../hooks/useRegistryFilters";
import { useRegistryEntity } from "../hooks/useRegistryEntity";
import { useAuth } from "../hooks/useAuth";
import * as registryService from "../services/registry/registryService";
import { Check } from "lucide-react";
import { useSearchParams } from "react-router-dom";
import styles from "./RegistryDataSourcesPage.module.css";

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

export const RegistryDataSourcesPage: React.FC = () => {
  const { currentUser } = useAuth();
  const { filters, setFilter, paginationProps } = useRegistryFilters("created_at", 10, "desc");
  const [searchParams, setSearchParams] = useSearchParams();
  const viewId = searchParams.get("view");

  // Set document title
  useEffect(() => {
    document.title = "Data Sources — GuardianIQ Registry";
  }, []);

  // Debounced search input state
  const [searchTerm, setSearchTerm] = useState(filters.search);

  useEffect(() => {
    const delayDebounceFn = setTimeout(() => {
      setFilter("search", searchTerm);
    }, 400);
    return () => clearTimeout(delayDebounceFn);
  }, [searchTerm, setFilter]);

  // Handle local query param for contains_pii mapping (All/Yes/No)
  const [containsPiiFilter, setContainsPiiFilter] = useState<string>("");

  const handlePiiFilterChange = (val: string) => {
    setContainsPiiFilter(val);
    if (val === "yes") {
      setFilter("contains_pii", true);
    } else if (val === "no") {
      setFilter("contains_pii", false);
    } else {
      setFilter("contains_pii", undefined);
    }
  };

  // Fetch data sources dynamically
  const { data, isLoading, refetch } = useRegistryEntity(
    () => registryService.listDataSources({
      search: filters.search,
      status: filters.status,
      source_type: filters.source_type || undefined,
      classification: filters.classification || undefined,
      sensitivity_level: filters.sensitivity_level || undefined,
      contains_pii: filters.contains_pii,
      page: filters.page,
      per_page: filters.pageSize,
      sort_by: filters.sortBy,
      sort_dir: filters.sortDir
    }),
    [
      filters.search,
      filters.status,
      filters.source_type,
      filters.classification,
      filters.sensitivity_level,
      filters.contains_pii,
      filters.page,
      filters.pageSize,
      filters.sortBy,
      filters.sortDir
    ]
  );

  // Modal Control
  const [modalOpen, setModalOpen] = useState(false);
  const [selectedSourceId, setSelectedSourceId] = useState<string | null>(null);

  useEffect(() => {
    if (viewId) {
      setSelectedSourceId(viewId);
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
    setSelectedSourceId(row.id);
    setModalOpen(true);
  };

  const handleRegisterClick = () => {
    setSelectedSourceId(null);
    setModalOpen(true);
  };

  const handleSort = (key: string, dir: "asc" | "desc") => {
    setFilter("sortBy", key);
    setFilter("sortDir", dir);
  };

  const columns = [
    { key: "source_code", label: "Code" },
    { key: "source_name", label: "Source Name", sortable: true },
    { 
      key: "source_type", 
      label: "Type", 
      render: (row: any) => <span className={styles.typeBadge}>{row.source_type}</span> 
    },
    { 
      key: "classification", 
      label: "Classification", 
      render: (row: any) => (
        <span className={`${styles.classificationBadge} ${styles[String(row.classification).toLowerCase()] || ""}`}>
          {row.classification}
        </span>
      ) 
    },
    { 
      key: "contains_pii", 
      label: "Contains PII", 
      render: (row: any) => (
        row.contains_pii ? (
          <span className={styles.piiYes}>
            <Check size={14} strokeWidth={3} />
          </span>
        ) : (
          <span className={styles.piiNo}>—</span>
        )
      ) 
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
      <div className={styles.breadcrumb}>Registry &gt; Data Sources</div>
      <PageHeader
        title="Secure Data Sources Registry"
        description="Govern corporate data structures, warehouse systems, regions, and PII status."
        actions={
          canRegister && (
            <Button variant="primary" onClick={handleRegisterClick}>
              + Register Data Source
            </Button>
          )
        }
      />

      {/* Filter Bar */}
      <div className={styles.filterBar}>
        <div className={styles.searchGroup}>
          <input
            type="text"
            placeholder="Search data sources..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className={styles.searchInput}
          />
        </div>

        <div className={styles.filtersGroup}>
          {/* Source Type Dropdown */}
          <select
            value={filters.source_type || ""}
            onChange={(e) => setFilter("source_type", e.target.value)}
            className={styles.filterSelect}
          >
            <option value="">All Types</option>
            <option value="DATABASE">DATABASE</option>
            <option value="API">API</option>
            <option value="FILE">FILE</option>
            <option value="CRM">CRM</option>
            <option value="ERP">ERP</option>
            <option value="DATA_LAKE">DATA LAKE</option>
            <option value="EMAIL">EMAIL</option>
            <option value="WEBFORM">WEBFORM</option>
          </select>

          {/* Classification Dropdown */}
          <select
            value={filters.classification || ""}
            onChange={(e) => setFilter("classification", e.target.value)}
            className={styles.filterSelect}
          >
            <option value="">All Classifications</option>
            <option value="PUBLIC">PUBLIC</option>
            <option value="INTERNAL">INTERNAL</option>
            <option value="CONFIDENTIAL">CONFIDENTIAL</option>
            <option value="RESTRICTED">RESTRICTED</option>
          </select>

          {/* Sensitivity Level Dropdown */}
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

          {/* Contains PII Selector */}
          <select
            value={containsPiiFilter}
            onChange={(e) => handlePiiFilterChange(e.target.value)}
            className={styles.filterSelect}
          >
            <option value="">All PII States</option>
            <option value="yes">Contains PII</option>
            <option value="no">No PII</option>
          </select>

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
          emptyMessage="No data sources found matching the search criteria."
        />
      </div>

      {/* Interactive Form Edit/Create Modal */}
      <DataSourceFormModal
        isOpen={modalOpen}
        onClose={handleClose}
        sourceId={selectedSourceId}
        onSuccess={refetch}
      />
    </div>
  );
};

export default RegistryDataSourcesPage;

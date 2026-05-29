/* src/pages/RegistryWorkflowsPage.tsx */

import React, { useEffect, useState } from "react";
import { PageHeader } from "../components/common/PageHeader";
import { RegistryDataTable } from "../components/common/RegistryDataTable";
import { RegistryStatusBadge } from "../components/common/RegistryStatusBadge";
import { RiskBadge } from "../components/common/RiskBadge";
import { Button } from "../components/common/Button";
import { WorkflowFormModal } from "../components/registry/WorkflowFormModal";
import { useRegistryFilters } from "../hooks/useRegistryFilters";
import { useRegistryEntity } from "../hooks/useRegistryEntity";
import { useAuth } from "../hooks/useAuth";
import * as registryService from "../services/registry/registryService";
import styles from "./RegistryWorkflowsPage.module.css";

export const RegistryWorkflowsPage: React.FC = () => {
  const { currentUser } = useAuth();
  const { filters, setFilter, paginationProps } = useRegistryFilters("workflow_name");

  // Set document title
  useEffect(() => {
    document.title = "Workflows — GuardianIQ Registry";
  }, []);

  // Debounced search
  const [searchTerm, setSearchTerm] = useState(filters.search);
  const [departmentsMap, setDepartmentsMap] = useState<Record<string, string>>({});

  useEffect(() => {
    const delayDebounceFn = setTimeout(() => {
      setFilter("search", searchTerm);
    }, 400);
    return () => clearTimeout(delayDebounceFn);
  }, [searchTerm, setFilter]);

  // Load department lookups to resolve department names
  useEffect(() => {
    async function loadDepts() {
      try {
        const res = await registryService.getDepartmentsLookup();
        if (res.data) {
          const mapping: Record<string, string> = {};
          res.data.forEach((d) => {
            mapping[d.id] = d.department_name;
          });
          setDepartmentsMap(mapping);
        }
      } catch (err) {
        console.error("Failed to load departments lookup:", err);
      }
    }
    loadDepts();
  }, []);

  // Fetch Workflows dynamic list
  const { data, isLoading, refetch } = useRegistryEntity(
    () => {
      const approvalParam =
        filters.approval_required === "yes"
          ? true
          : filters.approval_required === "no"
          ? false
          : undefined;

      return registryService.listWorkflows({
        search: filters.search,
        status: filters.status,
        workflow_type: filters.workflow_type,
        business_criticality: filters.business_criticality,
        approval_required: approvalParam,
        page: filters.page,
        per_page: filters.pageSize,
        sort_by: filters.sortBy,
        sort_dir: filters.sortDir
      });
    },
    [
      filters.search,
      filters.status,
      filters.workflow_type,
      filters.business_criticality,
      filters.approval_required,
      filters.page,
      filters.pageSize,
      filters.sortBy,
      filters.sortDir
    ]
  );

  // Modal control
  const [modalOpen, setModalOpen] = useState(false);
  const [selectedWorkflowId, setSelectedWorkflowId] = useState<string | null>(null);

  // RBAC Permission Check
  const canRegister = currentUser?.is_superuser || 
    currentUser?.roles?.some(role => ["admin", "governance_manager", "super_admin"].includes(role.toLowerCase()));

  const handleRowClick = (row: any) => {
    setSelectedWorkflowId(row.id);
    setModalOpen(true);
  };

  const handleRegisterClick = () => {
    setSelectedWorkflowId(null);
    setModalOpen(true);
  };

  const handleSort = (key: string, dir: "asc" | "desc") => {
    setFilter("sortBy", key);
    setFilter("sortDir", dir);
  };

  const columns = [
    { key: "workflow_code", label: "Code" },
    { key: "workflow_name", label: "Workflow Name", sortable: true },
    { 
      key: "workflow_type", 
      label: "Type",
      render: (row: any) => <span className={styles.typeBadge}>{row.workflow_type}</span>
    },
    { 
      key: "department_id", 
      label: "Department",
      render: (row: any) => {
        return row.department_name || row.department?.department_name || departmentsMap[row.department_id] || "—";
      }
    },
    { 
      key: "business_criticality", 
      label: "Criticality",
      render: (row: any) => <RiskBadge level={row.business_criticality || "LOW"} />
    },
    { 
      key: "approval_required", 
      label: "Approval Required",
      render: (row: any) => (
        <span className={row.approval_required ? styles.approvalRequiredYes : styles.approvalRequiredNo}>
          {row.approval_required ? "✓ Required" : "—"}
        </span>
      )
    },
    { 
      key: "status", 
      label: "Status",
      render: (row: any) => <RegistryStatusBadge status={row.status} />
    }
  ];

  return (
    <div className={styles.page}>
      <div className={styles.breadcrumb}>Registry &gt; Workflows</div>
      <PageHeader
        title="Workflows &amp; Pipelines Registry"
        description="Govern corporate decision tracks, data processing, and validation procedures"
        actions={
          canRegister && (
            <Button variant="primary" onClick={handleRegisterClick}>
              + Register Workflow
            </Button>
          )
        }
      />

      {/* Filters bar */}
      <div className={styles.filterBar}>
        <div className={styles.searchGroup}>
          <input
            type="text"
            placeholder="Search workflows..."
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

          {/* Workflow Type filter */}
          <select
            value={filters.workflow_type || ""}
            onChange={(e) => setFilter("workflow_type", e.target.value)}
            className={styles.filterSelect}
          >
            <option value="">All Types</option>
            <option value="ENQUIRY">ENQUIRY</option>
            <option value="APPROVAL">APPROVAL</option>
            <option value="CUSTOMER_SIGNAL">CUSTOMER_SIGNAL</option>
            <option value="RISK_REVIEW">RISK_REVIEW</option>
            <option value="OPERATIONAL_ACTION">OPERATIONAL_ACTION</option>
          </select>

          {/* Business Criticality filter */}
          <select
            value={filters.business_criticality || ""}
            onChange={(e) => setFilter("business_criticality", e.target.value)}
            className={styles.filterSelect}
          >
            <option value="">All Criticalities</option>
            <option value="LOW">LOW</option>
            <option value="MEDIUM">MEDIUM</option>
            <option value="HIGH">HIGH</option>
            <option value="CRITICAL">CRITICAL</option>
          </select>

          {/* Approval Required filter */}
          <select
            value={filters.approval_required || ""}
            onChange={(e) => setFilter("approval_required", e.target.value)}
            className={styles.filterSelect}
          >
            <option value="">All Approvals</option>
            <option value="yes">Requires Approval</option>
            <option value="no">No Approval</option>
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
          emptyMessage="No registry workflows found matching the search criteria."
        />
      </div>

      {/* Form Modal */}
      <WorkflowFormModal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        workflowId={selectedWorkflowId}
        onSuccess={refetch}
      />
    </div>
  );
};

export default RegistryWorkflowsPage;

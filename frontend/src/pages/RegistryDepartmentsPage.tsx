/* src/pages/RegistryDepartmentsPage.tsx */

import React, { useEffect, useState } from "react";
import { PageHeader } from "../components/common/PageHeader";
import { RegistryDataTable } from "../components/common/RegistryDataTable";
import { RegistryStatusBadge } from "../components/common/RegistryStatusBadge";
import { Button } from "../components/common/Button";
import { DepartmentFormModal } from "../components/registry/DepartmentFormModal";
import { useRegistryFilters } from "../hooks/useRegistryFilters";
import { useRegistryEntity } from "../hooks/useRegistryEntity";
import { useAuth } from "../hooks/useAuth";
import * as registryService from "../services/registry/registryService";
import { useSearchParams } from "react-router-dom";
import styles from "./RegistryDepartmentsPage.module.css";

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

export const RegistryDepartmentsPage: React.FC = () => {
  const { currentUser } = useAuth();
  const { filters, setFilter, paginationProps } = useRegistryFilters("department_name");
  const [searchParams, setSearchParams] = useSearchParams();
  const viewId = searchParams.get("view");

  // Set document title
  useEffect(() => {
    document.title = "Departments — GuardianIQ Registry";
  }, []);

  // Debounced search input state
  const [searchTerm, setSearchTerm] = useState(filters.search);

  useEffect(() => {
    const delayDebounceFn = setTimeout(() => {
      setFilter("search", searchTerm);
    }, 400);
    return () => clearTimeout(delayDebounceFn);
  }, [searchTerm, setFilter]);

  // Fetch departments dynamically
  const { data, isLoading, refetch } = useRegistryEntity(
    () => registryService.listDepartments({
      search: filters.search,
      status: filters.status,
      page: filters.page,
      per_page: filters.pageSize,
      sort_by: filters.sortBy,
      sort_dir: filters.sortDir
    }),
    [
      filters.search,
      filters.status,
      filters.page,
      filters.pageSize,
      filters.sortBy,
      filters.sortDir
    ]
  );

  // Parent department list to resolve parent names
  const [departmentsList, setDepartmentsList] = useState<any[]>([]);

  useEffect(() => {
    async function loadLookup() {
      try {
        const res = await registryService.getDepartmentsLookup();
        if (res.data) setDepartmentsList(res.data);
      } catch (err) {
        console.error("Failed to load departments lookup:", err);
      }
    }
    loadLookup();
  }, [data]);

  const getParentName = (parentId?: string) => {
    if (!parentId) return "—";
    const dept = departmentsList.find(d => d.id === parentId);
    return dept ? dept.department_name : "—";
  };

  // Modal Control
  const [modalOpen, setModalOpen] = useState(false);
  const [selectedDeptId, setSelectedDeptId] = useState<string | null>(null);

  useEffect(() => {
    if (viewId) {
      setSelectedDeptId(viewId);
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
    setSelectedDeptId(row.id);
    setModalOpen(true);
  };

  const handleRegisterClick = () => {
    setSelectedDeptId(null);
    setModalOpen(true);
  };

  const handleSort = (key: string, dir: "asc" | "desc") => {
    setFilter("sortBy", key);
    setFilter("sortDir", dir);
  };

  const columns = [
    { key: "department_code", label: "Code" },
    { key: "department_name", label: "Department Name", sortable: true },
    { 
      key: "parent_department_id", 
      label: "Parent Department", 
      render: (row: any) => <span>{getParentName(row.parent_department_id)}</span> 
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
      <div className={styles.breadcrumb}>Registry &gt; Departments</div>
      <PageHeader
        title="Department Registry"
        description="Govern corporate structures, department codes, and governance owners."
        actions={
          canRegister && (
            <Button variant="primary" onClick={handleRegisterClick}>
              + Register Department
            </Button>
          )
        }
      />

      {/* Filter and Search Options */}
      <div className={styles.filterBar}>
        <div className={styles.searchGroup}>
          <input
            type="text"
            placeholder="Search departments..."
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
          emptyMessage="No departments found matching the search criteria."
        />
      </div>

      {/* Interactive Form Edit/Create Modal */}
      <DepartmentFormModal
        isOpen={modalOpen}
        onClose={handleClose}
        deptId={selectedDeptId}
        onSuccess={refetch}
      />
    </div>
  );
};

export default RegistryDepartmentsPage;

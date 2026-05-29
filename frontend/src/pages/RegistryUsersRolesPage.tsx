/* src/pages/RegistryUsersRolesPage.tsx */

import React, { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { PageHeader } from "../components/common/PageHeader";
import { RegistryDataTable } from "../components/common/RegistryDataTable";
import { RegistryStatusBadge } from "../components/common/RegistryStatusBadge";
import { Button } from "../components/common/Button";
import { UserFormModal } from "../components/registry/UserFormModal";
import { RoleFormModal } from "../components/registry/RoleFormModal";
import { useRegistryFilters } from "../hooks/useRegistryFilters";
import { useRegistryEntity } from "../hooks/useRegistryEntity";
import { useAuth } from "../hooks/useAuth";
import * as registryService from "../services/registry/registryService";
import styles from "./RegistryUsersRolesPage.module.css";

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

export const RegistryUsersRolesPage: React.FC = () => {
  const { currentUser } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const activeTab = searchParams.get("tab") === "roles" ? "roles" : "users";

  // Set document title dynamically based on active tab
  useEffect(() => {
    document.title = activeTab === "users" 
      ? "Users Registry — GuardianIQ Registry"
      : "Roles Registry — GuardianIQ Registry";
  }, [activeTab]);

  // Tab switcher
  const handleTabChange = (tab: "users" | "roles") => {
    setSearchParams({ tab });
  };

  // Filter States for Users tab
  const { 
    filters: userFilters, 
    setFilter: setUserFilter, 
    paginationProps: userPaginationProps 
  } = useRegistryFilters("full_name");

  const [userSearchTerm, setUserSearchTerm] = useState(userFilters.search);

  useEffect(() => {
    const delayDebounceFn = setTimeout(() => {
      setUserFilter("search", userSearchTerm);
    }, 400);
    return () => clearTimeout(delayDebounceFn);
  }, [userSearchTerm, setUserFilter]);

  // Filter States for Roles tab
  const { 
    filters: roleFilters, 
    setFilter: setRoleFilter, 
    paginationProps: rolePaginationProps 
  } = useRegistryFilters("role_name");

  const [roleSearchTerm, setRoleSearchTerm] = useState(roleFilters.search);

  useEffect(() => {
    const delayDebounceFn = setTimeout(() => {
      setRoleFilter("search", roleSearchTerm);
    }, 400);
    return () => clearTimeout(delayDebounceFn);
  }, [roleSearchTerm, setRoleFilter]);

  // Lookups data
  const [departments, setDepartments] = useState<any[]>([]);
  const [rolesList, setRolesList] = useState<any[]>([]);

  useEffect(() => {
    async function loadLookups() {
      try {
        const [deptsRes, rolesRes] = await Promise.all([
          registryService.getDepartmentsLookup(),
          registryService.getRolesLookup()
        ]);
        if (deptsRes.data) setDepartments(deptsRes.data);
        if (rolesRes.data) setRolesList(rolesRes.data);
      } catch (err) {
        console.error("Failed to load lookups in users page:", err);
      }
    }
    loadLookups();
  }, []);

  // Fetch Users data
  const { data: usersData, isLoading: usersLoading, refetch: refetchUsers } = useRegistryEntity(
    () => registryService.listUsers({
      search: userFilters.search,
      status: userFilters.status,
      department_id: userFilters.department_id || undefined,
      role_id: userFilters.role_id || undefined,
      page: userFilters.page,
      per_page: userFilters.pageSize,
      sort_by: userFilters.sortBy,
      sort_dir: userFilters.sortDir
    }),
    [
      userFilters.search,
      userFilters.status,
      userFilters.department_id,
      userFilters.role_id,
      userFilters.page,
      userFilters.pageSize,
      userFilters.sortBy,
      userFilters.sortDir
    ]
  );

  // Fetch Roles data
  const { data: rolesData, isLoading: rolesLoading, refetch: refetchRoles } = useRegistryEntity(
    () => registryService.listRoles({
      search: roleFilters.search,
      role_type: roleFilters.role_type || undefined,
      status: roleFilters.status,
      page: roleFilters.page,
      per_page: roleFilters.pageSize,
      sort_by: roleFilters.sortBy,
      sort_dir: roleFilters.sortDir
    }),
    [
      roleFilters.search,
      roleFilters.role_type,
      roleFilters.status,
      roleFilters.page,
      roleFilters.pageSize,
      roleFilters.sortBy,
      roleFilters.sortDir
    ]
  );

  // Helper selectors
  const getDepartmentName = (deptId?: string) => {
    if (!deptId) return "—";
    const dept = departments.find(d => d.id === deptId);
    return dept ? dept.department_name : "—";
  };

  const getRoleName = (roleId?: string) => {
    if (!roleId) return "—";
    const r = rolesList.find(role => role.id === roleId);
    return r ? r.role_name : "—";
  };

  // Modal Control
  const [userModalOpen, setUserModalOpen] = useState(false);
  const [selectedUserId, setSelectedUserId] = useState<string | null>(null);

  const [roleModalOpen, setRoleModalOpen] = useState(false);
  const [selectedRoleId, setSelectedRoleId] = useState<string | null>(null);

  // Check RBAC permissions for register button
  const canRegister = currentUser?.is_superuser || 
    currentUser?.roles?.some(role => ["admin", "governance_manager", "super_admin"].includes(role.toLowerCase()));

  const handleUserRowClick = (row: any) => {
    setSelectedUserId(row.id);
    setUserModalOpen(true);
  };

  const handleRegisterUserClick = () => {
    setSelectedUserId(null);
    setUserModalOpen(true);
  };

  const handleRoleRowClick = (row: any) => {
    setSelectedRoleId(row.id);
    setRoleModalOpen(true);
  };

  const handleRegisterRoleClick = () => {
    setSelectedRoleId(null);
    setRoleModalOpen(true);
  };

  const handleUserSort = (key: string, dir: "asc" | "desc") => {
    setUserFilter("sortBy", key);
    setUserFilter("sortDir", dir);
  };

  const handleRoleSort = (key: string, dir: "asc" | "desc") => {
    setRoleFilter("sortBy", key);
    setRoleFilter("sortDir", dir);
  };

  const userColumns = [
    { key: "full_name", label: "Full Name", sortable: true },
    { key: "email", label: "Email Address" },
    { 
      key: "department_id", 
      label: "Department", 
      render: (row: any) => <span>{getDepartmentName(row.department_id)}</span> 
    },
    { 
      key: "role_id", 
      label: "Role", 
      render: (row: any) => <span>{getRoleName(row.role_id)}</span> 
    },
    { 
      key: "approval_limit_level", 
      label: "Approval Limit", 
      render: (row: any) => (
        <span className={styles.limitBadge}>
          {row.approval_limit_level || "NONE"}
        </span>
      ) 
    },
    { 
      key: "status", 
      label: "Status", 
      render: (row: any) => <RegistryStatusBadge status={row.status} /> 
    }
  ];

  const roleColumns = [
    { key: "role_code", label: "Role Code" },
    { key: "role_name", label: "Role Name", sortable: true },
    { 
      key: "role_type", 
      label: "Role Type", 
      render: (row: any) => (
        <span className={`${styles.typeBadge} ${styles[String(row.role_type).toLowerCase()] || ""}`}>
          {row.role_type}
        </span>
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
      <div className={styles.breadcrumb}>Registry &gt; Users &amp; Roles</div>
      <PageHeader
        title="Users &amp; Roles Governance"
        description="Manage secure identities, approval limit clearances, and role mappings."
        actions={
          canRegister && (
            activeTab === "users" ? (
              <Button variant="primary" onClick={handleRegisterUserClick}>
                + Register User
              </Button>
            ) : (
              <Button variant="primary" onClick={handleRegisterRoleClick}>
                + Register Role
              </Button>
            )
          )
        }
      />

      {/* Tab Selectors */}
      <div className={styles.tabsContainer}>
        <button
          type="button"
          onClick={() => handleTabChange("users")}
          className={`${styles.tabBtn} ${activeTab === "users" ? styles.activeTab : ""}`}
        >
          Users Registry
        </button>
        <button
          type="button"
          onClick={() => handleTabChange("roles")}
          className={`${styles.tabBtn} ${activeTab === "roles" ? styles.activeTab : ""}`}
        >
          Roles Registry
        </button>
      </div>

      {activeTab === "users" ? (
        <div className={styles.tabContent}>
          {/* Filters Bar for Users */}
          <div className={styles.filterBar}>
            <div className={styles.searchGroup}>
              <input
                type="text"
                placeholder="Search users..."
                value={userSearchTerm}
                onChange={(e) => setUserSearchTerm(e.target.value)}
                className={styles.searchInput}
              />
            </div>

            <div className={styles.filtersGroup}>
              {/* Department Selector */}
              <select
                value={userFilters.department_id || ""}
                onChange={(e) => setUserFilter("department_id", e.target.value)}
                className={styles.filterSelect}
              >
                <option value="">All Departments</option>
                {departments.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.department_name}
                  </option>
                ))}
              </select>

              {/* Role Selector */}
              <select
                value={userFilters.role_id || ""}
                onChange={(e) => setUserFilter("role_id", e.target.value)}
                className={styles.filterSelect}
              >
                <option value="">All Roles</option>
                {rolesList.map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.role_name}
                  </option>
                ))}
              </select>

              {/* Status Selector */}
              <select
                value={userFilters.status}
                onChange={(e) => setUserFilter("status", e.target.value)}
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

          <div className={styles.tableContainer}>
            <RegistryDataTable
              columns={userColumns}
              data={usersData?.items || []}
              isLoading={usersLoading}
              totalCount={usersData?.total || 0}
              page={userPaginationProps.page}
              pageSize={userPaginationProps.pageSize}
              onPageChange={userPaginationProps.onPageChange}
              onSort={handleUserSort}
              sortBy={userFilters.sortBy}
              sortDir={userFilters.sortDir}
              onRowClick={handleUserRowClick}
              emptyMessage="No users found matching the search criteria."
            />
          </div>
        </div>
      ) : (
        <div className={styles.tabContent}>
          {/* Filters Bar for Roles */}
          <div className={styles.filterBar}>
            <div className={styles.searchGroup}>
              <input
                type="text"
                placeholder="Search roles..."
                value={roleSearchTerm}
                onChange={(e) => setRoleSearchTerm(e.target.value)}
                className={styles.searchInput}
              />
            </div>

            <div className={styles.filtersGroup}>
              {/* Role Type Filter */}
              <select
                value={roleFilters.role_type || ""}
                onChange={(e) => setRoleFilter("role_type", e.target.value)}
                className={styles.filterSelect}
              >
                <option value="">All Types</option>
                <option value="SYSTEM">SYSTEM</option>
                <option value="BUSINESS">BUSINESS</option>
                <option value="GOVERNANCE">GOVERNANCE</option>
              </select>

              {/* Status Selector */}
              <select
                value={roleFilters.status}
                onChange={(e) => setRoleFilter("status", e.target.value)}
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

          <div className={styles.tableContainer}>
            <RegistryDataTable
              columns={roleColumns}
              data={rolesData?.items || []}
              isLoading={rolesLoading}
              totalCount={rolesData?.total || 0}
              page={rolePaginationProps.page}
              pageSize={rolePaginationProps.pageSize}
              onPageChange={rolePaginationProps.onPageChange}
              onSort={handleRoleSort}
              sortBy={roleFilters.sortBy}
              sortDir={roleFilters.sortDir}
              onRowClick={handleRoleRowClick}
              emptyMessage="No roles found matching the search criteria."
            />
          </div>
        </div>
      )}

      {/* Users Edit/Create Modal */}
      <UserFormModal
        isOpen={userModalOpen}
        onClose={() => setUserModalOpen(false)}
        userId={selectedUserId}
        onSuccess={refetchUsers}
      />

      {/* Roles Edit/Create Modal */}
      <RoleFormModal
        isOpen={roleModalOpen}
        onClose={() => setRoleModalOpen(false)}
        roleId={selectedRoleId}
        onSuccess={refetchRoles}
      />
    </div>
  );
};

export default RegistryUsersRolesPage;

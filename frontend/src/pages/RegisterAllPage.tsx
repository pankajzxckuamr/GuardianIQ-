/* src/pages/RegisterAllPage.tsx */

import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { PageHeader } from "../components/common/PageHeader";
import { RegistryDataTable } from "../components/common/RegistryDataTable";
import { Button } from "../components/common/Button";
import { RegisterAllWizardModal } from "../components/registry/RegisterAllWizardModal";
import { useRegistryFilters } from "../hooks/useRegistryFilters";
import { useRegistryEntity } from "../hooks/useRegistryEntity";
import { useAuth } from "../hooks/useAuth";
import * as registryService from "../services/registry/registryService";
import { Modal } from "../components/common/Modal";
import { ConfirmDeleteModal } from "../components/common/ConfirmDeleteModal";
import { useToast } from "../hooks/useToast";
import styles from "./RegisterAllPage.module.css";

const formatDate = (dateStr: string) => {
  if (!dateStr) return "-";
  try {
    const d = new Date(dateStr);
    return d.toLocaleString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit"
    });
  } catch {
    return dateStr;
  }
};

export const RegisterAllPage: React.FC = () => {
  const { currentUser } = useAuth();
  const { showToast } = useToast();
  const { filters, setFilter, paginationProps } = useRegistryFilters("name");

  // Set document title
  useEffect(() => {
    document.title = "Guided Onboarding — GuardianIQ Registry";
  }, []);

  const [searchTerm, setSearchTerm] = useState(filters.search);

  useEffect(() => {
    const delayDebounceFn = setTimeout(() => {
      setFilter("search", searchTerm);
    }, 400);
    return () => clearTimeout(delayDebounceFn);
  }, [searchTerm, setFilter]);

  // Fetch guided onboarding sessions
  const { data, isLoading, refetch } = useRegistryEntity(
    () => registryService.listRegisterAll({
      search: filters.search,
      page: filters.page,
      per_page: filters.pageSize,
      sort_by: filters.sortBy,
      sort_dir: filters.sortDir
    }),
    [
      filters.search,
      filters.page,
      filters.pageSize,
      filters.sortBy,
      filters.sortDir
    ]
  );

  // Modal Control (Wizard)
  const [wizardOpen, setWizardOpen] = useState(false);

  // Modal Control (Details View)
  const [selectedSession, setSelectedSession] = useState<any | null>(null);
  const [isDetailOpen, setIsDetailOpen] = useState(false);

  // Deletion state
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  const handleRowClick = (row: any) => {
    setSelectedSession(row);
    setIsDetailOpen(true);
  };

  const handleSort = (key: string, dir: "asc" | "desc") => {
    setFilter("sortBy", key);
    setFilter("sortDir", dir);
  };

  const handleDeleteClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsDeleteModalOpen(true);
  };

  const handleConfirmDelete = async () => {
    if (!selectedSession) return;
    setIsDeleting(true);
    try {
      await registryService.deleteRegisterAll(selectedSession.id);
      showToast("Guided Onboarding record deleted successfully.", "success");
      setIsDeleteModalOpen(false);
      setIsDetailOpen(false);
      refetch();
    } catch (err: any) {
      showToast(err.message || "Failed to delete onboarding record.", "error");
    } finally {
      setIsDeleting(false);
    }
  };

  const columns = [
    { key: "name", label: "Session Name", sortable: true },
    { 
      key: "department_name", 
      label: "Department", 
      render: (row: any) => <span>{row.department_name || "—"}</span> 
    },
    { 
      key: "user_name", 
      label: "User / Owner", 
      render: (row: any) => <span>{row.user_name || "—"}</span> 
    },
    { 
      key: "model_name", 
      label: "AI Model", 
      render: (row: any) => <span>{row.model_name || "—"}</span> 
    },
    { 
      key: "agent_name", 
      label: "AI Agent", 
      render: (row: any) => <span>{row.agent_name || "—"}</span> 
    },
    { 
      key: "workflow_name", 
      label: "Workflow", 
      render: (row: any) => <span>{row.workflow_name || "—"}</span> 
    },
    { 
      key: "created_at", 
      label: "Created At", 
      sortable: true, 
      render: (row: any) => formatDate(row.created_at) 
    }
  ];

  // Check RBAC permissions for register button
  const canRegister = currentUser?.is_superuser || 
    currentUser?.roles?.some(role => ["admin", "governance_manager", "super_admin"].includes(role.toLowerCase()));

  return (
    <div className={styles.page}>
      <div className={styles.breadcrumb}>Registry &gt; Guided Onboarding</div>
      <PageHeader
        title="Guided Onboarding"
        description="Onboard an entire system containing departments, roles, users, models, agents, tools, and workflows in one visual sequence."
        actions={
          canRegister && (
            <Button variant="primary" onClick={() => setWizardOpen(true)}>
              + Register All Assets
            </Button>
          )
        }
      />

      {/* Filter and Search */}
      <div className={styles.filterBar}>
        <div className={styles.searchGroup}>
          <input
            type="text"
            placeholder="Search onboarding sessions..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className={styles.searchInput}
          />
        </div>
      </div>

      {/* Main DataTable */}
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
          emptyMessage="No guided onboarding sessions found matching criteria."
        />
      </div>

      {/* Register All Wizard Stepper Modal */}
      <RegisterAllWizardModal
        isOpen={wizardOpen}
        onClose={() => setWizardOpen(false)}
        onSuccess={refetch}
      />

      {/* Details Modal */}
      <Modal
        isOpen={isDetailOpen}
        onClose={() => setIsDetailOpen(false)}
        title={`Onboarding Details: ${selectedSession?.name || ""}`}
        size="lg"
      >
        {selectedSession && (
          <div className={styles.detailContainer}>
            <div className={styles.detailGrid}>
              
              <div className={styles.detailItem}>
                <span className={styles.detailLabel}>Department</span>
                {selectedSession.department_id ? (
                  <Link 
                    className={styles.detailLink} 
                    to={`/registry/departments?search=${encodeURIComponent(selectedSession.department_name)}`}
                    onClick={() => setIsDetailOpen(false)}
                  >
                    {selectedSession.department_name}
                  </Link>
                ) : (
                  <span className={styles.emptyValue}>No department linked</span>
                )}
              </div>

              <div className={styles.detailItem}>
                <span className={styles.detailLabel}>Role Configuration</span>
                {selectedSession.role_id ? (
                  <Link 
                    className={styles.detailLink} 
                    to={`/registry/users-roles?tab=roles&search=${encodeURIComponent(selectedSession.role_name)}`}
                    onClick={() => setIsDetailOpen(false)}
                  >
                    {selectedSession.role_name}
                  </Link>
                ) : (
                  <span className={styles.emptyValue}>No role linked</span>
                )}
              </div>

              <div className={styles.detailItem}>
                <span className={styles.detailLabel}>User / Owner</span>
                {selectedSession.user_id ? (
                  <Link 
                    className={styles.detailLink} 
                    to={`/registry/users-roles?tab=users&search=${encodeURIComponent(selectedSession.user_name)}`}
                    onClick={() => setIsDetailOpen(false)}
                  >
                    {selectedSession.user_name}
                  </Link>
                ) : (
                  <span className={styles.emptyValue}>No user linked</span>
                )}
              </div>

              <div className={styles.detailItem}>
                <span className={styles.detailLabel}>Data Source</span>
                {selectedSession.data_source_id ? (
                  <Link 
                    className={styles.detailLink} 
                    to={`/registry/data-sources?search=${encodeURIComponent(selectedSession.data_source_name)}`}
                    onClick={() => setIsDetailOpen(false)}
                  >
                    {selectedSession.data_source_name}
                  </Link>
                ) : (
                  <span className={styles.emptyValue}>No data source linked</span>
                )}
              </div>

              <div className={styles.detailItem}>
                <span className={styles.detailLabel}>AI Model</span>
                {selectedSession.model_id ? (
                  <Link 
                    className={styles.detailLink} 
                    to={`/registry/models?search=${encodeURIComponent(selectedSession.model_name)}`}
                    onClick={() => setIsDetailOpen(false)}
                  >
                    {selectedSession.model_name}
                  </Link>
                ) : (
                  <span className={styles.emptyValue}>No AI model linked</span>
                )}
              </div>

              <div className={styles.detailItem}>
                <span className={styles.detailLabel}>AI Agent</span>
                {selectedSession.agent_id ? (
                  <Link 
                    className={styles.detailLink} 
                    to={`/registry/agents?search=${encodeURIComponent(selectedSession.agent_name)}`}
                    onClick={() => setIsDetailOpen(false)}
                  >
                    {selectedSession.agent_name}
                  </Link>
                ) : (
                  <span className={styles.emptyValue}>No AI agent linked</span>
                )}
              </div>

              <div className={styles.detailItem}>
                <span className={styles.detailLabel}>Tool Connector</span>
                {selectedSession.tool_id ? (
                  <Link 
                    className={styles.detailLink} 
                    to={`/registry/tools?search=${encodeURIComponent(selectedSession.tool_name)}`}
                    onClick={() => setIsDetailOpen(false)}
                  >
                    {selectedSession.tool_name}
                  </Link>
                ) : (
                  <span className={styles.emptyValue}>No tool linked</span>
                )}
              </div>

              <div className={styles.detailItem}>
                <span className={styles.detailLabel}>Workflow</span>
                {selectedSession.workflow_id ? (
                  <Link 
                    className={styles.detailLink} 
                    to={`/registry/workflows?search=${encodeURIComponent(selectedSession.workflow_name)}`}
                    onClick={() => setIsDetailOpen(false)}
                  >
                    {selectedSession.workflow_name}
                  </Link>
                ) : (
                  <span className={styles.emptyValue}>No workflow linked</span>
                )}
              </div>

            </div>

            {canRegister && (
              <button 
                type="button" 
                className={styles.deleteBtn}
                onClick={handleDeleteClick}
              >
                Delete Session Log
              </button>
            )}
          </div>
        )}
      </Modal>

      {/* Delete Confirmation */}
      <ConfirmDeleteModal
        isOpen={isDeleteModalOpen}
        onClose={() => setIsDeleteModalOpen(false)}
        onConfirm={handleConfirmDelete}
        entityName={selectedSession?.name || "Onboarding Session"}
        entityType="Onboarding Session"
        isDeleting={isDeleting}
      />
    </div>
  );
};

export default RegisterAllPage;

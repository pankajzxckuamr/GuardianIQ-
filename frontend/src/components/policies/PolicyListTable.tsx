import React, { useState } from "react";
import { Shield, Eye, PlusCircle, Search, AlertCircle, CheckCircle, Clock } from "lucide-react";
import type { Policy, PolicyCategory, PolicyStatus } from "../../types/policy";
import styles from "../../pages/PoliciesPage.module.css";

interface PolicyListTableProps {
  policies: Policy[];
  isLoading: boolean;
  onSelectPolicy: (policy: Policy) => void;
  onAttachPolicy: (policy: Policy) => void;
  onCreatePolicyClick: () => void;
}

export const PolicyListTable: React.FC<PolicyListTableProps> = ({
  policies,
  isLoading,
  onSelectPolicy,
  onAttachPolicy,
  onCreatePolicyClick,
}) => {
  const [searchTerm, setSearchTerm] = useState("");
  const [categoryFilter, setCategoryFilter] = useState<string>("ALL");
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [page, setPage] = useState<number>(1);
  const pageSize = 10;

  const handleSearchChange = (val: string) => {
    setSearchTerm(val);
    setPage(1);
  };

  const handleCategoryChange = (val: string) => {
    setCategoryFilter(val);
    setPage(1);
  };

  const handleStatusChange = (val: string) => {
    setStatusFilter(val);
    setPage(1);
  };

  const filtered = policies.filter((p) => {
    const matchesSearch =
      p.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      p.policy_code.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (p.description && p.description.toLowerCase().includes(searchTerm.toLowerCase()));
    const matchesCategory = categoryFilter === "ALL" || p.category === categoryFilter;
    const matchesStatus = statusFilter === "ALL" || p.status === statusFilter;
    return matchesSearch && matchesCategory && matchesStatus;
  });

  const totalCount = filtered.length;
  const totalPages = Math.ceil(totalCount / pageSize) || 1;
  const startRecord = totalCount === 0 ? 0 : (page - 1) * pageSize + 1;
  const endRecord = Math.min(page * pageSize, totalCount);
  const paginatedPolicies = filtered.slice((page - 1) * pageSize, page * pageSize);

  const getStatusBadge = (status: PolicyStatus) => {
    switch (status) {
      case "ACTIVE":
        return (
          <span style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "4px",
            padding: "2px 8px",
            borderRadius: "4px",
            fontSize: "0.75rem",
            fontWeight: 600,
            background: "rgba(16, 185, 129, 0.15)",
            color: "#34d399",
            border: "1px solid rgba(16, 185, 129, 0.3)"
          }}>
            <CheckCircle className="w-3 h-3" /> Active
          </span>
        );
      case "DRAFT":
        return (
          <span style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "4px",
            padding: "2px 8px",
            borderRadius: "4px",
            fontSize: "0.75rem",
            fontWeight: 600,
            background: "rgba(148, 163, 184, 0.15)",
            color: "#94a3b8",
            border: "1px solid rgba(148, 163, 184, 0.3)"
          }}>
            <Clock className="w-3 h-3" /> Draft
          </span>
        );
      case "SUSPENDED":
        return (
          <span style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "4px",
            padding: "2px 8px",
            borderRadius: "4px",
            fontSize: "0.75rem",
            fontWeight: 600,
            background: "rgba(245, 158, 11, 0.15)",
            color: "#fbbf24",
            border: "1px solid rgba(245, 158, 11, 0.3)"
          }}>
            <AlertCircle className="w-3 h-3" /> Suspended
          </span>
        );
      case "RETIRED":
        return (
          <span style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "4px",
            padding: "2px 8px",
            borderRadius: "4px",
            fontSize: "0.75rem",
            fontWeight: 600,
            background: "rgba(239, 68, 68, 0.15)",
            color: "#f87171",
            border: "1px solid rgba(239, 68, 68, 0.3)"
          }}>
            Retired
          </span>
        );
      default:
        return <span>{status}</span>;
    }
  };

  const getCategoryBadge = (category: PolicyCategory) => {
    return (
      <span style={{
        display: "inline-flex",
        alignItems: "center",
        padding: "2px 8px",
        borderRadius: "4px",
        fontSize: "0.75rem",
        fontWeight: 600,
        background: "rgba(99, 102, 241, 0.15)",
        color: "#818cf8",
        border: "1px solid rgba(99, 102, 241, 0.3)"
      }}>
        {category.replace("_", " ")}
      </span>
    );
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
      {/* Search & Filter Toolbar */}
      <div className={styles.toolbar}>
        <div style={{ display: "flex", alignItems: "center", gap: "10px", flex: 1, flexWrap: "wrap" }}>
          <div className={styles.searchBox}>
            <Search size={16} style={{ color: "var(--text-muted, #64748b)" }} />
            <input
              type="text"
              placeholder="Search policies by name, code, or description..."
              value={searchTerm}
              onChange={(e) => handleSearchChange(e.target.value)}
              className={styles.searchInput}
            />
          </div>

          <select
            value={categoryFilter}
            onChange={(e) => handleCategoryChange(e.target.value)}
            className={styles.filterSelect}
          >
            <option value="ALL">All Categories</option>
            <option value="ACCESS_CONTROL">Access Control</option>
            <option value="DATA_PROTECTION">Data Protection</option>
            <option value="FINANCIAL_SAFETY">Financial Safety</option>
            <option value="OPERATIONAL_SAFETY">Operational Safety</option>
            <option value="MODEL_SAFETY">Model Safety</option>
            <option value="GENERAL">General</option>
          </select>

          <select
            value={statusFilter}
            onChange={(e) => handleStatusChange(e.target.value)}
            className={styles.filterSelect}
          >
            <option value="ALL">All Statuses</option>
            <option value="ACTIVE">Active</option>
            <option value="DRAFT">Draft</option>
            <option value="SUSPENDED">Suspended</option>
            <option value="RETIRED">Retired</option>
          </select>
        </div>

        <button onClick={onCreatePolicyClick} className={styles.primaryBtn}>
          <PlusCircle size={16} /> Create Policy
        </button>
      </div>

      {/* Policies Table */}
      <div className={styles.tableWrapper}>
        <table className={styles.table}>
          <thead>
            <tr>
              <th className={styles.th}>Policy Code & Name</th>
              <th className={styles.th}>Category</th>
              <th className={styles.th}>Enforcement Mode</th>
              <th className={styles.th}>Priority</th>
              <th className={styles.th}>Status</th>
              <th className={styles.th} style={{ textAlign: "right" }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr>
                <td colSpan={6} style={{ padding: "48px 16px", textAlign: "center", color: "var(--text-muted, #64748b)" }}>
                  Loading policies...
                </td>
              </tr>
            ) : filtered.length === 0 ? (
              <tr>
                <td colSpan={6} style={{ padding: "48px 16px", textAlign: "center", color: "var(--text-muted, #64748b)" }}>
                  <Shield size={36} style={{ margin: "0 auto 8px auto", color: "var(--text-muted, #64748b)" }} />
                  <div>No compliance policies found matching your filters.</div>
                </td>
              </tr>
            ) : (
              paginatedPolicies.map((policy) => (
                <tr
                  key={policy.id}
                  className={styles.row}
                  style={{ cursor: "pointer" }}
                  onClick={() => onSelectPolicy(policy)}
                >
                  <td className={styles.td}>
                    <div style={{ fontWeight: 600, color: "var(--text-primary, #f8fafc)" }}>
                      {policy.name}
                    </div>
                    <div style={{ fontSize: "0.75rem", fontFamily: "monospace", color: "var(--text-secondary, #94a3b8)" }}>
                      {policy.policy_code}
                    </div>
                  </td>
                  <td className={styles.td}>{getCategoryBadge(policy.category)}</td>
                  <td className={styles.td}>
                    <span style={{
                      fontFamily: "monospace",
                      fontSize: "0.75rem",
                      padding: "2px 6px",
                      borderRadius: "4px",
                      background: "rgba(255, 255, 255, 0.06)",
                      color: "var(--text-secondary, #94a3b8)"
                    }}>
                      {policy.enforcement_mode}
                    </span>
                  </td>
                  <td className={styles.td} style={{ fontWeight: 700 }}>{policy.priority}</td>
                  <td className={styles.td}>{getStatusBadge(policy.status)}</td>
                  <td className={styles.td} style={{ textAlign: "right" }}>
                    <div style={{ display: "flex", alignItems: "center", justifyContent: "flex-end", gap: "8px" }} onClick={(e) => e.stopPropagation()}>
                      <button
                        onClick={() => onSelectPolicy(policy)}
                        title="View Details"
                        style={{
                          background: "rgba(255, 255, 255, 0.06)",
                          border: "1px solid rgba(255, 255, 255, 0.1)",
                          color: "var(--text-secondary, #94a3b8)",
                          padding: "6px",
                          borderRadius: "6px",
                          cursor: "pointer",
                          display: "flex",
                          alignItems: "center"
                        }}
                      >
                        <Eye size={14} />
                      </button>
                      <button
                        onClick={() => onAttachPolicy(policy)}
                        title="Attach to Entity"
                        style={{
                          background: "rgba(99, 102, 241, 0.15)",
                          border: "1px solid rgba(99, 102, 241, 0.3)",
                          color: "#818cf8",
                          padding: "4px 10px",
                          borderRadius: "6px",
                          fontSize: "0.75rem",
                          fontWeight: 600,
                          cursor: "pointer"
                        }}
                      >
                        Attach
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination Controls */}
      {totalCount > 0 && (
        <div style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          padding: "12px 16px",
          background: "rgba(15, 23, 42, 0.6)",
          border: "1px solid rgba(255, 255, 255, 0.08)",
          borderRadius: "8px",
          fontSize: "0.85rem",
          color: "var(--text-secondary, #94a3b8)"
        }}>
          <div>
            Showing <strong style={{ color: "#fff" }}>{startRecord}-{endRecord}</strong> of <strong style={{ color: "#fff" }}>{totalCount}</strong> policies
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <span>Page <strong style={{ color: "#fff" }}>{page}</strong> of <strong style={{ color: "#fff" }}>{totalPages}</strong></span>
            <div style={{ display: "flex", gap: "6px" }}>
              <button
                type="button"
                disabled={page <= 1}
                onClick={() => setPage((prev) => Math.max(1, prev - 1))}
                style={{
                  padding: "4px 12px",
                  borderRadius: "6px",
                  border: "1px solid rgba(255, 255, 255, 0.1)",
                  background: page <= 1 ? "rgba(255, 255, 255, 0.02)" : "rgba(255, 255, 255, 0.08)",
                  color: page <= 1 ? "#475569" : "#fff",
                  cursor: page <= 1 ? "not-allowed" : "pointer",
                  fontSize: "0.8rem",
                  fontWeight: 600
                }}
              >
                Previous
              </button>
              <button
                type="button"
                disabled={page >= totalPages}
                onClick={() => setPage((prev) => Math.min(totalPages, prev + 1))}
                style={{
                  padding: "4px 12px",
                  borderRadius: "6px",
                  border: "1px solid rgba(255, 255, 255, 0.1)",
                  background: page >= totalPages ? "rgba(255, 255, 255, 0.02)" : "rgba(255, 255, 255, 0.08)",
                  color: page >= totalPages ? "#475569" : "#fff",
                  cursor: page >= totalPages ? "not-allowed" : "pointer",
                  fontSize: "0.8rem",
                  fontWeight: 600
                }}
              >
                Next
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

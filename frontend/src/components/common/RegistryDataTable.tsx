/* src/components/common/RegistryDataTable.tsx */

import React, { useMemo } from "react";
import { Table, Column } from "./Table";
import { EmptyState } from "./EmptyState";
import { Button } from "./Button";
import "./RegistryDataTable.css";

interface RegistryColumn {
  key: string;
  label: string;
  sortable?: boolean;
  render?: (row: any) => React.ReactNode;
}

interface RegistryDataTableProps {
  columns: RegistryColumn[];
  data: any[];
  isLoading: boolean;
  totalCount: number;
  page: number;
  pageSize: number;
  onPageChange: (page: number) => void;
  onSort?: (key: string, dir: "asc" | "desc") => void;
  sortBy?: string;
  sortDir?: "asc" | "desc";
  emptyMessage?: string;
  onRowClick?: (row: any) => void;
}

export const RegistryDataTable: React.FC<RegistryDataTableProps> = ({
  columns,
  data,
  isLoading,
  totalCount,
  page,
  pageSize,
  onPageChange,
  onSort,
  sortBy = "",
  sortDir = "asc",
  emptyMessage,
  onRowClick
}) => {
  // Map Columns to Table.tsx structure
  const mappedColumns = useMemo((): Column<any>[] => {
    return columns.map((col) => {
      const isCurrentSort = sortBy === col.key;

      const headerContent = col.sortable ? (
        <button
          type="button"
          className={`registry-th-sort-btn ${isCurrentSort ? "active" : ""}`}
          onClick={() => {
            if (onSort) {
              const nextDir = isCurrentSort && sortDir === "asc" ? "desc" : "asc";
              onSort(col.key, nextDir);
            }
          }}
        >
          <span>{col.label}</span>
          <span className="registry-sort-arrow">
            {!isCurrentSort ? " ↕" : sortDir === "asc" ? " ↑" : " ↓"}
          </span>
        </button>
      ) : (
        col.label
      );

      const customRender = isLoading
        ? () => <div className="registry-skeleton-cell" />
        : col.render;

      return {
        key: col.key,
        header: headerContent as unknown as string,
        render: customRender
      };
    });
  }, [columns, isLoading, sortBy, sortDir, onSort]);

  const tableData = useMemo(() => {
    return isLoading ? Array(5).fill({}) : data;
  }, [isLoading, data]);

  // If empty and not loading, show the EmptyState component
  if (!isLoading && data.length === 0) {
    return (
      <EmptyState
        title="No records found"
        description={emptyMessage || "There are no records matching your search filters."}
      />
    );
  }

  // Calculate pagination boundaries
  const startRecord = totalCount === 0 ? 0 : (page - 1) * pageSize + 1;
  const endRecord = Math.min(page * pageSize, totalCount);

  const totalPages = Math.ceil(totalCount / pageSize) || 1;
  const hasPrev = page > 1;
  const hasNext = page < totalPages;

  return (
    <div className="registry-datatable-container">
      {/* Wrapped Base Table */}
      <Table
        columns={mappedColumns}
        data={tableData}
        loading={false} // Loading state is handled locally via skeletons
        onRowClick={isLoading ? undefined : onRowClick}
      />

      {/* Pagination Controls */}
      {!isLoading && (
        <div className="registry-pagination-bar">
          <div className="registry-pagination-info">
            Showing <span className="highlight">{startRecord}–{endRecord}</span> of{" "}
            <span className="highlight">{totalCount}</span> records
          </div>
          <div className="registry-pagination-actions">
            <Button
              variant="secondary"
              size="sm"
              disabled={!hasPrev}
              onClick={() => onPageChange(page - 1)}
            >
              Previous
            </Button>
            <span className="registry-page-num">
              Page {page} of {totalPages}
            </span>
            <Button
              variant="secondary"
              size="sm"
              disabled={!hasNext}
              onClick={() => onPageChange(page + 1)}
            >
              Next
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};

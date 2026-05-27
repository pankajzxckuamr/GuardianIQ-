/* src/components/common/Table.tsx */
import React from "react";
import "./Table.css";

export interface Column<T> {
  key: string;
  header: string;
  render?: (row: T) => React.ReactNode;
}

interface TableProps<T> {
  columns: Column<T>[];
  data: T[];
  loading?: boolean;
  emptyMessage?: string;
  onRowClick?: (row: T) => void;
}

export function Table<T>({
  columns,
  data,
  loading = false,
  emptyMessage = "No data available",
  onRowClick,
}: TableProps<T>) {
  return (
    <div className="table-container">
      <table className="table">
        <thead className="table-thead">
          <tr>
            {columns.map((col) => (
              <th key={col.key} className="table-th">
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="table-tbody">
          {loading ? (
            <tr>
              <td colSpan={columns.length} className="table-td-loading">
                <div className="table-spinner-container">
                  <div className="table-spinner" />
                  <span>Loading data...</span>
                </div>
              </td>
            </tr>
          ) : data.length === 0 ? (
            <tr>
              <td colSpan={columns.length} className="table-td-empty">
                {emptyMessage}
              </td>
            </tr>
          ) : (
            data.map((row, idx) => (
              <tr
                key={idx}
                className={`table-tr ${onRowClick ? "table-tr--clickable" : ""}`}
                onClick={() => onRowClick?.(row)}
              >
                {columns.map((col) => (
                  <td key={col.key} className="table-td">
                    {col.render ? col.render(row) : (row as Record<string, unknown>)[col.key] as React.ReactNode}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}

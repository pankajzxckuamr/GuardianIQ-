import React, { useState } from 'react';
import { SortOrder } from '@/types/common';

export interface ColumnDef<T> {
  /** The data key to access on each row, or a custom string key for render-only columns */
  key: keyof T | string;
  /** Column header label */
  header: string;
  /** Optional custom cell renderer; receives the full row object */
  render?: (row: T) => React.ReactNode;
  /** Optional fixed column width (e.g. "120px" or "10%") */
  width?: string;
  /** Whether this column can be sorted */
  sortable?: boolean;
}

export interface PaginationConfig {
  page: number;
  total: number;
  pageSize: number;
  onPageChange: (page: number) => void;
}

export interface DataTableProps<T> {
  columns: ColumnDef<T>[];
  data: T[];
  isLoading?: boolean;
  emptyState?: React.ReactNode;
  onSort?: (key: string, order: SortOrder) => void;
  pagination?: PaginationConfig;
  /** Optional unique row key extractor; falls back to row index */
  getRowKey?: (row: T, index: number) => string | number;
}

const SKELETON_ROW_COUNT = 3;

function SkeletonRows({ columnCount }: { columnCount: number }): React.ReactElement {
  return (
    <>
      {Array.from({ length: SKELETON_ROW_COUNT }).map((_, rowIdx) => (
        <tr key={rowIdx} className="data-table__row data-table__row--skeleton" aria-hidden="true">
          {Array.from({ length: columnCount }).map((_, colIdx) => (
            <td key={colIdx} className="data-table__cell">
              <span className="data-table__skeleton-cell" />
            </td>
          ))}
        </tr>
      ))}
    </>
  );
}

function SortIcon({ direction }: { direction: SortOrder | null }): React.ReactElement {
  if (direction === 'asc') return <span className="data-table__sort-icon" aria-hidden="true">↑</span>;
  if (direction === 'desc') return <span className="data-table__sort-icon" aria-hidden="true">↓</span>;
  return <span className="data-table__sort-icon data-table__sort-icon--idle" aria-hidden="true">↕</span>;
}

function Pagination({ page, total, pageSize, onPageChange }: PaginationConfig): React.ReactElement {
  const totalPages = Math.ceil(total / pageSize);
  const start = Math.min((page - 1) * pageSize + 1, total);
  const end = Math.min(page * pageSize, total);

  return (
    <div className="data-table__pagination" role="navigation" aria-label="Table pagination">
      <span className="data-table__pagination-info">
        {total === 0 ? '0 results' : `${start}–${end} of ${total}`}
      </span>
      <div className="data-table__pagination-controls">
        <button
          className="data-table__page-btn"
          onClick={() => onPageChange(1)}
          disabled={page === 1}
          aria-label="First page"
        >
          «
        </button>
        <button
          className="data-table__page-btn"
          onClick={() => onPageChange(page - 1)}
          disabled={page === 1}
          aria-label="Previous page"
        >
          ‹
        </button>
        <span className="data-table__pagination-page">
          Page {page} of {totalPages}
        </span>
        <button
          className="data-table__page-btn"
          onClick={() => onPageChange(page + 1)}
          disabled={page >= totalPages}
          aria-label="Next page"
        >
          ›
        </button>
        <button
          className="data-table__page-btn"
          onClick={() => onPageChange(totalPages)}
          disabled={page >= totalPages}
          aria-label="Last page"
        >
          »
        </button>
      </div>
    </div>
  );
}

export function DataTable<T extends Record<string, unknown>>({
  columns,
  data,
  isLoading = false,
  emptyState,
  onSort,
  pagination,
  getRowKey,
}: DataTableProps<T>): React.ReactElement {
  const [sortKey, setSortKey] = useState<string | null>(null);
  const [sortOrder, setSortOrder] = useState<SortOrder>('asc');

  const handleSort = (key: string) => {
    if (!onSort) return;
    const nextOrder: SortOrder = sortKey === key && sortOrder === 'asc' ? 'desc' : 'asc';
    setSortKey(key);
    setSortOrder(nextOrder);
    onSort(key, nextOrder);
  };

  const isEmpty = !isLoading && data.length === 0;

  return (
    <div className="data-table-wrapper">
      <div className="data-table-scroll">
        <table className="data-table" role="grid" aria-busy={isLoading}>
          <thead className="data-table__head">
            <tr>
              {columns.map((col) => {
                const colKey = col.key as string;
                const isSorted = sortKey === colKey;
                return (
                  <th
                    key={colKey}
                    className={[
                      'data-table__th',
                      col.sortable ? 'data-table__th--sortable' : '',
                      isSorted ? 'data-table__th--sorted' : '',
                    ]
                      .filter(Boolean)
                      .join(' ')}
                    style={col.width ? { width: col.width } : undefined}
                    aria-sort={
                      isSorted
                        ? sortOrder === 'asc'
                          ? 'ascending'
                          : 'descending'
                        : undefined
                    }
                    onClick={col.sortable ? () => handleSort(colKey) : undefined}
                    tabIndex={col.sortable ? 0 : undefined}
                    onKeyDown={
                      col.sortable
                        ? (e) => e.key === 'Enter' && handleSort(colKey)
                        : undefined
                    }
                  >
                    <span className="data-table__th-content">
                      {col.header}
                      {col.sortable && (
                        <SortIcon direction={isSorted ? sortOrder : null} />
                      )}
                    </span>
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody className="data-table__body">
            {isLoading ? (
              <SkeletonRows columnCount={columns.length} />
            ) : isEmpty ? (
              <tr>
                <td
                  colSpan={columns.length}
                  className="data-table__cell data-table__empty"
                >
                  {emptyState ?? <span>No data available.</span>}
                </td>
              </tr>
            ) : (
              data.map((row, rowIdx) => (
                <tr
                  key={getRowKey ? getRowKey(row, rowIdx) : rowIdx}
                  className="data-table__row"
                >
                  {columns.map((col) => {
                    const colKey = col.key as string;
                    const cellContent = col.render
                      ? col.render(row)
                      : (row[colKey as keyof T] as React.ReactNode);
                    return (
                      <td key={colKey} className="data-table__cell">
                        {cellContent}
                      </td>
                    );
                  })}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {pagination && !isLoading && <Pagination {...pagination} />}
    </div>
  );
}

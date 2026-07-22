import { useState, useCallback } from 'react';

interface UseTableStateOptions {
  initialPage?: number;
  initialPageSize?: number;
  initialSortBy?: string;
  initialSortDir?: 'asc' | 'desc';
}

export function useTableState(options: UseTableStateOptions = {}) {
  const [page, setPage] = useState(options.initialPage || 1);
  const [pageSize, setPageSize] = useState(options.initialPageSize || 10);
  const [sortBy, setSortBy] = useState(options.initialSortBy || 'created_at');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>(options.initialSortDir || 'desc');
  const [search, setSearch] = useState('');

  const handlePageChange = useCallback((newPage: number) => {
    setPage(newPage);
  }, []);

  const handlePageSizeChange = useCallback((newPageSize: number) => {
    setPageSize(newPageSize);
    setPage(1); // Reset to first page
  }, []);

  const handleSort = useCallback((columnId: string) => {
    setSortBy((prevSortBy) => {
      if (prevSortBy === columnId) {
        setSortDir((prevDir) => (prevDir === 'asc' ? 'desc' : 'asc'));
        return prevSortBy;
      }
      setSortDir('desc');
      return columnId;
    });
    setPage(1);
  }, []);

  const handleSearch = useCallback((newSearch: string) => {
    setSearch(newSearch);
    setPage(1);
  }, []);

  const reset = useCallback(() => {
    setPage(1);
    setSearch('');
    setSortBy(options.initialSortBy || 'created_at');
    setSortDir(options.initialSortDir || 'desc');
  }, [options.initialSortBy, options.initialSortDir]);

  return {
    page,
    pageSize,
    sortBy,
    sortDir,
    search,
    setPage: handlePageChange,
    setPageSize: handlePageSizeChange,
    handleSort,
    setSearch: handleSearch,
    reset,
  };
}

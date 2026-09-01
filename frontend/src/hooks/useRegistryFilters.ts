/* src/hooks/useRegistryFilters.ts */

import { useSearchParams } from "react-router-dom";
import { useCallback, useMemo } from "react";

export interface RegistryFilters {
  search: string;
  status: string;
  page: number;
  pageSize: number;
  sortBy: string;
  sortDir: "asc" | "desc";
  [key: string]: any;
}

export function useRegistryFilters(
  defaultSortBy = "created_at",
  defaultPageSize = 10,
  defaultSortDir: "asc" | "desc" = "desc"
) {
  const [searchParams, setSearchParams] = useSearchParams();

  const filters = useMemo((): RegistryFilters => {
    const search = searchParams.get("search") || "";
    const status = searchParams.get("status") || "";
    const pageVal = searchParams.get("page");
    const page = pageVal ? parseInt(pageVal, 10) || 1 : 1;
    const pageSizeVal = searchParams.get("pageSize");
    const pageSize = pageSizeVal ? parseInt(pageSizeVal, 10) || defaultPageSize : defaultPageSize;
    const sortBy = searchParams.get("sortBy") || defaultSortBy;
    const sortDirVal = searchParams.get("sortDir");
    const sortDir = (sortDirVal as "asc" | "desc") || defaultSortDir;

    // Grab any other query params dynamically
    const extraParams: Record<string, string> = {};
    searchParams.forEach((value, key) => {
      if (!["search", "status", "page", "pageSize", "sortBy", "sortDir"].includes(key)) {
        extraParams[key] = value;
      }
    });

    return {
      search,
      status,
      page,
      pageSize,
      sortBy,
      sortDir,
      ...extraParams
    };
  }, [searchParams, defaultSortBy, defaultPageSize, defaultSortDir]);

  const setFilter = useCallback((key: string, value: any) => {
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      const currentValue = prev.get(key) || "";
      const newValue = value === undefined || value === null ? "" : String(value);

      if (newValue === "") {
        next.delete(key);
      } else {
        next.set(key, newValue);
      }

      // Only reset page to 1 if the key is not "page" AND the value actually changed
      if (key !== "page" && currentValue !== newValue) {
        next.set("page", "1");
      }
      return next;
    });
  }, [setSearchParams]);

  const resetFilters = useCallback(() => {
    setSearchParams(() => {
      const next = new URLSearchParams();
      next.set("page", "1");
      if (defaultSortBy) {
        next.set("sortBy", defaultSortBy);
      }
      return next;
    });
  }, [setSearchParams, defaultSortBy]);

  const onPageChange = useCallback((newPage: number) => {
    setFilter("page", newPage);
  }, [setFilter]);

  const paginationProps = useMemo(() => ({
    page: filters.page,
    pageSize: filters.pageSize,
    onPageChange
  }), [filters.page, filters.pageSize, onPageChange]);

  return {
    filters,
    setFilter,
    resetFilters,
    paginationProps
  };
}

/**
 * Sorting order for lists and tables.
 */
export type SortOrder = "asc" | "desc";

/**
 * Parameters used for pagination and sorting in API requests.
 */
export interface PaginationParams {
  /** The current page number (1-indexed) */
  page: number;
  /** The number of items to return per page */
  page_size: number;
  /** Optional field name to sort the results by */
  sort_by?: string;
  /** Optional sort order */
  sort_order?: SortOrder;
}

/**
 * Defines the visual variant for status badges.
 */
export type StatusBadgeVariant = "success" | "warning" | "danger" | "info" | "neutral";

/**
 * Defines the application's theme mode.
 */
export type ThemeMode = "light" | "dark";

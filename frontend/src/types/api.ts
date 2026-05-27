/**
 * Represents the standard API response envelope emitted by the FastAPI backend.
 * All successful and error responses follow this structure.
 */
export interface StandardResponse<T> {
  /** The status of the response */
  status: "success" | "error";
  /** A unique identifier for the request, useful for tracing */
  request_id: string;
  /** A human-readable message describing the outcome */
  message: string;
  /** The payload data of the response, or null if there is no data or an error occurred */
  data: T | null;
}

/**
 * Represents a paginated response payload.
 */
export interface PaginatedResponse<T> {
  /** The array of items for the current page */
  items: T[];
  /** The total number of items available across all pages */
  total: number;
  /** The current page number (1-indexed) */
  page: number;
  /** The number of items per page */
  page_size: number;
}

/**
 * Represents a detailed API error structure, often embedded within the StandardResponse or thrown.
 */
export interface ApiError {
  /** A specific error code for programmatic handling */
  error_code: string;
  /** A generic error message */
  message: string;
  /** Detailed validation errors or specific field issues */
  detail: Array<Record<string, any>>;
}

/**
 * Metadata associated with a request for tracing and logging.
 */
export interface RequestMeta {
  /** A unique identifier for the request */
  request_id: string;
  /** The timestamp when the request was processed */
  timestamp: string;
}

/* src/types/api.ts */

export interface ApiResponse<T = unknown> {
  status: "success" | "error";
  request_id?: string;
  data?: T;
  message?: string;
  errors?: Record<string, string[]>;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

export interface ApiError {
  status: number;
  message: string;
  detail?: string;
  request_id?: string;
}

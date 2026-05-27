/**
 * Response shape from GET /api/health and GET /api/health/db.
 * Follows the standard backend envelope: StandardResponse<T>.
 */
export interface HealthData {
  /** Present on GET /api/health */
  status?: string;
  /** Present on GET /api/health/db */
  database?: string;
}

export interface HealthResponse {
  status: 'success' | 'error';
  request_id: string;
  message: string;
  data: HealthData | null;
}

/**
 * Local UI state enriched with timing and fetch metadata.
 */
export interface HealthCheckResult {
  response: HealthResponse | null;
  /** Round-trip latency in milliseconds */
  latencyMs: number | null;
  /** ISO timestamp of when the check completed */
  checkedAt: string | null;
  isLoading: boolean;
  error: string | null;
}

/**
 * The unwrapped data payload from GET /api/foundation/enums.
 * Keys are enum names (e.g. "SourceType"), values are the list of valid string values.
 */
export type EnumMap = Record<string, string[]>;

/**
 * Full response shape returned by GET /api/foundation/enums,
 * wrapped in the StandardResponse envelope.
 */
export interface EnumResponse {
  status: 'success' | 'error';
  request_id: string;
  message: string;
  data: EnumMap | null;
}

/**
 * Foundation health data for the API version endpoint (/api/version).
 * Not currently exposed by a dedicated health endpoint but reserved for future use.
 */
export interface FoundationHealthData {
  /** Semantic version string, e.g. "0.1.0" */
  version: string;
  /** Deployment environment identifier, e.g. "development" | "staging" | "production" */
  environment: string;
  /** Seconds since the process started */
  uptime_seconds: number;
}

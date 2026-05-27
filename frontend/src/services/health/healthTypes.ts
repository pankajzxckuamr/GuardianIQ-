/* src/services/health/healthTypes.ts */

export interface HealthStatus {
  status: "healthy" | "degraded" | "unhealthy";
  version?: string;
  uptime?: number;
  timestamp?: string;
}

export interface DbHealthStatus {
  status: "healthy" | "unhealthy";
  latency_ms?: number;
  message?: string;
}

export interface FullHealthReport {
  api: HealthStatus;
  database: DbHealthStatus;
}

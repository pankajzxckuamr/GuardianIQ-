/**
 * Backend AuditEvent schema as emitted by AuditEventResponse (Pydantic).
 * Field names mirror the backend exactly to avoid mapping errors.
 */
export interface AuditEventResponse {
  /** Auto-incremented integer primary key */
  id: number;
  /** The type/category of the event (e.g. "POLICY_CREATE", "LOGIN") */
  event_type: string;
  /** The type of entity this event relates to (e.g. "Policy", "User") */
  entity_type: string;
  /** The numeric ID of the affected entity; may be null for system-level events */
  entity_id: number | null;
  /** The numeric user ID of the actor who triggered this event; null for system actions */
  actor_user_id: number | null;
  /** The specific action performed (e.g. "create", "update", "delete") */
  action: string;
  /** Arbitrary key-value metadata attached to the event */
  event_metadata: Record<string, unknown> | null;
  /** ISO 8601 timestamp of when the event was recorded */
  created_at: string;
}

/**
 * Frontend-normalized AuditEvent type.
 * Maps backend snake_case fields to camelCase for consistency across the codebase.
 */
export interface AuditEvent {
  /** Auto-incremented integer primary key */
  id: number;
  /** The type/category of the event */
  eventType: string;
  /** The type of entity this event relates to */
  entityType: string;
  /** The ID of the affected entity; null for system-level events */
  entityId: number | null;
  /** The numeric user ID of the actor; null for system actions */
  actorUserId: number | null;
  /** The specific action performed */
  action: string;
  /** Arbitrary key-value metadata */
  eventMetadata: Record<string, unknown> | null;
  /** ISO 8601 timestamp */
  createdAt: string;
}

/**
 * Paginated list of AuditEvent items returned by GET /api/audit.
 * Mirrors the StandardResponse<list[AuditEventResponse]> envelope data field.
 */
export interface AuditListResponse {
  items: AuditEvent[];
  total: number;
  page: number;
  page_size: number;
}

/**
 * Query parameters accepted by GET /api/audit.
 * All fields are optional — omitted fields are ignored by the backend.
 */
export interface AuditQueryParams {
  /** 1-indexed page number */
  page?: number;
  /** Number of items per page */
  page_size?: number;
  /** Filter events by actor user ID */
  actor_id?: number;
  /** Filter events by action string */
  action?: string;
  /** ISO 8601 start date filter (inclusive) */
  from_date?: string;
  /** ISO 8601 end date filter (inclusive) */
  to_date?: string;
}

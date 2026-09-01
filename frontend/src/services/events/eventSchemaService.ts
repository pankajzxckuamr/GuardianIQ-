/* src/services/events/eventSchemaService.ts */
import serverClient from "../shared/apiClient";
import type { ApiResponse } from "../registry/registryTypes";

export interface EventSchemaRecord {
  id: string;
  event_type: string;
  version: string;
  json_schema: Record<string, any>;
  is_active: boolean;
  created_at: string;
  created_by?: string | null;
}

export interface CreateEventSchemaPayload {
  event_type: string;
  version?: string;
  json_schema: Record<string, any>;
  is_active?: boolean;
}

export interface UpdateEventSchemaPayload {
  json_schema?: Record<string, any>;
  is_active?: boolean;
}

const SCHEMAS_BASE = "/api/v1/events/schemas";

export async function fetchEventSchemas(): Promise<ApiResponse<EventSchemaRecord[]>> {
  const res = await serverClient.get<any>(SCHEMAS_BASE);
  return {
    status: "success",
    request_id: res?.request_id || "",
    data: Array.isArray(res) ? res : (res?.data || []),
    message: res?.message || "Event schemas retrieved successfully",
  };
}

export async function createEventSchema(
  payload: CreateEventSchemaPayload
): Promise<ApiResponse<EventSchemaRecord>> {
  const res = await serverClient.post<any>(SCHEMAS_BASE, payload);
  return {
    status: "success",
    request_id: res?.request_id || "",
    data: res?.data !== undefined ? res.data : res,
    message: res?.message || "Event schema created successfully",
  };
}

export async function updateEventSchema(
  schemaId: string,
  payload: UpdateEventSchemaPayload
): Promise<ApiResponse<EventSchemaRecord>> {
  const res = await serverClient.put<any>(`${SCHEMAS_BASE}/${schemaId}`, payload);
  return {
    status: "success",
    request_id: res?.request_id || "",
    data: res?.data !== undefined ? res.data : res,
    message: res?.message || "Event schema updated successfully",
  };
}

export async function deleteEventSchema(schemaId: string): Promise<ApiResponse<any>> {
  const res = await serverClient.delete<any>(`${SCHEMAS_BASE}/${schemaId}`);
  return {
    status: "success",
    request_id: res?.request_id || "",
    data: res?.data !== undefined ? res.data : res,
    message: res?.message || "Event schema deleted successfully",
  };
}

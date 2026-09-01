/* src/services/events/eventRetentionService.ts */
import serverClient from "../shared/apiClient";
import type { ApiResponse } from "../registry/registryTypes";

export interface EventRetentionRuleRecord {
  id: string;
  tenant_id: string;
  event_category: string;
  retention_days: number;
  action: string; // 'PURGE' | 'ARCHIVE' | 'ANONYMIZE'
  created_at: string;
}

export interface CreateRetentionRulePayload {
  event_category: string;
  retention_days: number;
  action: string;
}

export interface UpdateRetentionRulePayload {
  retention_days?: number;
  action?: string;
}

const RETENTION_BASE = "/api/v1/events/retention-rules";

export async function fetchRetentionRules(): Promise<ApiResponse<EventRetentionRuleRecord[]>> {
  const res = await serverClient.get<any>(RETENTION_BASE);
  return {
    status: "success",
    request_id: res?.request_id || "",
    data: Array.isArray(res) ? res : (res?.data || []),
    message: res?.message || "Retention rules retrieved successfully",
  };
}

export async function createRetentionRule(
  payload: CreateRetentionRulePayload
): Promise<ApiResponse<EventRetentionRuleRecord>> {
  const res = await serverClient.post<any>(RETENTION_BASE, payload);
  return {
    status: "success",
    request_id: res?.request_id || "",
    data: res?.data !== undefined ? res.data : res,
    message: res?.message || "Retention rule created successfully",
  };
}

export async function updateRetentionRule(
  ruleId: string,
  payload: UpdateRetentionRulePayload
): Promise<ApiResponse<EventRetentionRuleRecord>> {
  const res = await serverClient.put<any>(`${RETENTION_BASE}/${ruleId}`, payload);
  return {
    status: "success",
    request_id: res?.request_id || "",
    data: res?.data !== undefined ? res.data : res,
    message: res?.message || "Retention rule updated successfully",
  };
}

export async function deleteRetentionRule(ruleId: string): Promise<ApiResponse<any>> {
  const res = await serverClient.delete<any>(`${RETENTION_BASE}/${ruleId}`);
  return {
    status: "success",
    request_id: res?.request_id || "",
    data: res?.data !== undefined ? res.data : res,
    message: res?.message || "Retention rule deleted successfully",
  };
}

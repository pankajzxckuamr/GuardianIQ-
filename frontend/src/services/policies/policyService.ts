/* src/services/policies/policyService.ts */
import serverClient from "../shared/apiClient";
import type { ApiResponse } from "../registry/registryTypes";
import type {
  Policy,
  PolicyVersion,
  PolicyBinding,
  EffectiveBinding,
  PolicyCreatePayload,
  PolicyBindingCreatePayload,
} from "../../types/policy";

const POLICIES_BASE = "/api/v1/policies";
const BINDINGS_BASE = "/api/v1/policy-bindings";

export async function fetchPolicies(
  category?: string,
  status?: string
): Promise<ApiResponse<Policy[]>> {
  const params: Record<string, string> = {};
  if (category) params.category = category;
  if (status) params.status = status;

  const res = await serverClient.get<any>(POLICIES_BASE, { params });
  return {
    status: "success",
    request_id: res.request_id || "",
    data: res.data || [],
    message: res.message || "Policies retrieved successfully",
  };
}

export async function fetchPolicyDetails(policyId: string): Promise<ApiResponse<Policy>> {
  const res = await serverClient.get<any>(`${POLICIES_BASE}/${policyId}`);
  return {
    status: "success",
    request_id: res.request_id || "",
    data: res.data,
    message: res.message || "Policy retrieved successfully",
  };
}

export async function fetchPolicyVersions(policyId: string): Promise<ApiResponse<PolicyVersion[]>> {
  const res = await serverClient.get<any>(`${POLICIES_BASE}/${policyId}/versions`);
  return {
    status: "success",
    request_id: res.request_id || "",
    data: res.data || [],
    message: res.message || "Policy versions retrieved successfully",
  };
}

export async function createPolicy(payload: PolicyCreatePayload): Promise<ApiResponse<Policy>> {
  const res = await serverClient.post<any>(POLICIES_BASE, payload);
  return {
    status: "success",
    request_id: res.request_id || "",
    data: res.data,
    message: res.message || "Policy created successfully",
  };
}

export async function activatePolicyVersion(
  policyId: string,
  versionId: string
): Promise<ApiResponse<{ id: string; version_number: number; status: string }>> {
  const res = await serverClient.post<any>(
    `${POLICIES_BASE}/${policyId}/versions/${versionId}/activate`
  );
  return {
    status: "success",
    request_id: res.request_id || "",
    data: res.data,
    message: res.message || "Policy version activated successfully",
  };
}

export async function fetchPolicyBindings(
  policyId?: string,
  targetType?: string,
  targetId?: string
): Promise<ApiResponse<PolicyBinding[]>> {
  const params: Record<string, string> = {};
  if (policyId) params.policy_id = policyId;
  if (targetType) params.target_type = targetType;
  if (targetId) params.target_id = targetId;

  const res = await serverClient.get<any>(BINDINGS_BASE, { params });
  return {
    status: "success",
    request_id: res.request_id || "",
    data: res.data || [],
    message: res.message || "Policy bindings retrieved successfully",
  };
}

export async function createPolicyBinding(
  payload: PolicyBindingCreatePayload
): Promise<ApiResponse<PolicyBinding>> {
  const res = await serverClient.post<any>(BINDINGS_BASE, payload);
  return {
    status: "success",
    request_id: res.request_id || "",
    data: res.data,
    message: res.message || "Policy binding created successfully",
  };
}

export async function revokePolicyBinding(
  bindingId: string,
  reason?: string
): Promise<ApiResponse<{ id: string; status: string }>> {
  const res = await serverClient.post<any>(`${BINDINGS_BASE}/${bindingId}/revoke`, { reason });
  return {
    status: "success",
    request_id: res.request_id || "",
    data: res.data,
    message: res.message || "Policy binding revoked successfully",
  };
}

export async function fetchEffectiveBindings(
  targetType: string,
  targetId: string
): Promise<ApiResponse<EffectiveBinding[]>> {
  const res = await serverClient.get<any>(`${BINDINGS_BASE}/effective`, {
    params: { target_type: targetType, target_id: targetId },
  });
  return {
    status: "success",
    request_id: res.request_id || "",
    data: res.data || [],
    message: res.message || "Effective bindings resolved successfully",
  };
}

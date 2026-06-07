/* src/services/registry/registryService.ts */

import serverClient from "../shared/apiClient";
import type {
  ApiResponse,
  ListResponse,
  RegistrySummary,
  AIModel,
  AIAgent,
  Tool,
  Workflow,
  GuardianUser,
  RegistryRole,
  RegistryDepartment,
  DataSource,
  RegistryRelationship,
  RegistryAuditEvent,
  SearchResults
} from "./registryTypes";

const BASE_PATH = "/api/registry";

// Helper to wrap the decentralized client's response into the expected ApiResponse envelope
async function wrapResponse<T>(apiCall: Promise<T>): Promise<ApiResponse<T>> {
  try {
    const data = await apiCall;
    return {
      status: "success",
      request_id: "",
      data,
      message: "Operation completed successfully"
    };
  } catch (error: any) {
    // Handle errors by catching and rethrowing with the message from response
    throw new Error(error.message || "An unexpected error occurred");
  }
}

// Summary
export function getRegistrySummary(): Promise<ApiResponse<RegistrySummary>> {
  return wrapResponse<RegistrySummary>(
    serverClient.get(`${BASE_PATH}/summary`)
  );
}

// AI Models
export function listModels(params?: any): Promise<ApiResponse<ListResponse<AIModel>>> {
  return wrapResponse<ListResponse<AIModel>>(
    serverClient.get(`${BASE_PATH}/models`, { params })
  );
}

export function createModel(payload: any): Promise<ApiResponse<AIModel>> {
  return wrapResponse<AIModel>(
    serverClient.post(`${BASE_PATH}/models`, payload)
  );
}

export function getModel(id: string): Promise<ApiResponse<AIModel>> {
  return wrapResponse<AIModel>(
    serverClient.get(`${BASE_PATH}/models/${id}`)
  );
}

export function updateModel(id: string, payload: any): Promise<ApiResponse<AIModel>> {
  return wrapResponse<AIModel>(
    serverClient.put(`${BASE_PATH}/models/${id}`, payload)
  );
}

export function changeModelStatus(id: string, status: string, reason?: string): Promise<ApiResponse<AIModel>> {
  return wrapResponse<AIModel>(
    serverClient.patch(`${BASE_PATH}/models/${id}/status`, { status, reason })
  );
}

export function deleteModel(id: string): Promise<ApiResponse<void>> {
  return wrapResponse<void>(
    serverClient.delete(`${BASE_PATH}/models/${id}`)
  );
}

// AI Agents
export function listAgents(params?: any): Promise<ApiResponse<ListResponse<AIAgent>>> {
  return wrapResponse<ListResponse<AIAgent>>(
    serverClient.get(`${BASE_PATH}/agents`, { params })
  );
}

export function createAgent(payload: any): Promise<ApiResponse<AIAgent>> {
  return wrapResponse<AIAgent>(
    serverClient.post(`${BASE_PATH}/agents`, payload)
  );
}

export function getAgent(id: string): Promise<ApiResponse<AIAgent>> {
  return wrapResponse<AIAgent>(
    serverClient.get(`${BASE_PATH}/agents/${id}`)
  );
}

export function updateAgent(id: string, payload: any): Promise<ApiResponse<AIAgent>> {
  return wrapResponse<AIAgent>(
    serverClient.put(`${BASE_PATH}/agents/${id}`, payload)
  );
}

export function changeAgentStatus(id: string, status: string, reason?: string): Promise<ApiResponse<AIAgent>> {
  return wrapResponse<AIAgent>(
    serverClient.patch(`${BASE_PATH}/agents/${id}/status`, { status, reason })
  );
}

export function deleteAgent(id: string): Promise<ApiResponse<void>> {
  return wrapResponse<void>(
    serverClient.delete(`${BASE_PATH}/agents/${id}`)
  );
}

// Tools
export function listTools(params?: any): Promise<ApiResponse<ListResponse<Tool>>> {
  return wrapResponse<ListResponse<Tool>>(
    serverClient.get(`${BASE_PATH}/tools`, { params })
  );
}

export function createTool(payload: any): Promise<ApiResponse<Tool>> {
  return wrapResponse<Tool>(
    serverClient.post(`${BASE_PATH}/tools`, payload)
  );
}

export function getTool(id: string): Promise<ApiResponse<Tool>> {
  return wrapResponse<Tool>(
    serverClient.get(`${BASE_PATH}/tools/${id}`)
  );
}

export function updateTool(id: string, payload: any): Promise<ApiResponse<Tool>> {
  return wrapResponse<Tool>(
    serverClient.put(`${BASE_PATH}/tools/${id}`, payload)
  );
}

export function changeToolStatus(id: string, status: string, reason?: string): Promise<ApiResponse<Tool>> {
  return wrapResponse<Tool>(
    serverClient.patch(`${BASE_PATH}/tools/${id}/status`, { status, reason })
  );
}

export function deleteTool(id: string): Promise<ApiResponse<void>> {
  return wrapResponse<void>(
    serverClient.delete(`${BASE_PATH}/tools/${id}`)
  );
}

// Workflows
export function listWorkflows(params?: any): Promise<ApiResponse<ListResponse<Workflow>>> {
  return wrapResponse<ListResponse<Workflow>>(
    serverClient.get(`${BASE_PATH}/workflows`, { params })
  );
}

export function createWorkflow(payload: any): Promise<ApiResponse<Workflow>> {
  return wrapResponse<Workflow>(
    serverClient.post(`${BASE_PATH}/workflows`, payload)
  );
}

export function getWorkflow(id: string): Promise<ApiResponse<Workflow>> {
  return wrapResponse<Workflow>(
    serverClient.get(`${BASE_PATH}/workflows/${id}`)
  );
}

export function updateWorkflow(id: string, payload: any): Promise<ApiResponse<Workflow>> {
  return wrapResponse<Workflow>(
    serverClient.put(`${BASE_PATH}/workflows/${id}`, payload)
  );
}

export function changeWorkflowStatus(id: string, status: string, reason?: string): Promise<ApiResponse<Workflow>> {
  return wrapResponse<Workflow>(
    serverClient.patch(`${BASE_PATH}/workflows/${id}/status`, { status, reason })
  );
}

export function approveWorkflow(id: string): Promise<ApiResponse<Workflow>> {
  return wrapResponse<Workflow>(
    serverClient.post(`${BASE_PATH}/workflows/${id}/approve`)
  );
}

export function rejectWorkflow(id: string): Promise<ApiResponse<Workflow>> {
  return wrapResponse<Workflow>(
    serverClient.post(`${BASE_PATH}/workflows/${id}/reject`)
  );
}

export function deleteWorkflow(id: string): Promise<ApiResponse<void>> {
  return wrapResponse<void>(
    serverClient.delete(`${BASE_PATH}/workflows/${id}`)
  );
}

// Data Sources
export function listDataSources(params?: any): Promise<ApiResponse<ListResponse<DataSource>>> {
  return wrapResponse<ListResponse<DataSource>>(
    serverClient.get(`${BASE_PATH}/data-sources`, { params })
  );
}

export function createDataSource(payload: any): Promise<ApiResponse<DataSource>> {
  return wrapResponse<DataSource>(
    serverClient.post(`${BASE_PATH}/data-sources`, payload)
  );
}

export function getDataSource(id: string): Promise<ApiResponse<DataSource>> {
  return wrapResponse<DataSource>(
    serverClient.get(`${BASE_PATH}/data-sources/${id}`)
  );
}

export function updateDataSource(id: string, payload: any): Promise<ApiResponse<DataSource>> {
  return wrapResponse<DataSource>(
    serverClient.put(`${BASE_PATH}/data-sources/${id}`, payload)
  );
}

export function changeDataSourceStatus(id: string, status: string, reason?: string): Promise<ApiResponse<DataSource>> {
  return wrapResponse<DataSource>(
    serverClient.patch(`${BASE_PATH}/data-sources/${id}/status`, { status, reason })
  );
}

export function deleteDataSource(id: string): Promise<ApiResponse<void>> {
  return wrapResponse<void>(
    serverClient.delete(`${BASE_PATH}/data-sources/${id}`)
  );
}

// Departments
export function listDepartments(params?: any): Promise<ApiResponse<ListResponse<RegistryDepartment>>> {
  return wrapResponse<ListResponse<RegistryDepartment>>(
    serverClient.get(`${BASE_PATH}/departments`, { params })
  );
}

export function createDepartment(payload: any): Promise<ApiResponse<RegistryDepartment>> {
  return wrapResponse<RegistryDepartment>(
    serverClient.post(`${BASE_PATH}/departments`, payload)
  );
}

export function getDepartment(id: string): Promise<ApiResponse<RegistryDepartment>> {
  return wrapResponse<RegistryDepartment>(
    serverClient.get(`${BASE_PATH}/departments/${id}`)
  );
}

export function updateDepartment(id: string, payload: any): Promise<ApiResponse<RegistryDepartment>> {
  return wrapResponse<RegistryDepartment>(
    serverClient.put(`${BASE_PATH}/departments/${id}`, payload)
  );
}

export function changeDepartmentStatus(id: string, status: string, reason?: string): Promise<ApiResponse<RegistryDepartment>> {
  return wrapResponse<RegistryDepartment>(
    serverClient.patch(`${BASE_PATH}/departments/${id}/status`, { status, reason })
  );
}

export function deleteDepartment(id: string): Promise<ApiResponse<void>> {
  return wrapResponse<void>(
    serverClient.delete(`${BASE_PATH}/departments/${id}`)
  );
}

// Users
export function listUsers(params?: any): Promise<ApiResponse<ListResponse<GuardianUser>>> {
  return wrapResponse<ListResponse<GuardianUser>>(
    serverClient.get(`${BASE_PATH}/users`, { params })
  );
}

export function createUser(payload: any): Promise<ApiResponse<GuardianUser>> {
  return wrapResponse<GuardianUser>(
    serverClient.post(`${BASE_PATH}/users`, payload)
  );
}

export function getUser(id: string): Promise<ApiResponse<GuardianUser>> {
  return wrapResponse<GuardianUser>(
    serverClient.get(`${BASE_PATH}/users/${id}`)
  );
}

export function updateUser(id: string, payload: any): Promise<ApiResponse<GuardianUser>> {
  return wrapResponse<GuardianUser>(
    serverClient.put(`${BASE_PATH}/users/${id}`, payload)
  );
}

export function changeUserStatus(id: string, status: string, reason?: string): Promise<ApiResponse<GuardianUser>> {
  return wrapResponse<GuardianUser>(
    serverClient.patch(`${BASE_PATH}/users/${id}/status`, { status, reason })
  );
}

export function deleteUser(id: string): Promise<ApiResponse<void>> {
  return wrapResponse<void>(
    serverClient.delete(`${BASE_PATH}/users/${id}`)
  );
}

// Roles
export function listRoles(params?: any): Promise<ApiResponse<ListResponse<RegistryRole>>> {
  return wrapResponse<ListResponse<RegistryRole>>(
    serverClient.get(`${BASE_PATH}/roles`, { params })
  );
}

export function createRole(payload: any): Promise<ApiResponse<RegistryRole>> {
  return wrapResponse<RegistryRole>(
    serverClient.post(`${BASE_PATH}/roles`, payload)
  );
}

export function getRole(id: string): Promise<ApiResponse<RegistryRole>> {
  return wrapResponse<RegistryRole>(
    serverClient.get(`${BASE_PATH}/roles/${id}`)
  );
}

export function updateRole(id: string, payload: any): Promise<ApiResponse<RegistryRole>> {
  return wrapResponse<RegistryRole>(
    serverClient.put(`${BASE_PATH}/roles/${id}`, payload)
  );
}

export function changeRoleStatus(id: string, status: string, reason?: string): Promise<ApiResponse<RegistryRole>> {
  return wrapResponse<RegistryRole>(
    serverClient.patch(`${BASE_PATH}/roles/${id}/status`, { status, reason })
  );
}

export function deleteRole(id: string): Promise<ApiResponse<void>> {
  return wrapResponse<void>(
    serverClient.delete(`${BASE_PATH}/roles/${id}`)
  );
}

// Relationships
export function createRelationship(payload: any): Promise<ApiResponse<RegistryRelationship>> {
  return wrapResponse<RegistryRelationship>(
    serverClient.post(`${BASE_PATH}/relationships`, payload)
  );
}

export function listRelationships(entityType: string, entityId: string): Promise<ApiResponse<RegistryRelationship[]>> {
  return wrapResponse<RegistryRelationship[]>(
    serverClient.get(`${BASE_PATH}/relationships`, { params: { entity_type: entityType, entity_id: entityId } })
  );
}

export function deleteRelationship(id: string): Promise<ApiResponse<void>> {
  return wrapResponse<void>(
    serverClient.delete(`${BASE_PATH}/relationships/${id}`)
  );
}

// Audit Trail
export function getAuditTrail(entityType: string, entityId: string, params?: any): Promise<ApiResponse<ListResponse<RegistryAuditEvent>>> {
  return wrapResponse<ListResponse<RegistryAuditEvent>>(
    serverClient.get(`${BASE_PATH}/audit/${entityType}/${entityId}`, { params })
  );
}

// Global Search
export function globalSearch(q: string): Promise<ApiResponse<SearchResults>> {
  return wrapResponse<SearchResults>(
    serverClient.get(`${BASE_PATH}/search`, { params: { q } })
  );
}

// Dropdown Lookups
export function getDepartmentsLookup(): Promise<ApiResponse<{ id: string; department_name: string; department_code: string; }[]>> {
  return wrapResponse<{ id: string; department_name: string; department_code: string; }[]>(
    serverClient.get(`${BASE_PATH}/departments/lookup`)
  );
}

export function getUsersLookup(): Promise<ApiResponse<{ id: string; full_name: string; email: string; }[]>> {
  return wrapResponse<{ id: string; full_name: string; email: string; }[]>(
    serverClient.get(`${BASE_PATH}/users/lookup`)
  );
}

export function getRolesLookup(): Promise<ApiResponse<{ id: string; role_name: string; role_code: string; }[]>> {
  return wrapResponse<{ id: string; role_name: string; role_code: string; }[]>(
    serverClient.get(`${BASE_PATH}/roles/lookup`)
  );
}

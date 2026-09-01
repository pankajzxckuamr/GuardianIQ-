import apiClient from '../services/shared/apiClient';


export const scheduleApi = {
  list: (params?: Record<string, any>) => apiClient.get('/api/v1/workflow-scheduler/schedules', { params }),
  create: (body: any) => apiClient.post('/api/v1/workflow-scheduler/schedules', body),
  validateUniqueness: (body: any) => apiClient.post('/api/v1/workflow-scheduler/validate-uniqueness', body),
  getById: (id: string) => apiClient.get(`/api/v1/workflow-scheduler/schedules/${id}`),
  update: (id: string, body: any) => apiClient.put(`/api/v1/workflow-scheduler/schedules/${id}`, body),
  submit: (id: string) => apiClient.post(`/api/v1/workflow-scheduler/schedules/${id}/submit`),
  activate: (id: string, body?: any) => apiClient.post(`/api/v1/workflow-scheduler/schedules/${id}/activate`, body),
  reject: (id: string, body: any) => apiClient.post(`/api/v1/workflow-scheduler/schedules/${id}/reject`, body),
  pause: (id: string) => apiClient.post(`/api/v1/workflow-scheduler/schedules/${id}/pause`),
  resume: (id: string) => apiClient.post(`/api/v1/workflow-scheduler/schedules/${id}/resume`),
  retire: (id: string) => apiClient.post(`/api/v1/workflow-scheduler/schedules/${id}/retire`),
  runNow: (id: string) => apiClient.post(`/api/v1/workflow-scheduler/schedules/${id}/run-now`),
  getApprovals: (id: string) => apiClient.get(`/api/v1/workflow-scheduler/schedules/${id}/approvals`),
  getHistory: (id: string) => apiClient.get(`/api/v1/workflow-scheduler/schedules/${id}/history`),
  decideApproval: (approvalId: string, body: { decision: string, reason: string }) => apiClient.post(`/api/v1/schedule-approvals/${approvalId}/decide`, body),
  getApprovalMetrics: () => apiClient.get('/api/v1/schedule-approvals/metrics/today'),
  getDepartmentUsers: (departmentIdOrCode: string) => apiClient.get(`/api/v1/departments/${departmentIdOrCode}/users`),
  reassignApproval: (body: { schedule_id: string, old_user_id: string, new_user_id: string }) => apiClient.post('/api/v1/schedule-approvals/reassign', body),
};

export const runApi = {
  list: (params?: Record<string, any>) => apiClient.get('/api/v1/workflow-runs', { params }),
  getById: (runId: string) => apiClient.get(`/api/v1/workflow-runs/${runId}`),
  getSteps: (runId: string) => apiClient.get(`/api/v1/workflow-runs/${runId}/steps`),
  getOutputs: (runId: string) => apiClient.get(`/api/v1/workflow-runs/${runId}/outputs`),
  cancel: (runId: string) => apiClient.post(`/api/v1/workflow-runs/${runId}/cancel`),
};

export const notificationApi = {
  list: (params?: Record<string, any>) => apiClient.get('/api/v1/workflow-notifications', { params }),
  markRead: (id: string) => apiClient.put(`/api/v1/workflow-notifications/${id}/read`),
  acknowledge: (id: string) => apiClient.put(`/api/v1/workflow-notifications/${id}/acknowledge`),
};

export const auditApi = {
  getTimeline: (entityType: string, entityId: string) => apiClient.get('/api/v1/audit/events', { params: { entity_type: entityType, entity_id: entityId } }),
};

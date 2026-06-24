<<<<<<< HEAD
import { storage } from '../utils/storage';

const envelope = async <T>(res: Response): Promise<T> => {
  const json = await res.json();
  if (json.status !== 'success') throw new Error(json.message ?? 'API error');
  return json.data;
};

const getAuthHeaders = () => {
  const token = storage.get<string>('guardianiq_access_token');
  return {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {})
  };
};
=======
import apiClient from '../services/shared/apiClient';
>>>>>>> 1a84385 (Update Phase 2 workflow scheduling and approval queue)

export const scheduleApi = {
  list: (params?: Record<string, any>) => apiClient.get('/api/v1/workflow-scheduler/schedules', { params }),
  create: (body: any) => apiClient.post('/api/v1/workflow-scheduler/schedules', body),
  getById: (id: string) => apiClient.get(`/api/v1/workflow-scheduler/schedules/${id}`),
  update: (id: string, body: any) => apiClient.put(`/api/v1/workflow-scheduler/schedules/${id}`, body),
  submit: (id: string) => apiClient.post(`/api/v1/workflow-scheduler/schedules/${id}/submit`),
  activate: (id: string) => apiClient.post(`/api/v1/workflow-scheduler/schedules/${id}/activate`),
  pause: (id: string) => apiClient.post(`/api/v1/workflow-scheduler/schedules/${id}/pause`),
  resume: (id: string) => apiClient.post(`/api/v1/workflow-scheduler/schedules/${id}/resume`),
  retire: (id: string) => apiClient.post(`/api/v1/workflow-scheduler/schedules/${id}/retire`),
  runNow: (id: string) => apiClient.post(`/api/v1/workflow-scheduler/schedules/${id}/run-now`),
  getApprovals: (id: string) => apiClient.get(`/api/v1/workflow-scheduler/schedules/${id}/approvals`),
  getHistory: (id: string) => apiClient.get(`/api/v1/workflow-scheduler/schedules/${id}/history`),
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

import { storage } from '../utils/storage';

const envelope = async <T>(res: Response): Promise<T> => {
  const json = await res.json();
  if (!json.success) throw new Error(json.error ?? 'API error');
  return json.data;
};

const getAuthHeaders = () => {
  const token = storage.get<string>('guardianiq_access_token');
  return {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {})
  };
};

export const scheduleApi = {
  list: (params?: Record<string, any>) => 
    fetch(`/api/v1/workflow-scheduler/schedules?${new URLSearchParams(params as any)}`, { headers: getAuthHeaders() }).then(envelope),
  create: (body: any) => 
    fetch('/api/v1/workflow-scheduler/schedules', { method: 'POST', headers: getAuthHeaders(), body: JSON.stringify(body) }).then(envelope),
  getById: (id: string) => 
    fetch(`/api/v1/workflow-scheduler/schedules/${id}`, { headers: getAuthHeaders() }).then(envelope),
  update: (id: string, body: any) => 
    fetch(`/api/v1/workflow-scheduler/schedules/${id}`, { method: 'PUT', headers: getAuthHeaders(), body: JSON.stringify(body) }).then(envelope),
  submit: (id: string) => 
    fetch(`/api/v1/workflow-scheduler/schedules/${id}/submit`, { method: 'POST', headers: getAuthHeaders() }).then(envelope),
  activate: (id: string) => 
    fetch(`/api/v1/workflow-scheduler/schedules/${id}/activate`, { method: 'POST', headers: getAuthHeaders() }).then(envelope),
  pause: (id: string) => 
    fetch(`/api/v1/workflow-scheduler/schedules/${id}/pause`, { method: 'POST', headers: getAuthHeaders() }).then(envelope),
  resume: (id: string) => 
    fetch(`/api/v1/workflow-scheduler/schedules/${id}/resume`, { method: 'POST', headers: getAuthHeaders() }).then(envelope),
  retire: (id: string) => 
    fetch(`/api/v1/workflow-scheduler/schedules/${id}/retire`, { method: 'POST', headers: getAuthHeaders() }).then(envelope),
  runNow: (id: string) => 
    fetch(`/api/v1/workflow-scheduler/schedules/${id}/run-now`, { method: 'POST', headers: getAuthHeaders() }).then(envelope),
  getApprovals: (id: string) =>
    fetch(`/api/v1/workflow-scheduler/schedules/${id}/approvals`, { headers: getAuthHeaders() }).then(envelope),
  getHistory: (id: string) =>
    fetch(`/api/v1/workflow-scheduler/schedules/${id}/history`, { headers: getAuthHeaders() }).then(envelope),
};

export const runApi = {
  list: (params?: Record<string, any>) => 
    fetch(`/api/v1/workflow-runs?${new URLSearchParams(params as any)}`, { headers: getAuthHeaders() }).then(envelope),
  getById: (runId: string) => 
    fetch(`/api/v1/workflow-runs/${runId}`, { headers: getAuthHeaders() }).then(envelope),
  getSteps: (runId: string) => 
    fetch(`/api/v1/workflow-runs/${runId}/steps`, { headers: getAuthHeaders() }).then(envelope),
  getOutputs: (runId: string) => 
    fetch(`/api/v1/workflow-runs/${runId}/outputs`, { headers: getAuthHeaders() }).then(envelope),
  cancel: (runId: string) => 
    fetch(`/api/v1/workflow-runs/${runId}/cancel`, { method: 'POST', headers: getAuthHeaders() }).then(envelope),
};

export const notificationApi = {
  list: (params?: Record<string, any>) => 
    fetch(`/api/v1/workflow-notifications?${new URLSearchParams(params as any)}`, { headers: getAuthHeaders() }).then(envelope),
  markRead: (id: string) => 
    fetch(`/api/v1/workflow-notifications/${id}/read`, { method: 'PUT', headers: getAuthHeaders() }).then(envelope),
  acknowledge: (id: string) => 
    fetch(`/api/v1/workflow-notifications/${id}/acknowledge`, { method: 'PUT', headers: getAuthHeaders() }).then(envelope),
};

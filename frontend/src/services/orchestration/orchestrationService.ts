import api from '../shared/apiClient';
import { WorkflowExecution, ExecutionDetails } from './orchestrationTypes';

export const orchestrationService = {
  triggerExecution: async (workflowId: string, isDryRun: boolean = false) => {
    const response = await api.post(`/api/orchestration/${workflowId}/execute`, { is_dry_run: isDryRun });
    return response;
  },

  listExecutions: async (): Promise<WorkflowExecution[]> => {
    const response = await api.get('/api/orchestration/executions');
    return response;
  },

  getExecutionDetails: async (executionId: string): Promise<ExecutionDetails> => {
    const response = await api.get(`/api/orchestration/executions/${executionId}`);
    return response;
  }
};

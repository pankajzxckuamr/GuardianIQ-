import { useState, useEffect, useCallback } from 'react';
import { runApi, auditApi } from '../api/phase2Client';
import { WorkflowRunResponse, WorkflowRunStepResponse, WorkflowRunOutputResponse, AuditTimelineEvent } from '../types/phase2';
import { useToast } from './useToast';

export const useWorkflowRuns = (params: any) => {
  const [runs, setRuns] = useState<WorkflowRunResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState(0);

  const fetchRuns = useCallback(async () => {
    try {
      const res: any = await runApi.list(params);
      setRuns(res.items || []);
      setTotal(res.total || 0);
      setError(null);
    } catch (e: any) {
      setError(e.message || 'Failed to load runs');
    }
  }, [JSON.stringify(params)]);

  useEffect(() => {
    setLoading(true);
    fetchRuns().finally(() => setLoading(false));
  }, [fetchRuns]);

  // Auto-refresh logic for running status
  useEffect(() => {
    const hasRunning = runs.some(r => r.run_status === 'RUNNING' || r.run_status === 'QUEUED');
    if (!hasRunning) return undefined;
    const interval = setInterval(() => {
      fetchRuns();
    }, 10000); // 10 seconds
    return () => clearInterval(interval);
  }, [runs, fetchRuns]);

  return { runs, total, loading, error, refetch: fetchRuns };
};

export const useWorkflowRunDetail = (runId: string | undefined, enabled: boolean) => {
  const [run, setRun] = useState<WorkflowRunResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchRun = useCallback(async () => {
    if (!runId || !enabled) return;
    try {
      const res = await runApi.getById(runId);
      setRun(res as WorkflowRunResponse);
      setError(null);
    } catch (e: any) {
      setError(e.message || 'Failed to load run details');
    }
  }, [runId, enabled]);

  useEffect(() => {
    setLoading(true);
    fetchRun().finally(() => setLoading(false));
  }, [fetchRun]);

  // Auto refresh every 5s if QUEUED or RUNNING
  useEffect(() => {
    if (!run || (run.run_status !== 'QUEUED' && run.run_status !== 'RUNNING')) return undefined;
    const interval = setInterval(() => fetchRun(), 5000);
    return () => clearInterval(interval);
  }, [run, fetchRun]);

  return { run, loading, error, setRun, refetch: fetchRun };
};

export const useRunSteps = (runId: string | undefined, enabled: boolean) => {
  const [steps, setSteps] = useState<WorkflowRunStepResponse[]>([]);
  
  const fetchSteps = useCallback(async () => {
    if (!runId || !enabled) return;
    try {
      const res = await runApi.getSteps(runId);
      setSteps((res as any)?.items || res || []);
    } catch (e) {
      console.error(e);
    }
  }, [runId, enabled]);

  useEffect(() => {
    fetchSteps();
  }, [fetchSteps]);

  // Auto refresh steps every 5s if there is any RUNNING or QUEUED steps
  useEffect(() => {
    const hasActiveSteps = steps.some(s => s.step_status === 'RUNNING' || s.step_status === 'QUEUED' || s.step_status === 'PENDING');
    if (!hasActiveSteps) return undefined;
    const interval = setInterval(() => fetchSteps(), 5000);
    return () => clearInterval(interval);
  }, [steps, fetchSteps]);

  return { steps, refetch: fetchSteps };
};

export const useRunOutputs = (runId: string | undefined, enabled: boolean) => {
  const [outputs, setOutputs] = useState<WorkflowRunOutputResponse[]>([]);
  const [error, setError] = useState<string | null>(null);
  
  const fetchOutputs = useCallback(async () => {
    if (!runId || !enabled) return;
    try {
      const res = await runApi.getOutputs(runId);
      setOutputs((res as any)?.items || res || []);
      setError(null);
    } catch (e: any) {
      console.error(e);
      if (e.response?.status === 403) {
         setError('Output not accessible. Insufficient permissions.');
      } else {
         setError(e.message || 'Failed to fetch outputs');
      }
    }
  }, [runId, enabled]);

  useEffect(() => {
    fetchOutputs();
  }, [fetchOutputs]);

  return { outputs, error, refetch: fetchOutputs };
};

export const useRunAuditTimeline = (entityType: string, entityId: string | undefined) => {
  const [events, setEvents] = useState<AuditTimelineEvent[]>([]);

  const fetchEvents = useCallback(async () => {
    if (!entityId) return;
    try {
      const res = await auditApi.getTimeline(entityType, entityId);
      setEvents((res as any)?.items || res || []);
    } catch (e) {
      console.error(e);
    }
  }, [entityType, entityId]);

  useEffect(() => {
    fetchEvents();
  }, [fetchEvents]);

  return { events, refetch: fetchEvents };
};

export const useCancelRun = () => {
  const { showToast } = useToast();
  
  const cancelRun = async (runId: string, onSuccess?: () => void) => {
    try {
      await runApi.cancel(runId);
      showToast('Run cancelled successfully', 'success');
      if (onSuccess) onSuccess();
    } catch (e: any) {
      showToast(e.message || 'Failed to cancel run', 'error');
    }
  };

  return { cancelRun };
};

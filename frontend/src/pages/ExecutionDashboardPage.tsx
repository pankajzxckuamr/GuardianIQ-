import React, { useEffect, useState, useMemo } from 'react';
import { orchestrationService } from '../services/orchestration/orchestrationService';
import { WorkflowExecution, ExecutionDetails } from '../services/orchestration/orchestrationTypes';
import * as registryService from '../services/registry/registryService';
import styles from './ExecutionDashboardPage.module.css';
import { Loader2, PlayCircle, Clock, AlertTriangle, CheckCircle2, Eye, BrainCircuit, ShieldCheck, UserCheck, Wrench, Play } from 'lucide-react';
import { Modal } from '../components/common/Modal';
import { useToast } from '../hooks/useToast';
import {
  ReactFlow,
  Controls,
  Background,
  Handle,
  Position,
  Node,
  Edge,
  ReactFlowProvider,
  useReactFlow
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

// --- Flow Auto-Center and Zoom Helper ---
const FlowFitViewHelper: React.FC<{ nodes: any[] }> = ({ nodes }) => {
  const { fitView } = useReactFlow();
  useEffect(() => {
    if (nodes.length === 0) return;
    const timer = setTimeout(() => {
      fitView({ padding: 0.15, duration: 400 });
    }, 250);
    return () => clearTimeout(timer);
  }, [nodes, fitView]);
  return null;
};

// --- Custom Monitoring Nodes showing Execution Status ---

const getStatusStyles = (status: string) => {
  switch (status) {
    case 'COMPLETED':
      return {
        borderColor: '#10b981',
        boxShadow: '0 0 15px rgba(16, 185, 129, 0.4)',
        badgeColor: '#10b981',
        bgColor: 'rgba(16, 185, 129, 0.05)'
      };
    case 'RUNNING':
      return {
        borderColor: '#6366f1',
        boxShadow: '0 0 15px rgba(99, 102, 241, 0.6)',
        badgeColor: '#818cf8',
        bgColor: 'rgba(99, 102, 241, 0.05)'
      };
    case 'AWAITING_APPROVAL':
      return {
        borderColor: '#f59e0b',
        boxShadow: '0 0 15px rgba(245, 158, 11, 0.5)',
        badgeColor: '#fbbf24',
        bgColor: 'rgba(245, 158, 11, 0.05)'
      };
    case 'FAILED':
      return {
        borderColor: '#ef4444',
        boxShadow: '0 0 15px rgba(239, 68, 68, 0.5)',
        badgeColor: '#f87171',
        bgColor: 'rgba(239, 68, 68, 0.05)'
      };
    case 'REJECTED':
      return {
        borderColor: '#ef4444',
        boxShadow: '0 0 15px rgba(239, 68, 68, 0.4)',
        badgeColor: '#f87171',
        bgColor: 'rgba(239, 68, 68, 0.05)'
      };
    case 'REVOKED':
      return {
        borderColor: '#f43f5e',
        boxShadow: '0 0 15px rgba(244, 63, 94, 0.5)',
        badgeColor: '#fda4af',
        bgColor: 'rgba(244, 63, 94, 0.08)'
      };
    default:
      return {
        borderColor: 'rgba(255, 255, 255, 0.08)',
        boxShadow: 'none',
        badgeColor: '#94a3b8',
        bgColor: 'rgba(255, 255, 255, 0.01)'
      };
  }
};

const StartMonitorNode = ({ data }: { data: any }) => {
  const s = getStatusStyles(data.status);
  return (
    <div style={{
      padding: '6px 12px',
      borderRadius: '20px',
      background: 'linear-gradient(135deg, #1b2336, #0a0e17)',
      color: s.badgeColor,
      border: `2px solid ${s.borderColor}`,
      boxShadow: s.boxShadow,
      fontWeight: 'bold',
      display: 'flex',
      alignItems: 'center',
      gap: '6px',
      fontSize: '10px',
      letterSpacing: '0.5px'
    }}>
      <Play size={10} fill={s.badgeColor} />
      START
      <Handle type="source" position={Position.Right} style={{ background: s.borderColor, width: '6px', height: '6px' }} />
    </div>
  );
};

const EndMonitorNode = ({ data }: { data: any }) => {
  const s = getStatusStyles(data.status);
  return (
    <div style={{
      padding: '6px 12px',
      borderRadius: '20px',
      background: 'linear-gradient(135deg, #1b2336, #0a0e17)',
      color: s.badgeColor,
      border: `2px solid ${s.borderColor}`,
      boxShadow: s.boxShadow,
      fontWeight: 'bold',
      display: 'flex',
      alignItems: 'center',
      gap: '6px',
      fontSize: '10px',
      letterSpacing: '0.5px'
    }}>
      <Handle type="target" position={Position.Left} style={{ background: s.borderColor, width: '6px', height: '6px' }} />
      END
    </div>
  );
};

const StepMonitorNode = ({ data }: { data: any }) => {
  const s = getStatusStyles(data.status);
  return (
    <div style={{
      padding: '10px 14px',
      borderRadius: '12px',
      background: 'rgba(27, 35, 54, 0.95)',
      color: data.status === 'PENDING' ? '#64748b' : '#fff',
      border: `1.5px solid ${s.borderColor}`,
      boxShadow: s.boxShadow,
      width: '200px',
      position: 'relative'
    }}>
      <Handle type="target" position={Position.Left} style={{ background: s.borderColor }} />
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <div style={{ background: 'rgba(99, 102, 241, 0.15)', padding: '6px', borderRadius: '8px', color: s.badgeColor, display: 'flex', alignItems: 'center' }}>
          <BrainCircuit size={16} />
        </div>
        <div style={{ flex: 1, overflow: 'hidden' }}>
          <div style={{ fontSize: '9px', color: s.badgeColor, fontWeight: 'bold', textTransform: 'uppercase' }}>AI AGENT</div>
          <div style={{ fontSize: '12px', fontWeight: 'bold', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{data.step_name}</div>
        </div>
        {data.status === 'RUNNING' && <Loader2 size={12} className="animate-spin" style={{ color: '#6366f1' }} />}
        {data.status === 'COMPLETED' && <CheckCircle2 size={12} style={{ color: '#10b981' }} />}
        {data.status === 'FAILED' && <AlertTriangle size={12} style={{ color: '#ef4444' }} />}
      </div>
      <Handle type="source" position={Position.Right} style={{ background: s.borderColor }} />
    </div>
  );
};

const ApprovalMonitorNode = ({ data }: { data: any }) => {
  const s = getStatusStyles(data.status);
  return (
    <div style={{
      padding: '10px 14px',
      borderRadius: '12px',
      background: 'rgba(45, 34, 18, 0.95)',
      color: data.status === 'PENDING' ? '#64748b' : '#f59e0b',
      border: `1.5px solid ${s.borderColor}`,
      boxShadow: s.boxShadow,
      width: '200px',
      position: 'relative'
    }}>
      <Handle type="target" position={Position.Left} style={{ background: s.borderColor }} />
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <div style={{ background: 'rgba(245, 158, 11, 0.15)', padding: '6px', borderRadius: '8px', color: s.badgeColor, display: 'flex', alignItems: 'center' }}>
          <UserCheck size={16} />
        </div>
        <div style={{ flex: 1, overflow: 'hidden' }}>
          <div style={{ fontSize: '9px', color: s.badgeColor, fontWeight: 'bold', textTransform: 'uppercase' }}>HUMAN APPROVAL</div>
          <div style={{ fontSize: '12px', fontWeight: 'bold', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{data.step_name}</div>
        </div>
        {data.status === 'RUNNING' && <Loader2 size={12} className="animate-spin" style={{ color: '#6366f1' }} />}
        {data.status === 'AWAITING_APPROVAL' && <Clock size={12} className="animate-pulse" style={{ color: '#f59e0b' }} />}
        {data.status === 'COMPLETED' && <CheckCircle2 size={12} style={{ color: '#10b981' }} />}
        {data.status === 'FAILED' && <AlertTriangle size={12} style={{ color: '#ef4444' }} />}
      </div>
      <Handle type="source" position={Position.Right} style={{ background: s.borderColor }} />
    </div>
  );
};

const EvaluationMonitorNode = ({ data }: { data: any }) => {
  const s = getStatusStyles(data.status);
  return (
    <div style={{
      padding: '10px 14px',
      borderRadius: '12px',
      background: 'rgba(24, 45, 35, 0.95)',
      color: data.status === 'PENDING' ? '#64748b' : '#10b981',
      border: `1.5px solid ${s.borderColor}`,
      boxShadow: s.boxShadow,
      width: '200px',
      position: 'relative'
    }}>
      <Handle type="target" position={Position.Left} style={{ background: s.borderColor }} />
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <div style={{ background: 'rgba(16, 185, 129, 0.15)', padding: '6px', borderRadius: '8px', color: s.badgeColor, display: 'flex', alignItems: 'center' }}>
          <ShieldCheck size={16} />
        </div>
        <div style={{ flex: 1, overflow: 'hidden' }}>
          <div style={{ fontSize: '9px', color: s.badgeColor, fontWeight: 'bold', textTransform: 'uppercase' }}>EVALUATION</div>
          <div style={{ fontSize: '12px', fontWeight: 'bold', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{data.step_name}</div>
        </div>
        {data.status === 'RUNNING' && <Loader2 size={12} className="animate-spin" style={{ color: '#6366f1' }} />}
        {data.status === 'COMPLETED' && <CheckCircle2 size={12} style={{ color: '#10b981' }} />}
        {data.status === 'FAILED' && <AlertTriangle size={12} style={{ color: '#ef4444' }} />}
      </div>
      <Handle type="source" position={Position.Right} style={{ background: s.borderColor }} />
    </div>
  );
};

const ToolMonitorNode = ({ data }: { data: any }) => {
  const s = getStatusStyles(data.status);
  return (
    <div style={{
      padding: '10px 14px',
      borderRadius: '12px',
      background: 'rgba(21, 40, 59, 0.95)',
      color: data.status === 'PENDING' ? '#64748b' : '#06b6d4',
      border: `1.5px solid ${s.borderColor}`,
      boxShadow: s.boxShadow,
      width: '200px',
      position: 'relative'
    }}>
      <Handle type="target" position={Position.Left} style={{ background: s.borderColor }} />
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <div style={{ background: 'rgba(6, 182, 212, 0.15)', padding: '6px', borderRadius: '8px', color: s.badgeColor, display: 'flex', alignItems: 'center' }}>
          <Wrench size={16} />
        </div>
        <div style={{ flex: 1, overflow: 'hidden' }}>
          <div style={{ fontSize: '9px', color: s.badgeColor, fontWeight: 'bold', textTransform: 'uppercase' }}>TOOL CALL</div>
          <div style={{ fontSize: '12px', fontWeight: 'bold', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{data.step_name}</div>
        </div>
        {data.status === 'RUNNING' && <Loader2 size={12} className="animate-spin" style={{ color: '#6366f1' }} />}
        {data.status === 'COMPLETED' && <CheckCircle2 size={12} style={{ color: '#10b981' }} />}
        {data.status === 'FAILED' && <AlertTriangle size={12} style={{ color: '#ef4444' }} />}
      </div>
      <Handle type="source" position={Position.Right} style={{ background: s.borderColor }} />
    </div>
  );
};

// --- Main Execution Dashboard ---

export const ExecutionDashboardPage: React.FC = () => {
  const { showToast } = useToast();
  const [executions, setExecutions] = useState<WorkflowExecution[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [page, setPage] = useState<number>(1);
  const pageSize = 10;

  // Monitor Modal state
  const [selectedExecution, setSelectedExecution] = useState<WorkflowExecution | null>(null);
  const [details, setDetails] = useState<ExecutionDetails | null>(null);
  const [workflowSteps, setWorkflowSteps] = useState<any[]>([]);
  const [isStepsLoading, setIsStepsLoading] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isApproving, setIsApproving] = useState(false);
  const [isRejecting, setIsRejecting] = useState(false);
  const [isRevoking, setIsRevoking] = useState(false);

  // Reason Modal State
  const [isReasonModalOpen, setIsReasonModalOpen] = useState(false);
  const [reasonActionType, setReasonActionType] = useState<'REJECT' | 'REVOKE' | null>(null);
  const [reasonText, setReasonText] = useState('');

  // Load and poll all executions list
  useEffect(() => {
    const fetchExecutions = async () => {
      try {
        const data = await orchestrationService.listExecutions();
        setExecutions(data || []);
      } catch (error) {
        console.error('Failed to fetch executions:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchExecutions();
    const interval = setInterval(fetchExecutions, 5000);
    return () => clearInterval(interval);
  }, []);

  // Poll details of selected execution if modal is open
  useEffect(() => {
    if (!selectedExecution) {
      setDetails(null);
      setWorkflowSteps([]);
      setIsStepsLoading(false);
      return;
    }

    let isInitial = true;
    const fetchDetails = async () => {
      if (isInitial) setIsStepsLoading(true);
      try {
        const detailsData = await orchestrationService.getExecutionDetails(selectedExecution.id);
        setDetails(detailsData);

        // Fetch workflow details to build visual steps
        const wfRes = await registryService.getWorkflow(selectedExecution.workflow_id);
        let rawSteps = wfRes.data?.steps_json;
        if (typeof rawSteps === 'string') {
          try {
            rawSteps = JSON.parse(rawSteps);
          } catch {
            rawSteps = [];
          }
        }

        let parsedSteps: any[] = [];
        if (Array.isArray(rawSteps) && rawSteps.length > 0) {
          parsedSteps = rawSteps
            .filter((s: any) => {
              const name = (typeof s === 'string' ? s : s.step_name || s.name || '').toUpperCase();
              return name !== 'START' && name !== 'END';
            })
            .map((s: any, idx: number) => {
              if (typeof s === 'string') {
                return { id: `step_${idx}`, step_name: s, type: 'STEP' };
              }
              const stepName = s.step_name || s.name || `Step ${idx + 1}`;
              const lower = stepName.toLowerCase();
              const inferredType = s.type || (
                lower.includes('approval') || lower.includes('sign-off') ? 'APPROVAL' :
                lower.includes('evaluat') || lower.includes('audit') || lower.includes('check') || lower.includes('scan') ? 'EVALUATION' :
                lower.includes('api') || lower.includes('tool') || lower.includes('freeze') || lower.includes('stripe') ? 'TOOL' :
                'STEP'
              );
              return {
                id: s.id || `step_${idx}`,
                step_name: stepName,
                type: inferredType,
                description: s.description || '',
              };
            });
        }

        // Fallback: extract steps from execution logs if workflow steps_json was empty
        if (parsedSteps.length === 0 && detailsData?.logs && detailsData.logs.length > 0) {
          const stepLogs = detailsData.logs.filter((l: any) => l.event_type.includes('STEP'));
          if (stepLogs.length > 0) {
            const seen = new Set<string>();
            stepLogs.forEach((l: any, idx: number) => {
              const name = l.details || l.event_type;
              if (!seen.has(name)) {
                seen.add(name);
                parsedSteps.push({
                  id: `log_step_${idx}`,
                  step_name: name,
                  type: name.toLowerCase().includes('approval') ? 'APPROVAL' : 'STEP',
                  description: ''
                });
              }
            });
          }
        }

        setWorkflowSteps(parsedSteps);
      } catch (err) {
        console.error('Failed to load execution details:', err);
      } finally {
        if (isInitial) {
          setIsStepsLoading(false);
          isInitial = false;
        }
      }
    };

    fetchDetails();
    const interval = setInterval(fetchDetails, 2500);
    return () => clearInterval(interval);
  }, [selectedExecution]);

  const handleOpenDetails = (exec: WorkflowExecution) => {
    setSelectedExecution(exec);
    setIsModalOpen(true);
  };

  const handleCloseDetails = () => {
    setIsModalOpen(false);
    setSelectedExecution(null);
  };

  const handleApprove = async () => {
    if (!details) return;
    setIsApproving(true);
    try {
      await orchestrationService.approveExecution(details.id);
      showToast("Execution approved and resumed.", "success");
      
      // Refresh list and details
      const list = await orchestrationService.listExecutions();
      setExecutions(list || []);
      
      const updatedDetails = await orchestrationService.getExecutionDetails(details.id);
      setDetails(updatedDetails);
    } catch (err: any) {
      showToast(err.message || "Failed to approve execution.", "error");
    } finally {
      setIsApproving(false);
    }
  };

  const handleRejectClick = () => {
    setReasonActionType('REJECT');
    setReasonText('');
    setIsReasonModalOpen(true);
  };

  const executeReject = async () => {
    if (!details) return;
    setIsRejecting(true);
    setIsReasonModalOpen(false);
    try {
      await orchestrationService.rejectExecution(details.id, reasonText);
      showToast("Execution rejected.", "success");
      
      // Refresh list and details
      const list = await orchestrationService.listExecutions();
      setExecutions(list || []);
      
      const updatedDetails = await orchestrationService.getExecutionDetails(details.id);
      setDetails(updatedDetails);
    } catch (err: any) {
      showToast(err.message || "Failed to reject execution.", "error");
    } finally {
      setIsRejecting(false);
    }
  };

  const handleRevokeClick = () => {
    setReasonActionType('REVOKE');
    setReasonText('');
    setIsReasonModalOpen(true);
  };

  const executeRevoke = async () => {
    if (!details) return;
    setIsRevoking(true);
    setIsReasonModalOpen(false);
    try {
      await orchestrationService.revokeExecution(details.id, reasonText);
      showToast("Execution approval revoked successfully.", "success");
      
      // Refresh list and details
      const list = await orchestrationService.listExecutions();
      setExecutions(list || []);
      
      const updatedDetails = await orchestrationService.getExecutionDetails(details.id);
      setDetails(updatedDetails);
    } catch (err: any) {
      showToast(err.message || "Failed to revoke execution.", "error");
    } finally {
      setIsRevoking(false);
    }
  };

  const handleReasonSubmit = () => {
    if (reasonActionType === 'REJECT') {
      executeReject();
    } else if (reasonActionType === 'REVOKE') {
      executeRevoke();
    }
  };

  // Node styles configuration
  const nodeTypes = useMemo(() => ({
    START: StartMonitorNode,
    END: EndMonitorNode,
    STEP: StepMonitorNode,
    APPROVAL: ApprovalMonitorNode,
    EVALUATION: EvaluationMonitorNode,
    TOOL: ToolMonitorNode
  }), []);

  // Dynamically map execution state & logs into graph nodes
  const { flowNodes, flowEdges } = useMemo(() => {
    if (!workflowSteps.length) return { flowNodes: [], flowEdges: [] };

    const nodesList: Node[] = [];
    const edgesList: Edge[] = [];

    // Start Node Status
    let startStatus: 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED' | 'AWAITING_APPROVAL' = 'PENDING';
    if (details && details.logs && details.logs.length > 0) {
      startStatus = 'COMPLETED';
    }
    nodesList.push({
      id: 'start',
      type: 'START',
      position: { x: 50, y: 220 },
      data: { step_name: 'Start Trigger', status: startStatus }
    });

    let prevId = 'start';
    let currentX = 260;

    const getStepStatus = (stepName: string) => {
      if (!details) return 'PENDING';
      if (details.status === 'COMPLETED') return 'COMPLETED';

      const logs = details.logs || [];
      const hasCompleted = logs.some(l => l.event_type === 'STEP_COMPLETE' && l.details?.includes(stepName));
      if (hasCompleted) return 'COMPLETED';

      const hasStarted = logs.some(l => l.event_type === 'STEP_START' && l.details?.includes(stepName));
      const hasAwaitingApproval = logs.some(l => l.event_type === 'AWAITING_HUMAN_APPROVAL' && l.details?.includes(stepName));

      if (hasAwaitingApproval) {
        if (details.status === 'REJECTED') return 'FAILED';
        if (details.status === 'AWAITING_APPROVAL') return 'AWAITING_APPROVAL';
      }
      if (hasStarted) {
        if (details.status === 'FAILED') return 'FAILED';
        return 'RUNNING';
      }

      return 'PENDING';
    };

    workflowSteps.forEach((step, index) => {
      const nodeId = step.id || `node_${index}`;
      const status = getStepStatus(step.step_name);

      nodesList.push({
        id: nodeId,
        type: step.type || 'STEP',
        position: { x: currentX, y: 220 },
        data: {
          step_name: step.step_name,
          description: step.description || '',
          status: status
        }
      });

      edgesList.push({
        id: `e_${prevId}-${nodeId}`,
        source: prevId,
        target: nodeId,
        animated: status === 'RUNNING',
        style: {
          stroke: status === 'COMPLETED' ? '#10b981' : status === 'RUNNING' ? '#6366f1' : 'rgba(255,255,255,0.08)',
          strokeWidth: 2
        }
      });

      prevId = nodeId;
      currentX += 260;
    });

    // End Node Status
    let endStatus: string = 'PENDING';
    if (details) {
      if (details.status === 'COMPLETED') {
        endStatus = 'COMPLETED';
      } else if (details.status === 'REJECTED') {
        endStatus = 'REJECTED';
      } else if (details.status === 'REVOKED') {
        endStatus = 'REVOKED';
      } else if (details.status === 'FAILED') {
        endStatus = 'FAILED';
      }
    }
    nodesList.push({
      id: 'end',
      type: 'END',
      position: { x: currentX, y: 220 },
      data: { step_name: 'End Process', status: endStatus }
    });

    edgesList.push({
      id: `e_${prevId}-end`,
      source: prevId,
      target: 'end',
      animated: false,
      style: {
        stroke: endStatus === 'COMPLETED' ? '#10b981' : 'rgba(255,255,255,0.08)',
        strokeWidth: 2
      }
    });

    return { flowNodes: nodesList, flowEdges: edgesList };
  }, [workflowSteps, details]);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'COMPLETED': return <CheckCircle2 className={styles[`status-${status}`]} size={20} />;
      case 'RUNNING': return <Loader2 className={`animate-spin ${styles[`status-${status}`]}`} size={20} />;
      case 'FAILED': return <AlertTriangle className={styles[`status-${status}`]} size={20} />;
      case 'REJECTED': return <AlertTriangle className={styles[`status-${status}`]} size={20} />;
      case 'REVOKED': return <AlertTriangle className={styles[`status-${status}`]} size={20} />;
      case 'AWAITING_APPROVAL': return <Clock className={styles[`status-${status}`]} size={20} />;
      case 'PENDING': return <Clock className={styles[`status-${status}`]} size={20} />;
      default: return <PlayCircle size={20} />;
    }
  };

  return (
    <div className={styles.pageContainer}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '24px' }}>
        <header className={styles.header} style={{ marginBottom: 0 }}>
          <h1>Execution Dashboard</h1>
          <p>Monitor live and past AI workflow executions and agent activities.</p>
        </header>

        {!isLoading && executions.length > 0 && (
          <div style={{ display: 'flex', gap: '20px' }}>
            {/* Needs Approval Tile */}
            <div style={{
              background: 'linear-gradient(135deg, rgba(30, 41, 59, 0.7), rgba(15, 23, 42, 0.8))',
              border: '1px solid rgba(245, 158, 11, 0.3)',
              borderRadius: '12px',
              padding: '16px 20px',
              minWidth: '200px',
              boxShadow: '0 4px 20px rgba(245, 158, 11, 0.05)',
              display: 'flex',
              flexDirection: 'column'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#fbbf24', fontSize: '13px', fontWeight: 600, letterSpacing: '0.5px' }}>
                <Clock size={16} />
                NEEDS APPROVAL
              </div>
              <div style={{ fontSize: '32px', fontWeight: 700, color: '#fff', marginTop: '8px' }}>
                {executions.filter(e => e.status === 'AWAITING_APPROVAL').length}
              </div>
            </div>

            {/* Completed Tile */}
            <div style={{
              background: 'linear-gradient(135deg, rgba(30, 41, 59, 0.7), rgba(15, 23, 42, 0.8))',
              border: '1px solid rgba(16, 185, 129, 0.3)',
              borderRadius: '12px',
              padding: '16px 20px',
              minWidth: '200px',
              boxShadow: '0 4px 20px rgba(16, 185, 129, 0.05)',
              display: 'flex',
              flexDirection: 'column'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#34d399', fontSize: '13px', fontWeight: 600, letterSpacing: '0.5px' }}>
                <CheckCircle2 size={16} />
                COMPLETED
              </div>
              <div style={{ fontSize: '32px', fontWeight: 700, color: '#fff', marginTop: '8px' }}>
                {executions.filter(e => e.status === 'COMPLETED').length}
              </div>
            </div>
          </div>
        )}
      </div>

      {isLoading ? (
        <div className="flex justify-center p-12">
          <Loader2 className="animate-spin text-blue-500" size={32} />
        </div>
      ) : executions.length === 0 ? (
        <div className="text-center p-12 text-gray-500 border border-gray-700 rounded-lg">
          No workflow executions found. Trigger a workflow to see it here.
        </div>
      ) : (() => {
        const totalCount = executions.length;
        const totalPages = Math.ceil(totalCount / pageSize) || 1;
        const startRecord = totalCount === 0 ? 0 : (page - 1) * pageSize + 1;
        const endRecord = Math.min(page * pageSize, totalCount);
        const paginatedExecutions = executions.slice((page - 1) * pageSize, page * pageSize);

        return (
          <>
            <div className={styles.executionList}>
              {paginatedExecutions.map((execution) => (
                <div key={execution.id} className={styles.executionCard}>
                  <div className="flex items-center gap-4">
                    {getStatusIcon(execution.status)}
                    <div className={styles.cardInfo}>
                      <div className="flex items-center gap-3">
                        <span className="font-semibold text-white">Execution</span>
                        {execution.is_dry_run && (
                          <span className="px-2 py-0.5 text-xs bg-purple-500/20 text-purple-400 rounded">
                            DRY RUN
                          </span>
                        )}
                        <span className={`${styles.statusBadge} ${styles[`status-${execution.status}`]}`}>
                          {execution.status}
                        </span>
                      </div>
                      <div className={styles.workflowId}>
                        Workflow: <span style={{ color: '#fff', fontWeight: '600' }}>{execution.workflow_name || 'Unnamed Workflow'}</span>
                      </div>
                      <div style={{ fontSize: '11px', color: '#64748b', marginTop: '-2px' }}>
                        Workflow ID: {execution.workflow_id}
                      </div>
                      <div className="text-sm text-gray-400">
                        Started: {new Date(execution.started_at).toLocaleString()}
                      </div>
                    </div>
                  </div>
                  
                  <div className={styles.actions} style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '8px' }}>
                    <div style={{ fontSize: '12px', color: '#cbd5e1', fontWeight: 600, background: 'rgba(255,255,255,0.05)', padding: '4px 10px', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.1)' }}>
                      {execution.completed_steps || 0} / {execution.total_steps || 0} Steps
                    </div>
                    <button className={styles.viewButton} onClick={() => handleOpenDetails(execution)}>
                      <Eye size={14} style={{ marginRight: '6px', display: 'inline-block', verticalAlign: 'middle' }} />
                      View Details
                    </button>
                  </div>
                </div>
              ))}
            </div>

            {/* Executions Pagination Controls */}
            {totalCount > 0 && (
              <div style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                padding: "12px 16px",
                background: "rgba(15, 23, 42, 0.6)",
                border: "1px solid rgba(255, 255, 255, 0.08)",
                borderRadius: "8px",
                fontSize: "0.85rem",
                color: "#94a3b8",
                marginTop: "16px"
              }}>
                <div>
                  Showing <strong style={{ color: "#fff" }}>{startRecord}-{endRecord}</strong> of <strong style={{ color: "#fff" }}>{totalCount}</strong> executions
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                  <span>Page <strong style={{ color: "#fff" }}>{page}</strong> of <strong style={{ color: "#fff" }}>{totalPages}</strong></span>
                  <div style={{ display: "flex", gap: "6px" }}>
                    <button
                      type="button"
                      disabled={page <= 1}
                      onClick={() => setPage((prev) => Math.max(1, prev - 1))}
                      style={{
                        padding: "4px 12px",
                        borderRadius: "6px",
                        border: "1px solid rgba(255, 255, 255, 0.1)",
                        background: page <= 1 ? "rgba(255, 255, 255, 0.02)" : "rgba(255, 255, 255, 0.08)",
                        color: page <= 1 ? "#475569" : "#fff",
                        cursor: page <= 1 ? "not-allowed" : "pointer",
                        fontSize: "0.8rem",
                        fontWeight: 600
                      }}
                    >
                      Previous
                    </button>
                    <button
                      type="button"
                      disabled={page >= totalPages}
                      onClick={() => setPage((prev) => Math.min(totalPages, prev + 1))}
                      style={{
                        padding: "4px 12px",
                        borderRadius: "6px",
                        border: "1px solid rgba(255, 255, 255, 0.1)",
                        background: page >= totalPages ? "rgba(255, 255, 255, 0.02)" : "rgba(255, 255, 255, 0.08)",
                        color: page >= totalPages ? "#475569" : "#fff",
                        cursor: page >= totalPages ? "not-allowed" : "pointer",
                        fontSize: "0.8rem",
                        fontWeight: 600
                      }}
                    >
                      Next
                    </button>
                  </div>
                </div>
              </div>
            )}
          </>
        );
      })()}

      {/* Visual Execution Monitoring Modal */}
      {selectedExecution && (
        <Modal
          isOpen={isModalOpen}
          onClose={handleCloseDetails}
          title={`Execution Monitor: ${details?.workflow_name || selectedExecution.workflow_name || 'Unnamed Workflow'} (${selectedExecution.id})`}
          size="xl"
        >
          <div className={styles.modalContainer}>
            {/* Visual Canvas Board */}
            <div className={styles.graphSection}>
              <div className={styles.graphHeader}>
                <div className={styles.graphTitle}>WORKFLOW FLOW DIAGRAM</div>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <span className={`${styles.statusBadge} ${styles[`status-${details?.status || selectedExecution.status}`]}`}>
                    STATUS: {details?.status || selectedExecution.status}
                  </span>
                  {details?.is_dry_run && (
                    <span className="px-2 py-0.5 text-xs bg-purple-500/20 text-purple-400 rounded">
                      DRY RUN
                    </span>
                  )}
                </div>
              </div>

              <div className={styles.canvasWrapper}>
                {isStepsLoading ? (
                  <div style={{ display: 'flex', height: '100%', alignItems: 'center', justifyContent: 'center', color: '#64748b', fontSize: '13px' }}>
                    <Loader2 className="animate-spin" size={20} style={{ marginRight: '8px' }} />
                    Loading visual workflow steps...
                  </div>
                ) : workflowSteps.length > 0 ? (
                  <ReactFlowProvider>
                    <ReactFlow
                      nodes={flowNodes}
                      edges={flowEdges}
                      nodeTypes={nodeTypes}
                      fitView
                      fitViewOptions={{ padding: 0.15 }}
                      defaultEdgeOptions={{ style: { strokeWidth: 2 } }}
                      nodesConnectable={false}
                      nodesDraggable={false}
                      elementsSelectable={false}
                    >
                      <Background color="#0f172a" gap={20} size={1} />
                      <Controls />
                      <FlowFitViewHelper nodes={flowNodes} />
                    </ReactFlow>
                  </ReactFlowProvider>
                ) : (
                  <div style={{ display: 'flex', height: '100%', alignItems: 'center', justifyContent: 'center', color: '#64748b', fontSize: '13px', flexDirection: 'column', gap: '8px' }}>
                    <BrainCircuit size={28} style={{ color: '#475569' }} />
                    <span>No visual workflow steps configured for this workflow.</span>
                  </div>
                )}
              </div>
            </div>

            {/* Sidebar Details Panels */}
            <div className={styles.sidebarSection}>
              {/* Human Approval gate card */}
              {details?.status === 'AWAITING_APPROVAL' && (
                <div className={styles.approvalActions}>
                  <div className={styles.approvalTitle}>Human Approval Gate Awaiting Action</div>
                  <p style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                    A manual supervisor checkpoint has been reached. Please review governance criteria and sign off to proceed.
                  </p>
                  <div className={styles.approvalButtons}>
                    <button
                      className={styles.approveBtn}
                      onClick={handleApprove}
                      disabled={isApproving || isRejecting}
                    >
                      {isApproving ? 'Authorizing...' : 'Approve'}
                    </button>
                    <button
                      className={styles.rejectBtn}
                      onClick={handleRejectClick}
                      disabled={isApproving || isRejecting}
                    >
                      {isRejecting ? 'Rejecting...' : 'Reject'}
                    </button>
                  </div>
                </div>
              )}

              {details?.status === 'COMPLETED' && (workflowSteps.some(step => step.type === 'APPROVAL') || details?.logs?.some(log => log.event_type.includes('APPROVAL'))) && (
                <div className={styles.approvalActions} style={{ borderColor: 'rgba(244, 63, 94, 0.45)', background: 'linear-gradient(135deg, rgba(244, 63, 94, 0.08), rgba(244, 63, 94, 0.02))', animation: 'none' }}>
                  <div className={styles.approvalTitle} style={{ color: '#fda4af' }}>Approved Execution Actions</div>
                  <p style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                    This execution has finished successfully. You may revoke human approval to flag the execution if policy exceptions were identified post-run.
                  </p>
                  <div className={styles.approvalButtons}>
                    <button
                      className={styles.revokeBtn}
                      onClick={handleRevokeClick}
                      disabled={isRevoking}
                    >
                      {isRevoking ? 'Revoking...' : 'Revoke Human Approval'}
                    </button>
                  </div>
                </div>
              )}

              {/* Logs Timeline */}
              <div className={styles.panelCard}>
                <h3>EXECUTION LOGS</h3>
                <div className={styles.timeline}>
                  {details && details.logs && details.logs.length > 0 ? (
                    details.logs.map((log) => {
                      let dotColor = '#94a3b8';
                      if (log.event_type.includes('START') || log.event_type.includes('RUN')) dotColor = '#6366f1';
                      if (log.event_type.includes('COMPLETE') || log.event_type.includes('SUCCESS')) dotColor = '#10b981';
                      if (log.event_type.includes('FAIL') || log.event_type.includes('ERROR')) dotColor = '#ef4444';
                      if (log.event_type.includes('APPROVAL')) dotColor = '#f59e0b';

                      return (
                        <div key={log.id} className={styles.timelineItem}>
                          <div className={styles.timelineDot} style={{ backgroundColor: dotColor }} />
                          <div className={styles.timelineContent}>
                            <div style={{ fontWeight: '600', color: '#fff' }}>{log.event_type}</div>
                            <div style={{ color: '#94a3b8', marginTop: '2px' }}>{log.details}</div>
                            <div className={styles.timelineMeta}>
                              <span>{log.timestamp ? new Date(log.timestamp).toLocaleTimeString() : ''}</span>
                            </div>
                          </div>
                        </div>
                      );
                    })
                  ) : (
                    <div style={{ color: '#64748b', fontSize: '12px', padding: '12px 0' }}>
                      No execution logs generated yet.
                    </div>
                  )}
                </div>
              </div>

              {/* Security & Risk Findings */}
              <div className={styles.panelCard}>
                <h3>POLICY & SAFETY FINDINGS</h3>
                <div className={styles.findingsList}>
                  {details && details.findings && details.findings.length > 0 ? (
                    details.findings.map((finding) => (
                      <div key={finding.id} className={`${styles.findingItem} ${styles[`findingSeverity-${finding.severity}`]}`}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                          <span style={{ fontWeight: '700' }}>SEVERITY: {finding.severity}</span>
                          <span style={{ color: 'var(--text-muted)', fontSize: '10px' }}>
                            {finding.created_at ? new Date(finding.created_at).toLocaleTimeString() : ''}
                          </span>
                        </div>
                        <div style={{ color: '#fff', fontWeight: '500' }}>{finding.description}</div>
                        {finding.recommendation_text && (
                          <div style={{ color: 'var(--text-secondary)', fontSize: '11px', marginTop: '4px', borderTop: '1px dashed rgba(255,255,255,0.06)', paddingTop: '4px' }}>
                            <strong>Recommendation:</strong> {finding.recommendation_text}
                          </div>
                        )}
                      </div>
                    ))
                  ) : (
                    <div style={{ color: '#64748b', fontSize: '12px', padding: '12px 0' }}>
                      No security or compliance findings reported.
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </Modal>
      )}

      {/* Reason Modal for Reject/Revoke */}
      <Modal
        isOpen={isReasonModalOpen}
        onClose={() => setIsReasonModalOpen(false)}
        title={`Provide Reason for ${reasonActionType === 'REJECT' ? 'Rejection' : 'Revocation'}`}
        size="md"
      >
        <div style={{ padding: '20px' }}>
          <p style={{ color: 'var(--text-secondary)', marginBottom: '16px', fontSize: '14px' }}>
            Please enter a reason. This will be permanently recorded in the execution logs for audit purposes.
          </p>
          <textarea
            value={reasonText}
            onChange={(e) => setReasonText(e.target.value)}
            placeholder="Enter reason here..."
            style={{
              width: '100%',
              height: '100px',
              backgroundColor: 'rgba(15, 23, 42, 0.6)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              borderRadius: '8px',
              padding: '12px',
              color: '#fff',
              fontSize: '14px',
              resize: 'none',
              marginBottom: '20px'
            }}
          />
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
            <button
              onClick={() => setIsReasonModalOpen(false)}
              style={{
                padding: '8px 16px',
                borderRadius: '6px',
                background: 'transparent',
                color: '#94a3b8',
                border: '1px solid rgba(255,255,255,0.1)',
                cursor: 'pointer'
              }}
            >
              Cancel
            </button>
            <button
              onClick={handleReasonSubmit}
              disabled={!reasonText.trim()}
              style={{
                padding: '8px 16px',
                borderRadius: '6px',
                background: reasonActionType === 'REJECT' ? '#ef4444' : '#f43f5e',
                color: '#fff',
                border: 'none',
                cursor: reasonText.trim() ? 'pointer' : 'not-allowed',
                opacity: reasonText.trim() ? 1 : 0.5,
                fontWeight: 600
              }}
            >
              Submit {reasonActionType === 'REJECT' ? 'Rejection' : 'Revocation'}
            </button>
          </div>
        </div>
      </Modal>
    </div>
  );
};

export default ExecutionDashboardPage;

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  ReactFlow,
  Controls,
  Background,
  applyNodeChanges,
  applyEdgeChanges,
  addEdge,
  Handle,
  Position,
  NodeChange,
  EdgeChange,
  Connection,
  Edge,
  Node,
  NodeProps,
  ReactFlowProvider,
  useReactFlow
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { Play, BrainCircuit, ShieldCheck, UserCheck, Wrench } from 'lucide-react';
import * as registryService from '../../services/registry/registryService';

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

// --- Custom Node Components with Premium Glow and Styling ---

const StartNode = () => (
  <div style={{
    padding: '6px 12px',
    borderRadius: '20px',
    background: 'linear-gradient(135deg, #1b2336, #0a0e17)',
    color: '#10b981',
    border: '2px solid #10b981',
    boxShadow: '0 0 10px rgba(16, 185, 129, 0.25)',
    fontWeight: 'bold',
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
    fontSize: '10px',
    letterSpacing: '0.5px'
  }}>
    <Play size={10} fill="#10b981" />
    START
    <Handle type="source" position={Position.Right} style={{ background: '#10b981', width: '6px', height: '6px' }} />
  </div>
);

const EndNode = () => (
  <div style={{
    padding: '6px 12px',
    borderRadius: '20px',
    background: 'linear-gradient(135deg, #1b2336, #0a0e17)',
    color: '#ef4444',
    border: '2px solid #ef4444',
    boxShadow: '0 0 10px rgba(239, 68, 68, 0.25)',
    fontWeight: 'bold',
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
    fontSize: '10px',
    letterSpacing: '0.5px'
  }}>
    <Handle type="target" position={Position.Left} style={{ background: '#ef4444', width: '6px', height: '6px' }} />
    END
  </div>
);

const StepNode = ({ data }: NodeProps) => (
  <div style={{
    padding: '10px 14px',
    borderRadius: '12px',
    background: 'rgba(27, 35, 54, 0.9)',
    backdropFilter: 'blur(8px)',
    color: '#fff',
    border: '1.5px solid #6366f1',
    boxShadow: '0 4px 20px rgba(99, 102, 241, 0.15)',
    width: '200px',
    position: 'relative'
  }}>
    <Handle type="target" position={Position.Left} style={{ background: '#6366f1', width: '8px', height: '8px' }} />
    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
      <div style={{ background: 'rgba(99, 102, 241, 0.15)', padding: '6px', borderRadius: '8px', color: '#6366f1', display: 'flex', alignItems: 'center' }}>
        <BrainCircuit size={16} />
      </div>
      <div style={{ flex: 1, overflow: 'hidden' }}>
        <div style={{ fontSize: '9px', color: '#818cf8', fontWeight: 'bold', textTransform: 'uppercase', letterSpacing: '0.5px' }}>AI AGENT</div>
        <div style={{ fontSize: '12px', fontWeight: 'bold', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{data.step_name as string || 'New Agent'}</div>
      </div>
    </div>
    <Handle type="source" position={Position.Right} style={{ background: '#6366f1', width: '8px', height: '8px' }} />
  </div>
);

const ApprovalNode = ({ data }: NodeProps) => (
  <div style={{
    padding: '10px 14px',
    borderRadius: '12px',
    background: 'rgba(45, 34, 18, 0.9)',
    backdropFilter: 'blur(8px)',
    color: '#f59e0b',
    border: '1.5px solid #f59e0b',
    boxShadow: '0 4px 20px rgba(245, 158, 11, 0.15)',
    width: '200px',
    position: 'relative'
  }}>
    <Handle type="target" position={Position.Left} style={{ background: '#f59e0b', width: '8px', height: '8px' }} />
    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
      <div style={{ background: 'rgba(245, 158, 11, 0.15)', padding: '6px', borderRadius: '8px', color: '#f59e0b', display: 'flex', alignItems: 'center' }}>
        <UserCheck size={16} />
      </div>
      <div style={{ flex: 1, overflow: 'hidden' }}>
        <div style={{ fontSize: '9px', color: '#fbbf24', fontWeight: 'bold', textTransform: 'uppercase', letterSpacing: '0.5px' }}>HUMAN APPROVAL</div>
        <div style={{ fontSize: '12px', fontWeight: 'bold', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{data.step_name as string || 'New Approval'}</div>
      </div>
    </div>
    <Handle type="source" position={Position.Right} style={{ background: '#f59e0b', width: '8px', height: '8px' }} />
  </div>
);

const EvaluationNode = ({ data }: NodeProps) => (
  <div style={{
    padding: '10px 14px',
    borderRadius: '12px',
    background: 'rgba(24, 45, 35, 0.9)',
    backdropFilter: 'blur(8px)',
    color: '#10b981',
    border: '1.5px solid #10b981',
    boxShadow: '0 4px 20px rgba(16, 185, 129, 0.15)',
    width: '200px',
    position: 'relative'
  }}>
    <Handle type="target" position={Position.Left} style={{ background: '#10b981', width: '8px', height: '8px' }} />
    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
      <div style={{ background: 'rgba(16, 185, 129, 0.15)', padding: '6px', borderRadius: '8px', color: '#10b981', display: 'flex', alignItems: 'center' }}>
        <ShieldCheck size={16} />
      </div>
      <div style={{ flex: 1, overflow: 'hidden' }}>
        <div style={{ fontSize: '9px', color: '#34d399', fontWeight: 'bold', textTransform: 'uppercase', letterSpacing: '0.5px' }}>EVALUATION</div>
        <div style={{ fontSize: '12px', fontWeight: 'bold', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{data.step_name as string || 'New Evaluation'}</div>
      </div>
    </div>
    <Handle type="source" position={Position.Right} style={{ background: '#10b981', width: '8px', height: '8px' }} />
  </div>
);

const ToolNode = ({ data }: NodeProps) => (
  <div style={{
    padding: '10px 14px',
    borderRadius: '12px',
    background: 'rgba(21, 40, 59, 0.9)',
    backdropFilter: 'blur(8px)',
    color: '#06b6d4',
    border: '1.5px solid #06b6d4',
    boxShadow: '0 4px 20px rgba(6, 182, 212, 0.15)',
    width: '200px',
    position: 'relative'
  }}>
    <Handle type="target" position={Position.Left} style={{ background: '#06b6d4', width: '8px', height: '8px' }} />
    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
      <div style={{ background: 'rgba(6, 182, 212, 0.15)', padding: '6px', borderRadius: '8px', color: '#06b6d4', display: 'flex', alignItems: 'center' }}>
        <Wrench size={16} />
      </div>
      <div style={{ flex: 1, overflow: 'hidden' }}>
        <div style={{ fontSize: '9px', color: '#22d3ee', fontWeight: 'bold', textTransform: 'uppercase', letterSpacing: '0.5px' }}>TOOL INTEGRATION</div>
        <div style={{ fontSize: '12px', fontWeight: 'bold', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{data.step_name as string || 'New Tool'}</div>
      </div>
    </div>
    <Handle type="source" position={Position.Right} style={{ background: '#06b6d4', width: '8px', height: '8px' }} />
  </div>
);

// --- Main Canvas Component ---

export interface WorkflowStep {
  id?: string;
  type: string;
  step_name: string;
  description?: string;
}

interface WorkflowNodeCanvasProps {
  value: WorkflowStep[];
  onChange: (steps: WorkflowStep[]) => void;
}

const WorkflowNodeCanvas: React.FC<WorkflowNodeCanvasProps> = ({ value, onChange }) => {
  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);

  // Lookups lists from registry
  const [registryAgents, setRegistryAgents] = useState<any[]>([]);
  const [registryTools, setRegistryTools] = useState<any[]>([]);

  useEffect(() => {
    async function loadLookupAssets() {
      try {
        const [agentsRes, toolsRes] = await Promise.all([
          registryService.listAgents({ per_page: 100 }),
          registryService.listTools({ per_page: 100 })
        ]);
        if (agentsRes.data?.items) setRegistryAgents(agentsRes.data.items);
        if (toolsRes.data?.items) setRegistryTools(toolsRes.data.items);
      } catch (err) {
        console.error("Failed to load assets in visual canvas editor:", err);
      }
    }
    loadLookupAssets();
  }, []);

  const nodeTypes = useMemo(() => ({
    START: StartNode,
    END: EndNode,
    STEP: StepNode,
    APPROVAL: ApprovalNode,
    EVALUATION: EvaluationNode,
    TOOL: ToolNode
  }), []);

  // Deserialize incoming workflow steps
  useEffect(() => {
    if (nodes.length > 0) return;

    const initialNodes: Node[] = [];
    const initialEdges: Edge[] = [];

    initialNodes.push({
      id: 'start',
      type: 'START',
      position: { x: 50, y: 240 },
      data: { step_name: 'Start Trigger' },
      deletable: false,
    });

    let prevId = 'start';
    let currentX = 280;

    const steps = Array.isArray(value) ? value : [];

    steps.forEach((step, index) => {
      const nodeId = step.id || `node_${index}_${Date.now()}`;
      initialNodes.push({
        id: nodeId,
        type: step.type || 'STEP',
        position: { x: currentX, y: 240 },
        data: { step_name: step.step_name, description: step.description || '' },
      });

      initialEdges.push({
        id: `e_${prevId}-${nodeId}`,
        source: prevId,
        target: nodeId,
        animated: true,
        style: { stroke: '#6366f1', strokeWidth: 2 }
      });

      prevId = nodeId;
      currentX += 280;
    });

    initialNodes.push({
      id: 'end',
      type: 'END',
      position: { x: currentX, y: 240 },
      data: { step_name: 'End Process' },
      deletable: false,
    });

    initialEdges.push({
      id: `e_${prevId}-end`,
      source: prevId,
      target: 'end',
      animated: true,
      style: { stroke: '#6366f1', strokeWidth: 2 }
    });

    setNodes(initialNodes);
    setEdges(initialEdges);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Serialize graph layout to list format
  const serializeGraph = useCallback((currentNodes: Node[], currentEdges: Edge[]) => {
    const steps: WorkflowStep[] = [];
    let curr = 'start';
    const visited = new Set<string>();

    while (curr) {
      visited.add(curr);
      const outgoingEdge = currentEdges.find(e => e.source === curr);
      if (!outgoingEdge) break;

      curr = outgoingEdge.target;
      if (curr === 'end' || visited.has(curr)) break;

      const node = currentNodes.find(n => n.id === curr);
      if (node) {
        steps.push({
          id: node.id,
          type: node.type || 'STEP',
          step_name: (node.data.step_name as string) || '',
          description: (node.data.description as string) || ''
        });
      }
    }
    
    // Include any disconnected steps
    currentNodes.forEach(node => {
      if (node.id !== 'start' && node.id !== 'end' && !visited.has(node.id)) {
        steps.push({
          id: node.id,
          type: node.type || 'STEP',
          step_name: (node.data.step_name as string) || '',
          description: (node.data.description as string) || ''
        });
      }
    });

    onChange(steps);
  }, [onChange]);

  const onNodesChange = useCallback(
    (changes: NodeChange[]) => {
      setNodes((nds) => applyNodeChanges(changes, nds));
    },
    []
  );

  const onEdgesChange = useCallback(
    (changes: EdgeChange[]) => {
      setEdges((eds) => applyEdgeChanges(changes, eds));
    },
    []
  );

  useEffect(() => {
    if (nodes.length > 0) {
      serializeGraph(nodes, edges);
    }
  }, [edges, nodes.length, serializeGraph]);

  const onConnect = useCallback(
    (params: Connection) => {
      setEdges((eds) => addEdge({ ...params, animated: true, style: { stroke: '#6366f1', strokeWidth: 2 } }, eds));
    },
    []
  );

  const handleAddNode = (type: 'STEP' | 'APPROVAL' | 'EVALUATION' | 'TOOL') => {
    const id = `node_${Date.now()}`;
    let step_name = 'New Step';
    let description = 'Double-click to edit';

    if (type === 'APPROVAL') {
      step_name = 'Manager Approval';
      description = 'Requires supervisor sign-off';
    } else if (type === 'EVALUATION') {
      step_name = 'Policy Guardrail';
      description = 'Verify safe confidence levels';
    } else if (type === 'TOOL') {
      step_name = 'API Integration';
      description = 'Trigger action via tools';
    } else {
      step_name = 'Autonomous Agent';
      description = 'Delegate to AI Agent';
    }

    const newNode: Node = {
      id,
      type,
      position: { x: Math.random() * 200 + 100, y: Math.random() * 200 + 100 },
      data: { step_name, description },
    };
    setNodes((nds) => [...nds, newNode]);
  };

  const onNodeDoubleClick = (_event: React.MouseEvent, node: Node) => {
    if (node.id !== 'start' && node.id !== 'end') {
      setSelectedNodeId(node.id);
    }
  };

  const selectedNode = nodes.find(n => n.id === selectedNodeId);

  const updateSelectedNode = (field: string, val: string) => {
    if (!selectedNodeId) return;
    setNodes((nds) =>
      nds.map((n) => {
        if (n.id === selectedNodeId) {
          return {
            ...n,
            data: {
              ...n.data,
              [field]: val,
            },
          };
        }
        return n;
      })
    );
    setTimeout(() => {
      setNodes(currNodes => {
        serializeGraph(currNodes, edges);
        return currNodes;
      });
    }, 0);
  };

  const updateNodeType = (newType: string) => {
    if (!selectedNodeId) return;
    setNodes((nds) =>
      nds.map((n) => {
        if (n.id === selectedNodeId) {
          let step_name = n.data.step_name;
          let description = n.data.description;
          if (newType === 'APPROVAL') {
            step_name = 'Manager Approval';
            description = 'Requires supervisor sign-off';
          } else if (newType === 'EVALUATION') {
            step_name = 'Policy Guardrail';
            description = 'Verify safe confidence levels';
          } else if (newType === 'TOOL') {
            step_name = 'API Integration';
            description = 'Trigger action via tools';
          } else {
            step_name = 'Autonomous Agent';
            description = 'Delegate to AI Agent';
          }
          return {
            ...n,
            type: newType,
            data: { step_name, description }
          };
        }
        return n;
      })
    );
    setTimeout(() => {
      setNodes(currNodes => {
        serializeGraph(currNodes, edges);
        return currNodes;
      });
    }, 0);
  };

  return (
    <ReactFlowProvider>
      <div style={{ display: 'flex', flexDirection: 'column', height: '480px', background: '#0a0e17', borderRadius: '12px', overflow: 'hidden', border: '1px solid rgba(99, 102, 241, 0.2)', boxShadow: 'var(--shadow-neon)' }}>
      {/* Toolbar Header */}
      <div style={{ display: 'flex', gap: '10px', padding: '12px 18px', background: '#121824', borderBottom: '1px solid rgba(99, 102, 241, 0.15)', alignItems: 'center' }}>
        <button
          type="button"
          onClick={() => handleAddNode('STEP')}
          style={{ background: 'linear-gradient(135deg, #6366f1, #4f46e5)', color: 'white', border: 'none', padding: '8px 16px', borderRadius: '8px', cursor: 'pointer', fontWeight: '600', fontSize: '13px', display: 'flex', alignItems: 'center', gap: '6px', boxShadow: '0 0 10px rgba(99, 102, 241, 0.2)', transition: 'all 0.2s' }}
        >
          <BrainCircuit size={14} /> + Agent Step
        </button>
        <button
          type="button"
          onClick={() => handleAddNode('TOOL')}
          style={{ background: 'linear-gradient(135deg, #06b6d4, #0891b2)', color: 'white', border: 'none', padding: '8px 16px', borderRadius: '8px', cursor: 'pointer', fontWeight: '600', fontSize: '13px', display: 'flex', alignItems: 'center', gap: '6px', boxShadow: '0 0 10px rgba(6, 182, 212, 0.2)', transition: 'all 0.2s' }}
        >
          <Wrench size={14} /> + Tool Call
        </button>
        <button
          type="button"
          onClick={() => handleAddNode('EVALUATION')}
          style={{ background: 'linear-gradient(135deg, #10b981, #059669)', color: 'white', border: 'none', padding: '8px 16px', borderRadius: '8px', cursor: 'pointer', fontWeight: '600', fontSize: '13px', display: 'flex', alignItems: 'center', gap: '6px', boxShadow: '0 0 10px rgba(16, 185, 129, 0.2)', transition: 'all 0.2s' }}
        >
          <ShieldCheck size={14} /> + Guardrail Check
        </button>
        <button
          type="button"
          onClick={() => handleAddNode('APPROVAL')}
          style={{ background: 'linear-gradient(135deg, #f59e0b, #d97706)', color: 'white', border: 'none', padding: '8px 16px', borderRadius: '8px', cursor: 'pointer', fontWeight: '600', fontSize: '13px', display: 'flex', alignItems: 'center', gap: '6px', boxShadow: '0 0 10px rgba(245, 158, 11, 0.2)', transition: 'all 0.2s' }}
        >
          <UserCheck size={14} /> + Human Approval
        </button>
        <div style={{ marginLeft: 'auto', color: '#64748b', fontSize: '11px', fontWeight: '500' }}>
          Connect nodes to design flow. Double-click a node to configure.
        </div>
      </div>

      <div style={{ display: 'flex', flex: 1, position: 'relative' }}>
        {/* Canvas Workspace */}
        <div style={{ flex: 1, position: 'relative' }}>
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            nodeTypes={nodeTypes}
            onNodeDoubleClick={onNodeDoubleClick}
            onPaneClick={() => setSelectedNodeId(null)}
            fitView
            fitViewOptions={{ padding: 0.15 }}
            defaultEdgeOptions={{ style: { stroke: '#6366f1', strokeWidth: 2 } }}
          >
            <Background color="#0f172a" gap={20} size={1} />
            <Controls />
            <FlowFitViewHelper nodes={nodes} />
          </ReactFlow>
        </div>

        {/* Side Panel for Node Properties & Asset Selection */}
        {selectedNode && (
          <div style={{
            width: '320px',
            background: 'rgba(18, 24, 36, 0.95)',
            backdropFilter: 'blur(16px)',
            borderLeft: '1px solid rgba(99, 102, 241, 0.15)',
            padding: '24px',
            display: 'flex',
            flexDirection: 'column',
            gap: '18px',
            boxShadow: '-10px 0 30px rgba(0,0,0,0.5)',
            zIndex: 10
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h3 style={{ margin: 0, color: '#fff', fontSize: '15px', fontWeight: '700', letterSpacing: '0.5px' }}>NODE PROPERTIES</h3>
              <span style={{ fontSize: '10px', background: 'rgba(99,102,241,0.15)', color: '#818cf8', padding: '2px 8px', borderRadius: '4px', fontWeight: 'bold' }}>{selectedNode.type}</span>
            </div>
            
            {/* Node Type Selector */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <label style={{ color: '#94a3b8', fontSize: '11px', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Type Category</label>
              <select
                value={selectedNode.type || 'STEP'}
                onChange={(e) => updateNodeType(e.target.value)}
                style={{ background: '#0a0e17', border: '1px solid rgba(99, 102, 241, 0.2)', color: '#fff', padding: '10px', borderRadius: '8px', fontSize: '13px' }}
              >
                <option value="STEP">AI Agent Step</option>
                <option value="TOOL">Tool Integration</option>
                <option value="EVALUATION">Evaluation Guardrail</option>
                <option value="APPROVAL">Human Approval</option>
              </select>
            </div>

            {/* Custom Asset Selection Drawers */}
            {selectedNode.type === 'STEP' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                <label style={{ color: '#94a3b8', fontSize: '11px', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Select Registered AI Agent</label>
                <select
                  value={registryAgents.find(a => a.agent_name === selectedNode.data.step_name)?.id || ''}
                  onChange={(e) => {
                    const agentId = e.target.value;
                    const agent = registryAgents.find(a => a.id === agentId);
                    if (agent) {
                      updateSelectedNode('step_name', agent.agent_name);
                      updateSelectedNode('description', agent.description || `Agent Code: ${agent.agent_code} (${agent.risk_level} Risk)`);
                    }
                  }}
                  style={{ background: '#0a0e17', border: '1px solid rgba(99, 102, 241, 0.2)', color: '#fff', padding: '10px', borderRadius: '8px', fontSize: '13px' }}
                >
                  <option value="">-- Select Agent --</option>
                  {registryAgents.map(a => (
                    <option key={a.id} value={a.id}>{a.agent_name} ({a.agent_code})</option>
                  ))}
                </select>
              </div>
            )}

            {selectedNode.type === 'TOOL' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                <label style={{ color: '#94a3b8', fontSize: '11px', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Select Registered Tool</label>
                <select
                  value={registryTools.find(t => t.tool_name === selectedNode.data.step_name)?.id || ''}
                  onChange={(e) => {
                    const toolId = e.target.value;
                    const tool = registryTools.find(t => t.id === toolId);
                    if (tool) {
                      updateSelectedNode('step_name', tool.tool_name);
                      updateSelectedNode('description', `Tool: ${tool.tool_code} (${tool.tool_category})`);
                    }
                  }}
                  style={{ background: '#0a0e17', border: '1px solid rgba(99, 102, 241, 0.2)', color: '#fff', padding: '10px', borderRadius: '8px', fontSize: '13px' }}
                >
                  <option value="">-- Select Tool --</option>
                  {registryTools.map(t => (
                    <option key={t.id} value={t.id}>{t.tool_name} ({t.tool_code})</option>
                  ))}
                </select>
              </div>
            )}

            {/* Standard Text Edit fields */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <label style={{ color: '#94a3b8', fontSize: '11px', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Custom Label</label>
              <input
                type="text"
                value={(selectedNode.data.step_name as string) || ''}
                onChange={(e) => updateSelectedNode('step_name', e.target.value)}
                style={{ background: '#0a0e17', border: '1px solid rgba(99, 102, 241, 0.2)', color: '#fff', padding: '10px', borderRadius: '8px', fontSize: '13px' }}
              />
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <label style={{ color: '#94a3b8', fontSize: '11px', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Description</label>
              <textarea
                value={(selectedNode.data.description as string) || ''}
                onChange={(e) => updateSelectedNode('description', e.target.value)}
                rows={4}
                style={{ background: '#0a0e17', border: '1px solid rgba(99, 102, 241, 0.2)', color: '#fff', padding: '10px', borderRadius: '8px', fontSize: '13px', resize: 'vertical' }}
              />
            </div>

            <button
              type="button"
              onClick={() => setSelectedNodeId(null)}
              style={{ marginTop: 'auto', background: 'transparent', border: '1px solid rgba(255,255,255,0.15)', color: '#fff', padding: '10px', borderRadius: '8px', cursor: 'pointer', fontWeight: '600', fontSize: '13px', transition: 'all 0.2s' }}
            >
              Close Panel
            </button>
          </div>
        )}
      </div>
    </div>
    </ReactFlowProvider>
  );
};

export default WorkflowNodeCanvas;

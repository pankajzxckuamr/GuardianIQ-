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
  NodeProps
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

// --- Custom Node Components ---

const StartNode = () => (
  <div style={{ padding: '10px 20px', borderRadius: '20px', background: '#2c3e50', color: '#fff', border: '2px solid #34495e', fontWeight: 'bold' }}>
    START
    <Handle type="source" position={Position.Right} style={{ background: '#00f0ff' }} />
  </div>
);

const EndNode = () => (
  <div style={{ padding: '10px 20px', borderRadius: '20px', background: '#2c3e50', color: '#fff', border: '2px solid #34495e', fontWeight: 'bold' }}>
    <Handle type="target" position={Position.Left} style={{ background: '#00f0ff' }} />
    END
  </div>
);

const StepNode = ({ data }: NodeProps) => (
  <div style={{ padding: '15px', borderRadius: '8px', background: '#1a1f2e', color: '#fff', border: '1px solid #3b82f6', minWidth: '150px' }}>
    <Handle type="target" position={Position.Left} style={{ background: '#00f0ff' }} />
    <div style={{ fontSize: '14px', fontWeight: 'bold', marginBottom: '5px' }}>{data.step_name as string || 'New Step'}</div>
    <div style={{ fontSize: '12px', color: '#888' }}>{(data.description as string) || 'Double-click to edit'}</div>
    <Handle type="source" position={Position.Right} style={{ background: '#00f0ff' }} />
  </div>
);

const ApprovalNode = ({ data }: NodeProps) => (
  <div style={{ padding: '15px', borderRadius: '8px', background: '#3b2f15', color: '#f59e0b', border: '1px solid #f59e0b', minWidth: '150px' }}>
    <Handle type="target" position={Position.Left} style={{ background: '#f59e0b' }} />
    <div style={{ fontSize: '14px', fontWeight: 'bold', marginBottom: '5px' }}>{data.step_name as string || 'Approval'}</div>
    <div style={{ fontSize: '12px', color: '#b48629' }}>{(data.description as string) || 'Double-click to edit'}</div>
    <Handle type="source" position={Position.Right} style={{ background: '#f59e0b' }} />
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

  const nodeTypes = useMemo(() => ({
    START: StartNode,
    END: EndNode,
    STEP: StepNode,
    APPROVAL: ApprovalNode
  }), []);

  // Deserialize
  useEffect(() => {
    // Only deserialize if the canvas is completely empty (initial load)
    if (nodes.length > 0) return;

    const initialNodes: Node[] = [];
    const initialEdges: Edge[] = [];

    initialNodes.push({
      id: 'start',
      type: 'START',
      position: { x: 50, y: 150 },
      data: { label: 'Start' },
      deletable: false,
    });

    let prevId = 'start';
    let currentX = 250;

    const steps = Array.isArray(value) ? value : [];

    steps.forEach((step, index) => {
      const nodeId = step.id || `node_${index}_${Date.now()}`;
      initialNodes.push({
        id: nodeId,
        type: step.type === 'APPROVAL' ? 'APPROVAL' : 'STEP',
        position: { x: currentX, y: 150 },
        data: { step_name: step.step_name, description: step.description || '' },
      });

      initialEdges.push({
        id: `e_${prevId}-${nodeId}`,
        source: prevId,
        target: nodeId,
        animated: true,
        style: { stroke: '#00f0ff', strokeWidth: 2 }
      });

      prevId = nodeId;
      currentX += 250;
    });

    initialNodes.push({
      id: 'end',
      type: 'END',
      position: { x: currentX, y: 150 },
      data: { label: 'End' },
      deletable: false,
    });

    initialEdges.push({
      id: `e_${prevId}-end`,
      source: prevId,
      target: 'end',
      animated: true,
      style: { stroke: '#00f0ff', strokeWidth: 2 }
    });

    setNodes(initialNodes);
    setEdges(initialEdges);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Serialize
  const serializeGraph = useCallback((currentNodes: Node[], currentEdges: Edge[]) => {
    // Basic topological sort starting from "start" node
    const steps: WorkflowStep[] = [];
    let curr = 'start';

    // To prevent infinite loops in cyclic graphs
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
          type: node.type === 'APPROVAL' ? 'APPROVAL' : 'STEP',
          step_name: (node.data.step_name as string) || '',
          description: (node.data.description as string) || ''
        });
      }
    }
    
    // Also include any disconnected nodes so data isn't lost
    currentNodes.forEach(node => {
      if (node.id !== 'start' && node.id !== 'end' && !visited.has(node.id)) {
         steps.push({
          id: node.id,
          type: node.type === 'APPROVAL' ? 'APPROVAL' : 'STEP',
          step_name: (node.data.step_name as string) || '',
          description: (node.data.description as string) || ''
        });
      }
    });

    onChange(steps);
  }, [onChange]);

  const onNodesChange = useCallback(
    (changes: NodeChange[]) => {
      setNodes((nds) => {
        const newNodes = applyNodeChanges(changes, nds);
        // Only trigger serialize on deletion or other structural changes if needed, but simple dragging is fine
        return newNodes;
      });
    },
    []
  );

  const onEdgesChange = useCallback(
    (changes: EdgeChange[]) => {
      setEdges((eds) => {
        const newEdges = applyEdgeChanges(changes, eds);
        return newEdges;
      });
    },
    []
  );

  // Trigger serialization when edges change (connections made/broken) or nodes are deleted
  useEffect(() => {
    if (nodes.length > 0) {
      serializeGraph(nodes, edges);
    }
  }, [edges, nodes.length, serializeGraph]); // nodes.length captures additions/deletions

  const onConnect = useCallback(
    (params: Connection) => {
      setEdges((eds) => addEdge({ ...params, animated: true, style: { stroke: '#00f0ff', strokeWidth: 2 } }, eds));
    },
    []
  );

  const handleAddNode = (type: 'STEP' | 'APPROVAL') => {
    const id = `node_${Date.now()}`;
    const newNode: Node = {
      id,
      type,
      position: { x: Math.random() * 200 + 100, y: Math.random() * 200 + 100 },
      data: { step_name: type === 'APPROVAL' ? 'New Approval' : 'New Step', description: '' },
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
    // Serialize graph will pick this up on next render? No, nodes reference changed but length didn't.
    // We explicitly call serialize to ensure text changes are saved immediately.
    setTimeout(() => {
        setNodes(currNodes => {
            serializeGraph(currNodes, edges);
            return currNodes;
        });
    }, 0);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '500px', background: '#0b1120', borderRadius: '8px', overflow: 'hidden', border: '1px solid #1e293b' }}>
      {/* Toolbar */}
      <div style={{ display: 'flex', gap: '10px', padding: '10px 15px', background: '#1e293b', borderBottom: '1px solid #334155' }}>
        <button
          type="button"
          onClick={() => handleAddNode('STEP')}
          style={{ background: '#3b82f6', color: 'white', border: 'none', padding: '6px 12px', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}
        >
          + Add Step
        </button>
        <button
          type="button"
          onClick={() => handleAddNode('APPROVAL')}
          style={{ background: '#f59e0b', color: 'white', border: 'none', padding: '6px 12px', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}
        >
          + Add Approval
        </button>
        <div style={{ marginLeft: 'auto', color: '#94a3b8', fontSize: '12px', display: 'flex', alignItems: 'center' }}>
          Connect nodes to order steps. Double-click a node to edit.
        </div>
      </div>

      <div style={{ display: 'flex', flex: 1, position: 'relative' }}>
        {/* Canvas */}
        <div style={{ flex: 1 }}>
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
            defaultEdgeOptions={{ style: { stroke: '#00f0ff', strokeWidth: 2 } }}
          >
            <Background color="#1e293b" gap={16} />
            <Controls style={{ backgroundColor: '#1e293b', borderBottom: '1px solid #0b1120' }} />
          </ReactFlow>
        </div>

        {/* Side Panel for Editing */}
        {selectedNode && (
          <div style={{
            width: '300px',
            background: '#1e293b',
            borderLeft: '1px solid #334155',
            padding: '20px',
            display: 'flex',
            flexDirection: 'column',
            gap: '15px'
          }}>
            <h3 style={{ margin: 0, color: '#fff', fontSize: '16px' }}>Edit Node</h3>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
              <label style={{ color: '#94a3b8', fontSize: '12px', fontWeight: 'bold' }}>Step Name</label>
              <input
                type="text"
                value={(selectedNode.data.step_name as string) || ''}
                onChange={(e) => updateSelectedNode('step_name', e.target.value)}
                style={{ background: '#0b1120', border: '1px solid #334155', color: '#fff', padding: '8px', borderRadius: '4px' }}
              />
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
              <label style={{ color: '#94a3b8', fontSize: '12px', fontWeight: 'bold' }}>Description</label>
              <textarea
                value={(selectedNode.data.description as string) || ''}
                onChange={(e) => updateSelectedNode('description', e.target.value)}
                rows={4}
                style={{ background: '#0b1120', border: '1px solid #334155', color: '#fff', padding: '8px', borderRadius: '4px', resize: 'vertical' }}
              />
            </div>

            <button
              type="button"
              onClick={() => setSelectedNodeId(null)}
              style={{ marginTop: 'auto', background: 'transparent', border: '1px solid #475569', color: '#fff', padding: '8px', borderRadius: '4px', cursor: 'pointer' }}
            >
              Close Panel
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default WorkflowNodeCanvas;

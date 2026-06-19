import React from 'react';
import { ReactFlow, Background, Controls, Node, Edge, MarkerType } from '@xyflow/react';
import '@xyflow/react/dist/style.css';

interface InteractionGraphViewerProps {
  session: any;
}

export const InteractionGraphViewer: React.FC<InteractionGraphViewerProps> = ({ session }) => {
  const nodes: Node[] = [
    {
      id: 'dept',
      data: { label: `Department\n${session.department_name || 'N/A'}` },
      position: { x: 50, y: 50 },
      style: { background: '#1e293b', color: '#fff', border: '1px solid #3b82f6', borderRadius: '8px', padding: '10px' }
    },
    {
      id: 'role',
      data: { label: `Role\n${session.role_name || 'N/A'}` },
      position: { x: 250, y: 50 },
      style: { background: '#1e293b', color: '#fff', border: '1px solid #8b5cf6', borderRadius: '8px', padding: '10px' }
    },
    {
      id: 'user',
      data: { label: `User\n${session.user_name || 'N/A'}` },
      position: { x: 450, y: 50 },
      style: { background: '#1e293b', color: '#fff', border: '1px solid #10b981', borderRadius: '8px', padding: '10px' }
    },
    {
      id: 'ds',
      data: { label: `Data Source\n${session.data_source_name || 'N/A'}` },
      position: { x: 150, y: 150 },
      style: { background: '#1e293b', color: '#fff', border: '1px solid #eab308', borderRadius: '8px', padding: '10px' }
    },
    {
      id: 'model',
      data: { label: `AI Model\n${session.model_name || 'N/A'}` },
      position: { x: 350, y: 150 },
      style: { background: '#1e293b', color: '#fff', border: '1px solid #ec4899', borderRadius: '8px', padding: '10px' }
    },
    {
      id: 'agent',
      data: { label: `AI Agent\n${session.agent_name || 'N/A'}` },
      position: { x: 550, y: 150 },
      style: { background: '#1e293b', color: '#fff', border: '1px solid #f97316', borderRadius: '8px', padding: '10px' }
    },
    {
      id: 'tool',
      data: { label: `Tool\n${session.tool_name || 'N/A'}` },
      position: { x: 450, y: 250 },
      style: { background: '#1e293b', color: '#fff', border: '1px solid #06b6d4', borderRadius: '8px', padding: '10px' }
    },
    {
      id: 'wf',
      data: { label: `Workflow\n${session.workflow_name || 'N/A'}` },
      position: { x: 250, y: 250 },
      style: { background: '#1e293b', color: '#fff', border: '1px solid #ef4444', borderRadius: '8px', padding: '10px' }
    }
  ];

  const edges: Edge[] = [
    { id: 'e1', source: 'dept', target: 'role', label: 'HAS', animated: true, markerEnd: { type: MarkerType.ArrowClosed } },
    { id: 'e2', source: 'role', target: 'user', label: 'HAS', animated: true, markerEnd: { type: MarkerType.ArrowClosed } },
    { id: 'e3', source: 'user', target: 'wf', label: 'OWNS', animated: true, markerEnd: { type: MarkerType.ArrowClosed } },
    { id: 'e4', source: 'wf', target: 'agent', label: 'USES', animated: true, markerEnd: { type: MarkerType.ArrowClosed } },
    { id: 'e5', source: 'agent', target: 'model', label: 'USES', animated: true, markerEnd: { type: MarkerType.ArrowClosed } },
    { id: 'e6', source: 'agent', target: 'tool', label: 'USES', animated: true, markerEnd: { type: MarkerType.ArrowClosed } },
    { id: 'e7', source: 'model', target: 'ds', label: 'USES', animated: true, markerEnd: { type: MarkerType.ArrowClosed } }
  ];

  return (
    <div style={{ height: '400px', width: '100%', background: '#0f172a', borderRadius: '8px', overflow: 'hidden', border: '1px solid #334155' }}>
      <ReactFlow nodes={nodes} edges={edges} fitView>
        <Background color="#1e293b" gap={16} />
        <Controls />
      </ReactFlow>
    </div>
  );
};

export default InteractionGraphViewer;

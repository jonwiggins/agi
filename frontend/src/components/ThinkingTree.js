import React, { useEffect, useState, useCallback } from 'react';
import ReactFlow, { Background, Controls, MiniMap } from 'reactflow';
import 'reactflow/dist/style.css';
import { useWebSocket } from '../hooks/useWebSocket';
import './ThinkingTree.css';

const AgentNode = ({ data }) => {
  const statusColors = {
    pending: '#666',
    thinking: '#fbbf24',
    executing: '#3b82f6',
    evaluating: '#8b5cf6',
    completed: '#10b981',
    failed: '#ef4444',
  };

  return (
    <div className="agent-node" style={{ borderColor: statusColors[data.status] || '#666' }}>
      <div className="node-header">
        <div className="node-status" style={{ backgroundColor: statusColors[data.status] }} />
        <span className="node-title">Agent {data.depth}</span>
      </div>
      <div className="node-task">{data.task}</div>
      {data.status && (
        <div className="node-footer">
          <span className="status-badge">{data.status}</span>
        </div>
      )}
    </div>
  );
};

const nodeTypes = {
  agent: AgentNode,
};

function ThinkingTree({ executionId }) {
  const [nodes, setNodes] = useState([]);
  const [edges, setEdges] = useState([]);
  const { messages, connectionStatus } = useWebSocket(executionId);

  const updateTree = useCallback((message) => {
    if (message.type === 'agent_created') {
      // Add new node
      setNodes((prev) => {
        const exists = prev.find(n => n.id === message.agent_id);
        if (exists) return prev;

        const newNode = {
          id: message.agent_id,
          type: 'agent',
          position: {
            x: message.depth * 300 + 100,
            y: prev.filter(n => n.data.depth === message.depth).length * 150 + 100,
          },
          data: {
            task: message.task,
            depth: message.depth,
            status: 'pending',
          },
        };

        return [...prev, newNode];
      });

      // Add edge from parent
      if (message.parent_id) {
        setEdges((prev) => {
          const exists = prev.find(e =>
            e.source === message.parent_id && e.target === message.agent_id
          );
          if (exists) return prev;

          return [...prev, {
            id: `${message.parent_id}-${message.agent_id}`,
            source: message.parent_id,
            target: message.agent_id,
            animated: true,
          }];
        });
      }
    } else if (message.type === 'agent_status') {
      // Update node status
      setNodes((prev) =>
        prev.map((node) =>
          node.id === message.agent_id
            ? { ...node, data: { ...node.data, status: message.status } }
            : node
        )
      );
    }
  }, []);

  useEffect(() => {
    if (messages.length > 0) {
      const latestMessage = messages[messages.length - 1];
      updateTree(latestMessage);
    }
  }, [messages, updateTree]);

  return (
    <div className="thinking-tree-container">
      <div className="tree-header">
        <h3>Execution Tree</h3>
        <div className="connection-status">
          <span className={`status-dot ${connectionStatus === 'connected' ? 'connected' : ''}`} />
          {connectionStatus}
        </div>
      </div>
      <div className="tree-canvas">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          nodeTypes={nodeTypes}
          fitView
          attributionPosition="bottom-left"
        >
          <Background color="#333" gap={16} />
          <Controls />
          <MiniMap
            nodeColor={(node) => {
              const colors = {
                pending: '#666',
                thinking: '#fbbf24',
                executing: '#3b82f6',
                evaluating: '#8b5cf6',
                completed: '#10b981',
                failed: '#ef4444',
              };
              return colors[node.data.status] || '#666';
            }}
            maskColor="rgba(0, 0, 0, 0.8)"
          />
        </ReactFlow>
      </div>
    </div>
  );
}

export default ThinkingTree;

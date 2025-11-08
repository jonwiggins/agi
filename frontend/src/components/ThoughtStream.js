import React, { useEffect, useRef } from 'react';
import { useWebSocket } from '../hooks/useWebSocket';
import { Brain, Lightbulb, CheckCircle, XCircle } from 'lucide-react';
import './ThoughtStream.css';

const ThoughtIcon = ({ type }) => {
  const icons = {
    analysis: <Brain size={16} />,
    planning: <Lightbulb size={16} />,
    evaluation: <CheckCircle size={16} />,
    execution: <XCircle size={16} />,
  };
  return icons[type] || <Brain size={16} />;
};

function ThoughtStream({ executionId }) {
  const { messages } = useWebSocket(executionId);
  const streamRef = useRef(null);

  useEffect(() => {
    // Auto-scroll to bottom
    if (streamRef.current) {
      streamRef.current.scrollTop = streamRef.current.scrollHeight;
    }
  }, [messages]);

  const thoughts = messages.filter(m => m.type === 'thought');

  return (
    <div className="thought-stream-container">
      <div className="stream-header">
        <h3>Thought Stream</h3>
        <span className="thought-count">{thoughts.length} thoughts</span>
      </div>
      <div className="stream-content" ref={streamRef}>
        {thoughts.length === 0 ? (
          <div className="empty-state">
            <Brain size={48} color="#666" />
            <p>Waiting for thoughts...</p>
          </div>
        ) : (
          thoughts.map((msg, idx) => (
            <div key={idx} className="thought-item">
              <div className="thought-header">
                <ThoughtIcon type={msg.thought_type} />
                <span className="thought-type">{msg.thought_type}</span>
                <span className="thought-time">
                  {new Date(msg.timestamp).toLocaleTimeString()}
                </span>
              </div>
              <div className="thought-content">{msg.thought}</div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

export default ThoughtStream;

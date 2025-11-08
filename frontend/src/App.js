import React, { useState } from 'react';
import ThinkingTree from './components/ThinkingTree';
import ThoughtStream from './components/ThoughtStream';
import MemoryPanel from './components/MemoryPanel';
import TaskInput from './components/TaskInput';
import { Brain, Database, MessageSquare } from 'lucide-react';
import './App.css';

function App() {
  const [executionId, setExecutionId] = useState(null);
  const [activeTab, setActiveTab] = useState('tree');

  const handleTaskSubmit = (newExecutionId) => {
    setExecutionId(newExecutionId);
    setActiveTab('tree');
  };

  return (
    <div className="app-container">
      {/* Header */}
      <header className="app-header">
        <div className="header-content">
          <div className="logo">
            <Brain size={32} />
            <h1>AGI Platform</h1>
            <span className="subtitle">Real-time Thinking Visualization</span>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="main-content">
        {/* Task Input */}
        <div className="task-section">
          <TaskInput onSubmit={handleTaskSubmit} />
        </div>

        {/* Tabs */}
        {executionId && (
          <div className="tabs">
            <button
              className={`tab ${activeTab === 'tree' ? 'active' : ''}`}
              onClick={() => setActiveTab('tree')}
            >
              <Brain size={18} />
              Thinking Tree
            </button>
            <button
              className={`tab ${activeTab === 'thoughts' ? 'active' : ''}`}
              onClick={() => setActiveTab('thoughts')}
            >
              <MessageSquare size={18} />
              Thought Stream
            </button>
            <button
              className={`tab ${activeTab === 'memory' ? 'active' : ''}`}
              onClick={() => setActiveTab('memory')}
            >
              <Database size={18} />
              Memories
            </button>
          </div>
        )}

        {/* Content Panels */}
        {executionId && (
          <div className="content-panel">
            {activeTab === 'tree' && (
              <ThinkingTree executionId={executionId} />
            )}
            {activeTab === 'thoughts' && (
              <ThoughtStream executionId={executionId} />
            )}
            {activeTab === 'memory' && (
              <MemoryPanel />
            )}
          </div>
        )}

        {!executionId && (
          <div className="welcome-message">
            <Brain size={64} className="welcome-icon" />
            <h2>Welcome to AGI Platform</h2>
            <p>Enter a complex task above to see the recursive thinking process visualized in real-time.</p>
            <div className="features">
              <div className="feature">
                <Brain size={24} />
                <span>Recursive Task Decomposition</span>
              </div>
              <div className="feature">
                <MessageSquare size={24} />
                <span>Real-time Thought Streaming</span>
              </div>
              <div className="feature">
                <Database size={24} />
                <span>Persistent Memory</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;

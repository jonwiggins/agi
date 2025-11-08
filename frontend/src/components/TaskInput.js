import React, { useState } from 'react';
import { Send, Loader } from 'lucide-react';
import axios from 'axios';
import './TaskInput.css';

function TaskInput({ onSubmit }) {
  const [task, setTask] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!task.trim()) return;

    setLoading(true);
    try {
      const response = await axios.post('/execute', {
        task: task.trim(),
        max_depth: 5,
        max_iterations: 3,
        store_in_memory: true,
      });

      onSubmit(response.data.execution_id);
      setTask('');
    } catch (error) {
      console.error('Error submitting task:', error);
      alert('Error starting task execution');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="task-input-form">
      <div className="input-wrapper">
        <input
          type="text"
          value={task}
          onChange={(e) => setTask(e.target.value)}
          placeholder="Enter a complex task (e.g., 'Research quantum computing, analyze trends, predict future')"
          disabled={loading}
          className="task-input"
        />
        <button
          type="submit"
          disabled={loading || !task.trim()}
          className="submit-button"
        >
          {loading ? <Loader className="spin" size={20} /> : <Send size={20} />}
        </button>
      </div>
    </form>
  );
}

export default TaskInput;

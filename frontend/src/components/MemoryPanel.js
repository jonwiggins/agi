import React, { useState, useEffect } from 'react';
import { Search, Database } from 'lucide-react';
import axios from 'axios';
import './MemoryPanel.css';

function MemoryPanel() {
  const [memories, setMemories] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(false);

  const fetchMemories = async (query = '') => {
    setLoading(true);
    try {
      const params = query ? { query, limit: 50 } : { limit: 50 };
      const response = await axios.get('/memories', { params });
      setMemories(response.data.memories || []);
    } catch (error) {
      console.error('Error fetching memories:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMemories();
  }, []);

  const handleSearch = (e) => {
    e.preventDefault();
    fetchMemories(searchQuery);
  };

  return (
    <div className="memory-panel-container">
      <div className="memory-header">
        <h3>Memory Database</h3>
        <form onSubmit={handleSearch} className="search-form">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search memories..."
            className="search-input"
          />
          <button type="submit" className="search-button">
            <Search size={18} />
          </button>
        </form>
      </div>
      <div className="memory-content">
        {loading ? (
          <div className="loading">Loading...</div>
        ) : memories.length === 0 ? (
          <div className="empty-state">
            <Database size={48} color="#666" />
            <p>No memories found</p>
          </div>
        ) : (
          <div className="memory-list">
            {memories.map((memory, idx) => (
              <div key={memory.id || idx} className="memory-item">
                <div className="memory-meta">
                  {memory.relevance && (
                    <span className="relevance-badge">
                      {(memory.relevance * 100).toFixed(0)}% relevant
                    </span>
                  )}
                  {memory.timestamp && (
                    <span className="memory-time">
                      {new Date(memory.timestamp).toLocaleDateString()}
                    </span>
                  )}
                </div>
                <div className="memory-content-text">{memory.content}</div>
                {memory.metadata && Object.keys(memory.metadata).length > 0 && (
                  <div className="memory-tags">
                    {Object.entries(memory.metadata).slice(0, 3).map(([key, value]) => (
                      <span key={key} className="tag">
                        {key}: {String(value).substring(0, 20)}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default MemoryPanel;

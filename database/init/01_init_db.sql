-- AGI Platform Database Initialization Script
-- Recursive Subagent Architecture Schema

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For text search

-- ==========================================
-- Agent Tree System
-- ==========================================

-- Tasks: Root-level tasks submitted by users
CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Task details
    task_description TEXT NOT NULL,
    context JSONB,

    -- Constraints
    max_depth INTEGER DEFAULT 10,
    max_agents INTEGER DEFAULT 100,
    timeout_seconds INTEGER DEFAULT 3600,

    -- Status
    status VARCHAR(50) DEFAULT 'pending',
    current_depth INTEGER DEFAULT 0,
    total_agents INTEGER DEFAULT 0,

    -- Results
    final_result JSONB,
    insights JSONB,
    confidence_score FLOAT,

    -- Metrics
    execution_time_seconds FLOAT,
    total_cost_usd DECIMAL(10, 4),

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    updated_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT valid_task_status CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'timeout', 'cancelled'))
);

CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_created_at ON tasks(created_at DESC);

-- Agent Trees: Represents the entire tree structure for a task
CREATE TABLE IF NOT EXISTS agent_trees (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,

    -- Tree structure (stored as JSONB for easy visualization)
    tree_structure JSONB NOT NULL,

    -- Metrics
    total_nodes INTEGER DEFAULT 0,
    max_depth_reached INTEGER DEFAULT 0,
    total_tool_calls INTEGER DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_agent_trees_task_id ON agent_trees(task_id);

-- Agents: Individual agents in the tree
CREATE TABLE IF NOT EXISTS agents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,

    -- Tree position
    parent_id UUID REFERENCES agents(id) ON DELETE CASCADE,
    depth INTEGER NOT NULL DEFAULT 0,
    position_in_parent INTEGER,  -- Order among siblings

    -- Agent details
    assigned_task TEXT NOT NULL,
    context JSONB NOT NULL,
    constraints JSONB,

    -- Status
    status VARCHAR(50) DEFAULT 'created',

    -- Results
    result JSONB,
    thoughts TEXT,
    synthesis TEXT,
    learnings JSONB,

    -- Execution
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    execution_time_seconds FLOAT,
    timeout_seconds INTEGER DEFAULT 300,

    -- LLM tracking
    model_used VARCHAR(100),
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    total_tokens INTEGER,
    cost_usd DECIMAL(10, 6),

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT valid_agent_status CHECK (status IN (
        'created', 'queued', 'running', 'waiting_for_subagents',
        'evaluating', 'revising', 'completed', 'failed', 'timeout'
    ))
);

CREATE INDEX idx_agents_task_id ON agents(task_id);
CREATE INDEX idx_agents_parent_id ON agents(parent_id);
CREATE INDEX idx_agents_status ON agents(status);
CREATE INDEX idx_agents_depth ON agents(depth);

-- Agent Executions: Track multiple execution attempts (for revisions)
CREATE TABLE IF NOT EXISTS agent_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,

    -- Execution metadata
    attempt_number INTEGER NOT NULL DEFAULT 1,
    revision_reason TEXT,  -- Why this was re-executed

    -- Execution details
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    status VARCHAR(50) DEFAULT 'running',

    -- Results
    result JSONB,
    error_message TEXT,
    stack_trace TEXT,

    -- LLM tracking
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    cost_usd DECIMAL(10, 6),

    CONSTRAINT valid_execution_status CHECK (status IN ('running', 'completed', 'failed', 'timeout'))
);

CREATE INDEX idx_agent_executions_agent_id ON agent_executions(agent_id);
CREATE INDEX idx_agent_executions_attempt ON agent_executions(agent_id, attempt_number);

-- ==========================================
-- Tool System
-- ==========================================

-- Tool Calls: Record of all tool invocations
CREATE TABLE IF NOT EXISTS tool_calls (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    execution_id UUID REFERENCES agent_executions(id) ON DELETE CASCADE,

    -- Tool details
    tool_name VARCHAR(100) NOT NULL,
    arguments JSONB NOT NULL,

    -- Results
    result JSONB,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,

    -- Performance
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    execution_time_ms INTEGER,

    -- Cost tracking (for paid APIs)
    cost_usd DECIMAL(10, 6),

    CONSTRAINT valid_tool_name CHECK (tool_name IN (
        'web_search', 'db_query', 'execute_code',
        'create_subagent', 'store_data'
    ))
);

CREATE INDEX idx_tool_calls_agent_id ON tool_calls(agent_id);
CREATE INDEX idx_tool_calls_tool_name ON tool_calls(tool_name);
CREATE INDEX idx_tool_calls_created_at ON tool_calls(started_at DESC);

-- Code Executions: Detailed tracking of code execution tool calls
CREATE TABLE IF NOT EXISTS code_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tool_call_id UUID NOT NULL REFERENCES tool_calls(id) ON DELETE CASCADE,

    -- Code details
    language VARCHAR(50) NOT NULL,
    code TEXT NOT NULL,

    -- Execution environment
    sandbox_id VARCHAR(255),
    timeout_seconds INTEGER DEFAULT 30,

    -- Results
    stdout TEXT,
    stderr TEXT,
    exit_code INTEGER,
    success BOOLEAN,

    -- Resource usage
    execution_time_ms INTEGER,
    memory_usage_mb FLOAT,
    cpu_time_ms INTEGER,

    -- Timestamps
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

CREATE INDEX idx_code_executions_tool_call_id ON code_executions(tool_call_id);
CREATE INDEX idx_code_executions_language ON code_executions(language);

-- ==========================================
-- Evaluation System
-- ==========================================

-- Evaluations: Accept/reject decisions by parent agents
CREATE TABLE IF NOT EXISTS evaluations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Relationships
    parent_agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    child_agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    execution_id UUID REFERENCES agent_executions(id) ON DELETE CASCADE,

    -- Evaluation details
    decision VARCHAR(20) NOT NULL,
    score FLOAT,  -- 0.0 to 1.0
    reasoning TEXT NOT NULL,

    -- Feedback for revisions
    feedback TEXT,
    required_changes JSONB,

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT valid_decision CHECK (decision IN ('accept', 'reject', 'revise', 'escalate'))
);

CREATE INDEX idx_evaluations_parent ON evaluations(parent_agent_id);
CREATE INDEX idx_evaluations_child ON evaluations(child_agent_id);
CREATE INDEX idx_evaluations_decision ON evaluations(decision);

-- ==========================================
-- Knowledge Store
-- ==========================================

-- Knowledge Store: Data persisted by agents via store_data tool
CREATE TABLE IF NOT EXISTS knowledge_store (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Source tracking
    agent_id UUID REFERENCES agents(id) ON DELETE SET NULL,
    task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,

    -- Data
    category VARCHAR(100) NOT NULL,
    data JSONB NOT NULL,
    metadata JSONB,

    -- Semantic search
    embedding vector(1536),
    summary TEXT,

    -- Access tracking
    access_count INTEGER DEFAULT 0,
    last_accessed_at TIMESTAMP,

    -- Quality metrics
    usefulness_score FLOAT DEFAULT 0.5,
    verified BOOLEAN DEFAULT FALSE,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_knowledge_store_category ON knowledge_store(category);
CREATE INDEX idx_knowledge_store_task_id ON knowledge_store(task_id);
CREATE INDEX idx_knowledge_store_created_at ON knowledge_store(created_at DESC);

-- Vector similarity search index
CREATE INDEX idx_knowledge_store_embedding ON knowledge_store
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- ==========================================
-- Memory & Learning
-- ==========================================

-- Patterns: Learned patterns from successful task decompositions
CREATE TABLE IF NOT EXISTS learned_patterns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Pattern identification
    pattern_type VARCHAR(100) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,

    -- Pattern content
    trigger_conditions JSONB,  -- When to apply this pattern
    decomposition_strategy JSONB,  -- How to break down the task
    success_indicators JSONB,  -- What makes this successful

    -- Learning metadata
    learned_from_task_id UUID REFERENCES tasks(id) ON DELETE SET NULL,
    times_applied INTEGER DEFAULT 0,
    success_rate FLOAT DEFAULT 0.0,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_learned_patterns_type ON learned_patterns(pattern_type);
CREATE INDEX idx_learned_patterns_success_rate ON learned_patterns(success_rate DESC);

-- Agent Memories: Specific experiences agents should remember
CREATE TABLE IF NOT EXISTS agent_memories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Memory content
    memory_type VARCHAR(100) NOT NULL,
    content TEXT NOT NULL,
    context JSONB,

    -- Vector embedding for semantic search
    embedding vector(1536),

    -- Source
    source_task_id UUID REFERENCES tasks(id) ON DELETE SET NULL,
    source_agent_id UUID REFERENCES agents(id) ON DELETE SET NULL,

    -- Importance
    importance_score FLOAT DEFAULT 0.5,
    access_count INTEGER DEFAULT 0,
    last_accessed_at TIMESTAMP,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_agent_memories_type ON agent_memories(memory_type);
CREATE INDEX idx_agent_memories_importance ON agent_memories(importance_score DESC);

-- Vector similarity search index
CREATE INDEX idx_agent_memories_embedding ON agent_memories
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- ==========================================
-- Audit & Debugging
-- ==========================================

-- Message Log: Complete conversation history for each agent
CREATE TABLE IF NOT EXISTS message_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    execution_id UUID REFERENCES agent_executions(id) ON DELETE CASCADE,

    -- Message details
    role VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    tool_calls JSONB,
    tool_results JSONB,

    -- Metadata
    message_index INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT valid_message_role CHECK (role IN ('system', 'user', 'assistant', 'tool'))
);

CREATE INDEX idx_message_log_agent_id ON message_log(agent_id);
CREATE INDEX idx_message_log_execution_id ON message_log(execution_id);
CREATE INDEX idx_message_log_message_index ON message_log(agent_id, message_index);

-- System Events: Platform-wide events for monitoring
CREATE TABLE IF NOT EXISTS system_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Event details
    event_type VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    details JSONB,

    -- Context
    task_id UUID REFERENCES tasks(id) ON DELETE SET NULL,
    agent_id UUID REFERENCES agents(id) ON DELETE SET NULL,

    -- Timestamp
    created_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT valid_severity CHECK (severity IN ('debug', 'info', 'warning', 'error', 'critical'))
);

CREATE INDEX idx_system_events_type ON system_events(event_type);
CREATE INDEX idx_system_events_severity ON system_events(severity);
CREATE INDEX idx_system_events_created_at ON system_events(created_at DESC);

-- ==========================================
-- Helper Functions
-- ==========================================

-- Update updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply to relevant tables
CREATE TRIGGER update_tasks_updated_at BEFORE UPDATE ON tasks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_agents_updated_at BEFORE UPDATE ON agents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_agent_trees_updated_at BEFORE UPDATE ON agent_trees
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_knowledge_store_updated_at BEFORE UPDATE ON knowledge_store
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_learned_patterns_updated_at BEFORE UPDATE ON learned_patterns
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to get agent tree depth
CREATE OR REPLACE FUNCTION get_agent_depth(agent_uuid UUID)
RETURNS INTEGER AS $$
DECLARE
    depth INTEGER := 0;
    current_id UUID := agent_uuid;
    parent UUID;
BEGIN
    LOOP
        SELECT parent_id INTO parent FROM agents WHERE id = current_id;
        EXIT WHEN parent IS NULL;
        depth := depth + 1;
        current_id := parent;
    END LOOP;
    RETURN depth;
END;
$$ LANGUAGE plpgsql;

-- Function to get all descendants of an agent
CREATE OR REPLACE FUNCTION get_agent_descendants(agent_uuid UUID)
RETURNS TABLE(descendant_id UUID, generation INTEGER) AS $$
WITH RECURSIVE descendants AS (
    SELECT id, 0 as generation
    FROM agents
    WHERE parent_id = agent_uuid

    UNION ALL

    SELECT a.id, d.generation + 1
    FROM agents a
    INNER JOIN descendants d ON a.parent_id = d.id
)
SELECT id, generation FROM descendants;
$$ LANGUAGE sql;

-- Function for semantic search in knowledge store
CREATE OR REPLACE FUNCTION search_knowledge(
    query_embedding vector(1536),
    match_threshold FLOAT DEFAULT 0.7,
    match_count INTEGER DEFAULT 5,
    category_filter VARCHAR DEFAULT NULL
)
RETURNS TABLE (
    id UUID,
    category VARCHAR,
    data JSONB,
    summary TEXT,
    similarity FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        ks.id,
        ks.category,
        ks.data,
        ks.summary,
        1 - (ks.embedding <=> query_embedding) as similarity
    FROM knowledge_store ks
    WHERE
        (category_filter IS NULL OR ks.category = category_filter)
        AND 1 - (ks.embedding <=> query_embedding) > match_threshold
    ORDER BY ks.embedding <=> query_embedding
    LIMIT match_count;
END;
$$ LANGUAGE plpgsql;

-- Function for semantic search in agent memories
CREATE OR REPLACE FUNCTION search_memories(
    query_embedding vector(1536),
    match_threshold FLOAT DEFAULT 0.7,
    match_count INTEGER DEFAULT 5
)
RETURNS TABLE (
    id UUID,
    memory_type VARCHAR,
    content TEXT,
    importance_score FLOAT,
    similarity FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        am.id,
        am.memory_type,
        am.content,
        am.importance_score,
        1 - (am.embedding <=> query_embedding) as similarity
    FROM agent_memories am
    WHERE 1 - (am.embedding <=> query_embedding) > match_threshold
    ORDER BY am.embedding <=> query_embedding
    LIMIT match_count;
END;
$$ LANGUAGE plpgsql;

-- Function to calculate task metrics
CREATE OR REPLACE FUNCTION calculate_task_metrics(task_uuid UUID)
RETURNS TABLE (
    total_agents BIGINT,
    max_depth INTEGER,
    total_tool_calls BIGINT,
    total_cost NUMERIC,
    tool_call_breakdown JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        COUNT(DISTINCT a.id) as total_agents,
        MAX(a.depth) as max_depth,
        COUNT(tc.id) as total_tool_calls,
        COALESCE(SUM(a.cost_usd), 0) + COALESCE(SUM(tc.cost_usd), 0) as total_cost,
        jsonb_object_agg(tc.tool_name, COUNT(tc.id)) FILTER (WHERE tc.tool_name IS NOT NULL) as tool_call_breakdown
    FROM agents a
    LEFT JOIN tool_calls tc ON a.id = tc.agent_id
    WHERE a.task_id = task_uuid
    GROUP BY a.task_id;
END;
$$ LANGUAGE plpgsql;

-- Initialization complete
DO $$
BEGIN
    RAISE NOTICE 'AGI Platform database schema initialized successfully';
    RAISE NOTICE 'Recursive subagent architecture ready';
END $$;

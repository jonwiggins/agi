-- AGI Platform Database Initialization Script
-- This script sets up the core database schema for the AGI platform

-- Enable pgvector extension for vector similarity search
CREATE EXTENSION IF NOT EXISTS vector;

-- Enable UUID extension for unique identifiers
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ==========================================
-- Core Tables
-- ==========================================

-- Tasks: Stores all tasks submitted to the AGI
CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    description TEXT NOT NULL,
    context TEXT,
    priority VARCHAR(20) DEFAULT 'medium',
    status VARCHAR(50) DEFAULT 'pending',

    -- Execution details
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,

    -- Results
    result JSONB,
    reasoning_trace JSONB,

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Indexing
    CONSTRAINT valid_priority CHECK (priority IN ('low', 'medium', 'high', 'critical')),
    CONSTRAINT valid_status CHECK (status IN ('pending', 'in_progress', 'completed', 'failed', 'cancelled'))
);

CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_created_at ON tasks(created_at DESC);
CREATE INDEX idx_tasks_priority ON tasks(priority);

-- Sessions: Tracks conversation and interaction sessions
CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255),
    context JSONB,

    -- Session lifecycle
    started_at TIMESTAMP DEFAULT NOW(),
    last_activity_at TIMESTAMP DEFAULT NOW(),
    ended_at TIMESTAMP,

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_sessions_last_activity ON sessions(last_activity_at DESC);

-- Messages: Individual messages in sessions
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,

    -- Message content
    role VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT valid_role CHECK (role IN ('user', 'assistant', 'system', 'tool'))
);

CREATE INDEX idx_messages_session_id ON messages(session_id);
CREATE INDEX idx_messages_created_at ON messages(created_at DESC);

-- ==========================================
-- Memory System Tables
-- ==========================================

-- Episodic Memory: Records of experiences and events
CREATE TABLE IF NOT EXISTS episodic_memory (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Event details
    event_type VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    context JSONB,

    -- Associations
    task_id UUID REFERENCES tasks(id) ON DELETE SET NULL,
    session_id UUID REFERENCES sessions(id) ON DELETE SET NULL,

    -- Outcome and learning
    outcome VARCHAR(50),
    success BOOLEAN,
    insights JSONB,

    -- Vector embedding for semantic search
    embedding vector(1536),

    -- Temporal
    occurred_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),

    -- Importance and relevance
    importance_score FLOAT DEFAULT 0.5,
    access_count INTEGER DEFAULT 0,
    last_accessed_at TIMESTAMP
);

CREATE INDEX idx_episodic_memory_event_type ON episodic_memory(event_type);
CREATE INDEX idx_episodic_memory_occurred_at ON episodic_memory(occurred_at DESC);
CREATE INDEX idx_episodic_memory_importance ON episodic_memory(importance_score DESC);

-- Create HNSW index for vector similarity search
CREATE INDEX idx_episodic_memory_embedding ON episodic_memory
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- Semantic Memory: Knowledge and facts
CREATE TABLE IF NOT EXISTS semantic_memory (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Knowledge content
    knowledge_type VARCHAR(100) NOT NULL,
    subject VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,

    -- Relationships
    related_concepts JSONB,

    -- Vector embedding
    embedding vector(1536),

    -- Confidence and verification
    confidence_score FLOAT DEFAULT 0.5,
    verified BOOLEAN DEFAULT FALSE,
    source VARCHAR(255),

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    access_count INTEGER DEFAULT 0,
    last_accessed_at TIMESTAMP
);

CREATE INDEX idx_semantic_memory_subject ON semantic_memory(subject);
CREATE INDEX idx_semantic_memory_knowledge_type ON semantic_memory(knowledge_type);
CREATE INDEX idx_semantic_memory_confidence ON semantic_memory(confidence_score DESC);

-- Create HNSW index for vector similarity search
CREATE INDEX idx_semantic_memory_embedding ON semantic_memory
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- Procedural Memory: Skills and procedures
CREATE TABLE IF NOT EXISTS procedural_memory (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Skill details
    skill_name VARCHAR(255) NOT NULL,
    description TEXT,
    procedure JSONB NOT NULL,

    -- Prerequisites and context
    prerequisites JSONB,
    applicable_contexts JSONB,

    -- Performance metrics
    success_rate FLOAT DEFAULT 0.0,
    execution_count INTEGER DEFAULT 0,
    avg_execution_time FLOAT,

    -- Learning
    learned_from UUID REFERENCES episodic_memory(id) ON DELETE SET NULL,

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_used_at TIMESTAMP
);

CREATE INDEX idx_procedural_memory_skill_name ON procedural_memory(skill_name);
CREATE INDEX idx_procedural_memory_success_rate ON procedural_memory(success_rate DESC);

-- ==========================================
-- Knowledge Graph
-- ==========================================

-- Concepts: Nodes in the knowledge graph
CREATE TABLE IF NOT EXISTS concepts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    category VARCHAR(100),

    -- Vector embedding
    embedding vector(1536),

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_concepts_name ON concepts(name);
CREATE INDEX idx_concepts_category ON concepts(category);

-- Relationships: Edges in the knowledge graph
CREATE TABLE IF NOT EXISTS concept_relationships (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Relationship
    from_concept_id UUID REFERENCES concepts(id) ON DELETE CASCADE,
    to_concept_id UUID REFERENCES concepts(id) ON DELETE CASCADE,
    relationship_type VARCHAR(100) NOT NULL,

    -- Strength and metadata
    strength FLOAT DEFAULT 1.0,
    metadata JSONB,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT different_concepts CHECK (from_concept_id != to_concept_id)
);

CREATE INDEX idx_concept_relationships_from ON concept_relationships(from_concept_id);
CREATE INDEX idx_concept_relationships_to ON concept_relationships(to_concept_id);
CREATE INDEX idx_concept_relationships_type ON concept_relationships(relationship_type);

-- ==========================================
-- System Tables
-- ==========================================

-- Goals: Tracks AGI's goals and objectives
CREATE TABLE IF NOT EXISTS goals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Goal details
    title VARCHAR(255) NOT NULL,
    description TEXT,
    type VARCHAR(50),

    -- Hierarchy
    parent_goal_id UUID REFERENCES goals(id) ON DELETE CASCADE,

    -- Status
    status VARCHAR(50) DEFAULT 'active',
    progress FLOAT DEFAULT 0.0,

    -- Priority
    priority INTEGER DEFAULT 5,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    target_date TIMESTAMP,
    completed_at TIMESTAMP,

    CONSTRAINT valid_goal_status CHECK (status IN ('active', 'completed', 'abandoned', 'paused')),
    CONSTRAINT valid_progress CHECK (progress >= 0.0 AND progress <= 1.0)
);

CREATE INDEX idx_goals_status ON goals(status);
CREATE INDEX idx_goals_priority ON goals(priority DESC);
CREATE INDEX idx_goals_parent ON goals(parent_goal_id);

-- Reflections: Meta-cognitive insights and self-analysis
CREATE TABLE IF NOT EXISTS reflections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Reflection content
    type VARCHAR(100) NOT NULL,
    subject TEXT NOT NULL,
    insights JSONB NOT NULL,

    -- Context
    related_task_id UUID REFERENCES tasks(id) ON DELETE SET NULL,
    related_goal_id UUID REFERENCES goals(id) ON DELETE SET NULL,

    -- Action items
    action_items JSONB,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_reflections_type ON reflections(type);
CREATE INDEX idx_reflections_created_at ON reflections(created_at DESC);

-- ==========================================
-- Audit and Logging
-- ==========================================

-- Audit Log: Complete record of all actions
CREATE TABLE IF NOT EXISTS audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Action details
    action_type VARCHAR(100) NOT NULL,
    entity_type VARCHAR(100),
    entity_id UUID,

    -- Details
    description TEXT,
    metadata JSONB,

    -- User/system
    actor VARCHAR(100) DEFAULT 'system',

    -- Timestamp
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_audit_log_action_type ON audit_log(action_type);
CREATE INDEX idx_audit_log_entity_type ON audit_log(entity_type);
CREATE INDEX idx_audit_log_created_at ON audit_log(created_at DESC);

-- ==========================================
-- Helper Functions
-- ==========================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at trigger to relevant tables
CREATE TRIGGER update_tasks_updated_at BEFORE UPDATE ON tasks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_sessions_updated_at BEFORE UPDATE ON sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_semantic_memory_updated_at BEFORE UPDATE ON semantic_memory
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_procedural_memory_updated_at BEFORE UPDATE ON procedural_memory
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_concepts_updated_at BEFORE UPDATE ON concepts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_goals_updated_at BEFORE UPDATE ON goals
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function for semantic search
CREATE OR REPLACE FUNCTION search_memories(
    query_embedding vector(1536),
    match_threshold float DEFAULT 0.7,
    match_count int DEFAULT 5
)
RETURNS TABLE (
    id uuid,
    memory_type text,
    content text,
    similarity float
) AS $$
BEGIN
    RETURN QUERY
    (
        SELECT
            em.id,
            'episodic'::text as memory_type,
            em.description as content,
            1 - (em.embedding <=> query_embedding) as similarity
        FROM episodic_memory em
        WHERE 1 - (em.embedding <=> query_embedding) > match_threshold
        ORDER BY em.embedding <=> query_embedding
        LIMIT match_count
    )
    UNION ALL
    (
        SELECT
            sm.id,
            'semantic'::text as memory_type,
            sm.content,
            1 - (sm.embedding <=> query_embedding) as similarity
        FROM semantic_memory sm
        WHERE 1 - (sm.embedding <=> query_embedding) > match_threshold
        ORDER BY sm.embedding <=> query_embedding
        LIMIT match_count
    )
    ORDER BY similarity DESC
    LIMIT match_count;
END;
$$ LANGUAGE plpgsql;

-- Initialization complete
DO $$
BEGIN
    RAISE NOTICE 'AGI Platform database schema initialized successfully';
END $$;

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Knowledge Bases (Collections)
CREATE TABLE IF NOT EXISTS knowledge_bases (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    kb_type VARCHAR(50) NOT NULL DEFAULT 'generic',
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    tags TEXT,
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_kb_name ON knowledge_bases(name);
CREATE INDEX idx_kb_slug ON knowledge_bases(slug);
CREATE INDEX idx_kb_type ON knowledge_bases(kb_type);
CREATE INDEX idx_kb_created_at ON knowledge_bases(created_at);

-- Documents
CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    kb_id INTEGER NOT NULL REFERENCES knowledge_bases(id) ON DELETE CASCADE,
    doc_id VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    embedding vector(768),  -- nomic-embed-text produces 768-dim vectors
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(kb_id, doc_id)
);

CREATE INDEX idx_doc_kb_id ON documents(kb_id);
CREATE INDEX idx_doc_doc_id ON documents(doc_id);
CREATE INDEX idx_doc_metadata ON documents USING GIN(metadata);
CREATE INDEX idx_doc_embedding ON documents USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Agent OS specific content types
CREATE TABLE IF NOT EXISTS agent_os_content (
    id SERIAL PRIMARY KEY,
    kb_id INTEGER NOT NULL REFERENCES knowledge_bases(id) ON DELETE CASCADE,
    content_type VARCHAR(50) NOT NULL,  -- standard, agent, workflow, command, product, spec
    name VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    file_path TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(kb_id, content_type, name)
);

CREATE INDEX idx_aos_kb_id ON agent_os_content(kb_id);
CREATE INDEX idx_aos_content_type ON agent_os_content(content_type);
CREATE INDEX idx_aos_name ON agent_os_content(name);
CREATE INDEX idx_aos_metadata ON agent_os_content USING GIN(metadata);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to auto-update updated_at
CREATE TRIGGER update_kb_updated_at BEFORE UPDATE ON knowledge_bases
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Helper function for cosine similarity search
CREATE OR REPLACE FUNCTION search_documents(
    p_kb_id INTEGER,
    p_query_embedding vector(768),
    p_limit INTEGER DEFAULT 10,
    p_metadata_filter JSONB DEFAULT NULL
)
RETURNS TABLE (
    doc_id VARCHAR,
    content TEXT,
    similarity FLOAT,
    metadata JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        d.doc_id,
        d.content,
        1 - (d.embedding <=> p_query_embedding) AS similarity,
        d.metadata
    FROM documents d
    WHERE d.kb_id = p_kb_id
        AND (p_metadata_filter IS NULL OR d.metadata @> p_metadata_filter)
    ORDER BY d.embedding <=> p_query_embedding
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;


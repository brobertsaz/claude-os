-- ============================================================================
-- Code-Forge PGVectorStore-Compatible Schema
-- ============================================================================
-- This schema is designed to work with llama_index's PGVectorStore
-- while maintaining multi-tenancy support for multiple knowledge bases.
--
-- Strategy: Separate table per KB (data_{kb_name})
-- - Clean isolation between KBs
-- - Easy to delete entire KB (DROP TABLE)
-- - Matches PGVectorStore's expected structure
-- ============================================================================

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================================
-- METADATA TABLE: knowledge_bases
-- ============================================================================
-- Tracks all knowledge bases in the system
-- Each KB gets its own data_{kb_name} table created dynamically
-- ============================================================================

-- Create or alter knowledge_bases table
DO $$
BEGIN
    -- Create table if it doesn't exist
    CREATE TABLE IF NOT EXISTS knowledge_bases (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) UNIQUE NOT NULL,
        slug VARCHAR(255) UNIQUE NOT NULL,
        kb_type VARCHAR(50) DEFAULT 'GENERIC',
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        metadata JSONB DEFAULT '{}'::jsonb
    );

    -- Add new columns if they don't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='knowledge_bases' AND column_name='slug') THEN
        ALTER TABLE knowledge_bases ADD COLUMN slug VARCHAR(255) UNIQUE;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='knowledge_bases' AND column_name='table_name') THEN
        ALTER TABLE knowledge_bases ADD COLUMN table_name VARCHAR(255) UNIQUE;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='knowledge_bases' AND column_name='embed_dim') THEN
        ALTER TABLE knowledge_bases ADD COLUMN embed_dim INTEGER NOT NULL DEFAULT 768;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='knowledge_bases' AND column_name='updated_at') THEN
        ALTER TABLE knowledge_bases ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
    END IF;

    -- Add constraints if they don't exist
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'valid_kb_type') THEN
        ALTER TABLE knowledge_bases ADD CONSTRAINT valid_kb_type
            CHECK (kb_type IN ('GENERIC', 'CODE', 'DOCUMENTATION', 'AGENT_OS'));
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'valid_table_name') THEN
        ALTER TABLE knowledge_bases ADD CONSTRAINT valid_table_name
            CHECK (table_name IS NULL OR table_name ~ '^data_[a-z0-9_]+$');
    END IF;
END$$;

-- Index for fast lookups
CREATE INDEX IF NOT EXISTS idx_kb_name ON knowledge_bases(name);
CREATE INDEX IF NOT EXISTS idx_kb_slug ON knowledge_bases(slug);
CREATE INDEX IF NOT EXISTS idx_kb_table_name ON knowledge_bases(table_name);
CREATE INDEX IF NOT EXISTS idx_kb_type ON knowledge_bases(kb_type);

-- ============================================================================
-- VECTOR STORE TABLES: data_{kb_name}
-- ============================================================================
-- These tables are created dynamically per KB using the template below.
-- PGVectorStore expects this exact structure.
--
-- Example for KB named "pistn":
-- ============================================================================

-- TEMPLATE (not executed, just for reference):
/*
CREATE TABLE data_{kb_name} (
    id BIGSERIAL PRIMARY KEY,
    text VARCHAR NOT NULL,              -- Document text content
    metadata_ JSON,                     -- Document metadata (JSONB for better performance)
    node_id VARCHAR,                    -- llama_index node identifier
    embedding vector({embed_dim})       -- Vector embedding (768 for nomic-embed-text)
);

-- Index for metadata filtering (ref_doc_id is commonly used)
CREATE INDEX idx_{kb_name}_metadata_ref_doc
    ON data_{kb_name} ((metadata_ ->> 'ref_doc_id'));

-- Vector similarity index (IVFFlat for fast approximate search)
CREATE INDEX idx_{kb_name}_embedding
    ON data_{kb_name}
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- Optional: HNSW index for even faster search (requires more memory)
-- CREATE INDEX idx_{kb_name}_embedding_hnsw
--     ON data_{kb_name}
--     USING hnsw (embedding vector_cosine_ops)
--     WITH (m = 16, ef_construction = 64);
*/

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Function to create a new KB table
CREATE OR REPLACE FUNCTION create_kb_table(
    p_kb_name VARCHAR,
    p_table_name VARCHAR,
    p_embed_dim INTEGER DEFAULT 768
) RETURNS VOID AS $$
DECLARE
    v_index_suffix VARCHAR;
BEGIN
    -- Create safe index suffix from table name (remove data_ prefix)
    v_index_suffix := REPLACE(p_table_name, 'data_', '');

    -- Create the data table
    EXECUTE format('
        CREATE TABLE IF NOT EXISTS %I (
            id BIGSERIAL PRIMARY KEY,
            text VARCHAR NOT NULL,
            metadata_ JSON,
            node_id VARCHAR,
            embedding vector(%s)
        )', p_table_name, p_embed_dim);

    -- Create metadata index
    EXECUTE format('
        CREATE INDEX IF NOT EXISTS %I
        ON %I ((metadata_ ->> ''ref_doc_id''))',
        'idx_' || v_index_suffix || '_metadata_ref_doc',
        p_table_name);

    -- Create vector index (IVFFlat)
    EXECUTE format('
        CREATE INDEX IF NOT EXISTS %I
        ON %I USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100)',
        'idx_' || v_index_suffix || '_embedding',
        p_table_name);

    RAISE NOTICE 'Created table % with vector dimension %', p_table_name, p_embed_dim;
END;
$$ LANGUAGE plpgsql;

-- Function to drop a KB table
CREATE OR REPLACE FUNCTION drop_kb_table(p_table_name VARCHAR) RETURNS VOID AS $$
BEGIN
    EXECUTE format('DROP TABLE IF EXISTS %I CASCADE', p_table_name);
    RAISE NOTICE 'Dropped table %', p_table_name;
END;
$$ LANGUAGE plpgsql;

-- Function to get KB stats
CREATE OR REPLACE FUNCTION get_kb_stats(p_table_name VARCHAR)
RETURNS TABLE(
    total_documents BIGINT,
    avg_text_length NUMERIC,
    total_size_bytes BIGINT
) AS $$
BEGIN
    RETURN QUERY EXECUTE format('
        SELECT
            COUNT(*)::BIGINT as total_documents,
            AVG(LENGTH(text))::NUMERIC as avg_text_length,
            pg_total_relation_size(%L)::BIGINT as total_size_bytes
        FROM %I',
        p_table_name, p_table_name);
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- MIGRATION NOTES
-- ============================================================================
-- To migrate from old schema (documents table) to new schema:
--
-- 1. For each KB in knowledge_bases:
--    - Create new data_{kb_name} table using create_kb_table()
--    - Copy data from documents WHERE kb_id = X to data_{kb_name}
--    - Transform columns: content -> text, metadata -> metadata_
--    - Generate node_id if not present
--
-- 2. Update knowledge_bases table:
--    - Add table_name column
--    - Add embed_dim column
--
-- 3. Drop old documents table after verification
--
-- See scripts/migrate_to_pgvector.py for automated migration
-- ============================================================================

-- ============================================================================
-- EXAMPLE USAGE
-- ============================================================================
/*
-- Create a new KB
INSERT INTO knowledge_bases (name, kb_type, description, table_name, embed_dim)
VALUES ('pistn', 'CODE', 'Pistn appointment system documentation', 'data_pistn', 768);

-- Create the table
SELECT create_kb_table('pistn', 'data_pistn', 768);

-- Insert a document (normally done via PGVectorStore)
INSERT INTO data_pistn (text, metadata_, node_id, embedding)
VALUES (
    'Sample document text',
    '{"filename": "test.md", "source": "upload"}'::json,
    'node_abc123',
    '[0.1, 0.2, ...]'::vector(768)
);

-- Query similar documents
SELECT
    text,
    metadata_,
    1 - (embedding <=> '[0.1, 0.2, ...]'::vector(768)) as similarity
FROM data_pistn
ORDER BY embedding <=> '[0.1, 0.2, ...]'::vector(768)
LIMIT 10;

-- Get KB stats
SELECT * FROM get_kb_stats('data_pistn');

-- Delete a KB
DELETE FROM knowledge_bases WHERE name = 'pistn';
SELECT drop_kb_table('data_pistn');
*/


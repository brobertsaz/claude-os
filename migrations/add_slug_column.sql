-- Migration: Add slug column to knowledge_bases table
-- Date: 2025-10-24
-- Description: Adds a URL-friendly slug column for KB-specific MCP endpoints

-- Add slug column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'knowledge_bases' AND column_name = 'slug'
    ) THEN
        ALTER TABLE knowledge_bases ADD COLUMN slug VARCHAR(255);
    END IF;
END $$;

-- Generate slugs for existing KBs
UPDATE knowledge_bases
SET slug = LOWER(
    REGEXP_REPLACE(
        REGEXP_REPLACE(
            REGEXP_REPLACE(name, '[^a-zA-Z0-9\s-]', '', 'g'),
            '[\s_]+', '-', 'g'
        ),
        '-+', '-', 'g'
    )
)
WHERE slug IS NULL;

-- Make slug unique and not null
ALTER TABLE knowledge_bases ALTER COLUMN slug SET NOT NULL;
ALTER TABLE knowledge_bases ADD CONSTRAINT knowledge_bases_slug_unique UNIQUE (slug);

-- Create index for fast slug lookups
CREATE INDEX IF NOT EXISTS idx_kb_slug ON knowledge_bases(slug);

-- Verify migration
SELECT name, slug FROM knowledge_bases ORDER BY created_at;


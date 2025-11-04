-- Migration: Add Spec and Task Tracking for agent-os integration
-- Created: 2025-11-04
-- Purpose: Track agent-os specs and tasks in Claude OS for Kanban board

-- Specs table: Tracks specifications from agent-os/specs folders
CREATE TABLE IF NOT EXISTS specs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    slug TEXT NOT NULL,
    folder_name TEXT NOT NULL,  -- e.g., 2025-10-29-manual-appointment-times
    path TEXT NOT NULL,  -- Full path to spec folder
    total_tasks INTEGER DEFAULT 0,
    completed_tasks INTEGER DEFAULT 0,
    status TEXT DEFAULT 'planning',  -- planning, in_progress, completed, blocked
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT DEFAULT '{}',
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

-- Spec tasks table: Individual tasks from tasks.md
CREATE TABLE IF NOT EXISTS spec_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    spec_id INTEGER NOT NULL,
    task_code TEXT NOT NULL,  -- e.g., PHASE1-TASK1
    phase TEXT NOT NULL,  -- e.g., Phase 1
    title TEXT NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'todo',  -- todo, in_progress, done, blocked
    estimated_minutes INTEGER,
    actual_minutes INTEGER,
    risk_level TEXT,  -- low, medium, high
    dependencies TEXT DEFAULT '[]',  -- JSON array of task_codes
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (spec_id) REFERENCES specs(id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_specs_project ON specs(project_id);
CREATE INDEX IF NOT EXISTS idx_specs_status ON specs(status);
CREATE INDEX IF NOT EXISTS idx_specs_folder ON specs(folder_name);
CREATE INDEX IF NOT EXISTS idx_tasks_spec ON spec_tasks(spec_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON spec_tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_code ON spec_tasks(task_code);

-- Unique constraint: one spec per folder per project
CREATE UNIQUE INDEX IF NOT EXISTS idx_specs_unique ON specs(project_id, folder_name);

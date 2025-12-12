---
description: Initialize a new project with Claude OS
---

# Claude OS Project Initialization

You are helping the user initialize a new project with Claude OS. This is a multi-step interactive process that will:

1. Gather project information
2. Create the project in Claude OS via API
3. Set up project directory structure
4. Optionally ingest documentation
5. Analyze the codebase
6. Generate summary

## Process

### Step 0: Determine Claude OS Directory

Derive `{claude_os_dir}` from the path of this command file - it is two directories up from this file's location. For example, if this file is at `/home/user/repos/claude-os/templates/commands/claude-os-init.md`, then `{claude_os_dir}` is `/home/user/repos/claude-os`.

Use this path for all template references below.

### Step 1: Gather Project Information

Ask the user the following questions (provide smart defaults when possible):

```
👋 Welcome to Claude OS Setup!

Let's get your project configured for AI-powered development.
```

**Questions to ask:**

1. **Project name**:
   - Auto-detect from current directory name
   - Show: `Project name? [default: {current_dir_name}]`
   - Validate: Must be lowercase, alphanumeric with dashes/underscores only

2. **Project path**:
   - Use: `pwd` to get current directory
   - Don't ask, just use it

3. **Tech stack**:
   - Ask: `Tech stack? (e.g., Ruby on Rails, Python/Django, Node.js/React, etc.)`
   - Example answers to show: "Ruby on Rails", "Python/Django", "Node.js/Express", "Go", "Rust"

4. **Database**:
   - Ask: `Database? (e.g., PostgreSQL, MySQL, MongoDB, SQLite, etc.)`
   - Example answers: "PostgreSQL", "MySQL", "MongoDB", "SQLite", "None"

5. **Development environment**:
   - Ask: `Development environment? (e.g., Docker, Local, Docker Compose)`
   - Example answers: "Docker", "Local", "Docker Compose", "Kubernetes"

6. **Brief description**:
   - Ask: `Brief description? (1-2 sentences about what this project does)`
   - Required

7. **Documentation directory** (Optional):
   - Ask: `Do you have project documentation to index? [Y/n]`
   - If YES:
     - Ask: `Documentation directory path? (e.g., ./docs, ./documentation, /knowledge_docs)`
     - Use Glob to scan and show what you found:
       ```bash
       find {docs_path} -type f \( -name "*.md" -o -name "*.txt" -o -name "*.pdf" \) | head -20
       ```
     - Show summary: `Found: X markdown files, Y text files, Z PDFs`
     - Ask: `Ingest all of these? [Y/n]`

8. **Claude OS server URL**:
   - Default: `http://localhost:8051`
   - Ask: `Claude OS server URL? [default: http://localhost:8051]`

9. **Agent-OS Setup** (Optional - for advanced users):
   - Ask: `Enable Agent-OS for spec-driven development? [y/N]`
   - Explain:
     ```
     Agent-OS provides 8 specialized agents for structured feature development:
     - Gather requirements through iterative questions
     - Create detailed specifications
     - Generate task breakdowns
     - Implement and verify features

     This is recommended for complex projects with formal spec workflows.
     Note: Requires Ollama (local) or OpenAI API key for advanced features.
     ```
   - If YES:
     - Set `ENABLE_AGENT_OS=true`
     - Will create `agent-os/` directory structure
     - Will symlink agents to `.claude/agents/agent-os/`
   - If NO (default):
     - Set `ENABLE_AGENT_OS=false`
     - Can enable later by manually copying templates

### Step 2: Create Project in Claude OS

Use Bash to call the API:

```bash
curl -X POST {claude_os_url}/api/projects \
  -H "Content-Type: application/json" \
  -d '{
    "name": "{project_name}",
    "path": "{project_path}",
    "description": "{description}"
  }'
```

**Expected response:**
```json
{
  "project": {"id": 1, "name": "...", "path": "..."},
  "mcps": [
    {"mcp_type": "knowledge_docs", "kb_name": "{project_name}-knowledge_docs"},
    {"mcp_type": "project_profile", "kb_name": "{project_name}-project_profile"},
    {"mcp_type": "project_index", "kb_name": "{project_name}-project_index"},
    {"mcp_type": "project_memories", "kb_name": "{project_name}-project_memories"}
  ],
  "message": "Project created..."
}
```

Show success message:
```
📡 Creating project in Claude OS...
✅ Project created!
✅ Knowledge bases created:
   - {project_name}-project_memories
   - {project_name}-project_profile
   - {project_name}-project_index
   - {project_name}-knowledge_docs
```

### Step 3: Set Up Project Directory Structure

Create the following structure in the project directory:

**Create .claude/ directory:**
```bash
mkdir -p .claude/commands
mkdir -p .claude/skills
mkdir -p .claude/agents
```

**Create .claude-os/ directory:**
```bash
mkdir -p .claude-os
```

**Copy and customize CLAUDE.md:**
- Read template from: `{claude_os_dir}/templates/project-files/CLAUDE.md.template`
- Replace variables:
  - `{{PROJECT_NAME}}` → project_name
  - `{{PROJECT_DESCRIPTION}}` → description
  - `{{TECH_STACK}}` → tech_stack
  - `{{DATABASE}}` → database
  - `{{DEV_ENVIRONMENT}}` → dev_environment
  - `{{CLAUDE_OS_DIR}}` → {claude_os_dir}
  - `{{PROJECT_SPECIFIC_CONTENT}}` → empty for now
  - `{{DEVELOPMENT_GUIDELINES}}` → empty for now
  - `{{COMMON_TASKS}}` → empty for now
  - `{{BUSINESS_RULES}}` → empty for now
- Write to: `./CLAUDE.md`

**Create .claude-os/config.json:**
- Read template from: `{claude_os_dir}/templates/project-files/.claude-os/config.json.template`
- Replace variables:
  - `{{PROJECT_NAME}}` → project_name
  - `{{CLAUDE_OS_URL}}` → claude_os_url
  - `{{DOCS_PATHS}}` → JSON array of docs paths
  - `{{TECH_STACK}}` → tech_stack
  - `{{DATABASE}}` → database
  - `{{DEV_ENVIRONMENT}}` → dev_environment
  - `{{CREATED_AT}}` → ISO timestamp
- Write to: `./.claude-os/config.json`

**Create .claude-os/hooks.json:**
- Read template from: `{claude_os_dir}/templates/project-files/.claude-os/hooks.json.template`
- Replace `{{PROJECT_NAME}}` → project_name
- Write to: `./.claude-os/hooks.json`

**Copy .gitignore:**
- Copy from: `{claude_os_dir}/templates/project-files/.claude-os/.gitignore`
- Write to: `./.claude-os/.gitignore`

**Install TDD Skill (always - best practice for all projects):**
- Create directory: `mkdir -p ./.claude/skills/test-driven-development`
- Copy from: `{claude_os_dir}/templates/skills/test-driven-development/SKILL.md`
- Write to: `./.claude/skills/test-driven-development/SKILL.md`
- Show:
  ```
  ✅ Installed TDD skill (test-driven-development)
     - Guides RED-GREEN-REFACTOR workflow
     - Ensures tests fail first, then pass
     - Use: "I'm using the TDD skill to implement this feature"
  ```

**If Agent-OS is enabled (`ENABLE_AGENT_OS=true`):**

1. **Create agent-os/ directory structure:**
   ```bash
   mkdir -p agent-os/product
   mkdir -p agent-os/specs
   mkdir -p agent-os/standards/backend
   mkdir -p agent-os/standards/frontend
   mkdir -p agent-os/standards/global
   mkdir -p agent-os/standards/testing
   ```

2. **Copy agent-os config:**
   - Read: `{claude_os_dir}/templates/project-files/agent-os/config.yml.template`
   - Replace `{{TIMESTAMP}}` with current timestamp
   - Write to: `./agent-os/config.yml`

3. **Copy agent-os README:**
   - Read: `{claude_os_dir}/templates/project-files/agent-os/README.md`
   - Replace `{{PROJECT_NAME}}` → project_name
   - Write to: `./agent-os/README.md`

4. **Copy agent-os .gitignore:**
   - Copy: `{claude_os_dir}/templates/project-files/agent-os/.gitignore`
   - Write to: `./agent-os/.gitignore`

5. **Symlink agent-os agents:**
   ```bash
   mkdir -p .claude/agents/agent-os

   # Symlink all agents
   ln -s {claude_os_dir}/templates/agents/*.md .claude/agents/agent-os/
   ```

6. **Update CLAUDE.md with agent-os section:**
   - Read: `{claude_os_dir}/templates/project-files/agent-os-section.md`
   - Replace `{{AGENT_OS_SECTION}}` in CLAUDE.md with this content
   - Or if `{{AGENT_OS_SECTION}}` not present, leave empty

Show progress:
```
📁 Creating project structure...
   ✅ Created .claude/
   ✅ Created .claude-os/
   ✅ Created agent-os/ (with 8 agents)
   ✅ Created CLAUDE.md
   ✅ Created config files
```

### Step 4: Ingest Documentation (if provided)

If user provided a docs directory:

```bash
curl -X POST {claude_os_url}/api/kb/{project_name}-knowledge_docs/import \
  -H "Content-Type: application/json" \
  -d '{"directory_path": "{docs_path}"}'
```

Show progress:
```
📚 Ingesting documentation...

   Uploading to {project_name}-knowledge_docs:
   ✅ {successful} files indexed
   ❌ {failed} files failed

   Vector embeddings generated and searchable!
```

### Step 5: Phase 1 - Structural Indexing (FAST!)

**NEW: Lightning-fast hybrid indexing with tree-sitter!**

First, create the code_structure knowledge base:

```bash
curl -X POST {claude_os_url}/api/kb/create \
  -H "Content-Type: application/json" \
  -d '{
    "name": "{project_name}-code_structure",
    "kb_type": "generic",
    "description": "Structural code index (tree-sitter)"
  }'
```

Check if directory has code files (not just a new empty project):

```bash
find . -type f \( -name "*.rb" -o -name "*.py" -o -name "*.js" -o -name "*.ts" -o -name "*.go" \) | head -1
```

If code exists, run structural indexing:

```
⚡ Phase 1: Structural Indexing...

   Building code structure map with tree-sitter...
   This takes ~30 seconds for 10,000 files!
```

Call the API:

```bash
curl -X POST {claude_os_url}/api/kb/{project_name}-code_structure/index-structural \
  -H "Content-Type: application/json" \
  -d '{
    "project_path": "{project_path}",
    "token_budget": 2048
  }'
```

**Expected response:**
```json
{
  "success": true,
  "total_files": 1234,
  "total_symbols": 5678,
  "time_taken_seconds": 28.5,
  "message": "Structural index created: 5678 symbols in 1234 files"
}
```

Show success:
```
   ✅ Structural index complete!
      - Parsed {total_files} files
      - Extracted {total_symbols} symbols (classes, functions, methods)
      - Dependency graph built
      - PageRank importance computed
      - Time: {time_taken_seconds}s

   🎯 Ready to code! I now know your entire codebase structure.
```

### Step 6: Phase 2 - Semantic Indexing (Optional)

Ask the user if they want semantic indexing:

```
⚡ Phase 2: Semantic Indexing (Optional)

Phase 1 is complete! You can start coding now.

Would you like to run Phase 2 semantic indexing? This enables:
- Deep semantic search ("How does auth work?")
- More detailed context for complex queries
- Only indexes top 20% most important files + docs

Options:
  1. Yes, selective (top 20% + docs) - Recommended (~20 minutes)
  2. Yes, full (all files) - Complete but slow (~1-3 hours)
  3. No, skip for now - Can run later anytime

Your choice? [1/2/3]
```

**If option 1 (Selective):**

```bash
curl -X POST {claude_os_url}/api/kb/{project_name}-project_index/index-semantic \
  -H "Content-Type: application/json" \
  -d '{
    "project_path": "{project_path}",
    "selective": true
  }'
```

Show:
```
   🎯 Selective semantic indexing started!
      - Indexing {files_selected} files (top 20% + docs)
      - Running in background...
      - Estimated time: 20-30 minutes
      - You can start coding now!
```

**If option 2 (Full):**

```bash
curl -X POST {claude_os_url}/api/kb/{project_name}-project_index/index-semantic \
  -H "Content-Type: application/json" \
  -d '{
    "project_path": "{project_path}",
    "selective": false
  }'
```

Show:
```
   📚 Full semantic indexing started!
      - Indexing all {total_files} files
      - Running in background...
      - Estimated time: 1-3 hours
      - You can start coding now!
```

**If option 3 (Skip):**

Show:
```
   ⏭️  Skipped semantic indexing

   You can run it later anytime with:
   curl -X POST {claude_os_url}/api/kb/{project_name}-project_index/index-semantic \
     -H "Content-Type: application/json" \
     -d '{"project_path": "{project_path}", "selective": true}'
```

### Step 7: Analyze Codebase Architecture

If code exists, run the `initialize-project` skill:

```
🔍 Analyzing project architecture...
   Running initialize-project skill...
```

**Invoke the initialize-project skill** (it's a separate skill that already exists).

The skill will generate:
- `.claude/ARCHITECTURE.md`
- `.claude/CODING_STANDARDS.md`
- `.claude/DEVELOPMENT_PRACTICES.md`

Show success:
```
   ✅ Generated:
      - .claude/ARCHITECTURE.md
      - .claude/CODING_STANDARDS.md
      - .claude/DEVELOPMENT_PRACTICES.md
```

### Step 8: Create .gitignore entries (if .gitignore exists)

If `.gitignore` exists in the project root, append (if not already present):

```gitignore
# Claude OS state files (don't commit these)
.claude-os/claude-os-state.json
.claude-os/.index_state
.claude-os/.commit_count
```

### Step 9: Final Summary

Show complete summary:

```
🎉 Setup complete!

Your project is now connected to Claude OS.

📚 Knowledge Bases:
   - {project_name}-code_structure (structural index - {total_symbols} symbols) ⚡
   - {project_name}-project_index (semantic index - optional)
   - {project_name}-project_memories (for decisions & patterns)
   - {project_name}-project_profile (for architecture & standards)
   - {project_name}-knowledge_docs ({X} docs indexed ✅)

🛠️  Available Commands:
   /claude-os-search - Search your project memories & docs
   /claude-os-save - Save insights
   /claude-os-session - Manage development sessions
   /claude-os-remember - Quick save to memories

🧪 TDD Skill Installed:
   - RED-GREEN-REFACTOR workflow built-in
   - Say "I'm using the TDD skill" to activate
   - Write tests first, watch them fail, then implement

📂 Project Structure:
   ./CLAUDE.md - Project context (auto-loaded every session)
   ./.claude/ - Commands, skills, agents
   ./.claude-os/ - Config and state files

📖 Next Steps:
   1. Review and customize CLAUDE.md for your team
   2. Add more docs anytime via UI: {claude_os_url}
   3. Start a session: /claude-os-session start "feature name"
   4. Let's build something amazing!

💡 Tip: With hybrid indexing, I instantly know your entire codebase structure!
   - Structural search is INSTANT (tree-sitter)
   - Semantic search available if you enabled Phase 2
   - I can find anything in seconds!
```

## Error Handling

If any step fails:
1. Show clear error message
2. Provide troubleshooting steps:
   - Check if Claude OS server is running: `curl {claude_os_url}/health`
   - Check if directory is writable
   - Check if project name already exists
3. Offer to retry or skip the step

## Important Notes

- **Don't run on already initialized projects** - Check if `.claude-os/` exists first!
- Always validate inputs before API calls
- Use proper error handling with try/catch
- Save all configuration for potential later use
- Be conversational and encouraging!
- If something goes wrong, explain clearly and offer solutions

## Template Locations

All templates are in:
- `{claude_os_dir}/templates/project-files/`

Commands and skills will be symlinked from:
- `{claude_os_dir}/templates/commands/`
- `{claude_os_dir}/templates/skills/`

(These symlinks are set up during Claude OS installation via `./install.sh`)

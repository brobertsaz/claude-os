---
name: analyze-project
description: "Analyze a project's codebase and documentation to generate coding standards, architecture docs, and development practices. Perfect for new project onboarding. Usage: 'analyze-project: /path/to/project' or 'analyze: /path/to/project'"
allowed-tools: Read, Write, Bash, Glob, Grep
---

# Project Analysis Skill

## Purpose

Automatically analyze any project's codebase, specifications, and coding patterns to generate comprehensive documentation for the project_profile MCP. This enables AI assistants to understand:

- **Coding Standards**: Conventions, naming patterns, style guides
- **Architecture**: Design principles, structural patterns, module organization
- **Development Practices**: Workflows, testing approaches, deployment patterns

## How to Use

Simply say one of:
- **"analyze-project: 4"** - Analyze project with database ID 4
- **"analyze: 4"**
- **"project analysis: 4"**

**How it works:**
1. Fetches project from Claude OS using the database ID
2. Registers all 4 MCPs with Claude Code (if not already registered)
3. Analyzes the project codebase
4. Generates 3 documentation files (saved locally)
5. Creates a concise project summary
6. **Displays summary for you to save to Claude's native memory**
7. MCPs are registered but NOT loaded (saves context tokens)

**Example Workflow:**
```
You: "analyze-project: 1"

→ Loads project from Claude OS (ID #1)
→ Registers 4 MCPs (myapp-project-profile, etc.)
→ Analyzes codebase
→ Generates 3 docs locally
→ Displays summary:

   PROJECT: MyApp (ID: 1)
   TYPE: Rails
   ... (save this to native memory)

→ MCPs ready to load on-demand when you need them
```

**Then:**
```
You (saving to memory): "Remember: [paste the summary above]"

When working on the project: "Load myapp-project-profile"
→ Loads that specific MCP into context only when needed
```

## What Happens

When you invoke this skill:

1. **Scan the project** for source files, specs, and documentation
2. **Analyze code patterns** - naming conventions, structure, style
3. **Review documentation** - README, spec files, guides
4. **Generate 3 documents**:
   - `CODING_STANDARDS.md` - Style, conventions, patterns
   - `ARCHITECTURE.md` - Design, structure, principles
   - `DEVELOPMENT_PRACTICES.md` - Workflows, testing, deployment
5. **Save locally** to `.claude-os/project-profile/` for reference
6. **Ingest to MCP** (if project_id provided) - Adds docs to the project_profile knowledge base in Claude OS

## Document Structure

### CODING_STANDARDS.md
- Naming conventions (variables, functions, classes)
- Code style and formatting
- File organization
- Import/require patterns
- Comment and documentation style
- Linting/formatting rules

### ARCHITECTURE.md
- High-level design patterns
- Module organization
- Data flow and dependencies
- Database schema (if applicable)
- Key architectural decisions
- Technology stack

### DEVELOPMENT_PRACTICES.md
- Development workflow
- Testing strategy and patterns
- Git workflow (branching, commits)
- Code review process
- Deployment and release process
- Build and deployment pipelines
- Common debugging approaches

## Examples

### Example 1: Analyze a Rails Project
```
You: "analyze-project: /Users/me/Projects/my-rails-app"

→ I scan Rails structure (app/, config/, spec/, etc.)
→ Analyze Models, Controllers, Services, Views
→ Review gems and dependencies
→ Generate 3 docs with Rails-specific patterns
→ Save to mcp/kb/my-rails-app-project-profile/
→ Confirm: "✓ Project analysis complete. 3 docs saved to project_profile KB"
```

### Example 2: Analyze Specific Aspects
```
You: "analyze-project: /Users/me/Projects/api-service architecture"

→ Focus on architecture analysis
→ Generate ARCHITECTURE.md
→ Skip coding standards and practices (or generate minimal versions)
```

### Example 3: Re-analyze Project
```
You: "analyze-project: /Users/me/Projects/my-project"

→ Existing docs are replaced with fresh analysis
→ Useful after major refactoring or architecture changes
```

## Key Benefits

✅ **Consistency** - Apply same analysis to any project
✅ **Speed** - Generate docs in seconds instead of hours
✅ **Comprehensive** - Captures coding style, architecture, and practices
✅ **Automatic Integration** - Syncs directly to project_profile MCP
✅ **Reusable** - Same skill works for Rails, Python, Node, Go, etc.
✅ **AI-Friendly** - Docs enable Claude to write better code for your project

## Technical Details

**Output Location**: `mcp/kb/{project-name}-project-profile/`
**Document Names**:
- `CODING_STANDARDS.md`
- `ARCHITECTURE.md`
- `DEVELOPMENT_PRACTICES.md`

**Integration**: Automatically available in Claude OS's project_profile MCP
**Storage**: SQLite via project_profile knowledge base
**Sync**: Uses Claude OS file watcher for auto-updates

## Supported Project Types

- **Rails** - Ruby on Rails applications
- **Python** - Django, FastAPI, Flask projects
- **Node.js** - Express, NestJS, Next.js applications
- **Java** - Spring Boot, Maven/Gradle projects
- **Go** - Standard Go project structure
- **React** - React applications
- **Generic** - Any project with source code and documentation

---

**Pro Tip**: Run this skill immediately after creating a new project in Agent OS. The generated docs become the foundation for AI-assisted development, ensuring all code generation aligns with your project's patterns and practices.

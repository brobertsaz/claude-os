# Skills Library Guide

**Browse, install, and manage Claude Code skills with Claude OS.**

---

## What Are Skills?

Skills are reusable instruction sets that teach Claude specific capabilities. They're stored as markdown files in `.claude/skills/` directories and are automatically loaded by Claude Code when relevant.

Skills can include:
- Coding patterns and best practices
- Tool usage workflows (e.g., PDF manipulation, spreadsheet editing)
- Domain-specific knowledge (e.g., Rails patterns, React hooks)
- Development methodologies (e.g., TDD, debugging frameworks)

---

## Skill Types

### Global Skills (`~/.claude/skills/`)

Available in ALL projects. These are core skills that come with Claude OS:

| Skill | Description |
|-------|-------------|
| `memory` | Save and recall information across sessions |
| `remember-this` | Auto-save on trigger phrases like "remember this:" |
| `initialize-project` | Analyze codebase and generate documentation |

### Project Skills (`{project}/.claude/skills/`)

Available only in the specific project. Install from:
- **Local Templates** - Pre-built skills bundled with Claude OS
- **Community Skills** - Skills from GitHub repositories
- **Custom** - Skills you create yourself

---

## Using the Skills Command

The `/claude-os-skills` command provides full skills management:

```bash
# List all installed skills (global + project)
/claude-os-skills

# Browse available local templates
/claude-os-skills templates

# Install a template to your project
/claude-os-skills install <name>

# Create a custom skill interactively
/claude-os-skills create

# View skill details and content
/claude-os-skills view <name>

# Delete a project skill
/claude-os-skills delete <name>
```

### Example Output

```
═══════════════════════════════════════
📚 CLAUDE CODE SKILLS
═══════════════════════════════════════

🌐 GLOBAL SKILLS (always available)
────────────────────────────────────
  ✓ memory - Save and recall information
  ✓ remember-this - Auto-save on trigger phrases
  ✓ initialize-project - Analyze codebase

📁 PROJECT SKILLS (/path/to/project)
────────────────────────────────────
  ✓ rails-backend - Rails patterns and service objects
  ✓ rspec - RSpec testing patterns

💡 TIP: Run '/claude-os-skills templates' to see available templates
═══════════════════════════════════════
```

---

## Local Skill Templates

Claude OS includes a library of skill templates organized by category:

### Categories

| Category | Skills |
|----------|--------|
| **general** | `analyze-project`, `code-review` |
| **rails** | `rails-backend`, `rails-api`, `active-record` |
| **react** | `react-patterns`, `typescript-react`, `hooks` |
| **testing** | `rspec`, `jest`, `pytest`, `tdd` |

### Installing a Template

```bash
/claude-os-skills install rails-backend
```

This copies the template to your project's `.claude/skills/` directory.

---

## Community Skills

Browse and install skills from trusted GitHub repositories!

### Available Sources

| Source | Repository | Skills | Description |
|--------|------------|--------|-------------|
| **Anthropic Official** | `anthropics/skills` | 16 | Official skills from Anthropic |
| **Superpowers** | `obra/superpowers` | 20 | Battle-tested TDD, debugging, collaboration |

### Featured Community Skills

**From Anthropic Official:**

| Skill | Description |
|-------|-------------|
| `pdf` | Create, edit, analyze PDF documents |
| `xlsx` | Spreadsheet manipulation with formulas |
| `docx` | Word document creation and editing |
| `pptx` | Presentation creation and editing |
| `frontend-design` | Production-grade UI components |
| `mcp-builder` | Create MCP servers |
| `doc-coauthoring` | Collaborative documentation workflow |
| `canvas-design` | Visual art and poster creation |
| `webapp-testing` | Playwright-based web testing |

**From Superpowers:**

| Skill | Description |
|-------|-------------|
| `test-driven-development` | TDD workflow: red-green-refactor |
| `systematic-debugging` | Four-phase debugging framework |
| `root-cause-tracing` | Trace bugs back through call stack |
| `receiving-code-review` | Handle code review feedback |
| `requesting-code-review` | Dispatch code review subagent |
| `brainstorming` | Structured ideation process |
| `using-git-worktrees` | Isolated development branches |
| `verification-before-completion` | Evidence-based completion claims |
| `defense-in-depth` | Multi-layer validation |

### Installing via Web UI

1. Open http://localhost:5173
2. Select your project
3. Click the **Skills** tab
4. Click **Install Template** button
5. Switch to **Community Skills** tab
6. Browse skills from Anthropic Official and Superpowers
7. Click **Install** on any skill

### Installing via API

```bash
# List community sources
curl http://localhost:8051/api/skills/community/sources

# List all community skills
curl http://localhost:8051/api/skills/community

# Filter by source
curl "http://localhost:8051/api/skills/community?source=anthropic"

# Install a community skill
curl -X POST "http://localhost:8051/api/skills/community/install?project_path=/path/to/project" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "pdf",
    "source": "anthropic",
    "repo": "anthropics/skills",
    "path": "skills/pdf"
  }'
```

---

## Creating Custom Skills

### Via Command

```bash
/claude-os-skills create
```

Claude will interactively ask for:
1. Skill name (e.g., "deployment")
2. Description (one sentence)
3. Content (the skill instructions)

### Via API

```bash
curl -X POST "http://localhost:8051/api/skills?project_path=/path/to/project" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-deployment",
    "description": "Deployment workflow for my project",
    "content": "# Deployment Skill\n\n## Steps\n1. Run tests\n2. Build\n3. Deploy",
    "category": "devops",
    "tags": ["deployment", "ci-cd"]
  }'
```

### Skill File Structure

A skill is a directory containing:

```
my-skill/
├── skill.md           # Main skill instructions (required)
├── metadata.json      # Skill metadata (optional)
└── examples/          # Example files (optional)
    ├── example1.md
    └── example2.py
```

### Writing Good Skills

1. **Be Specific** - Focus on one capability
2. **Include Examples** - Show how to use the skill
3. **Document Triggers** - When should Claude use this skill?
4. **Test It** - Verify Claude follows the instructions

Example skill content:

```markdown
# Rails Service Objects

Use this skill when implementing business logic in Rails applications.

## When to Use
- Complex operations involving multiple models
- Operations that need to be tested in isolation
- Reusable business logic

## Pattern

```ruby
class CreateUser
  def initialize(params)
    @params = params
  end

  def call
    user = User.new(@params)
    if user.save
      send_welcome_email(user)
      Result.success(user)
    else
      Result.failure(user.errors)
    end
  end

  private

  def send_welcome_email(user)
    UserMailer.welcome(user).deliver_later
  end
end
```

## Usage

```ruby
result = CreateUser.new(user_params).call
if result.success?
  redirect_to result.value
else
  render :new, errors: result.errors
end
```
```

---

## Skill Locations

| Type | Location | Scope |
|------|----------|-------|
| Global Skills | `~/.claude/skills/` | All projects |
| Project Skills | `{project}/.claude/skills/` | Single project |
| Templates | `claude-os/templates/skill-library/` | Install to project |
| Community | GitHub repositories | Install to project |

---

## MCP Tools

Skills management is also available via MCP tools:

| Tool | Description |
|------|-------------|
| `mcp__code-forge__list_skills` | List all skills |
| `mcp__code-forge__list_skill_templates` | List available templates |
| `mcp__code-forge__install_skill_template` | Install a template |
| `mcp__code-forge__create_skill` | Create a custom skill |
| `mcp__code-forge__get_skill` | Get skill details |
| `mcp__code-forge__delete_skill` | Delete a project skill |

---

## Tips

1. **Start with templates** - Install what you need per-project
2. **Keep global minimal** - Only core skills should be global
3. **Customize after install** - Edit installed skills for your needs
4. **Create custom skills** - Document project-specific patterns
5. **Share with team** - Check `.claude/skills/` into git

---

## Troubleshooting

### "Skill not found"
- Check if the skill is installed: `/claude-os-skills`
- Verify the skill directory exists in `.claude/skills/`

### "Community skills not loading"
- Check internet connection
- GitHub API rate limits may apply (1 hour cache)
- Try refreshing: click the refresh button in UI

### "Skill not being used by Claude"
- Verify `skill.md` exists in the skill directory
- Check that the skill description matches your use case
- Explicitly invoke with: `skill: <name>`

---

**See Also:**
- [API Reference](../API_REFERENCE.md) - Skills API endpoints
- [README](../../README.md) - Full Claude OS documentation

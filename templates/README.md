# Claude OS Templates

This directory contains all template files used when initializing a new project with Claude OS.

## Directory Structure

```
templates/
├── commands/           # Slash command templates (symlinked to projects)
├── skills/             # Skill templates (symlinked to projects)
├── agents/             # Agent templates (project-specific)
├── project-files/      # Files created during project init
│   ├── CLAUDE.md.template
│   ├── .claude-os/
│   │   ├── config.json.template
│   │   ├── hooks.json.template
│   │   └── .gitignore
│   └── README.md
└── README.md          # This file
```

## Template Variables

Templates use `{{VARIABLE}}` syntax for placeholders that get replaced during project initialization:

### Common Variables

- `{{PROJECT_NAME}}` - Project name (e.g., "my-app")
- `{{PROJECT_DESCRIPTION}}` - Brief project description
- `{{TECH_STACK}}` - Technology stack (e.g., "Ruby on Rails, MySQL")
- `{{DATABASE}}` - Database system (e.g., "PostgreSQL", "MySQL")
- `{{DEV_ENVIRONMENT}}` - Dev environment (e.g., "Docker", "Local")
- `{{CLAUDE_OS_URL}}` - Claude OS server URL (default: http://localhost:8051)
- `{{DOCS_PATHS}}` - JSON array of documentation paths
- `{{CREATED_AT}}` - ISO timestamp of creation
- `{{PROJECT_SPECIFIC_CONTENT}}` - Custom project content
- `{{DEVELOPMENT_GUIDELINES}}` - Project-specific guidelines
- `{{COMMON_TASKS}}` - Common development tasks
- `{{BUSINESS_RULES}}` - Key business rules

## How Templates Are Used

When running `/claude-os-init`:

1. **Commands & Skills** - Symlinked from `templates/commands/` and `templates/skills/` to project's `.claude/` directory
2. **Project Files** - Copied from `templates/project-files/` with variables replaced
3. **Knowledge Bases** - Created via API with project-specific names
4. **MCP Configuration** - Updated in `~/.claude/mcp-servers/` with new project

## Adding New Templates

### New Command Template

1. Create file in `templates/commands/my-command.md`
2. Add command logic
3. Will be automatically available after `/claude-os-init`

### New Skill Template

1. Create directory in `templates/skills/my-skill/`
2. Add `SKILL.md` and any scripts
3. Will be automatically available after `/claude-os-init`

### Updating CLAUDE.md Template

Edit `templates/project-files/CLAUDE.md.template` to add:
- New sections
- Updated workflow instructions
- Additional context

Changes will apply to NEW projects only. Existing projects keep their CLAUDE.md unchanged.

## Consolidation Scripts

See the `cli/` directory in this repository for scripts to:
- Move commands from `~/.claude/commands/` to `templates/commands/`
- Move skills from `~/.claude/skills/` to `templates/skills/`
- Update existing projects to use templates

## For Coworkers

When you clone Claude OS and run `./install.sh`, these templates are:
1. Registered with your Claude CLI
2. Available for new project initialization
3. Ready to use with `/claude-os-init`

Then cd to any project and run `/claude-os-init` to connect it to Claude OS!

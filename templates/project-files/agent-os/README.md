# Agent-OS for {{PROJECT_NAME}}

## Overview

Agent-OS is a spec-driven development system that integrates with Claude OS to provide structured workflows for planning and implementing features.

## Directory Structure

```
agent-os/
├── config.yml          # Agent-OS configuration
├── product/            # Product documentation
│   ├── mission.md      # Product mission and goals
│   ├── roadmap.md      # Feature roadmap
│   └── tech-stack.md   # Technology stack documentation
├── specs/              # Feature specifications
│   └── YYYY-MM-DD-feature-name/
│       ├── planning/
│       ├── spec.md
│       └── tasks.md
└── standards/          # Coding standards
    ├── backend/
    ├── frontend/
    ├── global/
    └── testing/
```

## How It Works

Agent-OS provides 8 specialized agents accessible via slash commands:

1. **`/new-spec`** - Initialize a new feature specification
2. **`/create-spec`** - Create comprehensive specification with requirements gathering
3. **`/plan-product`** - Plan product mission, roadmap, and tech stack

The agents work together to:
- Gather requirements through targeted questions
- Create detailed specifications
- Generate task breakdowns
- Implement features
- Verify implementations

## Integration with Claude OS

Agent-OS agents use Claude OS knowledge bases to:
- Search for similar patterns and solutions
- Save decisions and learnings
- Build on previous work
- Maintain context across sessions

## Getting Started

1. **Create your first spec:**
   ```
   /new-spec
   ```

2. **The agent will guide you through:**
   - Requirements gathering
   - Visual asset collection
   - Existing code identification
   - Specification creation
   - Task breakdown
   - Implementation

3. **Your spec will be saved to:**
   ```
   agent-os/specs/YYYY-MM-DD-your-feature-name/
   ```

## Best Practices

- **Start with `/new-spec`** for all new features
- **Provide visual mockups** when available (place in `specs/[spec-name]/planning/visuals/`)
- **Reference existing code** to promote reusability
- **Let the agents guide you** through the process

## Commands Available

- `/new-spec` - Initialize new specification
- `/create-spec` - Full spec creation workflow
- `/plan-product` - Product planning
- `/implement-spec` - Implement a specification

## Learn More

See `.claude/agents/agent-os/` for agent definitions and workflows.

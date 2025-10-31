### Agent-OS: Spec-Driven Development (Optional)

**Agent-OS provides 8 specialized agents for structured feature development:**

#### Specification Workflow

1. **`/new-spec`** - Initialize new feature specification
   - Creates spec directory structure
   - Sets up planning workflow
   - Example: `/new-spec user-authentication`

2. **`/create-spec`** - Full specification creation workflow
   - Gathers requirements through targeted questions (1-3 at a time)
   - Collects visual assets
   - Identifies reusable code
   - Creates detailed specification and task breakdown
   - Example: `/create-spec`

3. **`/plan-product`** - Product planning and documentation
   - Creates mission.md, roadmap.md, tech-stack.md
   - Defines product vision and technical direction
   - Example: `/plan-product`

4. **`/implement-spec`** - Implement a specification
   - Follows tasks.md from spec
   - Implements features step-by-step
   - Verifies implementation against spec
   - Example: `/implement-spec user-authentication`

#### The 8 Agent-OS Agents

Available in `.claude/agents/agent-os/`:

1. **spec-initializer** - Initialize new spec directories
2. **spec-shaper** - Gather requirements through iterative questions
3. **spec-writer** - Create detailed technical specifications
4. **tasks-list-creator** - Break specs into actionable tasks
5. **implementer** - Implement features following tasks
6. **implementation-verifier** - Verify implementation completeness
7. **spec-verifier** - Verify specs and tasks consistency
8. **product-planner** - Create product documentation

#### Agent-OS Directory Structure

```
agent-os/
├── config.yml          # Agent-OS configuration
├── product/            # Product documentation
│   ├── mission.md      # Product mission and goals
│   ├── roadmap.md      # Feature roadmap
│   └── tech-stack.md   # Technology stack
├── specs/              # Feature specifications
│   └── YYYY-MM-DD-feature-name/
│       ├── planning/
│       │   ├── requirements.md
│       │   └── visuals/
│       ├── spec.md
│       └── tasks.md
└── standards/          # Coding standards (as skills)
```

#### How Agent-OS Works with Claude OS

Agent-OS agents integrate deeply with Claude OS:
- **Search memories** before creating specs (avoid reinventing the wheel)
- **Save decisions** to project_memories during specification
- **Reference patterns** from previous work
- **Build knowledge** over time

#### Best Practices

- **Always start with `/new-spec`** for new features
- **Provide visual mockups** when available (speeds up requirements)
- **Answer questions thoughtfully** (agents ask 1-3 at a time now!)
- **Reference existing code** (agents will search for patterns)
- **Let agents guide you** through the structured workflow

**See `agent-os/README.md` for detailed Agent-OS documentation.**

# Pistn Agent OS Files - Upload Priority Guide

## 🎯 Essential Files (Upload First - 10 files)

These give Claude CLI the core understanding of your project:

### Product Context (3 files)
```
✅ /agent-os/product/mission.md           - Project vision & goals
✅ /agent-os/product/tech-stack.md        - Technology decisions
✅ /agent-os/product/roadmap.md          - Development roadmap
```

### Global Standards (5 files)
```
✅ /agent-os/standards/global/conventions.md      - Overall conventions
✅ /agent-os/standards/global/coding-style.md     - Code style rules
✅ /agent-os/standards/global/tech-stack.md       - Tech stack standards
✅ /agent-os/standards/global/error-handling.md   - Error patterns
✅ /agent-os/standards/global/validation.md       - Validation rules
```

### Configuration (2 files)
```
✅ /agent-os/config.yml                  - Agent OS configuration
✅ /agent-os/roles/implementers.yml      - Developer roles
```

## 📋 High Priority (Upload Second - 10 files)

Based on what you're working on:

### For Backend Work (4 files)
```
⭐ /agent-os/standards/backend/api.md         - API design patterns
⭐ /agent-os/standards/backend/models.md      - Database models
⭐ /agent-os/standards/backend/queries.md     - Query patterns
⭐ /agent-os/standards/backend/migrations.md  - Migration standards
```

### For Frontend Work (4 files)
```
⭐ /agent-os/standards/frontend/components.md     - Component patterns
⭐ /agent-os/standards/frontend/css.md           - Styling rules
⭐ /agent-os/standards/frontend/accessibility.md  - A11y requirements
⭐ /agent-os/standards/frontend/responsive.md     - Responsive design
```

### For Testing (1 file)
```
⭐ /agent-os/standards/testing/test-writing.md    - Testing guidelines
```

### For Understanding Roles (1 file)
```
⭐ /agent-os/roles/verifiers.yml                  - QA/Verification roles
```

## 🔄 Recent Implementation Examples (Upload as Needed - 10 files)

Upload these when working on similar features:

### User Authentication Implementation
```
📄 /agent-os/specs/2025-10-14-account-users-devise/requirements.md
📄 /agent-os/specs/2025-10-14-account-users-devise/IMPLEMENTATION.md
📄 /agent-os/specs/2025-10-14-account-users-devise/follow-up-questions.md
```

### Group Account Rendering (Complex Feature Example)
```
📄 /agent-os/specs/2025-10-15-group-account-rendering/spec.md
📄 /agent-os/specs/2025-10-15-group-account-rendering/SUMMARY.md
📄 /agent-os/specs/2025-10-15-group-account-rendering/tasks.md
📄 /agent-os/specs/2025-10-15-group-account-rendering/planning/requirements.md
```

### Verification Examples
```
📄 /agent-os/specs/2025-10-15-group-account-rendering/CODE_REVIEW.md
📄 /agent-os/specs/2025-10-15-group-account-rendering/REVIEW_SUMMARY.md
📄 /agent-os/specs/2025-10-15-group-account-rendering/VERIFICATION_SUMMARY.md
```

## 📊 Upload Strategy by Use Case

### Scenario 1: "I need Claude to understand my project basics"
**Upload These 10 Files:**
1. product/mission.md
2. product/tech-stack.md
3. product/roadmap.md
4. standards/global/conventions.md
5. standards/global/coding-style.md
6. standards/global/tech-stack.md
7. standards/global/error-handling.md
8. standards/global/validation.md
9. config.yml
10. roles/implementers.yml

### Scenario 2: "I'm building a new API endpoint"
**Add These 4 Files:**
1. standards/backend/api.md
2. standards/backend/models.md
3. standards/backend/queries.md
4. standards/global/validation.md

### Scenario 3: "I'm building a React component"
**Add These 4 Files:**
1. standards/frontend/components.md
2. standards/frontend/css.md
3. standards/frontend/accessibility.md
4. standards/frontend/responsive.md

### Scenario 4: "I need to understand a complex feature"
**Add Relevant Spec Files:**
- Pick the most recent/similar spec folder
- Upload spec.md, requirements.md, IMPLEMENTATION.md
- Include any verification/review files

## 🚀 Quick Upload Process

1. **Go to Code-Forge UI** (http://localhost:3000)
2. **Select/Create "pistn" knowledge base** (type: agent-os)
3. **Upload Essential Files First** (10 core files)
4. **Test with a query** like "What is Pistn's mission and tech stack?"
5. **Add Domain-Specific Files** based on what you're working on
6. **Add Implementation Examples** as reference when needed

## 💡 Pro Tips

### File Size Considerations
- Most standards files are 2-5 KB (upload quickly)
- Spec files can be larger 10-30 KB (still fast)
- Total for essential files: ~50-100 KB

### Upload Order Matters
1. **Product files first** - Sets context
2. **Global standards second** - Establishes conventions
3. **Domain-specific third** - Based on your work
4. **Examples last** - For reference

### Skip These (Less Useful)
```
❌ Implementation phase files (too detailed)
❌ Individual task files (too granular)
❌ Test scripts (.sh files)
❌ Backup files
```

## 📈 Expected Results

After uploading the essential 10 files:
- Claude understands your project mission ✅
- Knows your tech stack and conventions ✅
- Can answer questions about coding standards ✅
- Response time: 5-10s for most queries ✅

After uploading all 20-30 priority files:
- Deep understanding of all domains ✅
- Can provide specific implementation guidance ✅
- Knows your patterns and examples ✅
- Can review code against your standards ✅

## 🎯 Minimal Set (If Limited Time)

Just upload these 5 files for basic context:
1. product/mission.md
2. product/tech-stack.md
3. standards/global/conventions.md
4. standards/global/coding-style.md
5. config.yml

This gives Claude CLI enough context to be helpful while keeping upload time under 1 minute.

---

**Upload these files via Code-Forge UI at http://localhost:3000** 🚀
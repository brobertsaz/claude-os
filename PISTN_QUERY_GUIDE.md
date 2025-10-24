# Pistn Knowledge Base Query Guide for Claude CLI

## 🎯 Quick Reference: What Claude CLI Now Knows About Pistn

After ingesting your Agent OS profile, Claude CLI has deep knowledge about:

### 📚 Standards & Conventions (14 files)
- **Backend**: API design, database models, query patterns, migrations
- **Frontend**: Components, CSS, accessibility, responsive design
- **Global**: Coding style, error handling, validation, commenting
- **Testing**: Test writing guidelines

### 🚀 Product Context (3 files)
- Mission and vision
- Technical roadmap
- Technology stack decisions

### 📋 Feature Specifications (32 files)
- Account/User implementation with Devise
- Group account rendering system
- Detailed implementation phases and verification

### 👥 Team Roles (2 files)
- Implementer responsibilities
- Verifier responsibilities

## 🔥 Most Effective Queries by Use Case

### When Starting New Features
```
"What are the Pistn conventions for [feature type]?"
"Show me similar implementations in Pistn specs"
"What is the standard workflow for implementing [feature]?"
```

### When Writing Code
```
"What are the Pistn API design patterns?"
"Show me the Pistn model conventions for [entity]"
"What are the CSS/component standards in Pistn?"
```

### When Debugging
```
"How does Pistn handle error handling for [scenario]?"
"What are the validation patterns in Pistn?"
"Show me the query optimization standards"
```

### When Testing
```
"What are the Pistn testing requirements?"
"How should I write tests for [feature]?"
"What is the verification process in Pistn?"
```

## ⚡ Query Performance Optimization

### Fastest Queries (2-5s cached)
Use type-specific searches when you know what you're looking for:

```python
# Get specific standards
"get_standards('pistn', 'api design')"
"get_standards('pistn', 'component')"

# Get workflows
"get_workflows('pistn', 'implementation')"

# Get specs
"get_specs('pistn', 'account')"
```

### Standard Queries (5-10s cached)
General questions about specific topics:

```
"How does Pistn implement user authentication?"
"What are the database migration standards?"
"Explain the frontend component architecture"
```

### Complex Queries (15-20s but comprehensive)
Multi-part questions requiring context synthesis:

```
"Explain the complete flow from user signup to account creation including all validations"
"How do group accounts work with rendering and permissions?"
"What are all the standards I need to follow for a new API endpoint?"
```

## 🎯 Query Strategies for Common Tasks

### 1. Before Starting Development
```
Query: "What is the Pistn tech stack and architecture?"
Purpose: Understand the overall system

Query: "Show me the coding conventions and style guide"
Purpose: Ensure consistent code style
```

### 2. Implementing New Features
```
Query: "What specs exist for [similar feature]?"
Purpose: Learn from existing implementations

Query: "What is the standard implementation workflow?"
Purpose: Follow established processes
```

### 3. API Development
```
Query: "Show me the API design standards and examples"
Purpose: Follow REST/GraphQL conventions

Query: "What are the authentication and authorization patterns?"
Purpose: Implement security correctly
```

### 4. Frontend Development
```
Query: "What are the component and CSS standards?"
Purpose: Maintain UI consistency

Query: "Show me the accessibility requirements"
Purpose: Ensure WCAG compliance
```

### 5. Database Work
```
Query: "What are the model and migration patterns?"
Purpose: Follow database conventions

Query: "Show me the query optimization standards"
Purpose: Write efficient queries
```

## 🚫 Queries to Avoid (Slow/Inefficient)

### ❌ Too Vague
```
"Tell me about Pistn"  # Too broad
"What should I know?"  # Not specific enough
```

### ❌ Requesting Everything
```
"Show me all standards"  # Returns too much
"List every specification"  # Overwhelming results
```

### ❌ Multiple Unrelated Topics
```
"Explain API, CSS, testing, and deployment"  # Break into separate queries
```

## ✅ Better Query Patterns

### Be Specific
```
❌ "How do I implement this?"
✅ "How do I implement user authentication in Pistn?"
```

### Reference File Types
```
❌ "What are the rules?"
✅ "What are the API design standards?"
✅ "Show me the frontend component conventions"
```

### Ask for Examples
```
✅ "Show me an example of account implementation from specs"
✅ "What does a proper API endpoint look like in Pistn?"
```

## 📊 Understanding Response Times

| Query Type | Cache Cold | Cache Warm | When to Use |
|------------|------------|------------|-------------|
| Type-specific (`get_standards`) | 10-15s | 2-3s | Known document type |
| Simple search | 15-20s | 5-8s | Specific questions |
| Hybrid search | 20-25s | 8-12s | Keyword + semantic |
| Full agentic | 30-40s | 15-20s | Complex multi-part |

## 💡 Pro Tips

1. **First Query After Restart**: Will be slower (builds cache)
2. **Subsequent Queries**: Much faster (uses cache)
3. **Be Specific**: Vague queries trigger expensive agentic mode
4. **Use File Context**: Reference standards/specs/product docs
5. **Break Complex Queries**: Multiple simple > one complex

## 🔍 Example Session for Maximum Efficiency

```bash
# 1. Start with context (5s)
"What is the Pistn mission and tech stack?"

# 2. Get relevant standards (3s each with cache)
"Show me the API design standards"
"Show me the model conventions"

# 3. Check existing implementations (5s)
"How was user authentication implemented?"

# 4. Ask specific implementation question (8s)
"How should I add a new user profile field following Pistn conventions?"

# Total time: ~25s for complete context vs 40s for one vague query
```

## 🚀 Running the Ingestion

```bash
# Make sure services are running
./start.sh

# Run the ingestion script
python ingest_pistn.py

# Or manually via MCP in Claude CLI:
# Tool: ingest_agent_os_profile
# kb_name: pistn
# profile_path: /Users/iamanmp/Projects/pistn/agent-os
```

---

**Your Pistn knowledge base is optimized for Claude CLI!** 🎯
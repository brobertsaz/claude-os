#!/usr/bin/env python3
"""
Project Analysis Skill - Generates project documentation
Analyzes codebase and creates:
- CODING_STANDARDS.md
- ARCHITECTURE.md
- DEVELOPMENT_PRACTICES.md

Saves directly to Claude OS project_profile MCP via API
"""

import os
import sys
import json
import urllib.request
import urllib.error
import subprocess
import time
from pathlib import Path
from collections import defaultdict
from datetime import datetime
from typing import Dict

# Import the CodeIndexer
from code_indexer import CodeIndexer

# ANSI color codes for nice terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text):
    """Print a prominent section header."""
    width = 70
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'=' * width}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.CYAN}  {text}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'=' * width}{Colors.ENDC}\n")

def print_subheader(text):
    """Print a subsection header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}▶ {text}{Colors.ENDC}")

def print_success(text):
    """Print a success message."""
    print(f"{Colors.GREEN}✅ {text}{Colors.ENDC}")

def print_error(text):
    """Print an error message."""
    print(f"{Colors.RED}❌ {text}{Colors.ENDC}")

def print_warning(text):
    """Print a warning message."""
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.ENDC}")

def print_info(text):
    """Print an info message."""
    print(f"{Colors.CYAN}ℹ️  {text}{Colors.ENDC}")

def print_step(step_num, total, text):
    """Print a numbered step."""
    print(f"{Colors.BOLD}[{step_num}/{total}]{Colors.ENDC} {text}")

def print_progress_bar(current, total, label=""):
    """Print a progress bar."""
    bar_length = 40
    filled = int(bar_length * current / total)
    bar = '█' * filled + '░' * (bar_length - filled)
    percent = int(100 * current / total)
    print(f"  {label:<20} [{bar}] {percent:3d}% ({current}/{total})", end='\r')

class ProjectAnalyzer:
    def __init__(self, project_id, api_url="http://localhost:8000"):
        self.code_forge_server = api_url
        self.project_id = project_id
        self.project_path = None
        self.project_name = None

        # Fetch project details from Claude OS
        self.project_details = self._fetch_project_details()
        if not self.project_details:
            raise ValueError(f"Project ID {project_id} not found in Claude OS")

        self.project_path = Path(self.project_details["path"]).resolve()
        if not self.project_path.exists():
            raise ValueError(f"Project path does not exist: {self.project_path}")

        self.project_name = self.project_details["name"]
        self.mcps = self.project_details.get("mcps", {})

        self.project_type = self._detect_project_type()
        self.source_files = self._find_source_files()
        self.config_files = self._find_config_files()
        self.patterns = defaultdict(list)

    def _fetch_json(self, url):
        """Fetch JSON from URL using urllib."""
        try:
            with urllib.request.urlopen(url, timeout=5) as response:
                return json.loads(response.read().decode())
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            print_error(f"HTTP Error {e.code}: {e.reason}")
            return None
        except urllib.error.URLError as e:
            print_error(f"Cannot connect to Claude OS at {self.code_forge_server}: {e.reason}")
            return None
        except Exception as e:
            print_error(f"Error fetching URL: {e}")
            return None

    def _get_registered_mcps(self):
        """Get list of currently registered MCPs in Claude Code."""
        try:
            result = subprocess.run(
                ["claude", "mcp", "list"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                # Parse MCP list output
                registered = set()
                for line in result.stdout.split('\n'):
                    if line.strip() and not line.startswith('Name'):
                        parts = line.split()
                        if parts:
                            registered.add(parts[0].lower())
                return registered
            return set()
        except Exception as e:
            return set()

    def _register_mcp(self, mcp_name, mcp_url):
        """Register an MCP with Claude Code."""
        try:
            result = subprocess.run(
                ["claude", "mcp", "add", mcp_name, mcp_url],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                print_success(f"Registered MCP: {Colors.BOLD}{mcp_name}{Colors.ENDC}")
                return True
            else:
                print_warning(f"Could not register MCP {mcp_name}: {result.stderr}")
                return False
        except Exception as e:
            print_warning(f"Error registering MCP {mcp_name}: {e}")
            return False

    def _setup_mcps(self):
        """Register project MCPs with Claude Code if they don't already exist."""
        if not self.mcps:
            return []

        print_info("Checking MCP registrations...")
        registered = self._get_registered_mcps()
        registered_mcps = []

        # Handle both list and dict formats
        mcps_list = self.mcps if isinstance(self.mcps, list) else list(self.mcps.values())

        for mcp_info in mcps_list:
            kb_name = mcp_info.get('kb_name', '')
            kb_slug = mcp_info.get('kb_slug', '').lower()

            if not kb_name:
                continue

            # Use kb_slug if available, otherwise generate from kb_name
            mcp_register_name = kb_slug if kb_slug else kb_name.lower().replace('_', '-')

            if mcp_register_name in registered:
                print_success(f"MCP already registered: {Colors.BOLD}{mcp_register_name}{Colors.ENDC}")
                registered_mcps.append(mcp_register_name)
            else:
                # Register the MCP
                mcp_url = f"{self.code_forge_server}/mcp/kb/{kb_name}"
                if self._register_mcp(mcp_register_name, mcp_url):
                    registered_mcps.append(mcp_register_name)

        return registered_mcps

    def _post_json(self, url, data):
        """Post JSON to URL using urllib."""
        try:
            payload = json.dumps(data).encode('utf-8')
            req = urllib.request.Request(
                url,
                data=payload,
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                return response.status, json.loads(response.read().decode())
        except urllib.error.HTTPError as e:
            return e.code, None
        except urllib.error.URLError as e:
            print_warning(f"Cannot connect to Claude OS: {e.reason}")
            return None, None
        except Exception as e:
            print_warning(f"Error posting to API: {e}")
            return None, None

    def _fetch_project_details(self):
        """Fetch project details from Claude OS by project ID or path."""
        try:
            import sqlite3

            # Get the project path from sqlite first (as fallback)
            sqlite_path = None
            try:
                db_path = Path.home() / ".claude" / "projects" / "claude-os" / "data" / "claude-os.db"
                if not db_path.exists():
                    db_path = Path("/Users/iamanmp/Projects/claude-os/data/claude-os.db")

                if db_path.exists():
                    conn = sqlite3.connect(str(db_path))
                    cursor = conn.cursor()
                    cursor.execute("SELECT path FROM projects WHERE id = ?", (self.project_id,))
                    result = cursor.fetchone()
                    if result:
                        sqlite_path = result[0]
                    conn.close()
            except:
                pass

            # First, try to fetch the specific project by ID from Claude OS API
            project_url = f"{self.code_forge_server}/api/projects/{self.project_id}"
            project = self._fetch_json(project_url)

            # If not found by ID, search all projects to find by path
            if project is None and sqlite_path:
                print_info(f"Project ID {self.project_id} not found in API, searching by path...")
                all_projects_url = f"{self.code_forge_server}/api/projects"
                all_projects_data = self._fetch_json(all_projects_url)

                if all_projects_data and isinstance(all_projects_data, dict) and "projects" in all_projects_data:
                    for proj in all_projects_data["projects"]:
                        if proj.get("path") == sqlite_path:
                            project = proj
                            # Update project_id to the correct one from API
                            self.project_id = proj["id"]
                            print_info(f"Found project by path, API ID is {self.project_id}")
                            break

            if project is None:
                print_error(f"Project ID {self.project_id} not found in Claude OS")
                return None

            if isinstance(project, dict) and "project" in project:
                project = project["project"]

            # Fetch MCPs for this project
            mcps_url = f"{self.code_forge_server}/api/projects/{self.project_id}/mcps"
            mcps_data = self._fetch_json(mcps_url)

            mcps = {}
            if mcps_data:
                if isinstance(mcps_data, dict) and "mcps" in mcps_data:
                    mcps = mcps_data["mcps"]
                elif isinstance(mcps_data, dict):
                    mcps = mcps_data

            project["mcps"] = mcps

            print_success(f"Loaded project from Claude OS: {Colors.BOLD}{project.get('name')}{Colors.ENDC} (API ID: {self.project_id})")
            print_info(f"Path: {project.get('path')}")
            if isinstance(mcps, dict) and mcps:
                print_info(f"MCPs: {', '.join(mcps.keys())}")

            return project

        except Exception as e:
            print_error(f"Error fetching project details: {e}")
            return None

    def _detect_project_type(self):
        """Detect project type based on config files and directory structure."""
        indicators = {
            'rails': ['Gemfile', 'config/rails.rb', 'app/models', 'app/controllers'],
            'python_django': ['manage.py', 'django.conf', 'requirements.txt'],
            'python_fastapi': ['requirements.txt', 'main.py'],
            'nodejs_express': ['package.json', 'express'],
            'nodejs_nextjs': ['next.config.js', 'package.json'],
            'go': ['go.mod', 'main.go'],
            'java_spring': ['pom.xml', 'spring-boot', 'build.gradle'],
            'rust': ['Cargo.toml'],
        }

        for project_type, files in indicators.items():
            if any((self.project_path / f).exists() or
                   any(f in str(self.project_path) for f in files.split('/'))
                   for f in files):
                return project_type

        return 'generic'

    def _find_source_files(self):
        """Find relevant source files for analysis."""
        extensions = {
            'rails': ['.rb'],
            'python_django': ['.py'],
            'python_fastapi': ['.py'],
            'nodejs_express': ['.js', '.ts'],
            'nodejs_nextjs': ['.js', '.tsx'],
            'go': ['.go'],
            'java_spring': ['.java'],
            'rust': ['.rs'],
            'generic': ['.py', '.js', '.ts', '.rb', '.go', '.java', '.rs'],
        }

        ext_list = extensions.get(self.project_type, extensions['generic'])
        ignore_dirs = {'.git', 'node_modules', '__pycache__', 'vendor', 'dist', 'build', '.venv', 'venv'}

        files = []
        for ext in ext_list:
            for root, dirs, filenames in os.walk(self.project_path):
                # Ignore agent-os and other config dirs
                dirs[:] = [d for d in dirs if d not in ignore_dirs and not d.startswith('.')]

                for filename in filenames:
                    if filename.endswith(ext) and len(files) < 50:  # Limit to 50 files
                        files.append(Path(root) / filename)

        return files[:50]

    def _find_config_files(self):
        """Find configuration and spec files."""
        config_patterns = [
            'README.md', 'README.txt',
            '*spec*.md', '*spec*.txt',
            'ARCHITECTURE.md', 'DESIGN.md',
            'CONVENTIONS.md', 'STANDARDS.md',
            '.editorconfig', 'package.json', 'Gemfile',
            'requirements.txt', 'go.mod', 'Cargo.toml',
        ]

        found = {}
        for pattern in config_patterns:
            for path in self.project_path.glob(f'**/{pattern}'):
                if path.is_file() and 'agent-os' not in str(path):
                    found[pattern] = path

        return found

    def _analyze_naming_conventions(self):
        """Analyze naming conventions from source files."""
        conventions = {
            'variables': [],
            'functions': [],
            'classes': [],
            'files': [],
        }

        sample_files = self.source_files[:10]

        for filepath in sample_files:
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read(2000)  # First 2KB

                    if self.project_type.startswith('python'):
                        # Look for Python patterns
                        if 'def ' in content:
                            conventions['functions'].append("snake_case (e.g., def my_function)")
                        if 'class ' in content:
                            conventions['classes'].append("PascalCase (e.g., class MyClass)")

                    elif self.project_type.startswith('nodejs') or self.project_type.startswith('javascript'):
                        if 'function ' in content or 'const ' in content:
                            conventions['functions'].append("camelCase (e.g., myFunction)")
                        if 'class ' in content:
                            conventions['classes'].append("PascalCase (e.g., class MyClass)")

                    elif self.project_type == 'rails':
                        if 'def ' in content:
                            conventions['functions'].append("snake_case methods")
                        if 'class ' in content:
                            conventions['classes'].append("PascalCase classes")

                    conventions['files'].append(Path(filepath).name)

            except Exception:
                pass

        return conventions

    def generate_coding_standards(self):
        """Generate CODING_STANDARDS.md"""
        conventions = self._analyze_naming_conventions()

        content = f"""# Coding Standards - {self.project_path.name}

*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*

## Project Type
**{self.project_type.replace('_', ' ').title()}**

## Naming Conventions

### Variables
- Prefer descriptive names
- Avoid single letters except in loops (i, j)
- Use full words over abbreviations when possible

### Functions/Methods
"""

        if conventions['functions']:
            for convention in set(conventions['functions']):
                content += f"- {convention}\n"
        else:
            content += f"- Follow {self.project_type.replace('_', ' ')} conventions\n"

        content += f"""
### Classes/Types
"""

        if conventions['classes']:
            for convention in set(conventions['classes']):
                content += f"- {convention}\n"
        else:
            content += f"- Follow {self.project_type.replace('_', ' ')} conventions\n"

        content += f"""
### Files & Directories
- Organize by feature/domain
- Keep related code together
- Use lowercase with hyphens for directory names
- Use language-appropriate extensions

## Code Style

### Formatting
- **Indentation**: Use project linter configuration
- **Line Length**: Enforce via linter
- **Trailing Commas**: Allowed in multi-line structures
- **Comments**: Explain 'why', not 'what'

### Documentation
- Add docstrings/comments for public APIs
- Include type hints where applicable
- Document non-obvious logic
- Keep comments up-to-date with code changes

## Import/Require Patterns
- Group imports: standard library → third-party → local
- Avoid circular dependencies
- Import only what you need
- Use absolute imports over relative imports

## Testing Standards
- Unit tests for all business logic
- Integration tests for APIs
- Naming: test_feature_scenario pattern
- Aim for >80% code coverage on critical paths

## Error Handling
- Use project's error types/classes
- Provide meaningful error messages
- Log errors with context
- Handle errors gracefully at boundaries

## Performance Considerations
- Avoid N+1 queries
- Cache when appropriate
- Profile before optimizing
- Document performance-critical sections

## Security
- Validate all inputs
- Avoid hardcoding secrets
- Use environment variables for configuration
- Follow OWASP principles

## Common Patterns Observed

Sample source files analyzed:
{', '.join(str(f.relative_to(self.project_path)) for f in self.source_files[:5])}

## Linting & Formatting
- Check project for `.editorconfig`, `prettier`, `eslint`, `rubocop`, `pylint`, etc.
- Run linter before committing
- Fix formatting issues automatically when possible
"""

        return content

    def generate_architecture(self):
        """Generate ARCHITECTURE.md"""
        content = f"""# Architecture - {self.project_path.name}

*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*

## Project Type
**{self.project_type.replace('_', ' ').title()}**

## High-Level Design

### Directory Structure
```
{self.project_path.name}/
├── agent-os/          # Agent OS configuration and specs
├── app/              # Application code (varies by project type)
├── config/           # Configuration files
├── tests/            # Test files
├── docs/             # Documentation
└── README.md         # Project overview
```

## Technology Stack

### Core Framework/Language
- **Language**: {self.project_type.split('_')[0].title()}
- **Framework**: {self.project_type.split('_')[1].title() if '_' in self.project_type else 'Unknown'}

### Key Dependencies
Check `package.json`, `Gemfile`, `requirements.txt`, `go.mod`, or `Cargo.toml` for exact versions.

## Architecture Patterns

### Code Organization
"""

        if self.project_type == 'rails':
            content += """- **MVC Pattern**: Models → Views → Controllers
- **Services Layer**: Encapsulate business logic in Service classes
- **Presenters**: Handle view-specific data formatting
- **Decorators**: Wrap objects to add behavior
"""

        elif self.project_type.startswith('nodejs'):
            content += """- **Separation of Concerns**: Routes → Controllers → Services → Models
- **Middleware Pattern**: Request processing pipeline
- **Async/Await**: Handle asynchronous operations
- **Error Handling Middleware**: Centralized error handling
"""

        elif self.project_type.startswith('python'):
            content += """- **Models**: Data layer (SQLAlchemy, Django ORM)
- **Services**: Business logic layer
- **Views/Handlers**: Request handling layer
- **Middleware**: Request/response processing
"""

        elif self.project_type == 'go':
            content += """- **Interfaces**: Define contracts for components
- **Dependency Injection**: Pass dependencies to constructors
- **Middleware Chain**: HTTP middleware pattern
- **Packages**: Organize by functionality
"""

        else:
            content += """- Follow the framework's recommended architecture pattern
- Separate concerns (business logic, data access, presentation)
- Use dependency injection for loose coupling
- Keep layers independent and testable
"""

        content += f"""
### Data Flow
1. Request enters through router/controller
2. Validates input
3. Calls service/business logic layer
4. Interacts with data layer/database
5. Returns response through view/presenter
6. Response serialized and sent to client

## Key Components

### Database Layer
- Check migrations and schema files
- Understand relationships and constraints
- Review indexes for performance-critical queries

### API Layer
- REST conventions (or GraphQL if applicable)
- Request/response format
- Authentication mechanism
- Error response format

### External Integrations
- Third-party APIs used
- Webhook handlers
- Message queues if applicable

## Scalability & Performance

### Caching Strategy
- Implement for frequently accessed data
- Cache invalidation strategy

### Database Optimization
- Index important queries
- Avoid N+1 queries
- Use query optimization

### Async Processing
- Background jobs for long-running operations
- Message queues for event-driven architecture

## Security Architecture

- **Authentication**: {self._get_auth_type()}
- **Authorization**: Role-based access control (RBAC)
- **Data Protection**: Encryption for sensitive data
- **API Security**: Rate limiting, CORS, etc.

## Deployment Architecture

- Check deployment configuration
- Container strategy (Docker if applicable)
- Environment configuration management
- CI/CD pipeline structure

## Dependency Management

Core dependencies:
{self._list_dependencies()}

Update dependencies regularly and keep security patches current.

## Testing Architecture

- **Unit Tests**: Individual component testing
- **Integration Tests**: Component interaction testing
- **E2E Tests**: Full workflow testing
- **Test Coverage**: Aim for >80% on critical paths

"""

        return content

    def generate_development_practices(self):
        """Generate DEVELOPMENT_PRACTICES.md"""
        content = f"""# Development Practices - {self.project_path.name}

*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*

## Development Workflow

### Setting Up Development Environment
1. Clone the repository
2. Install dependencies:
   - For Python: `pip install -r requirements.txt`
   - For Node: `npm install` or `yarn install`
   - For Ruby: `bundle install`
   - For Go: `go mod download`
3. Set up environment variables (copy `.env.example` to `.env`)
4. Run migrations (if database-backed)
5. Start development server

### Local Development
- Run tests before committing
- Use linting/formatting tools
- Keep local database in sync with migrations
- Document any local setup quirks

## Testing Strategy

### Unit Tests
- Test individual functions/methods
- Mock external dependencies
- Fast execution (< 1s per test)
- Naming: `test_feature_scenario`

### Integration Tests
- Test API endpoints
- Use test database fixtures
- Clean up after each test
- Verify database state changes

### End-to-End Tests
- Test user workflows
- Use browser automation (Selenium, Playwright, etc.)
- Run against staging environment
- Cover critical user paths

### Running Tests
```bash
# Run all tests
npm test / pytest / go test ./...

# Run specific test
npm test -- test/feature.test.js

# Run with coverage
npm test -- --coverage
```

### Coverage Goals
- Aim for >80% coverage on critical business logic
- Don't chase 100% - focus on meaningful coverage
- Prioritize coverage of error paths and edge cases

## Git Workflow

### Branching Strategy
- **main**: Production-ready code
- **develop**: Integration branch
- **feature/XXX**: Feature branches from develop
- **bugfix/XXX**: Bug fix branches
- **hotfix/XXX**: Emergency fixes from main

### Commit Messages
Follow conventional commits format:
```
type(scope): description

[optional body]
[optional footer]
```

Types: feat, fix, docs, style, refactor, perf, test, chore

Example:
```
feat(auth): add email verification for signup

- Implement email verification flow
- Add verification token storage
- Create email notification service

Fixes #123
```

### Pull Requests
1. Create feature branch from develop
2. Make commits with clear messages
3. Push and open PR with description
4. Address code review feedback
5. Merge to develop when approved
6. Delete feature branch

### Code Review Checklist
- [ ] Code follows project standards
- [ ] Tests added/updated
- [ ] No hardcoded values
- [ ] Performance acceptable
- [ ] Security considerations addressed
- [ ] Documentation updated
- [ ] Commits are atomic and well-described

## Deployment Process

### Development Environment
- Automatic deploy on push to develop
- Use feature flags for in-progress features
- Smoke tests after deploy

### Staging Environment
- Deploy manually from develop
- Run full test suite
- Performance testing
- User acceptance testing

### Production Environment
- Tag releases with version numbers
- Automatic deploy with human approval
- Monitoring and alerting
- Rollback procedure if needed

## Common Development Tasks

### Adding a New Feature
1. Create feature branch: `git checkout -b feature/my-feature`
2. Write tests first (TDD approach)
3. Implement feature
4. Update documentation
5. Commit with descriptive messages
6. Push and create PR
7. Address review feedback
8. Merge when approved

### Fixing a Bug
1. Create bugfix branch: `git checkout -b bugfix/issue-description`
2. Write test that reproduces bug
3. Fix bug
4. Verify test passes
5. Create PR with bug reference
6. Merge when approved

### Running Database Migrations
```bash
# Rails
rails db:migrate

# Django
python manage.py migrate

# Prisma/Node
npx prisma migrate deploy
```

### Adding Dependencies
1. Add to package.json / Gemfile / requirements.txt
2. Run install command (npm install / bundle / pip install)
3. Test that everything works
4. Commit both files (package.json + lock file)

## Debugging Techniques

### Logging
- Use project's logger configuration
- Include context (user ID, request ID, etc.)
- Use appropriate log levels (DEBUG, INFO, WARN, ERROR)

### Using Debuggers
- Breakpoints and step through code
- Inspect variable values
- Watch expressions for value changes
- Node: `node --inspect`, Python: `pdb`

### Common Issues
- Check logs first
- Verify environment variables are set
- Clear caches (.cache, node_modules, venv)
- Restart development server
- Check git status for uncommitted changes

## Code Quality Tools

### Linting
- Run before commit: `npm run lint` / `rubocop` / `pylint`
- Fix automatically: `npm run lint:fix` / `black`

### Formatting
- Use project formatter: Prettier, Rubocop, Black, gofmt
- Configure IDE to format on save

### Static Analysis
- Security linting (Brakeman, Bandit, etc.)
- Dependency checking (npm audit, bundle audit)
- Code complexity analysis

## Performance Optimization

### Profiling
- Identify slow queries with logging/APM
- Use browser DevTools for frontend performance
- Profile CPU usage with appropriate tools

### Optimization Priorities
1. Fix database queries (N+1, missing indexes)
2. Add caching for expensive computations
3. Optimize asset delivery (compression, CDN)
4. Code-level optimizations

## Documentation

### Code Documentation
- Docstrings/comments for complex logic
- README.md for project overview
- API documentation (Swagger, etc.)
- Architecture decisions (ADRs)

### Keeping Docs Current
- Update docs with code changes
- Review docs in code reviews
- Archive outdated information

## Release Process

### Version Numbering
- Use semantic versioning: MAJOR.MINOR.PATCH
- MAJOR: Breaking changes
- MINOR: New features (backward compatible)
- PATCH: Bug fixes

### Release Checklist
- [ ] All tests passing
- [ ] Code reviewed
- [ ] Documentation updated
- [ ] Version number bumped
- [ ] Changelog updated
- [ ] Build succeeds
- [ ] Deploy to production
- [ ] Monitor for issues

## Monitoring & Logging

### Application Monitoring
- Set up error tracking (Sentry, Rollbar, etc.)
- Monitor performance metrics
- Alert on critical errors

### Log Aggregation
- Centralize logs for easier debugging
- Search and filter capabilities
- Retention policies

### Health Checks
- Implement health check endpoints
- Monitor external dependencies
- Alert on downtime
"""

        return content

    def _get_auth_type(self):
        """Detect authentication type used in project."""
        for filepath in self.source_files[:10]:
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    if 'jwt' in content.lower() or 'token' in content.lower():
                        return "JWT/Token-based"
                    if 'devise' in content or 'omniauth' in content:
                        return "Devise/OmniAuth (Rails)"
                    if 'passport' in content:
                        return "Passport (Node.js)"
            except:
                pass
        return "Check authentication implementation in codebase"

    def _list_dependencies(self):
        """List main dependencies from config files."""
        deps = []

        # Check package.json
        try:
            with open(self.project_path / 'package.json', 'r') as f:
                data = json.load(f)
                deps.extend(list(data.get('dependencies', {}).keys())[:3])
        except:
            pass

        # Check Gemfile
        try:
            with open(self.project_path / 'Gemfile', 'r') as f:
                content = f.read()
                for line in content.split('\n'):
                    if 'gem ' in line:
                        deps.append(line.strip())
                        if len(deps) >= 3:
                            break
        except:
            pass

        # Check requirements.txt
        try:
            with open(self.project_path / 'requirements.txt', 'r') as f:
                deps.extend(f.read().strip().split('\n')[:3])
        except:
            pass

        if deps:
            return "- " + "\n- ".join(str(d) for d in deps[:5])
        return "- Check dependency files for current dependencies"

    def _init_index_state(self, indexed_files: list) -> bool:
        """Initialize the index state file with initially indexed files."""
        try:
            state_dir = self.project_path / ".claude-os"
            state_dir.mkdir(parents=True, exist_ok=True)

            state_file = state_dir / ".index_state"
            state_data = {
                "indexed_files": indexed_files,
                "total_files": len(indexed_files),
                "initialized": datetime.now().isoformat()
            }

            with open(state_file, 'w') as f:
                json.dump(state_data, f, indent=2)

            return True
        except Exception as e:
            print_warning(f"Could not initialize index state: {e}")
            return False

    def _create_git_hook(self) -> str:
        """Create smart git post-commit hook with incremental index expansion."""
        hook_script = f"""#!/bin/bash

# Claude OS Smart Auto-Indexer Post-Commit Hook
# 1. Indexes changed code files on every commit
# 2. Every 10 commits, expands index with previously unindexed files

PROJECT_ID="{self.project_id}"
API_URL="{self.code_forge_server}"
PROJECT_PATH="{self.project_path}"
CLAUDE_OS_DIR="$PROJECT_PATH/.claude-os"
COMMIT_COUNT_FILE="$CLAUDE_OS_DIR/.commit_count"
INDEXER_PATH="$HOME/.claude/skills/analyze-project/incremental_indexer.py"

# Ensure .claude-os directory exists
mkdir -p "$CLAUDE_OS_DIR"

# 1. Index changed files (incremental)
CHANGED_FILES=$(git diff-tree --no-commit-id --name-only -r HEAD)
INDEXED_COUNT=0

for file in $CHANGED_FILES; do
  case "$file" in
    *.rb|*.js|*.ts|*.tsx|*.jsx|*.json|*.yml|*.yaml|*.md)
      # File changed - it will be indexed by incremental_indexer if called
      INDEXED_COUNT=$((INDEXED_COUNT + 1))
      ;;
  esac
done

# 2. Track commit count for periodic expansion
if [ -f "$COMMIT_COUNT_FILE" ]; then
  COMMIT_COUNT=$(cat "$COMMIT_COUNT_FILE")
else
  COMMIT_COUNT=0
fi

COMMIT_COUNT=$((COMMIT_COUNT + 1))
echo $COMMIT_COUNT > "$COMMIT_COUNT_FILE"

# 3. Every 10 commits, expand the index with unindexed files
if [ $((COMMIT_COUNT % 10)) -eq 0 ]; then
  if [ -f "$INDEXER_PATH" ]; then
    echo "[Claude OS] 🔄 Expanding index (commit #$COMMIT_COUNT)..." >&2
    python3 "$INDEXER_PATH" "$PROJECT_ID" "$PROJECT_PATH" "$API_URL" 30 2>&1 | grep -E "✅|⚠️|📊" >&2 || true
  fi
fi

exit 0
"""
        return hook_script

    def _install_git_hook(self) -> bool:
        """Install the post-commit hook in the project's .git directory."""
        try:
            hook_path = self.project_path / ".git" / "hooks" / "post-commit"
            hook_content = self._create_git_hook()

            # Create hook file
            with open(hook_path, 'w') as f:
                f.write(hook_content)

            # Make it executable
            os.chmod(hook_path, 0o755)

            print_success(f"Installed git hook: {Colors.BOLD}{hook_path}{Colors.ENDC}")
            return True
        except Exception as e:
            print_warning(f"Could not install git hook: {e}")
            return False

    def _setup_kb_hooks(self) -> Dict:
        """Setup automatic file watcher hooks for each MCP type."""
        hooks_setup = {
            "knowledge_docs": False,
            "project_profile": False,
            "project_index": False,
            "project_memories": False
        }

        # Common folder mappings for each MCP type
        folder_mappings = {
            "knowledge_docs": ["docs", "documentation", "knowledge_docs", "doc"],
            "project_profile": [".claude-os/project-profile", ".claude-os/project_profile"],
            "project_index": [".claude-os/project-index", ".claude-os/project_index"],
            "project_memories": [".claude-os/memories", ".claude-os/project-memories"]
        }

        # Try to setup hooks for each MCP type
        for mcp_type, possible_folders in folder_mappings.items():
            for folder_name in possible_folders:
                folder_path = self.project_path / folder_name

                # For project_profile and project_index, always use the .claude-os subdirectories
                if mcp_type == "project_profile":
                    folder_path = self.project_path / ".claude-os" / "project-profile"
                elif mcp_type == "project_index":
                    folder_path = self.project_path / ".claude-os" / "project-index"
                elif mcp_type == "project_memories":
                    folder_path = self.project_path / ".claude-os" / "memories"

                # Create the folder if it doesn't exist (for managed MCPs)
                if mcp_type in ["project_profile", "project_index", "project_memories"]:
                    folder_path.mkdir(parents=True, exist_ok=True)

                # If knowledge_docs folder exists, use it; otherwise create a default one
                if mcp_type == "knowledge_docs" and not folder_path.exists():
                    # Look for common documentation folder
                    for alt_folder in ["docs", "documentation", "doc"]:
                        alt_path = self.project_path / alt_folder
                        if alt_path.exists():
                            folder_path = alt_path
                            break
                    else:
                        # Create default docs folder if none exist
                        folder_path = self.project_path / "docs"
                        folder_path.mkdir(parents=True, exist_ok=True)

                # Enable hook via API
                try:
                    hook_url = f"{self.code_forge_server}/api/projects/{self.project_id}/hooks/{mcp_type}/enable"
                    payload = {
                        "folder_path": str(folder_path),
                        "file_patterns": None  # Use default patterns from config
                    }

                    status, response = self._post_json(hook_url, payload)

                    if status in [200, 201]:
                        hooks_setup[mcp_type] = True
                    else:
                        print_warning(f"Could not setup hook for {mcp_type}")
                except Exception as e:
                    print_warning(f"Error setting up {mcp_type} hook: {e}")

        return hooks_setup

    def _start_file_watcher(self) -> bool:
        """Start the file watcher for automatic folder synchronization."""
        try:
            watcher_url = f"{self.code_forge_server}/api/watcher/start/{self.project_id}"
            status, response = self._post_json(watcher_url, {})

            if status in [200, 201]:
                return True
            else:
                print_warning(f"Could not start file watcher: {status}")
                return False
        except Exception as e:
            print_warning(f"Error starting file watcher: {e}")
            return False

    def _generate_summary(self):
        """Generate a concise project summary for Claude's native memory."""
        summary = f"""PROJECT: {self.project_name} (ID: {self.project_id})
TYPE: {self.project_type.replace('_', ' ').title()}
PATH: {self.project_path}

KEY FACTS:
- Source files: {len(self.source_files)}
- Config files: {len(self.config_files)}
- Analyzed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

INDEXING STRATEGY:
- Initial: 25 key files indexed immediately
- Auto-expand: Every 10 commits, ~30 more files indexed
- Incremental: Changed files indexed on each commit
- Timeline: Full index in ~6-10 commits (typical dev pace)

STANDARDS:
- Methods: snake_case
- Classes: PascalCase
- Testing: Unit + integration (>80% coverage target)

REGISTERED MCPs (load on-demand):
- project-profile: Coding standards, architecture, practices
- knowledge-docs: Project documentation
- project-index: Entire codebase indexed & searchable
- project-memories: Important insights"""
        return summary

    def _ingest_to_mcp(self, doc_name, doc_content, mcp_type="project_profile"):
        """Ingest a document into the Claude OS project MCP."""
        try:
            payload = {
                "filename": doc_name,
                "content": doc_content,
                "mcp_type": mcp_type
            }

            url = f"{self.code_forge_server}/api/projects/{self.project_id}/ingest-document"
            status, response = self._post_json(url, payload)

            if status in [200, 201]:
                return True
            else:
                if status:
                    print_warning(f"Could not ingest {doc_name} via API: {status}")
                return False

        except Exception as e:
            print_warning(f"Error ingesting {doc_name}: {e}")
            return False

    def _check_and_start_rq_workers(self):
        """Check if RQ workers are running and start them if needed."""
        try:
            # First check if Redis is running
            result = subprocess.run(
                ["redis-cli", "ping"],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode != 0:
                print_warning("Redis is not running - RQ workers require Redis")
                return False

            # Check if RQ workers are already running
            result = subprocess.run(
                ["rq", "info"],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0 and "Worker" in result.stdout:
                # Workers are already running
                print_success("RQ workers already running")
                return True

            # Find Claude OS project directory
            # Try multiple locations
            claude_os_paths = [
                Path("/Users/iamanmp/Projects/claude-os"),
                Path.home() / "Projects" / "claude-os",
                Path("/opt/claude-os"),
                Path("/srv/claude-os")
            ]

            claude_os_path = None
            for path in claude_os_paths:
                if (path / "start_redis_workers.sh").exists():
                    claude_os_path = path
                    break

            if not claude_os_path:
                print_warning("Claude OS project not found - cannot start RQ workers")
                print_info("Expected locations: /Users/iamanmp/Projects/claude-os or ~/Projects/claude-os")
                return False

            # Start RQ workers in background
            print_info("Starting RQ workers for real-time learning system...")
            start_script = claude_os_path / "start_redis_workers.sh"

            # Run in background using subprocess with nohup
            subprocess.Popen(
                ["bash", str(start_script)],
                cwd=str(claude_os_path),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )

            # Wait for workers to start
            print_info("Waiting for RQ workers to come online...")
            max_retries = 10
            for i in range(max_retries):
                time.sleep(1)
                result = subprocess.run(
                    ["rq", "info"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )

                if result.returncode == 0 and "claude-os:" in result.stdout:
                    print_success("RQ workers started successfully")
                    # Extract worker info
                    for line in result.stdout.split('\n'):
                        if "claude-os:" in line:
                            print_info(f"  • {line.strip()}")
                    return True

            print_warning("RQ workers did not start within timeout")
            return False

        except subprocess.TimeoutExpired:
            print_warning("Timeout checking RQ workers status")
            return False
        except Exception as e:
            print_warning(f"Error starting RQ workers: {e}")
            return False

    def run(self):
        """Analyze project and prepare for efficient context loading with native memory."""
        print_header(f"🚀 INITIALIZING PROJECT: {self.project_name}")

        print_info(f"Project ID: {self.project_id}")
        print_info(f"Path: {self.project_path}")
        print_info(f"Type: {self.project_type.replace('_', ' ').title()}")

        # Step 0: Ensure RQ workers are running for real-time learning system
        print_subheader("Step 0/5: Starting Real-Time Learning System")
        workers_started = self._check_and_start_rq_workers()
        if workers_started:
            print_success("Real-time learning system is active")
        else:
            print_warning("Real-time learning system could not be started")
            print_info("Project initialization will continue, but real-time features may be limited")

        # Step 1: Register MCPs with Claude Code if they don't already exist
        print_subheader("Step 1/5: Registering MCPs with Claude Code")
        registered_mcps = self._setup_mcps()

        if registered_mcps:
            print_success(f"Registered {len(registered_mcps)} MCPs")
            for mcp in registered_mcps:
                print_info(f"  • {mcp}")
        else:
            print_warning("No MCPs registered (check Claude OS connection)")

        # Step 1b: Setup KB file watcher hooks
        print_subheader("Step 1b/5: Setting up automatic file watchers")
        hooks_setup = self._setup_kb_hooks()
        hooks_enabled = sum(1 for v in hooks_setup.values() if v)
        if hooks_enabled > 0:
            print_success(f"Enabled file watchers for {hooks_enabled} MCP types")
            for mcp_type, enabled in hooks_setup.items():
                status = "✓" if enabled else "✗"
                print_info(f"  {status} {mcp_type}")
        else:
            print_warning("No file watchers configured")

        # Start the file watcher
        if self._start_file_watcher():
            print_success("File watcher started - changes will be auto-indexed")
        else:
            print_warning("Could not start file watcher (may need manual restart)")

        # Step 2: Generate documents for local reference
        print_subheader("Step 2/5: Generating project documentation")
        print_step(1, 3, "Analyzing coding standards...")
        coding_standards = self.generate_coding_standards()
        print_progress_bar(1, 3, "Coding Standards")
        time.sleep(0.2)

        print_step(2, 3, "Analyzing architecture...")
        architecture = self.generate_architecture()
        print_progress_bar(2, 3, "Architecture")
        time.sleep(0.2)

        print_step(3, 3, "Analyzing development practices...")
        dev_practices = self.generate_development_practices()
        print_progress_bar(3, 3, "Dev Practices")
        print()

        # Save locally for reference
        local_output = self.project_path / ".claude"
        local_output.mkdir(parents=True, exist_ok=True)

        coding_path = local_output / "CODING_STANDARDS.md"
        with open(coding_path, 'w') as f:
            f.write(coding_standards)

        arch_path = local_output / "ARCHITECTURE.md"
        with open(arch_path, 'w') as f:
            f.write(architecture)

        dev_path = local_output / "DEVELOPMENT_PRACTICES.md"
        with open(dev_path, 'w') as f:
            f.write(dev_practices)

        print_success(f"Documentation saved to {Colors.BOLD}.claude/{Colors.ENDC}")
        print_info(f"  • CODING_STANDARDS.md ({len(coding_standards)} bytes)")
        print_info(f"  • ARCHITECTURE.md ({len(architecture)} bytes)")
        print_info(f"  • DEVELOPMENT_PRACTICES.md ({len(dev_practices)} bytes)")

        # Step 3: Ingest documents into project_profile MCP
        print_subheader("Step 3/5: Ingesting documentation into project_profile MCP")
        ingested = 0

        print_step(1, 3, "Ingesting CODING_STANDARDS.md...")
        if self._ingest_to_mcp("CODING_STANDARDS.md", coding_standards, "project_profile"):
            print_progress_bar(1, 3, "Coding Standards")
            ingested += 1
        time.sleep(0.1)

        print_step(2, 3, "Ingesting ARCHITECTURE.md...")
        if self._ingest_to_mcp("ARCHITECTURE.md", architecture, "project_profile"):
            print_progress_bar(2, 3, "Architecture")
            ingested += 1
        time.sleep(0.1)

        print_step(3, 3, "Ingesting DEVELOPMENT_PRACTICES.md...")
        if self._ingest_to_mcp("DEVELOPMENT_PRACTICES.md", dev_practices, "project_profile"):
            print_progress_bar(3, 3, "Dev Practices")
            ingested += 1
        print()

        print_success(f"Ingested {ingested}/3 documentation files to project_profile MCP")

        # Step 4: Index source code files for project_index MCP
        print_subheader("Step 4/5: Indexing source code files")
        try:
            print_info("Indexing top 50 source files for semantic search...")
            indexer = CodeIndexer(str(self.project_path), self.project_id, self.code_forge_server, max_files=50)
            index_results = indexer.run()

            print_success(f"Project indexing complete!")
            print_info(f"  • Files indexed: {index_results['total_files']}")
            print_info(f"  • Code chunks created: {index_results['total_chunks']}")
            print_info(f"  • Available for semantic search in project_index MCP")

            # Initialize index state file with initial 25 files
            self._init_index_state(index_results.get('files_indexed', []))
        except Exception as e:
            print_warning(f"Could not index code files: {e}")

        # Step 5: Install git post-commit hook for incremental indexing
        print_subheader("Step 5/5: Installing git hooks for auto-indexing")
        if self._install_git_hook():
            print_success(f"Git post-commit hook installed")
            print_info(f"  • Changed files will be auto-indexed on each commit")
            print_info(f"  • Every 10 commits: 30 new files added to index")
        else:
            print_warning(f"Could not install git hook (check .git directory)")

        # Generate summary for native memory
        summary = self._generate_summary()

        # Print completion and summary prominently
        print_header("✨ PROJECT INITIALIZATION COMPLETE")

        print(f"{Colors.BOLD}{Colors.YELLOW}📝 SAVE THIS TO YOUR NATIVE MEMORY:{Colors.ENDC}\n")
        print(f"{Colors.BOLD}{'─' * 70}{Colors.ENDC}")
        for line in summary.split('\n'):
            if line.strip():
                print(f"  {line}")
        print(f"{Colors.BOLD}{'─' * 70}{Colors.ENDC}\n")

        # Print MCPs status
        print_success(f"Project analysis complete! All systems ready.")

        print_subheader("Registered MCPs (ready to load on-demand)")
        if registered_mcps:
            for i, mcp in enumerate(registered_mcps, 1):
                print_info(f"{i}. {Colors.BOLD}{mcp}{Colors.ENDC}")
        else:
            print_warning("No MCPs registered")

        print_subheader("What's Next?")
        print_step(1, 5, "Save the summary above to your native memory")
        print_step(2, 5, f"MCPs are registered but NOT loaded (saves tokens)")
        print_step(3, 5, f"File watchers are now active - new files will auto-sync to MCPs")
        print_step(4, 5, f"When working on this project, load specific MCPs as needed")
        if registered_mcps:
            print_info(f"   Example: 'load {registered_mcps[0]}' to access project standards")
        print_step(5, 5, f"Git hooks will auto-index changes on each commit")

        print()

        return {
            "project_id": self.project_id,
            "project_name": self.project_name,
            "registered_mcps": registered_mcps,
            "summary": summary,
            "docs": {
                "coding_standards": str(coding_path),
                "architecture": str(arch_path),
                "practices": str(dev_path)
            }
        }

def main():
    if len(sys.argv) < 2:
        print("Usage: analyze_project.py <project_id> [code_forge_url]")
        print("Example: analyze_project.py 1")
        print("Example: analyze_project.py 1 http://localhost:8000")
        sys.exit(1)

    try:
        project_id = int(sys.argv[1])
    except ValueError:
        print(f"❌ Error: Project ID must be an integer, got: {sys.argv[1]}")
        sys.exit(1)

    api_url = sys.argv[2] if len(sys.argv) > 2 else "http://localhost:8000"

    try:
        analyzer = ProjectAnalyzer(project_id, api_url=api_url)
        analyzer.run()
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

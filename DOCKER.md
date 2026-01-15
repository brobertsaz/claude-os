# Claude OS - Docker Installation

This guide covers running Claude OS using Docker and Docker Compose.

## Quick Start

### 1. Basic Setup (with external Ollama)

If you already have Ollama running on your host machine:

```bash
# Copy environment file
cp .env.example .env

# Edit .env to point to your host Ollama
# OLLAMA_HOST=http://host.docker.internal:11434

# Start services
docker compose up -d
```

### 2. Full Stack (with Ollama in Docker)

Run everything in Docker including Ollama:

```bash
# Copy environment file
cp .env.example .env

# Start all services including Ollama
docker compose --profile full up -d
```

### 3. Cloud Provider (OpenAI)

Use OpenAI instead of local Ollama:

```bash
# Set up environment
cp .env.example .env

# Edit .env:
# CLAUDE_OS_PROVIDER=openai
# OPENAI_API_KEY=sk-your-api-key

# Start services
docker compose up -d
```

## Docker Compose Profiles

| Profile | Description | Command |
|---------|-------------|---------|
| (default) | API + Redis + Frontend | `docker compose up -d` |
| `dev` | Development with hot reload | `docker compose --profile dev up` |
| `ollama` | Include Ollama service | `docker compose --profile ollama up -d` |
| `full` | All services including Ollama | `docker compose --profile full up -d` |

## Services

| Service | Port | Description |
|---------|------|-------------|
| `api` | 8051 | FastAPI server (MCP + REST) |
| `frontend` | 5173 | React web UI |
| `redis` | 6379 | Cache and job queue |
| `worker` | - | Background job processor |
| `ollama` | 11434 | Local LLM (optional) |

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and customize:

```bash
# Provider: local or openai
CLAUDE_OS_PROVIDER=local

# Ollama (local provider)
OLLAMA_HOST=http://ollama:11434
LLM_MODEL=llama3.2:3b
EMBEDDING_MODEL=nomic-embed-text

# OpenAI (cloud provider)
OPENAI_API_KEY=sk-...

# Ports
CLAUDE_OS_PORT=8051
FRONTEND_PORT=5173
```

### Using External Ollama

If Ollama is running on your host:

```bash
# macOS/Windows
OLLAMA_HOST=http://host.docker.internal:11434

# Linux (use host network IP)
OLLAMA_HOST=http://172.17.0.1:11434
```

## Building Images

### Build all images

```bash
docker compose build
```

### Build specific service

```bash
docker compose build api
docker compose build frontend
```

### Build with no cache

```bash
docker compose build --no-cache
```

## Development Mode

For development with hot reload:

```bash
# Start in dev mode
docker compose --profile dev up

# Frontend available at http://localhost:5173
# API available at http://localhost:8051
```

## Volumes

| Volume | Purpose |
|--------|---------|
| `claude-os-data` | SQLite database |
| `claude-os-logs` | Application logs |
| `claude-os-redis` | Redis persistence |
| `claude-os-ollama` | Ollama models |

### Backup Data

```bash
# Backup database
docker run --rm -v claude-os-data:/data -v $(pwd):/backup alpine tar cvf /backup/claude-os-data.tar /data

# Restore database
docker run --rm -v claude-os-data:/data -v $(pwd):/backup alpine tar xvf /backup/claude-os-data.tar -C /
```

## GPU Support

For GPU acceleration with Ollama:

```bash
# Ensure NVIDIA container toolkit is installed
# https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html

# Start with GPU support
docker compose --profile full up -d
```

The `ollama` service is configured to use NVIDIA GPUs when available.

## Troubleshooting

### Check service status

```bash
docker compose ps
```

### View logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f api
```

### Health checks

```bash
# API health
curl http://localhost:8051/health

# Ollama health
curl http://localhost:11434/api/tags
```

### Reset everything

```bash
# Stop and remove containers
docker compose down

# Remove volumes (WARNING: deletes data)
docker compose down -v

# Rebuild and start fresh
docker compose build --no-cache
docker compose up -d
```

## Non-Interactive Setup

For CI/CD or automated deployments:

```bash
# Set environment variables
export CLAUDE_OS_PROVIDER=local
export CLAUDE_OS_MODEL_SIZE=lite

# Run setup in non-interactive mode
./setup-claude-os.sh --noninteractive
```

Or use Docker directly without the setup script:

```bash
docker compose --profile full up -d
```

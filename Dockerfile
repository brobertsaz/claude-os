# ============================================================================
# Claude OS - Main API Server Dockerfile
# ============================================================================
# Multi-stage build for optimized production image
# ============================================================================

FROM python:3.12-slim AS builder

# Build arguments
ARG TARGETARCH

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /build

# Copy requirements first for better caching
COPY requirements.txt .

# Create virtual environment and install dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# ============================================================================
# Production stage
# ============================================================================
FROM python:3.12-slim AS production

# Labels
LABEL org.opencontainers.image.title="Claude OS API Server"
LABEL org.opencontainers.image.description="AI Memory System for Claude Code"
LABEL org.opencontainers.image.source="https://github.com/brobertsaz/claude-os"

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    # Claude OS configuration
    CLAUDE_OS_HOST=0.0.0.0 \
    CLAUDE_OS_PORT=8051 \
    CLAUDE_OS_DB_PATH=/data/claude-os.db \
    # Provider configuration (local or openai)
    CLAUDE_OS_PROVIDER=local \
    # Ollama configuration
    OLLAMA_HOST=http://ollama:11434 \
    LLM_MODEL=llama3.2:3b \
    EMBEDDING_MODEL=nomic-embed-text \
    # OpenAI configuration (if using cloud provider)
    OPENAI_API_KEY="" \
    # Redis configuration
    REDIS_HOST=redis \
    REDIS_PORT=6379

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --shell /bin/bash claude

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=claude:claude app/ ./app/
COPY --chown=claude:claude mcp_server/ ./mcp_server/
COPY --chown=claude:claude templates/ ./templates/
COPY --chown=claude:claude scripts/docker-entrypoint.sh /docker-entrypoint.sh

# Create necessary directories
RUN mkdir -p /data /logs && \
    chown -R claude:claude /data /logs /app && \
    chmod +x /docker-entrypoint.sh

# Switch to non-root user
USER claude

# Expose port
EXPOSE 8051

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8051/health || exit 1

# Entrypoint
ENTRYPOINT ["/docker-entrypoint.sh"]

# Default command
CMD ["python", "mcp_server/server.py"]

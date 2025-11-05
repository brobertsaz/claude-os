FROM python:3.11-slim as builder

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install Python dependencies
COPY requirements.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Final stage
FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libmagic1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy only necessary application files
COPY mcp_server/ /app/mcp_server/
COPY app/core/ /app/app/core/
COPY app/db/ /app/app/db/
COPY app/utils/ /app/app/utils/
COPY app/__init__.py /app/app/__init__.py

# Create data directory for database
RUN mkdir -p /app/data

# Expose MCP server port
EXPOSE 8051

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8051/health || exit 1

# Run MCP server
CMD ["python", "-m", "uvicorn", "mcp_server.server:app", "--host", "0.0.0.0", "--port", "8051"]

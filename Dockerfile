FROM python:3.11-slim

# Set working directory
WORKDIR /workspace

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY ./app /workspace/app
COPY ./mcp_server /workspace/mcp_server

# Create data directories
RUN mkdir -p /workspace/data/uploads

# Copy container entrypoint script
COPY entrypoint.sh /workspace/entrypoint.sh
RUN chmod +x /workspace/entrypoint.sh

# Expose MCP server port
EXPOSE 8051

# Set environment variables
ENV MCP_SERVER_PORT=8051
ENV PYTHONPATH=/workspace:$PYTHONPATH

# Run entrypoint script
CMD ["/workspace/entrypoint.sh"]


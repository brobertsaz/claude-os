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
COPY ./.streamlit /workspace/.streamlit

# Create data directories
RUN mkdir -p /workspace/data/uploads

# Copy startup script
COPY start.sh /workspace/start.sh
RUN chmod +x /workspace/start.sh

# Expose ports
EXPOSE 8501 8051

# Set environment variables
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV MCP_SERVER_PORT=8051
ENV PYTHONPATH=/workspace:$PYTHONPATH

# Run startup script
CMD ["/workspace/start.sh"]


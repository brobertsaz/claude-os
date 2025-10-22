#!/bin/bash

# Set Python path to include workspace
export PYTHONPATH=/workspace:$PYTHONPATH

# Start MCP server in background
echo "Starting MCP server on port 8051..."
cd /workspace && python mcp_server/server.py &
MCP_PID=$!

# Start Streamlit UI
echo "Starting Streamlit UI on port 8501..."
cd /workspace && streamlit run app/main.py --server.headless true --server.port 8501 --server.address 0.0.0.0 &
STREAMLIT_PID=$!

# Wait for both processes
wait $MCP_PID $STREAMLIT_PID


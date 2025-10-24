"""
Welcome page for Code-Forge with onboarding and system status checks.
"""

import streamlit as st
import os
import subprocess
import requests
from app.core.pg_manager import get_pg_manager
from app.core.config import Config

# Page config
st.set_page_config(
    page_title="Welcome to Code-Forge",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Redirect to Welcome page (this IS the default landing page)
st.switch_page("pages/0_Welcome.py")

# Custom CSS for Archon-inspired design
st.markdown("""
<style>
    .big-title {
        font-size: 3rem;
        font-weight: bold;
        background: linear-gradient(135deg, hsl(271, 91%, 65%), hsl(330, 90%, 65%));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 1rem;
    }
    .subtitle {
        text-align: center;
        color: hsl(160, 84%, 39%);
        font-size: 1.2rem;
        margin-bottom: 2rem;
    }
    .feature-box {
        background: linear-gradient(135deg, rgba(139, 92, 246, 0.1), rgba(236, 72, 153, 0.1));
        border-left: 4px solid hsl(271, 91%, 65%);
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .status-good {
        color: hsl(160, 84%, 39%);
        font-weight: bold;
    }
    .status-bad {
        color: hsl(0, 84%, 60%);
        font-weight: bold;
    }
    .status-warning {
        color: hsl(45, 93%, 47%);
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="big-title">🔥 Welcome to Code-Forge</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Production-Grade RAG System with PostgreSQL + pgvector</div>', unsafe_allow_html=True)

# Navigation
nav1, nav2, nav3, nav4 = st.columns([1, 1, 1, 6])
with nav1:
    if st.button("🏠 Welcome", use_container_width=True, key="nav_welcome", type="primary"):
        st.switch_page("pages/0_Welcome.py")
with nav2:
    if st.button("⚙️ Main", use_container_width=True, key="nav_main"):
        st.switch_page("main.py")

# Introduction
st.markdown("""
---

## 🚀 What is Code-Forge?

**Code-Forge** is a **localized, production-grade RAG (Retrieval-Augmented Generation) system** that runs entirely on your machine.

### Key Features:

- **🗄️ PostgreSQL + pgvector** - ACID-compliant vector database
- **🤖 Ollama** - Local LLMs and embeddings (no API keys needed)
- **🔌 MCP Integration** - Expose knowledge bases to AI agents
- **📚 Multi-KB Architecture** - Isolated knowledge bases per project
- **🧠 Advanced RAG** - Vector search, hybrid search, reranking, agentic RAG
- **🎨 Beautiful UI** - Archon-inspired design

---
""")

# System Status Check
st.markdown("## 🔍 System Status")

col1, col2, col3 = st.columns(3)

# Check PostgreSQL
with col1:
    st.markdown("### PostgreSQL")
    try:
        pg_manager = get_pg_manager()
        # Try to list collections
        collections = pg_manager.list_collections()
        st.markdown(f'<p class="status-good">✅ Connected</p>', unsafe_allow_html=True)
        st.metric("Knowledge Bases", len(collections))
    except Exception as e:
        st.markdown(f'<p class="status-bad">❌ Not Connected</p>', unsafe_allow_html=True)
        st.error(f"Error: {str(e)}")
        st.info("Make sure PostgreSQL is running and the `codeforge` database exists.")

# Check Ollama
with col2:
    st.markdown("### Ollama")
    try:
        response = requests.get(f"{Config.OLLAMA_HOST}/api/tags", timeout=2)
        if response.status_code == 200:
            models = response.json().get("models", [])
            st.markdown(f'<p class="status-good">✅ Running</p>', unsafe_allow_html=True)
            st.metric("Models Installed", len(models))
        else:
            st.markdown(f'<p class="status-warning">⚠️ Unexpected Response</p>', unsafe_allow_html=True)
    except Exception as e:
        st.markdown(f'<p class="status-bad">❌ Not Running</p>', unsafe_allow_html=True)
        st.error(f"Error: {str(e)}")
        st.info("Make sure Ollama container is running: `docker-compose up -d`")

# Check Required Models
with col3:
    st.markdown("### Required Models")
    try:
        response = requests.get(f"{Config.OLLAMA_HOST}/api/tags", timeout=2)
        if response.status_code == 200:
            models = response.json().get("models", [])
            model_names = [m["name"] for m in models]

            required_models = ["nomic-embed-text:latest", "llama3.2:3b"]
            missing_models = [m for m in required_models if m not in model_names]

            if not missing_models:
                st.markdown(f'<p class="status-good">✅ All Present</p>', unsafe_allow_html=True)
                st.success("All required models are installed!")
            else:
                st.markdown(f'<p class="status-warning">⚠️ Missing Models</p>', unsafe_allow_html=True)
                st.warning(f"Missing: {', '.join(missing_models)}")
                st.info("Run: `ollama pull nomic-embed-text && ollama pull llama3.2:3b`")
    except Exception:
        st.markdown(f'<p class="status-bad">❌ Cannot Check</p>', unsafe_allow_html=True)

st.markdown("---")

# Quick Start Guide
st.markdown("## 🎯 Quick Start Guide")

tab1, tab2, tab3, tab4 = st.tabs(["1️⃣ Create KB", "2️⃣ Ingest Docs", "3️⃣ Query", "4️⃣ MCP"])

with tab1:
    st.markdown("""
    ### Creating Your First Knowledge Base

    1. **Navigate to the main page** (use the sidebar)
    2. **Expand "➕ Create New KB"** in the sidebar
    3. **Choose a KB type**:
       - 📚 **GENERIC** - General-purpose knowledge
       - 💻 **CODE** - Source code repositories
       - 📖 **DOCUMENTATION** - Technical documentation
       - 🤖 **AGENT_OS** - Spec-driven development
    4. **Enter a name** (e.g., `my-project`)
    5. **Add a description** (optional)
    6. **Click "Create"**

    ✨ Your knowledge base is now ready for documents!
    """)

    st.info("💡 **Tip**: Use separate KBs for different projects to keep contexts isolated.")

with tab2:
    st.markdown("""
    ### Ingesting Documents

    **Option 1: File Upload**
    1. Select your KB from the sidebar
    2. Go to the **"📚 Knowledge Base"** tab
    3. Click **"Choose files"** and select documents
    4. Click **"Upload Files"**

    **Option 2: Directory Import**
    1. Select your KB from the sidebar
    2. Go to the **"📚 Knowledge Base"** tab
    3. Enter the full path to your project directory
    4. Click **"Import Directory"**

    **Supported File Types:**
    - Documents: `.md`, `.txt`, `.pdf`
    - Code: `.py`, `.js`, `.jsx`, `.ts`, `.tsx`, `.go`, `.rs`, `.java`, `.cpp`, `.c`, `.h`
    - Config: `.json`, `.yaml`, `.yml`
    """)

    st.info("💡 **Tip**: For large codebases, use directory import to ingest all files at once.")

with tab3:
    st.markdown("""
    ### Querying Your Knowledge Base

    1. **Select your KB** from the sidebar
    2. **Go to the "💬 Chat" tab**
    3. **Choose a RAG strategy**:
       - 🔍 **Base** - Simple vector search (fastest)
       - 🔀 **Hybrid** - BM25 + vector fusion (better for keywords)
       - 🎯 **Reranking** - Cross-encoder reranking (most accurate)
       - 🤖 **Agentic** - Sub-question decomposition (best for complex queries)
    4. **Type your question** and press Enter
    5. **View sources** by expanding "📚 View Sources"

    **Example Queries:**
    - "How does authentication work in this codebase?"
    - "What are the main components of the system?"
    - "Show me examples of error handling"
    """)

    st.info("💡 **Tip**: Use hybrid search for technical queries with specific keywords.")

with tab4:
    st.markdown("""
    ### MCP Integration (Model Context Protocol)

    Code-Forge exposes your knowledge bases via HTTP for AI agent integration.

    **MCP Server Endpoint:**
    ```
    http://localhost:8051/mcp
    ```

    **Available Tools:**
    - `list_knowledge_bases` - List all KBs
    - `create_knowledge_base` - Create new KB
    - `search_knowledge_base` - Query KB with RAG
    - `get_kb_stats` - Get KB statistics
    - `ingest_documents` - Add documents
    - `get_standards` - Get Agent OS standards
    - `get_workflows` - Get Agent OS workflows
    - `get_specs` - Get Agent OS specs

    **Example Request:**
    ```bash
    curl -X POST http://localhost:8051/mcp \\
      -H "Content-Type: application/json" \\
      -d '{
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
          "name": "search_knowledge_base",
          "arguments": {
            "kb_name": "my-docs",
            "query": "How do I configure authentication?",
            "strategy": "hybrid"
          }
        }
      }'
    ```
    """)

    st.info("💡 **Tip**: See the README for full MCP API documentation.")

st.markdown("---")

# Feature Highlights
st.markdown("## ✨ Feature Highlights")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div class="feature-box">
        <h3>🗄️ Production-Grade Database</h3>
        <p>PostgreSQL + pgvector ensures your data is safe with ACID compliance,
        transaction safety, and bulletproof persistence. Your data survives all
        Docker operations and system restarts.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="feature-box">
        <h3>🧠 Advanced RAG Strategies</h3>
        <p>Choose from multiple retrieval strategies: vector search, hybrid search
        (BM25 + vector), reranking with cross-encoders, or agentic RAG with
        sub-question decomposition.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="feature-box">
        <h3>🔒 100% Local & Private</h3>
        <p>All data stays on your machine. No API keys, no cloud dependencies,
        no telemetry. Perfect for sensitive codebases and proprietary documentation.</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="feature-box">
        <h3>🤖 Agent OS Support</h3>
        <p>First-class support for spec-driven development with Agent OS.
        Ingest standards, workflows, and specs with specialized retrieval tools.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="feature-box">
        <h3>🔌 MCP Integration</h3>
        <p>Expose your knowledge bases to AI agents via Model Context Protocol.
        12 HTTP endpoints for seamless integration with Claude Desktop and other agents.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="feature-box">
        <h3>📚 Multi-KB Architecture</h3>
        <p>Create isolated knowledge bases for different projects. Each KB has
        its own type, metadata, and documents. Perfect for teams working on
        multiple projects.</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Resources
st.markdown("## 📚 Resources")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    ### 📖 Documentation
    - [README.md](../README.md)
    - [Setup Guide](../docs/SETUP.md)
    - [Usage Guide](../docs/USAGE.md)
    - [Troubleshooting](../docs/TROUBLESHOOTING.md)
    """)

with col2:
    st.markdown("""
    ### 🔗 Quick Links
    - [Streamlit UI](http://localhost:8501)
    - [MCP Server](http://localhost:8051)
    - [Ollama API](http://localhost:11434)
    """)

with col3:
    st.markdown("""
    ### 🛠️ Useful Commands
    ```bash
    # View logs
    docker-compose logs -f

    # Restart services
    docker-compose restart

    # Stop services
    docker-compose down
    ```
    """)

st.markdown("---")

# Footer
st.markdown("""
<div style="text-align: center; color: hsl(271, 91%, 65%); margin-top: 2rem;">
    <p><strong>Ready to get started?</strong></p>
    <p>Use the sidebar to navigate to the main page and create your first knowledge base!</p>
    <p style="margin-top: 2rem; font-size: 0.9rem;">Built with ❤️ for the local-first AI community</p>
</div>
""", unsafe_allow_html=True)


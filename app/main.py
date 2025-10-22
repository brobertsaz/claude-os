"""
Code-Forge: Localized Multi-KB RAG System
Main Streamlit application with badass Archon-inspired UI.
"""

import logging
import os
from pathlib import Path

import streamlit as st

from app.core.chroma_manager import get_chroma_manager
from app.core.config import Config
from app.core.health import check_chroma_health, check_ollama_health
from app.core.ingestion import ingest_directory, ingest_file
from app.core.kb_metadata import get_documents_metadata
from app.core.rag_engine import RAGEngine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Code-Forge 🔥",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if "selected_kb" not in st.session_state:
    st.session_state.selected_kb = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "rag_settings" not in st.session_state:
    st.session_state.rag_settings = {
        "hybrid": False,
        "rerank": False,
        "agentic": False
    }

# Custom CSS with Archon aesthetic
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Material+Icons&display=swap');

    * {
        font-family: 'JetBrains Mono', monospace !important;
    }

    /* Hide Material Icons text in expanders and buttons */
    [data-testid="stIconMaterial"] {
        font-size: 0 !important;
        width: 20px !important;
        height: 20px !important;
        display: inline-block !important;
        position: relative !important;
    }

    /* Replace expander arrow with CSS */
    [data-testid="stIconMaterial"]::before {
        content: "▶" !important;
        font-size: 14px !important;
        color: hsl(271, 91%, 65%) !important;
        position: absolute !important;
        top: 50% !important;
        left: 50% !important;
        transform: translate(-50%, -50%) !important;
        font-family: 'JetBrains Mono', monospace !important;
    }

    /* Rotate arrow when expander is open */
    details[open] [data-testid="stIconMaterial"]::before {
        transform: translate(-50%, -50%) rotate(90deg) !important;
    }

    /* Hide sidebar collapse button if it exists */
    [data-testid="collapsedControl"] {
        display: none !important;
    }

    /* Root app container */
    .stApp {
        background-color: #0E0E0E;
    }

    /* Fix main content area - prevent cutoff */
    .main .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
        padding-left: 5rem !important;
        padding-right: 5rem !important;
        max-width: none !important;
    }

    .main {
        background-color: #0E0E0E;
    }

    /* Ensure all content has proper spacing */
    .element-container {
        margin-left: 0 !important;
        padding-left: 0 !important;
    }

    /* Fix sidebar width and padding - make it wider and disable collapse */
    section[data-testid="stSidebar"] {
        width: 450px !important;
        min-width: 450px !important;
        max-width: 450px !important;
        background-color: #0E0E0E;
        border-right: 2px solid hsl(271, 91%, 65%);
        overflow-x: hidden !important;
    }

    [data-testid="stSidebar"] > div:first-child {
        padding: 2rem 1.5rem !important;
        width: 100% !important;
        overflow-x: hidden !important;
    }

    [data-testid="stSidebar"] .element-container {
        padding-left: 0 !important;
        margin-left: 0 !important;
        width: 100% !important;
        max-width: 100% !important;
        overflow-x: hidden !important;
    }

    /* Completely hide sidebar collapse button */
    [data-testid="collapsedControl"],
    button[kind="header"] {
        display: none !important;
        visibility: hidden !important;
    }

    /* Make sidebar text wrap properly with better font sizes */
    [data-testid="stSidebar"] .stMarkdown {
        width: 100% !important;
        max-width: 100% !important;
        overflow-wrap: break-word !important;
        word-wrap: break-word !important;
    }

    [data-testid="stSidebar"] code {
        font-size: 11px !important;
        word-break: break-all !important;
        white-space: pre-wrap !important;
        line-height: 1.4 !important;
    }

    [data-testid="stSidebar"] pre {
        white-space: pre-wrap !important;
        word-wrap: break-word !important;
        overflow-x: hidden !important;
        max-width: 100% !important;
        font-size: 11px !important;
        line-height: 1.4 !important;
    }

    [data-testid="stSidebar"] p {
        overflow-wrap: break-word !important;
        word-wrap: break-word !important;
        font-size: 13px !important;
    }

    /* Larger text for headings in sidebar */
    [data-testid="stSidebar"] h3 {
        font-size: 16px !important;
    }

    [data-testid="stSidebar"] h4 {
        font-size: 14px !important;
    }

    /* Fix expander headers in sidebar */
    [data-testid="stSidebar"] .streamlit-expanderHeader {
        font-size: 13px !important;
        overflow-wrap: break-word !important;
        word-wrap: break-word !important;
    }

    [data-testid="stSidebar"] details summary {
        overflow-wrap: break-word !important;
        word-wrap: break-word !important;
    }

    /* Fix any negative margins */
    div[data-testid="column"] {
        padding-left: 0 !important;
    }

    /* Status indicators */
    .status-healthy {
        color: hsl(160, 84%, 39%);
        font-weight: bold;
        text-shadow: 0 0 10px hsl(160, 84%, 39%);
    }

    .status-unhealthy {
        color: #FF0000;
        font-weight: bold;
        text-shadow: 0 0 10px #FF0000;
    }

    /* Document cards */
    .doc-card {
        background: linear-gradient(135deg, #1A1A1A 0%, #0E0E0E 100%);
        border: 2px solid hsl(330, 90%, 65%);
        border-radius: 12px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 8px 16px rgba(233, 30, 99, 0.3);
        transition: all 0.3s ease;
    }

    .doc-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 24px rgba(233, 30, 99, 0.5);
        border-color: hsl(271, 91%, 65%);
    }

    /* Tags */
    .tag {
        display: inline-block;
        background: linear-gradient(135deg, hsl(271, 91%, 65%) 0%, hsl(330, 90%, 65%) 100%);
        color: white;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 11px;
        font-weight: bold;
        margin: 2px;
        box-shadow: 0 2px 4px rgba(156, 39, 176, 0.3);
    }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #E91E63 0%, hsl(271, 91%, 65%) 100%);
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: bold;
        padding: 12px 24px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 8px rgba(233, 30, 99, 0.3);
        width: 100% !important;
        max-width: 100% !important;
    }

    .stButton > button:hover {
        box-shadow: 0 0 30px rgba(233, 30, 99, 0.8);
        transform: scale(1.05);
    }

    /* Fix sidebar buttons to not overflow */
    [data-testid="stSidebar"] .stButton > button {
        font-size: 12px !important;
        padding: 8px 12px !important;
        white-space: normal !important;
        word-wrap: break-word !important;
    }

    /* Chat messages */
    .user-message {
        background: linear-gradient(135deg, #E91E63 0%, hsl(271, 91%, 65%) 100%);
        color: white;
        padding: 16px;
        border-radius: 12px;
        margin: 12px 0;
        box-shadow: 0 4px 8px rgba(233, 30, 99, 0.3);
    }

    .assistant-message {
        background: #1A1A1A;
        color: white;
        padding: 16px;
        border-radius: 12px;
        margin: 12px 0;
        border-left: 4px solid hsl(160, 84%, 39%);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.5);
    }

    /* Header */
    .main-header {
        text-align: center;
        padding: 20px;
        background: linear-gradient(135deg, #0E0E0E 0%, #1A1A1A 100%);
        border-bottom: 2px solid hsl(271, 91%, 65%);
        margin-bottom: 20px;
    }

    .main-header h1 {
        color: hsl(271, 91%, 65%);
        text-shadow: 0 0 20px hsl(271, 91%, 65%);
    }

    .main-header p {
        color: hsl(160, 84%, 39%);
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="main-header">
    <h1>🔥 Code-Forge</h1>
    <p>Localized Multi-KB RAG System with MCP Integration</p>
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("## ⚙️ Settings")

    # Connection Status
    st.markdown("### 🔌 Connection Status")

    ollama_status = check_ollama_health()
    chroma_status = check_chroma_health()

    if ollama_status["status"] == "healthy":
        st.markdown('<p class="status-healthy">🟢 Ollama Connected</p>', unsafe_allow_html=True)
        if ollama_status.get("models"):
            st.caption(f"Models: {', '.join(ollama_status['models'][:3])}")
    else:
        st.markdown('<p class="status-unhealthy">🔴 Ollama Disconnected</p>', unsafe_allow_html=True)
        st.caption(ollama_status.get("error", "Unknown error"))

    if chroma_status["status"] == "healthy":
        st.markdown('<p class="status-healthy">🟢 ChromaDB Connected</p>', unsafe_allow_html=True)
    else:
        st.markdown('<p class="status-unhealthy">🔴 ChromaDB Disconnected</p>', unsafe_allow_html=True)
        st.caption(chroma_status.get("error", "Unknown error"))

    st.divider()

    # MCP Server Info
    st.markdown("### 🔗 MCP Server")
    mcp_url = f"http://localhost:{Config.MCP_SERVER_PORT}/mcp"
    st.code(mcp_url, language="text")

    st.caption("**Connection Command:**")
    st.code(f"claude mcp add --transport http code-forge {mcp_url}", language="bash")

    st.divider()

    # Knowledge Base Selector
    st.markdown("### 📚 Knowledge Base")

    chroma_manager = get_chroma_manager()
    collections = chroma_manager.list_collections()

    if collections:
        selected = st.selectbox(
            "Select KB",
            collections,
            key="kb_selector"
        )
        st.session_state.selected_kb = selected
    else:
        st.warning("No knowledge bases found. Create one below!")
        st.session_state.selected_kb = None

    # Create new KB
    with st.expander("➕ Create New KB"):
        new_kb_name = st.text_input("KB Name", key="new_kb_name")
        if st.button("Create"):
            if new_kb_name:
                if chroma_manager.create_collection(new_kb_name):
                    st.success(f"Created KB: {new_kb_name}")
                    st.rerun()
                else:
                    st.error("Failed to create KB")
            else:
                st.error("Please enter a KB name")

    st.divider()

    # RAG Strategy Toggles
    st.markdown("### 🎯 RAG Strategies")

    st.session_state.rag_settings["hybrid"] = st.checkbox(
        "🔀 Hybrid Search",
        value=st.session_state.rag_settings["hybrid"],
        help="**Hybrid Search**: Combines semantic vector search with BM25 keyword search for better recall. Uses reciprocal rank fusion to merge results. Best for queries with specific technical terms."
    )

    st.session_state.rag_settings["rerank"] = st.checkbox(
        "🎯 Reranking",
        value=st.session_state.rag_settings["rerank"],
        help="**Reranking**: Re-scores retrieved chunks using a cross-encoder model (ms-marco-MiniLM) for higher precision. Keeps top 3 most relevant results. Improves answer quality but adds latency."
    )

    st.session_state.rag_settings["agentic"] = st.checkbox(
        "🤖 Agentic RAG",
        value=st.session_state.rag_settings["agentic"],
        help="**Agentic RAG**: Breaks complex questions into sub-questions and answers them independently before synthesizing. Best for multi-part or analytical queries. Slower but more thorough."
    )

# Main content tabs
tab1, tab2 = st.tabs(["📚 Knowledge Base", "💬 Chat"])

# Tab 1: Knowledge Base Management
with tab1:
    st.markdown("## 📚 Knowledge Base Management")

    if not st.session_state.selected_kb:
        st.info("👈 Please select or create a knowledge base from the sidebar")
    else:
        st.markdown(f"### Current KB: **{st.session_state.selected_kb}**")

        st.markdown("---")

        # Document Upload
        col1, col2 = st.columns(2, gap="large")

        with col1:
            st.markdown("#### 📤 Upload Documents")
            st.caption("Choose files to upload to the knowledge base")

            # Initialize upload counter in session state
            if "upload_counter" not in st.session_state:
                st.session_state.upload_counter = 0

            # Use dynamic key to reset file uploader after upload
            uploaded_files = st.file_uploader(
                "Choose files",
                accept_multiple_files=True,
                type=[ext.replace(".", "") for ext in Config.SUPPORTED_FILE_TYPES],
                label_visibility="collapsed",
                key=f"file_uploader_{st.session_state.upload_counter}"
            )

            if uploaded_files and st.button("Upload Files", key="upload_files_btn", use_container_width=True):
                try:
                    Config.ensure_upload_dir()
                    progress_bar = st.progress(0)
                    status_container = st.container()

                    for i, uploaded_file in enumerate(uploaded_files):
                        with status_container:
                            st.write(f"Processing: {uploaded_file.name}...")

                        # Save file
                        file_path = Path(Config.UPLOAD_DIR) / uploaded_file.name
                        with open(file_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())

                        # Ingest file
                        result = ingest_file(
                            str(file_path),
                            st.session_state.selected_kb,
                            uploaded_file.name
                        )

                        with status_container:
                            if result["status"] == "success":
                                st.success(f"✅ {uploaded_file.name}: {result['chunks']} chunks")
                            else:
                                st.error(f"❌ {uploaded_file.name}: {result.get('error', 'Unknown error')}")

                        progress_bar.progress((i + 1) / len(uploaded_files))

                    with status_container:
                        st.success("🎉 Upload complete! Refreshing document list...")

                    # Increment counter to reset file uploader on next render
                    st.session_state.upload_counter += 1

                    # Wait a moment before rerun so user can see the success message
                    import time
                    time.sleep(1.5)
                    st.rerun()

                except Exception as e:
                    st.error(f"❌ Upload failed: {str(e)}")
                    import traceback
                    st.code(traceback.format_exc())

        with col2:
            st.markdown("#### 📁 Import Directory")
            st.caption("Import all supported files from a directory")

            st.info("💡 **Tip:** Mount your directory as a volume in docker-compose.yml first. Paths are relative to `/workspace` in the container.")

            dir_path = st.text_input(
                "Directory Path",
                placeholder="/workspace/mounted_docs",
                help="Path must exist inside the Docker container",
                label_visibility="collapsed"
            )

            if st.button("Import Directory", key="import_dir_btn", use_container_width=True):
                if not dir_path:
                    st.error("Please enter a directory path")
                else:
                    with st.spinner("Importing files..."):
                        results = ingest_directory(dir_path, st.session_state.selected_kb)

                        if not results:
                            st.warning("No supported files found in directory")
                        elif results[0].get("error") and "not found" in results[0].get("error", ""):
                            st.error(f"Directory not found: {dir_path}")
                        else:
                            success_count = sum(1 for r in results if r.get("status") == "success")
                            error_count = len(results) - success_count

                            if success_count > 0:
                                st.success(f"✅ Imported {success_count} file(s)")
                            if error_count > 0:
                                st.warning(f"⚠️ {error_count} file(s) failed")

                            # Show first 5 results
                            for result in results[:5]:
                                if result.get("status") == "success":
                                    st.caption(f"✅ {result.get('filename', 'Unknown')}")
                                else:
                                    st.caption(f"❌ {result.get('filename', 'Unknown')}: {result.get('error', 'Unknown error')}")

                            if len(results) > 5:
                                st.caption(f"... and {len(results) - 5} more")

                    st.rerun()

        st.divider()

        # Document Grid
        st.markdown("#### 📄 Documents")

        docs = get_documents_metadata(st.session_state.selected_kb)

        if not docs:
            st.info("No documents in this knowledge base. Upload files to get started!")
        else:
            # Display in 3-column grid
            cols = st.columns(3)

            for i, doc in enumerate(docs):
                with cols[i % 3]:
                    # File icon based on type
                    icon_map = {
                        ".py": "🐍", ".js": "📜", ".jsx": "⚛️",
                        ".ts": "📘", ".tsx": "⚛️", ".md": "📄",
                        ".pdf": "📕", ".json": "📋", ".yaml": "⚙️"
                    }
                    icon = icon_map.get(doc["file_type"], "📄")

                    # Create card
                    tags_html = "".join([f'<span class="tag">{tag}</span>' for tag in doc["tags"]])

                    st.markdown(f"""
                    <div class="doc-card">
                        <div style="font-size: 24px;">{icon}</div>
                        <div style="font-weight: bold; margin: 8px 0;">{doc["filename"]}</div>
                        <div>{tags_html}</div>
                        <div style="font-size: 11px; color: #888; margin-top: 8px;">
                            {doc["formatted_date"]}<br>
                            {doc["chunk_count"]} chunks
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

# Tab 2: Chat Interface
with tab2:
    st.markdown("## 💬 Chat with Your Knowledge Base")

    if not st.session_state.selected_kb:
        st.info("👈 Please select a knowledge base from the sidebar")
    else:
        # Display active strategies banner
        active_strategies = []
        if st.session_state.rag_settings["hybrid"]:
            active_strategies.append("🔀 Hybrid Search")
        if st.session_state.rag_settings["rerank"]:
            active_strategies.append("🎯 Reranking")
        if st.session_state.rag_settings["agentic"]:
            active_strategies.append("🤖 Agentic RAG")

        if active_strategies:
            strategies_text = " + ".join(active_strategies)
            st.markdown(f"""
            <div style="background: linear-gradient(90deg, hsl(271 91% 65% / 0.15), hsl(160 84% 39% / 0.15));
                        border-left: 3px solid hsl(271 91% 65%);
                        padding: 12px 16px;
                        border-radius: 4px;
                        margin-bottom: 16px;
                        font-family: 'JetBrains Mono', monospace;">
                <strong>🎯 Active Retrieval Strategies:</strong> {strategies_text}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="background: hsl(0 0% 10%);
                        border-left: 3px solid hsl(0 0% 30%);
                        padding: 12px 16px;
                        border-radius: 4px;
                        margin-bottom: 16px;
                        font-family: 'JetBrains Mono', monospace;
                        color: hsl(0 0% 60%);">
                <strong>📊 Mode:</strong> Standard Vector Search
            </div>
            """, unsafe_allow_html=True)

        # Display chat history
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

                if message["role"] == "assistant" and message.get("sources"):
                    with st.expander("📚 View Sources"):
                        for i, source in enumerate(message["sources"][:3], 1):
                            st.markdown(f"**Source {i}:**")
                            st.code(source["text"][:200] + "..." if len(source["text"]) > 200 else source["text"])
                            if source.get("metadata"):
                                st.caption(f"From: {source['metadata'].get('filename', 'Unknown')}")
                            if source.get("score"):
                                st.caption(f"Score: {source['score']:.3f}")
                            st.divider()

        # Chat input
        if prompt := st.chat_input("Ask a question about your knowledge base..."):
            # Add user message
            st.session_state.chat_history.append({
                "role": "user",
                "content": prompt
            })

            # Display user message
            with st.chat_message("user"):
                st.markdown(prompt)

            # Generate response
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    try:
                        rag_engine = RAGEngine(st.session_state.selected_kb)
                        result = rag_engine.query(
                            prompt,
                            use_hybrid=st.session_state.rag_settings["hybrid"],
                            use_rerank=st.session_state.rag_settings["rerank"],
                            use_agentic=st.session_state.rag_settings["agentic"]
                        )

                        answer = result.get("answer", "No answer generated")
                        sources = result.get("sources", [])

                        st.markdown(answer)

                        # Add to history
                        st.session_state.chat_history.append({
                            "role": "assistant",
                            "content": answer,
                            "sources": sources
                        })

                        # Display sources
                        if sources:
                            with st.expander("📚 View Sources"):
                                for i, source in enumerate(sources[:3], 1):
                                    st.markdown(f"**Source {i}:**")
                                    st.code(source["text"][:200] + "..." if len(source["text"]) > 200 else source["text"])
                                    if source.get("metadata"):
                                        st.caption(f"From: {source['metadata'].get('filename', 'Unknown')}")
                                    if source.get("score"):
                                        st.caption(f"Score: {source['score']:.3f}")
                                    st.divider()

                    except Exception as e:
                        error_msg = f"Error: {str(e)}"
                        st.error(error_msg)
                        st.session_state.chat_history.append({
                            "role": "assistant",
                            "content": error_msg
                        })

        # Clear chat button
        if st.session_state.chat_history and st.button("🗑️ Clear Chat"):
            st.session_state.chat_history = []
            st.rerun()


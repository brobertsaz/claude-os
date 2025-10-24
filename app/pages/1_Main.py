"""
Code-Forge: Localized Multi-KB RAG System
Main Streamlit application with badass Archon-inspired UI.
"""

import logging
import os
from pathlib import Path

import streamlit as st

from app.core.pg_manager import get_pg_manager
from app.core.config import Config
from app.core.health import check_chroma_health, check_ollama_health
from app.core.ingestion import ingest_directory, ingest_file
from app.core.kb_metadata import get_documents_metadata, get_kb_type_badge, get_kb_type_summary
from app.core.kb_types import KBType, get_kb_type_choices, get_kb_type_info
from app.core.rag_engine import RAGEngine
from app.core.agent_os_ingestion import AgentOSIngestion

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Code-Forge 🔥",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="collapsed"
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

    /* Hide Streamlit's sidebar completely */
    section[data-testid="stSidebar"] {
        display: none !important;
    }
</style>

<style>

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

# Navigation
nav1, nav2, nav3 = st.columns([1, 1, 6])
with nav1:
    if st.button("🏠 Welcome", use_container_width=True, key="nav_welcome"):
        st.switch_page("pages/0_Welcome.py")
with nav2:
    if st.button("⚙️ Main", use_container_width=True, key="nav_main", type="primary"):
        st.switch_page("pages/1_Main.py")

st.divider()

# Create two-column layout: left panel + main content
left_col, main_col = st.columns([1, 3], gap="medium")

# Left Panel
with left_col:
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
        st.markdown('<p class="status-healthy">🟢 PostgreSQL Connected</p>', unsafe_allow_html=True)
    else:
        st.markdown('<p class="status-unhealthy">🔴 PostgreSQL Disconnected</p>', unsafe_allow_html=True)
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

    pg_manager = get_pg_manager()
    collections = pg_manager.list_collections()

    if collections:
        # Optional type filter
        type_summary = get_kb_type_summary()
        filter_options = ["All Types"] + [
            f"{get_kb_type_info(KBType(kb_type)).icon} {get_kb_type_info(KBType(kb_type)).name} ({count})"
            for kb_type, count in type_summary.items() if count > 0
        ]

        selected_filter = st.selectbox(
            "Filter by Type",
            options=filter_options,
            key="kb_type_filter"
        )

        # Filter collections if needed
        if selected_filter != "All Types":
            # Extract the KB type value from the filter string
            filter_type_value = None
            for kb_type, count in type_summary.items():
                type_info = get_kb_type_info(KBType(kb_type))
                if f"{type_info.icon} {type_info.name}" in selected_filter:
                    filter_type_value = kb_type
                    break

            if filter_type_value:
                collections = [
                    col for col in collections
                    if col["metadata"].get("kb_type") == filter_type_value
                ]

        # Build display options with type badges
        kb_display_options = []
        kb_name_map = {}  # Map display string to actual name

        for col in collections:
            name = col["name"]
            metadata = col["metadata"]
            kb_type = KBType(metadata.get("kb_type", KBType.GENERIC.value))
            type_info = get_kb_type_info(kb_type)

            display_name = f"{type_info.icon} {name}"
            kb_display_options.append(display_name)
            kb_name_map[display_name] = name

        selected_display = st.selectbox(
            "Select KB",
            kb_display_options,
            key="kb_selector"
        )

        # Map back to actual KB name
        st.session_state.selected_kb = kb_name_map[selected_display]

        # Display selected KB metadata
        selected_col = next(
            (col for col in collections if col["name"] == st.session_state.selected_kb),
            None
        )

        if selected_col:
            metadata = selected_col["metadata"]
            kb_type = KBType(metadata.get("kb_type", KBType.GENERIC.value))

            # Show type badge
            st.markdown(get_kb_type_badge(kb_type), unsafe_allow_html=True)

            # Show description if available
            description = metadata.get("description", "")
            if description:
                st.caption(description)
    else:
        st.warning("No knowledge bases found. Create one below!")
        st.session_state.selected_kb = None

    # Create new KB
    with st.expander("➕ Create New KB"):
        new_kb_name = st.text_input("KB Name", key="new_kb_name", placeholder="my-project")

        # KB Type Selector
        kb_type_choices = get_kb_type_choices()
        selected_type_display = st.selectbox(
            "KB Type",
            options=kb_type_choices,
            key="kb_type_selector",
            help="Select the type of knowledge base to create"
        )

        # Extract the actual KBType from the display string
        # Format is "🤖 Agent OS Profile" -> need to map back to KBType
        type_map = {choice: kb_type for kb_type, choice in zip(KBType, kb_type_choices)}
        selected_kb_type = type_map[selected_type_display]

        # Show type-specific info
        type_info = get_kb_type_info(selected_kb_type)
        st.caption(f"**{type_info.description}**")

        # Optional description
        kb_description = st.text_area(
            "Description (optional)",
            key="kb_description",
            placeholder="Brief description of this knowledge base...",
            height=80
        )

        if st.button("Create", type="primary"):
            if new_kb_name:
                if pg_manager.create_collection(
                    name=new_kb_name,
                    kb_type=selected_kb_type,
                    description=kb_description
                ):
                    st.success(f"✅ Created {type_info.icon} **{new_kb_name}** ({type_info.name})")
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

# Main content area (right column)
with main_col:
    # Main content tabs
    tab1, tab2 = st.tabs(["📚 Knowledge Base", "💬 Chat"])

    # Tab 1: Knowledge Base Management
    with tab1:
        st.markdown("## 📚 Knowledge Base Management")

        if not st.session_state.selected_kb:
            st.info("👈 Please select or create a knowledge base from the left panel")
        else:
            st.markdown(f"### Current KB: **{st.session_state.selected_kb}**")

            st.markdown("---")

            # Document Upload
            doc_col1, doc_col2 = st.columns(2, gap="large")

            with doc_col1:
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

        with doc_col2:
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

        # Agent OS Profile Import (only for Agent OS KBs)
        kb_metadata = pg_manager.get_collection_metadata(st.session_state.selected_kb)
        kb_type_str = kb_metadata.get("kb_type", "generic")

        if kb_type_str == "agent-os":
            st.markdown("---")
            st.markdown("#### 🤖 Import Agent OS Profile")
            st.caption("Import an Agent OS profile directory with standards, agents, workflows, and commands")

            st.info("💡 **Tip:** Mount your Agent OS profile directory as a volume in docker-compose.yml. The path should point to the profile root (containing standards/, agents/, etc.)")

            agent_os_path = st.text_input(
                "Agent OS Profile Path",
                placeholder="/workspace/my-agent-os-profile",
                help="Path to Agent OS profile directory (must exist inside the Docker container)",
                key="agent_os_path_input"
            )

            if st.button("Import Agent OS Profile", key="import_agent_os_btn", use_container_width=True):
                if not agent_os_path:
                    st.error("Please enter an Agent OS profile path")
                else:
                    with st.spinner("Parsing and ingesting Agent OS profile..."):
                        try:
                            agent_os_ingestion = AgentOSIngestion(pg_manager)
                            stats = agent_os_ingestion.ingest_profile(
                                kb_name=st.session_state.selected_kb,
                                profile_path=agent_os_path
                            )

                            if stats.get("success"):
                                st.success(f"✅ Imported {stats['total_documents']} Agent OS documents!")

                                # Show breakdown by type
                                st.markdown("**Documents by type:**")
                                for content_type, count in stats.get("documents_by_type", {}).items():
                                    type_emoji = {
                                        "standard": "📋",
                                        "agent": "🤖",
                                        "workflow": "🔄",
                                        "command": "⚡",
                                        "product": "🎯",
                                        "spec": "📝"
                                    }.get(content_type, "📄")
                                    st.caption(f"{type_emoji} {content_type}: {count}")

                                st.rerun()
                            else:
                                st.error("❌ Agent OS import failed")
                                if stats.get("errors"):
                                    for error in stats["errors"]:
                                        st.caption(f"⚠️ {error}")

                        except Exception as e:
                            st.error(f"❌ Agent OS import failed: {str(e)}")
                            import traceback
                            st.code(traceback.format_exc())

        st.divider()

        # Agent OS Content Stats (only for Agent OS KBs)
        if kb_type_str == "agent-os":
            agent_os_ingestion = AgentOSIngestion(pg_manager)
            agent_os_stats = agent_os_ingestion.get_profile_stats(st.session_state.selected_kb)

            if agent_os_stats.get("total_documents", 0) > 0:
                st.markdown("#### 🤖 Agent OS Content")

                # Display stats in columns
                stat_cols = st.columns(len(agent_os_stats.get("documents_by_type", {})) or 1)

                type_info = {
                    "standard": {"emoji": "📋", "name": "Standards"},
                    "agent": {"emoji": "🤖", "name": "Agents"},
                    "workflow": {"emoji": "🔄", "name": "Workflows"},
                    "command": {"emoji": "⚡", "name": "Commands"},
                    "product": {"emoji": "🎯", "name": "Product"},
                    "spec": {"emoji": "📝", "name": "Specs"}
                }

                for idx, (content_type, count) in enumerate(agent_os_stats.get("documents_by_type", {}).items()):
                    info = type_info.get(content_type, {"emoji": "📄", "name": content_type.title()})
                    with stat_cols[idx]:
                        st.metric(
                            label=f"{info['emoji']} {info['name']}",
                            value=count
                        )

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
            st.info("👈 Please select a knowledge base from the left panel")
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


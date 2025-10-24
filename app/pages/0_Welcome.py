"""
Welcome page for Code-Forge - Default landing page
"""

import streamlit as st
from pathlib import Path

# Page config
st.set_page_config(
    page_title="Welcome to Code-Forge",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS - Archon-inspired badass styling
st.markdown("""
<style>
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Hide sidebar completely */
    section[data-testid="stSidebar"] {
        display: none !important;
    }

    /* Hero section */
    .hero {
        background: linear-gradient(135deg,
            hsl(271, 91%, 15%) 0%,
            hsl(0, 0%, 0%) 50%,
            hsl(160, 84%, 15%) 100%);
        padding: 4rem 2rem;
        border-radius: 20px;
        margin-bottom: 2rem;
        border: 2px solid hsl(271, 91%, 65%);
        box-shadow: 0 0 40px hsla(271, 91%, 65%, 0.3);
        position: relative;
        overflow: hidden;
    }

    .hero::before {
        content: "";
        position: absolute;
        top: -50%;
        right: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, hsla(271, 91%, 65%, 0.1) 0%, transparent 70%);
        animation: pulse 8s ease-in-out infinite;
    }

    @keyframes pulse {
        0%, 100% { transform: scale(1); opacity: 0.5; }
        50% { transform: scale(1.1); opacity: 0.8; }
    }

    .hero-title {
        font-size: 4rem;
        font-weight: 900;
        background: linear-gradient(135deg, hsl(271, 91%, 65%), hsl(330, 90%, 65%), hsl(160, 84%, 39%));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 1rem;
        position: relative;
        z-index: 1;
        text-shadow: 0 0 30px hsla(271, 91%, 65%, 0.5);
    }

    .hero-subtitle {
        text-align: center;
        color: hsl(160, 84%, 39%);
        font-size: 1.5rem;
        margin-bottom: 2rem;
        position: relative;
        z-index: 1;
    }

    .hero-emoji {
        font-size: 6rem;
        text-align: center;
        margin-bottom: 1rem;
        filter: drop-shadow(0 0 20px hsla(271, 91%, 65%, 0.8));
        animation: float 3s ease-in-out infinite;
    }

    .hero-image {
        max-width: 600px;
        margin: 0 auto 2rem auto;
        display: block;
        border-radius: 15px;
        filter: drop-shadow(0 0 30px hsla(271, 91%, 65%, 0.6));
        animation: float 3s ease-in-out infinite;
    }

    @keyframes float {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-20px); }
    }

    .feature-card {
        background: linear-gradient(135deg, hsl(271, 91%, 10%), hsl(0, 0%, 5%));
        padding: 1.5rem;
        border-radius: 15px;
        border: 1px solid hsl(271, 91%, 35%);
        margin-bottom: 1rem;
        transition: all 0.3s ease;
    }

    .feature-card:hover {
        border-color: hsl(271, 91%, 65%);
        box-shadow: 0 0 20px hsla(271, 91%, 65%, 0.3);
        transform: translateY(-5px);
    }

    .cta-button {
        background: linear-gradient(135deg, hsl(271, 91%, 65%), hsl(330, 90%, 65%));
        color: white;
        padding: 1rem 2rem;
        border-radius: 10px;
        text-align: center;
        font-size: 1.2rem;
        font-weight: bold;
        margin: 2rem auto;
        cursor: pointer;
        border: none;
        box-shadow: 0 0 20px hsla(271, 91%, 65%, 0.5);
    }
</style>
""", unsafe_allow_html=True)

# Hero Section
hero_path = Path("assets/hero.png")

st.markdown('<div class="hero">', unsafe_allow_html=True)

if hero_path.exists():
    st.image(str(hero_path), use_container_width=False, output_format="PNG")
else:
    st.markdown('<div class="hero-emoji">🔥</div>', unsafe_allow_html=True)

st.markdown("""
    <div class="hero-title">CODE-FORGE</div>
    <div class="hero-subtitle">Production-Grade RAG System with PostgreSQL + pgvector</div>
</div>
""", unsafe_allow_html=True)

# Navigation
nav1, nav2, nav3 = st.columns([1, 1, 6])
with nav1:
    if st.button("🏠 Welcome", use_container_width=True, type="primary"):
        st.switch_page("pages/0_Welcome.py")
with nav2:
    if st.button("⚙️ Main", use_container_width=True):
        st.switch_page("pages/1_Main.py")

st.markdown("<br>", unsafe_allow_html=True)

st.markdown("""
## 🚀 What is Code-Forge?

**Code-Forge** is a **localized, production-grade RAG system** that runs entirely on your machine.

### Key Features:

- 🗄️ **PostgreSQL + pgvector** - ACID-compliant vector database
- 🤖 **Ollama** - Local LLMs and embeddings
- 🔌 **MCP Integration** - Expose knowledge bases to AI agents
- 📚 **Multi-KB Architecture** - Isolated knowledge bases per project
- 🧠 **Advanced RAG** - Vector search, hybrid search, reranking, agentic RAG

## 🎯 Quick Start

1. Click **"⚙️ Main"** button above
2. Create a Knowledge Base from the left panel
3. Upload documents or import a directory
4. Start chatting with your knowledge base

---

**Ready to get started? Click the "⚙️ Main" button above!**
""")

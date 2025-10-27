# 🚀 Sharing Claude OS with Your Team

This guide explains how to share Claude OS with coworkers so they can run it on their own machines.

## 📦 What Your Coworker Needs

### Prerequisites
1. **Docker Desktop** (includes Docker Compose)
   - Mac: https://docs.docker.com/desktop/install/mac-install/
   - Windows: https://docs.docker.com/desktop/install/windows-install/
   - Linux: https://docs.docker.com/desktop/install/linux-install/

2. **Git** (to clone the repository)
   - Mac: Pre-installed or via Homebrew: `brew install git`
   - Windows: https://git-scm.com/download/win
   - Linux: `sudo apt install git` or `sudo yum install git`

That's it! No Python, Node.js, or other dependencies needed - Docker handles everything.

---

## 🎯 Quick Start for Your Coworker

### Option 1: Share via Git Repository (Recommended)

**If you have a private Git repo:**

1. **Push your code to the repo:**
   ```bash
   git add .
   git commit -m "Add Claude OS RAG system"
   git push origin main
   ```

2. **Share the repo URL with your coworker**

3. **Your coworker clones and runs:**
   ```bash
   # Clone the repository
   git clone <your-repo-url>
   cd claude-os

   # Start the system
   docker compose up -d

   # Pull Ollama models (one-time setup)
   docker compose exec ollama ollama pull nomic-embed-text
   docker compose exec ollama ollama pull llama3.1
   ```

4. **Access the UI:**
   - Open browser: http://localhost:5173
   - Done! 🎉

---

### Option 2: Share as ZIP File

**If you don't have a Git repo:**

1. **Create a ZIP of your project:**
   ```bash
   cd /Users/iamanmp/Projects
   zip -r claude-os.zip claude-os \
     -x "claude-os/data/*" \
     -x "claude-os/.git/*" \
     -x "claude-os/__pycache__/*" \
     -x "claude-os/**/__pycache__/*"
   ```

2. **Share `claude-os.zip` via:**
   - Email (if < 25MB)
   - Google Drive / Dropbox / OneDrive
   - Slack / Teams file sharing

3. **Your coworker extracts and runs:**
   ```bash
   # Extract the ZIP
   unzip claude-os.zip
   cd claude-os

   # Start the system
   docker compose up -d

   # Pull Ollama models (one-time setup)
   docker compose exec ollama ollama pull nomic-embed-text
   docker compose exec ollama ollama pull llama3.1
   ```

---

## 🔧 What Gets Shared vs. What Doesn't

### ✅ Shared (in the repository/ZIP)
- **All source code** (`app/`, `mcp_server/`, `frontend/`, etc.)
- **Configuration files** (`docker-compose.yml`, `Dockerfile`, etc.)
- **Requirements** (`requirements.txt`, `package.json`)

### ❌ NOT Shared (stays local)
- **Ollama models** (~5GB) - Each person downloads their own
- **ChromaDB data** (knowledge bases) - Each person creates their own
- **Uploaded files** - Each person uploads their own documents
- **Docker volumes** - Created fresh on each machine

---

## 📊 Data Sharing Options

### If You Want to Share Knowledge Bases Too:

**Option A: Export/Import Knowledge Bases**

Currently, knowledge bases are stored in Docker volumes. To share them:

1. **Export ChromaDB data:**
   ```bash
   # Create a backup directory
   mkdir -p backups

   # Copy ChromaDB data from Docker volume
   docker compose cp chromadb:/chroma/chroma ./backups/chroma_data
   ```

2. **Share the backup:**
   - Add `backups/` to your ZIP or Git repo
   - Your coworker copies it to their ChromaDB volume:
     ```bash
     docker compose up -d chromadb
     docker compose cp ./backups/chroma_data chromadb:/chroma/chroma
     docker compose restart chromadb app
     ```

**Option B: Share Original Documents**

Simpler approach:
1. Create a `shared_docs/` folder in the repo
2. Add your markdown/PDF files there
3. Your coworker uploads them via the UI or directory import

---

## 🌐 Network Sharing (Same Office/VPN)

If you want your coworker to access **your running instance** instead of running their own:

### 1. Find Your Local IP Address

**Mac/Linux:**
```bash
ifconfig | grep "inet " | grep -v 127.0.0.1
```

**Windows:**
```cmd
ipconfig
```

Look for something like `192.168.1.100`

### 2. Update docker-compose.yml

Change the ports to bind to all interfaces:

```yaml
services:
  app:
    ports:
      - "0.0.0.0:8051:8051"  # MCP Server
  frontend:
    ports:
      - "0.0.0.0:5173:5173"  # React UI
```

### 3. Restart the containers

```bash
docker compose down
docker compose up -d
```

### 4. Share the URL

Your coworker can access:
- **UI**: `http://<your-ip>:5173`
- **MCP**: `http://<your-ip>:8051/mcp`

**⚠️ Security Note:** This exposes your instance to your local network. Only do this on trusted networks (office LAN, VPN). For internet sharing, use a reverse proxy with authentication.

---

## 🔐 Security Considerations

### For Local Sharing (Same Machine)
- ✅ Safe - Everything runs locally
- ✅ No authentication needed
- ✅ Data stays on the machine

### For Network Sharing (Same Office/VPN)
- ⚠️ Use only on trusted networks
- ⚠️ No built-in authentication
- ⚠️ Anyone on the network can access

### For Internet Sharing
- ❌ **NOT RECOMMENDED** without additional security
- If needed, use:
  - Reverse proxy (nginx, Caddy)
  - Authentication (OAuth, basic auth)
  - HTTPS/SSL certificates
  - Firewall rules

---

## 🐛 Troubleshooting for Your Coworker

### "Docker command not found"
- Install Docker Desktop: https://www.docker.com/products/docker-desktop/

### "Port 5173 already in use"
- Another app is using that port
- Change ports in `docker-compose.yml`:
  ```yaml
  frontend:
    ports:
      - "5174:5173"  # Use 5174 instead
  ```

### "Ollama models not found"
- They forgot to pull the models:
  ```bash
  docker compose exec ollama ollama pull nomic-embed-text
  docker compose exec ollama ollama pull llama3.1
  ```

### "ChromaDB connection error"
- Wait 10 seconds for services to start
- Check status: `docker compose ps`
- Restart: `docker compose restart`

### "Out of disk space"
- Ollama models are ~5GB
- Docker images are ~2GB
- Free up space or use external drive

---

## 📝 Quick Reference Commands

```bash
# Start everything
docker compose up -d

# Stop everything
docker compose down

# View logs
docker compose logs -f app

# Restart a service
docker compose restart app

# Check status
docker compose ps

# Pull Ollama models
docker compose exec ollama ollama pull nomic-embed-text
docker compose exec ollama ollama pull llama3.1

# Access Ollama shell
docker compose exec ollama bash
```

---

## 🎓 What Your Coworker Should Know

1. **First startup takes 5-10 minutes** (downloading models)
2. **Subsequent startups take ~10 seconds**
3. **Each person has their own knowledge bases** (unless you share ChromaDB data)
4. **Models run locally** - no API keys or internet needed after setup
5. **Everything is containerized** - won't mess up their system

---

## 📞 Support

If your coworker has issues:
1. Check the troubleshooting section above
2. Run `docker compose logs -f` to see errors
3. Verify Docker Desktop is running
4. Try `docker compose down && docker compose up -d` (restart)

---

## 🚀 Next Steps

After your coworker gets it running:
1. Create a knowledge base
2. Upload some documents
3. Try the chat interface
4. Experiment with RAG strategies (Hybrid, Reranking, Agentic)
5. Connect Claude Desktop via MCP (optional)

Enjoy! 🎉


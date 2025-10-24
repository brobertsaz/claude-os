import { motion } from 'framer-motion';
import { Database, Upload, MessageSquare, Settings, Zap, Code, FileText, BookOpen } from 'lucide-react';

export default function HelpDocs() {
  return (
    <div className="space-y-6 max-w-5xl">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <h1 className="text-3xl font-bold gradient-text mb-2">Code-Forge Documentation</h1>
        <p className="text-light-grey">Everything you need to know about using Code-Forge</p>
      </motion.div>

      {/* Quick Start */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="card"
      >
        <h2 className="text-2xl font-bold text-electric-teal mb-4 flex items-center gap-2">
          <Zap className="w-6 h-6" />
          Quick Start
        </h2>
        <div className="space-y-4 text-light-grey">
          <div className="flex gap-4">
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-electric-teal/20 flex items-center justify-center text-electric-teal font-bold">1</div>
            <div>
              <h3 className="font-semibold text-white mb-1">Create a Knowledge Base</h3>
              <p>Click the <span className="text-electric-teal">+</span> button in the sidebar to create a new KB. Choose the appropriate type for your content.</p>
            </div>
          </div>
          <div className="flex gap-4">
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-electric-teal/20 flex items-center justify-center text-electric-teal font-bold">2</div>
            <div>
              <h3 className="font-semibold text-white mb-1">Upload Documents</h3>
              <p>Go to KB Management tab and drag & drop files or click to browse. Supports text, markdown, PDF, code files, and more.</p>
            </div>
          </div>
          <div className="flex gap-4">
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-electric-teal/20 flex items-center justify-center text-electric-teal font-bold">3</div>
            <div>
              <h3 className="font-semibold text-white mb-1">Start Chatting</h3>
              <p>Switch to the Chat tab and ask questions about your documents. The AI will retrieve relevant context and provide answers.</p>
            </div>
          </div>
        </div>
      </motion.div>

      {/* KB Types */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="card"
      >
        <h2 className="text-2xl font-bold text-electric-teal mb-4 flex items-center gap-2">
          <Database className="w-6 h-6" />
          Knowledge Base Types
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-4 bg-cool-blue/10 rounded-lg border border-electric-teal/20">
            <div className="flex items-center gap-2 mb-2">
              <FileText className="w-5 h-5 text-electric-teal" />
              <h3 className="font-bold text-white">Generic</h3>
            </div>
            <p className="text-sm text-light-grey mb-2">General-purpose knowledge base for mixed content types.</p>
            <p className="text-xs text-light-grey"><strong className="text-electric-teal">Use for:</strong> Random notes, mixed documents, general reference material</p>
          </div>

          <div className="p-4 bg-cool-blue/10 rounded-lg border border-electric-teal/20">
            <div className="flex items-center gap-2 mb-2">
              <Code className="w-5 h-5 text-electric-teal" />
              <h3 className="font-bold text-white">Code</h3>
            </div>
            <p className="text-sm text-light-grey mb-2">Optimized for source code with better chunking and structure preservation.</p>
            <p className="text-xs text-light-grey"><strong className="text-electric-teal">Use for:</strong> Codebases, libraries, API implementations, code examples</p>
          </div>

          <div className="p-4 bg-cool-blue/10 rounded-lg border border-electric-teal/20">
            <div className="flex items-center gap-2 mb-2">
              <BookOpen className="w-5 h-5 text-electric-teal" />
              <h3 className="font-bold text-white">Documentation</h3>
            </div>
            <p className="text-sm text-light-grey mb-2">Optimized for technical documentation with enhanced markdown processing.</p>
            <p className="text-xs text-light-grey"><strong className="text-electric-teal">Use for:</strong> MCP docs, API docs, tutorials, guides, technical specs</p>
          </div>

          <div className="p-4 bg-cool-blue/10 rounded-lg border border-electric-teal/20">
            <div className="flex items-center gap-2 mb-2">
              <Settings className="w-5 h-5 text-electric-teal" />
              <h3 className="font-bold text-white">Agent OS</h3>
            </div>
            <p className="text-sm text-light-grey mb-2">Special type for Agent OS YAML profiles with structured metadata extraction.</p>
            <p className="text-xs text-light-grey"><strong className="text-electric-teal">Use for:</strong> Agent OS configuration files only</p>
          </div>
        </div>
      </motion.div>

      {/* RAG Settings */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="card"
      >
        <h2 className="text-2xl font-bold text-electric-teal mb-4 flex items-center gap-2">
          <Settings className="w-6 h-6" />
          RAG Settings Explained
        </h2>
        <div className="space-y-4">
          <div className="p-4 bg-cool-blue/10 rounded-lg border border-electric-teal/20">
            <h3 className="font-bold text-white mb-2">Hybrid Search (Vector + BM25)</h3>
            <p className="text-sm text-light-grey mb-2">Combines semantic vector search with keyword-based BM25 search for better retrieval.</p>
            <p className="text-xs text-light-grey"><strong className="text-blaze-orange">When to use:</strong> When you need both semantic understanding AND exact keyword matching. Great for technical queries.</p>
          </div>

          <div className="p-4 bg-cool-blue/10 rounded-lg border border-electric-teal/20">
            <h3 className="font-bold text-white mb-2">Reranking</h3>
            <p className="text-sm text-light-grey mb-2">Re-scores retrieved documents using a cross-encoder model for higher accuracy.</p>
            <p className="text-xs text-light-grey"><strong className="text-blaze-orange">When to use:</strong> When you need the most relevant results and can afford slightly slower queries. Improves precision.</p>
          </div>

          <div className="p-4 bg-cool-blue/10 rounded-lg border border-electric-teal/20">
            <h3 className="font-bold text-white mb-2">Agentic RAG</h3>
            <p className="text-sm text-light-grey mb-2">Uses multi-step reasoning with an LLM agent to iteratively refine queries and answers.</p>
            <p className="text-xs text-light-grey"><strong className="text-blaze-orange">When to use:</strong> For complex questions requiring multiple retrieval steps or reasoning. Slower but more intelligent.</p>
          </div>

          <div className="p-4 bg-electric-teal/10 rounded-lg border border-electric-teal/30">
            <p className="text-sm text-white"><strong>💡 Pro Tip:</strong> Start with basic vector search, then enable Hybrid + Rerank for better results. Use Agentic RAG for complex research questions.</p>
          </div>
        </div>
      </motion.div>

      {/* File Upload */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="card"
      >
        <h2 className="text-2xl font-bold text-electric-teal mb-4 flex items-center gap-2">
          <Upload className="w-6 h-6" />
          Supported File Types
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-sm text-light-grey">
          <div className="p-2 bg-cool-blue/10 rounded border border-electric-teal/20 text-center">.txt</div>
          <div className="p-2 bg-cool-blue/10 rounded border border-electric-teal/20 text-center">.md</div>
          <div className="p-2 bg-cool-blue/10 rounded border border-electric-teal/20 text-center">.pdf</div>
          <div className="p-2 bg-cool-blue/10 rounded border border-electric-teal/20 text-center">.py</div>
          <div className="p-2 bg-cool-blue/10 rounded border border-electric-teal/20 text-center">.js</div>
          <div className="p-2 bg-cool-blue/10 rounded border border-electric-teal/20 text-center">.ts</div>
          <div className="p-2 bg-cool-blue/10 rounded border border-electric-teal/20 text-center">.tsx</div>
          <div className="p-2 bg-cool-blue/10 rounded border border-electric-teal/20 text-center">.jsx</div>
          <div className="p-2 bg-cool-blue/10 rounded border border-electric-teal/20 text-center">.json</div>
          <div className="p-2 bg-cool-blue/10 rounded border border-electric-teal/20 text-center">.yaml</div>
          <div className="p-2 bg-cool-blue/10 rounded border border-electric-teal/20 text-center">.html</div>
          <div className="p-2 bg-cool-blue/10 rounded border border-electric-teal/20 text-center">.css</div>
          <div className="p-2 bg-cool-blue/10 rounded border border-electric-teal/20 text-center">.cpp</div>
          <div className="p-2 bg-cool-blue/10 rounded border border-electric-teal/20 text-center">.java</div>
          <div className="p-2 bg-cool-blue/10 rounded border border-electric-teal/20 text-center">.go</div>
          <div className="p-2 bg-cool-blue/10 rounded border border-electric-teal/20 text-center">.rs</div>
        </div>
        <p className="text-sm text-light-grey mt-4">And many more! Code-Forge automatically extracts text from PDFs and processes markdown with enhanced structure preservation.</p>
      </motion.div>

      {/* MCP Integration */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
        className="card"
      >
        <h2 className="text-2xl font-bold text-electric-teal mb-4 flex items-center gap-2">
          <MessageSquare className="w-6 h-6" />
          MCP Integration
        </h2>
        <p className="text-light-grey mb-4">Code-Forge exposes 12 MCP tools for AI agents to interact with your knowledge bases:</p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-sm mb-6">
          <div className="p-3 bg-cool-blue/10 rounded border border-electric-teal/20">
            <code className="text-electric-teal">list_knowledge_bases</code>
          </div>
          <div className="p-3 bg-cool-blue/10 rounded border border-electric-teal/20">
            <code className="text-electric-teal">create_knowledge_base</code>
          </div>
          <div className="p-3 bg-cool-blue/10 rounded border border-electric-teal/20">
            <code className="text-electric-teal">delete_knowledge_base</code>
          </div>
          <div className="p-3 bg-cool-blue/10 rounded border border-electric-teal/20">
            <code className="text-electric-teal">ingest_document</code>
          </div>
          <div className="p-3 bg-cool-blue/10 rounded border border-electric-teal/20">
            <code className="text-electric-teal">ingest_directory</code>
          </div>
          <div className="p-3 bg-cool-blue/10 rounded border border-electric-teal/20">
            <code className="text-electric-teal">query_knowledge_base</code>
          </div>
          <div className="p-3 bg-cool-blue/10 rounded border border-electric-teal/20">
            <code className="text-electric-teal">get_kb_stats</code>
          </div>
          <div className="p-3 bg-cool-blue/10 rounded border border-electric-teal/20">
            <code className="text-electric-teal">get_standards</code>
          </div>
        </div>

        <div className="space-y-4">
          <div className="p-4 bg-electric-teal/10 rounded-lg border border-electric-teal/30">
            <p className="text-sm text-white mb-2"><strong>MCP Endpoint:</strong> <code className="text-electric-teal">http://localhost:8051/mcp</code></p>
          </div>

          <div className="p-4 bg-blaze-orange/10 rounded-lg border border-blaze-orange/30">
            <h3 className="font-bold text-white mb-3 flex items-center gap-2">
              <MessageSquare className="w-5 h-5 text-blaze-orange" />
              Add to Claude Desktop
            </h3>

            <div className="mb-4">
              <p className="text-sm text-white mb-2"><strong>Option 1: Using CLI (Recommended)</strong></p>
              <p className="text-sm text-light-grey mb-3">Run this command in your terminal:</p>
              <div className="bg-deep-night rounded-lg p-4 border border-electric-teal/30">
                <code className="text-electric-teal text-sm">npx @modelcontextprotocol/inspector http://localhost:8051/mcp</code>
              </div>
              <p className="text-xs text-light-grey mt-2">Or add directly to Claude Desktop:</p>
              <div className="bg-deep-night rounded-lg p-4 border border-electric-teal/30 mt-2">
                <code className="text-electric-teal text-sm">claude mcp add code-forge http://localhost:8051/mcp</code>
              </div>
            </div>

            <div className="mb-4">
              <p className="text-sm text-white mb-2"><strong>Option 2: Manual Configuration</strong></p>
              <p className="text-sm text-light-grey mb-3">Edit your Claude Desktop config file:</p>

              <div className="bg-deep-night rounded-lg p-4 border border-blaze-orange/30 mb-3">
                <p className="text-xs text-light-grey mb-2"><strong>macOS:</strong> <code className="text-electric-teal">~/Library/Application Support/Claude/claude_desktop_config.json</code></p>
                <p className="text-xs text-light-grey"><strong>Windows:</strong> <code className="text-electric-teal">%APPDATA%\Claude\claude_desktop_config.json</code></p>
              </div>

              <div className="bg-deep-night rounded-lg p-4 border border-electric-teal/30 overflow-x-auto">
                <pre className="text-xs text-electric-teal">
{`{
  "mcpServers": {
    "code-forge": {
      "url": "http://localhost:8051/mcp"
    }
  }
}`}
                </pre>
              </div>
            </div>

            <p className="text-xs text-light-grey">
              <strong className="text-blaze-orange">Note:</strong> Restart Claude Desktop after adding the configuration. The MCP server must be running (docker-compose up).
            </p>
          </div>
        </div>
      </motion.div>
    </div>
  );
}

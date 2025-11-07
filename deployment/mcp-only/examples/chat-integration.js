/**
 * Example: Integrating Claude OS MCP with a Node.js/Express Chat Application
 *
 * This example shows how to use the MCP server as a knowledge base
 * backend for a chat API.
 */

const express = require('express');
const axios = require('axios');

class ClaudeOSKnowledgeBase {
  constructor(baseUrl = 'http://localhost:8051', apiToken = null) {
    this.baseUrl = baseUrl;
    this.headers = { 'Content-Type': 'application/json' };

    if (apiToken) {
      this.headers['Authorization'] = `Bearer ${apiToken}`;
    }
  }

  /**
   * Make a JSON-RPC call to the MCP server
   */
  async callTool(toolName, arguments, kbSlug = null) {
    // Use KB-specific endpoint if slug provided
    let url = `${this.baseUrl}/mcp`;
    if (kbSlug) {
      url = `${this.baseUrl}/mcp/kb/${kbSlug}`;
    }

    const payload = {
      jsonrpc: '2.0',
      method: 'tools/call',
      params: {
        name: toolName,
        arguments: arguments
      },
      id: 1
    };

    try {
      const response = await axios.post(url, payload, {
        headers: this.headers
      });

      if (response.data.error) {
        throw new Error(`MCP Error: ${JSON.stringify(response.data.error)}`);
      }

      return response.data.result || {};
    } catch (error) {
      throw new Error(`Failed to call MCP: ${error.message}`);
    }
  }

  /**
   * Search a knowledge base for relevant information
   */
  async search(kbName, query, options = {}) {
    const {
      topK = 10,
      useHybrid = false,
      useRerank = false
    } = options;

    const result = await this.callTool('search_knowledge_base', {
      kb_name: kbName,
      query: query,
      top_k: topK,
      use_hybrid: useHybrid,
      use_rerank: useRerank
    });

    return result.results || [];
  }

  /**
   * List all available knowledge bases
   */
  async listKnowledgeBases() {
    const result = await this.callTool('list_knowledge_bases', {});
    return result.knowledge_bases || [];
  }

  /**
   * Get statistics for a knowledge base
   */
  async getKBStats(kbName) {
    return await this.callTool('get_kb_stats', { kb_name: kbName });
  }
}

/**
 * Create an Express.js API for the chat application
 */
function createChatAPI() {
  const app = express();
  app.use(express.json());

  // Initialize MCP client
  const mcp = new ClaudeOSKnowledgeBase(
    process.env.MCP_BASE_URL || 'http://localhost:8051',
    process.env.MCP_API_TOKEN || null
  );

  /**
   * POST /api/chat
   * Ask a question and get a knowledge-based response
   */
  app.post('/api/chat', async (req, res) => {
    try {
      const { question, kb_name, options = {} } = req.body;

      if (!question || !kb_name) {
        return res.status(400).json({
          error: 'Missing required fields: question and kb_name'
        });
      }

      // Search the knowledge base
      const results = await mcp.search(kb_name, question, {
        topK: options.top_k || 5,
        useHybrid: options.use_hybrid !== false, // default true
        useRerank: options.use_rerank !== false  // default true
      });

      if (results.length === 0) {
        return res.json({
          answer: "I couldn't find any relevant information in the knowledge base.",
          sources: []
        });
      }

      // Format the context
      const sources = results.map((result, idx) => ({
        id: idx + 1,
        text: result.text,
        filename: result.metadata?.filename || 'Unknown',
        score: result.score || 0
      }));

      // In a real app, you'd call your LLM here with the context
      // For this example, just return the sources
      res.json({
        answer: `Found ${results.length} relevant results. (In production, this would be processed by an LLM to generate a natural language answer)`,
        sources: sources,
        question: question
      });

    } catch (error) {
      console.error('Chat error:', error);
      res.status(500).json({
        error: error.message
      });
    }
  });

  /**
   * GET /api/knowledge-bases
   * List all available knowledge bases
   */
  app.get('/api/knowledge-bases', async (req, res) => {
    try {
      const kbs = await mcp.listKnowledgeBases();

      res.json({
        knowledge_bases: kbs.map(kb => ({
          name: kb.name,
          slug: kb.slug,
          type: kb.kb_type,
          description: kb.description
        }))
      });

    } catch (error) {
      console.error('Error listing KBs:', error);
      res.status(500).json({
        error: error.message
      });
    }
  });

  /**
   * GET /api/knowledge-bases/:name/stats
   * Get statistics for a specific knowledge base
   */
  app.get('/api/knowledge-bases/:name/stats', async (req, res) => {
    try {
      const stats = await mcp.getKBStats(req.params.name);
      res.json(stats);
    } catch (error) {
      console.error('Error getting stats:', error);
      res.status(500).json({
        error: error.message
      });
    }
  });

  /**
   * GET /health
   * Health check endpoint
   */
  app.get('/health', async (req, res) => {
    try {
      // Try to list KBs to verify MCP connection
      await mcp.listKnowledgeBases();
      res.json({ status: 'ok', mcp_connected: true });
    } catch (error) {
      res.status(503).json({
        status: 'degraded',
        mcp_connected: false,
        error: error.message
      });
    }
  });

  return app;
}

/**
 * Example usage with streaming responses (for real-time chat)
 */
async function streamingChatExample(kbName, question) {
  const mcp = new ClaudeOSKnowledgeBase('http://localhost:8051');

  // 1. Search the knowledge base
  const results = await mcp.search(kbName, question, {
    topK: 5,
    useHybrid: true,
    useRerank: true
  });

  // 2. Build context for LLM
  const context = results
    .map((r, idx) => `[${idx + 1}] ${r.text}`)
    .join('\n\n---\n\n');

  console.log('Context for LLM:');
  console.log(context);

  // 3. In a real app, stream the LLM response
  // using OpenAI SDK, Anthropic SDK, etc.
  /*
  const stream = await openai.chat.completions.create({
    model: 'gpt-4',
    messages: [
      {
        role: 'system',
        content: `You are a helpful assistant. Answer the user's question based on the following context:\n\n${context}`
      },
      {
        role: 'user',
        content: question
      }
    ],
    stream: true
  });

  for await (const chunk of stream) {
    process.stdout.write(chunk.choices[0]?.delta?.content || '');
  }
  */
}

// Run the server if this file is executed directly
if (require.main === module) {
  const app = createChatAPI();
  const PORT = process.env.PORT || 3000;

  app.listen(PORT, () => {
    console.log(`Chat API server running on port ${PORT}`);
    console.log('');
    console.log('Endpoints:');
    console.log(`  POST   http://localhost:${PORT}/api/chat`);
    console.log(`  GET    http://localhost:${PORT}/api/knowledge-bases`);
    console.log(`  GET    http://localhost:${PORT}/api/knowledge-bases/:name/stats`);
    console.log(`  GET    http://localhost:${PORT}/health`);
    console.log('');
    console.log('Example request:');
    console.log(`  curl -X POST http://localhost:${PORT}/api/chat \\`);
    console.log(`    -H "Content-Type: application/json" \\`);
    console.log(`    -d '{"question": "How do I configure auth?", "kb_name": "my-docs"}'`);
  });
}

module.exports = {
  ClaudeOSKnowledgeBase,
  createChatAPI,
  streamingChatExample
};

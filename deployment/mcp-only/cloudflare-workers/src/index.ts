/**
 * Claude OS MCP Server - Cloudflare Workers Implementation
 *
 * This is a BASIC EXAMPLE showing how to implement MCP endpoints
 * on Cloudflare Workers. A production implementation would require
 * all 12 tools and proper error handling.
 */

export interface Env {
  DB: D1Database;          // D1 database binding
  VECTORIZE: VectorizeIndex; // Vectorize binding
  AI: any;                 // Workers AI binding
}

interface MCPRequest {
  jsonrpc: string;
  method: string;
  params?: {
    name?: string;
    arguments?: any;
  };
  id: number;
}

interface MCPResponse {
  jsonrpc: string;
  result?: any;
  error?: {
    code: number;
    message: string;
  };
  id: number;
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    // CORS headers
    const corsHeaders = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    };

    // Handle preflight
    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders });
    }

    // Health check
    if (url.pathname === '/health') {
      return new Response(
        JSON.stringify({ status: 'ok', version: '1.0.0' }),
        {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        }
      );
    }

    // MCP endpoint
    if (url.pathname === '/mcp' && request.method === 'POST') {
      try {
        const body: MCPRequest = await request.json();
        const response = await handleMCPRequest(body, env);

        return new Response(JSON.stringify(response), {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
      } catch (error) {
        return new Response(
          JSON.stringify({
            jsonrpc: '2.0',
            error: {
              code: -32603,
              message: error instanceof Error ? error.message : 'Internal error'
            },
            id: null
          }),
          {
            status: 500,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          }
        );
      }
    }

    return new Response('Not found', { status: 404, headers: corsHeaders });
  },
};

/**
 * Handle MCP JSON-RPC requests
 */
async function handleMCPRequest(request: MCPRequest, env: Env): Promise<MCPResponse> {
  const { method, params, id } = request;

  // Initialize method
  if (method === 'initialize') {
    return {
      jsonrpc: '2.0',
      result: {
        protocolVersion: '2024-11-05',
        serverInfo: {
          name: 'claude-os-mcp',
          version: '1.0.0'
        },
        capabilities: {
          tools: {}
        }
      },
      id
    };
  }

  // List available tools
  if (method === 'tools/list') {
    return {
      jsonrpc: '2.0',
      result: {
        tools: [
          {
            name: 'search_knowledge_base',
            description: 'Search a knowledge base for relevant information',
            inputSchema: {
              type: 'object',
              properties: {
                kb_name: { type: 'string' },
                query: { type: 'string' },
                top_k: { type: 'number' }
              },
              required: ['kb_name', 'query']
            }
          },
          {
            name: 'list_knowledge_bases',
            description: 'List all available knowledge bases',
            inputSchema: {
              type: 'object',
              properties: {}
            }
          }
          // TODO: Add remaining 10 tools
        ]
      },
      id
    };
  }

  // Call a tool
  if (method === 'tools/call') {
    const toolName = params?.name;
    const args = params?.arguments || {};

    let result;

    switch (toolName) {
      case 'search_knowledge_base':
        result = await searchKnowledgeBase(env, args);
        break;

      case 'list_knowledge_bases':
        result = await listKnowledgeBases(env);
        break;

      // TODO: Implement remaining tools:
      // - list_knowledge_bases_by_type
      // - create_knowledge_base
      // - get_kb_stats
      // - list_documents
      // - ingest_agent_os_profile
      // - get_agent_os_stats
      // - get_standards
      // - get_workflows
      // - get_specs
      // - get_product_context

      default:
        return {
          jsonrpc: '2.0',
          error: {
            code: -32601,
            message: `Unknown tool: ${toolName}`
          },
          id
        };
    }

    return {
      jsonrpc: '2.0',
      result,
      id
    };
  }

  return {
    jsonrpc: '2.0',
    error: {
      code: -32601,
      message: `Unknown method: ${method}`
    },
    id
  };
}

/**
 * Search knowledge base using vector similarity
 */
async function searchKnowledgeBase(
  env: Env,
  args: { kb_name: string; query: string; top_k?: number }
): Promise<any> {
  const { kb_name, query, top_k = 10 } = args;

  // 1. Get KB ID
  const kb = await env.DB.prepare(
    'SELECT id, slug FROM knowledge_bases WHERE name = ? OR slug = ?'
  ).bind(kb_name, kb_name).first();

  if (!kb) {
    throw new Error(`Knowledge base not found: ${kb_name}`);
  }

  // 2. Generate query embedding using Workers AI
  const embeddingResponse: any = await env.AI.run('@cf/baai/bge-base-en-v1.5', {
    text: query
  });

  const queryEmbedding = embeddingResponse.data[0];

  // 3. Search vectors using Vectorize
  const matches = await env.VECTORIZE.query(queryEmbedding, {
    topK: top_k,
    returnMetadata: true,
    filter: { kb_id: kb.id }  // Filter by knowledge base
  });

  // 4. Fetch full document content from D1
  const documentIds = matches.matches.map(m => m.id);

  if (documentIds.length === 0) {
    return {
      results: [],
      kb_name,
      query,
      count: 0
    };
  }

  const placeholders = documentIds.map(() => '?').join(',');
  const documents = await env.DB.prepare(
    `SELECT id, content, metadata FROM documents WHERE id IN (${placeholders})`
  ).bind(...documentIds).all();

  // 5. Combine results
  const results = matches.matches.map((match, idx) => {
    const doc = documents.results.find(d => d.id === match.id);

    return {
      text: doc?.content || '',
      metadata: doc?.metadata ? JSON.parse(doc.metadata) : {},
      score: match.score,
      distance: 1 - match.score
    };
  });

  return {
    results,
    kb_name,
    query,
    count: results.length,
    search_mode: 'vector'
  };
}

/**
 * List all knowledge bases
 */
async function listKnowledgeBases(env: Env): Promise<any> {
  const result = await env.DB.prepare(
    'SELECT id, name, slug, kb_type, description, created_at FROM knowledge_bases ORDER BY created_at DESC'
  ).all();

  return {
    knowledge_bases: result.results.map(kb => ({
      id: kb.id,
      name: kb.name,
      slug: kb.slug,
      kb_type: kb.kb_type,
      description: kb.description,
      created_at: kb.created_at
    })),
    count: result.results.length
  };
}

/**
 * Additional helper functions would go here:
 * - getKBStats()
 * - listDocuments()
 * - createKnowledgeBase()
 * - etc.
 */

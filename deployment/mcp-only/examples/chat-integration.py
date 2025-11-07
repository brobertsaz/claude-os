"""
Example: Integrating Claude OS MCP with a Chat Application

This example shows how to use the MCP server as a knowledge base
backend for a chat application.
"""

import requests
from typing import List, Dict, Optional


class ClaudeOSKnowledgeBase:
    """Client for Claude OS MCP Server"""

    def __init__(
        self,
        base_url: str = "http://localhost:8051",
        api_token: Optional[str] = None
    ):
        self.base_url = base_url
        self.headers = {"Content-Type": "application/json"}

        if api_token:
            self.headers["Authorization"] = f"Bearer {api_token}"

    def _call_tool(
        self,
        tool_name: str,
        arguments: Dict,
        kb_slug: Optional[str] = None
    ) -> Dict:
        """Make a JSON-RPC call to the MCP server"""

        # Use KB-specific endpoint if slug provided
        url = f"{self.base_url}/mcp"
        if kb_slug:
            url = f"{self.base_url}/mcp/kb/{kb_slug}"

        payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            },
            "id": 1
        }

        response = requests.post(url, json=payload, headers=self.headers)
        response.raise_for_status()

        result = response.json()
        if "error" in result:
            raise Exception(f"MCP Error: {result['error']}")

        return result.get("result", {})

    def search(
        self,
        kb_name: str,
        query: str,
        top_k: int = 10,
        use_hybrid: bool = False,
        use_rerank: bool = False
    ) -> List[Dict]:
        """
        Search a knowledge base for relevant information

        Args:
            kb_name: Name of the knowledge base to search
            query: User's question or search query
            top_k: Number of results to return
            use_hybrid: Enable hybrid search (vector + keyword)
            use_rerank: Enable reranking for better results

        Returns:
            List of relevant document chunks with metadata
        """
        result = self._call_tool(
            "search_knowledge_base",
            {
                "kb_name": kb_name,
                "query": query,
                "top_k": top_k,
                "use_hybrid": use_hybrid,
                "use_rerank": use_rerank
            }
        )

        # Parse the results
        if isinstance(result, dict) and "results" in result:
            return result["results"]
        return []

    def list_knowledge_bases(self) -> List[Dict]:
        """List all available knowledge bases"""
        result = self._call_tool("list_knowledge_bases", {})
        return result.get("knowledge_bases", [])

    def get_kb_stats(self, kb_name: str) -> Dict:
        """Get statistics for a knowledge base"""
        result = self._call_tool("get_kb_stats", {"kb_name": kb_name})
        return result


class ChatWithKnowledge:
    """
    Example chat application that uses Claude OS knowledge bases
    """

    def __init__(self, mcp_client: ClaudeOSKnowledgeBase):
        self.mcp = mcp_client

    def answer_question(
        self,
        question: str,
        kb_name: str,
        use_hybrid: bool = True,
        use_rerank: bool = True
    ) -> str:
        """
        Answer a user question using the knowledge base

        This is a simple example - in a real app, you'd:
        1. Search the knowledge base
        2. Pass results + question to your LLM
        3. Generate a response grounded in the retrieved docs
        """

        # 1. Search the knowledge base
        results = self.mcp.search(
            kb_name=kb_name,
            query=question,
            top_k=5,
            use_hybrid=use_hybrid,
            use_rerank=use_rerank
        )

        if not results:
            return "I couldn't find any relevant information in the knowledge base."

        # 2. Format the context from search results
        context_parts = []
        for idx, result in enumerate(results, 1):
            text = result.get("text", "")
            metadata = result.get("metadata", {})
            filename = metadata.get("filename", "Unknown")
            score = result.get("score", 0)

            context_parts.append(
                f"[{idx}] {filename} (relevance: {score:.2f})\n{text}\n"
            )

        context = "\n---\n".join(context_parts)

        # 3. In a real app, you'd call your LLM here
        # For this example, just return the context
        response = f"""Based on the knowledge base, here's what I found:

{context}

Question: {question}

(In a production app, this would be processed by an LLM to generate a natural language answer)
"""

        return response

    def list_available_topics(self) -> str:
        """List all available knowledge bases"""
        kbs = self.mcp.list_knowledge_bases()

        if not kbs:
            return "No knowledge bases available."

        response = "Available topics:\n\n"
        for kb in kbs:
            name = kb.get("name", "Unknown")
            description = kb.get("description", "No description")
            kb_type = kb.get("kb_type", "generic")

            response += f"- **{name}** ({kb_type})\n  {description}\n\n"

        return response


# Example usage
if __name__ == "__main__":
    # Initialize the MCP client
    mcp = ClaudeOSKnowledgeBase(
        base_url="http://localhost:8051",
        # api_token="your-jwt-token-here"  # Uncomment if auth enabled
    )

    # Create chat interface
    chat = ChatWithKnowledge(mcp)

    # Example 1: List available knowledge bases
    print("=" * 60)
    print("AVAILABLE KNOWLEDGE BASES")
    print("=" * 60)
    print(chat.list_available_topics())
    print()

    # Example 2: Ask a question
    print("=" * 60)
    print("ASKING A QUESTION")
    print("=" * 60)

    question = "How do I configure authentication?"
    kb_name = "my-docs"  # Change to your actual KB name

    print(f"Question: {question}")
    print(f"Knowledge Base: {kb_name}")
    print()

    try:
        answer = chat.answer_question(
            question=question,
            kb_name=kb_name,
            use_hybrid=True,
            use_rerank=True
        )
        print(answer)
    except Exception as e:
        print(f"Error: {e}")

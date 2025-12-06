"""
Tests for the Claude Code MCP Server (claude_code_mcp.py).

This is the critical bridge between Claude Code and the Claude OS REST API.
These tests ensure the MCP protocol is correctly implemented.
"""

import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestMCPServerTools:
    """Test the MCP server tool definitions."""

    @pytest.fixture
    def mock_server(self):
        """Create a mock MCP server for testing."""
        with patch.dict(os.environ, {"CLAUDE_OS_API": "http://localhost:8051"}):
            from mcp_server.claude_code_mcp import server, list_tools
            return server, list_tools

    @pytest.mark.asyncio
    async def test_list_tools_returns_all_tools(self, mock_server):
        """Test that list_tools returns all expected tools."""
        server, list_tools_func = mock_server
        tools = await list_tools_func()

        # Should have all the expected tools
        tool_names = [t.name for t in tools]

        expected_tools = [
            "list_knowledge_bases",
            "create_knowledge_base",
            "search_knowledge_base",
            "get_kb_stats",
            "list_documents",
            "delete_knowledge_base",
            "list_projects",
            "create_project",
            "get_project",
            "index_structural",
            "index_semantic",
            "upload_document",
            "delete_document",
            "get_ollama_models",
            "health_check"
        ]

        for expected in expected_tools:
            assert expected in tool_names, f"Missing tool: {expected}"

    @pytest.mark.asyncio
    async def test_list_tools_have_valid_schemas(self, mock_server):
        """Test that all tools have valid input schemas."""
        server, list_tools_func = mock_server
        tools = await list_tools_func()

        for tool in tools:
            assert tool.inputSchema is not None, f"Tool {tool.name} has no schema"
            assert "type" in tool.inputSchema, f"Tool {tool.name} schema missing 'type'"
            assert tool.inputSchema["type"] == "object", f"Tool {tool.name} schema should be object"
            assert "properties" in tool.inputSchema, f"Tool {tool.name} schema missing 'properties'"
            assert "required" in tool.inputSchema, f"Tool {tool.name} schema missing 'required'"


class TestMCPServerAPIIntegration:
    """Test the MCP server's integration with the REST API."""

    @pytest.fixture
    def mock_httpx(self):
        """Mock httpx for API calls."""
        with patch("mcp_server.claude_code_mcp.httpx.AsyncClient") as mock:
            yield mock

    @pytest.mark.asyncio
    async def test_api_url_builder(self):
        """Test the API URL builder function."""
        with patch.dict(os.environ, {"CLAUDE_OS_API": "http://test:9000"}):
            # Re-import to pick up new env var
            import importlib
            import mcp_server.claude_code_mcp as mcp_module
            importlib.reload(mcp_module)

            url = mcp_module.api_url("/api/kb")
            assert url == "http://test:9000/api/kb"

    @pytest.mark.asyncio
    async def test_list_knowledge_bases_calls_correct_endpoint(self, mock_httpx):
        """Test that list_knowledge_bases calls the correct API endpoint."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"knowledge_bases": []}
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_httpx.return_value = mock_client

        from mcp_server.claude_code_mcp import _execute_tool
        result = await _execute_tool("list_knowledge_bases", {})

        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert "/api/kb" in str(call_args)

    @pytest.mark.asyncio
    async def test_search_knowledge_base_calls_correct_endpoint(self, mock_httpx):
        """Test that search_knowledge_base calls the correct API endpoint."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"answer": "test", "sources": []}
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_httpx.return_value = mock_client

        from mcp_server.claude_code_mcp import _execute_tool
        result = await _execute_tool("search_knowledge_base", {
            "kb_name": "test_kb",
            "query": "test query"
        })

        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert "/api/kb/test_kb/chat" in str(call_args)

    @pytest.mark.asyncio
    async def test_create_knowledge_base_sends_correct_payload(self, mock_httpx):
        """Test that create_knowledge_base sends the correct payload."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": 1, "name": "new_kb"}
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_httpx.return_value = mock_client

        from mcp_server.claude_code_mcp import _execute_tool
        result = await _execute_tool("create_knowledge_base", {
            "name": "new_kb",
            "kb_type": "documentation",
            "description": "Test KB"
        })

        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        # Check the JSON payload
        assert call_args.kwargs.get("json", {}).get("name") == "new_kb"


class TestMCPServerErrorHandling:
    """Test error handling in the MCP server."""

    @pytest.mark.asyncio
    async def test_unknown_tool_returns_error(self):
        """Test that unknown tools return an error."""
        from mcp_server.claude_code_mcp import _execute_tool
        result = await _execute_tool("nonexistent_tool", {})

        assert "error" in result
        assert "Unknown tool" in result["error"]

    @pytest.mark.asyncio
    async def test_connection_error_handled_gracefully(self):
        """Test that connection errors are handled gracefully."""
        import httpx

        with patch("mcp_server.claude_code_mcp.httpx.AsyncClient") as mock_httpx:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(side_effect=httpx.ConnectError("Connection refused"))
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_httpx.return_value = mock_client

            from mcp_server.claude_code_mcp import call_tool
            result = await call_tool("list_knowledge_bases", {})

            # Should return a TextContent with error message
            assert len(result) == 1
            text = result[0].text
            error_data = json.loads(text)
            assert "error" in error_data
            assert "Cannot connect" in error_data["error"] or "Connection" in str(error_data)

    @pytest.mark.asyncio
    async def test_http_error_handled_gracefully(self):
        """Test that HTTP errors are handled gracefully."""
        import httpx

        with patch("mcp_server.claude_code_mcp.httpx.AsyncClient") as mock_httpx:
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.text = "Internal Server Error"

            mock_client = AsyncMock()
            mock_client.get = AsyncMock(side_effect=httpx.HTTPStatusError(
                "Server error",
                request=MagicMock(),
                response=mock_response
            ))
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_httpx.return_value = mock_client

            from mcp_server.claude_code_mcp import call_tool
            result = await call_tool("list_knowledge_bases", {})

            # Should return a TextContent with error message
            assert len(result) == 1
            text = result[0].text
            error_data = json.loads(text)
            assert "error" in error_data


class TestMCPServerHealthCheck:
    """Test the health check functionality."""

    @pytest.mark.asyncio
    async def test_health_check_success(self):
        """Test health check when server is healthy."""
        with patch("mcp_server.claude_code_mcp.api_get") as mock_get:
            mock_get.return_value = {"knowledge_bases": [{"id": 1}, {"id": 2}]}

            from mcp_server.claude_code_mcp import _execute_tool
            result = await _execute_tool("health_check", {})

            assert result["status"] == "healthy"
            assert result["kb_count"] == 2

    @pytest.mark.asyncio
    async def test_health_check_failure(self):
        """Test health check when server is unhealthy."""
        with patch("mcp_server.claude_code_mcp.api_get") as mock_get:
            mock_get.side_effect = Exception("Connection failed")

            from mcp_server.claude_code_mcp import _execute_tool
            result = await _execute_tool("health_check", {})

            assert result["status"] == "unhealthy"
            assert "error" in result


class TestMCPServerDocumentOperations:
    """Test document-related operations."""

    @pytest.fixture
    def mock_httpx(self):
        """Mock httpx for API calls."""
        with patch("mcp_server.claude_code_mcp.httpx.AsyncClient") as mock:
            yield mock

    @pytest.mark.asyncio
    async def test_upload_document_sends_correct_payload(self, mock_httpx):
        """Test that upload_document sends the correct payload."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"success": True}
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_httpx.return_value = mock_client

        from mcp_server.claude_code_mcp import _execute_tool
        result = await _execute_tool("upload_document", {
            "kb_name": "test_kb",
            "content": "# Test Document\n\nThis is a test.",
            "filename": "test.md",
            "title": "Test Document",
            "tags": ["test", "example"]
        })

        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        payload = call_args.kwargs.get("json", {})

        assert payload.get("content") == "# Test Document\n\nThis is a test."
        assert payload.get("filename") == "test.md"
        assert payload.get("metadata", {}).get("title") == "Test Document"

    @pytest.mark.asyncio
    async def test_delete_document_calls_correct_endpoint(self, mock_httpx):
        """Test that delete_document calls the correct endpoint."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"success": True}
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.delete = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_httpx.return_value = mock_client

        from mcp_server.claude_code_mcp import _execute_tool
        result = await _execute_tool("delete_document", {
            "kb_name": "test_kb",
            "filename": "old_doc.md"
        })

        mock_client.delete.assert_called_once()
        call_args = mock_client.delete.call_args
        assert "/api/kb/test_kb/documents/old_doc.md" in str(call_args)


class TestMCPServerIndexingOperations:
    """Test indexing-related operations."""

    @pytest.fixture
    def mock_httpx(self):
        """Mock httpx for API calls."""
        with patch("mcp_server.claude_code_mcp.httpx.AsyncClient") as mock:
            yield mock

    @pytest.mark.asyncio
    async def test_index_structural_sends_path(self, mock_httpx):
        """Test that index_structural sends the correct path."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"indexed": 50}
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_httpx.return_value = mock_client

        from mcp_server.claude_code_mcp import _execute_tool
        result = await _execute_tool("index_structural", {
            "kb_name": "code_kb",
            "path": "/path/to/project"
        })

        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        payload = call_args.kwargs.get("json", {})
        assert payload.get("path") == "/path/to/project"

    @pytest.mark.asyncio
    async def test_index_semantic_calls_correct_endpoint(self, mock_httpx):
        """Test that index_semantic calls the correct endpoint."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"embedded": 100}
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_httpx.return_value = mock_client

        from mcp_server.claude_code_mcp import _execute_tool
        result = await _execute_tool("index_semantic", {
            "kb_name": "docs_kb"
        })

        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert "/api/kb/docs_kb/index-semantic" in str(call_args)

"""
Tests for FastAPI endpoints.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.api
class TestKnowledgeBaseAPI:
    """Test knowledge base API endpoints."""
    
    def test_list_knowledge_bases(self, api_client, sample_kb):
        """Test listing knowledge bases."""
        response = api_client.get("/api/kb")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert any(kb["name"] == sample_kb["name"] for kb in data)
    
    def test_create_knowledge_base(self, api_client, clean_db):
        """Test creating a knowledge base."""
        response = api_client.post(
            "/api/kb",
            json={
                "name": "new_test_kb",
                "kb_type": "GENERIC",
                "description": "Test KB"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "new_test_kb"
    
    def test_get_kb_stats(self, api_client, sample_kb):
        """Test getting KB statistics."""
        response = api_client.get(f"/api/kb/{sample_kb['name']}/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert "document_count" in data
        assert "chunk_count" in data
    
    def test_list_documents(self, api_client, sample_kb, sample_documents):
        """Test listing documents in a KB."""
        response = api_client.get(f"/api/kb/{sample_kb['name']}/documents")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == len(sample_documents)
    
    def test_delete_knowledge_base(self, api_client, clean_db):
        """Test deleting a knowledge base."""
        # Create a KB first
        create_response = api_client.post(
            "/api/kb",
            json={
                "name": "kb_to_delete",
                "kb_type": "GENERIC",
                "description": "Will be deleted"
            }
        )
        assert create_response.status_code == 200
        
        # Delete it
        delete_response = api_client.delete("/api/kb/kb_to_delete")
        assert delete_response.status_code == 200
        
        # Verify it's gone
        list_response = api_client.get("/api/kb")
        data = list_response.json()
        assert not any(kb["name"] == "kb_to_delete" for kb in data)


@pytest.mark.api
@pytest.mark.rag
class TestChatAPI:
    """Test chat/query API endpoints."""
    
    def test_chat_endpoint(self, api_client, sample_kb, sample_documents):
        """Test the chat endpoint."""
        response = api_client.post(
            f"/api/kb/{sample_kb['name']}/chat",
            json={
                "question": "test question",
                "strategy": "base"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert "sources" in data
    
    def test_chat_with_empty_kb(self, api_client, sample_kb, clean_db):
        """Test chat with empty knowledge base."""
        response = api_client.post(
            f"/api/kb/{sample_kb['name']}/chat",
            json={
                "question": "test question",
                "strategy": "base"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["answer"] == "Empty Response"
    
    def test_chat_invalid_kb(self, api_client):
        """Test chat with non-existent KB."""
        response = api_client.post(
            "/api/kb/nonexistent_kb/chat",
            json={
                "question": "test question",
                "strategy": "base"
            }
        )
        
        assert response.status_code in [404, 500]


@pytest.mark.api
class TestHealthAPI:
    """Test health check endpoints."""
    
    def test_health_endpoint(self, api_client):
        """Test the health check endpoint."""
        response = api_client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "database" in data
        assert "ollama" in data


@pytest.mark.api
class TestDocumentUploadAPI:
    """Test document upload endpoints."""
    
    def test_upload_text_file(self, api_client, sample_kb, sample_text_file):
        """Test uploading a text file."""
        with open(sample_text_file, "rb") as f:
            response = api_client.post(
                f"/api/kb/{sample_kb['name']}/upload",
                files={"file": ("test.txt", f, "text/plain")}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_upload_invalid_file_type(self, api_client, sample_kb, tmp_path):
        """Test uploading an invalid file type."""
        invalid_file = tmp_path / "test.xyz"
        invalid_file.write_text("invalid content")
        
        with open(invalid_file, "rb") as f:
            response = api_client.post(
                f"/api/kb/{sample_kb['name']}/upload",
                files={"file": ("test.xyz", f, "application/octet-stream")}
            )
        
        # Should either reject or handle gracefully
        assert response.status_code in [200, 400, 415]

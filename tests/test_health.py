"""
Tests for health check functionality.
"""

import pytest
from unittest.mock import patch, MagicMock

from app.core.health import (
    check_ollama_health,
    check_sqlite_health,
    wait_for_services
)


@pytest.mark.unit
class TestOllamaHealth:
    """Test Ollama health check functionality."""

    @patch('app.core.health.requests.get')
    def test_ollama_healthy(self, mock_get):
        """Test Ollama health check when service is healthy."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [
                {"name": "llama3.1:latest"},
                {"name": "nomic-embed-text"}
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = check_ollama_health()

        assert result["status"] == "healthy"
        assert "models" in result
        assert len(result["models"]) == 2
        assert "llama3.1:latest" in result["models"]
        assert "nomic-embed-text" in result["models"]
        assert result["url"] == "http://localhost:11434"

    @patch('app.core.health.requests.get')
    def test_ollama_unhealthy_connection_error(self, mock_get):
        """Test Ollama health check with connection error."""
        # Mock connection error
        mock_get.side_effect = Exception("Connection refused")

        result = check_ollama_health()

        assert result["status"] == "unhealthy"
        assert "error" in result
        assert "Connection refused" in result["error"]
        assert result["url"] == "http://localhost:11434"

    @patch('app.core.health.requests.get')
    def test_ollama_unhealthy_timeout(self, mock_get):
        """Test Ollama health check with timeout."""
        # Mock timeout error
        import requests
        mock_get.side_effect = requests.exceptions.Timeout("Request timed out")

        result = check_ollama_health()

        assert result["status"] == "unhealthy"
        assert "error" in result
        assert "Request timed out" in result["error"]
        assert result["url"] == "http://localhost:11434"

    @patch('app.core.health.requests.get')
    def test_ollama_unhealthy_connection_refused(self, mock_get):
        """Test Ollama health check with connection refused."""
        # Mock connection refused error
        import requests
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection refused")

        result = check_ollama_health()

        assert result["status"] == "unhealthy"
        assert "error" in result
        assert "Connection refused" in result["error"]
        assert result["url"] == "http://localhost:11434"

    @patch('app.core.health.requests.get')
    def test_ollama_unhealthy_http_error(self, mock_get):
        """Test Ollama health check with HTTP error."""
        # Mock HTTP error
        import requests
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("500 Server Error")
        mock_get.return_value = mock_response

        result = check_ollama_health()

        assert result["status"] == "unhealthy"
        assert "error" in result
        assert "500 Server Error" in result["error"]
        assert result["url"] == "http://localhost:11434"

    @patch('app.core.health.requests.get')
    def test_ollama_empty_models_list(self, mock_get):
        """Test Ollama health check with empty models list."""
        # Mock response with no models
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"models": []}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = check_ollama_health()

        assert result["status"] == "healthy"
        assert "models" in result
        assert len(result["models"]) == 0

    @patch('app.core.health.requests.get')
    def test_ollama_malformed_response(self, mock_get):
        """Test Ollama health check with malformed response."""
        # Mock malformed JSON response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("No JSON object could be decoded")
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = check_ollama_health()

        assert result["status"] == "unhealthy"
        assert "error" in result
        assert "No JSON object could be decoded" in result["error"]
        assert result["url"] == "http://localhost:11434"


@pytest.mark.unit
class TestSQLiteHealth:
    """Test SQLite health check functionality."""

    @patch('app.core.health.get_sqlite_manager')
    def test_sqlite_healthy(self, mock_get_db):
        """Test SQLite health check when service is healthy."""
        # Mock successful database connection
        mock_db = MagicMock()
        mock_db.list_collections.return_value = [
            {"name": "kb1"},
            {"name": "kb2"}
        ]
        mock_get_db.return_value = mock_db

        result = check_sqlite_health()

        assert result["status"] == "healthy"
        assert result["collections"] == 2

    @patch('app.core.health.get_sqlite_manager')
    def test_sqlite_unhealthy(self, mock_get_db):
        """Test SQLite health check when service is unhealthy."""
        # Mock database connection error
        mock_get_db.side_effect = Exception("Connection failed")

        result = check_sqlite_health()

        assert result["status"] == "unhealthy"
        assert "error" in result
        assert "Connection refused" in result["error"]

    @patch('app.core.health.get_sqlite_manager')
    def test_sqlite_empty_database(self, mock_get_db):
        """Test SQLite health check with empty database."""
        # Mock empty database
        mock_db = MagicMock()
        mock_db.list_collections.return_value = []
        mock_get_db.return_value = mock_db

        result = check_sqlite_health()

        assert result["status"] == "healthy"
        assert result["collections"] == 0

    @patch('app.core.health.get_sqlite_manager')
    def test_sqlite_list_collections_error(self, mock_get_db):
        """Test SQLite health check when list_collections fails."""
        # Mock list_collections error
        mock_db = MagicMock()
        mock_db.list_collections.side_effect = Exception("Query failed")
        mock_get_db.return_value = mock_db

        result = check_sqlite_health()

        assert result["status"] == "unhealthy"
        assert "error" in result
        assert "Query failed" in result["error"]


@pytest.mark.unit
class TestWaitForServices:
    """Test wait_for_services functionality."""

    @patch('app.core.health.check_ollama_health')
    @patch('app.core.health.check_sqlite_health')
    @patch('app.core.health.time.sleep')
    def test_wait_for_services_immediate_success(self, mock_sleep, mock_pg_check, mock_ollama_check):
        """Test waiting for services when they're immediately healthy."""
        # Mock healthy services
        mock_ollama_check.return_value = {"status": "healthy"}
        mock_pg_check.return_value = {"status": "healthy"}

        result = wait_for_services(max_retries=3, delay=0.1)

        assert result is True
        # Should not need to sleep
        mock_sleep.assert_not_called()
        # Should check services once
        mock_ollama_check.assert_called_once()
        mock_pg_check.assert_called_once()

    @patch('app.core.health.check_ollama_health')
    @patch('app.core.health.check_sqlite_health')
    @patch('app.core.health.time.sleep')
    def test_wait_for_services_eventual_success(self, mock_sleep, mock_pg_check, mock_ollama_check):
        """Test waiting for services that become healthy after retries."""
        # Mock services that fail first, then succeed
        mock_ollama_check.side_effect = [
            {"status": "unhealthy"},
            {"status": "unhealthy"},
            {"status": "healthy"}
        ]
        mock_pg_check.return_value = {"status": "healthy"}

        result = wait_for_services(max_retries=3, delay=0.1)

        assert result is True
        # Should sleep between retries
        assert mock_sleep.call_count == 2  # After first and second attempts
        # Should check services multiple times
        assert mock_ollama_check.call_count == 3
        assert mock_pg_check.call_count == 3

    @patch('app.core.health.check_ollama_health')
    @patch('app.core.health.check_sqlite_health')
    @patch('app.core.health.time.sleep')
    def test_wait_for_services_timeout(self, mock_sleep, mock_pg_check, mock_ollama_check):
        """Test waiting for services that never become healthy."""
        # Mock services that always fail
        mock_ollama_check.return_value = {"status": "unhealthy"}
        mock_pg_check.return_value = {"status": "unhealthy"}

        result = wait_for_services(max_retries=3, delay=0.1)

        assert result is False
        # Should sleep between retries
        assert mock_sleep.call_count == 2  # After first and second attempts
        # Should check services max_retries times
        assert mock_ollama_check.call_count == 3
        assert mock_pg_check.call_count == 3

    @patch('app.core.health.check_ollama_health')
    @patch('app.core.health.check_sqlite_health')
    @patch('app.core.health.time.sleep')
    def test_wait_for_services_partial_failure(self, mock_sleep, mock_pg_check, mock_ollama_check):
        """Test waiting when one service is always unhealthy."""
        # Mock Ollama always fails, SQLite succeeds
        mock_ollama_check.return_value = {"status": "unhealthy"}
        mock_pg_check.return_value = {"status": "healthy"}

        result = wait_for_services(max_retries=3, delay=0.1)

        assert result is False
        # Should still check both services each time
        assert mock_ollama_check.call_count == 3
        assert mock_pg_check.call_count == 3

    @patch('app.core.health.check_ollama_health')
    @patch('app.core.health.check_sqlite_health')
    @patch('app.core.health.time.sleep')
    def test_wait_for_services_default_parameters(self, mock_sleep, mock_pg_check, mock_ollama_check):
        """Test wait_for_services with default parameters."""
        # Mock healthy services
        mock_ollama_check.return_value = {"status": "healthy"}
        mock_pg_check.return_value = {"status": "healthy"}

        result = wait_for_services()

        assert result is True
        # Should use default parameters
        mock_ollama_check.call_count == 30  # Default max_retries
        mock_pg_check.call_count == 30
        # Should not sleep with immediate success
        mock_sleep.assert_not_called()

    @patch('app.core.health.check_ollama_health')
    @patch('app.core.health.check_sqlite_health')
    @patch('app.core.health.time.sleep')
    def test_wait_for_services_logging(self, mock_sleep, mock_pg_check, mock_ollama_check):
        """Test that wait_for_services logs progress."""
        # Mock services that fail then succeed
        mock_ollama_check.side_effect = [
            {"status": "unhealthy"},
            {"status": "healthy"}
        ]
        mock_pg_check.return_value = {"status": "healthy"}

        with patch('app.core.health.logger.info') as mock_logger:
            wait_for_services(max_retries=2, delay=0.1)

            # Should log progress
            assert mock_logger.call_count >= 1

            # Check that log messages contain expected info
            log_calls = [call[0][0] for call in mock_logger.call_args_list]
            log_messages = " ".join(log_calls)

            assert "Waiting for services" in log_messages
            assert "Attempt 1/2" in log_messages
            assert "Ollama=unhealthy" in log_messages
            assert "SQLite=healthy" in log_messages
            assert "All services healthy" in log_messages

    @patch('app.core.health.check_ollama_health')
    @patch('app.core.health.check_sqlite_health')
    @patch('app.core.health.time.sleep')
    def test_wait_for_services_error_during_check(self, mock_sleep, mock_pg_check, mock_ollama_check):
        """Test wait_for_services when health check raises exception."""
        # Mock health check that raises exception
        mock_ollama_check.side_effect = Exception("Health check failed")
        mock_pg_check.return_value = {"status": "healthy"}

        result = wait_for_services(max_retries=2, delay=0.1)

        # Should handle exception gracefully and return False
        assert result is False
        # Should still attempt all retries
        assert mock_ollama_check.call_count == 2

    @patch('app.core.health.check_ollama_health')
    @patch('app.core.health.check_sqlite_health')
    @patch('app.core.health.time.sleep')
    def test_wait_for_services_custom_delay(self, mock_sleep, mock_pg_check, mock_ollama_check):
        """Test wait_for_services with custom delay."""
        # Mock services that need retries
        mock_ollama_check.side_effect = [
            {"status": "unhealthy"},
            {"status": "healthy"}
        ]
        mock_pg_check.return_value = {"status": "healthy"}

        result = wait_for_services(max_retries=2, delay=0.5)

        assert result is True
        # Should use custom delay
        mock_sleep.assert_called_once_with(0.5)

    @patch('app.core.health.check_ollama_health')
    @patch('app.core.health.check_sqlite_health')
    @patch('app.core.health.time.sleep')
    def test_wait_for_services_custom_retries(self, mock_sleep, mock_pg_check, mock_ollama_check):
        """Test wait_for_services with custom retry count."""
        # Mock services that need all retries
        mock_ollama_check.side_effect = [
            {"status": "unhealthy"},
            {"status": "unhealthy"},
            {"status": "unhealthy"},
            {"status": "healthy"}
        ]
        mock_pg_check.return_value = {"status": "healthy"}

        result = wait_for_services(max_retries=4, delay=0.1)

        assert result is True
        # Should use custom retry count
        assert mock_ollama_check.call_count == 4
        assert mock_pg_check.call_count == 4
        assert mock_sleep.call_count == 3


@pytest.mark.integration
class TestHealthIntegration:
    """Integration tests for health checks."""

    @patch('app.core.health.requests.get')
    def test_real_ollama_check_structure(self, mock_get):
        """Test that Ollama check has correct structure."""
        # Mock realistic response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [
                {
                    "name": "llama3.1:latest",
                    "modified_at": "2023-01-01T00:00:00Z",
                    "size": 4000000000
                },
                {
                    "name": "nomic-embed-text",
                    "modified_at": "2023-01-01T00:00:00Z",
                    "size": 100000000
                }
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = check_ollama_health()

        # Check response structure
        assert "status" in result
        assert "models" in result
        assert "url" in result
        assert isinstance(result["models"], list)
        assert len(result["models"]) == 2

        # Check model structure
        model = result["models"][0]
        assert "name" in model
        assert isinstance(model["name"], str)

    @patch('app.core.health.get_sqlite_manager')
    def test_real_sqlite_check_structure(self, mock_get_db):
        """Test that SQLite check has correct structure."""
        # Mock realistic database
        mock_db = MagicMock()
        mock_db.list_collections.return_value = [
            {"name": "kb1", "type": "generic"},
            {"name": "kb2", "type": "code"},
            {"name": "kb3", "type": "documentation"}
        ]
        mock_get_db.return_value = mock_db

        result = check_sqlite_health()

        # Check response structure
        assert "status" in result
        assert "collections" in result
        assert isinstance(result["collections"], int)
        assert result["collections"] == 3

    def test_health_check_error_handling(self):
        """Test that health checks handle errors gracefully."""
        # Test with invalid Ollama URL
        with patch('app.core.health.Config.OLLAMA_HOST', 'http://invalid-host:99999'):
            result = check_ollama_health()

            # Should handle error gracefully
            assert result["status"] == "unhealthy"
            assert "error" in result

    def test_health_check_timeout_configuration(self):
        """Test that health checks respect timeout configuration."""
        with patch('app.core.health.requests.get') as mock_get:
            # Mock timeout
            import requests
            mock_get.side_effect = requests.exceptions.Timeout("Request timed out")

            result = check_ollama_health()

            # Should handle timeout
            assert result["status"] == "unhealthy"
            assert "timed out" in result["error"].lower()
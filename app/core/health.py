"""
Health check utilities for monitoring service connectivity.
"""

import logging
import time
from typing import Dict

import requests

from app.core.config import Config

logger = logging.getLogger(__name__)


def check_ollama_health() -> Dict[str, any]:
    """
    Check Ollama service health and available models.

    Returns:
        dict: Status information with 'status', 'models', and optional 'error'
    """
    try:
        response = requests.get(
            f"{Config.OLLAMA_HOST}/api/tags",
            timeout=5
        )
        response.raise_for_status()

        data = response.json()
        models = [model.get("name", "unknown") for model in data.get("models", [])]

        return {
            "status": "healthy",
            "models": models,
            "url": Config.OLLAMA_HOST
        }
    except requests.exceptions.ConnectionError as e:
        logger.warning(f"Ollama connection failed: {e}")
        return {
            "status": "unhealthy",
            "error": "Connection refused - is Ollama running?",
            "url": Config.OLLAMA_HOST
        }
    except requests.exceptions.Timeout as e:
        logger.warning(f"Ollama timeout: {e}")
        return {
            "status": "unhealthy",
            "error": "Request timed out",
            "url": Config.OLLAMA_HOST
        }
    except Exception as e:
        logger.error(f"Ollama health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "url": Config.OLLAMA_HOST
        }


def check_postgres_health() -> Dict[str, any]:
    """
    Check PostgreSQL service health.

    Returns:
        dict: Status information with 'status' and optional 'error'
    """
    try:
        from app.core.sqlite_manager import get_sqlite_manager

        pg_manager = get_sqlite_manager()
        # Try to list collections as a health check
        collections = pg_manager.list_collections()

        return {
            "status": "healthy",
            "collections": len(collections)
        }
    except Exception as e:
        logger.warning(f"PostgreSQL connection failed: {e}")
        return {
            "status": "unhealthy",
            "error": "Connection refused - is PostgreSQL running?"
        }


# Backwards compatibility alias
check_chroma_health = check_postgres_health


def wait_for_services(max_retries: int = 30, delay: int = 2) -> bool:
    """
    Wait for both Ollama and PostgreSQL services to become healthy.

    Args:
        max_retries: Maximum number of retry attempts
        delay: Seconds to wait between retries

    Returns:
        bool: True if both services are healthy, False if max retries exceeded
    """
    logger.info("Waiting for services to become healthy...")

    for attempt in range(1, max_retries + 1):
        ollama_status = check_ollama_health()
        postgres_status = check_postgres_health()

        if ollama_status["status"] == "healthy" and postgres_status["status"] == "healthy":
            logger.info(f"All services healthy after {attempt} attempts")
            return True

        logger.info(
            f"Attempt {attempt}/{max_retries}: "
            f"Ollama={ollama_status['status']}, "
            f"PostgreSQL={postgres_status['status']}"
        )

        if attempt < max_retries:
            time.sleep(delay)

    logger.error(f"Services did not become healthy after {max_retries} attempts")
    return False


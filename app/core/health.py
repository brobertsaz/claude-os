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


def check_chroma_health() -> Dict[str, any]:
    """
    Check ChromaDB service health.

    Returns:
        dict: Status information with 'status' and optional 'error'
    """
    try:
        # Use v2 API endpoint for health check
        response = requests.get(
            f"{Config.get_chroma_url()}/api/v2/auth/identity",
            timeout=5
        )
        response.raise_for_status()

        return {
            "status": "healthy",
            "url": Config.get_chroma_url()
        }
    except requests.exceptions.ConnectionError as e:
        logger.warning(f"ChromaDB connection failed: {e}")
        return {
            "status": "unhealthy",
            "error": "Connection refused - is ChromaDB running?",
            "url": Config.get_chroma_url()
        }
    except requests.exceptions.Timeout as e:
        logger.warning(f"ChromaDB timeout: {e}")
        return {
            "status": "unhealthy",
            "error": "Request timed out",
            "url": Config.get_chroma_url()
        }
    except Exception as e:
        logger.error(f"ChromaDB health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "url": Config.get_chroma_url()
        }


def wait_for_services(max_retries: int = 30, delay: int = 2) -> bool:
    """
    Wait for both Ollama and ChromaDB services to become healthy.

    Args:
        max_retries: Maximum number of retry attempts
        delay: Seconds to wait between retries

    Returns:
        bool: True if both services are healthy, False if max retries exceeded
    """
    logger.info("Waiting for services to become healthy...")

    for attempt in range(1, max_retries + 1):
        ollama_status = check_ollama_health()
        chroma_status = check_chroma_health()

        if ollama_status["status"] == "healthy" and chroma_status["status"] == "healthy":
            logger.info(f"All services healthy after {attempt} attempts")
            return True

        logger.info(
            f"Attempt {attempt}/{max_retries}: "
            f"Ollama={ollama_status['status']}, "
            f"ChromaDB={chroma_status['status']}"
        )

        if attempt < max_retries:
            time.sleep(delay)

    logger.error(f"Services did not become healthy after {max_retries} attempts")
    return False


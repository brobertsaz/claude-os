"""
Agent OS Ingestion Module

Handles ingestion of Agent OS profiles into Code-Forge knowledge bases.
Integrates with ChromaManager to store parsed Agent OS content.
"""

import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from llama_index.embeddings.ollama import OllamaEmbedding

from app.core.agent_os_parser import AgentOSParser, AgentOSDocument, AgentOSContentType
from app.core.pg_manager import PostgresManager
from app.core.config import Config

logger = logging.getLogger(__name__)


class AgentOSIngestion:
    """Handles ingestion of Agent OS profiles into knowledge bases."""

    def __init__(self, db_manager: PostgresManager):
        """
        Initialize Agent OS ingestion.

        Args:
            db_manager: PostgresManager instance for storage
        """
        self.db_manager = db_manager
        self.parser = AgentOSParser()

    def ingest_profile(
        self,
        kb_name: str,
        profile_path: str,
        batch_size: int = 100
    ) -> Dict[str, Any]:
        """
        Ingest an Agent OS profile into a knowledge base.

        Args:
            kb_name: Name of the knowledge base
            profile_path: Path to the Agent OS profile directory
            batch_size: Number of documents to process in each batch

        Returns:
            Dictionary with ingestion statistics

        Raises:
            ValueError: If KB doesn't exist or profile path is invalid
        """
        logger.info(f"Starting Agent OS profile ingestion: {profile_path} -> {kb_name}")

        # Validate KB exists
        collections = self.db_manager.list_collections()
        kb_names = [col["name"] for col in collections]
        if kb_name not in kb_names:
            raise ValueError(f"Knowledge base '{kb_name}' does not exist")

        # Parse the profile directory
        try:
            documents = self.parser.parse_directory(profile_path)
        except Exception as e:
            logger.error(f"Failed to parse Agent OS profile: {e}")
            raise ValueError(f"Failed to parse Agent OS profile: {e}")

        if not documents:
            logger.warning("No documents found in Agent OS profile")
            return {
                "success": False,
                "message": "No documents found in profile",
                "documents_processed": 0
            }

        # Ingest documents in batches
        stats = {
            "total_documents": len(documents),
            "documents_by_type": {},
            "success": True,
            "errors": []
        }

        # Count documents by type
        for doc in documents:
            content_type = doc.content_type.value
            stats["documents_by_type"][content_type] = \
                stats["documents_by_type"].get(content_type, 0) + 1

        # Process in batches
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            try:
                self._ingest_batch(kb_name, batch)
                logger.info(f"Ingested batch {i//batch_size + 1}: {len(batch)} documents")
            except Exception as e:
                error_msg = f"Failed to ingest batch {i//batch_size + 1}: {e}"
                logger.error(error_msg)
                stats["errors"].append(error_msg)
                stats["success"] = False

        logger.info(f"Agent OS ingestion complete: {stats}")
        return stats

    def _ingest_batch(self, kb_name: str, documents: List[AgentOSDocument]) -> None:
        """
        Ingest a batch of documents into the knowledge base.

        Args:
            kb_name: Name of the knowledge base
            documents: List of AgentOSDocument objects to ingest
        """
        if not documents:
            return

        # Prepare data for ChromaDB
        texts = []
        metadatas = []
        ids = []

        for idx, doc in enumerate(documents):
            # Create unique ID
            doc_id = f"{doc.content_type.value}_{Path(doc.file_path).stem}_{idx}"

            # Prepare metadata (ChromaDB only supports string, int, float, bool)
            metadata = {
                "content_type": doc.content_type.value,
                "title": doc.title,
                "file_path": doc.file_path,
                "source": "agent_os",
            }

            # Add document metadata (convert complex types to strings)
            for key, value in doc.metadata.items():
                if isinstance(value, (str, int, float, bool)):
                    metadata[key] = value
                elif isinstance(value, list):
                    # Serialize lists as comma-separated strings
                    metadata[key] = ",".join(str(v) for v in value)
                else:
                    # Convert other types to string
                    metadata[key] = str(value)

            texts.append(doc.content)
            metadatas.append(metadata)
            ids.append(doc_id)

        # Generate embeddings
        embed_model = OllamaEmbedding(
            model_name=Config.OLLAMA_EMBED_MODEL,
            base_url=Config.OLLAMA_HOST
        )
        embeddings = [embed_model.get_text_embedding(text) for text in texts]

        # Add to PostgreSQL
        self.db_manager.add_documents(
            kb_name=kb_name,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )

        logger.debug(f"Added {len(documents)} documents to {kb_name}")

    def get_profile_stats(self, kb_name: str) -> Dict[str, Any]:
        """
        Get statistics about Agent OS content in a knowledge base.

        Args:
            kb_name: Name of the knowledge base

        Returns:
            Dictionary with statistics
        """
        try:
            # Get all documents with agent_os source
            results = self.db_manager.get_documents_by_metadata(
                kb_name=kb_name,
                where={"source": "agent_os"}
            )

            if not results:
                return {
                    "total_documents": 0,
                    "documents_by_type": {}
                }

            # Count by content type
            type_counts = {}
            for doc in results:
                metadata = doc.get("metadata", {})
                content_type = metadata.get("content_type", "unknown")
                type_counts[content_type] = type_counts.get(content_type, 0) + 1

            return {
                "total_documents": len(results),
                "documents_by_type": type_counts
            }

        except Exception as e:
            logger.error(f"Failed to get profile stats for {kb_name}: {e}")
            return {
                "total_documents": 0,
                "documents_by_type": {},
                "error": str(e)
            }

    def search_by_type(
        self,
        kb_name: str,
        content_type: AgentOSContentType,
        query: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search Agent OS content by type.

        Args:
            kb_name: Name of the knowledge base
            content_type: Type of content to search
            query: Optional search query (if None, returns all of type)
            limit: Maximum number of results

        Returns:
            List of matching documents
        """
        try:
            where_filter = {
                "source": "agent_os",
                "content_type": content_type.value
            }

            if query:
                # Semantic search with type filter
                embed_model = OllamaEmbedding(
                    model_name=Config.OLLAMA_EMBED_MODEL,
                    base_url=Config.OLLAMA_HOST
                )
                query_embedding = embed_model.get_text_embedding(query)

                results = self.db_manager.query_documents(
                    kb_name=kb_name,
                    query_embedding=query_embedding,
                    n_results=limit,
                    where=where_filter
                )

                # Format query results
                documents = []
                for i in range(len(results.get("documents", []))):
                    documents.append({
                        "content": results["documents"][i],
                        "metadata": results["metadatas"][i],
                        "distance": results.get("distances", [0])[i]
                    })
            else:
                # Just get all of this type
                results = self.db_manager.get_documents_by_metadata(
                    kb_name=kb_name,
                    where=where_filter,
                    limit=limit
                )

                # Format get results
                documents = []
                for doc in results:
                    documents.append({
                        "content": doc.get("content", ""),
                        "metadata": doc.get("metadata", {})
                    })

            return documents

        except Exception as e:
            logger.error(f"Failed to search by type in {kb_name}: {e}")
            return []


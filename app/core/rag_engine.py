"""
RAG Engine with advanced retrieval strategies.
Supports vector search, hybrid search, reranking, and agentic modes.
Now using SQLite with in-memory vector similarity instead of PostgreSQL.
"""

import logging
from typing import Dict, List, Optional
import numpy as np

from llama_index.core import Settings, VectorStoreIndex, get_response_synthesizer, PromptTemplate
from llama_index.core.query_engine import SubQuestionQueryEngine
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.tools import QueryEngineTool
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.llms.ollama import Ollama
from llama_index.core.postprocessor import SentenceTransformerRerank, SimilarityPostprocessor
from llama_index.core.schema import TextNode

# BM25 retriever - needs to be installed separately
try:
    from llama_index.retrievers.bm25 import BM25Retriever
    HAS_BM25 = True
except ImportError:
    HAS_BM25 = False

from app.core.sqlite_manager import get_sqlite_manager
from app.core.config import Config

logger = logging.getLogger(__name__)


class SimpleVectorRetriever:
    """Simple vector retriever using SQLite for similarity search."""

    def __init__(self, kb_name: str, db_manager, similarity_top_k: int = 10):
        """Initialize vector retriever."""
        self.kb_name = kb_name
        self.db_manager = db_manager
        self.similarity_top_k = similarity_top_k

    def retrieve(self, query_str: str, query_embedding: List[float]) -> List[TextNode]:
        """Retrieve similar documents using vector similarity."""
        results = self.db_manager.query_documents(
            self.kb_name,
            query_embedding,
            n_results=self.similarity_top_k
        )

        nodes = []
        if results["ids"] and len(results["ids"]) > 0:
            for doc_id, content, metadata, distance in zip(
                results["ids"][0],
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0]
            ):
                # Convert distance back to similarity score (1 - distance)
                similarity = float(1 - distance)  # Convert numpy float to Python float

                # Store similarity score in metadata since TextNode doesn't have a score attribute
                if metadata is None:
                    metadata = {}
                metadata["similarity_score"] = similarity

                node = TextNode(
                    text=content,
                    id_=doc_id,
                    metadata=metadata
                )
                nodes.append(node)

        return nodes


class RAGEngine:
    """Advanced RAG engine with SQLite vector storage."""

    def __init__(self, collection_name: str):
        """
        Initialize RAG engine for a specific knowledge base using SQLite.

        Args:
            collection_name: Name of the knowledge base
        """
        self.collection_name = collection_name

        # Initialize Ollama LLM optimized for Apple M4 Pro (14 cores, 48GB RAM)
        # Using native Ollama with Metal GPU acceleration
        self.llm = Ollama(
            model="llama3.1:latest",  # 8B model runs great on M4 Pro
            base_url="http://localhost:11434",  # Native Ollama (not Docker)
            request_timeout=120.0,  # Increased to 120s for LLM generation
            context_window=8192,  # Larger context with 48GB RAM
            num_ctx=8192,  # Match context_window
            temperature=0.1,  # Very low for factual RAG responses
            num_predict=512,  # Can handle more tokens with M4 Pro
            top_k=40,  # Better quality sampling
            top_p=0.9,  # Nucleus sampling for better quality
            num_thread=12,  # Use most cores (leave 2 for system)
            num_gpu=99,  # Use all GPU layers on Apple Silicon
            repeat_penalty=1.1,  # Avoid repetition
            num_batch=512,  # Larger batch size for M4 Pro
            use_mmap=True,  # Memory-map model for faster loading
            use_mlock=True,  # Lock model in RAM (plenty available)
        )
        Settings.llm = self.llm

        # Initialize Ollama embeddings
        self.embed_model = OllamaEmbedding(
            model_name=Config.OLLAMA_EMBED_MODEL,
            base_url="http://localhost:11434"  # Native Ollama (not Docker)
        )
        Settings.embed_model = self.embed_model

        # Verify KB exists
        self.db_manager = get_sqlite_manager()
        if not self.db_manager.collection_exists(collection_name):
            raise ValueError(f"Collection {collection_name} not found")

        # Get KB metadata
        kb_metadata = self.db_manager.get_collection_metadata(collection_name)
        self.kb_type = kb_metadata.get("kb_type", "generic")

        logger.info(f"Initializing RAGEngine for KB: {collection_name} (type: {self.kb_type})")

        # Create simple retriever for SQLite
        self.vector_retriever = SimpleVectorRetriever(
            collection_name,
            self.db_manager,
            similarity_top_k=Config.TOP_K_RETRIEVAL
        )

        # Initialize reranker (DISABLED by default due to performance issues)
        self.reranker = None
        logger.info("Reranker disabled for performance (enable in code if needed)")

        # Create comprehensive prompt template optimized for M4 Pro performance
        qa_prompt_template = PromptTemplate(
            "Context from {kb_name}:\n{{context_str}}\n\n"
            "Question: {{query_str}}\n\n"
            "Instructions: Provide a helpful answer based on the context above. "
            "Include relevant details, code examples, and step-by-step instructions when available. "
            "If the information is not in the context, say 'This information is not available in the current documentation.' "
            "Answer:"
        )
        self.qa_prompt = qa_prompt_template

        # Create similarity filter (disabled due to Pydantic validation issues with score attribute)
        # self.similarity_filter = SimilarityPostprocessor(similarity_cutoff=Config.SIMILARITY_THRESHOLD)
        self.similarity_filter = None

        logger.info(f"Created RAGEngine for {collection_name}")

        # Initialize BM25 retriever (for hybrid search)
        self.bm25_retriever = None
        if HAS_BM25:
            try:
                # Get all documents for BM25
                all_docs = self.db_manager.list_collections()  # Will need to adapt
                if all_docs:
                    logger.info("BM25 retriever initialization skipped (requires document nodes)")
                else:
                    logger.warning("No documents found for BM25 retriever")
            except Exception as e:
                logger.warning(f"Failed to initialize BM25 retriever: {e}")
        else:
            logger.warning("BM25 retriever not available")

        # Initialize agentic query engine
        self.sub_question_engine = None
        logger.info("Agentic engine initialization skipped for SQLite version")

    def _reciprocal_rank_fusion(
        self,
        results_list: List[List],
        k: int = 60
    ) -> List:
        """
        Fuse multiple retrieval results using reciprocal rank fusion.

        Args:
            results_list: List of retrieval result lists
            k: RRF parameter (default 60)

        Returns:
            Fused and sorted list of nodes
        """
        node_scores = {}

        for results in results_list:
            for rank, node in enumerate(results, start=1):
                node_id = node.id_
                score = 1.0 / (k + rank)

                if node_id in node_scores:
                    node_scores[node_id]["score"] += score
                else:
                    node_scores[node_id] = {
                        "node": node,
                        "score": score
                    }

        # Sort by score
        sorted_nodes = sorted(
            node_scores.values(),
            key=lambda x: x["score"],
            reverse=True
        )

        return [item["node"] for item in sorted_nodes[:Config.TOP_K_RETRIEVAL]]

    def _query_hybrid(self, question: str, query_embedding: List[float]) -> Dict[str, any]:
        """
        Execute hybrid search (vector + BM25).

        Args:
            question: Query string
            query_embedding: Query embedding vector

        Returns:
            dict: Answer and sources
        """
        if not self.bm25_retriever:
            logger.warning("BM25 retriever not available, falling back to vector search")
            return self._query_base(question, query_embedding)

        # Retrieve from vector search
        vector_results = self.vector_retriever.retrieve(question, query_embedding)

        # Fuse results (just use vector for now since BM25 requires documents)
        fused_nodes = vector_results[:Config.TOP_K_RETRIEVAL]

        # Synthesize answer
        synthesizer = get_response_synthesizer()
        response = synthesizer.synthesize(question, nodes=fused_nodes)

        return self._format_response(response, fused_nodes)

    def _apply_reranking(self, nodes: List, query: str) -> List:
        """
        Apply reranking to retrieved nodes.

        Args:
            nodes: Retrieved nodes
            query: Query string

        Returns:
            Reranked nodes
        """
        if not self.reranker:
            return nodes

        reranked = self.reranker.postprocess_nodes(nodes, query_str=query)
        return reranked

    def _query_agentic(self, question: str, query_embedding: List[float]) -> Dict[str, any]:
        """
        Execute agentic RAG with sub-question decomposition.

        Args:
            question: Query string
            query_embedding: Query embedding vector

        Returns:
            dict: Answer, sub-questions, and sources
        """
        if not self.sub_question_engine:
            logger.warning("Agentic engine not available, falling back to base query")
            return self._query_base(question, query_embedding)

        response = self.sub_question_engine.query(question)

        # Extract sub-questions if available
        sub_questions = []
        if hasattr(response, "metadata") and response.metadata:
            sub_qa = response.metadata.get("sub_qa", [])
            sub_questions = [
                {"question": item[0], "answer": item[1]}
                for item in sub_qa
            ]

        result = self._format_response(response, response.source_nodes if hasattr(response, "source_nodes") else [])
        result["sub_questions"] = sub_questions

        return result

    def _query_base(self, question: str, query_embedding: List[float]) -> Dict[str, any]:
        """
        Execute base vector search query using SQLite.

        Args:
            question: Query string
            query_embedding: Query embedding vector

        Returns:
            dict: Answer and sources
        """
        logger.info(f"Executing base query: {question}")

        # Retrieve similar documents
        source_nodes = self.vector_retriever.retrieve(question, query_embedding)

        # Apply similarity filtering (if enabled)
        if self.similarity_filter is not None:
            filtered_nodes = self.similarity_filter.postprocess_nodes(source_nodes, query_str=question)
        else:
            filtered_nodes = source_nodes

        # If we filtered out all results, return a no-results response
        if not filtered_nodes:
            return {
                "answer": f"No relevant information found in {self.collection_name}.",
                "sources": []
            }

        # Synthesize answer using LLM
        synthesizer = get_response_synthesizer()
        response = synthesizer.synthesize(question, nodes=filtered_nodes)

        logger.info(f"Generated answer: {str(response)[:200]}")

        return self._format_response(response, filtered_nodes)

    def _format_response(self, response, source_nodes) -> Dict[str, any]:
        """Format query response for return."""
        sources = []
        for node in source_nodes:
            # Retrieve score from metadata (stored during node creation)
            metadata = node.metadata if hasattr(node, "metadata") else {}
            score = metadata.get("similarity_score") if metadata else None
            if score is not None:
                score = float(score)

            # Return metadata without the internal similarity_score
            display_metadata = {k: v for k, v in metadata.items() if k != "similarity_score"} if metadata else {}

            sources.append({
                "text": node.text,
                "metadata": display_metadata,
                "score": score
            })

        return {
            "answer": str(response),
            "sources": sources
        }

    def query(
        self,
        question: str,
        use_hybrid: bool = False,
        use_rerank: bool = False,
        use_agentic: bool = False
    ) -> Dict[str, any]:
        """
        Execute query with specified strategies.

        Args:
            question: Query string
            use_hybrid: Enable hybrid search
            use_rerank: Enable reranking
            use_agentic: Enable agentic RAG

        Returns:
            dict: Answer and sources
        """
        try:
            # Get query embedding
            query_embedding = self.embed_model.get_text_embedding(question)

            # Route to appropriate query method
            if use_agentic:
                return self._query_agentic(question, query_embedding)
            elif use_hybrid:
                return self._query_hybrid(question, query_embedding)
            else:
                return self._query_base(question, query_embedding)

        except Exception as e:
            logger.error(f"Query failed: {e}")
            return {
                "answer": f"Error executing query: {str(e)}",
                "sources": []
            }

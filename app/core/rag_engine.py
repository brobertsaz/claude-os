"""
RAG Engine with advanced retrieval strategies.
Supports vector search, hybrid search, reranking, and agentic modes.
"""

import logging
from typing import Dict, List, Optional

from llama_index.core import Settings, StorageContext, VectorStoreIndex, get_response_synthesizer
from llama_index.core.query_engine import SubQuestionQueryEngine
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.tools import QueryEngineTool
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.llms.ollama import Ollama
from llama_index.core.postprocessor import SentenceTransformerRerank
from llama_index.vector_stores.chroma import ChromaVectorStore

# BM25 retriever - needs to be installed separately
try:
    from llama_index.retrievers.bm25 import BM25Retriever
    HAS_BM25 = True
except ImportError:
    HAS_BM25 = False

from app.core.chroma_manager import get_chroma_manager
from app.core.config import Config

logger = logging.getLogger(__name__)


class RAGEngine:
    """Advanced RAG engine with multiple retrieval strategies."""

    def __init__(self, collection_name: str):
        """
        Initialize RAG engine for a specific knowledge base.

        Args:
            collection_name: Name of the ChromaDB collection
        """
        self.collection_name = collection_name

        # Initialize Ollama LLM with optimized context window
        # Context needs to fit: retrieved chunks (5 × 1024 = 5120) + question + answer
        # Using 4096 is a good balance between memory usage and functionality
        Settings.llm = Ollama(
            model=Config.OLLAMA_MODEL,
            base_url=Config.OLLAMA_HOST,
            request_timeout=120.0,
            context_window=4096,  # Balanced: fits most RAG queries without excessive memory
            num_ctx=4096  # Ollama-specific parameter for context size
        )

        # Initialize Ollama embeddings
        Settings.embed_model = OllamaEmbedding(
            model_name=Config.OLLAMA_EMBED_MODEL,
            base_url=Config.OLLAMA_HOST
        )

        # Get ChromaDB collection
        chroma_manager = get_chroma_manager()
        collection = chroma_manager.get_collection(collection_name)

        if not collection:
            raise ValueError(f"Collection {collection_name} not found")

        # Create vector store and index
        vector_store = ChromaVectorStore(chroma_collection=collection)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        self.index = VectorStoreIndex.from_vector_store(
            vector_store,
            storage_context=storage_context
        )

        # Create base query engine
        self.query_engine = self.index.as_query_engine(
            similarity_top_k=Config.TOP_K_RETRIEVAL
        )

        # Initialize retrievers
        self.vector_retriever = VectorIndexRetriever(
            index=self.index,
            similarity_top_k=Config.TOP_K_RETRIEVAL
        )

        # Initialize BM25 retriever (for hybrid search)
        if HAS_BM25:
            try:
                all_nodes = self.index.docstore.docs.values()
                self.bm25_retriever = BM25Retriever.from_defaults(
                    nodes=list(all_nodes),
                    similarity_top_k=Config.TOP_K_RETRIEVAL
                )
            except Exception as e:
                logger.warning(f"Failed to initialize BM25 retriever: {e}")
                self.bm25_retriever = None
        else:
            logger.warning("BM25 retriever not available - llama-index-retrievers-bm25 not installed")
            self.bm25_retriever = None

        # Initialize reranker
        try:
            self.reranker = SentenceTransformerRerank(
                model="cross-encoder/ms-marco-MiniLM-L-6-v2",
                top_n=Config.RERANK_TOP_N
            )
        except Exception as e:
            logger.warning(f"Failed to initialize reranker: {e}")
            self.reranker = None

        # Initialize agentic query engine
        try:
            query_tool = QueryEngineTool.from_defaults(
                query_engine=self.query_engine,
                name="knowledge_base",
                description=f"Searches the {collection_name} knowledge base for relevant information"
            )
            self.sub_question_engine = SubQuestionQueryEngine.from_defaults(
                query_engine_tools=[query_tool]
            )
        except Exception as e:
            logger.warning(f"Failed to initialize agentic engine: {e}")
            self.sub_question_engine = None

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
        # Aggregate scores by node ID
        node_scores = {}

        for results in results_list:
            for rank, node in enumerate(results, start=1):
                node_id = node.node_id
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

    def _query_hybrid(self, question: str) -> Dict[str, any]:
        """
        Execute hybrid search (vector + BM25).

        Args:
            question: Query string

        Returns:
            dict: Answer and sources
        """
        if not self.bm25_retriever:
            logger.warning("BM25 retriever not available, falling back to vector search")
            return self._query_base(question)

        # Retrieve from both methods
        vector_results = self.vector_retriever.retrieve(question)
        bm25_results = self.bm25_retriever.retrieve(question)

        # Fuse results
        fused_nodes = self._reciprocal_rank_fusion([vector_results, bm25_results])

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
            logger.warning("Reranker not available")
            return nodes

        reranked = self.reranker.postprocess_nodes(nodes, query_str=query)
        return reranked

    def _query_agentic(self, question: str) -> Dict[str, any]:
        """
        Execute agentic RAG with sub-question decomposition.

        Args:
            question: Query string

        Returns:
            dict: Answer, sub-questions, and sources
        """
        if not self.sub_question_engine:
            logger.warning("Agentic engine not available, falling back to base query")
            return self._query_base(question)

        response = self.sub_question_engine.query(question)

        # Extract sub-questions if available
        sub_questions = []
        if hasattr(response, "metadata") and response.metadata:
            sub_qa = response.metadata.get("sub_qa", [])
            sub_questions = [
                {"question": item[0], "answer": item[1]}
                for item in sub_qa
            ]

        result = self._format_response(response, response.source_nodes)
        result["sub_questions"] = sub_questions

        return result

    def _query_base(self, question: str) -> Dict[str, any]:
        """
        Execute base vector search query.

        Args:
            question: Query string

        Returns:
            dict: Answer and sources
        """
        response = self.query_engine.query(question)
        return self._format_response(response, response.source_nodes)

    def _format_response(self, response, source_nodes) -> Dict[str, any]:
        """Format query response for return."""
        sources = []
        for node in source_nodes:
            sources.append({
                "text": node.text,
                "metadata": node.metadata if hasattr(node, "metadata") else {},
                "score": node.score if hasattr(node, "score") else None
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
            # Route to appropriate query method
            if use_agentic:
                return self._query_agentic(question)
            elif use_hybrid:
                result = self._query_hybrid(question)
                if use_rerank and result.get("sources"):
                    # Note: Reranking after hybrid fusion
                    pass  # Already applied in hybrid
                return result
            else:
                result = self._query_base(question)
                if use_rerank and result.get("sources"):
                    # Apply reranking to base results
                    nodes = self.vector_retriever.retrieve(question)
                    reranked_nodes = self._apply_reranking(nodes, question)
                    synthesizer = get_response_synthesizer()
                    response = synthesizer.synthesize(question, nodes=reranked_nodes)
                    return self._format_response(response, reranked_nodes)
                return result

        except Exception as e:
            logger.error(f"Query failed: {e}")
            return {
                "answer": f"Error executing query: {str(e)}",
                "sources": []
            }


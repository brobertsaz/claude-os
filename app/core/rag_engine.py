"""
RAG Engine with advanced retrieval strategies.
Supports vector search, hybrid search, reranking, and agentic modes.
"""

import logging
from typing import Dict, List, Optional

from llama_index.core import Settings, StorageContext, VectorStoreIndex, get_response_synthesizer, PromptTemplate
from llama_index.core.query_engine import SubQuestionQueryEngine
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.tools import QueryEngineTool
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.llms.ollama import Ollama
from llama_index.core.postprocessor import SentenceTransformerRerank, SimilarityPostprocessor
from llama_index.vector_stores.postgres import PGVectorStore
from sqlalchemy import make_url

# BM25 retriever - needs to be installed separately
try:
    from llama_index.retrievers.bm25 import BM25Retriever
    HAS_BM25 = True
except ImportError:
    HAS_BM25 = False

from app.core.pg_manager import get_pg_manager
from app.core.config import Config

logger = logging.getLogger(__name__)


class RAGEngine:
    """Advanced RAG engine with multiple retrieval strategies."""

    def __init__(self, collection_name: str):
        """
        Initialize RAG engine for a specific knowledge base using PGVectorStore.

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

        # Verify KB exists and get table name
        self.pg_manager = get_pg_manager()
        if not self.pg_manager.collection_exists(collection_name):
            raise ValueError(f"Collection {collection_name} not found")

        # Get KB metadata
        conn = self.pg_manager.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, table_name, embed_dim FROM knowledge_bases WHERE name = %s",
                    (collection_name,)
                )
                result = cur.fetchone()
                if not result:
                    raise ValueError(f"Collection {collection_name} not found")
                self.kb_id, self.table_name, self.embed_dim = result

                if not self.table_name:
                    raise ValueError(f"Collection {collection_name} has not been migrated to PGVectorStore schema")
        finally:
            self.pg_manager.return_connection(conn)

        logger.info(f"Initializing RAGEngine for KB: {collection_name} (table: {self.table_name})")

        # Create PGVectorStore instance
        import os
        pg_user = os.getenv("POSTGRES_USER", os.getenv("USER", "postgres"))
        pg_password = os.getenv("POSTGRES_PASSWORD", "")
        pg_host = os.getenv("POSTGRES_HOST", "localhost")
        pg_port = os.getenv("POSTGRES_PORT", "5432")
        pg_db = os.getenv("POSTGRES_DB", "codeforge")

        logger.info(f"Connecting to PostgreSQL: {pg_user}@{pg_host}:{pg_port}/{pg_db}")

        # PGVectorStore automatically adds 'data_' prefix to table names
        # Our schema already has 'data_' prefix, so we need to strip it
        pgvector_table_name = self.table_name.removeprefix('data_')
        logger.info(f"Using PGVectorStore table name: {pgvector_table_name} (actual table: {self.table_name})")

        # Use individual parameters instead of connection_string
        # This ensures PGVectorStore creates both sync and async connection strings correctly
        self.vector_store = PGVectorStore.from_params(
            host=pg_host,
            port=pg_port,
            database=pg_db,
            user=pg_user,
            password=pg_password,
            table_name=pgvector_table_name,  # PGVectorStore will add 'data_' prefix
            embed_dim=self.embed_dim,
            hybrid_search=False,  # Start with pure vector search
            hnsw_kwargs=None,  # Use IVFFlat index (already created)
            perform_setup=False  # Don't recreate tables, use existing schema
        )

        # Create VectorStoreIndex from the vector store
        self.index = VectorStoreIndex.from_vector_store(
            vector_store=self.vector_store,
            embed_model=self.embed_model
        )
        logger.info(f"Created VectorStoreIndex for {collection_name}")

        # Create vector retriever
        self.vector_retriever = VectorIndexRetriever(
            index=self.index,
            similarity_top_k=Config.TOP_K_RETRIEVAL
        )

        # Initialize reranker (DISABLED by default due to performance issues - 40+ seconds per query)
        # The reranker downloads a large model and runs on CPU which is extremely slow
        # Enable only if you have GPU acceleration or can tolerate 40+ second delays
        self.reranker = None
        logger.info("Reranker disabled for performance (enable in code if needed)")

        # Create comprehensive prompt template optimized for M4 Pro performance
        qa_prompt_template = PromptTemplate(
            "Context from Pistn Documentation:\n{context_str}\n\n"
            "Question: {query_str}\n\n"
            "Instructions: Provide a helpful answer based on the context above. "
            "Include relevant details, code examples, and step-by-step instructions when available. "
            "If the information is not in the context, say 'This information is not available in the current documentation.' "
            "Answer:"
        )

        # Create similarity filter to enforce minimum relevance threshold
        similarity_filter = SimilarityPostprocessor(similarity_cutoff=Config.SIMILARITY_THRESHOLD)

        # Create query engine with custom prompt and strict filtering
        # Using "simple_summarize" mode for faster responses (single LLM call instead of multiple)
        node_postprocessors = [similarity_filter]
        if self.reranker:
            node_postprocessors.append(self.reranker)

        self.query_engine = self.index.as_query_engine(
            similarity_top_k=Config.TOP_K_RETRIEVAL,
            node_postprocessors=node_postprocessors,
            response_mode="simple_summarize",
            text_qa_template=qa_prompt_template
        )
        logger.info(f"Created query engine with strict filtering (similarity >= {Config.SIMILARITY_THRESHOLD}, top_k={Config.TOP_K_RETRIEVAL})")

        # Initialize BM25 retriever (for hybrid search)
        self.bm25_retriever = None
        if HAS_BM25:
            try:
                all_nodes = list(self.index.docstore.docs.values())
                if all_nodes:
                    self.bm25_retriever = BM25Retriever.from_defaults(
                        nodes=all_nodes,
                        similarity_top_k=Config.TOP_K_RETRIEVAL
                    )
                    logger.info("Initialized BM25 retriever for hybrid search")
                else:
                    logger.warning("No documents found for BM25 retriever")
            except Exception as e:
                logger.warning(f"Failed to initialize BM25 retriever: {e}")
        else:
            logger.warning("BM25 retriever not available")

        # Initialize agentic query engine
        self.sub_question_engine = None
        try:
            query_tool = QueryEngineTool.from_defaults(
                query_engine=self.query_engine,
                name="knowledge_base",
                description=f"Searches the {collection_name} knowledge base for relevant information"
            )
            self.sub_question_engine = SubQuestionQueryEngine.from_defaults(
                query_engine_tools=[query_tool]
            )
            logger.info("Initialized agentic query engine")
        except Exception as e:
            logger.warning(f"Failed to initialize agentic engine: {e}")

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
        Execute base vector search query using PGVectorStore and llama_index query engine.

        Args:
            question: Query string

        Returns:
            dict: Answer and sources
        """
        logger.info(f"Executing base query: {question}")

        # Use llama_index query engine (with reranking if available)
        response = self.query_engine.query(question)

        logger.info(f"Generated answer: {str(response)[:200]}")

        # Format response
        return self._format_response(response, response.source_nodes)

    def _format_response(self, response, source_nodes) -> Dict[str, any]:
        """Format query response for return."""
        sources = []
        for node in source_nodes:
            # Convert score to Python float for JSON serialization
            score = node.score if hasattr(node, "score") else None
            if score is not None:
                score = float(score)

            sources.append({
                "text": node.text,
                "metadata": node.metadata if hasattr(node, "metadata") else {},
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
            use_hybrid: Enable hybrid search (not implemented yet)
            use_rerank: Enable reranking (always enabled if reranker is available)
            use_agentic: Enable agentic RAG

        Returns:
            dict: Answer and sources
        """
        try:
            # Route to appropriate query method
            # Note: Reranking is always enabled if reranker is available (via node_postprocessors)
            if use_agentic:
                return self._query_agentic(question)
            elif use_hybrid:
                return self._query_hybrid(question)
            else:
                return self._query_base(question)

        except Exception as e:
            logger.error(f"Query failed: {e}")
            return {
                "answer": f"Error executing query: {str(e)}",
                "sources": []
            }


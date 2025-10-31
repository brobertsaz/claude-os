"""
Document ingestion pipeline for Claude OS.
Handles file upload, text extraction, chunking, embedding, and storage.
"""

import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import fitz  # PyMuPDF
from llama_index.core import Document, Settings
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.ollama import OllamaEmbedding

from app.core.sqlite_manager import get_sqlite_manager
from app.core.config import Config
from app.core.markdown_preprocessor import preprocess_markdown

logger = logging.getLogger(__name__)


def extract_text_from_file(file_path: str) -> str:
    """
    Extract text content from a file.

    Args:
        file_path: Path to the file

    Returns:
        str: Extracted text content
    """
    file_path = Path(file_path)
    extension = file_path.suffix.lower()

    try:
        if extension == ".pdf":
            # Extract text from PDF using PyMuPDF
            text = ""
            with fitz.open(file_path) as doc:
                for page in doc:
                    text += page.get_text()
            return text
        else:
            # Read text/code files with UTF-8 encoding
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
    except Exception as e:
        logger.error(f"Failed to extract text from {file_path}: {e}")
        return ""


def chunk_document(text: str, metadata: Dict) -> List[Document]:
    """
    Chunk document text into smaller pieces with overlap.

    Args:
        text: Document text
        metadata: Document metadata

    Returns:
        List of Document objects
    """
    splitter = SentenceSplitter(
        chunk_size=Config.CHUNK_SIZE,
        chunk_overlap=Config.CHUNK_OVERLAP
    )

    # Create a single document
    doc = Document(text=text, metadata=metadata)

    # Split into chunks
    nodes = splitter.get_nodes_from_documents([doc])

    # Convert nodes back to documents
    chunks = []
    for i, node in enumerate(nodes):
        chunk_metadata = metadata.copy()
        chunk_metadata["chunk_index"] = i
        chunk_metadata["chunk_id"] = node.node_id
        chunks.append(Document(text=node.text, metadata=chunk_metadata))

    return chunks


def ingest_file(
    file_path: str,
    collection_name: str,
    filename: str
) -> Dict[str, any]:
    """
    Ingest a single file into a knowledge base.

    Args:
        file_path: Path to the file
        collection_name: Target collection name
        filename: Original filename

    Returns:
        dict: Ingestion result with status and details
    """
    try:
        # Extract text
        text = extract_text_from_file(file_path)
        if not text.strip():
            return {
                "status": "error",
                "filename": filename,
                "error": "No text content extracted"
            }

        # Create base metadata
        file_ext = Path(filename).suffix.lower()
        metadata = {
            "filename": filename,
            "file_type": file_ext,
            "upload_date": datetime.now().isoformat(),
            "source_path": str(file_path)
        }

        # Preprocess markdown files
        if file_ext in ['.md', '.markdown']:
            try:
                processed_text, enriched_metadata = preprocess_markdown(
                    text, filename, str(file_path)
                )
                text = processed_text
                metadata.update(enriched_metadata)
                logger.info(f"Preprocessed markdown: {filename}")
            except Exception as e:
                logger.warning(f"Markdown preprocessing failed for {filename}: {e}")
                # Continue with original text if preprocessing fails

        # Chunk document
        chunks = chunk_document(text, metadata)

        # Initialize embedding model
        embed_model = OllamaEmbedding(
            model_name=Config.OLLAMA_EMBED_MODEL,
            base_url=Config.OLLAMA_HOST
        )

        # Get SQLite collection
        pg_manager = get_sqlite_manager()
        if not pg_manager.collection_exists(collection_name):
            return {
                "status": "error",
                "filename": filename,
                "error": f"Collection {collection_name} not found"
            }

        # Generate embeddings and add to collection
        documents = []
        embeddings = []
        metadatas = []
        ids = []

        failed_chunks = 0

        for i, chunk in enumerate(chunks):
            try:
                # Truncate very long chunks to prevent Ollama crashes
                chunk_text = chunk.text
                if len(chunk_text) > 8000:  # Limit to ~8K characters
                    logger.warning(f"Truncating chunk {i} of {filename} from {len(chunk_text)} to 8000 chars")
                    chunk_text = chunk_text[:8000]

                # Generate embedding
                embedding = embed_model.get_text_embedding(chunk_text)

                # Create unique ID
                chunk_id = f"{filename}_{chunk.metadata['chunk_index']}_{uuid.uuid4().hex[:8]}"

                # Collect data for batch insert
                documents.append(chunk_text)
                embeddings.append(embedding)
                metadatas.append(chunk.metadata)
                ids.append(chunk_id)
            except Exception as e:
                failed_chunks += 1
                logger.warning(f"Failed to embed chunk {i} of {filename}: {e}. Skipping this chunk.")
                continue

        if not documents:
            return {
                "status": "error",
                "filename": filename,
                "error": f"All {len(chunks)} chunks failed to generate embeddings"
            }

        # Add all documents to SQLite in batch
        pg_manager.add_documents(
            kb_name=collection_name,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )

        success_msg = f"Ingested {filename}: {len(documents)}/{len(chunks)} chunks"
        if failed_chunks > 0:
            success_msg += f" ({failed_chunks} chunks skipped due to errors)"
        logger.info(success_msg)

        return {
            "status": "success",
            "filename": filename,
            "chunks": len(chunks),
            "file_type": file_ext
        }

    except Exception as e:
        logger.error(f"Failed to ingest {filename}: {e}")
        return {
            "status": "error",
            "filename": filename,
            "error": str(e)
        }


def ingest_documents(
    collection_name: str,
    documents: List[str],
    metadatas: List[Dict]
) -> Dict[str, any]:
    """
    Ingest a list of pre-processed documents into a knowledge base.
    Used by hooks system for bulk ingestion.

    Args:
        collection_name: Target collection name
        documents: List of document texts
        metadatas: List of metadata dicts corresponding to each document

    Returns:
        dict: Ingestion result with status and details
    """
    try:
        # Initialize embedding model
        embed_model = OllamaEmbedding(
            model_name=Config.OLLAMA_EMBED_MODEL,
            base_url=Config.OLLAMA_HOST
        )

        # Get SQLite manager
        db_manager = get_sqlite_manager()
        if not db_manager.collection_exists(collection_name):
            return {
                "status": "error",
                "error": f"Collection {collection_name} not found",
                "documents_processed": 0
            }

        # Process all documents
        all_document_texts = []
        all_embeddings = []
        all_metadatas = []
        all_ids = []

        for doc_text, metadata in zip(documents, metadatas):
            if not doc_text.strip():
                logger.warning(f"Skipping empty document: {metadata.get('filename', 'unknown')}")
                continue

            # Chunk the document
            chunks = chunk_document(doc_text, metadata)

            # Generate embeddings for each chunk
            for i, chunk in enumerate(chunks):
                try:
                    # Truncate very long chunks to prevent Ollama crashes
                    chunk_text = chunk.text
                    if len(chunk_text) > 8000:  # Limit to ~8K characters
                        logger.warning(f"Truncating chunk {i} from {len(chunk_text)} to 8000 chars")
                        chunk_text = chunk_text[:8000]

                    embedding = embed_model.get_text_embedding(chunk_text)

                    # Create unique ID
                    chunk_id = f"{metadata.get('filename', 'doc')}_{chunk.metadata['chunk_index']}_{uuid.uuid4().hex[:8]}"

                    # Collect data
                    all_document_texts.append(chunk_text)
                    all_embeddings.append(embedding)
                    all_metadatas.append(chunk.metadata)
                    all_ids.append(chunk_id)
                except Exception as e:
                    logger.warning(f"Failed to embed chunk {i}: {e}. Skipping this chunk.")
                    continue

        if not all_document_texts:
            return {
                "status": "error",
                "error": "No valid documents to ingest",
                "documents_processed": 0
            }

        # Add all documents to database in batch
        db_manager.add_documents(
            kb_name=collection_name,
            documents=all_document_texts,
            embeddings=all_embeddings,
            metadatas=all_metadatas,
            ids=all_ids
        )

        logger.info(f"Ingested {len(documents)} documents into {collection_name}: {len(all_document_texts)} total chunks")

        return {
            "status": "success",
            "documents_processed": len(documents),
            "chunks_created": len(all_document_texts),
            "collection_name": collection_name
        }

    except Exception as e:
        logger.error(f"Failed to ingest documents into {collection_name}: {e}")
        return {
            "status": "error",
            "error": str(e),
            "documents_processed": 0
        }


def ingest_directory(
    dir_path: str,
    collection_name: str
) -> List[Dict[str, any]]:
    """
    Recursively ingest all supported files from a directory.

    Args:
        dir_path: Path to directory
        collection_name: Target collection name

    Returns:
        List of ingestion results
    """
    results = []
    dir_path = Path(dir_path)

    if not dir_path.exists() or not dir_path.is_dir():
        logger.error(f"Directory not found: {dir_path}")
        return [{
            "status": "error",
            "error": f"Directory not found: {dir_path}"
        }]

    # Recursively find all supported files
    for file_path in dir_path.rglob("*"):
        if file_path.is_file() and Config.is_supported_file(file_path.name):
            result = ingest_file(
                str(file_path),
                collection_name,
                file_path.name
            )
            results.append(result)

    return results


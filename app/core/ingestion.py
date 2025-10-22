"""
Document ingestion pipeline for Code-Forge.
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

from app.core.chroma_manager import get_chroma_manager
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

        # Get ChromaDB collection
        chroma_manager = get_chroma_manager()
        collection = chroma_manager.get_collection(collection_name)

        if not collection:
            return {
                "status": "error",
                "filename": filename,
                "error": f"Collection {collection_name} not found"
            }

        # Generate embeddings and add to collection
        for chunk in chunks:
            # Generate embedding
            embedding = embed_model.get_text_embedding(chunk.text)

            # Create unique ID
            chunk_id = f"{filename}_{chunk.metadata['chunk_index']}_{uuid.uuid4().hex[:8]}"

            # Add to ChromaDB
            collection.add(
                documents=[chunk.text],
                embeddings=[embedding],
                metadatas=[chunk.metadata],
                ids=[chunk_id]
            )

        logger.info(f"Ingested {filename}: {len(chunks)} chunks")

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


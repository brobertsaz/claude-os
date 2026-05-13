"""
Document ingestion pipeline for Claude OS.
Handles file upload, text extraction, chunking, embedding, and storage.
"""

import fnmatch
import hashlib
import json
import logging
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, List, Optional, Set

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

    Skips the file if its SHA-256 hash matches what's already stored in the KB
    (i.e. the file has not changed since last index). Uses deterministic chunk IDs
    so re-indexing an updated file replaces existing chunks in-place.

    Args:
        file_path: Path to the file
        collection_name: Target collection name
        filename: Original filename

    Returns:
        dict: Ingestion result with status ("success", "skipped", or "error")
    """
    try:
        # Compute file hash for change detection
        try:
            file_hash = hashlib.sha256(Path(file_path).read_bytes()).hexdigest()
        except Exception as e:
            logger.warning(f"Could not hash {file_path}: {e}. Proceeding without hash check.")
            file_hash = None

        # Skip unchanged files
        if file_hash:
            db_mgr = get_sqlite_manager()
            existing_hash = db_mgr.get_file_hash_in_kb(collection_name, str(file_path))
            if existing_hash == file_hash:
                logger.debug(f"Skipping unchanged file: {filename}")
                return {"status": "skipped", "filename": filename}

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
            "source_path": str(file_path),
        }
        if file_hash:
            metadata["file_hash"] = file_hash

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

                # Deterministic chunk ID — stable across re-indexing runs
                chunk_id = hashlib.sha256(
                    f"{file_path}:{chunk.metadata['chunk_index']}".encode()
                ).hexdigest()[:24]

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


# Directories to always skip during ingestion
SKIP_DIRECTORIES = {
    'node_modules',
    '.git',
    '.svn',
    '.hg',
    '__pycache__',
    '.pytest_cache',
    '.mypy_cache',
    '.tox',
    '.nox',
    '.eggs',
    '*.egg-info',
    'dist',
    'build',
    '.next',
    '.nuxt',
    '.output',
    'coverage',
    '.nyc_output',
    '.cache',
    'vendor',
    'target',  # Rust/Java
    'Pods',  # iOS
    '.gradle',
    '.idea',
    '.vscode',
    '.claude-os',  # Our own config/cache
    '.claude',     # Claude Code memory/skills
}


def should_skip_path(
    file_path: Path,
    extra_skip_dirs: Optional[Set[str]] = None,
    skip_file_patterns: Optional[Set[str]] = None,
) -> bool:
    """Check if a file path should be skipped based on directory/file exclusions.

    Supports fnmatch glob patterns in both skip sets.
    """
    combined_skip_dirs = SKIP_DIRECTORIES | (extra_skip_dirs or set())
    for part in file_path.parts:
        for pattern in combined_skip_dirs:
            if fnmatch.fnmatch(part, pattern):
                return True

    if skip_file_patterns and file_path.is_file():
        for pattern in skip_file_patterns:
            if fnmatch.fnmatch(file_path.name, pattern):
                return True

    return False


def _load_project_config(dir_path: Path) -> Dict:
    """Load .claude-os/config.json from a project root, return {} if missing."""
    config_file = dir_path / ".claude-os" / "config.json"
    if config_file.exists():
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to read project config {config_file}: {e}")
    return {}


def ingest_directory(
    dir_path: str,
    collection_name: str,
    progress_callback: Optional[Callable[[int, str], None]] = None,
    num_workers: int = 1,
) -> List[Dict[str, any]]:
    """
    Recursively ingest all supported files from a directory.
    Automatically skips common non-source directories and respects per-project
    .claude-os/config.json (skip_dirs + skip_file_patterns with glob support).

    Args:
        dir_path: Path to directory
        collection_name: Target collection name
        progress_callback: Optional callable(progress_pct, message) for progress updates
        num_workers: Number of parallel workers for embedding (default 1 = sequential)

    Returns:
        List of ingestion results
    """
    results = []
    dir_path = Path(dir_path)

    if not dir_path.exists() or not dir_path.is_dir():
        logger.error(f"Directory not found: {dir_path}")
        return [{"status": "error", "error": f"Directory not found: {dir_path}"}]

    # Load per-project skip configuration
    project_config = _load_project_config(dir_path)
    extra_skip_dirs: Set[str] = set(project_config.get("skip_dirs", []))
    skip_file_patterns: Set[str] = set(project_config.get("skip_file_patterns", []))

    if extra_skip_dirs:
        logger.info(f"Ingestion skip_dirs from config: {extra_skip_dirs}")
    if skip_file_patterns:
        logger.info(f"Ingestion skip_file_patterns from config: {skip_file_patterns}")

    # Collect all candidate files first so we can report progress
    all_files: List[Path] = []
    for file_path in dir_path.rglob("*"):
        if should_skip_path(file_path, extra_skip_dirs, skip_file_patterns):
            continue
        if file_path.is_file() and Config.is_supported_file(file_path.name):
            all_files.append(file_path)

    total = len(all_files)
    logger.info(f"Ingesting {total} files into {collection_name} (workers={num_workers})")

    if num_workers > 1:
        # Parallel ingestion via ThreadPoolExecutor
        lock = threading.Lock()
        completed_count = [0]  # mutable container for thread-safe counter

        def _ingest_with_progress(fp: Path) -> Dict:
            result = ingest_file(str(fp), collection_name, fp.name)
            with lock:
                completed_count[0] += 1
                done = completed_count[0]
                if progress_callback and (done % 50 == 0 or done == total):
                    pct = 10 + int((done / total) * 78)
                    progress_callback(pct, f"Indexed {done}/{total} files...")
            return result

        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = {executor.submit(_ingest_with_progress, fp): fp for fp in all_files}
            for future in as_completed(futures):
                try:
                    results.append(future.result())
                except Exception as e:
                    fp = futures[future]
                    logger.warning(f"Worker failed for {fp}: {e}")
                    results.append({"status": "error", "filename": fp.name, "error": str(e)})
    else:
        # Sequential ingestion (default)
        for i, file_path in enumerate(all_files):
            result = ingest_file(str(file_path), collection_name, file_path.name)
            results.append(result)

            if progress_callback and (((i + 1) % 50 == 0) or (i + 1) == total):
                pct = 10 + int(((i + 1) / total) * 78)
                progress_callback(pct, f"Indexed {i + 1}/{total} files...")

    # Stale cleanup: remove docs for files no longer in the project/filter set
    current_paths = {str(f) for f in all_files}
    if current_paths:
        db_manager = get_sqlite_manager()
        deleted = db_manager.delete_docs_not_in_paths(collection_name, current_paths)
        if deleted > 0:
            logger.info(f"Stale cleanup: removed {deleted} docs for {collection_name} (files removed or filtered out)")
        if progress_callback:
            progress_callback(98, f"Cleaned up {deleted} stale docs...")

    if progress_callback:
        progress_callback(100, f"Done: {len(results)} files processed")

    return results


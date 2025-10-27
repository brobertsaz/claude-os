"""
Markdown preprocessing for Claude OS.
Standardizes markdown files for better chunking and retrieval.
"""

import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)


def extract_frontmatter(text: str) -> Tuple[Optional[Dict], str]:
    """
    Extract YAML/TOML frontmatter from markdown.
    
    Args:
        text: Markdown content
    
    Returns:
        Tuple of (frontmatter_dict, content_without_frontmatter)
    """
    frontmatter = {}
    content = text
    
    # Check for YAML frontmatter (--- ... ---)
    yaml_pattern = r'^---\s*\n(.*?)\n---\s*\n'
    yaml_match = re.match(yaml_pattern, text, re.DOTALL)
    
    if yaml_match:
        frontmatter_text = yaml_match.group(1)
        content = text[yaml_match.end():]
        
        # Parse simple YAML (key: value pairs)
        for line in frontmatter_text.split('\n'):
            line = line.strip()
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                frontmatter[key] = value
    
    # Check for TOML frontmatter (+++ ... +++)
    toml_pattern = r'^\+\+\+\s*\n(.*?)\n\+\+\+\s*\n'
    toml_match = re.match(toml_pattern, text, re.DOTALL)
    
    if toml_match:
        frontmatter_text = toml_match.group(1)
        content = text[toml_match.end():]
        
        # Parse simple TOML (key = value pairs)
        for line in frontmatter_text.split('\n'):
            line = line.strip()
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                frontmatter[key] = value
    
    return frontmatter if frontmatter else None, content


def extract_title(text: str) -> Optional[str]:
    """
    Extract title from markdown (first H1 or frontmatter).
    
    Args:
        text: Markdown content
    
    Returns:
        Title string or None
    """
    # Try to find first H1 header
    h1_pattern = r'^#\s+(.+)$'
    match = re.search(h1_pattern, text, re.MULTILINE)
    
    if match:
        return match.group(1).strip()
    
    return None


def normalize_headers(text: str) -> str:
    """
    Normalize markdown headers to ATX style (# ## ###).
    
    Args:
        text: Markdown content
    
    Returns:
        Normalized markdown
    """
    lines = text.split('\n')
    normalized = []
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Check if next line is a setext-style header underline
        if i + 1 < len(lines):
            next_line = lines[i + 1].strip()
            
            # H1: underlined with ===
            if next_line and all(c == '=' for c in next_line):
                normalized.append(f"# {line}")
                i += 2  # Skip the underline
                continue
            
            # H2: underlined with ---
            if next_line and all(c == '-' for c in next_line) and len(next_line) >= 3:
                normalized.append(f"## {line}")
                i += 2  # Skip the underline
                continue
        
        # Keep line as-is
        normalized.append(line)
        i += 1
    
    return '\n'.join(normalized)


def clean_whitespace(text: str) -> str:
    """
    Clean up excessive whitespace while preserving code blocks.
    
    Args:
        text: Markdown content
    
    Returns:
        Cleaned markdown
    """
    # Preserve code blocks
    code_blocks = []
    code_pattern = r'```[\s\S]*?```'
    
    def save_code_block(match):
        code_blocks.append(match.group(0))
        return f"__CODE_BLOCK_{len(code_blocks) - 1}__"
    
    text = re.sub(code_pattern, save_code_block, text)
    
    # Remove trailing whitespace from lines
    lines = [line.rstrip() for line in text.split('\n')]
    
    # Collapse multiple blank lines to max 2
    cleaned = []
    blank_count = 0
    
    for line in lines:
        if not line.strip():
            blank_count += 1
            if blank_count <= 2:
                cleaned.append(line)
        else:
            blank_count = 0
            cleaned.append(line)
    
    text = '\n'.join(cleaned)
    
    # Restore code blocks
    for i, code_block in enumerate(code_blocks):
        text = text.replace(f"__CODE_BLOCK_{i}__", code_block)
    
    return text


def normalize_code_fences(text: str) -> str:
    """
    Normalize code fence markers to triple backticks.
    
    Args:
        text: Markdown content
    
    Returns:
        Normalized markdown
    """
    # Replace ~~~ with ```
    text = re.sub(r'^~~~', '```', text, flags=re.MULTILINE)
    
    return text


def slugify(text: str) -> str:
    """
    Convert text to URL-friendly slug.
    
    Args:
        text: Text to slugify
    
    Returns:
        Slugified string
    """
    # Convert to lowercase
    text = text.lower()
    
    # Replace spaces and underscores with hyphens
    text = re.sub(r'[\s_]+', '-', text)
    
    # Remove non-alphanumeric characters (except hyphens)
    text = re.sub(r'[^a-z0-9-]', '', text)
    
    # Remove multiple consecutive hyphens
    text = re.sub(r'-+', '-', text)
    
    # Remove leading/trailing hyphens
    text = text.strip('-')
    
    return text


def preprocess_markdown(
    text: str,
    filename: str,
    file_path: str
) -> Tuple[str, Dict]:
    """
    Preprocess markdown file for better chunking and retrieval.
    
    Args:
        text: Raw markdown content
        filename: Original filename
        file_path: File path
    
    Returns:
        Tuple of (processed_text, enriched_metadata)
    """
    logger.info(f"Preprocessing markdown: {filename}")
    
    # Extract frontmatter
    frontmatter, content = extract_frontmatter(text)
    
    # Extract title
    title = None
    if frontmatter and 'title' in frontmatter:
        title = frontmatter['title']
    else:
        title = extract_title(content)
    
    # If no title found, use filename
    if not title:
        title = Path(filename).stem.replace('-', ' ').replace('_', ' ').title()
    
    # Normalize content
    content = normalize_headers(content)
    content = normalize_code_fences(content)
    content = clean_whitespace(content)
    
    # Build enriched metadata
    metadata = {
        "title": title,
        "original_filename": filename,
        "source_path": file_path,
        "preprocessed": True,
        "preprocessed_date": datetime.now().isoformat()
    }
    
    # Add frontmatter fields to metadata
    if frontmatter:
        for key, value in frontmatter.items():
            if key not in metadata:  # Don't override existing keys
                metadata[f"fm_{key}"] = value  # Prefix with 'fm_' to indicate frontmatter
    
    # Extract tags if present
    if frontmatter and 'tags' in frontmatter:
        tags = frontmatter['tags']
        if isinstance(tags, str):
            # Parse comma-separated or space-separated tags
            tags = re.split(r'[,\s]+', tags)
            tags = [t.strip() for t in tags if t.strip()]
        metadata['tags'] = ','.join(tags) if tags else ''
    
    # Extract author if present
    if frontmatter and 'author' in frontmatter:
        metadata['author'] = frontmatter['author']
    
    # Extract date if present
    if frontmatter and 'date' in frontmatter:
        metadata['document_date'] = frontmatter['date']
    
    logger.info(f"Preprocessed {filename}: title='{title}', metadata_fields={len(metadata)}")
    
    return content, metadata


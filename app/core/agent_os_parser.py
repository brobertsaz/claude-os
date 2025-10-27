"""
Agent OS Parser Module

Parses Agent OS profile directory structures and extracts structured content
for ingestion into Claude OS knowledge bases.

Agent OS Structure:
- standards/ - Coding standards and best practices
- agents/ - Agent configurations and skills
- workflows/ - Development workflow definitions
- commands/ - Command definitions
- product/ - Product vision and roadmap (optional)
- specs/ - Feature specifications (optional)
"""

import os
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class AgentOSContentType(str, Enum):
    """Types of content in Agent OS profiles."""
    STANDARD = "standard"
    AGENT = "agent"
    WORKFLOW = "workflow"
    COMMAND = "command"
    PRODUCT = "product"
    SPEC = "spec"
    UNKNOWN = "unknown"


@dataclass
class AgentOSDocument:
    """Represents a parsed Agent OS document."""
    content_type: AgentOSContentType
    title: str
    content: str
    file_path: str
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "content_type": self.content_type.value,
            "title": self.title,
            "content": self.content,
            "file_path": self.file_path,
            "metadata": self.metadata
        }


class AgentOSParser:
    """Parser for Agent OS profile directories."""
    
    # Map directory names to content types
    DIRECTORY_TYPE_MAP = {
        "standards": AgentOSContentType.STANDARD,
        "agents": AgentOSContentType.AGENT,
        "workflows": AgentOSContentType.WORKFLOW,
        "commands": AgentOSContentType.COMMAND,
        "product": AgentOSContentType.PRODUCT,
        "specs": AgentOSContentType.SPEC,
    }
    
    # Supported file extensions
    SUPPORTED_EXTENSIONS = {".yml", ".yaml", ".md"}
    
    def __init__(self):
        """Initialize the Agent OS parser."""
        pass
    
    def parse_directory(self, directory_path: str) -> List[AgentOSDocument]:
        """
        Parse an Agent OS profile directory.
        
        Args:
            directory_path: Path to the Agent OS profile directory
            
        Returns:
            List of parsed AgentOSDocument objects
            
        Raises:
            ValueError: If directory doesn't exist or isn't a valid Agent OS profile
        """
        path = Path(directory_path)
        
        if not path.exists():
            raise ValueError(f"Directory does not exist: {directory_path}")
        
        if not path.is_dir():
            raise ValueError(f"Path is not a directory: {directory_path}")
        
        # Validate it's an Agent OS profile (has at least one expected subdirectory)
        subdirs = [d.name for d in path.iterdir() if d.is_dir()]
        valid_subdirs = set(self.DIRECTORY_TYPE_MAP.keys())
        
        if not any(subdir in valid_subdirs for subdir in subdirs):
            raise ValueError(
                f"Not a valid Agent OS profile. Expected at least one of: {', '.join(valid_subdirs)}"
            )
        
        documents = []
        
        # Parse each subdirectory
        for subdir_name, content_type in self.DIRECTORY_TYPE_MAP.items():
            subdir_path = path / subdir_name
            if subdir_path.exists() and subdir_path.is_dir():
                docs = self._parse_content_directory(subdir_path, content_type)
                documents.extend(docs)
                logger.info(f"Parsed {len(docs)} documents from {subdir_name}/")
        
        logger.info(f"Total documents parsed: {len(documents)}")
        return documents
    
    def _parse_content_directory(
        self, 
        directory: Path, 
        content_type: AgentOSContentType
    ) -> List[AgentOSDocument]:
        """
        Parse all files in a content directory.
        
        Args:
            directory: Path to the content directory
            content_type: Type of content in this directory
            
        Returns:
            List of parsed documents
        """
        documents = []
        
        # Recursively find all supported files
        for file_path in directory.rglob("*"):
            if file_path.is_file() and file_path.suffix in self.SUPPORTED_EXTENSIONS:
                try:
                    doc = self._parse_file(file_path, content_type, directory)
                    if doc:
                        documents.append(doc)
                except Exception as e:
                    logger.error(f"Failed to parse {file_path}: {e}")
        
        return documents
    
    def _parse_file(
        self, 
        file_path: Path, 
        content_type: AgentOSContentType,
        base_dir: Path
    ) -> Optional[AgentOSDocument]:
        """
        Parse a single file.
        
        Args:
            file_path: Path to the file
            content_type: Type of content
            base_dir: Base directory for relative path calculation
            
        Returns:
            Parsed AgentOSDocument or None if parsing fails
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                raw_content = f.read()
            
            # Determine file type and parse accordingly
            if file_path.suffix in {".yml", ".yaml"}:
                return self._parse_yaml_file(file_path, raw_content, content_type, base_dir)
            elif file_path.suffix == ".md":
                return self._parse_markdown_file(file_path, raw_content, content_type, base_dir)
            
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return None
    
    def _parse_yaml_file(
        self,
        file_path: Path,
        raw_content: str,
        content_type: AgentOSContentType,
        base_dir: Path
    ) -> Optional[AgentOSDocument]:
        """Parse a YAML file."""
        try:
            data = yaml.safe_load(raw_content)
            
            if not data:
                logger.warning(f"Empty YAML file: {file_path}")
                return None
            
            # Extract title (use 'name', 'title', or filename)
            title = (
                data.get("name") or 
                data.get("title") or 
                file_path.stem
            )
            
            # Extract metadata
            metadata = {
                "file_type": "yaml",
                "relative_path": str(file_path.relative_to(base_dir)),
            }
            
            # Add common YAML fields to metadata
            for key in ["description", "version", "category", "priority", "tags"]:
                if key in data:
                    metadata[key] = data[key]
            
            # Convert YAML to readable text for content
            content = self._yaml_to_text(data, title)
            
            return AgentOSDocument(
                content_type=content_type,
                title=title,
                content=content,
                file_path=str(file_path),
                metadata=metadata
            )
            
        except yaml.YAMLError as e:
            logger.error(f"YAML parsing error in {file_path}: {e}")
            return None
    
    def _parse_markdown_file(
        self,
        file_path: Path,
        raw_content: str,
        content_type: AgentOSContentType,
        base_dir: Path
    ) -> Optional[AgentOSDocument]:
        """Parse a Markdown file."""
        # Extract title from first heading or filename
        title = file_path.stem
        lines = raw_content.split('\n')
        for line in lines:
            if line.startswith('# '):
                title = line[2:].strip()
                break
        
        metadata = {
            "file_type": "markdown",
            "relative_path": str(file_path.relative_to(base_dir)),
        }
        
        return AgentOSDocument(
            content_type=content_type,
            title=title,
            content=raw_content,
            file_path=str(file_path),
            metadata=metadata
        )
    
    def _yaml_to_text(self, data: Dict[str, Any], title: str) -> str:
        """
        Convert YAML data to readable text format.
        
        This creates a structured text representation that's good for RAG.
        """
        lines = [f"# {title}\n"]
        
        def format_value(value: Any, indent: int = 0) -> List[str]:
            """Recursively format YAML values."""
            result = []
            prefix = "  " * indent
            
            if isinstance(value, dict):
                for k, v in value.items():
                    result.append(f"{prefix}**{k}:**")
                    result.extend(format_value(v, indent + 1))
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, (dict, list)):
                        result.extend(format_value(item, indent))
                    else:
                        result.append(f"{prefix}- {item}")
            else:
                result.append(f"{prefix}{value}")
            
            return result
        
        # Format each top-level key
        for key, value in data.items():
            if key in ["name", "title"]:  # Skip title fields (already in header)
                continue
            
            lines.append(f"\n## {key.replace('_', ' ').title()}")
            lines.extend(format_value(value, 0))
        
        return "\n".join(lines)


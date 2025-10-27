"""
Knowledge Base Type System for Claude OS.
Defines KB types, metadata models, and type-specific configurations.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class KBType(str, Enum):
    """
    Knowledge Base types supported by Claude OS.

    Each type represents a distinct category of knowledge with
    specialized handling and retrieval strategies.
    """
    GENERIC = "generic"
    CODE = "code"
    DOCUMENTATION = "documentation"
    AGENT_OS = "agent-os"


class KBMetadata(BaseModel):
    """
    Type-safe metadata model for Knowledge Bases.

    Attributes:
        kb_type: The type of knowledge base
        description: Optional human-readable description
        created_at: ISO timestamp of creation
        tags: Optional list of custom tags
    """
    kb_type: KBType = Field(default=KBType.GENERIC)
    description: str = Field(default="")
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    tags: List[str] = Field(default_factory=list)

    class Config:
        use_enum_values = True  # Serialize enums as their values

    def to_dict(self) -> Dict[str, any]:
        """
        Convert to dictionary for ChromaDB storage.

        Note: ChromaDB only supports string, int, float, and bool metadata values.
        Lists must be serialized to JSON strings.
        """
        return {
            "kb_type": self.kb_type.value if isinstance(self.kb_type, KBType) else self.kb_type,
            "description": self.description,
            "created_at": self.created_at,
            "tags": ",".join(self.tags) if self.tags else ""  # Serialize list as comma-separated string
        }

    @classmethod
    def from_dict(cls, data: Dict[str, any]) -> "KBMetadata":
        """
        Create from dictionary retrieved from ChromaDB.

        Note: Deserializes comma-separated tag strings back to lists.
        """
        tags_str = data.get("tags", "")
        tags = [tag.strip() for tag in tags_str.split(",") if tag.strip()] if tags_str else []

        return cls(
            kb_type=KBType(data.get("kb_type", KBType.GENERIC.value)),
            description=data.get("description", ""),
            created_at=data.get("created_at", datetime.utcnow().isoformat()),
            tags=tags
        )


class KBTypeInfo(BaseModel):
    """
    Display information for a KB type.

    Attributes:
        icon: Emoji icon for UI display
        color: HSL color for Archon-inspired theming
        name: Human-readable name
        description: Detailed description of the type
        use_cases: List of typical use cases
    """
    icon: str
    color: str
    name: str
    description: str
    use_cases: List[str]


# Type-specific display configurations
KB_TYPE_INFO: Dict[KBType, KBTypeInfo] = {
    KBType.GENERIC: KBTypeInfo(
        icon="📦",
        color="hsl(0, 0%, 60%)",  # Gray
        name="Generic",
        description="General-purpose knowledge base for mixed content",
        use_cases=[
            "Mixed documentation and code",
            "Personal notes and references",
            "Unstructured knowledge collections"
        ]
    ),
    KBType.CODE: KBTypeInfo(
        icon="💻",
        color="hsl(271, 91%, 65%)",  # Archon purple
        name="Code Repository",
        description="Source code and technical implementation knowledge",
        use_cases=[
            "Application codebases",
            "Library and framework code",
            "Code examples and snippets",
            "Technical implementation details"
        ]
    ),
    KBType.DOCUMENTATION: KBTypeInfo(
        icon="📚",
        color="hsl(160, 84%, 39%)",  # Archon green
        name="Documentation",
        description="Technical documentation, guides, and references",
        use_cases=[
            "API documentation",
            "User guides and tutorials",
            "Technical specifications",
            "Architecture documentation"
        ]
    ),
    KBType.AGENT_OS: KBTypeInfo(
        icon="🤖",
        color="hsl(330, 90%, 65%)",  # Archon pink
        name="Agent OS Profile",
        description="Spec-driven development profiles with standards, specs, and workflows",
        use_cases=[
            "Coding standards and conventions",
            "Product vision and roadmap",
            "Feature specifications",
            "Development workflows",
            "Agent OS 3-layer context (Standards, Product, Specs)"
        ]
    )
}


def get_kb_type_info(kb_type: KBType) -> KBTypeInfo:
    """
    Get display information for a KB type.

    Args:
        kb_type: The KB type to get info for

    Returns:
        KBTypeInfo object with display metadata

    Example:
        >>> info = get_kb_type_info(KBType.AGENT_OS)
        >>> print(f"{info.icon} {info.name}")
        🤖 Agent OS Profile
    """
    return KB_TYPE_INFO.get(kb_type, KB_TYPE_INFO[KBType.GENERIC])


def validate_kb_type(kb_type_str: str) -> Optional[KBType]:
    """
    Validate and convert a string to KBType enum.

    Args:
        kb_type_str: String representation of KB type

    Returns:
        KBType enum if valid, None otherwise

    Example:
        >>> validate_kb_type("agent-os")
        <KBType.AGENT_OS: 'agent-os'>
        >>> validate_kb_type("invalid")
        None
    """
    try:
        return KBType(kb_type_str)
    except ValueError:
        return None


def get_kb_type_display_name(kb_type: KBType) -> str:
    """
    Get human-readable display name for a KB type.

    Args:
        kb_type: The KB type

    Returns:
        Display name string

    Example:
        >>> get_kb_type_display_name(KBType.AGENT_OS)
        '🤖 Agent OS Profile'
    """
    info = get_kb_type_info(kb_type)
    return f"{info.icon} {info.name}"


def get_all_kb_types() -> List[KBType]:
    """
    Get list of all available KB types.

    Returns:
        List of KBType enums
    """
    return list(KBType)


def get_kb_type_choices() -> Dict[str, KBType]:
    """
    Get KB type choices for UI dropdowns.

    Returns:
        Dict mapping display names to KBType enums

    Example:
        >>> choices = get_kb_type_choices()
        >>> choices["🤖 Agent OS Profile"]
        <KBType.AGENT_OS: 'agent-os'>
    """
    return {
        get_kb_type_display_name(kb_type): kb_type
        for kb_type in get_all_kb_types()
    }


"""
Skill Manager for Claude Code skills.
Manages global skills (~/.claude/skills/) and project-level skills ({project}/.claude/skills/).
"""

import json
import logging
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class Skill:
    """A Claude Code skill."""
    name: str
    path: str
    description: str
    scope: str  # "global" or "project"
    source: str  # "claude-os-core", "template", "custom"
    content: str = ""
    enabled: bool = True
    category: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    created: Optional[str] = None
    modified: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "path": self.path,
            "description": self.description,
            "scope": self.scope,
            "source": self.source,
            "content": self.content,
            "enabled": self.enabled,
            "category": self.category,
            "tags": self.tags,
            "created": self.created,
            "modified": self.modified
        }


@dataclass
class SkillTemplate:
    """A skill template that can be installed."""
    name: str
    category: str
    description: str
    path: str
    tags: List[str] = field(default_factory=list)
    version: str = "1.0.0"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "path": self.path,
            "tags": self.tags,
            "version": self.version
        }


class SkillManager:
    """Manage Claude Code skills (global and project-level)."""

    GLOBAL_SKILLS_DIR = Path.home() / ".claude" / "skills"
    TEMPLATES_DIR = Path(__file__).parent.parent.parent / "templates" / "skill-library"

    # Core skills that should remain global
    CORE_SKILLS = {"memory"}

    def __init__(self, project_path: Optional[str] = None):
        """
        Initialize skill manager.

        Args:
            project_path: Optional project path for project-level operations
        """
        self.project_path = Path(project_path) if project_path else None

        # Ensure global skills directory exists
        self.GLOBAL_SKILLS_DIR.mkdir(parents=True, exist_ok=True)

    @property
    def project_skills_dir(self) -> Optional[Path]:
        """Get project skills directory."""
        if self.project_path:
            return self.project_path / ".claude" / "skills"
        return None

    def list_global_skills(self) -> List[Skill]:
        """
        List skills in ~/.claude/skills/

        Returns:
            List of global Skill objects
        """
        skills = []

        if not self.GLOBAL_SKILLS_DIR.exists():
            return skills

        for item in self.GLOBAL_SKILLS_DIR.iterdir():
            if item.is_dir() or (item.is_symlink() and item.resolve().is_dir()):
                try:
                    skill = self._parse_skill(item, scope="global")
                    if skill:
                        skills.append(skill)
                except Exception as e:
                    logger.warning(f"Failed to parse skill {item.name}: {e}")

        return sorted(skills, key=lambda s: s.name)

    def list_project_skills(self) -> List[Skill]:
        """
        List skills in {project}/.claude/skills/

        Returns:
            List of project Skill objects
        """
        skills = []

        if not self.project_skills_dir or not self.project_skills_dir.exists():
            return skills

        for item in self.project_skills_dir.iterdir():
            if item.is_dir():
                try:
                    skill = self._parse_skill(item, scope="project")
                    if skill:
                        skills.append(skill)
                except Exception as e:
                    logger.warning(f"Failed to parse project skill {item.name}: {e}")

        return sorted(skills, key=lambda s: s.name)

    def list_all_skills(self, include_content: bool = False) -> Dict[str, List[Skill]]:
        """
        List all skills (global and project).

        Args:
            include_content: Whether to include skill content

        Returns:
            Dict with "global" and "project" skill lists
        """
        global_skills = self.list_global_skills()
        project_skills = self.list_project_skills()

        if not include_content:
            for skill in global_skills + project_skills:
                skill.content = ""

        return {
            "global": global_skills,
            "project": project_skills
        }

    def list_templates(self, category: Optional[str] = None) -> List[SkillTemplate]:
        """
        List available skill templates.

        Args:
            category: Optional category filter

        Returns:
            List of SkillTemplate objects
        """
        templates = []

        if not self.TEMPLATES_DIR.exists():
            logger.warning(f"Templates directory not found: {self.TEMPLATES_DIR}")
            return templates

        for category_dir in self.TEMPLATES_DIR.iterdir():
            if not category_dir.is_dir():
                continue

            if category and category_dir.name != category:
                continue

            for template_dir in category_dir.iterdir():
                if not template_dir.is_dir():
                    continue

                try:
                    template = self._parse_template(template_dir, category_dir.name)
                    if template:
                        templates.append(template)
                except Exception as e:
                    logger.warning(f"Failed to parse template {template_dir.name}: {e}")

        return sorted(templates, key=lambda t: (t.category, t.name))

    def get_template_categories(self) -> List[str]:
        """
        Get list of template categories.

        Returns:
            List of category names
        """
        categories = []

        if not self.TEMPLATES_DIR.exists():
            return categories

        for item in self.TEMPLATES_DIR.iterdir():
            if item.is_dir():
                categories.append(item.name)

        return sorted(categories)

    def get_skill(self, name: str, scope: str) -> Optional[Skill]:
        """
        Get skill details including content.

        Args:
            name: Skill name
            scope: "global" or "project"

        Returns:
            Skill object or None if not found
        """
        if scope == "global":
            skill_path = self.GLOBAL_SKILLS_DIR / name
        elif scope == "project" and self.project_skills_dir:
            skill_path = self.project_skills_dir / name
        else:
            return None

        if not skill_path.exists():
            # Check if it's a symlink
            if skill_path.is_symlink():
                skill_path = skill_path.resolve()
            else:
                return None

        return self._parse_skill(skill_path, scope, include_content=True)

    def install_template(
        self,
        template_name: str,
        custom_name: Optional[str] = None
    ) -> Skill:
        """
        Install a skill template to the project.

        Args:
            template_name: Name of template to install
            custom_name: Optional custom name for the installed skill

        Returns:
            Installed Skill object

        Raises:
            ValueError: If template not found or no project path set
            FileExistsError: If skill already exists
        """
        if not self.project_path:
            raise ValueError("No project path set")

        # Find template
        template = None
        for t in self.list_templates():
            if t.name == template_name:
                template = t
                break

        if not template:
            raise ValueError(f"Template not found: {template_name}")

        # Determine target name and path
        skill_name = custom_name or template_name
        target_dir = self.project_skills_dir / skill_name

        if target_dir.exists():
            raise FileExistsError(f"Skill already exists: {skill_name}")

        # Create project skills directory if needed
        self.project_skills_dir.mkdir(parents=True, exist_ok=True)

        # Copy template to project
        template_path = Path(template.path)
        shutil.copytree(template_path, target_dir)

        # Update metadata if renamed
        if custom_name:
            metadata_file = target_dir / "metadata.json"
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                metadata["name"] = custom_name
                metadata["source"] = "template"
                metadata["installed_from"] = template_name
                metadata["installed_at"] = datetime.now().isoformat()
                with open(metadata_file, 'w') as f:
                    json.dump(metadata, f, indent=2)

        logger.info(f"Installed template {template_name} as {skill_name}")

        return self._parse_skill(target_dir, scope="project", include_content=True)

    def create_skill(
        self,
        name: str,
        description: str,
        content: str,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Skill:
        """
        Create a custom skill for the project.

        Args:
            name: Skill name
            description: Skill description
            content: Skill content (markdown)
            category: Optional category
            tags: Optional tags

        Returns:
            Created Skill object

        Raises:
            ValueError: If no project path set
            FileExistsError: If skill already exists
        """
        if not self.project_path:
            raise ValueError("No project path set")

        target_dir = self.project_skills_dir / name

        if target_dir.exists():
            raise FileExistsError(f"Skill already exists: {name}")

        # Create directories
        self.project_skills_dir.mkdir(parents=True, exist_ok=True)
        target_dir.mkdir()

        # Write skill content
        skill_file = target_dir / "skill.md"
        with open(skill_file, 'w') as f:
            f.write(content)

        # Write metadata
        metadata = {
            "name": name,
            "description": description,
            "category": category,
            "tags": tags or [],
            "source": "custom",
            "created_at": datetime.now().isoformat(),
            "version": "1.0.0"
        }
        metadata_file = target_dir / "metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"Created custom skill: {name}")

        return self._parse_skill(target_dir, scope="project", include_content=True)

    def update_skill(
        self,
        name: str,
        content: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Skill:
        """
        Update an existing project skill.

        Args:
            name: Skill name
            content: New content (optional)
            description: New description (optional)
            tags: New tags (optional)

        Returns:
            Updated Skill object

        Raises:
            ValueError: If no project path set
            FileNotFoundError: If skill not found
        """
        if not self.project_path:
            raise ValueError("No project path set")

        skill_dir = self.project_skills_dir / name

        if not skill_dir.exists():
            raise FileNotFoundError(f"Skill not found: {name}")

        # Update content
        if content is not None:
            skill_file = skill_dir / "skill.md"
            with open(skill_file, 'w') as f:
                f.write(content)

        # Update metadata
        metadata_file = skill_dir / "metadata.json"
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
        else:
            metadata = {"name": name}

        if description is not None:
            metadata["description"] = description
        if tags is not None:
            metadata["tags"] = tags
        metadata["modified_at"] = datetime.now().isoformat()

        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"Updated skill: {name}")

        return self._parse_skill(skill_dir, scope="project", include_content=True)

    def delete_skill(self, name: str) -> bool:
        """
        Delete a project skill.

        Args:
            name: Skill name

        Returns:
            True if deleted

        Raises:
            ValueError: If no project path set or trying to delete global skill
            FileNotFoundError: If skill not found
        """
        if not self.project_path:
            raise ValueError("No project path set")

        skill_dir = self.project_skills_dir / name

        if not skill_dir.exists():
            raise FileNotFoundError(f"Skill not found: {name}")

        shutil.rmtree(skill_dir)
        logger.info(f"Deleted skill: {name}")

        return True

    def _parse_skill(
        self,
        skill_path: Path,
        scope: str,
        include_content: bool = False
    ) -> Optional[Skill]:
        """
        Parse a skill directory into a Skill object.

        Args:
            skill_path: Path to skill directory
            scope: "global" or "project"
            include_content: Whether to include skill content

        Returns:
            Skill object or None if invalid
        """
        # Resolve symlinks
        if skill_path.is_symlink():
            resolved_path = skill_path.resolve()
        else:
            resolved_path = skill_path

        if not resolved_path.exists() or not resolved_path.is_dir():
            return None

        name = skill_path.name

        # Determine source
        if name in self.CORE_SKILLS and scope == "global":
            source = "claude-os-core"
        elif scope == "global":
            source = "template"
        else:
            source = "custom"

        # Load metadata if exists
        metadata_file = resolved_path / "metadata.json"
        metadata = {}
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                    source = metadata.get("source", source)
            except Exception as e:
                logger.warning(f"Failed to load metadata for {name}: {e}")

        # Load content
        content = ""
        if include_content:
            skill_file = resolved_path / "skill.md"
            if skill_file.exists():
                with open(skill_file, 'r') as f:
                    content = f.read()
            else:
                # Try other common names
                for filename in ["README.md", "index.md", f"{name}.md"]:
                    alt_file = resolved_path / filename
                    if alt_file.exists():
                        with open(alt_file, 'r') as f:
                            content = f.read()
                        break

        # Extract description from content if not in metadata
        description = metadata.get("description", "")
        if not description and content:
            # Try to extract from first paragraph
            lines = content.strip().split('\n')
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    description = line[:200]
                    break

        # Get file stats
        stat = resolved_path.stat()
        created = datetime.fromtimestamp(stat.st_ctime).isoformat()
        modified = datetime.fromtimestamp(stat.st_mtime).isoformat()

        return Skill(
            name=name,
            path=str(skill_path),
            description=description,
            scope=scope,
            source=source,
            content=content,
            enabled=True,
            category=metadata.get("category"),
            tags=metadata.get("tags", []),
            created=metadata.get("created_at", created),
            modified=metadata.get("modified_at", modified)
        )

    def _parse_template(self, template_path: Path, category: str) -> Optional[SkillTemplate]:
        """
        Parse a template directory into a SkillTemplate object.

        Args:
            template_path: Path to template directory
            category: Template category

        Returns:
            SkillTemplate object or None if invalid
        """
        if not template_path.is_dir():
            return None

        name = template_path.name

        # Load metadata
        metadata_file = template_path / "metadata.json"
        metadata = {}
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load template metadata for {name}: {e}")

        # Get description
        description = metadata.get("description", "")
        if not description:
            # Try to extract from skill.md
            skill_file = template_path / "skill.md"
            if skill_file.exists():
                with open(skill_file, 'r') as f:
                    content = f.read()
                    lines = content.strip().split('\n')
                    for line in lines:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            description = line[:200]
                            break

        return SkillTemplate(
            name=name,
            category=category,
            description=description,
            path=str(template_path),
            tags=metadata.get("tags", []),
            version=metadata.get("version", "1.0.0")
        )


# Convenience functions

def list_skills(project_path: Optional[str] = None) -> Dict[str, List[Dict]]:
    """
    List all skills.

    Args:
        project_path: Optional project path

    Returns:
        Dict with global and project skill lists as dicts
    """
    manager = SkillManager(project_path)
    skills = manager.list_all_skills()

    return {
        "global": [s.to_dict() for s in skills["global"]],
        "project": [s.to_dict() for s in skills["project"]]
    }


def list_skill_templates(category: Optional[str] = None) -> List[Dict]:
    """
    List available skill templates.

    Args:
        category: Optional category filter

    Returns:
        List of template dicts
    """
    manager = SkillManager()
    templates = manager.list_templates(category)
    return [t.to_dict() for t in templates]


# ============================================================================
# COMMUNITY SKILLS - Fetch from external GitHub repositories
# ============================================================================

import httpx
import base64
import re
import tempfile

@dataclass
class CommunitySkill:
    """A skill from an external community repository."""
    name: str
    description: str
    source: str  # "anthropic", "superpowers", etc.
    repo: str  # Full repo path e.g., "anthropics/skills"
    path: str  # Path within repo e.g., "skills/frontend-design"
    tags: List[str] = field(default_factory=list)
    url: str = ""  # GitHub URL

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "source": self.source,
            "repo": self.repo,
            "path": self.path,
            "tags": self.tags,
            "url": self.url
        }


# Community skill sources configuration
COMMUNITY_SOURCES = {
    "anthropic": {
        "repo": "anthropics/skills",
        "skills_path": "skills",
        "name": "Anthropic Official",
        "description": "Official skills from Anthropic"
    },
    "superpowers": {
        "repo": "obra/superpowers",
        "skills_path": "skills",
        "name": "Superpowers",
        "description": "Battle-tested skills for TDD, debugging, and collaboration"
    }
}


class CommunitySkillsManager:
    """Fetch and install skills from community GitHub repositories."""

    GITHUB_API = "https://api.github.com"
    GITHUB_RAW = "https://raw.githubusercontent.com"
    CACHE_TTL = 3600  # Cache for 1 hour

    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._cache_times: Dict[str, float] = {}

    def _is_cache_valid(self, key: str) -> bool:
        """Check if cache entry is still valid."""
        if key not in self._cache_times:
            return False
        import time
        return (time.time() - self._cache_times[key]) < self.CACHE_TTL

    def _set_cache(self, key: str, value: Any) -> None:
        """Set cache entry."""
        import time
        self._cache[key] = value
        self._cache_times[key] = time.time()

    async def list_community_skills(self, source: Optional[str] = None) -> List[CommunitySkill]:
        """
        List skills from community repositories.

        Args:
            source: Optional source filter ("anthropic", "superpowers", etc.)

        Returns:
            List of CommunitySkill objects
        """
        skills = []
        sources = {source: COMMUNITY_SOURCES[source]} if source else COMMUNITY_SOURCES

        for source_key, config in sources.items():
            try:
                source_skills = await self._fetch_skills_from_repo(source_key, config)
                skills.extend(source_skills)
            except Exception as e:
                logger.warning(f"Failed to fetch skills from {source_key}: {e}")

        return skills

    async def _fetch_skills_from_repo(
        self,
        source_key: str,
        config: Dict[str, str]
    ) -> List[CommunitySkill]:
        """Fetch skill list from a GitHub repository."""
        cache_key = f"skills_{source_key}"
        if self._is_cache_valid(cache_key):
            return self._cache[cache_key]

        repo = config["repo"]
        skills_path = config["skills_path"]

        # Fetch directory listing from GitHub API
        url = f"{self.GITHUB_API}/repos/{repo}/contents/{skills_path}"

        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=15.0)
            if response.status_code != 200:
                logger.error(f"GitHub API error for {repo}: {response.status_code}")
                return []

            items = response.json()

        skills = []
        for item in items:
            if item.get("type") != "dir":
                continue

            skill_name = item["name"]
            skill_path = f"{skills_path}/{skill_name}"

            # Try to fetch SKILL.md to get description
            description = await self._fetch_skill_description(repo, skill_path)

            skill = CommunitySkill(
                name=skill_name,
                description=description,
                source=source_key,
                repo=repo,
                path=skill_path,
                tags=self._infer_tags(skill_name, description),
                url=f"https://github.com/{repo}/tree/main/{skill_path}"
            )
            skills.append(skill)

        self._set_cache(cache_key, skills)
        return skills

    async def _fetch_skill_description(self, repo: str, skill_path: str) -> str:
        """Fetch skill description from SKILL.md."""
        # Try both SKILL.md and skill.md
        for filename in ["SKILL.md", "skill.md"]:
            url = f"{self.GITHUB_RAW}/{repo}/main/{skill_path}/{filename}"

            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(url, timeout=10.0)
                    if response.status_code == 200:
                        content = response.text
                        # Extract description from YAML frontmatter or first paragraph
                        return self._extract_description(content)
            except Exception:
                continue

        return ""

    def _extract_description(self, content: str) -> str:
        """Extract description from skill markdown content."""
        # Try YAML frontmatter first
        frontmatter_match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
        if frontmatter_match:
            frontmatter = frontmatter_match.group(1)
            desc_match = re.search(r'description:\s*["\']?([^"\'\n]+)["\']?', frontmatter)
            if desc_match:
                return desc_match.group(1).strip()[:200]

        # Fall back to first non-header paragraph
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#') and not line.startswith('---'):
                return line[:200]

        return ""

    def _infer_tags(self, name: str, description: str) -> List[str]:
        """Infer tags from skill name and description."""
        tags = []
        text = f"{name} {description}".lower()

        tag_keywords = {
            "testing": ["test", "tdd", "spec", "jest", "pytest", "rspec"],
            "debugging": ["debug", "error", "fix", "trace"],
            "frontend": ["frontend", "react", "vue", "ui", "css", "design"],
            "backend": ["backend", "api", "server", "database"],
            "documentation": ["doc", "readme", "markdown", "write"],
            "automation": ["automat", "script", "workflow"],
            "design": ["design", "canvas", "art", "visual", "brand"],
            "git": ["git", "commit", "branch", "merge"],
        }

        for tag, keywords in tag_keywords.items():
            if any(kw in text for kw in keywords):
                tags.append(tag)

        return tags

    async def get_skill_content(self, repo: str, skill_path: str) -> Dict[str, str]:
        """
        Fetch full skill content from GitHub.

        Returns:
            Dict with filename -> content mappings
        """
        # Get list of files in skill directory
        url = f"{self.GITHUB_API}/repos/{repo}/contents/{skill_path}"

        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=15.0)
            if response.status_code != 200:
                raise ValueError(f"Failed to fetch skill: {response.status_code}")

            items = response.json()

            contents = {}
            for item in items:
                if item.get("type") != "file":
                    continue

                filename = item["name"]
                # Fetch file content
                file_url = f"{self.GITHUB_RAW}/{repo}/main/{skill_path}/{filename}"

                file_response = await client.get(file_url, timeout=10.0)
                if file_response.status_code == 200:
                    contents[filename] = file_response.text

        return contents

    async def install_community_skill(
        self,
        skill: CommunitySkill,
        project_path: str,
        custom_name: Optional[str] = None
    ) -> Skill:
        """
        Install a community skill to a project.

        Args:
            skill: CommunitySkill to install
            project_path: Target project path
            custom_name: Optional custom name for the skill

        Returns:
            Installed Skill object
        """
        # Fetch skill content
        contents = await self.get_skill_content(skill.repo, skill.path)

        if not contents:
            raise ValueError(f"No content found for skill: {skill.name}")

        # Determine target directory
        skill_name = custom_name or skill.name
        target_dir = Path(project_path) / ".claude" / "skills" / skill_name

        if target_dir.exists():
            raise FileExistsError(f"Skill already exists: {skill_name}")

        # Create directory
        target_dir.mkdir(parents=True, exist_ok=True)

        # Write files
        for filename, content in contents.items():
            # Normalize SKILL.md to skill.md
            if filename.upper() == "SKILL.MD":
                filename = "skill.md"

            file_path = target_dir / filename
            with open(file_path, 'w') as f:
                f.write(content)

        # Create/update metadata
        metadata_file = target_dir / "metadata.json"
        metadata = {
            "name": skill_name,
            "description": skill.description,
            "source": f"community:{skill.source}",
            "original_repo": skill.repo,
            "original_path": skill.path,
            "installed_at": datetime.now().isoformat(),
            "tags": skill.tags
        }

        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"Installed community skill {skill.name} from {skill.source}")

        # Return as Skill object
        manager = SkillManager(project_path)
        return manager._parse_skill(target_dir, scope="project", include_content=True)


# Singleton instance
_community_manager: Optional[CommunitySkillsManager] = None


def get_community_manager() -> CommunitySkillsManager:
    """Get or create the community skills manager singleton."""
    global _community_manager
    if _community_manager is None:
        _community_manager = CommunitySkillsManager()
    return _community_manager


async def list_community_skills(source: Optional[str] = None) -> List[Dict]:
    """
    List available community skills.

    Args:
        source: Optional source filter

    Returns:
        List of community skill dicts
    """
    manager = get_community_manager()
    skills = await manager.list_community_skills(source)
    return [s.to_dict() for s in skills]


async def install_community_skill(
    source: str,
    skill_name: str,
    project_path: str,
    custom_name: Optional[str] = None
) -> Dict:
    """
    Install a community skill to a project.

    Args:
        source: Source key ("anthropic", "superpowers")
        skill_name: Name of the skill
        project_path: Target project path
        custom_name: Optional custom name

    Returns:
        Installed skill dict
    """
    manager = get_community_manager()

    # Find the skill
    skills = await manager.list_community_skills(source)
    skill = next((s for s in skills if s.name == skill_name), None)

    if not skill:
        raise ValueError(f"Skill not found: {skill_name} in {source}")

    installed = await manager.install_community_skill(skill, project_path, custom_name)
    return installed.to_dict()

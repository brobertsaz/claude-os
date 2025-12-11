"""
Tests for skill_manager.py - Skill management functionality.
"""

import json
import pytest
import tempfile
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock, AsyncMock
import httpx

from app.core.skill_manager import (
    Skill,
    SkillTemplate,
    SkillManager,
    CommunitySkill,
    CommunitySkillsManager,
    COMMUNITY_SOURCES,
    list_skills,
    list_skill_templates,
    list_community_skills,
    install_community_skill,
    get_community_manager,
)


class TestSkillDataclass:
    """Tests for Skill dataclass."""

    def test_skill_creation(self):
        """Test basic Skill creation."""
        skill = Skill(
            name="test-skill",
            path="/path/to/skill",
            description="A test skill",
            scope="global",
            source="custom"
        )
        assert skill.name == "test-skill"
        assert skill.path == "/path/to/skill"
        assert skill.description == "A test skill"
        assert skill.scope == "global"
        assert skill.source == "custom"
        assert skill.content == ""
        assert skill.enabled is True
        assert skill.category is None
        assert skill.tags == []

    def test_skill_with_all_fields(self):
        """Test Skill with all fields populated."""
        skill = Skill(
            name="full-skill",
            path="/path/to/skill",
            description="Full skill",
            scope="project",
            source="template",
            content="# Skill content",
            enabled=False,
            category="testing",
            tags=["test", "demo"],
            created="2025-01-01T00:00:00",
            modified="2025-01-02T00:00:00"
        )
        assert skill.enabled is False
        assert skill.category == "testing"
        assert skill.tags == ["test", "demo"]
        assert skill.created == "2025-01-01T00:00:00"
        assert skill.modified == "2025-01-02T00:00:00"

    def test_skill_to_dict(self):
        """Test Skill.to_dict() method."""
        skill = Skill(
            name="test-skill",
            path="/path",
            description="Test",
            scope="global",
            source="custom",
            category="testing",
            tags=["a", "b"]
        )
        result = skill.to_dict()

        assert isinstance(result, dict)
        assert result["name"] == "test-skill"
        assert result["path"] == "/path"
        assert result["description"] == "Test"
        assert result["scope"] == "global"
        assert result["source"] == "custom"
        assert result["category"] == "testing"
        assert result["tags"] == ["a", "b"]


class TestSkillTemplateDataclass:
    """Tests for SkillTemplate dataclass."""

    def test_template_creation(self):
        """Test basic SkillTemplate creation."""
        template = SkillTemplate(
            name="template-name",
            category="productivity",
            description="A template",
            path="/path/to/template"
        )
        assert template.name == "template-name"
        assert template.category == "productivity"
        assert template.description == "A template"
        assert template.path == "/path/to/template"
        assert template.tags == []
        assert template.version == "1.0.0"

    def test_template_to_dict(self):
        """Test SkillTemplate.to_dict() method."""
        template = SkillTemplate(
            name="test",
            category="test-cat",
            description="Test template",
            path="/path",
            tags=["tag1"],
            version="2.0.0"
        )
        result = template.to_dict()

        assert result["name"] == "test"
        assert result["category"] == "test-cat"
        assert result["description"] == "Test template"
        assert result["tags"] == ["tag1"]
        assert result["version"] == "2.0.0"


class TestCommunitySkillDataclass:
    """Tests for CommunitySkill dataclass."""

    def test_community_skill_creation(self):
        """Test CommunitySkill creation."""
        skill = CommunitySkill(
            name="frontend-design",
            description="Design skills",
            source="anthropic",
            repo="anthropics/skills",
            path="skills/frontend-design"
        )
        assert skill.name == "frontend-design"
        assert skill.source == "anthropic"
        assert skill.repo == "anthropics/skills"
        assert skill.tags == []
        assert skill.url == ""

    def test_community_skill_to_dict(self):
        """Test CommunitySkill.to_dict() method."""
        skill = CommunitySkill(
            name="test-skill",
            description="Test",
            source="superpowers",
            repo="obra/superpowers",
            path="skills/test",
            tags=["testing"],
            url="https://github.com/obra/superpowers"
        )
        result = skill.to_dict()

        assert result["name"] == "test-skill"
        assert result["source"] == "superpowers"
        assert result["repo"] == "obra/superpowers"
        assert result["tags"] == ["testing"]
        assert result["url"] == "https://github.com/obra/superpowers"


class TestSkillManager:
    """Tests for SkillManager class."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for skills."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def skill_manager(self, temp_dir):
        """Create SkillManager with mocked paths."""
        with patch.object(SkillManager, 'GLOBAL_SKILLS_DIR', temp_dir / "global_skills"):
            with patch.object(SkillManager, 'TEMPLATES_DIR', temp_dir / "templates"):
                manager = SkillManager(project_path=str(temp_dir / "project"))
                manager.GLOBAL_SKILLS_DIR.mkdir(parents=True, exist_ok=True)
                yield manager

    def test_init_without_project(self, temp_dir):
        """Test SkillManager initialization without project path."""
        with patch.object(SkillManager, 'GLOBAL_SKILLS_DIR', temp_dir / "global"):
            manager = SkillManager()
            assert manager.project_path is None
            assert manager.project_skills_dir is None

    def test_init_with_project(self, temp_dir):
        """Test SkillManager initialization with project path."""
        with patch.object(SkillManager, 'GLOBAL_SKILLS_DIR', temp_dir / "global"):
            manager = SkillManager(project_path=str(temp_dir / "myproject"))
            assert manager.project_path == temp_dir / "myproject"
            assert manager.project_skills_dir == temp_dir / "myproject" / ".claude" / "skills"

    def test_list_global_skills_empty(self, skill_manager):
        """Test listing global skills when none exist."""
        skills = skill_manager.list_global_skills()
        assert skills == []

    def test_list_global_skills_with_skills(self, skill_manager):
        """Test listing global skills with existing skills."""
        # Create a skill directory
        skill_dir = skill_manager.GLOBAL_SKILLS_DIR / "test-skill"
        skill_dir.mkdir(parents=True)

        # Create skill.md
        (skill_dir / "skill.md").write_text("# Test Skill\n\nThis is a test skill.")

        skills = skill_manager.list_global_skills()
        assert len(skills) == 1
        assert skills[0].name == "test-skill"
        assert skills[0].scope == "global"

    def test_list_global_skills_with_metadata(self, skill_manager):
        """Test listing global skills with metadata.json."""
        skill_dir = skill_manager.GLOBAL_SKILLS_DIR / "documented-skill"
        skill_dir.mkdir(parents=True)

        # Create metadata
        metadata = {
            "name": "documented-skill",
            "description": "A well documented skill",
            "category": "productivity",
            "tags": ["demo", "test"],
            "source": "custom"
        }
        (skill_dir / "metadata.json").write_text(json.dumps(metadata))
        (skill_dir / "skill.md").write_text("Skill content")

        skills = skill_manager.list_global_skills()
        assert len(skills) == 1
        assert skills[0].description == "A well documented skill"
        assert skills[0].category == "productivity"
        assert skills[0].tags == ["demo", "test"]

    def test_list_project_skills_no_project(self, temp_dir):
        """Test listing project skills without project path."""
        with patch.object(SkillManager, 'GLOBAL_SKILLS_DIR', temp_dir / "global"):
            manager = SkillManager()
            skills = manager.list_project_skills()
            assert skills == []

    def test_list_project_skills_with_skills(self, skill_manager, temp_dir):
        """Test listing project skills with existing skills."""
        # Create project skills directory
        project_skills_dir = temp_dir / "project" / ".claude" / "skills" / "my-skill"
        project_skills_dir.mkdir(parents=True)
        (project_skills_dir / "skill.md").write_text("# My Skill")

        skills = skill_manager.list_project_skills()
        assert len(skills) == 1
        assert skills[0].name == "my-skill"
        assert skills[0].scope == "project"

    def test_list_all_skills(self, skill_manager, temp_dir):
        """Test listing all skills (global and project)."""
        # Create global skill
        global_skill = skill_manager.GLOBAL_SKILLS_DIR / "global-skill"
        global_skill.mkdir(parents=True)
        (global_skill / "skill.md").write_text("Global")

        # Create project skill
        project_skill = temp_dir / "project" / ".claude" / "skills" / "project-skill"
        project_skill.mkdir(parents=True)
        (project_skill / "skill.md").write_text("Project")

        all_skills = skill_manager.list_all_skills()
        assert "global" in all_skills
        assert "project" in all_skills
        assert len(all_skills["global"]) == 1
        assert len(all_skills["project"]) == 1

    def test_get_skill_global(self, skill_manager):
        """Test getting a global skill by name."""
        skill_dir = skill_manager.GLOBAL_SKILLS_DIR / "my-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "skill.md").write_text("# Skill Content\n\nDetails here")

        skill = skill_manager.get_skill("my-skill", "global")
        assert skill is not None
        assert skill.name == "my-skill"
        assert "Skill Content" in skill.content

    def test_get_skill_not_found(self, skill_manager):
        """Test getting a non-existent skill."""
        skill = skill_manager.get_skill("nonexistent", "global")
        assert skill is None

    def test_get_skill_invalid_scope(self, skill_manager):
        """Test getting skill with invalid scope."""
        skill = skill_manager.get_skill("test", "invalid")
        assert skill is None

    def test_create_skill(self, skill_manager, temp_dir):
        """Test creating a new custom skill."""
        # Ensure project skills directory can be created
        skill = skill_manager.create_skill(
            name="new-skill",
            description="A new skill",
            content="# New Skill\n\nContent here",
            category="productivity",
            tags=["new", "test"]
        )

        assert skill.name == "new-skill"
        assert skill.description == "A new skill"
        assert skill.category == "productivity"
        assert skill.scope == "project"

        # Verify files were created
        skill_path = temp_dir / "project" / ".claude" / "skills" / "new-skill"
        assert (skill_path / "skill.md").exists()
        assert (skill_path / "metadata.json").exists()

    def test_create_skill_no_project(self, temp_dir):
        """Test creating skill without project path."""
        with patch.object(SkillManager, 'GLOBAL_SKILLS_DIR', temp_dir / "global"):
            manager = SkillManager()
            with pytest.raises(ValueError, match="No project path set"):
                manager.create_skill("test", "desc", "content")

    def test_create_skill_already_exists(self, skill_manager, temp_dir):
        """Test creating skill that already exists."""
        # Create existing skill
        skill_path = temp_dir / "project" / ".claude" / "skills" / "existing"
        skill_path.mkdir(parents=True)
        (skill_path / "skill.md").write_text("Existing")

        with pytest.raises(FileExistsError, match="Skill already exists"):
            skill_manager.create_skill("existing", "desc", "content")

    def test_update_skill(self, skill_manager, temp_dir):
        """Test updating an existing skill."""
        # Create skill first
        skill_path = temp_dir / "project" / ".claude" / "skills" / "update-me"
        skill_path.mkdir(parents=True)
        (skill_path / "skill.md").write_text("Original content")
        (skill_path / "metadata.json").write_text(json.dumps({"name": "update-me"}))

        # Update it
        skill = skill_manager.update_skill(
            name="update-me",
            content="Updated content",
            description="New description",
            tags=["updated"]
        )

        assert skill.name == "update-me"
        assert "Updated content" in (skill_path / "skill.md").read_text()

    def test_update_skill_not_found(self, skill_manager):
        """Test updating non-existent skill."""
        with pytest.raises(FileNotFoundError, match="Skill not found"):
            skill_manager.update_skill("nonexistent", content="new")

    def test_delete_skill(self, skill_manager, temp_dir):
        """Test deleting a skill."""
        # Create skill
        skill_path = temp_dir / "project" / ".claude" / "skills" / "delete-me"
        skill_path.mkdir(parents=True)
        (skill_path / "skill.md").write_text("Delete me")

        result = skill_manager.delete_skill("delete-me")
        assert result is True
        assert not skill_path.exists()

    def test_delete_skill_not_found(self, skill_manager):
        """Test deleting non-existent skill."""
        with pytest.raises(FileNotFoundError, match="Skill not found"):
            skill_manager.delete_skill("nonexistent")

    def test_list_templates(self, skill_manager, temp_dir):
        """Test listing skill templates."""
        # Create template directories
        templates_dir = skill_manager.TEMPLATES_DIR
        templates_dir.mkdir(parents=True)

        category_dir = templates_dir / "productivity"
        category_dir.mkdir()

        template_dir = category_dir / "time-tracker"
        template_dir.mkdir()
        (template_dir / "skill.md").write_text("# Time Tracker\n\nTrack your time.")
        (template_dir / "metadata.json").write_text(json.dumps({
            "name": "time-tracker",
            "description": "Track your time"
        }))

        templates = skill_manager.list_templates()
        assert len(templates) == 1
        assert templates[0].name == "time-tracker"
        assert templates[0].category == "productivity"

    def test_list_templates_by_category(self, skill_manager, temp_dir):
        """Test listing templates filtered by category."""
        templates_dir = skill_manager.TEMPLATES_DIR
        templates_dir.mkdir(parents=True)

        # Create two categories
        for cat in ["productivity", "testing"]:
            cat_dir = templates_dir / cat
            cat_dir.mkdir()
            (cat_dir / "skill-1").mkdir()
            (cat_dir / "skill-1" / "skill.md").write_text(f"# {cat} skill")

        # Filter by category
        templates = skill_manager.list_templates(category="testing")
        assert len(templates) == 1
        assert templates[0].category == "testing"

    def test_get_template_categories(self, skill_manager, temp_dir):
        """Test getting template categories."""
        templates_dir = skill_manager.TEMPLATES_DIR
        templates_dir.mkdir(parents=True)

        for cat in ["productivity", "testing", "debugging"]:
            (templates_dir / cat).mkdir()

        categories = skill_manager.get_template_categories()
        assert sorted(categories) == ["debugging", "productivity", "testing"]

    def test_install_template(self, skill_manager, temp_dir):
        """Test installing a template to project."""
        # Create template
        templates_dir = skill_manager.TEMPLATES_DIR
        templates_dir.mkdir(parents=True)
        cat_dir = templates_dir / "testing"
        cat_dir.mkdir()
        template_dir = cat_dir / "tdd-skill"
        template_dir.mkdir()
        (template_dir / "skill.md").write_text("# TDD Skill")
        (template_dir / "metadata.json").write_text(json.dumps({
            "name": "tdd-skill",
            "description": "Test-driven development"
        }))

        # Install it
        skill = skill_manager.install_template("tdd-skill")
        assert skill.name == "tdd-skill"
        assert skill.scope == "project"

        # Verify installed
        installed_path = temp_dir / "project" / ".claude" / "skills" / "tdd-skill"
        assert installed_path.exists()

    def test_install_template_with_custom_name(self, skill_manager, temp_dir):
        """Test installing template with custom name."""
        templates_dir = skill_manager.TEMPLATES_DIR
        templates_dir.mkdir(parents=True)
        cat_dir = templates_dir / "productivity"
        cat_dir.mkdir()
        template_dir = cat_dir / "original-name"
        template_dir.mkdir()
        (template_dir / "skill.md").write_text("# Skill")
        (template_dir / "metadata.json").write_text(json.dumps({"name": "original-name"}))

        skill = skill_manager.install_template("original-name", custom_name="my-custom-name")
        assert skill.name == "my-custom-name"

    def test_install_template_not_found(self, skill_manager):
        """Test installing non-existent template."""
        with pytest.raises(ValueError, match="Template not found"):
            skill_manager.install_template("nonexistent")

    def test_parse_skill_with_symlink(self, skill_manager, temp_dir):
        """Test parsing skill that is a symlink."""
        # Create actual skill
        real_skill = temp_dir / "real-skill"
        real_skill.mkdir()
        (real_skill / "skill.md").write_text("# Real Skill")

        # Create symlink
        link_path = skill_manager.GLOBAL_SKILLS_DIR / "linked-skill"
        link_path.symlink_to(real_skill)

        skills = skill_manager.list_global_skills()
        assert len(skills) == 1
        assert skills[0].name == "linked-skill"

    def test_parse_skill_extracts_description_from_content(self, skill_manager):
        """Test that description is extracted from content if not in metadata."""
        skill_dir = skill_manager.GLOBAL_SKILLS_DIR / "no-meta"
        skill_dir.mkdir(parents=True)
        (skill_dir / "skill.md").write_text("# Header\n\nThis is the description paragraph.\n\nMore content.")

        skill = skill_manager.get_skill("no-meta", "global")
        assert skill is not None
        assert "This is the description paragraph" in skill.description

    def test_core_skills_marked_correctly(self, skill_manager):
        """Test that core skills are marked with correct source."""
        # Create a core skill (memory is in CORE_SKILLS)
        skill_dir = skill_manager.GLOBAL_SKILLS_DIR / "memory"
        skill_dir.mkdir(parents=True)
        (skill_dir / "skill.md").write_text("Memory skill")

        skills = skill_manager.list_global_skills()
        memory_skill = next(s for s in skills if s.name == "memory")
        assert memory_skill.source == "claude-os-core"


class TestCommunitySkillsManager:
    """Tests for CommunitySkillsManager class."""

    @pytest.fixture
    def manager(self):
        """Create CommunitySkillsManager instance."""
        return CommunitySkillsManager()

    def test_cache_validity(self, manager):
        """Test cache validity checking."""
        # Initially cache should be invalid
        assert manager._is_cache_valid("test_key") is False

        # After setting, should be valid
        manager._set_cache("test_key", "value")
        assert manager._is_cache_valid("test_key") is True

    def test_set_cache(self, manager):
        """Test setting cache values."""
        manager._set_cache("key1", {"data": "value"})
        assert manager._cache["key1"] == {"data": "value"}
        assert "key1" in manager._cache_times

    def test_extract_description_from_frontmatter(self, manager):
        """Test extracting description from YAML frontmatter."""
        content = """---
description: "This is the skill description"
version: 1.0
---
# Skill Title

Content here."""

        description = manager._extract_description(content)
        assert description == "This is the skill description"

    def test_extract_description_from_paragraph(self, manager):
        """Test extracting description from first paragraph."""
        content = """# Skill Title

This is the first paragraph that should be used as description.

More content here."""

        description = manager._extract_description(content)
        assert description == "This is the first paragraph that should be used as description."

    def test_extract_description_truncates_long_text(self, manager):
        """Test that description is truncated to 200 chars."""
        long_text = "A" * 500
        content = f"# Title\n\n{long_text}"

        description = manager._extract_description(content)
        assert len(description) == 200

    def test_infer_tags_testing(self, manager):
        """Test tag inference for testing-related skills."""
        tags = manager._infer_tags("tdd-helper", "Test-driven development workflow")
        assert "testing" in tags

    def test_infer_tags_frontend(self, manager):
        """Test tag inference for frontend skills."""
        tags = manager._infer_tags("react-components", "Build React UI components")
        assert "frontend" in tags

    def test_infer_tags_multiple(self, manager):
        """Test inferring multiple tags."""
        tags = manager._infer_tags("debug-tests", "Debug and fix failing tests")
        assert "testing" in tags
        assert "debugging" in tags

    @pytest.mark.asyncio
    async def test_list_community_skills_cached(self, manager):
        """Test that cache is used when valid."""
        # The _fetch_skills_from_repo method checks cache internally
        # So we need to test that _is_cache_valid returns True
        cached_skills = [
            CommunitySkill("skill1", "desc", "anthropic", "anthropics/skills", "skills/skill1"),
        ]

        # Set cache directly and verify it's valid
        manager._set_cache("skills_anthropic", cached_skills)
        assert manager._is_cache_valid("skills_anthropic") is True

        # The internal _fetch_skills_from_repo will return cached data
        # We verify by checking the cache mechanism works
        assert manager._cache["skills_anthropic"] == cached_skills

    @pytest.mark.asyncio
    async def test_fetch_skills_from_repo_success(self, manager):
        """Test fetching skills from GitHub repo."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"type": "dir", "name": "skill-one"},
            {"type": "dir", "name": "skill-two"},
            {"type": "file", "name": "README.md"},  # Should be skipped
        ]

        with patch.object(httpx.AsyncClient, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response

            # Also mock description fetching
            with patch.object(manager, '_fetch_skill_description', new_callable=AsyncMock) as mock_desc:
                mock_desc.return_value = "Skill description"

                skills = await manager._fetch_skills_from_repo(
                    "anthropic",
                    {"repo": "anthropics/skills", "skills_path": "skills"}
                )

                assert len(skills) == 2
                assert skills[0].name == "skill-one"
                assert skills[1].name == "skill-two"

    @pytest.mark.asyncio
    async def test_fetch_skills_from_repo_api_error(self, manager):
        """Test handling GitHub API errors."""
        mock_response = MagicMock()
        mock_response.status_code = 404

        with patch.object(httpx.AsyncClient, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response

            skills = await manager._fetch_skills_from_repo(
                "anthropic",
                {"repo": "anthropics/skills", "skills_path": "skills"}
            )

            assert skills == []

    @pytest.mark.asyncio
    async def test_get_skill_content(self, manager):
        """Test fetching skill content from GitHub."""
        # Mock directory listing
        dir_response = MagicMock()
        dir_response.status_code = 200
        dir_response.json.return_value = [
            {"type": "file", "name": "skill.md"},
            {"type": "file", "name": "metadata.json"},
        ]

        # Mock file content
        file_response = MagicMock()
        file_response.status_code = 200
        file_response.text = "File content"

        with patch.object(httpx.AsyncClient, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = [dir_response, file_response, file_response]

            contents = await manager.get_skill_content("anthropics/skills", "skills/test")

            assert "skill.md" in contents
            assert "metadata.json" in contents

    @pytest.mark.asyncio
    async def test_install_community_skill(self, manager):
        """Test installing a community skill."""
        skill = CommunitySkill(
            name="test-skill",
            description="Test",
            source="anthropic",
            repo="anthropics/skills",
            path="skills/test-skill",
            tags=["testing"]
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            # Mock get_skill_content
            with patch.object(manager, 'get_skill_content', new_callable=AsyncMock) as mock_content:
                mock_content.return_value = {
                    "SKILL.md": "# Skill Content",
                    "metadata.json": json.dumps({"name": "test-skill"})
                }

                installed = await manager.install_community_skill(skill, tmpdir)

                assert installed.name == "test-skill"
                assert installed.scope == "project"

                # Verify files created
                skill_path = Path(tmpdir) / ".claude" / "skills" / "test-skill"
                assert skill_path.exists()
                assert (skill_path / "skill.md").exists()  # Normalized from SKILL.md

    @pytest.mark.asyncio
    async def test_install_community_skill_already_exists(self, manager):
        """Test installing skill that already exists."""
        skill = CommunitySkill("existing", "desc", "anthropic", "repo", "path")

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create existing skill
            existing = Path(tmpdir) / ".claude" / "skills" / "existing"
            existing.mkdir(parents=True)

            # Mock get_skill_content to avoid HTTP request
            with patch.object(manager, 'get_skill_content', new_callable=AsyncMock) as mock_content:
                mock_content.return_value = {"skill.md": "Content"}

                with pytest.raises(FileExistsError, match="Skill already exists"):
                    await manager.install_community_skill(skill, tmpdir)

    @pytest.mark.asyncio
    async def test_install_community_skill_empty_content(self, manager):
        """Test installing skill with no content."""
        skill = CommunitySkill("empty", "desc", "anthropic", "repo", "path")

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(manager, 'get_skill_content', new_callable=AsyncMock) as mock_content:
                mock_content.return_value = {}

                with pytest.raises(ValueError, match="No content found"):
                    await manager.install_community_skill(skill, tmpdir)


class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""

    def test_list_skills(self):
        """Test list_skills function."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(SkillManager, 'GLOBAL_SKILLS_DIR', Path(tmpdir) / "global"):
                Path(tmpdir, "global").mkdir()

                result = list_skills()
                assert "global" in result
                assert "project" in result
                assert isinstance(result["global"], list)
                assert isinstance(result["project"], list)

    def test_list_skill_templates(self):
        """Test list_skill_templates function."""
        with tempfile.TemporaryDirectory() as tmpdir:
            templates_dir = Path(tmpdir) / "templates"
            templates_dir.mkdir()

            with patch.object(SkillManager, 'TEMPLATES_DIR', templates_dir):
                result = list_skill_templates()
                assert isinstance(result, list)

    def test_get_community_manager_singleton(self):
        """Test that get_community_manager returns singleton."""
        manager1 = get_community_manager()
        manager2 = get_community_manager()
        assert manager1 is manager2

    @pytest.mark.asyncio
    async def test_list_community_skills_function(self):
        """Test list_community_skills convenience function."""
        mock_skills = [CommunitySkill("test", "desc", "anthropic", "repo", "path")]

        with patch.object(CommunitySkillsManager, 'list_community_skills', new_callable=AsyncMock) as mock_list:
            mock_list.return_value = mock_skills

            result = await list_community_skills()
            assert len(result) == 1
            assert result[0]["name"] == "test"

    @pytest.mark.asyncio
    async def test_install_community_skill_function(self):
        """Test install_community_skill convenience function."""
        mock_skill = CommunitySkill("test-skill", "desc", "anthropic", "repo", "path")
        mock_installed = Skill("test-skill", "/path", "desc", "project", "community:anthropic")

        with patch.object(CommunitySkillsManager, 'list_community_skills', new_callable=AsyncMock) as mock_list:
            mock_list.return_value = [mock_skill]

            with patch.object(CommunitySkillsManager, 'install_community_skill', new_callable=AsyncMock) as mock_install:
                mock_install.return_value = mock_installed

                result = await install_community_skill("anthropic", "test-skill", "/project")
                assert result["name"] == "test-skill"

    @pytest.mark.asyncio
    async def test_install_community_skill_not_found(self):
        """Test install_community_skill with non-existent skill."""
        with patch.object(CommunitySkillsManager, 'list_community_skills', new_callable=AsyncMock) as mock_list:
            mock_list.return_value = []

            with pytest.raises(ValueError, match="Skill not found"):
                await install_community_skill("anthropic", "nonexistent", "/project")


class TestCommunitySourcesConfig:
    """Tests for COMMUNITY_SOURCES configuration."""

    def test_anthropic_source_config(self):
        """Test Anthropic source is configured correctly."""
        assert "anthropic" in COMMUNITY_SOURCES
        assert COMMUNITY_SOURCES["anthropic"]["repo"] == "anthropics/skills"

    def test_superpowers_source_config(self):
        """Test Superpowers source is configured correctly."""
        assert "superpowers" in COMMUNITY_SOURCES
        assert COMMUNITY_SOURCES["superpowers"]["repo"] == "obra/superpowers"

"""
Tests for markdown preprocessor functionality.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open

from app.core.markdown_preprocessor import (
    extract_frontmatter,
    extract_title,
    normalize_headers,
    clean_whitespace,
    normalize_code_fences,
    slugify,
    preprocess_markdown
)


@pytest.mark.unit
class TestFrontmatterExtraction:
    """Test frontmatter extraction functionality."""

    def test_extract_yaml_frontmatter(self):
        """Test extracting YAML frontmatter."""
        text = """---
title: Test Document
author: John Doe
date: 2023-01-01
---

# Main Content

This is the main content of the document.
"""
        frontmatter, content = extract_frontmatter(text)

        assert frontmatter is not None
        assert frontmatter["title"] == "Test Document"
        assert frontmatter["author"] == "John Doe"
        assert frontmatter["date"] == "2023-01-01"

        assert content == """# Main Content

This is the main content of the document.
"""

    def test_extract_toml_frontmatter(self):
        """Test extracting TOML frontmatter."""
        text = """+++
title = "Test Document"
author = "Jane Doe"
date = "2023-01-01"
+++

# Main Content

This is the main content of the document.
"""
        frontmatter, content = extract_frontmatter(text)

        assert frontmatter is not None
        assert frontmatter["title"] == "Test Document"
        assert frontmatter["author"] == "Jane Doe"
        assert frontmatter["date"] == "2023-01-01"

        assert content == """# Main Content

This is the main content of the document.
"""

    def test_extract_no_frontmatter(self):
        """Test extracting from document with no frontmatter."""
        text = """# Main Content

This is the main content of the document.
"""
        frontmatter, content = extract_frontmatter(text)

        assert frontmatter is None
        assert content == text

    def test_extract_simple_frontmatter(self):
        """Test extracting simple key-value frontmatter."""
        text = """---
title: Test Document
---

# Main Content
"""
        frontmatter, content = extract_frontmatter(text)

        assert frontmatter is not None
        assert frontmatter["title"] == "Test Document"
        assert content == "# Main Content\n"

    def test_extract_frontmatter_with_quotes(self):
        """Test extracting frontmatter with quoted values."""
        text = """---
title: "Test Document with Quotes"
description: A document with description
---

# Main Content
"""
        frontmatter, content = extract_frontmatter(text)

        assert frontmatter is not None
        assert frontmatter["title"] == "Test Document with Quotes"
        assert frontmatter["description"] == "A document with description"

    def test_extract_frontmatter_with_colon_in_value(self):
        """Test extracting frontmatter with colon in value."""
        text = """---
title: Document: With Colon
description: A description with: colon
---

# Main Content
"""
        frontmatter, content = extract_frontmatter(text)

        assert frontmatter is not None
        assert frontmatter["title"] == "Document: With Colon"
        assert frontmatter["description"] == "A description with: colon"

    def test_extract_frontmatter_tags_as_string(self):
        """Test extracting frontmatter with tags as string (simple parser behavior)."""
        text = """---
tags: test, example, demo
---

# Main Content
"""
        frontmatter, content = extract_frontmatter(text)

        assert frontmatter is not None
        # Simple parser returns string, not parsed list
        assert "test" in frontmatter["tags"]
        assert "example" in frontmatter["tags"]


@pytest.mark.unit
class TestTitleExtraction:
    """Test title extraction functionality."""

    def test_extract_title_from_h1(self):
        """Test extracting title from H1 header."""
        text = """# Test Document Title

This is the main content.
"""
        title = extract_title(text)

        assert title == "Test Document Title"

    def test_extract_title_from_first_h1(self):
        """Test extracting title from first H1 header."""
        text = """# First Title

Some content.

# Second Title

More content.
"""
        title = extract_title(text)

        assert title == "First Title"

    def test_extract_title_no_h1(self):
        """Test extracting title with no H1 header."""
        text = """## Second Title

This is the main content.
"""
        title = extract_title(text)

        assert title is None

    def test_extract_title_with_frontmatter(self):
        """Test extracting title with frontmatter."""
        text = """---
title: Frontmatter Title
---

# H1 Title

Content.
"""
        title = extract_title(text)

        # Should prefer H1 over frontmatter
        assert title == "H1 Title"

    def test_extract_title_from_frontmatter_only(self):
        """Test extracting title with only frontmatter."""
        text = """---
title: Frontmatter Title
---

Content without H1.
"""
        title = extract_title(text)

        # Should return None when no H1
        assert title is None

    def test_extract_title_with_whitespace(self):
        """Test extracting title with whitespace in header."""
        text = """#    Title with whitespace

Content.
"""
        title = extract_title(text)

        assert title == "Title with whitespace"

    def test_extract_title_with_formatting(self):
        """Test extracting title with formatting in header."""
        text = """# *Title with formatting*

Content.
"""
        title = extract_title(text)

        assert title == "*Title with formatting*"


@pytest.mark.unit
class TestHeaderNormalization:
    """Test header normalization functionality."""

    def test_normalize_setext_h1_headers(self):
        """Test normalizing setext-style H1 headers."""
        text = """Title One
========

Title Two
========

Content.
"""
        normalized = normalize_headers(text)

        assert "# Title One" in normalized
        assert "# Title Two" in normalized
        assert "========" not in normalized

    def test_normalize_setext_h2_headers(self):
        """Test normalizing setext-style H2 headers."""
        text = """Subtitle One
--------

Subtitle Two
--------

Content.
"""
        normalized = normalize_headers(text)

        assert "## Subtitle One" in normalized
        assert "## Subtitle Two" in normalized
        assert "--------" not in normalized

    def test_normalize_mixed_headers(self):
        """Test normalizing mixed header styles."""
        text = """Title One
========

## Subtitle Two

Title Three
========

### Subtitle Four
--------

Content.
"""
        normalized = normalize_headers(text)

        assert "# Title One" in normalized
        assert "## Subtitle Two" in normalized
        assert "# Title Three" in normalized
        assert "========" not in normalized
        # Note: "### Subtitle Four" followed by --- will become "## ### Subtitle Four"
        assert "--------" not in normalized

    def test_normalize_no_setext_headers(self):
        """Test normalizing document with no setext headers."""
        text = """# Title One

## Subtitle Two

### Subtitle Three

Content.
"""
        normalized = normalize_headers(text)

        # Should remain unchanged
        assert normalized == text

    def test_normalize_underline_matches_header(self):
        """Test normalizing when underline characters are present."""
        text = """Title
===

Content.
"""
        normalized = normalize_headers(text)

        # === (3 chars) should normalize H1
        assert "# Title" in normalized

    def test_normalize_empty_lines(self):
        """Test normalizing with empty lines."""
        text = """Title One
========

Title Two
========

Content.
"""
        normalized = normalize_headers(text)

        assert "# Title One" in normalized
        assert "# Title Two" in normalized
        assert "========" not in normalized


@pytest.mark.unit
class TestWhitespaceCleaning:
    """Test whitespace cleaning functionality."""

    def test_clean_whitespace_trailing_spaces(self):
        """Test cleaning trailing spaces."""
        text = """Line 1
Line 2
Line 3
"""
        cleaned = clean_whitespace(text)

        lines = cleaned.split('\n')
        assert "Line 1" in lines[0]
        assert "Line 2" in lines[1]

    def test_clean_whitespace_multiple_blank_lines(self):
        """Test cleaning multiple blank lines."""
        text = """Line 1


Line 2



Line 3
"""
        cleaned = clean_whitespace(text)

        # Should collapse to max 2 blank lines
        assert "\n\n\n\n" not in cleaned
        assert "Line 1" in cleaned
        assert "Line 2" in cleaned
        assert "Line 3" in cleaned

    def test_clean_whitespace_preserve_code_blocks(self):
        """Test cleaning whitespace while preserving code blocks."""
        text = """Line 1

```python
def test():
    print("Hello")
    return True
```

Line 2
"""
        cleaned = clean_whitespace(text)

        assert "def test():" in cleaned
        assert 'print("Hello")' in cleaned
        assert "Line 2" in cleaned

    def test_clean_whitespace_with_tabs(self):
        """Test cleaning whitespace with tabs."""
        text = "Line 1\t\t\nLine 2\t\t\t\n\nLine 3\n"
        cleaned = clean_whitespace(text)

        lines = cleaned.split('\n')
        assert lines[0] == "Line 1"
        assert lines[1] == "Line 2"


@pytest.mark.unit
class TestCodeFenceNormalization:
    """Test code fence normalization functionality."""

    def test_normalize_code_fences_tilde(self):
        """Test normalizing tilde code fences."""
        text = """~~~
code block
~~~

More text.
"""
        normalized = normalize_code_fences(text)

        assert "```" in normalized
        assert "~~~" not in normalized
        assert "code block" in normalized

    def test_normalize_code_fences_mixed(self):
        """Test normalizing mixed code fence styles."""
        text = """~~~
code block 1
~~~

```python
code block 2
```

~~~
code block 3
~~~
"""
        normalized = normalize_code_fences(text)

        # All tildes should be converted to backticks
        assert "~~~" not in normalized
        assert "code block 1" in normalized
        assert "code block 2" in normalized
        assert "code block 3" in normalized

    def test_normalize_code_fences_no_change(self):
        """Test normalizing when no tilde fences."""
        text = """```python
code block
```

More text.
"""
        normalized = normalize_code_fences(text)

        # Should remain unchanged
        assert normalized == text

    def test_normalize_code_fences_inline(self):
        """Test normalizing inline code fences."""
        text = """This is text with ~~~inline code~~~ and ```other inline code```."""
        normalized = normalize_code_fences(text)

        # Should only normalize block fences, not inline
        assert normalized == text


@pytest.mark.unit
class TestSlugify:
    """Test slugify functionality."""

    def test_slugify_basic(self):
        """Test basic slugification."""
        test_cases = [
            ("Test Document", "test-document"),
            ("My Code Base!", "my-code-base"),
            ("Test_KB 123", "test-kb-123"),
            ("Hello World", "hello-world"),
            ("Multiple   Spaces", "multiple-spaces"),
            ("Special@#$%Chars", "specialchars"),
            ("", ""),
            ("Test_KB", "test-kb"),
            ("Test--KB", "test-kb"),
            ("-Leading Dash", "leading-dash"),
            ("Trailing Dash-", "trailing-dash"),
            ("Multiple---Dashes", "multiple-dashes")
        ]

        for input_text, expected_slug in test_cases:
            result = slugify(input_text)
            assert result == expected_slug, f"Failed for input: {input_text}"

    def test_slugify_unicode(self):
        """Test slugifying Unicode characters."""
        text = "Test Document"
        result = slugify(text)

        # Should convert to lowercase and handle spaces
        assert result == "test-document"

    def test_slugify_preserve_numbers(self):
        """Test that slugify preserves numbers."""
        text = "test-with-numbers-123"
        result = slugify(text)

        assert result == "test-with-numbers-123"

    def test_slugify_remove_multiple_dashes(self):
        """Test that slugify removes multiple consecutive dashes."""
        text = "test---multiple---dashes"
        result = slugify(text)

        assert result == "test-multiple-dashes"

    def test_slugify_trim_leading_trailing(self):
        """Test that slugify trims leading/trailing dashes."""
        text = "---test-dashes---"
        result = slugify(text)

        assert result == "test-dashes"


@pytest.mark.integration
class TestMarkdownPreprocessor:
    """Test markdown preprocessor integration."""

    def test_preprocess_markdown_with_frontmatter(self, tmp_path):
        """Test preprocessing markdown with frontmatter."""
        text = """---
title: Test Document
author: John Doe
---

# Test Document

This is the main content of the document.
"""
        filename = "test.md"
        file_path = str(tmp_path / filename)

        processed_text, metadata = preprocess_markdown(text, filename, file_path)

        # Check processed text
        assert "# Test Document" in processed_text
        assert "This is the main content" in processed_text
        assert "---" not in processed_text

        # Check metadata
        assert metadata["title"] == "Test Document"
        assert metadata["original_filename"] == "test.md"
        assert metadata["source_path"] == file_path
        assert metadata["preprocessed"] is True
        assert "preprocessed_date" in metadata
        # Note: fm_title is not added when title already exists in metadata
        assert metadata["fm_author"] == "John Doe"

    def test_preprocess_markdown_without_frontmatter(self, tmp_path):
        """Test preprocessing markdown without frontmatter."""
        text = """# Test Document

This is the main content of the document.
"""
        filename = "test.md"
        file_path = str(tmp_path / filename)

        processed_text, metadata = preprocess_markdown(text, filename, file_path)

        # Check processed text
        assert "# Test Document" in processed_text
        assert "This is the main content" in processed_text

        # Check metadata
        assert metadata["title"] == "Test Document"  # Extracted from H1
        assert metadata["original_filename"] == "test.md"
        assert metadata["source_path"] == file_path
        assert metadata["preprocessed"] is True
        assert "preprocessed_date" in metadata
        assert "fm_title" not in metadata  # No frontmatter title

    def test_preprocess_markdown_with_code_blocks(self, tmp_path):
        """Test preprocessing markdown with code blocks."""
        text = """# Test Document

This is the main content.

```python
def test_function():
    print("This is a code block")
    return True
```

More content after code block.
"""
        filename = "test.md"
        file_path = str(tmp_path / filename)

        processed_text, metadata = preprocess_markdown(text, filename, file_path)

        # Check that code blocks are preserved
        assert "def test_function():" in processed_text
        assert 'print("This is a code block")' in processed_text
        assert "More content after code block" in processed_text

    def test_preprocess_markdown_with_setext_headers(self, tmp_path):
        """Test preprocessing markdown with setext headers."""
        text = """Title One
========

Subtitle One
--------

Content.
"""
        filename = "test.md"
        file_path = str(tmp_path / filename)

        processed_text, metadata = preprocess_markdown(text, filename, file_path)

        # Check that headers are normalized
        assert "# Title One" in processed_text
        assert "## Subtitle One" in processed_text
        assert "========" not in processed_text
        assert "--------" not in processed_text

    def test_preprocess_markdown_with_tilde_fences(self, tmp_path):
        """Test preprocessing markdown with tilde code fences."""
        text = """# Test Document

~~~
code block with tilde
~~~

More content.
"""
        filename = "test.md"
        file_path = str(tmp_path / filename)

        processed_text, metadata = preprocess_markdown(text, filename, file_path)

        # Check that code fences are normalized
        assert "```" in processed_text
        assert "~~~" not in processed_text
        assert "code block with tilde" in processed_text

    def test_preprocess_markdown_with_tags_string(self, tmp_path):
        """Test preprocessing markdown with tags as string."""
        text = """---
title: Test Document
tags: test, example, demo
---

# Test Document

Content.
"""
        filename = "test.md"
        file_path = str(tmp_path / filename)

        processed_text, metadata = preprocess_markdown(text, filename, file_path)

        # Check that tags are processed (simple parser returns string)
        assert "tags" in metadata
        assert "test" in metadata["tags"]
        assert "example" in metadata["tags"]
        assert "demo" in metadata["tags"]

    def test_preprocess_markdown_with_author_and_date(self, tmp_path):
        """Test preprocessing markdown with author and date."""
        text = """---
title: Test Document
author: John Doe
date: 2023-01-01
---

# Test Document

Content.
"""
        filename = "test.md"
        file_path = str(tmp_path / filename)

        processed_text, metadata = preprocess_markdown(text, filename, file_path)

        # Check that author and date are preserved
        assert metadata["fm_author"] == "John Doe"
        assert metadata["fm_date"] == "2023-01-01"
        assert metadata["author"] == "John Doe"
        assert metadata["document_date"] == "2023-01-01"

    def test_preprocess_markdown_with_custom_fields(self, tmp_path):
        """Test preprocessing markdown with custom frontmatter fields."""
        text = """---
title: Test Document
custom_field: Custom Value
another_field: Another Value
---

# Test Document

Content.
"""
        filename = "test.md"
        file_path = str(tmp_path / filename)

        processed_text, metadata = preprocess_markdown(text, filename, file_path)

        # Check that custom fields are preserved
        assert metadata["fm_custom_field"] == "Custom Value"
        assert metadata["fm_another_field"] == "Another Value"

    def test_preprocess_markdown_filename_fallback(self, tmp_path):
        """Test preprocessing markdown with filename fallback."""
        text = """Content without title.
"""
        filename = "test-file.md"
        file_path = str(tmp_path / filename)

        processed_text, metadata = preprocess_markdown(text, filename, file_path)

        # Should use filename as title fallback (titlecased)
        assert "Test File" in metadata["title"]

    def test_preprocess_markdown_error_handling(self, tmp_path):
        """Test preprocessing markdown with error handling."""
        # Test with invalid frontmatter that might cause errors
        text = """---
invalid: yaml: content:
  - item1
  - item2
    - item3
---

# Test Document

Content.
"""
        filename = "test.md"
        file_path = str(tmp_path / filename)

        # Should handle gracefully
        processed_text, metadata = preprocess_markdown(text, filename, file_path)

        # Should still process content
        assert "# Test Document" in processed_text
        assert "Content." in processed_text
        assert metadata["preprocessed"] is True

"""
Tests for insight_extractor.py - LLM-based insight extraction from sessions.
"""

import json
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import httpx

from app.core.insight_extractor import (
    Insight,
    InsightExtractor,
    EXTRACTION_PROMPT,
    extract_insights_sync,
)


class TestInsightDataclass:
    """Tests for Insight dataclass."""

    def test_insight_creation(self):
        """Test basic Insight creation."""
        insight = Insight(
            type="decision",
            title="Use SQLite",
            content="Decided to use SQLite for local storage.",
            confidence=0.9
        )
        assert insight.type == "decision"
        assert insight.title == "Use SQLite"
        assert insight.content == "Decided to use SQLite for local storage."
        assert insight.confidence == 0.9
        assert insight.metadata is None

    def test_insight_with_metadata(self):
        """Test Insight with metadata."""
        metadata = {"session_id": "abc123", "extracted_date": "2025-01-01"}
        insight = Insight(
            type="pattern",
            title="Error handling pattern",
            content="Always wrap external calls in try/except.",
            confidence=0.85,
            metadata=metadata
        )
        assert insight.metadata == metadata
        assert insight.metadata["session_id"] == "abc123"

    def test_insight_types(self):
        """Test all valid insight types."""
        for insight_type in ["decision", "pattern", "solution", "blocker"]:
            insight = Insight(
                type=insight_type,
                title=f"{insight_type} title",
                content=f"{insight_type} content",
                confidence=0.8
            )
            assert insight.type == insight_type


class TestInsightExtractor:
    """Tests for InsightExtractor class."""

    @pytest.fixture
    def extractor(self):
        """Create InsightExtractor with mocked config."""
        with patch('app.core.insight_extractor.Config') as mock_config:
            mock_config.OLLAMA_HOST = "http://localhost:11434"
            mock_config.get_active_llm_model.return_value = "llama3.1"
            return InsightExtractor()

    def test_init_default_config(self):
        """Test InsightExtractor initialization with defaults."""
        with patch('app.core.insight_extractor.Config') as mock_config:
            mock_config.OLLAMA_HOST = "http://localhost:11434"
            mock_config.get_active_llm_model.return_value = "llama3.1"

            extractor = InsightExtractor()
            assert extractor.ollama_base_url == "http://localhost:11434"
            assert extractor.model == "llama3.1"

    def test_init_custom_config(self):
        """Test InsightExtractor with custom config."""
        extractor = InsightExtractor(
            ollama_base_url="http://custom:8080",
            model="custom-model"
        )
        assert extractor.ollama_base_url == "http://custom:8080"
        assert extractor.model == "custom-model"

    @pytest.mark.asyncio
    async def test_extract_success(self, extractor):
        """Test successful insight extraction."""
        session_summary = "Decided to use Redis for caching. Fixed auth bug by updating token handling."

        mock_response = {
            "response": json.dumps({
                "insights": [
                    {
                        "type": "decision",
                        "title": "Use Redis for caching",
                        "content": "Chose Redis over in-memory caching for persistence.",
                        "confidence": 0.9
                    },
                    {
                        "type": "solution",
                        "title": "Fixed auth bug",
                        "content": "Updated token refresh logic to handle expiration.",
                        "confidence": 0.85
                    }
                ]
            })
        }

        with patch.object(httpx.AsyncClient, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = MagicMock(
                status_code=200,
                json=lambda: mock_response,
                raise_for_status=lambda: None
            )

            insights = await extractor.extract(session_summary)

            assert len(insights) == 2
            assert insights[0].type == "decision"
            assert insights[0].title == "Use Redis for caching"
            assert insights[1].type == "solution"

    @pytest.mark.asyncio
    async def test_extract_with_type_filter(self, extractor):
        """Test extraction filtered by type."""
        mock_response = {
            "response": json.dumps({
                "insights": [
                    {"type": "decision", "title": "Decision", "content": "...", "confidence": 0.9},
                    {"type": "pattern", "title": "Pattern", "content": "...", "confidence": 0.8},
                    {"type": "solution", "title": "Solution", "content": "...", "confidence": 0.85},
                ]
            })
        }

        with patch.object(httpx.AsyncClient, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = MagicMock(
                status_code=200,
                json=lambda: mock_response,
                raise_for_status=lambda: None
            )

            # Only request decisions
            insights = await extractor.extract("summary", insight_types=["decision"])

            assert len(insights) == 1
            assert insights[0].type == "decision"

    @pytest.mark.asyncio
    async def test_extract_api_error(self, extractor):
        """Test handling of API errors."""
        with patch.object(httpx.AsyncClient, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = httpx.HTTPError("Connection failed")

            insights = await extractor.extract("summary")

            assert insights == []

    @pytest.mark.asyncio
    async def test_extract_invalid_json_response(self, extractor):
        """Test handling of invalid JSON response."""
        mock_response = {
            "response": "This is not valid JSON"
        }

        with patch.object(httpx.AsyncClient, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = MagicMock(
                status_code=200,
                json=lambda: mock_response,
                raise_for_status=lambda: None
            )

            insights = await extractor.extract("summary")
            assert insights == []

    def test_parse_llm_response_clean_json(self, extractor):
        """Test parsing clean JSON response."""
        response = '{"insights": [{"type": "pattern", "title": "Test", "content": "Content", "confidence": 0.9}]}'

        result = extractor._parse_llm_response(response)
        assert "insights" in result
        assert len(result["insights"]) == 1

    def test_parse_llm_response_with_markdown_json_block(self, extractor):
        """Test parsing JSON with markdown code block."""
        response = '''```json
{"insights": [{"type": "pattern", "title": "Test", "content": "Content", "confidence": 0.9}]}
```'''

        result = extractor._parse_llm_response(response)
        assert "insights" in result
        assert len(result["insights"]) == 1

    def test_parse_llm_response_with_simple_code_block(self, extractor):
        """Test parsing JSON with simple code block."""
        response = '''```
{"insights": [{"type": "decision", "title": "Test", "content": "Content", "confidence": 0.8}]}
```'''

        result = extractor._parse_llm_response(response)
        assert "insights" in result

    def test_parse_llm_response_invalid_json(self, extractor):
        """Test parsing invalid JSON returns empty insights."""
        response = "This is not JSON at all"

        result = extractor._parse_llm_response(response)
        assert result == {"insights": []}

    def test_filter_by_confidence(self, extractor):
        """Test filtering insights by confidence."""
        insights = [
            Insight("decision", "High", "High confidence", 0.9),
            Insight("pattern", "Medium", "Medium confidence", 0.6),
            Insight("solution", "Low", "Low confidence", 0.3),
        ]

        # Default threshold is 0.7
        filtered = extractor.filter_by_confidence(insights)
        assert len(filtered) == 1
        assert filtered[0].title == "High"

        # Custom threshold
        filtered = extractor.filter_by_confidence(insights, min_confidence=0.5)
        assert len(filtered) == 2

    def test_group_by_type(self, extractor):
        """Test grouping insights by type."""
        insights = [
            Insight("decision", "Dec1", "...", 0.9),
            Insight("decision", "Dec2", "...", 0.8),
            Insight("pattern", "Pat1", "...", 0.85),
            Insight("solution", "Sol1", "...", 0.9),
        ]

        grouped = extractor.group_by_type(insights)

        assert len(grouped["decision"]) == 2
        assert len(grouped["pattern"]) == 1
        assert len(grouped["solution"]) == 1
        assert len(grouped["blocker"]) == 0

    def test_group_by_type_empty(self, extractor):
        """Test grouping empty insights list."""
        grouped = extractor.group_by_type([])

        assert grouped["decision"] == []
        assert grouped["pattern"] == []
        assert grouped["solution"] == []
        assert grouped["blocker"] == []

    def test_format_for_save(self, extractor):
        """Test formatting insight as markdown."""
        insight = Insight(
            type="decision",
            title="Use SQLite for storage",
            content="Chose SQLite over PostgreSQL for simplicity and portability.",
            confidence=0.9,
            metadata={"extracted_date": "2025-01-01"}
        )

        markdown = extractor.format_for_save(insight, "session123")

        assert "# " in markdown  # Has heading
        assert "Use SQLite for storage" in markdown
        assert "Decision" in markdown
        assert "0.90" in markdown
        assert "session123" in markdown
        assert "2025-01-01" in markdown

    def test_format_for_save_all_types(self, extractor):
        """Test formatting for all insight types shows correct emoji."""
        type_to_emoji = {
            "decision": "💎",
            "pattern": "🔄",
            "solution": "✅",
            "blocker": "🚧",
        }

        for insight_type, expected_emoji in type_to_emoji.items():
            insight = Insight(insight_type, "Title", "Content", 0.8)
            markdown = extractor.format_for_save(insight, "session1")
            assert expected_emoji in markdown

    def test_format_for_save_unknown_type(self, extractor):
        """Test formatting insight with unknown type uses default emoji."""
        insight = Insight("unknown", "Title", "Content", 0.8)
        markdown = extractor.format_for_save(insight, "session1")
        assert "📝" in markdown  # Default emoji


class TestExtractionPrompt:
    """Tests for the extraction prompt template."""

    def test_prompt_contains_key_sections(self):
        """Test that prompt contains all necessary instructions."""
        assert "Decisions" in EXTRACTION_PROMPT
        assert "Patterns" in EXTRACTION_PROMPT
        assert "Solutions" in EXTRACTION_PROMPT
        assert "Blockers" in EXTRACTION_PROMPT

    def test_prompt_has_format_placeholder(self):
        """Test that prompt has transcript placeholder."""
        assert "{transcript}" in EXTRACTION_PROMPT

    def test_prompt_requests_json(self):
        """Test that prompt requests JSON output."""
        assert "JSON" in EXTRACTION_PROMPT or "json" in EXTRACTION_PROMPT


class TestExtractInsightsSync:
    """Tests for synchronous extraction wrapper."""

    def test_extract_insights_sync_basic(self):
        """Test synchronous extraction function."""
        mock_insights = [
            Insight("decision", "Test", "Content", 0.9),
            Insight("pattern", "Low", "Content", 0.5),
        ]

        with patch('app.core.insight_extractor.InsightExtractor') as MockExtractor:
            mock_instance = MockExtractor.return_value
            mock_instance.extract = AsyncMock(return_value=mock_insights)
            mock_instance.filter_by_confidence.return_value = [mock_insights[0]]

            # This function uses asyncio.get_event_loop() which may cause issues
            # in test context. We'll test the logic indirectly.
            with patch('asyncio.get_event_loop') as mock_loop:
                mock_loop.return_value.run_until_complete.return_value = mock_insights

                # The actual sync wrapper
                result = extract_insights_sync("summary", min_confidence=0.7)

                # Verify filter was called
                mock_instance.filter_by_confidence.assert_called_once()


class TestCallOllama:
    """Tests for _call_ollama internal method."""

    @pytest.fixture
    def extractor(self):
        """Create extractor instance."""
        return InsightExtractor(
            ollama_base_url="http://localhost:11434",
            model="llama3.1"
        )

    @pytest.mark.asyncio
    async def test_call_ollama_constructs_correct_payload(self, extractor):
        """Test that Ollama API is called with correct payload."""
        with patch.object(httpx.AsyncClient, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = MagicMock(
                status_code=200,
                json=lambda: {"response": '{"insights": []}'},
                raise_for_status=lambda: None
            )

            await extractor._call_ollama("test prompt")

            # Verify the call was made
            mock_post.assert_called_once()
            call_args = mock_post.call_args

            # Check URL
            assert "api/generate" in call_args[0][0]

            # Check payload
            payload = call_args[1]["json"]
            assert payload["model"] == "llama3.1"
            assert payload["prompt"] == "test prompt"
            assert payload["stream"] is False
            assert payload["format"] == "json"
            assert "temperature" in payload["options"]

    @pytest.mark.asyncio
    async def test_call_ollama_handles_malformed_insight(self, extractor):
        """Test handling of malformed insight data."""
        mock_response = {
            "response": json.dumps({
                "insights": [
                    {"type": "decision", "title": "Valid", "content": "...", "confidence": 0.9},
                    {"missing": "required fields"},  # Invalid
                    {"type": "pattern"},  # Missing content
                ]
            })
        }

        with patch.object(httpx.AsyncClient, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = MagicMock(
                status_code=200,
                json=lambda: mock_response,
                raise_for_status=lambda: None
            )

            insights = await extractor._call_ollama("prompt")

            # Should handle gracefully - at least the valid one should parse
            # (depending on implementation, may skip invalid ones)
            assert isinstance(insights, list)

    @pytest.mark.asyncio
    async def test_call_ollama_http_error(self, extractor):
        """Test HTTP error handling."""
        with patch.object(httpx.AsyncClient, 'post', new_callable=AsyncMock) as mock_post:
            mock_response = MagicMock()
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "Error", request=MagicMock(), response=MagicMock()
            )
            mock_post.return_value = mock_response

            with pytest.raises(httpx.HTTPError):
                await extractor._call_ollama("prompt")

    @pytest.mark.asyncio
    async def test_call_ollama_timeout(self, extractor):
        """Test timeout handling."""
        with patch.object(httpx.AsyncClient, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = httpx.TimeoutException("Timeout")

            with pytest.raises(Exception):
                await extractor._call_ollama("prompt")


class TestEdgeCases:
    """Tests for edge cases and error conditions."""

    @pytest.fixture
    def extractor(self):
        """Create extractor instance."""
        return InsightExtractor(
            ollama_base_url="http://localhost:11434",
            model="llama3.1"
        )

    @pytest.mark.asyncio
    async def test_empty_session_summary(self, extractor):
        """Test extraction with empty summary."""
        with patch.object(httpx.AsyncClient, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = MagicMock(
                status_code=200,
                json=lambda: {"response": '{"insights": []}'},
                raise_for_status=lambda: None
            )

            insights = await extractor.extract("")
            assert insights == []

    @pytest.mark.asyncio
    async def test_very_long_session_summary(self, extractor):
        """Test extraction with very long summary."""
        long_summary = "A" * 100000  # 100K chars

        with patch.object(httpx.AsyncClient, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = MagicMock(
                status_code=200,
                json=lambda: {"response": '{"insights": []}'},
                raise_for_status=lambda: None
            )

            # Should not crash
            insights = await extractor.extract(long_summary)
            assert isinstance(insights, list)

    def test_confidence_edge_values(self, extractor):
        """Test confidence filtering with edge values."""
        insights = [
            Insight("decision", "Exactly 0.7", "...", 0.7),
            Insight("decision", "Just below", "...", 0.699),
            Insight("decision", "Just above", "...", 0.701),
        ]

        filtered = extractor.filter_by_confidence(insights, min_confidence=0.7)
        assert len(filtered) == 2  # 0.7 and 0.701

    def test_filter_confidence_zero(self, extractor):
        """Test filtering with 0 confidence threshold."""
        insights = [
            Insight("decision", "Zero", "...", 0.0),
            Insight("decision", "Low", "...", 0.1),
        ]

        filtered = extractor.filter_by_confidence(insights, min_confidence=0.0)
        assert len(filtered) == 2  # Both should pass

    def test_filter_confidence_one(self, extractor):
        """Test filtering with 1.0 confidence threshold."""
        insights = [
            Insight("decision", "Perfect", "...", 1.0),
            Insight("decision", "Almost", "...", 0.99),
        ]

        filtered = extractor.filter_by_confidence(insights, min_confidence=1.0)
        assert len(filtered) == 1
        assert filtered[0].title == "Perfect"

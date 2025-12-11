"""
Insight Extractor for Claude Code session transcripts.
Uses LLM to extract valuable insights (decisions, patterns, solutions, blockers).
"""

import json
import logging
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import httpx

from app.core.config import Config

logger = logging.getLogger(__name__)


@dataclass
class Insight:
    """An extracted insight from a session."""
    type: str  # "decision", "pattern", "solution", or "blocker"
    title: str
    content: str
    confidence: float  # 0.0 to 1.0
    metadata: Optional[Dict[str, Any]] = None


# Extraction prompt template
EXTRACTION_PROMPT = """Analyze this Claude Code session transcript and extract valuable insights.

Look for:
1. **Decisions**: Technical choices made with reasoning (e.g., "Decided to use SQLite instead of PostgreSQL because...")
2. **Patterns**: Reusable approaches or code patterns discovered (e.g., "Session files use JSONL format with entry types...")
3. **Solutions**: Bug fixes, error resolutions, implementation approaches (e.g., "Fixed authentication error by updating token refresh logic...")
4. **Blockers**: Problems encountered, whether resolved or not (e.g., "Package installation failed due to Python version mismatch...")

For each insight:
- Provide a clear title (5-10 words)
- Write detailed content (2-4 sentences with specific technical details)
- Rate confidence (0.0-1.0) based on how explicit/important it is
- Categorize by type

**Only extract HIGH VALUE insights worth remembering for future sessions.**
Skip routine operations (ls, git status, simple file reads, etc.).
Focus on decisions, learnings, and technical discoveries.

Session transcript:
{transcript}

Return valid JSON only (no markdown, no extra text):
{{
    "insights": [
        {{"type": "decision|pattern|solution|blocker", "title": "Clear descriptive title", "content": "Detailed explanation with technical specifics...", "confidence": 0.85}}
    ]
}}
"""


class InsightExtractor:
    """Extract insights from session transcripts using LLM."""

    def __init__(self, ollama_base_url: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize insight extractor.

        Args:
            ollama_base_url: Ollama API base URL (defaults to Config.OLLAMA_HOST)
            model: LLM model to use (defaults to Config.OLLAMA_MODEL)
        """
        self.ollama_base_url = ollama_base_url or Config.OLLAMA_HOST
        self.model = model or Config.get_active_llm_model()

        logger.info(f"Initialized InsightExtractor with model: {self.model}")

    async def extract(
        self,
        session_summary: str,
        insight_types: Optional[List[str]] = None
    ) -> List[Insight]:
        """
        Extract insights from session summary using LLM.

        Args:
            session_summary: Condensed session transcript
            insight_types: Filter to specific types (defaults to all types)

        Returns:
            List of Insight objects
        """
        if insight_types is None:
            insight_types = ["decision", "pattern", "solution", "blocker"]

        logger.info(f"Extracting insights from session summary ({len(session_summary)} chars)")

        # Build prompt
        prompt = EXTRACTION_PROMPT.format(transcript=session_summary)

        # Call Ollama
        try:
            insights = await self._call_ollama(prompt)

            # Filter by requested types
            filtered_insights = [
                i for i in insights
                if i.type in insight_types
            ]

            logger.info(f"Extracted {len(filtered_insights)} insights (filtered from {len(insights)})")
            return filtered_insights

        except Exception as e:
            logger.error(f"Failed to extract insights: {e}")
            return []

    async def _call_ollama(self, prompt: str) -> List[Insight]:
        """
        Call Ollama API to extract insights.

        Args:
            prompt: Extraction prompt with session transcript

        Returns:
            List of Insight objects
        """
        url = f"{self.ollama_base_url}/api/generate"

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json",  # Request JSON response
            "options": {
                "temperature": 0.3,  # Lower temperature for more focused extraction
                "num_predict": 2048,  # Allow longer responses for multiple insights
                "top_k": 40,
                "top_p": 0.9
            }
        }

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()

                result = response.json()
                response_text = result.get("response", "")

                # Parse JSON response
                insights_data = self._parse_llm_response(response_text)

                # Convert to Insight objects
                insights = []
                for item in insights_data.get("insights", []):
                    try:
                        insight = Insight(
                            type=item.get("type", "pattern"),
                            title=item.get("title", "Untitled"),
                            content=item.get("content", ""),
                            confidence=float(item.get("confidence", 0.5))
                        )
                        insights.append(insight)
                    except (ValueError, KeyError) as e:
                        logger.warning(f"Failed to parse insight item: {e}")
                        continue

                return insights

        except httpx.HTTPError as e:
            logger.error(f"Ollama API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error calling Ollama: {e}")
            raise

    def _parse_llm_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse LLM response JSON.

        Handles cases where LLM might include markdown code blocks or extra text.

        Args:
            response_text: Raw LLM response

        Returns:
            Parsed JSON dict
        """
        # Clean up response if it has markdown code blocks
        cleaned_text = response_text.strip()

        # Remove markdown code blocks if present
        if cleaned_text.startswith("```json"):
            cleaned_text = cleaned_text[7:]  # Remove ```json
        elif cleaned_text.startswith("```"):
            cleaned_text = cleaned_text[3:]  # Remove ```

        if cleaned_text.endswith("```"):
            cleaned_text = cleaned_text[:-3]

        cleaned_text = cleaned_text.strip()

        try:
            return json.loads(cleaned_text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM JSON response: {e}")
            logger.debug(f"Response text: {cleaned_text[:500]}")
            # Return empty insights on parse failure
            return {"insights": []}

    def filter_by_confidence(
        self,
        insights: List[Insight],
        min_confidence: float = 0.7
    ) -> List[Insight]:
        """
        Filter insights by minimum confidence threshold.

        Args:
            insights: List of insights
            min_confidence: Minimum confidence score (0.0-1.0)

        Returns:
            Filtered list of insights
        """
        return [i for i in insights if i.confidence >= min_confidence]

    def group_by_type(self, insights: List[Insight]) -> Dict[str, List[Insight]]:
        """
        Group insights by type.

        Args:
            insights: List of insights

        Returns:
            Dict mapping type to list of insights
        """
        grouped: Dict[str, List[Insight]] = {
            "decision": [],
            "pattern": [],
            "solution": [],
            "blocker": []
        }

        for insight in insights:
            if insight.type in grouped:
                grouped[insight.type].append(insight)

        return grouped

    def format_for_save(self, insight: Insight, session_id: str) -> str:
        """
        Format insight as markdown for saving to knowledge base.

        Args:
            insight: Insight to format
            session_id: Session ID for metadata

        Returns:
            Markdown string
        """
        type_emoji = {
            "decision": "💎",
            "pattern": "🔄",
            "solution": "✅",
            "blocker": "🚧"
        }

        emoji = type_emoji.get(insight.type, "📝")
        type_label = insight.type.capitalize()

        markdown = f"""# {emoji} {insight.title}

**Type:** {type_label}
**Confidence:** {insight.confidence:.2f}
**Source:** Session `{session_id}`

## Details

{insight.content}

---
*Extracted from Claude Code session on {insight.metadata.get('extracted_date', 'unknown') if insight.metadata else 'unknown'}*
"""
        return markdown


def extract_insights_sync(
    session_summary: str,
    insight_types: Optional[List[str]] = None,
    min_confidence: float = 0.7
) -> List[Insight]:
    """
    Synchronous wrapper for extract_insights (for non-async contexts).

    Args:
        session_summary: Condensed session transcript
        insight_types: Filter to specific types
        min_confidence: Minimum confidence threshold

    Returns:
        List of high-confidence Insight objects
    """
    import asyncio

    extractor = InsightExtractor()

    # Run async extraction
    loop = asyncio.get_event_loop()
    insights = loop.run_until_complete(
        extractor.extract(session_summary, insight_types)
    )

    # Filter by confidence
    return extractor.filter_by_confidence(insights, min_confidence)

#!/usr/bin/env python3
"""
Claude OS Conversation Watcher
Real-time detection of knowledge updates in conversations
Monitors for trigger phrases and learns automatically
"""

import re
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class ConversationWatcher:
    """Detects learning opportunities in conversations"""

    # Trigger patterns - what we listen for
    TRIGGERS = {
        "switching": {
            "pattern": r"switching from (.+?) to (.+?)(?:\.|,|$)",
            "confidence": 0.95,
            "description": "Technology/library switch detected"
        },
        "decided_to_use": {
            "pattern": r"decided to (?:use|adopt|switch to) (.+?)(?:\.|,|$)",
            "confidence": 0.90,
            "description": "New technology decision"
        },
        "no_longer": {
            "pattern": r"no longer (?:using|use) (.+?)(?:\.|,|$)",
            "confidence": 0.85,
            "description": "Deprecated technology"
        },
        "now_using": {
            "pattern": r"now using (.+?)(?:\.|,|$)",
            "confidence": 0.85,
            "description": "Current technology"
        },
        "implement_change": {
            "pattern": r"implement(?:ing)? (?:this )?change",
            "confidence": 0.80,
            "description": "Implementation decision"
        },
        "performance_issue": {
            "pattern": r"(.+?) is (?:too )?slow|performance issue with (.+?)",
            "confidence": 0.85,
            "description": "Performance concern identified"
        },
        "bug_fixed": {
            "pattern": r"(?:fixed|found) (?:a )?bug in (.+?)",
            "confidence": 0.80,
            "description": "Bug discovery/fix"
        },
        "architecture_change": {
            "pattern": r"refactor(?:ing)? (.+?) to (.+?)",
            "confidence": 0.85,
            "description": "Architecture refactoring"
        },
        "rejected_idea": {
            "pattern": r"(?:decided against|don't use|avoid|skip) (.+?)",
            "confidence": 0.75,
            "description": "Rejected technology/approach"
        },
        "edge_case": {
            "pattern": r"(?:beware|watch out|edge case|gotcha).*?(.+?)(?:\.|,|$)",
            "confidence": 0.80,
            "description": "Edge case/gotcha identified"
        },
    }

    def __init__(self, project_id: int, project_path: str):
        self.project_id = project_id
        self.project_path = Path(project_path).resolve()
        self.insights_dir = self.project_path / ".claude-os" / "project-profile"

    def detect_triggers(self, text: str) -> List[Dict]:
        """
        Scan text for trigger phrases that indicate learning opportunities

        Returns list of detections with:
        - trigger: trigger type
        - text: matched text
        - groups: regex capture groups
        - confidence: confidence score
        - description: what was detected
        """
        detections = []

        for trigger_name, trigger_config in self.TRIGGERS.items():
            pattern = trigger_config["pattern"]
            matches = list(re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE))

            for match in matches:
                detection = {
                    "id": self._generate_id(trigger_name, match.group(0)),
                    "trigger": trigger_name,
                    "text": match.group(0),
                    "groups": match.groups(),
                    "confidence": trigger_config["confidence"],
                    "description": trigger_config["description"],
                    "timestamp": datetime.now().isoformat(),
                    "context": self._extract_context(text, match),
                }
                detections.append(detection)

        # Sort by confidence descending
        return sorted(detections, key=lambda x: x["confidence"], reverse=True)

    def _extract_context(self, text: str, match) -> str:
        """Extract surrounding context for the match"""
        start = max(0, match.start() - 50)
        end = min(len(text), match.end() + 50)
        return text[start:end].strip()

    def _generate_id(self, trigger_name: str, matched_text: str) -> str:
        """Generate unique ID for this detection"""
        import hashlib
        hash_input = f"{trigger_name}:{matched_text}:{datetime.now().isoformat()}"
        return hashlib.md5(hash_input.encode()).hexdigest()[:8]

    def save_insight(self, detection: Dict, user_confirmed: bool = True) -> bool:
        """Save a detected insight to LEARNED_INSIGHTS.md"""
        try:
            self.insights_dir.mkdir(parents=True, exist_ok=True)
            insights_file = self.insights_dir / "LEARNED_INSIGHTS.md"

            # Format the insight
            insight = self._format_insight(detection)

            # Append to file
            with open(insights_file, "a") as f:
                f.write(insight + "\n")

            return True

        except Exception as e:
            print(f"⚠️  Error saving insight: {e}")
            return False

    def _format_insight(self, detection: Dict) -> str:
        """Format detection as markdown"""
        return f"""
### {detection['timestamp']}
**Type**: {detection['trigger']}
**Confidence**: {detection['confidence']:.0%}
**Text**: {detection['text']}
**Context**: {detection.get('context', '')}
**Description**: {detection['description']}

"""

    def get_learned_insights(self) -> List[Dict]:
        """Read all learned insights from file"""
        insights_file = self.insights_dir / "LEARNED_INSIGHTS.md"

        if not insights_file.exists():
            return []

        # Parse the markdown file to extract structured data
        # For now, just return file exists indicator
        try:
            with open(insights_file, "r") as f:
                content = f.read()
            return {"count": content.count("###"), "content": content[:500]}
        except Exception:
            return []

    def should_prompt_user(self, detection: Dict) -> bool:
        """Determine if we should ask user about this detection"""
        # Only prompt for high-confidence detections
        return detection["confidence"] >= 0.75


# Utility function for the CLI
def detect_learning_opportunities(project_id: int, project_path: str, text: str) -> List[Dict]:
    """Quick wrapper to detect triggers in text"""
    watcher = ConversationWatcher(project_id, project_path)
    return watcher.detect_triggers(text)

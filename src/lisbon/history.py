"""Episodic Conversation History and Automated Knowledge Learner for LISBON."""

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


class ConversationHistory:
    """Maintains persistent multi-session dialogue history and extracts user context."""

    def __init__(self, history_path: Optional[Path] = None):
        if history_path is None:
            history_path = Path(__file__).parent / "data" / "history.json"
        self.history_path = Path(history_path)
        self.data: Dict[str, Any] = self._load()

    def _load(self) -> Dict[str, Any]:
        """Loads dialogue turns from JSON disk storage safely."""
        if not self.history_path.exists():
            return {"turns": []}
        try:
            with open(self.history_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"turns": []}

    def save(self) -> None:
        """Persists dialogue history to disk."""
        self.history_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.history_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2)

    def add_turn(
        self,
        user_message: str,
        butler_response: str,
        topics: Optional[List[str]] = None,
        sentiment: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Records a completed conversation turn."""
        turn_id = f"turn-{len(self.data.get('turns', [])) + 1}"
        record = {
            "id": turn_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user": user_message.strip(),
            "butler": butler_response.strip(),
            "topics": topics or self._detect_topics(user_message),
            "sentiment": sentiment or self._detect_sentiment(user_message),
        }
        self.data.setdefault("turns", []).append(record)
        self.save()
        return record

    def get_recent_turns(self, limit: int = 6) -> List[Dict[str, Any]]:
        """Returns the most recent N turns in chronological order."""
        turns = self.data.get("turns", [])
        return turns[-limit:] if limit > 0 else turns

    def format_for_prompt(self, limit: int = 5) -> str:
        """Formats recent dialogue turns into a conversational context block for LLM prompts."""
        recent = self.get_recent_turns(limit=limit)
        if not recent:
            return ""

        dialogue_lines = ["\n[Recent Conversation History]:"]
        for turn in recent:
            dialogue_lines.append(f"Master: {turn['user']}")
            # Truncate very long past responses in prompt to save context
            resp = turn['butler']
            if len(resp) > 200:
                resp = resp[:200] + "..."
            dialogue_lines.append(f"LISBON: {resp}")
        return "\n".join(dialogue_lines)

    def search_history(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Searches past conversation turns by query keywords."""
        terms = [t.lower() for t in query.split() if t]
        matches = []
        for turn in reversed(self.data.get("turns", [])):
            text = f"{turn.get('user', '')} {turn.get('butler', '')}".lower()
            if any(term in text for term in terms):
                matches.append(turn)
                if len(matches) >= limit:
                    break
        return matches

    def auto_extract_facts(self, user_message: str) -> List[Dict[str, Any]]:
        """Analyzes user statements to extract personal habits, preferences, and facts."""
        text = user_message.strip()
        learned_facts = []

        patterns = [
            # Likes / preferences
            (r"\b(?:i like|i love|i enjoy|i prefer)\s+([^.,;!?]+)", "preferences", 4),
            # Dislikes
            (r"\b(?:i hate|i dislike|i cannot stand|i can't stand)\s+([^.,;!?]+)", "preferences", 4),
            # Ongoing activities & projects
            (r"\b(?:i am working on|i'm working on|i am building|i'm building)\s+([^.,;!?]+)", "projects", 5),
            # Deadlines & exams
            (r"\b(?:i have an exam|i have a test|i have a deadline|my deadline is)\s+([^.,;!?]+)", "academics", 5),
            # Daily routines & habits
            (r"\b(?:i usually|i always|i never|my routine is)\s+([^.,;!?]+)", "habits", 4),
            # Identity & life details
            (r"\b(?:i am a|i'm a|i study|my major is)\s+([^.,;!?]+)", "education", 5),
        ]

        for pattern, category, importance in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                fact_snippet = match.group(0).strip()
                # Capitalize first letter
                fact_text = f"Master noted: '{fact_snippet}'"
                learned_facts.append({
                    "fact": fact_text,
                    "category": category,
                    "importance": importance,
                })

        return learned_facts

    def _detect_topics(self, text: str) -> List[str]:
        """Classifies text into high-level functional domains."""
        text_lower = text.lower()
        topics = []
        mapping = {
            "academics": ["exam", "test", "study", "dsa", "hpc", "os", "ml", "java", "college", "assignment", "lab"],
            "engineering": ["code", "bug", "python", "git", "github", "build", "lisbon", "compile", "deploy"],
            "life": ["sleep", "tired", "morning", "night", "eat", "routine", "exercise", "walk", "break"],
            "strategy": ["goal", "priority", "plan", "future", "schedule", "focus", "roadmap"],
        }
        for domain, keywords in mapping.items():
            if any(k in text_lower for k in keywords):
                topics.append(domain)
        return topics or ["general"]

    def _detect_sentiment(self, text: str) -> str:
        """Heuristic detection of master's emotional tone."""
        text_lower = text.lower()
        if any(w in text_lower for w in ["stressed", "overwhelmed", "exhausted", "tired", "anxious", "worried", "lost"]):
            return "stressed"
        if any(w in text_lower for w in ["happy", "excited", "great", "awesome", "crushed it", "done", "finished", "success"]):
            return "motivated"
        if any(w in text_lower for w in ["why", "what if", "thinking", "curious", "wonder"]):
            return "reflective"
        return "neutral"

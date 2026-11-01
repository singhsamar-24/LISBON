"""Core Brain, Persona, and Context Loader for LISBON."""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from lisbon.goals import GoalsTracker
    from lisbon.memory import PersonalMemory
except ImportError:
    from goals import GoalsTracker
    from memory import PersonalMemory


class LisbonBrain:
    """The foundational persona, intelligence, and context coordinator for LISBON."""

    def __init__(
        self,
        profile_path: Optional[Path] = None,
        goals_path: Optional[Path] = None,
        memory_path: Optional[Path] = None,
    ):
        base_dir = Path(__file__).parent / "data"
        if profile_path is None:
            profile_path = base_dir / "profile.json"
        self.profile_path = Path(profile_path)
        self.profile: Dict[str, Any] = self._load_profile()

        # Initialize Goals and Long-Term Memory
        self.goals = GoalsTracker(goals_path or (base_dir / "goals.json"))
        self.memory = PersonalMemory(memory_path or (base_dir / "memory.json"))

    def _load_profile(self) -> Dict[str, Any]:
        """Reads user profile data safely from disk."""
        if not self.profile_path.exists():
            return {
                "user": {"name": "Master", "role": "Master"},
                "butler": {"name": "LISBON", "tone": "loyal, respectful, concise, proactive"},
                "current_focus": [],
            }
        try:
            with open(self.profile_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {
                "user": {"name": "Master", "role": "Master"},
                "butler": {"name": "LISBON", "tone": "loyal, respectful, concise, proactive"},
            }

    @property
    def master_name(self) -> str:
        return self.profile.get("user", {}).get("name", "Sir")

    @property
    def butler_name(self) -> str:
        return self.profile.get("butler", {}).get("name", "LISBON")

    def get_greeting(self) -> str:
        """Generates a dynamic, time-aware greeting tailored to the user."""
        hour = datetime.now().hour
        if 5 <= hour < 12:
            time_salutation = "Good morning"
        elif 12 <= hour < 17:
            time_salutation = "Good afternoon"
        elif 17 <= hour < 22:
            time_salutation = "Good evening"
        else:
            time_salutation = "Greetings"

        return f"{time_salutation}, {self.master_name}. {self.butler_name} is online and at your service."

    def get_daily_briefing(self) -> str:
        """Compiles a complete butler morning/evening briefing."""
        summary = self.goals.get_summary()
        active_goals = self.goals.list_goals(status="in_progress")
        top_facts = self.memory.get_top_facts(limit=3)

        lines = [
            f"🤵 **{self.butler_name} Daily Briefing for {self.master_name}**",
            f"📅 Local Time: {datetime.now().strftime('%A, %B %d, %Y - %I:%M %p')}",
            "",
            "🎯 **Life Goals & Project Status**:",
            f"• Active Goals: {summary['active_goals']} (Overall Progress: {summary['overall_progress_pct']}%)",
        ]

        for g in active_goals:
            pending = [m["title"] for m in g.get("milestones", []) if not m.get("completed")]
            pending_str = f"Pending: {', '.join(pending[:2])}" if pending else "All milestones up to date"
            lines.append(f"  - [{g.get('category')}] {g.get('title')}: {pending_str}")

        if top_facts:
            lines.append("")
            lines.append("🧠 **Key Context & Standing Directives**:")
            for fact in top_facts:
                lines.append(f"  • {fact}")

        lines.append("")
        lines.append("How may I assist you with your priorities today?")
        return "\n".join(lines)

    def build_system_prompt(self) -> str:
        """Prepares the rich system context prompt for conversational LLM sessions."""
        user_info = self.profile.get("user", {})
        focus_areas = ", ".join(self.profile.get("current_focus", []))
        summary = self.goals.get_summary()
        top_facts = " | ".join(self.memory.get_top_facts(limit=5))

        return (
            f"You are {self.butler_name}, a loyal, hyper-competent personal digital butler dedicated solely to {user_info.get('name', 'Sir')}. "
            f"Your persona tone: {self.profile.get('butler', {}).get('tone')}. "
            f"Master's current priorities: {focus_areas}. "
            f"Active Goals Progress: {summary['completed_milestones']}/{summary['total_milestones']} milestones ({summary['overall_progress_pct']}%). "
            f"Personal Context & Directives: {top_facts}. "
            f"Always answer concisely, respectfully, and with immediate actionable loyalty. Address your user as {user_info.get('name', 'Sir')} or Master."
        )

    def generate_response(self, user_input: str) -> str:
        """Generates an intelligent response using available API or internal butler logic."""
        gemini_key = os.environ.get("GEMINI_API_KEY")

        # 1. If Gemini API key is present, attempt live call via REST (no heavy SDK dependency needed)
        if gemini_key:
            try:
                import httpx
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}"
                payload = {
                    "contents": [{"parts": [{"text": f"{self.build_system_prompt()}\n\nMaster: {user_input}\nLISBON:"}]}],
                    "generationConfig": {"temperature": 0.4, "maxOutputTokens": 800},
                }
                resp = httpx.post(url, json=payload, timeout=12.0)
                if resp.status_code == 200:
                    data = resp.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        content_parts = candidates[0].get("content", {}).get("parts", [])
                        if content_parts:
                            return content_parts[0].get("text", "").strip()
            except Exception:
                pass

        # 2. Offline Butler Rule Engine
        msg = user_input.strip().lower()

        if any(w in msg for w in ["briefing", "report", "update", "status"]):
            return self.get_daily_briefing()

        if "goal" in msg:
            summary = self.goals.get_summary()
            active = self.goals.list_goals(status="in_progress")
            res = [f"You currently have {summary['active_goals']} active goals with {summary['overall_progress_pct']}% overall completion:"]
            for g in active:
                res.append(f"• {g['title']} ({g.get('category', 'General')})")
            return "\n".join(res)

        if any(w in msg for w in ["who are you", "what are you", "identity"]):
            return (
                f"I am {self.butler_name}, your personal AI butler. "
                f"My purpose is to manage your schedule, track your goals, protect your focus, and assist {self.master_name} across all technical and personal domains."
            )

        if any(w in msg for w in ["priority", "priorities", "focus"]):
            focus = self.profile.get("current_focus", [])
            return f"Your current master priorities are:\n" + "\n".join([f"• {f}" for f in focus])

        if any(w in msg for w in ["hello", "hi", "hey"]):
            return f"{self.get_greeting()} How may I serve you at this moment?"

        return (
            f"Acknowledged, {self.master_name}. I have noted: '{user_input}'. "
            f"To interact with me, you can ask for your 'briefing', check 'goals', or use commands like `/goals` and `/memory`."
        )

import json
from pathlib import Path

class LisbonBrain:
    """The foundational persona and context loader for LISBON."""

    def __init__(self, profile_path: Path | None = None):
        if profile_path is None:
            profile_path = Path(__file__).parent / "data" / "profile.json"
        self.profile_path = profile_path
        self.profile = self._load_profile()

    def _load_profile(self) -> dict:
        """Reads user profile data safely from disk."""
        if not self.profile_path.exists():
            return {"user": {"name": "Master"}, "butler": {"name": "LISBON"}}
        with open(self.profile_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def get_greeting(self) -> str:
        """Generates an initial greeting tailored to the user."""
        master_name = self.profile.get("user", {}).get("name", "Sir")
        butler_name = self.profile.get("butler", {}).get("name", "LISBON")
        return f"Greetings, {master_name}. {butler_name} is online and at your service."

    def build_system_prompt(self) -> str:
        """Prepares the system context prompt injected into LLM sessions."""
        user_info = self.profile.get("user", {})
        focus_areas = ", ".join(self.profile.get("current_focus", []))
        return (
            f"You are LISBON, a loyal personal butler to {user_info.get('name', 'Sir')}. "
            f"Your tone is {self.profile.get('butler', {}).get('tone')}. "
            f"Current Master Priorities: {focus_areas}. "
            f"Always keep your master's goals and time top of mind."
        )

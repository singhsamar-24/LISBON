"""Life Goals and Milestones Tracker for LISBON."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


class GoalsTracker:
    """Manages master life goals, priorities, and daily milestone tracking."""

    def __init__(self, goals_path: Optional[Path] = None):
        if goals_path is None:
            goals_path = Path(__file__).parent / "data" / "goals.json"
        self.goals_path = Path(goals_path)
        self.data: Dict[str, Any] = self._load()

    def _load(self) -> Dict[str, Any]:
        """Loads goals from JSON storage safely."""
        if not self.goals_path.exists():
            return {"goals": []}
        try:
            with open(self.goals_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"goals": []}

    def save(self) -> None:
        """Saves current goals state to disk."""
        self.goals_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.goals_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2)

    def list_goals(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Returns all goals, optionally filtered by status ('in_progress', 'completed', etc.)."""
        goals = self.data.get("goals", [])
        if status:
            return [g for g in goals if g.get("status") == status]
        return goals

    def add_goal(
        self,
        title: str,
        category: str = "General",
        target_date: str = "",
        milestones: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Adds a new goal with initial milestones."""
        goal_id = f"goal-{len(self.data.get('goals', [])) + 1}"
        formatted_milestones = []
        if milestones:
            for m in milestones:
                formatted_milestones.append({"title": m, "completed": False})

        new_goal = {
            "id": goal_id,
            "title": title.strip(),
            "category": category.strip(),
            "status": "in_progress",
            "target_date": target_date.strip(),
            "milestones": formatted_milestones,
        }
        self.data.setdefault("goals", []).append(new_goal)
        self.save()
        return new_goal

    def complete_milestone(self, goal_id: str, milestone_identifier: str | int) -> bool:
        """Marks a milestone completed by index (0-based) or substring title."""
        for goal in self.data.get("goals", []):
            if goal.get("id") == goal_id:
                milestones = goal.get("milestones", [])
                if isinstance(milestone_identifier, int) and 0 <= milestone_identifier < len(milestones):
                    milestones[milestone_identifier]["completed"] = True
                    self.save()
                    return True
                for m in milestones:
                    if milestone_identifier.lower() in m.get("title", "").lower():
                        m["completed"] = True
                        self.save()
                        return True
        return False

    def add_milestone(self, goal_id: str, milestone_title: str) -> bool:
        """Adds a milestone to an existing goal."""
        for goal in self.data.get("goals", []):
            if goal.get("id") == goal_id:
                goal.setdefault("milestones", []).append({
                    "title": milestone_title.strip(),
                    "completed": False,
                })
                self.save()
                return True
        return False

    def set_goal_status(self, goal_id: str, status: str) -> bool:
        """Updates status of a goal (e.g. 'in_progress', 'completed', 'paused')."""
        for goal in self.data.get("goals", []):
            if goal.get("id") == goal_id:
                goal["status"] = status
                self.save()
                return True
        return False

    def get_summary(self) -> Dict[str, Any]:
        """Calculates high-level progress statistics."""
        goals = self.data.get("goals", [])
        total_goals = len(goals)
        active_goals = [g for g in goals if g.get("status") == "in_progress"]
        completed_goals = [g for g in goals if g.get("status") == "completed"]

        total_milestones = 0
        completed_milestones = 0
        for g in goals:
            for m in g.get("milestones", []):
                total_milestones += 1
                if m.get("completed"):
                    completed_milestones += 1

        progress_pct = (
            int((completed_milestones / total_milestones) * 100) if total_milestones > 0 else 0
        )

        return {
            "total_goals": total_goals,
            "active_goals": len(active_goals),
            "completed_goals": len(completed_goals),
            "total_milestones": total_milestones,
            "completed_milestones": completed_milestones,
            "overall_progress_pct": progress_pct,
        }

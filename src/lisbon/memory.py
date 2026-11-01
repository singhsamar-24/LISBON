"""Personal context and long-term memory engine for LISBON."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


class PersonalMemory:
    """Stores and retrieves personal facts, user context, and preferences."""

    def __init__(self, memory_path: Optional[Path] = None):
        if memory_path is None:
            memory_path = Path(__file__).parent / "data" / "memory.json"
        self.memory_path = Path(memory_path)
        self.data: Dict[str, Any] = self._load()

    def _load(self) -> Dict[str, Any]:
        """Loads memories from JSON storage."""
        if not self.memory_path.exists():
            return {"memories": []}
        try:
            with open(self.memory_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"memories": []}

    def save(self) -> None:
        """Saves memory state to disk."""
        self.memory_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.memory_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2)

    def add_memory(
        self,
        fact: str,
        category: str = "general",
        importance: int = 3,
    ) -> Dict[str, Any]:
        """Records a new fact about the user or current situation."""
        mem_id = f"mem-{len(self.data.get('memories', [])) + 1}"
        record = {
            "id": mem_id,
            "fact": fact.strip(),
            "category": category.strip().lower(),
            "importance": max(1, min(5, importance)),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self.data.setdefault("memories", []).append(record)
        self.save()
        return record

    def search(self, query: str) -> List[Dict[str, Any]]:
        """Finds memories containing query terms."""
        terms = [t.lower() for t in query.split() if t]
        results = []
        for mem in self.data.get("memories", []):
            fact_lower = mem.get("fact", "").lower()
            cat_lower = mem.get("category", "").lower()
            if any(term in fact_lower or term in cat_lower for term in terms):
                results.append(mem)
        return results

    def get_all(self) -> List[Dict[str, Any]]:
        """Returns all recorded memories."""
        return self.data.get("memories", [])

    def get_top_facts(self, limit: int = 5) -> List[str]:
        """Returns highest-importance facts formatted as strings."""
        mems = self.data.get("memories", [])
        sorted_mems = sorted(mems, key=lambda x: x.get("importance", 1), reverse=True)
        return [m["fact"] for m in sorted_mems[:limit]]

    def remove_memory(self, memory_id: str) -> bool:
        """Deletes a memory by ID."""
        memories = self.data.get("memories", [])
        for i, m in enumerate(memories):
            if m.get("id") == memory_id:
                del memories[i]
                self.save()
                return True
        return False

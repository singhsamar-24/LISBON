"""Unit tests for LISBON Butler Core, Voice, and History modules."""

import json
from pathlib import Path
import pytest

from lisbon.brain import LisbonBrain
from lisbon.goals import GoalsTracker
from lisbon.history import ConversationHistory
from lisbon.memory import PersonalMemory
from lisbon.voice import LisbonVoice, clean_for_speech


@pytest.fixture
def temp_lisbon_env(tmp_path: Path):
    """Creates isolated JSON storage files for testing."""
    profile_path = tmp_path / "profile.json"
    goals_path = tmp_path / "goals.json"
    memory_path = tmp_path / "memory.json"
    history_path = tmp_path / "history.json"

    profile_data = {
        "user": {
            "name": "TestMaster",
            "role": "Master",
            "occupation": "Software Engineer",
            "academics": {"core_subjects": ["DSA", "HPC"]},
        },
        "butler": {
            "name": "LISBON",
            "tone": "respectful and sharp",
            "voice": {"default_enabled": False, "rate": 180, "volume": 0.9},
        },
        "current_focus": ["Unit Testing", "System Verification"],
    }
    with open(profile_path, "w", encoding="utf-8") as f:
        json.dump(profile_data, f)

    return profile_path, goals_path, memory_path, history_path


def test_goals_tracker(tmp_path: Path):
    goals_file = tmp_path / "test_goals.json"
    tracker = GoalsTracker(goals_path=goals_file)

    # 1. Add goal
    goal = tracker.add_goal(
        title="Complete Algorithms Exam",
        category="Academics",
        target_date="2026-12-15",
        milestones=["Review Trees", "Review Graphs"],
    )
    assert goal["title"] == "Complete Algorithms Exam"
    assert len(goal["milestones"]) == 2
    assert goal["milestones"][0]["completed"] is False

    # 2. Complete milestone
    ok = tracker.complete_milestone(goal["id"], "Trees")
    assert ok is True

    summary = tracker.get_summary()
    assert summary["total_goals"] == 1
    assert summary["active_goals"] == 1
    assert summary["completed_milestones"] == 1
    assert summary["overall_progress_pct"] == 50


def test_personal_memory(tmp_path: Path):
    mem_file = tmp_path / "test_memory.json"
    mem = PersonalMemory(memory_path=mem_file)

    # Add memory
    rec = mem.add_memory("Prefers dark mode on all IDE interfaces.", category="preferences", importance=5)
    assert rec["id"] == "mem-1"

    # Search
    results = mem.search("dark mode")
    assert len(results) == 1
    assert "dark mode" in results[0]["fact"]

    # Top facts
    top = mem.get_top_facts()
    assert len(top) == 1
    assert "Prefers dark mode" in top[0]

    # Remove
    assert mem.remove_memory("mem-1") is True
    assert len(mem.get_all()) == 0


def test_conversation_history(tmp_path: Path):
    hist_file = tmp_path / "test_history.json"
    history = ConversationHistory(history_path=hist_file)

    # 1. Add turn
    turn = history.add_turn(
        user_message="I have an exam on HPC and CUDA programming tomorrow.",
        butler_response="Understood. Let's focus on parallel thread scheduling and memory banks.",
    )
    assert turn["id"] == "turn-1"
    assert "academics" in turn["topics"]

    # 2. Recent turns
    recent = history.get_recent_turns(limit=5)
    assert len(recent) == 1
    assert "HPC" in recent[0]["user"]

    # 3. Prompt formatting
    formatted = history.format_for_prompt()
    assert "Master: I have an exam" in formatted
    assert "LISBON: Understood" in formatted

    # 4. Search
    matches = history.search_history("CUDA")
    assert len(matches) == 1

    # 5. Auto-extract facts
    learned = history.auto_extract_facts("I like dark roast coffee and clean code")
    assert len(learned) >= 1
    assert "coffee" in learned[0]["fact"]


def test_voice_cleaner():
    raw_md = "### **Greetings!** Here is [the documentation](https://example.com) with `code`:\n```python\nprint(1)\n```\n• Bullet 1 🚀"
    cleaned = clean_for_speech(raw_md)
    assert "Greetings!" in cleaned
    assert "the documentation" in cleaned
    assert "https://" not in cleaned
    assert "```" not in cleaned
    assert "🚀" not in cleaned


def test_voice_engine():
    voice = LisbonVoice(enabled=False, rate=170, volume=0.8)
    assert voice.enabled is False
    assert voice.rate == 170

    # Toggle
    new_state = voice.toggle()
    assert new_state is True
    assert voice.enabled is True

    voice.toggle()
    assert voice.enabled is False
    voice.stop()


def test_brain_orchestration_with_voice_and_history(temp_lisbon_env):
    profile_p, goals_p, mem_p, hist_p = temp_lisbon_env
    brain = LisbonBrain(
        profile_path=profile_p,
        goals_path=goals_p,
        memory_path=mem_p,
        history_path=hist_p,
        enable_voice=False,
    )

    assert brain.master_name == "TestMaster"
    assert brain.butler_name == "LISBON"
    assert brain.voice.enabled is False

    # Greeting
    greeting = brain.get_greeting()
    assert "TestMaster" in greeting
    assert "LISBON" in greeting

    # Conversational turn with auto-learning
    resp = brain.generate_response("I love building autonomous systems and high performance computing", speak_aloud=False)
    assert resp is not None

    # Check that turn was recorded in history
    recent_history = brain.history.get_recent_turns(limit=5)
    assert len(recent_history) == 1
    assert "autonomous" in recent_history[0]["user"]

    # Check that fact was auto-learned into memory
    memories = brain.memory.get_all()
    assert len(memories) >= 1

    # System prompt should include human context, history, and goals
    prompt = brain.build_system_prompt()
    assert "TestMaster" in prompt
    assert "Unit Testing" in prompt
    assert "Recent Conversation History" in prompt

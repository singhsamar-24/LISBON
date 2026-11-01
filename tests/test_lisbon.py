"""Unit tests for LISBON Butler Core modules."""

import json
from pathlib import Path
import pytest

from lisbon.brain import LisbonBrain
from lisbon.goals import GoalsTracker
from lisbon.memory import PersonalMemory


@pytest.fixture
def temp_lisbon_env(tmp_path: Path):
    """Creates isolated JSON storage files for testing."""
    profile_path = tmp_path / "profile.json"
    goals_path = tmp_path / "goals.json"
    memory_path = tmp_path / "memory.json"

    profile_data = {
        "user": {"name": "TestMaster", "role": "Master"},
        "butler": {"name": "LISBON", "tone": "respectful and sharp"},
        "current_focus": ["Unit Testing", "System Verification"],
    }
    with open(profile_path, "w", encoding="utf-8") as f:
        json.dump(profile_data, f)

    return profile_path, goals_path, memory_path


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


def test_brain_orchestration(temp_lisbon_env):
    profile_p, goals_p, mem_p = temp_lisbon_env
    brain = LisbonBrain(profile_path=profile_p, goals_path=goals_p, memory_path=mem_p)

    assert brain.master_name == "TestMaster"
    assert brain.butler_name == "LISBON"

    # Greeting
    greeting = brain.get_greeting()
    assert "TestMaster" in greeting
    assert "LISBON" in greeting

    # System prompt
    prompt = brain.build_system_prompt()
    assert "TestMaster" in prompt
    assert "Unit Testing" in prompt

    # Butler offline intent response
    res_who = brain.generate_response("who are you")
    assert "personal AI butler" in res_who

    res_priorities = brain.generate_response("what are my priorities")
    assert "Unit Testing" in res_priorities

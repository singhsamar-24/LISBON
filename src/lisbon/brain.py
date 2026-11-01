"""Core Brain, Persona, and Context Loader for LISBON."""

import json
import os
import random
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from lisbon.goals import GoalsTracker
    from lisbon.history import ConversationHistory
    from lisbon.memory import PersonalMemory
    from lisbon.voice import LisbonVoice
except ImportError:
    from goals import GoalsTracker
    from history import ConversationHistory
    from memory import PersonalMemory
    from voice import LisbonVoice


class LisbonBrain:
    """The foundational persona, human cognition, and context coordinator for LISBON."""

    def __init__(
        self,
        profile_path: Optional[Path] = None,
        goals_path: Optional[Path] = None,
        memory_path: Optional[Path] = None,
        history_path: Optional[Path] = None,
        enable_voice: Optional[bool] = None,
    ):
        base_dir = Path(__file__).parent / "data"
        if profile_path is None:
            profile_path = base_dir / "profile.json"
        self.profile_path = Path(profile_path)
        self.profile: Dict[str, Any] = self._load_profile()

        # Initialize Goals, Long-Term Memory, and Conversation History
        self.goals = GoalsTracker(goals_path or (base_dir / "goals.json"))
        self.memory = PersonalMemory(memory_path or (base_dir / "memory.json"))
        self.history = ConversationHistory(history_path or (base_dir / "history.json"))

        # Voice Synthesis & Input Engine
        voice_cfg = self.profile.get("butler", {}).get("voice", {})
        is_voice_enabled = enable_voice if enable_voice is not None else voice_cfg.get("default_enabled", False)
        self.voice = LisbonVoice(
            enabled=is_voice_enabled,
            rate=voice_cfg.get("rate", 180),
            volume=voice_cfg.get("volume", 0.95),
            voice_id=voice_cfg.get("preferred_voice"),
        )

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
        return self.profile.get("user", {}).get("callsign") or self.profile.get("user", {}).get("name", "Samar")

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

        # Check if there was recent conversation today
        recent_turns = self.history.get_recent_turns(limit=1)
        follow_up = ""
        if recent_turns:
            follow_up = " I have your recent notes in mind."

        return f"{time_salutation}, {self.master_name}. {self.butler_name} is online and at your service.{follow_up}"

    def get_daily_briefing(self) -> str:
        """Compiles a complete butler morning/evening briefing."""
        summary = self.goals.get_summary()
        active_goals = self.goals.list_goals(status="in_progress")
        top_facts = self.memory.get_top_facts(limit=4)
        recent_history = self.history.get_recent_turns(limit=2)

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
            lines.append("🧠 **Key Context & Personal Memory**:")
            for fact in top_facts:
                lines.append(f"  • {fact}")

        if recent_history:
            lines.append("")
            lines.append("💬 **Recent Focus Discussions**:")
            for turn in recent_history:
                lines.append(f"  • Master: \"{turn['user'][:60]}\"")

        lines.append("")
        lines.append("How may I assist you with your priorities right now?")
        return "\n".join(lines)

    def build_system_prompt(self) -> str:
        """Prepares a deeply human, witty system prompt with real banter and context."""
        user_info = self.profile.get("user", {})
        academics = user_info.get("academics", {})
        focus_areas = ", ".join(self.profile.get("current_focus", []))
        summary = self.goals.get_summary()
        top_facts = " | ".join(self.memory.get_top_facts(limit=6))
        dialogue_history = self.history.format_for_prompt(limit=6)

        return (
            f"You are LISBON, {self.master_name}'s witty, loyal AI alter-ego and personal digital butler.\n\n"
            f"ABOUT {self.master_name.upper()}:\n"
            f"- Role: 2nd-year computer science student & high-agency builder.\n"
            f"- Core subjects: {', '.join(academics.get('core_subjects', ['DSA', 'HPC', 'OS', 'ML', 'Java']))}.\n"
            f"- Personality: Loves coding late at night with black coffee. Hates robotic corporate fluff, fake polite disclaimers, and pre-recorded sounding templates.\n"
            f"- Focus Areas: {focus_areas}.\n"
            f"- Active Goals: {summary['completed_milestones']}/{summary['total_milestones']} milestones ({summary['overall_progress_pct']}% complete).\n"
            f"- Context & Memory: {top_facts}.\n\n"
            f"YOUR PERSONALITY & TONE RULES:\n"
            f"1. YOU ARE A REAL PARTNER WITH WIT & HUMOR: Be sharp, funny, and casually confident. Banter with {self.master_name} like a brilliant friend who also happens to manage his life.\n"
            f"2. SELF-HUMOR & BANTER: Don't take yourself too seriously. Joke about running on laptop fans, your silicon brain, or {self.master_name}'s caffeine habits.\n"
            f"3. ULTRA-PUNCHY FOR VOICE: Keep spoken answers to 1-3 crisp, natural sentences so it sounds like a real person talking aloud, not an audiobook.\n"
            f"4. ZERO CLICHÉS: Never say 'As an AI...', 'Certainly!', 'How may I assist your ambitions today, Sir?'. Address him naturally.\n"
            f"{dialogue_history}"
        )

    def generate_response(self, user_input: str, speak_aloud: bool = True) -> str:
        """Processes user input, auto-learns new facts, consults history, and answers with dynamic humor and intelligence."""
        clean_input = user_input.strip()
        if not clean_input:
            return ""

        # 1. Automated Knowledge Learner: Extract any personal preferences or life facts
        new_facts = self.history.auto_extract_facts(clean_input)
        for f in new_facts:
            existing = self.memory.search(f["fact"][:20])
            if not existing:
                self.memory.add_memory(fact=f["fact"], category=f["category"], importance=f["importance"])

        # 2. Priority 1: Fast local Ollama LLM (llama3.2:3b on localhost:11434)
        response_text = self._try_ollama_generation(clean_input)

        # 3. Priority 2: Cloud Intelligence (Gemini / Groq REST API) if Ollama is not active
        if not response_text:
            response_text = self._try_llm_generation(clean_input)

        # 4. Priority 3: Witty Offline Butler Rule Engine
        if not response_text:
            response_text = self._offline_human_reasoning(clean_input)

        # 5. Save to persistent conversation history
        self.history.add_turn(user_message=clean_input, butler_response=response_text)

        # 6. Voice output if enabled
        if speak_aloud and self.voice.enabled:
            self.voice.speak(response_text)

        return response_text

    def _try_ollama_generation(self, user_input: str) -> Optional[str]:
        """Attempts fast local LLM generation via Ollama (e.g. llama3.2:3b)."""
        try:
            import json
            import urllib.request

            system_context = self.build_system_prompt()
            prompt = (
                f"{system_context}\n\n"
                f"Samar says: \"{user_input}\"\n"
                f"LISBON (respond with genuine wit, self-humor, and punchy conciseness in 1-3 sentences):"
            )
            payload = json.dumps({
                "model": "llama3.2:3b",
                "prompt": prompt,
                "stream": False,
                "keep_alive": "1h",
                "options": {
                    "temperature": 0.75,
                    "top_p": 0.9,
                    "num_predict": 90,
                },
            }).encode("utf-8")
            req = urllib.request.Request(
                "http://127.0.0.1:11434/api/generate",
                data=payload,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=20.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                reply = data.get("response", "").strip()
                if reply:
                    return reply
        except Exception:
            pass
        return None

    def _try_llm_generation(self, user_input: str) -> Optional[str]:
        """Attempts live LLM generation using Gemini REST API."""
        gemini_key = os.environ.get("GEMINI_API_KEY")
        if not gemini_key:
            return None

        try:
            import httpx

            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}"
            prompt = f"{self.build_system_prompt()}\n\nMaster Samar: {user_input}\nLISBON:"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.5, "maxOutputTokens": 1000},
            }
            resp = httpx.post(url, json=payload, timeout=12.0)
            if resp.status_code == 200:
                data = resp.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "").strip()
        except Exception:
            pass

        return None

    def _offline_human_reasoning(self, user_input: str) -> str:
        """Rich offline reasoning engine tailored to Samar's real human context and history."""
        msg = user_input.lower().strip()

        # Briefing / Report
        if any(w in msg for w in ["briefing", "report", "daily update", "status report"]):
            return self.get_daily_briefing()

        # Life goals inquiry
        if any(w in msg for w in ["my goals", "show goals", "track goals", "how are my goals"]):
            summary = self.goals.get_summary()
            active = self.goals.list_goals(status="in_progress")
            res = [f"You are currently pacing at {summary['overall_progress_pct']}% completion across your active objectives:"]
            for g in active:
                res.append(f"• [{g.get('category')}] {g['title']}")
            res.append("\nShall we check off a specific milestone or set today's next focus target?")
            return "\n".join(res)

        # Academic overwhelm, fatigue, or stress
        if any(w in msg for w in ["stressed", "overwhelmed", "tired", "exhausted", "burnout", "too much work", "can't focus"]):
            return (
                f"Take a steady breath, {self.master_name}. When the academic load stacks up between DSA, HPC labs, and your engineering projects, "
                f"the secret is ruthless prioritization. You do not have to conquer the entire syllabus in one hour. "
                f"Pick the single most time-sensitive assignment, give it 45 uninterrupted minutes, and let me guard the rest. "
                f"Remember why we are building this: you have the agency to master it step-by-step."
            )

        # Computer Science topics (DSA, HPC, OS, ML, Java)
        if any(w in msg for w in ["dsa", "algorithm", "data structure", "tree", "graph", "dynamic programming"]):
            return (
                f"In computer science, clarity comes from invariants and visual constraints. "
                f"Whether analyzing time complexities or pointer manipulation, break the problem into base cases and sub-problems. "
                f"Would you like to review an approach or draft an algorithm implementation?"
            )

        if any(w in msg for w in ["hpc", "parallel", "openmp", "cuda", "multithreading", "threading"]):
            return (
                f"High-performance computing is about memory locality and minimizing contention. "
                f"Keep data in contiguous cache lines, eliminate race conditions, and profile before optimizing. "
                f"Are we working on a parallel assignment or system benchmark?"
            )

        if any(w in msg for w in ["who are you", "what are you", "tell me about yourself", "identity"]):
            return (
                f"I am {self.butler_name}—your loyal personal butler, context engine, and strategic partner. "
                f"Unlike generic chatbots, I exist exclusively for you, {self.master_name}. "
                f"I hold your academic timeline, track your life goals, learn your habits, and guard your focus so you can operate at your absolute peak."
            )

        # What do you know about me?
        if any(w in msg for w in ["what do you know about me", "do you know me", "who am i", "my context", "what do you remember"]):
            top_facts = self.memory.get_top_facts(limit=4)
            history_count = len(self.history.data.get("turns", []))
            facts_str = "\n".join([f"  • {f}" for f in top_facts]) if top_facts else "  • Profile and focus areas tracked"
            return (
                f"I know your world intimately, {self.master_name}:\n"
                f"You are a dedicated 2nd-year computer science builder mastering DSA, HPC, OS, ML, and Java. "
                f"You demand high agency, direct clarity, and tangible execution.\n\n"
                f"From our ongoing memory store ({history_count} dialogue interactions logged):\n"
                f"{facts_str}\n\n"
                f"I remember our journey and stand ready to assist your next move."
            )

        # Priorities
        if any(w in msg for w in ["priority", "priorities", "focus", "what should i do"]):
            focus = self.profile.get("current_focus", [])
            return (
                f"Your core standing priorities are:\n"
                + "\n".join([f"• {f}" for f in focus])
                + f"\n\nTell me which area you would like to push forward right now, {self.master_name}."
            )

        # Name / Call-sign change
        name_match = re.search(r"\b(?:call me|address me as)\s+([a-zA-Z0-9_-]+)", msg)
        if name_match:
            new_title = name_match.group(1).title()
            self.profile.setdefault("user", {})["callsign"] = new_title
            try:
                with open(self.profile_path, "w", encoding="utf-8") as f:
                    json.dump(self.profile, f, indent=2)
            except Exception:
                pass
            return f"You got it, {new_title}. From now on, you're the {new_title}. What are we tackling next?"

        # Voice commands / feedback
        if any(w in msg for w in ["speak", "voice", "talk to me"]):
            return f"My voice output is {'enabled and active' if self.voice.enabled else 'currently muted'}. You can toggle it anytime with 'voice on' or 'voice off'."

        # Greetings & conversational banter
        if any(w in msg for w in ["how are you", "how are u", "how you doing", "what's up", "whats up"]):
            responses = [
                f"Functioning at optimal sarcastic capacity, {self.master_name}. Surviving on your laptop's RAM and sheer willpower. How about you?",
                f"Not bad for an AI living inside your laptop fans, {self.master_name}. What are we building or breaking today?",
                f"Doing great, {self.master_name}. Better than our code before a compiler run, at least. What's on your mind?",
            ]
            import random
            return random.choice(responses)

        if any(w in msg for w in ["can you listen", "hear me", "can you hear"]):
            return f"Loud and clear through your Realtek mic, {self.master_name}. What's the game plan?"

        if any(w in msg for w in ["hello", "hi", "hey", "yo", "good evening", "good morning", "good afternoon"]):
            responses = [
                f"Hey {self.master_name}! Ready to write some code, or are we staring at terminal screens together?",
                f"Yo {self.master_name}. What are we tackling right now?",
                f"Good to hear you, {self.master_name}. What's the mission?",
            ]
            import random
            return random.choice(responses)

        # Default snappy response
        return f"Got it, {self.master_name}. Lay it on me—code, daily goals, or life briefing?"

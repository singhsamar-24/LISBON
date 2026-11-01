"""Main entry point for LISBON - Personal AI Butler."""

import sys
from pathlib import Path

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure src is on Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lisbon.brain import LisbonBrain
from lisbon.cli import interactive_loop


def main():
    brain = LisbonBrain()

    # If arguments are passed, handle quick subcommands
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg in ["--briefing", "-b", "briefing"]:
            print(brain.get_daily_briefing())
            return
        elif arg in ["--greeting", "-g"]:
            print(brain.get_greeting())
            return
        elif arg in ["--system-prompt", "-p"]:
            print(brain.build_system_prompt())
            return

    # Default to interactive butler terminal loop
    interactive_loop(brain)


if __name__ == "__main__":
    main()

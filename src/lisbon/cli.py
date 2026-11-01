"""Interactive Terminal Interface for LISBON Butler with Voice & Episodic History."""

import sys
from typing import Optional

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

try:
    from lisbon.brain import LisbonBrain
except ImportError:
    from brain import LisbonBrain

console = Console()


def print_banner(brain: LisbonBrain) -> None:
    """Displays the elegant LISBON terminal banner."""
    summary = brain.goals.get_summary()
    voice_status = "[bold green]ENABLED[/bold green]" if brain.voice.enabled else "[dim]MUTED[/dim]"
    fact_count = len(brain.memory.get_all())
    turn_count = len(brain.history.data.get("turns", []))

    content = (
        f"[bold white]{brain.get_greeting()}[/bold white]\n\n"
        f"[dim]Master:[/dim] [cyan]{brain.master_name}[/cyan]  •  "
        f"[dim]Butler:[/dim] [bold yellow]{brain.butler_name}[/bold yellow]  •  "
        f"[dim]Voice:[/dim] {voice_status}\n"
        f"[dim]Active Goals:[/dim] [green]{summary['active_goals']}[/green] ({summary['overall_progress_pct']}% complete)  •  "
        f"[dim]Memory:[/dim] [magenta]{fact_count} facts[/magenta]  •  "
        f"[dim]History:[/dim] [blue]{turn_count} interactions[/blue]"
    )
    console.print(Panel(content, title="[bold gold1]🤵 LISBON PERSONAL AI BUTLER[/bold gold1]", border_style="gold1"))


def show_goals(brain: LisbonBrain) -> None:
    """Renders all master goals in a formatted table."""
    goals = brain.goals.list_goals()
    if not goals:
        console.print("[dim]No goals tracked yet. Use 'add-goal' to create one.[/dim]")
        return

    table = Table(title="🎯 Master's Life Goals & Milestones", border_style="cyan")
    table.add_column("ID", style="bold dim", width=8)
    table.add_column("Category", style="magenta", width=12)
    table.add_column("Goal Title", style="bold white")
    table.add_column("Status", width=12)
    table.add_column("Milestones Progress", style="cyan")

    for g in goals:
        milestones = g.get("milestones", [])
        completed = sum(1 for m in milestones if m.get("completed"))
        total = len(milestones)
        status_color = "green" if g.get("status") == "completed" else "yellow"

        m_details = []
        for m in milestones:
            check = "✓" if m.get("completed") else "○"
            m_details.append(f"{check} {m.get('title')}")
        progress_str = f"({completed}/{total})\n" + "\n".join(m_details) if m_details else "No milestones"

        table.add_row(
            g.get("id", ""),
            g.get("category", "General"),
            g.get("title", ""),
            f"[{status_color}]{g.get('status', 'in_progress')}[/{status_color}]",
            progress_str,
        )
    console.print(table)


def show_memory(brain: LisbonBrain) -> None:
    """Displays all personal memory records."""
    memories = brain.memory.get_all()
    if not memories:
        console.print("[dim]No personal memories recorded yet. Use 'remember <fact>' to add.[/dim]")
        return

    table = Table(title="🧠 Personal Context & Long-Term Memory", border_style="magenta")
    table.add_column("ID", style="bold dim", width=8)
    table.add_column("Category", style="cyan", width=14)
    table.add_column("Fact / Directives", style="white")
    table.add_column("Importance", justify="center", width=10)

    for m in memories:
        table.add_row(
            m.get("id", ""),
            m.get("category", "general"),
            m.get("fact", ""),
            "★" * m.get("importance", 1),
        )
    console.print(table)


def show_history(brain: LisbonBrain, limit: int = 10) -> None:
    """Displays recent conversation history turns."""
    turns = brain.history.get_recent_turns(limit=limit)
    if not turns:
        console.print("[dim]No past dialogue recorded yet. Speak with LISBON to build history.[/dim]")
        return

    table = Table(title=f"💬 Recent Conversation History (Last {len(turns)} turns)", border_style="blue")
    table.add_column("ID", style="bold dim", width=8)
    table.add_column("Timestamp", style="dim", width=12)
    table.add_column(f"Master ({brain.master_name})", style="white", width=35)
    table.add_column(f"Butler ({brain.butler_name})", style="yellow", width=40)
    table.add_column("Topic/Mood", style="cyan", width=16)

    for t in turns:
        # Format time
        ts = t.get("timestamp", "")
        time_display = ts[11:19] if len(ts) >= 19 else ts
        user_short = t.get("user", "")
        if len(user_short) > 75:
            user_short = user_short[:75] + "..."
        butler_short = t.get("butler", "")
        if len(butler_short) > 85:
            butler_short = butler_short[:85] + "..."
        meta = f"{', '.join(t.get('topics', []))}\n[dim]({t.get('sentiment', 'neutral')})[/dim]"

        table.add_row(
            t.get("id", ""),
            time_display,
            user_short,
            butler_short,
            meta,
        )
    console.print(table)


def show_voices(brain: LisbonBrain) -> None:
    """Lists available system TTS voices."""
    voices = brain.voice.get_available_voices()
    if not voices:
        console.print("[dim]No TTS voices detected.[/dim]")
        return

    table = Table(title="🎙️ Available Voice Synthesis Engines", border_style="gold1")
    table.add_column("#", style="dim", width=4)
    table.add_column("Voice Name", style="bold white")
    table.add_column("Languages", style="cyan")

    for i, v in enumerate(voices):
        langs = ", ".join(v.get("languages", [])) or "en-US"
        table.add_row(str(i + 1), v.get("name", "Unknown"), langs)
    console.print(table)


def show_help() -> None:
    """Prints command cheat sheet."""
    help_text = """
### 🤵 Available Butler Commands:
- **`briefing`** or **`report`**: Get your comprehensive daily briefing
- **`goals`**: Display all goals, milestones, and completion status
- **`add-goal`**: Create a new life goal interactively
- **`done <goal_id> <keyword>`**: Mark a milestone completed (e.g. `done goal-1 DSA`)
- **`memory`**: View personal context and long-term memory
- **`remember <fact>`**: Teach LISBON a new personal fact
- **`history`**: View recent conversation turns and topics
- **`search-history <query>`**: Search through past conversation history
- **`voice on` / **`voice off`**: Toggle speech output aloud
- **`listen`** or **`mic`**: Activate microphone to speak your question aloud
- **`voices`**: List available system TTS voices
- **`profile`**: View user profile settings
- **`exit`** or **`quit`**: Put LISBON to standby
- *Or simply talk with your butler naturally!*
"""
    console.print(Markdown(help_text))


def interactive_loop(brain: LisbonBrain) -> None:
    """Runs the main butler command and conversation REPL."""
    print_banner(brain)

    # If voice is enabled, speak initial greeting aloud
    if brain.voice.enabled:
        brain.voice.speak(brain.get_greeting())

    console.print("[dim]Type [bold cyan]briefing[/bold cyan], [bold cyan]goals[/bold cyan], [bold cyan]voice on/off[/bold cyan], [bold cyan]listen[/bold cyan], [bold cyan]help[/bold cyan], or speak naturally.[/dim]\n")

    while True:
        try:
            user_input = Prompt.ask(f"[bold gold1]{brain.master_name}[/bold gold1] [dim]>[/dim]").strip()
            if not user_input:
                continue

            cmd_lower = user_input.lower()

            if cmd_lower in ["exit", "quit", "q"]:
                farewell = f"Until next time, {brain.master_name}. Standing by."
                console.print(f"\n[bold gold1]{brain.butler_name}:[/bold gold1] {farewell}\n")
                if brain.voice.enabled:
                    brain.voice.speak(farewell)
                break

            elif cmd_lower in ["help", "/help", "?", "commands"]:
                show_help()

            elif cmd_lower in ["briefing", "/briefing", "report", "status"]:
                briefing_text = brain.get_daily_briefing()
                console.print(Panel(Markdown(briefing_text), title="[bold gold1]🤵 Daily Butler Briefing[/bold gold1]", border_style="gold1"))
                if brain.voice.enabled:
                    brain.voice.speak(briefing_text)

            elif cmd_lower in ["goals", "/goals"]:
                show_goals(brain)

            elif cmd_lower in ["memory", "/memory", "memories", "facts"]:
                show_memory(brain)

            elif cmd_lower in ["history", "/history"]:
                show_history(brain)

            elif cmd_lower.startswith("search-history ") or cmd_lower.startswith("find "):
                q = user_input.split(maxsplit=1)[1].strip()
                matches = brain.history.search_history(q)
                if matches:
                    console.print(f"[bold cyan]Found {len(matches)} historical interactions matching '{q}':[/bold cyan]")
                    for m in matches:
                        console.print(f"[dim]{m.get('timestamp', '')[:10]}[/dim] [bold white]You:[/bold white] {m.get('user')}")
                        console.print(f"[yellow]{brain.butler_name}:[/yellow] {m.get('butler')}\n")
                else:
                    console.print(f"[dim]No past discussions found matching '{q}'.[/dim]")

            elif cmd_lower in ["voice", "voice on", "enable voice"]:
                brain.voice.enabled = True
                msg = f"Voice synthesis enabled, {brain.master_name}."
                console.print(f"[green]✓ {msg}[/green]")
                brain.voice.speak(msg)

            elif cmd_lower in ["voice off", "mute", "disable voice"]:
                brain.voice.enabled = False
                console.print("[yellow]✓ Voice synthesis muted.[/yellow]")

            elif cmd_lower in ["voices", "list voices"]:
                show_voices(brain)

            elif cmd_lower in ["listen", "mic", "talk", "speak"]:
                console.print("[bold cyan]🎙️ Listening to microphone... Speak clearly now.[/bold cyan]")
                spoken_text = brain.voice.listen(phrase_time_limit=10, timeout=7)
                if spoken_text:
                    console.print(f"[dim]Heard:[/dim] [bold white]\"{spoken_text}\"[/bold white]")
                    with console.status(f"[gold1]{brain.butler_name} is reasoning...[/gold1]", spinner="dots"):
                        response = brain.generate_response(spoken_text)
                    console.print(f"\n[bold gold1]{brain.butler_name}:[/bold gold1] {response}\n")
                elif spoken_text == "":
                    console.print("[dim]Could not discern speech clearly. Please try again.[/dim]")
                else:
                    console.print("[dim]No speech detected within the listening window.[/dim]")

            elif cmd_lower.startswith("remember "):
                fact = user_input[9:].strip()
                if fact:
                    rec = brain.memory.add_memory(fact=fact, category="user_note", importance=4)
                    console.print(f"[green]✓ Recorded into memory bank as {rec['id']}.[/green]")
                    if brain.voice.enabled:
                        brain.voice.speak(f"Understood, {brain.master_name}. I have committed that to memory.")

            elif cmd_lower.startswith("add-goal") or cmd_lower == "add goal":
                title = Prompt.ask("[bold]Goal title[/bold]").strip()
                category = Prompt.ask("[bold]Category[/bold] (e.g. Academics, Engineering, Health)", default="General").strip()
                target_date = Prompt.ask("[bold]Target completion date[/bold] (optional)", default="").strip()
                milestones_raw = Prompt.ask("[bold]Initial milestones[/bold] (comma-separated)", default="").strip()
                milestones = [m.strip() for m in milestones_raw.split(",") if m.strip()]
                new_g = brain.goals.add_goal(title=title, category=category, target_date=target_date, milestones=milestones)
                console.print(f"[green]✓ Goal '{new_g['title']}' recorded with ID {new_g['id']}.[/green]")

            elif cmd_lower.startswith("done "):
                parts = user_input.split(maxsplit=2)
                if len(parts) >= 3:
                    goal_id = parts[1]
                    m_kw = parts[2]
                    ok = brain.goals.complete_milestone(goal_id, m_kw)
                    if ok:
                        console.print(f"[green]✓ Milestone marked complete for {goal_id}![/green]")
                    else:
                        console.print(f"[red]Could not match milestone '{m_kw}' under {goal_id}.[/red]")
                else:
                    console.print("[dim]Usage: done <goal_id> <milestone keyword>[/dim]")

            elif cmd_lower in ["profile", "/profile"]:
                console.print_json(data=brain.profile)

            else:
                # Conversational processing with human reasoning
                with console.status(f"[gold1]{brain.butler_name} is reasoning...[/gold1]", spinner="dots"):
                    response = brain.generate_response(user_input)
                console.print(f"\n[bold gold1]{brain.butler_name}:[/bold gold1] {response}\n")

        except KeyboardInterrupt:
            console.print(f"\n\n[bold gold1]{brain.butler_name}:[/bold gold1] Butler session interrupted. Standing by.\n")
            break
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")


def main() -> None:
    brain = LisbonBrain()
    interactive_loop(brain)


if __name__ == "__main__":
    main()

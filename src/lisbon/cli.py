"""Interactive Terminal Interface for LISBON Butler."""

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
    content = (
        f"[bold white]{brain.get_greeting()}[/bold white]\n\n"
        f"[dim]Master:[/dim] [cyan]{brain.master_name}[/cyan]  •  "
        f"[dim]Butler:[/dim] [bold yellow]{brain.butler_name}[/bold yellow]  •  "
        f"[dim]Active Goals:[/dim] [green]{summary['active_goals']}[/green] ({summary['overall_progress_pct']}% complete)"
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

    table = Table(title="🧠 Personal Context & Memory Bank", border_style="magenta")
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


def show_help() -> None:
    """Prints command cheat sheet."""
    help_text = """
### 🤵 Available Butler Commands:
- **`briefing`** or **`report`**: Get your comprehensive daily briefing
- **`goals`**: Display all goals, milestones, and completion status
- **`add-goal`**: Create a new life goal interactively
- **`done <goal_id> <keyword>`**: Mark a milestone completed (e.g. `done goal-1 DSA`)
- **`memory`**: View your personal context and long-term memory
- **`remember <fact>`**: Teach LISBON a new personal fact or preference
- **`profile`**: View user profile settings
- **`help`**: Show this help manual
- **`exit`** or **`quit`**: Put LISBON to standby
- *Or simply talk to LISBON naturally!*
"""
    console.print(Markdown(help_text))


def interactive_loop(brain: LisbonBrain) -> None:
    """Runs the main butler command and conversation REPL."""
    print_banner(brain)
    console.print("[dim]Type [bold cyan]briefing[/bold cyan], [bold cyan]goals[/bold cyan], [bold cyan]help[/bold cyan], or speak naturally with your butler.[/dim]\n")

    while True:
        try:
            user_input = Prompt.ask(f"[bold gold1]{brain.master_name}[/bold gold1] [dim]>[/dim]").strip()
            if not user_input:
                continue

            cmd_lower = user_input.lower()

            if cmd_lower in ["exit", "quit", "q"]:
                console.print(f"\n[bold gold1]{brain.butler_name}:[/bold gold1] Until next time, {brain.master_name}. Standing by.\n")
                break

            elif cmd_lower in ["help", "/help", "?", "commands"]:
                show_help()

            elif cmd_lower in ["briefing", "/briefing", "report", "status"]:
                console.print(Panel(Markdown(brain.get_daily_briefing()), title="[bold gold1]🤵 Daily Butler Briefing[/bold gold1]", border_style="gold1"))

            elif cmd_lower in ["goals", "/goals"]:
                show_goals(brain)

            elif cmd_lower in ["memory", "/memory", "memories", "facts"]:
                show_memory(brain)

            elif cmd_lower.startswith("remember "):
                fact = user_input[9:].strip()
                if fact:
                    rec = brain.memory.add_memory(fact=fact, category="user_note", importance=4)
                    console.print(f"[green]✓ Recorded into memory bank as {rec['id']}.[/green]")

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
                # Conversational processing
                with console.status(f"[gold1]{brain.butler_name} is processing...[/gold1]", spinner="dots"):
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

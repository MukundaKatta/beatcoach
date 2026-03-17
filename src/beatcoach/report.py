"""Performance report generation with rich console output."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from beatcoach.models import (
    Note,
    Performance,
    PracticeSession,
    ScoreBreakdown,
)


class PerformanceReport:
    """Generates formatted performance reports using Rich.

    Parameters
    ----------
    console : Console | None
        Rich console for output. Creates one if not provided.
    """

    def __init__(self, console: Console | None = None) -> None:
        self.console = console or Console()

    def print_score(self, score: ScoreBreakdown, title: str = "Performance Score") -> None:
        """Print a score breakdown as a rich panel."""
        grade_color = self._grade_color(score.grade)

        table = Table(show_header=True, header_style="bold cyan", expand=True)
        table.add_column("Category", style="bold")
        table.add_column("Score", justify="right")
        table.add_column("Bar", min_width=20)

        categories = [
            ("Pitch Accuracy", score.pitch_accuracy),
            ("Rhythm Consistency", score.rhythm_consistency),
            ("Dynamics Control", score.dynamics_control),
        ]

        for name, value in categories:
            bar = self._score_bar(value)
            color = self._score_color(value)
            table.add_row(name, f"[{color}]{value:.1f}[/{color}]", bar)

        table.add_section()
        table.add_row(
            "[bold]Overall[/bold]",
            f"[bold {grade_color}]{score.overall:.1f}[/bold {grade_color}]",
            self._score_bar(score.overall),
        )

        grade_text = Text(f" Grade: {score.grade} ", style=f"bold {grade_color}")
        panel = Panel(
            table,
            title=f"[bold]{title}[/bold]",
            subtitle=grade_text,
            border_style=grade_color,
        )
        self.console.print(panel)

    def print_session_summary(self, session: PracticeSession) -> None:
        """Print a practice session summary."""
        self.console.print()
        self.console.rule(f"[bold cyan]Session: {session.exercise_name}[/bold cyan]")
        self.console.print()

        info_table = Table(show_header=False, box=None)
        info_table.add_column("Key", style="dim")
        info_table.add_column("Value")

        info_table.add_row("Instrument", session.instrument)
        info_table.add_row("Started", session.started_at.strftime("%Y-%m-%d %H:%M"))

        if session.duration_minutes is not None:
            info_table.add_row("Duration", f"{session.duration_minutes:.1f} min")
        if session.target_tempo:
            info_table.add_row("Target Tempo", f"{session.target_tempo:.0f} BPM")

        info_table.add_row("Performances", str(len(session.performances)))

        if session.average_score is not None:
            avg = session.average_score
            color = self._score_color(avg)
            info_table.add_row("Average Score", f"[{color}]{avg:.1f}[/{color}]")

        self.console.print(info_table)
        self.console.print()

        # Print individual scores
        for i, score_item in enumerate(session.scores):
            self.print_score(score_item, title=f"Performance {i + 1}")

    def print_notes(self, notes: list[Note], title: str = "Detected Notes") -> None:
        """Print a table of detected notes."""
        table = Table(title=title, show_header=True, header_style="bold magenta")
        table.add_column("#", style="dim", width=4)
        table.add_column("Note", style="bold")
        table.add_column("Freq (Hz)", justify="right")
        table.add_column("Time (s)", justify="right")
        table.add_column("Duration (s)", justify="right")

        for i, note in enumerate(notes[:50]):  # Limit display
            table.add_row(
                str(i + 1),
                note.full_name,
                f"{note.frequency:.2f}",
                f"{note.timestamp:.3f}",
                f"{note.duration:.3f}",
            )

        if len(notes) > 50:
            table.add_row("...", f"({len(notes)} total)", "", "", "")

        self.console.print(table)

    def print_tuning(self, tuning_results: list) -> None:
        """Print tuning results for all strings/notes."""
        table = Table(title="Tuning", show_header=True, header_style="bold green")
        table.add_column("Target", style="bold")
        table.add_column("Played (Hz)", justify="right")
        table.add_column("Cents Off", justify="right")
        table.add_column("Status")

        for result in tuning_results:
            if result.in_tune:
                status = "[green]IN TUNE[/green]"
            elif result.direction == "sharp":
                status = f"[red]SHARP +{abs(result.cents_off):.1f}c[/red]"
            else:
                status = f"[yellow]FLAT {result.cents_off:.1f}c[/yellow]"

            table.add_row(
                result.target_note.full_name,
                f"{result.played_frequency:.2f}",
                f"{result.cents_off:+.1f}",
                status,
            )

        self.console.print(table)

    def print_exercise(self, notes: list[Note], name: str) -> None:
        """Print an exercise's notes in a compact format."""
        note_names = " - ".join(n.full_name for n in notes)
        panel = Panel(
            note_names,
            title=f"[bold cyan]{name}[/bold cyan]",
            border_style="cyan",
        )
        self.console.print(panel)

    @staticmethod
    def _score_bar(value: float, width: int = 20) -> str:
        """Create a colored progress bar string."""
        filled = int(value / 100 * width)
        empty = width - filled
        color = PerformanceReport._score_color(value)
        bar = f"[{color}]{'|' * filled}[/{color}][dim]{'.' * empty}[/dim]"
        return bar

    @staticmethod
    def _score_color(value: float) -> str:
        """Return a color name based on score value."""
        if value >= 90:
            return "green"
        elif value >= 75:
            return "yellow"
        elif value >= 60:
            return "dark_orange"
        else:
            return "red"

    @staticmethod
    def _grade_color(grade: str) -> str:
        """Return a color for a letter grade."""
        if grade.startswith("A"):
            return "green"
        elif grade.startswith("B"):
            return "yellow"
        elif grade.startswith("C"):
            return "dark_orange"
        else:
            return "red"

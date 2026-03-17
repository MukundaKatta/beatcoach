"""BEATCOACH command-line interface."""

from __future__ import annotations

import uuid

import click
from rich.console import Console

from beatcoach.models import PracticeSession, TimeSignature

console = Console()


@click.group()
@click.version_option(package_name="beatcoach")
def cli() -> None:
    """BEATCOACH - AI Music Practice Coach with real-time feedback."""
    pass


@cli.command()
@click.option(
    "--instrument",
    type=click.Choice(["guitar", "violin", "ukulele", "piano"]),
    default="guitar",
    help="Instrument to tune.",
)
@click.option("--reference", default=440.0, help="A4 reference frequency in Hz.")
def tune(instrument: str, reference: float) -> None:
    """Tune your instrument with standard reference pitches."""
    from beatcoach.analyzer.tuner import InstrumentTuner
    from beatcoach.report import PerformanceReport

    tuner = InstrumentTuner(instrument=instrument, reference_a4=reference)
    report = PerformanceReport(console=console)

    console.print(f"\n[bold cyan]Tuning: {instrument.title()}[/bold cyan]")
    console.print(f"[dim]Reference: A4 = {reference} Hz[/dim]\n")

    for target in tuner.target_notes[:12]:  # Limit display for piano
        console.print(f"  {target.full_name:>4}  {target.frequency:>8.2f} Hz")

    if instrument == "piano":
        console.print(f"  [dim]... ({len(tuner.target_notes)} keys total)[/dim]")

    console.print()


@cli.command()
@click.option("--key", default="C", help="Root key (e.g. C, F#, Bb).")
@click.option("--scale", "scale_type", default="major", help="Scale type.")
@click.option("--octave", default=4, help="Starting octave.")
def practice(key: str, scale_type: str, octave: int) -> None:
    """Run a practice exercise."""
    from beatcoach.practice.exercises import PracticeExercise
    from beatcoach.report import PerformanceReport

    exercise = PracticeExercise(root=key, octave=octave)
    report = PerformanceReport(console=console)

    scale_methods = {
        "major": exercise.major_scale,
        "minor": exercise.natural_minor_scale,
        "harmonic-minor": exercise.harmonic_minor_scale,
        "melodic-minor": exercise.melodic_minor_scale,
        "pentatonic-major": exercise.pentatonic_major_scale,
        "pentatonic-minor": exercise.pentatonic_minor_scale,
        "chromatic": exercise.chromatic_scale,
    }

    method = scale_methods.get(scale_type)
    if method is None:
        console.print(
            f"[red]Unknown scale type: {scale_type}[/red]\n"
            f"Available: {', '.join(scale_methods.keys())}"
        )
        return

    notes = method()
    report.print_exercise(notes, f"{key} {scale_type} scale")


@cli.command()
@click.option("--bpm", default=120.0, help="Tempo in beats per minute.")
@click.option("--beats", default=4, help="Beats per measure (numerator).")
@click.option("--beat-unit", default=4, help="Beat unit (denominator).")
@click.option("--measures", default=4, help="Number of measures to generate.")
def metronome(bpm: float, beats: int, beat_unit: int, measures: int) -> None:
    """Start the metronome."""
    from beatcoach.practice.metronome import Metronome

    ts = TimeSignature(numerator=beats, denominator=beat_unit)
    met = Metronome(bpm=bpm, time_signature=ts)

    console.print(f"\n[bold cyan]Metronome[/bold cyan]")
    console.print(f"  Tempo:          {bpm} BPM")
    console.print(f"  Time Signature: {ts}")
    console.print(f"  Measures:       {measures}")
    console.print(f"  Accent Pattern: {met.accent_pattern}")
    console.print(f"  Beat Duration:  {met.beat_duration:.3f}s")
    console.print(f"  Measure Length:  {met.measure_duration:.3f}s\n")

    beat_times = met.get_beat_times(measures)
    console.print(f"  Beat times: {', '.join(f'{t:.2f}s' for t in beat_times[:16])}")
    if len(beat_times) > 16:
        console.print(f"  ... ({len(beat_times)} beats total)")
    console.print()


@cli.command()
@click.argument("audio_file", required=False)
def analyze(audio_file: str | None) -> None:
    """Analyze a performance (from audio file or demo)."""
    from beatcoach.report import PerformanceReport

    report = PerformanceReport(console=console)

    if audio_file:
        console.print(f"\n[bold cyan]Analyzing: {audio_file}[/bold cyan]")
        console.print("[dim]Audio file loading not yet implemented.[/dim]")
        console.print("[dim]Use the Python API for programmatic analysis.[/dim]\n")
    else:
        console.print("\n[bold cyan]BEATCOACH Analysis Demo[/bold cyan]")
        console.print("[dim]Pass an audio file to analyze a real performance.[/dim]\n")


@cli.command()
def start() -> None:
    """Start an interactive practice session."""
    session = PracticeSession(
        session_id=str(uuid.uuid4())[:8],
        exercise_name="Interactive Session",
        instrument="unknown",
    )

    console.print("\n[bold cyan]BEATCOACH - Interactive Practice Session[/bold cyan]")
    console.print(f"[dim]Session ID: {session.session_id}[/dim]")
    console.print()
    console.print("Available commands:")
    console.print("  [bold]beatcoach tune[/bold]       - Tune your instrument")
    console.print("  [bold]beatcoach practice[/bold]   - Run a practice exercise")
    console.print("  [bold]beatcoach metronome[/bold]  - Start the metronome")
    console.print("  [bold]beatcoach analyze[/bold]    - Analyze a recording")
    console.print()


@cli.command(name="scales")
def list_scales() -> None:
    """List all available scales in every key."""
    from beatcoach.practice.exercises import PracticeExercise

    console.print("\n[bold cyan]All Major Scales[/bold cyan]\n")
    for key, notes in PracticeExercise.all_major_scales().items():
        note_str = " ".join(f"{n.full_name:>4}" for n in notes)
        console.print(f"  {key:>2} major:  {note_str}")

    console.print("\n[bold cyan]All Natural Minor Scales[/bold cyan]\n")
    for key, notes in PracticeExercise.all_minor_scales().items():
        note_str = " ".join(f"{n.full_name:>4}" for n in notes)
        console.print(f"  {key:>2} minor:  {note_str}")
    console.print()


if __name__ == "__main__":
    cli()

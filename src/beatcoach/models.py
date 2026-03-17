"""Pydantic data models for BEATCOACH."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class NoteName(str, Enum):
    """The 12 chromatic note names."""

    C = "C"
    Cs = "C#"
    D = "D"
    Ds = "D#"
    E = "E"
    F = "F"
    Fs = "F#"
    G = "G"
    Gs = "G#"
    A = "A"
    As = "A#"
    B = "B"


# Ordered list for semitone arithmetic
CHROMATIC_SCALE = [
    NoteName.C,
    NoteName.Cs,
    NoteName.D,
    NoteName.Ds,
    NoteName.E,
    NoteName.F,
    NoteName.Fs,
    NoteName.G,
    NoteName.Gs,
    NoteName.A,
    NoteName.As,
    NoteName.B,
]

# Enharmonic mapping for display purposes
ENHARMONIC_MAP: dict[str, str] = {
    "C#": "Db",
    "D#": "Eb",
    "F#": "Gb",
    "G#": "Ab",
    "A#": "Bb",
}


class Note(BaseModel):
    """A musical note with pitch information."""

    name: NoteName = Field(description="Note name (e.g. C, C#, D)")
    octave: int = Field(ge=0, le=8, description="Octave number (0-8)")
    frequency: float = Field(gt=0, description="Frequency in Hz")
    duration: float = Field(default=0.0, ge=0, description="Duration in seconds")
    velocity: float = Field(
        default=0.8, ge=0, le=1.0, description="Velocity/dynamics (0-1)"
    )
    timestamp: float = Field(
        default=0.0, ge=0, description="Onset time in seconds from start"
    )

    @property
    def midi_number(self) -> int:
        """MIDI note number (A4=440Hz = MIDI 69)."""
        idx = CHROMATIC_SCALE.index(self.name)
        return (self.octave + 1) * 12 + idx

    @property
    def full_name(self) -> str:
        """Full note name with octave, e.g. 'A4'."""
        return f"{self.name.value}{self.octave}"

    @classmethod
    def from_frequency(cls, frequency: float, **kwargs) -> Note:
        """Create a Note from a frequency in Hz using A4=440 reference."""
        if frequency <= 0:
            raise ValueError("Frequency must be positive")
        a4 = 440.0
        semitones_from_a4 = 12 * _log2(frequency / a4)
        midi = round(semitones_from_a4) + 69
        octave = (midi // 12) - 1
        note_idx = midi % 12
        return cls(
            name=CHROMATIC_SCALE[note_idx],
            octave=octave,
            frequency=frequency,
            **kwargs,
        )

    @classmethod
    def from_name(cls, name: str, octave: int) -> Note:
        """Create a Note from a name and octave, computing frequency."""
        note_name = NoteName(name)
        idx = CHROMATIC_SCALE.index(note_name)
        midi = (octave + 1) * 12 + idx
        frequency = 440.0 * (2 ** ((midi - 69) / 12))
        return cls(name=note_name, octave=octave, frequency=frequency)


def _log2(x: float) -> float:
    """Base-2 logarithm."""
    import math

    return math.log2(x)


class TimeSignature(BaseModel):
    """A musical time signature."""

    numerator: int = Field(default=4, ge=1, le=16, description="Beats per measure")
    denominator: int = Field(
        default=4, description="Beat unit (4=quarter, 8=eighth, etc.)"
    )

    def __str__(self) -> str:
        return f"{self.numerator}/{self.denominator}"


class Performance(BaseModel):
    """A recorded musical performance with detected notes."""

    notes: list[Note] = Field(default_factory=list, description="Detected notes")
    sample_rate: int = Field(default=44100, description="Audio sample rate in Hz")
    duration: float = Field(default=0.0, ge=0, description="Total duration in seconds")
    detected_tempo: Optional[float] = Field(
        default=None, description="Detected tempo in BPM"
    )
    detected_time_signature: Optional[TimeSignature] = Field(
        default=None, description="Detected time signature"
    )

    @property
    def note_count(self) -> int:
        return len(self.notes)

    @property
    def pitch_range(self) -> tuple[float, float] | None:
        """Return (min_freq, max_freq) or None if no notes."""
        if not self.notes:
            return None
        freqs = [n.frequency for n in self.notes]
        return (min(freqs), max(freqs))


class ScoreBreakdown(BaseModel):
    """Breakdown of a performance score."""

    pitch_accuracy: float = Field(
        ge=0, le=100, description="Pitch accuracy score (0-100)"
    )
    rhythm_consistency: float = Field(
        ge=0, le=100, description="Rhythm consistency score (0-100)"
    )
    dynamics_control: float = Field(
        ge=0, le=100, description="Dynamics control score (0-100)"
    )
    overall: float = Field(ge=0, le=100, description="Overall score (0-100)")

    @property
    def grade(self) -> str:
        """Letter grade based on overall score."""
        if self.overall >= 95:
            return "A+"
        elif self.overall >= 90:
            return "A"
        elif self.overall >= 85:
            return "B+"
        elif self.overall >= 80:
            return "B"
        elif self.overall >= 75:
            return "C+"
        elif self.overall >= 70:
            return "C"
        elif self.overall >= 60:
            return "D"
        else:
            return "F"


class PracticeSession(BaseModel):
    """A complete practice session record."""

    session_id: str = Field(description="Unique session identifier")
    started_at: datetime = Field(
        default_factory=datetime.now, description="Session start time"
    )
    ended_at: Optional[datetime] = Field(
        default=None, description="Session end time"
    )
    exercise_name: str = Field(default="free play", description="Exercise name")
    instrument: str = Field(default="unknown", description="Instrument being played")
    performances: list[Performance] = Field(
        default_factory=list, description="Performances in this session"
    )
    scores: list[ScoreBreakdown] = Field(
        default_factory=list, description="Scores for each performance"
    )
    target_tempo: Optional[float] = Field(
        default=None, description="Target tempo in BPM"
    )
    notes_text: str = Field(default="", description="Free-form session notes")

    @property
    def duration_minutes(self) -> float | None:
        """Session duration in minutes."""
        if self.ended_at is None:
            return None
        delta = self.ended_at - self.started_at
        return delta.total_seconds() / 60

    @property
    def average_score(self) -> float | None:
        """Average overall score across performances."""
        if not self.scores:
            return None
        return sum(s.overall for s in self.scores) / len(self.scores)

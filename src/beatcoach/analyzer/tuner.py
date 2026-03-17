"""Instrument tuner with standard tuning frequencies."""

from __future__ import annotations

from dataclasses import dataclass

from beatcoach.models import Note, NoteName

# A4 concert pitch reference
A4_FREQ = 440.0

# Standard tuning frequencies for supported instruments.
# Each entry is (note_name, octave, frequency_hz).
GUITAR_STANDARD = [
    ("E", 2, 82.41),
    ("A", 2, 110.00),
    ("D", 3, 146.83),
    ("G", 3, 196.00),
    ("B", 3, 246.94),
    ("E", 4, 329.63),
]

VIOLIN_STANDARD = [
    ("G", 3, 196.00),
    ("D", 4, 293.66),
    ("A", 4, 440.00),
    ("E", 5, 659.26),
]

UKULELE_STANDARD = [
    ("G", 4, 392.00),
    ("C", 4, 261.63),
    ("E", 4, 329.63),
    ("A", 4, 440.00),
]

# Piano range: A0 (27.5 Hz) to C8 (4186.01 Hz), 88 keys
PIANO_KEY_RANGE = (21, 108)  # MIDI numbers for A0 to C8


@dataclass
class TuningResult:
    """Result of comparing a played frequency to a target note."""

    target_note: Note
    played_frequency: float
    cents_off: float
    in_tune: bool
    direction: str  # "sharp", "flat", or "in tune"

    @property
    def description(self) -> str:
        arrow = {
            "sharp": "^",
            "flat": "v",
            "in tune": "=",
        }[self.direction]
        return (
            f"{self.target_note.full_name} "
            f"({self.target_note.frequency:.2f} Hz) "
            f"{arrow} {abs(self.cents_off):.1f} cents {self.direction}"
        )


class InstrumentTuner:
    """Tuner for guitar, violin, ukulele, and piano.

    Compares a detected frequency against the nearest target note for the
    selected instrument and reports how many cents sharp or flat the pitch is.

    Parameters
    ----------
    instrument : str
        One of 'guitar', 'violin', 'ukulele', 'piano'.
    tolerance_cents : float
        Maximum deviation in cents to consider "in tune". Default is 10.
    reference_a4 : float
        Concert A4 frequency. Default is 440.0 Hz.
    """

    INSTRUMENTS = {
        "guitar": GUITAR_STANDARD,
        "violin": VIOLIN_STANDARD,
        "ukulele": UKULELE_STANDARD,
    }

    def __init__(
        self,
        instrument: str = "guitar",
        tolerance_cents: float = 10.0,
        reference_a4: float = 440.0,
    ) -> None:
        self.instrument = instrument.lower()
        self.tolerance_cents = tolerance_cents
        self.reference_a4 = reference_a4
        self._target_notes = self._build_targets()

    def _build_targets(self) -> list[Note]:
        """Build the list of target tuning notes for the instrument."""
        if self.instrument == "piano":
            return self._build_piano_targets()

        tuning_data = self.INSTRUMENTS.get(self.instrument)
        if tuning_data is None:
            raise ValueError(
                f"Unsupported instrument: {self.instrument}. "
                f"Choose from: {', '.join(list(self.INSTRUMENTS) + ['piano'])}"
            )

        notes = []
        for name, octave, freq in tuning_data:
            notes.append(Note(name=NoteName(name), octave=octave, frequency=freq))
        return notes

    def _build_piano_targets(self) -> list[Note]:
        """Build target notes for all 88 piano keys."""
        from beatcoach.models import CHROMATIC_SCALE

        notes = []
        for midi in range(PIANO_KEY_RANGE[0], PIANO_KEY_RANGE[1] + 1):
            freq = self.reference_a4 * (2 ** ((midi - 69) / 12))
            octave = (midi // 12) - 1
            note_idx = midi % 12
            notes.append(
                Note(
                    name=CHROMATIC_SCALE[note_idx],
                    octave=octave,
                    frequency=freq,
                )
            )
        return notes

    @property
    def target_notes(self) -> list[Note]:
        """Return the list of target tuning notes."""
        return list(self._target_notes)

    def tune(self, frequency: float) -> TuningResult:
        """Compare a frequency against the nearest target note.

        Parameters
        ----------
        frequency : float
            Detected frequency in Hz.

        Returns
        -------
        TuningResult
            How far the frequency is from the nearest target.
        """
        if frequency <= 0:
            raise ValueError("Frequency must be positive")

        nearest = self._find_nearest_target(frequency)
        cents = self._cents_difference(frequency, nearest.frequency)

        if abs(cents) <= self.tolerance_cents:
            direction = "in tune"
            in_tune = True
        elif cents > 0:
            direction = "sharp"
            in_tune = False
        else:
            direction = "flat"
            in_tune = False

        return TuningResult(
            target_note=nearest,
            played_frequency=frequency,
            cents_off=cents,
            in_tune=in_tune,
            direction=direction,
        )

    def _find_nearest_target(self, frequency: float) -> Note:
        """Find the target note closest in pitch to the given frequency."""
        import math

        best_note = self._target_notes[0]
        best_distance = abs(self._cents_difference(frequency, best_note.frequency))

        for note in self._target_notes[1:]:
            distance = abs(self._cents_difference(frequency, note.frequency))
            if distance < best_distance:
                best_distance = distance
                best_note = note

        return best_note

    @staticmethod
    def _cents_difference(freq_played: float, freq_target: float) -> float:
        """Compute the difference in cents between two frequencies.

        Returns positive if sharp, negative if flat.
        """
        import math

        if freq_target <= 0 or freq_played <= 0:
            return 0.0
        return 1200.0 * math.log2(freq_played / freq_target)

    def get_string_targets(self) -> list[str]:
        """Return a display-friendly list of target notes (for string instruments)."""
        return [
            f"String {i + 1}: {n.full_name} ({n.frequency:.2f} Hz)"
            for i, n in enumerate(self._target_notes)
        ]

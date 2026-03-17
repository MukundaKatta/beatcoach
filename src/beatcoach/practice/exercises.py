"""Practice exercises: scales, arpeggios, and chord progressions."""

from __future__ import annotations

from beatcoach.models import CHROMATIC_SCALE, Note, NoteName

# Interval patterns (in semitones) for scale construction
MAJOR_SCALE_INTERVALS = [0, 2, 4, 5, 7, 9, 11]
NATURAL_MINOR_SCALE_INTERVALS = [0, 2, 3, 5, 7, 8, 10]
HARMONIC_MINOR_SCALE_INTERVALS = [0, 2, 3, 5, 7, 8, 11]
MELODIC_MINOR_UP_INTERVALS = [0, 2, 3, 5, 7, 9, 11]
PENTATONIC_MAJOR_INTERVALS = [0, 2, 4, 7, 9]
PENTATONIC_MINOR_INTERVALS = [0, 3, 5, 7, 10]
CHROMATIC_INTERVALS = list(range(12))

# Arpeggio intervals
MAJOR_ARPEGGIO = [0, 4, 7]
MINOR_ARPEGGIO = [0, 3, 7]
DOMINANT_7_ARPEGGIO = [0, 4, 7, 10]
MAJOR_7_ARPEGGIO = [0, 4, 7, 11]
MINOR_7_ARPEGGIO = [0, 3, 7, 10]
DIMINISHED_ARPEGGIO = [0, 3, 6]
AUGMENTED_ARPEGGIO = [0, 4, 8]

# Common chord progressions (as Roman numeral degree offsets in semitones)
# Each progression is a list of (degree_semitones, quality) tuples
CHORD_PROGRESSIONS = {
    "I-IV-V-I": [(0, "major"), (5, "major"), (7, "major"), (0, "major")],
    "I-V-vi-IV": [(0, "major"), (7, "major"), (9, "minor"), (5, "major")],
    "ii-V-I": [(2, "minor"), (7, "major"), (0, "major")],
    "I-vi-IV-V": [(0, "major"), (9, "minor"), (5, "major"), (7, "major")],
    "I-IV-vi-V": [(0, "major"), (5, "major"), (9, "minor"), (7, "major")],
    "vi-IV-I-V": [(9, "minor"), (5, "major"), (0, "major"), (7, "major")],
    "I-ii-V-I": [(0, "major"), (2, "minor"), (7, "major"), (0, "major")],
    "12-bar-blues": [
        (0, "major"),
        (0, "major"),
        (0, "major"),
        (0, "major"),
        (5, "major"),
        (5, "major"),
        (0, "major"),
        (0, "major"),
        (7, "major"),
        (5, "major"),
        (0, "major"),
        (7, "major"),
    ],
}

# All 12 root notes
ALL_ROOTS = list(CHROMATIC_SCALE)


class PracticeExercise:
    """Generator for music practice exercises.

    Provides scales, arpeggios, and chord progressions in any key.

    Parameters
    ----------
    root : str
        Root note name (e.g., "C", "F#", "Bb").
    octave : int
        Starting octave for the exercise.
    """

    def __init__(self, root: str = "C", octave: int = 4) -> None:
        # Handle enharmonic input
        enharmonic_to_sharp = {
            "Db": "C#",
            "Eb": "D#",
            "Gb": "F#",
            "Ab": "G#",
            "Bb": "A#",
        }
        resolved = enharmonic_to_sharp.get(root, root)
        self.root = NoteName(resolved)
        self.octave = octave
        self._root_index = CHROMATIC_SCALE.index(self.root)

    def _build_notes(self, intervals: list[int], ascending: bool = True) -> list[Note]:
        """Build a list of Notes from interval pattern relative to root."""
        notes = []
        for semitone_offset in intervals:
            idx = (self._root_index + semitone_offset) % 12
            oct = self.octave + (self._root_index + semitone_offset) // 12
            note_name = CHROMATIC_SCALE[idx]
            freq = 440.0 * (2 ** (((oct + 1) * 12 + idx - 69) / 12))
            notes.append(Note(name=note_name, octave=oct, frequency=freq))
        if not ascending:
            notes = list(reversed(notes))
        return notes

    # --- Scales ---

    def major_scale(self, ascending: bool = True) -> list[Note]:
        """Generate major scale from root."""
        return self._build_notes(MAJOR_SCALE_INTERVALS, ascending)

    def natural_minor_scale(self, ascending: bool = True) -> list[Note]:
        """Generate natural minor scale from root."""
        return self._build_notes(NATURAL_MINOR_SCALE_INTERVALS, ascending)

    def harmonic_minor_scale(self, ascending: bool = True) -> list[Note]:
        """Generate harmonic minor scale from root."""
        return self._build_notes(HARMONIC_MINOR_SCALE_INTERVALS, ascending)

    def melodic_minor_scale(self) -> list[Note]:
        """Generate melodic minor scale (ascending form)."""
        return self._build_notes(MELODIC_MINOR_UP_INTERVALS)

    def pentatonic_major_scale(self) -> list[Note]:
        """Generate major pentatonic scale."""
        return self._build_notes(PENTATONIC_MAJOR_INTERVALS)

    def pentatonic_minor_scale(self) -> list[Note]:
        """Generate minor pentatonic scale."""
        return self._build_notes(PENTATONIC_MINOR_INTERVALS)

    def chromatic_scale(self) -> list[Note]:
        """Generate chromatic scale (all 12 semitones)."""
        return self._build_notes(CHROMATIC_INTERVALS)

    # --- Arpeggios ---

    def major_arpeggio(self) -> list[Note]:
        """Generate major arpeggio (1-3-5)."""
        return self._build_notes(MAJOR_ARPEGGIO)

    def minor_arpeggio(self) -> list[Note]:
        """Generate minor arpeggio (1-b3-5)."""
        return self._build_notes(MINOR_ARPEGGIO)

    def dominant_7_arpeggio(self) -> list[Note]:
        """Generate dominant 7th arpeggio (1-3-5-b7)."""
        return self._build_notes(DOMINANT_7_ARPEGGIO)

    def major_7_arpeggio(self) -> list[Note]:
        """Generate major 7th arpeggio (1-3-5-7)."""
        return self._build_notes(MAJOR_7_ARPEGGIO)

    def minor_7_arpeggio(self) -> list[Note]:
        """Generate minor 7th arpeggio (1-b3-5-b7)."""
        return self._build_notes(MINOR_7_ARPEGGIO)

    def diminished_arpeggio(self) -> list[Note]:
        """Generate diminished arpeggio (1-b3-b5)."""
        return self._build_notes(DIMINISHED_ARPEGGIO)

    def augmented_arpeggio(self) -> list[Note]:
        """Generate augmented arpeggio (1-3-#5)."""
        return self._build_notes(AUGMENTED_ARPEGGIO)

    # --- Chord Progressions ---

    def chord_progression(self, name: str) -> list[list[Note]]:
        """Generate a chord progression by name.

        Parameters
        ----------
        name : str
            Progression name (e.g. "I-IV-V-I", "ii-V-I").

        Returns
        -------
        list[list[Note]]
            Each inner list is the notes of one chord in the progression.
        """
        prog = CHORD_PROGRESSIONS.get(name)
        if prog is None:
            available = ", ".join(CHORD_PROGRESSIONS.keys())
            raise ValueError(
                f"Unknown progression '{name}'. Available: {available}"
            )

        chords = []
        for semitone_offset, quality in prog:
            chord_root_idx = (self._root_index + semitone_offset) % 12
            oct = self.octave + (self._root_index + semitone_offset) // 12

            if quality == "major":
                intervals = MAJOR_ARPEGGIO
            elif quality == "minor":
                intervals = MINOR_ARPEGGIO
            else:
                intervals = MAJOR_ARPEGGIO

            chord_notes = []
            for interval in intervals:
                idx = (chord_root_idx + interval) % 12
                note_oct = oct + (chord_root_idx + interval) // 12
                note_name = CHROMATIC_SCALE[idx]
                freq = 440.0 * (2 ** (((note_oct + 1) * 12 + idx - 69) / 12))
                chord_notes.append(
                    Note(name=note_name, octave=note_oct, frequency=freq)
                )
            chords.append(chord_notes)

        return chords

    @staticmethod
    def list_progressions() -> list[str]:
        """Return all available chord progression names."""
        return list(CHORD_PROGRESSIONS.keys())

    @staticmethod
    def all_major_scales() -> dict[str, list[Note]]:
        """Generate all 12 major scales."""
        result = {}
        for root in ALL_ROOTS:
            ex = PracticeExercise(root=root.value, octave=4)
            result[root.value] = ex.major_scale()
        return result

    @staticmethod
    def all_minor_scales() -> dict[str, list[Note]]:
        """Generate all 12 natural minor scales."""
        result = {}
        for root in ALL_ROOTS:
            ex = PracticeExercise(root=root.value, octave=4)
            result[root.value] = ex.natural_minor_scale()
        return result

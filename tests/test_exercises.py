"""Tests for practice exercises."""

import pytest

from beatcoach.models import NoteName
from beatcoach.practice.exercises import (
    ALL_ROOTS,
    CHORD_PROGRESSIONS,
    PracticeExercise,
)


class TestPracticeExercise:
    def test_c_major_scale(self):
        ex = PracticeExercise(root="C", octave=4)
        scale = ex.major_scale()
        assert len(scale) == 7
        expected_names = ["C", "D", "E", "F", "G", "A", "B"]
        actual_names = [n.name.value for n in scale]
        assert actual_names == expected_names

    def test_a_minor_scale(self):
        ex = PracticeExercise(root="A", octave=4)
        scale = ex.natural_minor_scale()
        assert len(scale) == 7
        expected = ["A", "B", "C", "D", "E", "F", "G"]
        actual = [n.name.value for n in scale]
        assert actual == expected

    def test_g_major_scale(self):
        ex = PracticeExercise(root="G", octave=4)
        scale = ex.major_scale()
        assert len(scale) == 7
        assert scale[0].name == NoteName.G
        assert scale[6].name == NoteName("F#")

    def test_descending_scale(self):
        ex = PracticeExercise(root="C", octave=4)
        asc = ex.major_scale(ascending=True)
        desc = ex.major_scale(ascending=False)
        assert len(desc) == 7
        assert desc[0].name == asc[-1].name
        assert desc[-1].name == asc[0].name

    def test_harmonic_minor(self):
        ex = PracticeExercise(root="A", octave=4)
        scale = ex.harmonic_minor_scale()
        assert len(scale) == 7
        # Harmonic minor has raised 7th: G#
        assert scale[6].name == NoteName("G#")

    def test_pentatonic_major(self):
        ex = PracticeExercise(root="C", octave=4)
        scale = ex.pentatonic_major_scale()
        assert len(scale) == 5

    def test_pentatonic_minor(self):
        ex = PracticeExercise(root="A", octave=4)
        scale = ex.pentatonic_minor_scale()
        assert len(scale) == 5

    def test_chromatic_scale(self):
        ex = PracticeExercise(root="C", octave=4)
        scale = ex.chromatic_scale()
        assert len(scale) == 12

    def test_major_arpeggio(self):
        ex = PracticeExercise(root="C", octave=4)
        arp = ex.major_arpeggio()
        assert len(arp) == 3
        names = [n.name.value for n in arp]
        assert names == ["C", "E", "G"]

    def test_minor_arpeggio(self):
        ex = PracticeExercise(root="A", octave=4)
        arp = ex.minor_arpeggio()
        assert len(arp) == 3
        names = [n.name.value for n in arp]
        assert names == ["A", "C", "E"]

    def test_dominant_7_arpeggio(self):
        ex = PracticeExercise(root="G", octave=4)
        arp = ex.dominant_7_arpeggio()
        assert len(arp) == 4

    def test_all_12_major_scales(self):
        scales = PracticeExercise.all_major_scales()
        assert len(scales) == 12
        for key, notes in scales.items():
            assert len(notes) == 7, f"{key} major scale has {len(notes)} notes"

    def test_all_12_minor_scales(self):
        scales = PracticeExercise.all_minor_scales()
        assert len(scales) == 12
        for key, notes in scales.items():
            assert len(notes) == 7, f"{key} minor scale has {len(notes)} notes"

    def test_enharmonic_input(self):
        ex_sharp = PracticeExercise(root="F#", octave=4)
        ex_flat = PracticeExercise(root="Gb", octave=4)
        assert ex_sharp.root == ex_flat.root

    def test_chord_progression_I_IV_V_I(self):
        ex = PracticeExercise(root="C", octave=4)
        chords = ex.chord_progression("I-IV-V-I")
        assert len(chords) == 4
        # First chord should be C major
        assert chords[0][0].name == NoteName.C

    def test_chord_progression_ii_V_I(self):
        ex = PracticeExercise(root="C", octave=4)
        chords = ex.chord_progression("ii-V-I")
        assert len(chords) == 3

    def test_12_bar_blues(self):
        ex = PracticeExercise(root="A", octave=3)
        chords = ex.chord_progression("12-bar-blues")
        assert len(chords) == 12

    def test_invalid_progression(self):
        ex = PracticeExercise(root="C", octave=4)
        with pytest.raises(ValueError, match="Unknown progression"):
            ex.chord_progression("nonexistent")

    def test_list_progressions(self):
        progs = PracticeExercise.list_progressions()
        assert "I-IV-V-I" in progs
        assert "ii-V-I" in progs
        assert "12-bar-blues" in progs

    def test_all_roots_count(self):
        assert len(ALL_ROOTS) == 12

    def test_frequencies_increase_in_scale(self):
        ex = PracticeExercise(root="C", octave=4)
        scale = ex.major_scale()
        freqs = [n.frequency for n in scale]
        for i in range(len(freqs) - 1):
            assert freqs[i] < freqs[i + 1], (
                f"Frequency should increase: {freqs[i]} >= {freqs[i+1]}"
            )

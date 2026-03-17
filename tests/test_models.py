"""Tests for beatcoach data models."""

import pytest

from beatcoach.models import (
    CHROMATIC_SCALE,
    Note,
    NoteName,
    Performance,
    PracticeSession,
    ScoreBreakdown,
    TimeSignature,
)


class TestNote:
    def test_from_frequency_a4(self):
        note = Note.from_frequency(440.0)
        assert note.name == NoteName.A
        assert note.octave == 4
        assert note.frequency == 440.0

    def test_from_frequency_c4(self):
        note = Note.from_frequency(261.63)
        assert note.name == NoteName.C
        assert note.octave == 4

    def test_from_frequency_e2(self):
        note = Note.from_frequency(82.41)
        assert note.name == NoteName.E
        assert note.octave == 2

    def test_from_name_a4(self):
        note = Note.from_name("A", 4)
        assert note.name == NoteName.A
        assert note.octave == 4
        assert abs(note.frequency - 440.0) < 0.01

    def test_from_name_c4(self):
        note = Note.from_name("C", 4)
        assert abs(note.frequency - 261.63) < 0.1

    def test_midi_number(self):
        a4 = Note.from_name("A", 4)
        assert a4.midi_number == 69

        c4 = Note.from_name("C", 4)
        assert c4.midi_number == 60

    def test_full_name(self):
        note = Note.from_name("F#", 3)
        assert note.full_name == "F#3"

    def test_invalid_frequency_raises(self):
        with pytest.raises(ValueError):
            Note.from_frequency(-1.0)

        with pytest.raises(ValueError):
            Note.from_frequency(0.0)


class TestTimeSignature:
    def test_default(self):
        ts = TimeSignature()
        assert ts.numerator == 4
        assert ts.denominator == 4
        assert str(ts) == "4/4"

    def test_waltz(self):
        ts = TimeSignature(numerator=3, denominator=4)
        assert str(ts) == "3/4"


class TestPerformance:
    def test_empty(self):
        perf = Performance()
        assert perf.note_count == 0
        assert perf.pitch_range is None

    def test_with_notes(self):
        notes = [
            Note.from_name("C", 4),
            Note.from_name("E", 4),
            Note.from_name("G", 4),
        ]
        perf = Performance(notes=notes, duration=3.0)
        assert perf.note_count == 3
        low, high = perf.pitch_range
        assert low < high


class TestScoreBreakdown:
    def test_grade_a_plus(self):
        s = ScoreBreakdown(
            pitch_accuracy=98, rhythm_consistency=96, dynamics_control=95, overall=96
        )
        assert s.grade == "A+"

    def test_grade_f(self):
        s = ScoreBreakdown(
            pitch_accuracy=30, rhythm_consistency=40, dynamics_control=20, overall=30
        )
        assert s.grade == "F"

    def test_all_grades(self):
        thresholds = [
            (96, "A+"), (92, "A"), (87, "B+"), (82, "B"),
            (77, "C+"), (72, "C"), (65, "D"), (50, "F"),
        ]
        for score, expected_grade in thresholds:
            s = ScoreBreakdown(
                pitch_accuracy=score,
                rhythm_consistency=score,
                dynamics_control=score,
                overall=score,
            )
            assert s.grade == expected_grade, f"Score {score} should be {expected_grade}"


class TestPracticeSession:
    def test_average_score(self):
        session = PracticeSession(session_id="test-1")
        assert session.average_score is None

        session.scores.append(
            ScoreBreakdown(
                pitch_accuracy=80, rhythm_consistency=90,
                dynamics_control=85, overall=85,
            )
        )
        session.scores.append(
            ScoreBreakdown(
                pitch_accuracy=90, rhythm_consistency=95,
                dynamics_control=90, overall=92,
            )
        )
        assert session.average_score == pytest.approx(88.5)

    def test_chromatic_scale_has_12_notes(self):
        assert len(CHROMATIC_SCALE) == 12

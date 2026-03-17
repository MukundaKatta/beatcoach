"""Tests for performance scorer."""

import pytest

from beatcoach.models import Note, NoteName, Performance
from beatcoach.practice.scorer import PerformanceScorer


def _make_note(name: str, octave: int, freq: float, **kwargs) -> Note:
    return Note(name=NoteName(name), octave=octave, frequency=freq, **kwargs)


class TestPerformanceScorer:
    def test_perfect_pitch_score(self):
        scorer = PerformanceScorer()
        expected = [
            _make_note("C", 4, 261.63),
            _make_note("E", 4, 329.63),
            _make_note("G", 4, 392.00),
        ]
        played = [
            _make_note("C", 4, 261.63),
            _make_note("E", 4, 329.63),
            _make_note("G", 4, 392.00),
        ]
        perf = Performance(notes=played)
        score = scorer.score(perf, expected_notes=expected)
        assert score.pitch_accuracy == pytest.approx(100.0, abs=1.0)

    def test_imperfect_pitch_score(self):
        scorer = PerformanceScorer()
        expected = [_make_note("A", 4, 440.0)]
        # 20 cents sharp of A4
        sharp_freq = 440.0 * (2 ** (20 / 1200))
        played = [_make_note("A", 4, sharp_freq)]
        perf = Performance(notes=played)
        score = scorer.score(perf, expected_notes=expected)
        assert 0 < score.pitch_accuracy < 100

    def test_perfect_rhythm(self):
        scorer = PerformanceScorer(target_tempo=120.0)
        notes = [
            _make_note("C", 4, 261.63, timestamp=0.0),
            _make_note("D", 4, 293.66, timestamp=0.5),
            _make_note("E", 4, 329.63, timestamp=1.0),
            _make_note("F", 4, 349.23, timestamp=1.5),
        ]
        perf = Performance(notes=notes)
        score = scorer.score(perf)
        assert score.rhythm_consistency > 90.0

    def test_poor_rhythm(self):
        scorer = PerformanceScorer(target_tempo=120.0)
        # Very uneven timing
        notes = [
            _make_note("C", 4, 261.63, timestamp=0.0),
            _make_note("D", 4, 293.66, timestamp=0.3),
            _make_note("E", 4, 329.63, timestamp=1.2),
            _make_note("F", 4, 349.23, timestamp=1.4),
        ]
        perf = Performance(notes=notes)
        score = scorer.score(perf)
        assert score.rhythm_consistency < 80.0

    def test_consistent_dynamics(self):
        scorer = PerformanceScorer()
        notes = [
            _make_note("C", 4, 261.63, velocity=0.8),
            _make_note("D", 4, 293.66, velocity=0.8),
            _make_note("E", 4, 329.63, velocity=0.8),
        ]
        perf = Performance(notes=notes)
        score = scorer.score(perf)
        assert score.dynamics_control == pytest.approx(100.0, abs=1.0)

    def test_inconsistent_dynamics(self):
        scorer = PerformanceScorer()
        notes = [
            _make_note("C", 4, 261.63, velocity=0.2),
            _make_note("D", 4, 293.66, velocity=0.9),
            _make_note("E", 4, 329.63, velocity=0.3),
            _make_note("F", 4, 349.23, velocity=1.0),
        ]
        perf = Performance(notes=notes)
        score = scorer.score(perf)
        assert score.dynamics_control < 80.0

    def test_overall_is_weighted_average(self):
        scorer = PerformanceScorer()
        notes = [
            _make_note("C", 4, 261.63, timestamp=0.0, velocity=0.8),
            _make_note("E", 4, 329.63, timestamp=0.5, velocity=0.8),
            _make_note("G", 4, 392.00, timestamp=1.0, velocity=0.8),
        ]
        expected = [
            _make_note("C", 4, 261.63),
            _make_note("E", 4, 329.63),
            _make_note("G", 4, 392.00),
        ]
        perf = Performance(notes=notes)
        score = scorer.score(perf, expected_notes=expected)

        expected_overall = (
            0.45 * score.pitch_accuracy
            + 0.35 * score.rhythm_consistency
            + 0.20 * score.dynamics_control
        )
        assert score.overall == pytest.approx(expected_overall, abs=0.2)

    def test_empty_performance(self):
        scorer = PerformanceScorer()
        perf = Performance(notes=[])
        score = scorer.score(perf)
        assert score.pitch_accuracy == 0.0

    def test_single_note_performance(self):
        scorer = PerformanceScorer()
        perf = Performance(notes=[_make_note("A", 4, 440.0)])
        score = scorer.score(perf)
        # Should not crash, should return reasonable defaults
        assert 0 <= score.overall <= 100

    def test_grade_assignment(self):
        scorer = PerformanceScorer()
        notes = [
            _make_note("C", 4, 261.63, timestamp=0.0, velocity=0.8),
            _make_note("E", 4, 329.63, timestamp=0.5, velocity=0.8),
            _make_note("G", 4, 392.00, timestamp=1.0, velocity=0.8),
        ]
        perf = Performance(notes=notes)
        score = scorer.score(perf)
        assert score.grade in ("A+", "A", "B+", "B", "C+", "C", "D", "F")

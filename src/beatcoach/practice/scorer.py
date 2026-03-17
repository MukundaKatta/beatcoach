"""Performance scorer: grades pitch accuracy, rhythm consistency, and dynamics."""

from __future__ import annotations

import math

import numpy as np

from beatcoach.models import Note, Performance, ScoreBreakdown


class PerformanceScorer:
    """Scores a musical performance against a target exercise.

    Evaluates three dimensions:
    - Pitch accuracy: how close played notes are to expected pitches (in cents)
    - Rhythm consistency: how tightly onsets align to the beat grid
    - Dynamics control: how consistent the velocity/loudness is

    Parameters
    ----------
    pitch_tolerance_cents : float
        Maximum cents deviation for a "perfect" pitch score.
    rhythm_tolerance_ms : float
        Maximum timing deviation in milliseconds for "perfect" rhythm.
    target_tempo : float | None
        Expected tempo in BPM for rhythm evaluation.
    """

    # Weights for overall score
    WEIGHT_PITCH = 0.45
    WEIGHT_RHYTHM = 0.35
    WEIGHT_DYNAMICS = 0.20

    def __init__(
        self,
        pitch_tolerance_cents: float = 25.0,
        rhythm_tolerance_ms: float = 50.0,
        target_tempo: float | None = None,
    ) -> None:
        self.pitch_tolerance_cents = pitch_tolerance_cents
        self.rhythm_tolerance_ms = rhythm_tolerance_ms
        self.target_tempo = target_tempo

    def score(
        self,
        performance: Performance,
        expected_notes: list[Note] | None = None,
    ) -> ScoreBreakdown:
        """Score a performance, optionally against expected notes.

        Parameters
        ----------
        performance : Performance
            The recorded performance to evaluate.
        expected_notes : list[Note] | None
            Target notes for pitch comparison. If None, pitch accuracy
            is evaluated based on pitch stability alone.

        Returns
        -------
        ScoreBreakdown
            Detailed score breakdown.
        """
        pitch_score = self._score_pitch(performance.notes, expected_notes)
        rhythm_score = self._score_rhythm(performance)
        dynamics_score = self._score_dynamics(performance.notes)

        overall = (
            self.WEIGHT_PITCH * pitch_score
            + self.WEIGHT_RHYTHM * rhythm_score
            + self.WEIGHT_DYNAMICS * dynamics_score
        )

        return ScoreBreakdown(
            pitch_accuracy=round(pitch_score, 1),
            rhythm_consistency=round(rhythm_score, 1),
            dynamics_control=round(dynamics_score, 1),
            overall=round(overall, 1),
        )

    def _score_pitch(
        self,
        played_notes: list[Note],
        expected_notes: list[Note] | None,
    ) -> float:
        """Score pitch accuracy (0-100).

        If expected_notes are provided, scores based on cent deviation from
        each target. Otherwise, scores based on how stable each note's pitch
        is (proximity to nearest semitone).
        """
        if not played_notes:
            return 0.0

        if expected_notes:
            return self._score_pitch_against_target(played_notes, expected_notes)

        # Score based on proximity to nearest semitone
        total_score = 0.0
        for note in played_notes:
            nearest = _nearest_semitone_freq(note.frequency)
            cents = abs(_cents_diff(note.frequency, nearest))
            # Map cents to score: 0 cents = 100, tolerance = 50, 2*tolerance = 0
            note_score = max(0.0, 100.0 * (1.0 - cents / (2 * self.pitch_tolerance_cents)))
            total_score += note_score

        return total_score / len(played_notes)

    def _score_pitch_against_target(
        self,
        played: list[Note],
        expected: list[Note],
    ) -> float:
        """Score each played note against the nearest expected note."""
        n = min(len(played), len(expected))
        if n == 0:
            return 0.0

        total = 0.0
        for i in range(n):
            cents = abs(_cents_diff(played[i].frequency, expected[i].frequency))
            score = max(0.0, 100.0 * (1.0 - cents / (2 * self.pitch_tolerance_cents)))
            total += score

        # Penalty for wrong number of notes
        count_ratio = n / max(len(played), len(expected))
        return (total / n) * count_ratio

    def _score_rhythm(self, performance: Performance) -> float:
        """Score rhythm consistency (0-100).

        Evaluates how evenly spaced the note onsets are relative to
        the target or detected tempo.
        """
        notes = performance.notes
        if len(notes) < 2:
            return 50.0  # Insufficient data

        onset_times = np.array(sorted(n.timestamp for n in notes))
        ioi = np.diff(onset_times)
        ioi = ioi[ioi > 0]

        if len(ioi) < 1:
            return 50.0

        tempo = self.target_tempo or performance.detected_tempo
        if tempo and tempo > 0:
            expected_ioi = 60.0 / tempo
            deviations_ms = np.abs(ioi - expected_ioi) * 1000.0
        else:
            # No tempo reference: evaluate consistency of IOIs
            median_ioi = np.median(ioi)
            if median_ioi <= 0:
                return 50.0
            deviations_ms = np.abs(ioi - median_ioi) * 1000.0

        # Map average deviation to score
        avg_deviation = float(np.mean(deviations_ms))
        tolerance = self.rhythm_tolerance_ms
        score = max(0.0, 100.0 * (1.0 - avg_deviation / (2 * tolerance)))
        return score

    def _score_dynamics(self, notes: list[Note]) -> float:
        """Score dynamics control (0-100).

        Evaluates how consistent the note velocities are. A perfectly
        even performance scores 100. High variance reduces the score.
        """
        if len(notes) < 2:
            return 80.0  # Default for insufficient data

        velocities = np.array([n.velocity for n in notes])
        std = float(np.std(velocities))

        # Map standard deviation to score
        # std=0 -> 100, std=0.3 -> 0
        score = max(0.0, 100.0 * (1.0 - std / 0.3))
        return score


def _nearest_semitone_freq(frequency: float) -> float:
    """Compute the frequency of the nearest semitone to a given frequency."""
    if frequency <= 0:
        return 440.0
    semitones = 12 * math.log2(frequency / 440.0)
    nearest_semitone = round(semitones)
    return 440.0 * (2 ** (nearest_semitone / 12))


def _cents_diff(freq_a: float, freq_b: float) -> float:
    """Compute signed cents difference: positive if freq_a is sharp of freq_b."""
    if freq_a <= 0 or freq_b <= 0:
        return 0.0
    return 1200.0 * math.log2(freq_a / freq_b)

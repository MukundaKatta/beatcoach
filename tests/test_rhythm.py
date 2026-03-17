"""Tests for rhythm analysis."""

import numpy as np
import pytest

from beatcoach.analyzer.rhythm import RhythmAnalyzer
from beatcoach.models import Note, NoteName, TimeSignature


class TestRhythmAnalyzer:
    def setup_method(self):
        self.analyzer = RhythmAnalyzer(sample_rate=44100)

    def test_estimate_tempo_120bpm(self):
        # Create perfectly spaced onsets at 120 BPM (0.5s apart)
        onset_times = np.arange(0, 5.0, 0.5)
        tempo = self.analyzer.estimate_tempo(onset_times)
        assert tempo is not None
        assert abs(tempo - 120.0) < 5.0, f"Expected ~120 BPM, got {tempo:.1f}"

    def test_estimate_tempo_90bpm(self):
        # 90 BPM = 0.667s between beats
        onset_times = np.arange(0, 5.0, 60.0 / 90.0)
        tempo = self.analyzer.estimate_tempo(onset_times)
        assert tempo is not None
        assert abs(tempo - 90.0) < 5.0

    def test_estimate_tempo_insufficient_data(self):
        result = self.analyzer.estimate_tempo(np.array([0.0, 0.5]))
        # Only 2 onsets, minimum is 3
        assert result is None

    def test_detect_time_signature_4_4(self):
        # Even beats at 120 BPM
        onset_times = np.arange(0, 8.0, 0.5)
        ts = self.analyzer.detect_time_signature(onset_times, 120.0)
        assert isinstance(ts, TimeSignature)
        # Should detect a simple meter
        assert ts.numerator in (2, 3, 4, 6)

    def test_beat_deviations_perfect(self):
        onset_times = np.arange(0, 4.0, 0.5)
        devs = self.analyzer.compute_beat_deviations(onset_times, 120.0)
        assert len(devs) == len(onset_times)
        # Perfect timing should have near-zero deviations
        assert np.allclose(devs, 0.0, atol=1e-10)

    def test_beat_deviations_with_errors(self):
        # Add some jitter
        rng = np.random.default_rng(42)
        ideal = np.arange(0, 4.0, 0.5)
        jittered = ideal + rng.normal(0, 0.02, len(ideal))
        devs = self.analyzer.compute_beat_deviations(jittered, 120.0)
        assert len(devs) == len(jittered)
        assert np.max(np.abs(devs)) < 0.1

    def test_extract_rhythm_from_notes(self):
        notes = [
            Note(name=NoteName.C, octave=4, frequency=261.63, timestamp=0.0),
            Note(name=NoteName.E, octave=4, frequency=329.63, timestamp=0.5),
            Note(name=NoteName.G, octave=4, frequency=392.00, timestamp=1.0),
        ]
        times = self.analyzer.extract_rhythm_from_notes(notes)
        assert len(times) == 3
        np.testing.assert_array_almost_equal(times, [0.0, 0.5, 1.0])

    def test_extract_rhythm_empty(self):
        times = self.analyzer.extract_rhythm_from_notes([])
        assert len(times) == 0

    def test_empty_signal_no_onsets(self):
        signal = np.zeros(44100)
        onsets = self.analyzer.detect_onsets(signal)
        assert len(onsets) == 0

    def test_detect_onsets_with_clicks(self):
        sr = 44100
        signal = np.zeros(sr * 2)  # 2 seconds
        # Place sharp transients at known positions
        click_times = [0.2, 0.7, 1.2, 1.7]
        for t in click_times:
            idx = int(t * sr)
            # Short burst
            burst_len = 200
            burst = np.sin(2 * np.pi * 1000 * np.arange(burst_len) / sr) * 0.8
            signal[idx : idx + burst_len] += burst

        onsets = self.analyzer.detect_onsets(signal)
        # Should detect approximately 4 onsets
        assert len(onsets) >= 2

"""Tests for pitch detection."""

import numpy as np
import pytest

from beatcoach.analyzer.pitch import PitchDetector


class TestPitchDetector:
    def setup_method(self):
        self.sample_rate = 44100
        self.detector = PitchDetector(sample_rate=self.sample_rate)

    def _generate_sine(self, freq: float, duration: float = 0.1) -> np.ndarray:
        """Generate a pure sine wave at a given frequency."""
        t = np.arange(int(duration * self.sample_rate)) / self.sample_rate
        return np.sin(2 * np.pi * freq * t)

    def test_detect_a4(self):
        signal = self._generate_sine(440.0, duration=0.2)
        notes = self.detector.detect_pitch(signal)
        assert len(notes) > 0
        freqs = [n.frequency for n in notes]
        avg_freq = np.mean(freqs)
        assert abs(avg_freq - 440.0) < 5.0, f"Expected ~440 Hz, got {avg_freq:.1f}"

    def test_detect_c4(self):
        signal = self._generate_sine(261.63, duration=0.2)
        notes = self.detector.detect_pitch(signal)
        assert len(notes) > 0
        avg_freq = np.mean([n.frequency for n in notes])
        assert abs(avg_freq - 261.63) < 5.0

    def test_detect_e2_low(self):
        signal = self._generate_sine(82.41, duration=0.3)
        notes = self.detector.detect_pitch(signal)
        assert len(notes) > 0
        avg_freq = np.mean([n.frequency for n in notes])
        assert abs(avg_freq - 82.41) < 3.0

    def test_silence_no_pitch(self):
        signal = np.zeros(self.sample_rate)
        notes = self.detector.detect_pitch(signal)
        # Silence should produce no notes (or very few spurious)
        assert len(notes) == 0

    def test_noise_minimal_detection(self):
        rng = np.random.default_rng(42)
        signal = rng.normal(0, 0.01, self.sample_rate)
        notes = self.detector.detect_pitch(signal)
        # Low-amplitude noise should not produce many confident detections
        # (threshold handles this)
        assert len(notes) < 10

    def test_single_frame_detection(self):
        signal = self._generate_sine(440.0, duration=0.1)
        frame = signal[:2048]
        freq = self.detector.detect_pitch_single(frame)
        assert freq is not None
        assert abs(freq - 440.0) < 5.0

    def test_autocorrelation_peak(self):
        signal = self._generate_sine(440.0, duration=0.1)
        frame = signal[:2048]
        acf = self.detector.autocorrelation(frame)
        # ACF should peak at lag 0 (normalized to 1.0)
        assert acf[0] == pytest.approx(1.0)
        # Should have a secondary peak near lag = sample_rate/freq
        expected_lag = int(self.sample_rate / 440.0)
        # Check neighborhood
        neighborhood = acf[expected_lag - 3 : expected_lag + 4]
        assert np.max(neighborhood) > 0.8

    def test_short_frame_returns_none(self):
        frame = np.zeros(100)
        result = self.detector.detect_pitch_single(frame)
        assert result is None

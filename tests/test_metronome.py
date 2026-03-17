"""Tests for metronome."""

import numpy as np
import pytest

from beatcoach.models import TimeSignature
from beatcoach.practice.metronome import Metronome


class TestMetronome:
    def test_default_creation(self):
        met = Metronome()
        assert met.bpm == 120.0
        assert met.time_signature.numerator == 4
        assert met.time_signature.denominator == 4

    def test_beat_duration(self):
        met = Metronome(bpm=120.0)
        assert met.beat_duration == pytest.approx(0.5)

        met60 = Metronome(bpm=60.0)
        assert met60.beat_duration == pytest.approx(1.0)

    def test_measure_duration(self):
        met = Metronome(bpm=120.0)
        assert met.measure_duration == pytest.approx(2.0)

        met_waltz = Metronome(
            bpm=120.0,
            time_signature=TimeSignature(numerator=3, denominator=4),
        )
        assert met_waltz.measure_duration == pytest.approx(1.5)

    def test_generate_click(self):
        met = Metronome()
        click = met.generate_click(1000.0)
        assert len(click) > 0
        assert isinstance(click, np.ndarray)
        # Click should start loud and decay
        assert abs(click[0]) > abs(click[-1])

    def test_generate_measure(self):
        met = Metronome(bpm=120.0)
        measure = met.generate_measure()
        expected_samples = int(0.5 * 44100) * 4  # 4 beats at 0.5s each
        assert len(measure) == expected_samples

    def test_generate_track(self):
        met = Metronome(bpm=120.0)
        track = met.generate_track(num_measures=4)
        measure = met.generate_measure()
        assert len(track) == len(measure) * 4

    def test_generate_track_zero_measures(self):
        met = Metronome()
        track = met.generate_track(num_measures=0)
        assert len(track) == 0

    def test_beat_times(self):
        met = Metronome(bpm=120.0)
        times = met.get_beat_times(num_measures=2)
        assert len(times) == 8  # 4 beats * 2 measures
        assert times[0] == pytest.approx(0.0)
        assert times[1] == pytest.approx(0.5)
        assert times[4] == pytest.approx(2.0)

    def test_waltz_beat_times(self):
        ts = TimeSignature(numerator=3, denominator=4)
        met = Metronome(bpm=120.0, time_signature=ts)
        times = met.get_beat_times(num_measures=1)
        assert len(times) == 3

    def test_default_accent_pattern_4_4(self):
        met = Metronome()
        assert met.accent_pattern[0] == 1.0
        assert all(a == 0.7 for a in met.accent_pattern[1:])

    def test_default_accent_pattern_6_8(self):
        ts = TimeSignature(numerator=6, denominator=8)
        met = Metronome(time_signature=ts)
        assert met.accent_pattern[0] == 1.0
        assert met.accent_pattern[3] == 0.85

    def test_custom_accent_pattern(self):
        accent = [1.0, 0.5, 0.8, 0.5]
        met = Metronome(accent_pattern=accent)
        assert met.accent_pattern == accent

    def test_wrong_accent_pattern_length(self):
        with pytest.raises(ValueError, match="Accent pattern length"):
            Metronome(accent_pattern=[1.0, 0.5, 0.5])  # 3 for 4/4

    def test_invalid_bpm(self):
        with pytest.raises(ValueError):
            Metronome(bpm=0)
        with pytest.raises(ValueError):
            Metronome(bpm=-60)

    def test_set_tempo(self):
        met = Metronome(bpm=120.0)
        met.set_tempo(140.0)
        assert met.bpm == 140.0

    def test_set_time_signature(self):
        met = Metronome()
        met.set_time_signature(3, 4)
        assert met.time_signature.numerator == 3
        assert len(met.accent_pattern) == 3

    def test_repr(self):
        met = Metronome(bpm=90)
        r = repr(met)
        assert "90" in r
        assert "4/4" in r

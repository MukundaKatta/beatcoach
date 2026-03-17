"""Metronome with configurable tempo, time signature, and accent patterns."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from beatcoach.models import TimeSignature


class Metronome:
    """A digital metronome that generates click tracks.

    Produces audio click tracks with configurable tempo, time signature,
    and accent patterns. The downbeat (beat 1) uses a higher-pitched click
    to distinguish it from other beats.

    Parameters
    ----------
    bpm : float
        Tempo in beats per minute.
    time_signature : TimeSignature
        Time signature (default 4/4).
    sample_rate : int
        Audio sample rate in Hz.
    accent_pattern : list[float] | None
        Per-beat velocity multipliers. Length must match time signature numerator.
        If None, default accent pattern is used (beat 1 accented).
    """

    # Click tone parameters
    CLICK_FREQ_HIGH = 1500.0  # Hz, downbeat / accent
    CLICK_FREQ_LOW = 1000.0  # Hz, regular beat
    CLICK_DURATION = 0.03  # seconds

    def __init__(
        self,
        bpm: float = 120.0,
        time_signature: TimeSignature | None = None,
        sample_rate: int = 44100,
        accent_pattern: list[float] | None = None,
    ) -> None:
        if bpm <= 0:
            raise ValueError("BPM must be positive")

        self.bpm = bpm
        self.time_signature = time_signature or TimeSignature(numerator=4, denominator=4)
        self.sample_rate = sample_rate

        if accent_pattern is not None:
            if len(accent_pattern) != self.time_signature.numerator:
                raise ValueError(
                    f"Accent pattern length ({len(accent_pattern)}) must match "
                    f"time signature numerator ({self.time_signature.numerator})"
                )
            self.accent_pattern = accent_pattern
        else:
            self.accent_pattern = self._default_accent_pattern()

    def _default_accent_pattern(self) -> list[float]:
        """Create default accent pattern: strong on beat 1, medium elsewhere."""
        n = self.time_signature.numerator
        pattern = [0.7] * n
        pattern[0] = 1.0  # Downbeat accent

        # Additional accent conventions
        if n == 6:
            # 6/8: compound duple, accent beats 1 and 4
            pattern[3] = 0.85
        elif n == 3:
            # 3/4: waltz feel
            pattern[0] = 1.0
        return pattern

    @property
    def beat_duration(self) -> float:
        """Duration of one beat in seconds."""
        return 60.0 / self.bpm

    @property
    def measure_duration(self) -> float:
        """Duration of one full measure in seconds."""
        return self.beat_duration * self.time_signature.numerator

    def generate_click(
        self, frequency: float, amplitude: float = 1.0
    ) -> NDArray[np.float64]:
        """Generate a single click tone.

        Parameters
        ----------
        frequency : float
            Click tone frequency in Hz.
        amplitude : float
            Amplitude multiplier (0-1).

        Returns
        -------
        NDArray
            Audio samples for one click.
        """
        num_samples = int(self.CLICK_DURATION * self.sample_rate)
        t = np.arange(num_samples) / self.sample_rate
        # Sine tone with exponential decay envelope
        envelope = np.exp(-t * 50)
        click = amplitude * envelope * np.sin(2 * np.pi * frequency * t)
        return click

    def generate_measure(self) -> NDArray[np.float64]:
        """Generate audio for one complete measure.

        Returns
        -------
        NDArray
            Audio samples for one measure.
        """
        beat_samples = int(self.beat_duration * self.sample_rate)
        total_samples = beat_samples * self.time_signature.numerator
        measure = np.zeros(total_samples)

        for beat_idx in range(self.time_signature.numerator):
            accent = self.accent_pattern[beat_idx]
            freq = (
                self.CLICK_FREQ_HIGH if beat_idx == 0 else self.CLICK_FREQ_LOW
            )
            click = self.generate_click(freq, accent)

            start = beat_idx * beat_samples
            end = start + len(click)
            if end <= total_samples:
                measure[start:end] += click

        return measure

    def generate_track(self, num_measures: int = 4) -> NDArray[np.float64]:
        """Generate a click track spanning multiple measures.

        Parameters
        ----------
        num_measures : int
            Number of measures to generate.

        Returns
        -------
        NDArray
            Audio samples for the click track.
        """
        if num_measures <= 0:
            return np.array([])

        measure = self.generate_measure()
        track = np.tile(measure, num_measures)
        return track

    def get_beat_times(self, num_measures: int = 1) -> list[float]:
        """Return the onset times of all beats in the given number of measures.

        Parameters
        ----------
        num_measures : int
            Number of measures.

        Returns
        -------
        list[float]
            Beat onset times in seconds.
        """
        times = []
        for m in range(num_measures):
            for b in range(self.time_signature.numerator):
                t = m * self.measure_duration + b * self.beat_duration
                times.append(t)
        return times

    def set_tempo(self, bpm: float) -> None:
        """Update the tempo."""
        if bpm <= 0:
            raise ValueError("BPM must be positive")
        self.bpm = bpm

    def set_time_signature(self, numerator: int, denominator: int) -> None:
        """Update the time signature and regenerate default accent pattern."""
        self.time_signature = TimeSignature(numerator=numerator, denominator=denominator)
        self.accent_pattern = self._default_accent_pattern()

    def __repr__(self) -> str:
        return (
            f"Metronome(bpm={self.bpm}, "
            f"time_signature={self.time_signature}, "
            f"accent={self.accent_pattern})"
        )

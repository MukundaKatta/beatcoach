"""Pitch detection using autocorrelation and the YIN algorithm."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from beatcoach.models import Note


class PitchDetector:
    """Detects fundamental frequency from audio using the YIN algorithm.

    The YIN algorithm (de Cheveigne & Kawahara, 2002) estimates the fundamental
    frequency of a monophonic audio signal through an improved autocorrelation
    method with cumulative mean normalized difference.

    Parameters
    ----------
    sample_rate : int
        Audio sample rate in Hz.
    frame_size : int
        Number of samples per analysis frame.
    hop_size : int
        Number of samples between successive frames.
    threshold : float
        YIN absolute threshold for pitch detection (lower = stricter).
    min_freq : float
        Minimum detectable frequency in Hz.
    max_freq : float
        Maximum detectable frequency in Hz.
    """

    def __init__(
        self,
        sample_rate: int = 44100,
        frame_size: int = 2048,
        hop_size: int = 512,
        threshold: float = 0.15,
        min_freq: float = 50.0,
        max_freq: float = 5000.0,
    ) -> None:
        self.sample_rate = sample_rate
        self.frame_size = frame_size
        self.hop_size = hop_size
        self.threshold = threshold
        self.min_freq = min_freq
        self.max_freq = max_freq

        # Pre-compute lag bounds from frequency bounds
        self.min_lag = max(2, int(sample_rate / max_freq))
        self.max_lag = min(frame_size // 2, int(sample_rate / min_freq))

    def detect_pitch(self, signal: NDArray[np.float64]) -> list[Note]:
        """Detect pitches across all frames of the signal.

        Parameters
        ----------
        signal : NDArray
            Mono audio signal, expected to be normalized to [-1, 1].

        Returns
        -------
        list[Note]
            Detected notes with frequency, name, octave, and timestamp.
        """
        notes: list[Note] = []
        num_frames = max(0, (len(signal) - self.frame_size) // self.hop_size + 1)

        for i in range(num_frames):
            start = i * self.hop_size
            frame = signal[start : start + self.frame_size]
            freq = self._yin_pitch(frame)
            if freq is not None:
                timestamp = start / self.sample_rate
                note = Note.from_frequency(freq, timestamp=timestamp)
                notes.append(note)

        return notes

    def detect_pitch_single(self, frame: NDArray[np.float64]) -> float | None:
        """Detect pitch of a single frame.

        Returns frequency in Hz or None if no pitch detected.
        """
        return self._yin_pitch(frame)

    def _yin_pitch(self, frame: NDArray[np.float64]) -> float | None:
        """Run YIN algorithm on a single frame.

        Steps:
        1. Compute the difference function d(tau).
        2. Compute the cumulative mean normalized difference function d'(tau).
        3. Apply absolute threshold to find the first dip below threshold.
        4. Refine with parabolic interpolation.
        """
        if len(frame) < self.frame_size:
            return None

        # Step 1: Difference function
        diff = self._difference_function(frame)

        # Step 2: Cumulative mean normalized difference
        cmnd = self._cumulative_mean_normalized_difference(diff)

        # Step 3: Absolute threshold
        tau = self._absolute_threshold(cmnd)
        if tau is None:
            return None

        # Step 4: Parabolic interpolation for sub-sample accuracy
        tau_refined = self._parabolic_interpolation(cmnd, tau)

        freq = self.sample_rate / tau_refined
        if self.min_freq <= freq <= self.max_freq:
            return freq
        return None

    def _difference_function(self, frame: NDArray[np.float64]) -> NDArray[np.float64]:
        """Compute YIN difference function using FFT for efficiency.

        d(tau) = sum_{j=0}^{W-1} (x_j - x_{j+tau})^2

        This is computed efficiently via:
        d(tau) = r(0) + r_shifted(0) - 2*r(tau)
        where r is the autocorrelation computed via FFT.
        """
        n = len(frame)
        # Zero-pad for FFT-based autocorrelation
        fft_size = 1
        while fft_size < 2 * n:
            fft_size *= 2

        fft_frame = np.fft.rfft(frame, fft_size)
        acf = np.fft.irfft(fft_frame * np.conj(fft_frame))[:n]

        # Compute cumulative sum of squared values for the shifted energy term
        sq = frame ** 2
        cum_sq = np.cumsum(sq)

        # d(tau) = energy_x + energy_shifted(tau) - 2 * acf(tau)
        # energy_x = sum(x[0:W]^2) for each window
        # energy_shifted(tau) = sum(x[tau:tau+W]^2)
        half = n // 2
        diff = np.zeros(half)
        diff[0] = 0.0
        energy_total = cum_sq[-1]  # sum of all x^2
        for tau in range(1, half):
            # Energy of x[0:n-tau]
            energy_start = cum_sq[n - tau - 1]
            # Energy of x[tau:n]
            energy_shifted = energy_total - cum_sq[tau - 1]
            diff[tau] = energy_start + energy_shifted - 2.0 * acf[tau]

        return diff

    def _cumulative_mean_normalized_difference(
        self, diff: NDArray[np.float64]
    ) -> NDArray[np.float64]:
        """Compute cumulative mean normalized difference function d'(tau).

        d'(tau) = 1 if tau == 0
        d'(tau) = d(tau) / ((1/tau) * sum_{j=1}^{tau} d(j))  otherwise
        """
        n = len(diff)
        cmnd = np.ones(n)
        running_sum = 0.0

        for tau in range(1, n):
            running_sum += diff[tau]
            if running_sum == 0:
                cmnd[tau] = 1.0
            else:
                cmnd[tau] = diff[tau] * tau / running_sum

        return cmnd

    def _absolute_threshold(self, cmnd: NDArray[np.float64]) -> int | None:
        """Find the first tau where cmnd dips below threshold.

        Searches within [min_lag, max_lag] for the first valley below threshold.
        If no value is below threshold, returns the global minimum in the range.
        """
        search_start = max(self.min_lag, 1)
        search_end = min(self.max_lag, len(cmnd) - 1)

        if search_start >= search_end:
            return None

        # Find first dip below threshold
        for tau in range(search_start, search_end):
            if cmnd[tau] < self.threshold:
                # Walk to the local minimum
                while tau + 1 < search_end and cmnd[tau + 1] < cmnd[tau]:
                    tau += 1
                return tau

        # Fallback: global minimum in search range
        segment = cmnd[search_start:search_end]
        if len(segment) == 0:
            return None
        min_val = np.min(segment)
        if min_val < 0.5:  # Only accept if reasonably periodic
            return int(search_start + np.argmin(segment))
        return None

    def _parabolic_interpolation(
        self, cmnd: NDArray[np.float64], tau: int
    ) -> float:
        """Refine lag estimate with parabolic interpolation around tau.

        Fits a parabola through (tau-1, tau, tau+1) and returns the vertex.
        """
        if tau <= 0 or tau >= len(cmnd) - 1:
            return float(tau)

        alpha = cmnd[tau - 1]
        beta = cmnd[tau]
        gamma = cmnd[tau + 1]

        denominator = 2.0 * (2.0 * beta - alpha - gamma)
        if abs(denominator) < 1e-10:
            return float(tau)

        adjustment = (alpha - gamma) / denominator
        return tau + adjustment

    def autocorrelation(self, frame: NDArray[np.float64]) -> NDArray[np.float64]:
        """Compute the normalized autocorrelation of a frame via FFT.

        Useful for direct inspection and debugging.
        """
        n = len(frame)
        fft_size = 1
        while fft_size < 2 * n:
            fft_size *= 2

        fft_frame = np.fft.rfft(frame, fft_size)
        acf = np.fft.irfft(fft_frame * np.conj(fft_frame))[:n]

        if acf[0] != 0:
            acf = acf / acf[0]

        return acf

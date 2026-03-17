"""Rhythm analysis for beat timing, tempo, and time signature detection."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray
from scipy import signal as sp_signal

from beatcoach.models import Note, TimeSignature


class RhythmAnalyzer:
    """Analyzes rhythmic properties of a musical performance.

    Detects beat onsets, estimates tempo (BPM), and infers time signature
    from a sequence of detected notes or from raw audio onset times.

    Parameters
    ----------
    sample_rate : int
        Audio sample rate in Hz.
    min_bpm : float
        Minimum expected tempo.
    max_bpm : float
        Maximum expected tempo.
    """

    def __init__(
        self,
        sample_rate: int = 44100,
        min_bpm: float = 40.0,
        max_bpm: float = 240.0,
    ) -> None:
        self.sample_rate = sample_rate
        self.min_bpm = min_bpm
        self.max_bpm = max_bpm

    def detect_onsets(
        self, signal: NDArray[np.float64], hop_size: int = 512
    ) -> NDArray[np.float64]:
        """Detect onset times from audio using spectral flux.

        Parameters
        ----------
        signal : NDArray
            Mono audio signal.
        hop_size : int
            Hop size for STFT frames.

        Returns
        -------
        NDArray
            Array of onset times in seconds.
        """
        frame_size = hop_size * 4

        # Compute STFT magnitudes
        num_frames = max(0, (len(signal) - frame_size) // hop_size + 1)
        if num_frames < 2:
            return np.array([])

        window = np.hanning(frame_size)
        magnitudes = []
        for i in range(num_frames):
            start = i * hop_size
            frame = signal[start : start + frame_size] * window
            spectrum = np.abs(np.fft.rfft(frame))
            magnitudes.append(spectrum)

        magnitudes_arr = np.array(magnitudes)

        # Spectral flux: sum of positive differences between consecutive frames
        flux = np.zeros(num_frames)
        for i in range(1, num_frames):
            diff = magnitudes_arr[i] - magnitudes_arr[i - 1]
            flux[i] = np.sum(np.maximum(diff, 0))

        # Normalize
        if np.max(flux) > 0:
            flux = flux / np.max(flux)

        # Peak-pick onsets above adaptive threshold
        threshold = np.median(flux) + 0.3 * np.std(flux)
        threshold = max(threshold, 0.1)

        onset_frames: list[int] = []
        min_gap_frames = int(0.05 * self.sample_rate / hop_size)  # 50ms minimum gap

        for i in range(1, len(flux) - 1):
            if (
                flux[i] > threshold
                and flux[i] >= flux[i - 1]
                and flux[i] >= flux[i + 1]
            ):
                if not onset_frames or (i - onset_frames[-1]) >= min_gap_frames:
                    onset_frames.append(i)

        onset_times = np.array(onset_frames, dtype=np.float64) * hop_size / self.sample_rate
        return onset_times

    def estimate_tempo(self, onset_times: NDArray[np.float64]) -> float | None:
        """Estimate tempo in BPM from onset times using inter-onset intervals.

        Uses autocorrelation of the onset times to find the dominant periodicity.

        Parameters
        ----------
        onset_times : NDArray
            Array of onset times in seconds.

        Returns
        -------
        float or None
            Estimated tempo in BPM, or None if insufficient data.
        """
        if len(onset_times) < 3:
            return None

        # Compute inter-onset intervals
        ioi = np.diff(onset_times)
        ioi = ioi[ioi > 0]

        if len(ioi) < 2:
            return None

        # Convert BPM bounds to IOI bounds (in seconds)
        min_ioi = 60.0 / self.max_bpm
        max_ioi = 60.0 / self.min_bpm

        # Filter IOIs within expected range
        valid_ioi = ioi[(ioi >= min_ioi) & (ioi <= max_ioi)]
        if len(valid_ioi) < 2:
            # Try using raw IOIs
            valid_ioi = ioi

        # Use autocorrelation-based approach on a quantized onset signal
        duration = onset_times[-1] - onset_times[0]
        if duration <= 0:
            return None

        resolution = 0.01  # 10ms resolution
        num_bins = int(duration / resolution) + 1
        onset_signal = np.zeros(num_bins)

        for t in onset_times:
            idx = int((t - onset_times[0]) / resolution)
            if 0 <= idx < num_bins:
                onset_signal[idx] = 1.0

        # Autocorrelation
        min_lag = int(min_ioi / resolution)
        max_lag = min(int(max_ioi / resolution), num_bins // 2)

        if min_lag >= max_lag or max_lag >= num_bins:
            # Fallback: median IOI
            median_ioi = float(np.median(valid_ioi))
            return 60.0 / median_ioi if median_ioi > 0 else None

        acf = np.correlate(onset_signal, onset_signal, mode="full")
        acf = acf[len(onset_signal) - 1 :]  # Keep non-negative lags

        # Find dominant peak in valid lag range
        search = acf[min_lag : max_lag + 1]
        if len(search) == 0:
            return None

        peak_lag = min_lag + int(np.argmax(search))
        beat_period = peak_lag * resolution
        bpm = 60.0 / beat_period if beat_period > 0 else None

        return bpm

    def detect_time_signature(
        self, onset_times: NDArray[np.float64], tempo_bpm: float
    ) -> TimeSignature:
        """Infer time signature from onset pattern and tempo.

        Groups onsets into measures and looks for accent patterns consistent
        with common time signatures (4/4, 3/4, 6/8, 2/4).

        Parameters
        ----------
        onset_times : NDArray
            Onset times in seconds.
        tempo_bpm : float
            Estimated tempo in BPM.

        Returns
        -------
        TimeSignature
            Detected or best-guess time signature.
        """
        if len(onset_times) < 4 or tempo_bpm <= 0:
            return TimeSignature(numerator=4, denominator=4)

        beat_duration = 60.0 / tempo_bpm
        ioi = np.diff(onset_times)

        # Quantize IOIs to beat fractions
        beat_fractions = ioi / beat_duration

        # Count how many onsets per "strong beat" cycle
        # Test candidate time signatures
        candidates = [
            TimeSignature(numerator=4, denominator=4),
            TimeSignature(numerator=3, denominator=4),
            TimeSignature(numerator=2, denominator=4),
            TimeSignature(numerator=6, denominator=8),
        ]

        best_sig = candidates[0]
        best_score = float("inf")

        for sig in candidates:
            if sig.denominator == 8:
                beats_per_measure = sig.numerator / 2  # compound meter
            else:
                beats_per_measure = sig.numerator

            measure_duration = beats_per_measure * beat_duration

            # Measure how well onsets align to measure boundaries
            total_error = 0.0
            for t in onset_times:
                phase = (t - onset_times[0]) % measure_duration
                # Distance to nearest measure boundary
                dist = min(phase, measure_duration - phase)
                total_error += dist ** 2

            avg_error = total_error / len(onset_times)
            if avg_error < best_score:
                best_score = avg_error
                best_sig = sig

        return best_sig

    def extract_rhythm_from_notes(self, notes: list[Note]) -> NDArray[np.float64]:
        """Extract onset times from a list of Note objects.

        Parameters
        ----------
        notes : list[Note]
            Detected notes with timestamps.

        Returns
        -------
        NDArray
            Sorted array of onset times in seconds.
        """
        if not notes:
            return np.array([])
        times = np.array([n.timestamp for n in notes])
        return np.sort(times)

    def compute_beat_deviations(
        self, onset_times: NDArray[np.float64], tempo_bpm: float
    ) -> NDArray[np.float64]:
        """Compute how far each onset deviates from the nearest ideal beat.

        Parameters
        ----------
        onset_times : NDArray
            Onset times in seconds.
        tempo_bpm : float
            Target tempo in BPM.

        Returns
        -------
        NDArray
            Signed deviations in seconds (positive = late, negative = early).
        """
        if len(onset_times) == 0 or tempo_bpm <= 0:
            return np.array([])

        beat_period = 60.0 / tempo_bpm
        start = onset_times[0]

        deviations = np.zeros(len(onset_times))
        for i, t in enumerate(onset_times):
            elapsed = t - start
            nearest_beat = round(elapsed / beat_period) * beat_period
            deviations[i] = elapsed - nearest_beat

        return deviations

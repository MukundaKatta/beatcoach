"""Tests for instrument tuner."""

import pytest

from beatcoach.analyzer.tuner import InstrumentTuner


class TestInstrumentTuner:
    def test_guitar_string_count(self):
        tuner = InstrumentTuner(instrument="guitar")
        assert len(tuner.target_notes) == 6

    def test_violin_string_count(self):
        tuner = InstrumentTuner(instrument="violin")
        assert len(tuner.target_notes) == 4

    def test_ukulele_string_count(self):
        tuner = InstrumentTuner(instrument="ukulele")
        assert len(tuner.target_notes) == 4

    def test_piano_key_count(self):
        tuner = InstrumentTuner(instrument="piano")
        assert len(tuner.target_notes) == 88

    def test_unsupported_instrument(self):
        with pytest.raises(ValueError, match="Unsupported instrument"):
            InstrumentTuner(instrument="banjo")

    def test_tune_in_tune(self):
        tuner = InstrumentTuner(instrument="guitar")
        result = tuner.tune(82.41)  # E2 frequency
        assert result.target_note.full_name == "E2"
        assert abs(result.cents_off) < 1.0
        assert result.in_tune is True
        assert result.direction == "in tune"

    def test_tune_sharp(self):
        tuner = InstrumentTuner(instrument="guitar")
        # 85 Hz is sharp of E2 (82.41 Hz)
        result = tuner.tune(85.0)
        assert result.direction == "sharp"
        assert result.cents_off > 0

    def test_tune_flat(self):
        tuner = InstrumentTuner(instrument="guitar")
        # 80 Hz is flat of E2 (82.41 Hz)
        result = tuner.tune(80.0)
        assert result.direction == "flat"
        assert result.cents_off < 0

    def test_tune_a4_exactly(self):
        tuner = InstrumentTuner(instrument="guitar")
        result = tuner.tune(440.0)
        assert result.target_note.full_name == "E4"  # Nearest guitar string
        # 440 Hz is between B3 and E4, closer to E4
        # Actually E4 on guitar is 329.63, so A4 (440) is closest to E4
        # Let's check it finds the right note

    def test_piano_a4(self):
        tuner = InstrumentTuner(instrument="piano")
        result = tuner.tune(440.0)
        assert result.target_note.full_name == "A4"
        assert result.in_tune is True

    def test_piano_middle_c(self):
        tuner = InstrumentTuner(instrument="piano")
        result = tuner.tune(261.63)
        assert result.target_note.full_name == "C4"
        assert abs(result.cents_off) < 1.0

    def test_cents_calculation(self):
        cents = InstrumentTuner._cents_difference(440.0, 440.0)
        assert cents == pytest.approx(0.0)

        # One semitone up = 100 cents
        cents = InstrumentTuner._cents_difference(
            440.0 * 2 ** (1 / 12), 440.0
        )
        assert cents == pytest.approx(100.0, abs=0.1)

        # One octave up = 1200 cents
        cents = InstrumentTuner._cents_difference(880.0, 440.0)
        assert cents == pytest.approx(1200.0, abs=0.1)

    def test_invalid_frequency(self):
        tuner = InstrumentTuner(instrument="guitar")
        with pytest.raises(ValueError):
            tuner.tune(-1.0)

    def test_string_targets_display(self):
        tuner = InstrumentTuner(instrument="guitar")
        strings = tuner.get_string_targets()
        assert len(strings) == 6
        assert "String 1" in strings[0]
        assert "E2" in strings[0]

    def test_custom_reference(self):
        tuner = InstrumentTuner(instrument="piano", reference_a4=432.0)
        result = tuner.tune(432.0)
        assert result.target_note.full_name == "A4"
        assert result.in_tune is True

    def test_tuning_result_description(self):
        tuner = InstrumentTuner(instrument="guitar")
        result = tuner.tune(82.41)
        desc = result.description
        assert "E2" in desc
        assert "Hz" in desc

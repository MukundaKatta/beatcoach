# BEATCOACH

AI Music Practice Coach with real-time feedback.

BEATCOACH analyzes your musical performance in real time, providing feedback on pitch accuracy, rhythm consistency, and dynamics. It supports multiple instruments and includes a library of practice exercises covering scales, arpeggios, and chord progressions across all 12 major and minor keys.

## Features

- **Pitch Detection** - Autocorrelation/YIN algorithm for accurate fundamental frequency detection
- **Rhythm Analysis** - Beat timing, tempo estimation, and time signature detection
- **Instrument Tuner** - Standard tuning references for guitar, violin, ukulele, and piano
- **Practice Exercises** - Scales (major/minor), arpeggios, and chord progressions in all 12 keys
- **Metronome** - Configurable tempo, time signature, and accent patterns
- **Performance Scoring** - Grades for pitch accuracy, rhythm consistency, and dynamics

## Installation

```bash
pip install -e .
```

Or install dependencies directly:

```bash
pip install -r requirements.txt
```

## Usage

```bash
# Start the interactive coach
beatcoach start

# Tune your instrument
beatcoach tune --instrument guitar

# Run a practice exercise
beatcoach practice --exercise "C major scale"

# Start the metronome
beatcoach metronome --bpm 120 --time-signature 4/4

# Analyze a performance
beatcoach analyze recording.wav
```

## Project Structure

```
src/beatcoach/
    cli.py              # Command-line interface (Click)
    models.py           # Pydantic data models
    report.py           # Performance report generation
    analyzer/
        pitch.py        # PitchDetector (YIN/autocorrelation)
        rhythm.py       # RhythmAnalyzer (tempo/beat/time signature)
        tuner.py        # InstrumentTuner (standard frequencies)
    practice/
        exercises.py    # PracticeExercise (scales/arpeggios/chords)
        metronome.py    # Metronome (tempo/time signature/accent)
        scorer.py       # PerformanceScorer (pitch/rhythm/dynamics)
```

## Supported Instruments

| Instrument | Tuning |
|---|---|
| Guitar (standard) | E2 A2 D3 G3 B3 E4 |
| Violin | G3 D4 A4 E5 |
| Ukulele | G4 C4 E4 A4 |
| Piano | A0 (27.5 Hz) to C8 (4186 Hz) |

## License

MIT

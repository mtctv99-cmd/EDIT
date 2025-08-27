# Placeholder for FunASR integration
from pathlib import Path


def transcribe(audio: Path) -> Path:
    """Run ASR and return path to SRT file."""
    # TODO: call FunASR
    return audio.with_suffix('.srt')

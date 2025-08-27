# Placeholder for Gemini translation
from pathlib import Path


def translate_srt(src: Path, dest: Path):
    """Translate subtitle file to Vietnamese."""
    # TODO: call Gemini API
    dest.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")

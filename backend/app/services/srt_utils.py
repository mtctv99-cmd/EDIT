from pathlib import Path
from typing import List


def read_srt(path: Path) -> List[str]:
    return path.read_text(encoding="utf-8").splitlines()


def write_srt(lines: List[str], path: Path):
    path.write_text("\n".join(lines), encoding="utf-8")

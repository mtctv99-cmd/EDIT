import subprocess
from pathlib import Path


def run_cmd(args: list[str]):
    cmd = ["ffmpeg", "-y"] + args
    subprocess.run(cmd, check=True)


def probe(path: Path) -> dict:
    cmd = ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", str(path)]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    import json
    return json.loads(result.stdout)

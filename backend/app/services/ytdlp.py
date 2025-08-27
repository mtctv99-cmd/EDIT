import subprocess
from pathlib import Path


def download(url: str, output: Path):
    cmd = ["yt-dlp", url, "-o", str(output)]
    subprocess.run(cmd, check=True)

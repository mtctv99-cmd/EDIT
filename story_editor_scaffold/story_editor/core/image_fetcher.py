import os
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


def fetch_images(url: str, output_dir: str):
    """Download images from a web page.

    This is a simplified implementation that fetches all ``<img>`` elements on the
    page and saves them into ``output_dir`` with sequential filenames
    ``page_XXX.ext``. It does not execute JavaScript or handle complex lazy-load
    schemes but works for many static sites.
    """
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    output = []
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    for img in soup.find_all("img"):
        src = img.get("data-src") or img.get("src")
        if not src:
            continue
        img_url = urljoin(resp.url, src)
        try:
            r = requests.get(img_url, timeout=10)
            r.raise_for_status()
        except Exception:
            continue
        ext = os.path.splitext(img_url.split("?")[0])[1]
        if ext.lower() not in [".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp"]:
            ext = ".png"
        fname = f"page_{len(output)+1:03d}{ext}"
        path = Path(output_dir) / fname
        with open(path, "wb") as f:
            f.write(r.content)
        output.append(str(path))
    return output

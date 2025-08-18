from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from pathlib import Path

def load_pixmap_scaled(path: str | Path, max_width: int = 520) -> QPixmap:
    pix = QPixmap(str(path))
    if pix.isNull():
        return pix
    if pix.width() > max_width:
        return pix.scaledToWidth(max_width, Qt.SmoothTransformation)
    return pix

def parse_srt_to_text_blocks(srt_content: str) -> list[str]:
    blocks = []
    current_block = []
    for line in srt_content.splitlines():
        line = line.strip()
        if not line:
            if current_block:
                blocks.append(" ".join(current_block))
                current_block = []
            continue
        if line.isdigit() or "-->" in line:
            continue
        current_block.append(line)
    if current_block:
        blocks.append(" ".join(current_block))
    return blocks

def split_txt_to_paragraphs(txt_content: str) -> list[str]:
    paragraphs = []
    current_paragraph = []
    for line in txt_content.splitlines():
        line = line.strip()
        if not line:
            if current_paragraph:
                paragraphs.append(" ".join(current_paragraph))
                current_paragraph = []
            continue
        current_paragraph.append(line)
    if current_paragraph:
        paragraphs.append(" ".join(current_paragraph))
    return paragraphs
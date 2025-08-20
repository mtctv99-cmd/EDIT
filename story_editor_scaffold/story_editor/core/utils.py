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

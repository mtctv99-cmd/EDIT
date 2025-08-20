from PyQt5.QtWidgets import QWidget, QVBoxLayout, QScrollArea
from .widgets import RowWidget

class EditorScreen(QWidget):
    def __init__(self, host: 'MainWindow'):
        super().__init__()
        self.host = host
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.container = QWidget()
        self.vbox = QVBoxLayout(self.container)
        self.vbox.setContentsMargins(8, 8, 8, 50)
        self.vbox.setSpacing(6)
        self.scroll.setWidget(self.container)

        layout = QVBoxLayout(self)
        layout.addWidget(self.scroll)

    def load_from_manager(self):
        while self.vbox.count():
            w = self.vbox.takeAt(0).widget()
            if w: w.deleteLater()
        for img, txt in self.host.project_manager.data:
            self.vbox.addWidget(RowWidget(self, image_path=img, text=txt))
        if not self.host.project_manager.data:
            self.vbox.addWidget(RowWidget(self))

    def add_row(self, image_path=None, text=""):
        self.vbox.addWidget(RowWidget(self, image_path, text))

    def insert_row(self, ref_row, above: bool):
        index = self.vbox.indexOf(ref_row)
        if index == -1: return
        target = index if above else index + 1
        self.vbox.insertWidget(target, RowWidget(self))

    def delete_row(self, row):
        row.setParent(None)
        row.deleteLater()

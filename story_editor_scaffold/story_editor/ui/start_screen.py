from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QListWidget, QListWidgetItem, QFileDialog
from PyQt5.QtCore import Qt
from ..core.settings import Settings

class StartScreen(QWidget):
    def __init__(self, host: 'MainWindow'):
        super().__init__()
        self.host = host
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        title = QLabel("📖 Story Editor")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 28px; font-weight: bold; margin-bottom: 30px;")
        layout.addWidget(title)

        btn_new = QPushButton("➕ New Project")
        btn_new.setFixedSize(220, 60)
        btn_new.clicked.connect(lambda: self.host.open_editor(new=True))
        layout.addWidget(btn_new, alignment=Qt.AlignCenter)

        btn_open = QPushButton("📂 Open Project")
        btn_open.setFixedSize(220, 60)
        btn_open.clicked.connect(self.open_project)
        layout.addWidget(btn_open, alignment=Qt.AlignCenter)

        recent_label = QLabel("Recent Projects")
        recent_label.setStyleSheet("font-size: 16px; margin-top: 40px;")
        layout.addWidget(recent_label, alignment=Qt.AlignCenter)

        self.recent_list = QListWidget()
        self.recent_list.setMaximumWidth(500)
        self.recent_list.itemDoubleClicked.connect(self.open_recent)
        layout.addWidget(self.recent_list, alignment=Qt.AlignCenter)

        self.refresh_recent()

    def refresh_recent(self):
        self.recent_list.clear()
        for path in Settings.get_recent():
            self.recent_list.addItem(QListWidgetItem(path))

    def open_project(self):
        file, _ = QFileDialog.getOpenFileName(self, "Open Project", "", "Project (*.json)")
        if file:
            Settings.add_recent(file)
            self.host.open_editor(new=False, filepath=file)
            self.refresh_recent()

    def open_recent(self, item):
        self.host.open_editor(new=False, filepath=item.text())

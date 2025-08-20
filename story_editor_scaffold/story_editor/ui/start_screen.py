from pathlib import Path

from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QFileDialog,
    QGroupBox,
    QFrame,
    QHBoxLayout,
    QSpacerItem,
    QSizePolicy,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon

from ..core.settings import Settings

class StartScreen(QWidget):
    def __init__(self, host: 'MainWindow'):
        super().__init__()
        self.host = host
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        res_dir = Path(__file__).resolve().parent.parent / "resources"

        title = QLabel("Story Editor")
        title.setAlignment(Qt.AlignCenter)
        title.setObjectName("titleLabel")
        layout.addWidget(title)

        actions_frame = QFrame()
        actions_layout = QVBoxLayout(actions_frame)

        btn_new = QPushButton("New Project")
        btn_new.setObjectName("newButton")
        btn_new.setFixedSize(220, 60)
        btn_new.setIcon(QIcon(str(res_dir / "new_project.svg")))
        btn_new.clicked.connect(lambda: self.host.open_editor(new=True))
        actions_layout.addWidget(btn_new, alignment=Qt.AlignCenter)

        btn_open = QPushButton("Open Project")
        btn_open.setObjectName("openButton")
        btn_open.setFixedSize(220, 60)
        btn_open.setIcon(QIcon(str(res_dir / "open_project.svg")))
        btn_open.clicked.connect(self.open_project)
        actions_layout.addWidget(btn_open, alignment=Qt.AlignCenter)

        layout.addWidget(actions_frame, alignment=Qt.AlignCenter)

        layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        recent_group = QGroupBox()
        recent_layout = QVBoxLayout(recent_group)

        header_widget = QFrame()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        lbl_icon = QLabel()
        lbl_icon.setPixmap(QIcon(str(res_dir / "recent_projects.svg")).pixmap(16, 16))
        header_layout.addWidget(lbl_icon)
        recent_label = QLabel("Recent Projects")
        recent_label.setObjectName("recentLabel")
        header_layout.addWidget(recent_label)
        header_layout.addStretch()
        recent_layout.addWidget(header_widget)

        self.recent_list = QListWidget()
        self.recent_list.setObjectName("recentList")
        self.recent_list.setMaximumWidth(500)
        self.recent_list.itemDoubleClicked.connect(self.open_recent)
        recent_layout.addWidget(self.recent_list)

        layout.addWidget(recent_group, alignment=Qt.AlignCenter)

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

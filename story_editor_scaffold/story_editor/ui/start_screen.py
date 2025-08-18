from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QListWidget, QListWidgetItem, QFileDialog, QFrame, QHBoxLayout, QToolButton, QMenu, QAction
from PyQt5.QtCore import Qt
from ..core.settings import Settings
import os

class StartScreen(QWidget):
    def __init__(self, host: 'MainWindow'):
        super().__init__()
        self.host = host
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignCenter)
        main_layout.setSpacing(20) # Add some spacing between sections

        # Hero Section
        hero_title = QLabel("Story Editor")
        hero_title.setObjectName("HeroTitle")
        hero_title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(hero_title)

        hero_subtitle = QLabel("Biên tập truyện nhanh: Sáng tạo, chỉnh sửa, và xuất bản câu chuyện của bạn.")
        hero_subtitle.setObjectName("HeroSubtitle")
        hero_subtitle.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(hero_subtitle)

        # Action Card
        action_card = QFrame(self)
        action_card.setObjectName("ActionCard")
        action_card_layout = QHBoxLayout(action_card)
        action_card_layout.setContentsMargins(20, 20, 20, 20)
        action_card_layout.setSpacing(20)
        action_card.setFixedSize(500, 100) # Fixed size for the card

        btn_new = QPushButton("➕ New Project")
        btn_new.setObjectName("PrimaryButton")
        btn_new.setMinimumHeight(44)
        btn_new.clicked.connect(lambda: self.host.open_editor(new=True))
        action_card_layout.addWidget(btn_new)

        btn_open = QPushButton("📂 Open Project")
        btn_open.setObjectName("PrimaryButton")
        btn_open.setMinimumHeight(44)
        btn_open.clicked.connect(self.open_project)
        action_card_layout.addWidget(btn_open)
        
        main_layout.addWidget(action_card, alignment=Qt.AlignCenter)

        # Recent Projects Section
        recent_header_layout = QHBoxLayout()
        recent_header_layout.setContentsMargins(0, 0, 0, 0)
        recent_header_layout.setSpacing(10)
        recent_header_layout.setAlignment(Qt.AlignCenter)

        recent_label = QLabel("Gần đây")
        recent_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        recent_header_layout.addWidget(recent_label)

        btn_clear_recent = QToolButton(self)
        btn_clear_recent.setText("Xoá danh sách")
        btn_clear_recent.clicked.connect(self.clear_recent_projects)
        recent_header_layout.addWidget(btn_clear_recent)
        
        main_layout.addLayout(recent_header_layout)

        self.recent_list = QListWidget(self)
        self.recent_list.setObjectName("RecentList")
        self.recent_list.setMaximumWidth(500)
        self.recent_list.setMinimumHeight(200) # Give it some initial height
        self.recent_list.itemDoubleClicked.connect(self.open_recent)
        self.recent_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.recent_list.customContextMenuRequested.connect(self.show_recent_context_menu)
        main_layout.addWidget(self.recent_list, alignment=Qt.AlignCenter)

        self.refresh_recent()

    def refresh_recent(self):
        self.recent_list.clear()
        for path in Settings.get_recent():
            item = QListWidgetItem(f"🗂 {path}")
            item.setData(Qt.UserRole, path) # Store the full path in UserRole
            self.recent_list.addItem(item)

    def open_project(self):
        file, _ = QFileDialog.getOpenFileName(self, "Open Project", "", "Project (*.json)")
        if file:
            Settings.add_recent(file)
            self.host.open_editor(new=False, filepath=file)
            self.refresh_recent()

    def open_recent(self, item):
        filepath = item.data(Qt.UserRole) # Get the full path from UserRole
        self.host.open_editor(new=False, filepath=filepath)

    def clear_recent_projects(self):
        Settings.clear_recent()
        self.refresh_recent()

    def show_recent_context_menu(self, pos):
        item = self.recent_list.itemAt(pos)
        if not item: return

        menu = QMenu(self)
        action_open = menu.addAction("Mở")
        action_remove = menu.addAction("Gỡ khỏi Gần đây")
        action_open_folder = menu.addAction("Mở thư mục chứa")

        action = menu.exec_(self.recent_list.mapToGlobal(pos))

        if action == action_open:
            self.open_recent(item)
        elif action == action_remove:
            filepath = item.data(Qt.UserRole)
            Settings.remove_recent(filepath) # Need to implement remove_recent in Settings
            self.refresh_recent()
        elif action == action_open_folder:
            filepath = item.data(Qt.UserRole)
            folder_path = os.path.dirname(filepath)
            if os.path.exists(folder_path):
                os.startfile(folder_path) # Windows specific
            else:
                # Handle case where folder doesn't exist
                pass


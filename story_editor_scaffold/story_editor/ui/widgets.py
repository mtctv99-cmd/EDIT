from PyQt5.QtWidgets import QWidget, QLabel, QTextEdit, QHBoxLayout, QFileDialog, QMenu, QSizePolicy
from PyQt5.QtCore import Qt
from ..core.utils import load_pixmap_scaled

class RowWidget(QWidget):
    def __init__(self, host: 'EditorScreen', image_path=None, text=""):
        super().__init__()
        self.host = host
        self._image_path = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(12)

        # image
        self.image_label = QLabel("— Chưa có ảnh —")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("QLabel { border: 1px dashed #aaa; color: #777; padding: 8px; }")
        self.image_label.setMinimumWidth(520)
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        layout.addWidget(self.image_label, 0)
        self.image_label.setContextMenuPolicy(Qt.CustomContextMenu)
        self.image_label.customContextMenuRequested.connect(self.show_image_menu)

        # text
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("Viết thoại/tóm tắt/lời dẫn tại đây…")
        self.text_edit.setText(text)
        layout.addWidget(self.text_edit, 1)
        self.text_edit.setContextMenuPolicy(Qt.CustomContextMenu)
        self.text_edit.customContextMenuRequested.connect(self.show_text_menu)

        if image_path:
            self.set_image(image_path)

    def set_image(self, path):
        self._image_path = path
        pix = load_pixmap_scaled(path)
        if pix.isNull():
            self.image_label.setText("— Ảnh lỗi —")
        else:
            self.image_label.setPixmap(pix)

    def clear_image(self):
        self._image_path = None
        self.image_label.clear()
        self.image_label.setText("— Chưa có ảnh —")

    def replace_image_dialog(self):
        path, _ = QFileDialog.getOpenFileName(self, "Chọn ảnh", "", "Ảnh (*.png *.jpg *.jpeg *.bmp *.webp)")
        if path:
            self.set_image(path)

    def clear_text(self):
        self.text_edit.clear()

    def show_image_menu(self, pos):
        menu = QMenu(self)
        act_replace = menu.addAction("Thay ảnh")
        act_clear = menu.addAction("Xóa ảnh")
        menu.addSeparator()
        act_insert_above = menu.addAction("Chèn TRÊN")
        act_insert_below = menu.addAction("Chèn DƯỚI")
        act_delete = menu.addAction("Xóa CẶP")
        action = menu.exec_(self.image_label.mapToGlobal(pos))
        if not action: return
        if action == act_replace: self.replace_image_dialog()
        elif action == act_clear: self.clear_image()
        elif action == act_insert_above: self.host.insert_row(self, True)
        elif action == act_insert_below: self.host.insert_row(self, False)
        elif action == act_delete: self.host.delete_row(self)

    def show_text_menu(self, pos):
        menu = QMenu(self)
        act_clear = menu.addAction("Xóa văn bản")
        menu.addSeparator()
        act_insert_above = menu.addAction("Chèn TRÊN")
        act_insert_below = menu.addAction("Chèn DƯỚI")
        act_delete = menu.addAction("Xóa CẶP")
        action = menu.exec_(self.text_edit.mapToGlobal(pos))
        if not action: return
        if action == act_clear: self.clear_text()
        elif action == act_insert_above: self.host.insert_row(self, True)
        elif action == act_insert_below: self.host.insert_row(self, False)
        elif action == act_delete: self.host.delete_row(self)

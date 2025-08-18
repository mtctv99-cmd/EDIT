from PyQt5.QtWidgets import QWidget, QLabel, QTextEdit, QHBoxLayout, QVBoxLayout, QFileDialog, QMenu, QSizePolicy, QPushButton
from PyQt5.QtCore import Qt, QRect, QPoint
from PyQt5.QtGui import QPainter, QPen, QColor
from ..core.utils import load_pixmap_scaled
from .crop_dialog import ImageCropDialog
import cv2, numpy as np, os, tempfile
from uuid import uuid4
from ..core.commands import ReplaceImageCommand, ClearImageCommand, ClearTextCommand, InsertRowCommand, DeleteRowCommand

class RowWidget(QWidget):
    def __init__(self, host: 'EditorScreen', image_path=None, text=""):
        super().__init__()
        self.host = host
        self._image_path = None
        self._rubber_origin = None
        self._rubber_rect = None  # QRect khung crop hiện tại

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(12)

        # Image and Process Button Layout
        image_col_layout = QVBoxLayout()
        image_col_layout.setContentsMargins(0, 0, 0, 0)
        image_col_layout.setSpacing(6)

        # image
        self.image_label = QLabel("— Chưa có ảnh —")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("QLabel { border: 1px dashed #aaa; color: #777; padding: 8px; }")
        self.image_label.setMinimumWidth(520)
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        image_col_layout.addWidget(self.image_label) # Add to vertical layout
        self.image_label.setContextMenuPolicy(Qt.CustomContextMenu)
        self.image_label.customContextMenuRequested.connect(self.show_image_menu)
        self.image_label.setMouseTracking(True)
        self.image_label.installEventFilter(self)  # chặn event tại label

        # Process button
        self.btn_process = QPushButton("Xử lý ảnh này")
        self.btn_process.clicked.connect(self._on_process_button_clicked)
        image_col_layout.addWidget(self.btn_process) # Add to vertical layout

        layout.addLayout(image_col_layout, 0) # Add vertical layout to main horizontal layout

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

    def _on_process_button_clicked(self):
        self.host.run_single_row(self)

    

    def _get_image_from_dialog(self):
        path, _ = QFileDialog.getOpenFileName(self, "Chọn ảnh", "", "Ảnh (*.png *.jpg *.jpeg *.bmp *.webp)")
        return path

    def show_image_menu(self, pos):
        menu = QMenu(self)
        act_replace = menu.addAction("Thay ảnh")
        act_clear = menu.addAction("Xóa ảnh")
        act_crop = menu.addAction("Cắt ảnh…")
        menu.addSeparator()
        act_insert_above_img = menu.addAction("Chèn TRÊN (ảnh)")
        act_insert_below_img = menu.addAction("Chèn DƯỚI (ảnh)")
        act_insert_above_all = menu.addAction("Chèn TRÊN (cả 2 ảnh & txt)")
        act_insert_below_all = menu.addAction("Chèn DƯỚI (cả 2 ảnh & txt)")
        menu.addSeparator()
        act_delete = menu.addAction("Xóa CẶP")
        action = menu.exec_(self.image_label.mapToGlobal(pos))
        if not action: return
        if action == act_replace:
            path = self._get_image_from_dialog()
            if path:
                cmd = ReplaceImageCommand(self, self._image_path, path)
                self.host.host.push_command(cmd)
        elif action == act_clear:
            cmd = ClearImageCommand(self, self._image_path)
            self.host.host.push_command(cmd)
        elif action == act_crop:
            if self._image_path:
                dlg = ImageCropDialog(self._image_path, self)
                if dlg.exec_():
                    cmd = ReplaceImageCommand(self, self._image_path, dlg.result_path)
                    self.host.host.push_command(cmd)
        elif action == act_insert_above_img:
            path = self._get_image_from_dialog()
            if path:
                index = self.host.vbox.indexOf(self)
                cmd = InsertRowCommand(self.host, index, image_path=path)
                self.host.host.push_command(cmd)
        elif action == act_insert_below_img:
            path = self._get_image_from_dialog()
            if path:
                index = self.host.vbox.indexOf(self)
                cmd = InsertRowCommand(self.host, index + 1, image_path=path)
                self.host.host.push_command(cmd)
        elif action == act_insert_above_all:
            path = self._get_image_from_dialog()
            if path:
                index = self.host.vbox.indexOf(self)
                cmd = InsertRowCommand(self.host, index, image_path=path, text="")
                self.host.host.push_command(cmd)
        elif action == act_insert_below_all:
            path = self._get_image_from_dialog()
            if path:
                index = self.host.vbox.indexOf(self)
                cmd = InsertRowCommand(self.host, index + 1, image_path=path, text="")
                self.host.host.push_command(cmd)
        elif action == act_delete:
            index = self.host.vbox.indexOf(self)
            cmd = DeleteRowCommand(self.host, index, self._image_path, self.text_edit.toPlainText())
            self.host.host.push_command(cmd)

    def show_text_menu(self, pos):
        menu = QMenu(self)
        act_clear = menu.addAction("Xóa văn bản")
        menu.addSeparator()
        act_insert_above_txt = menu.addAction("Chèn TRÊN (văn bản)")
        act_insert_below_txt = menu.addAction("Chèn DƯỚI (văn bản)")
        act_insert_above_all = menu.addAction("Chèn TRÊN (cả 2 ảnh & txt)")
        act_insert_below_all = menu.addAction("Chèn DƯỚI (cả 2 ảnh & txt)")
        menu.addSeparator()
        act_delete = menu.addAction("Xóa CẶP")
        action = menu.exec_(self.text_edit.mapToGlobal(pos))
        if not action: return
        if action == act_clear:
            cmd = ClearTextCommand(self, self.text_edit.toPlainText())
            self.host.host.push_command(cmd)
        elif action == act_insert_above_txt:
            index = self.host.vbox.indexOf(self)
            cmd = InsertRowCommand(self.host, index, text="")
            self.host.host.push_command(cmd)
        elif action == act_insert_below_txt:
            index = self.host.vbox.indexOf(self)
            cmd = InsertRowCommand(self.host, index + 1, text="")
            self.host.host.push_command(cmd)
        elif action == act_insert_above_all:
            path = self._get_image_from_dialog()
            if path:
                index = self.host.vbox.indexOf(self)
                cmd = InsertRowCommand(self.host, index, image_path=path, text="")
                self.host.host.push_command(cmd)
        elif action == act_insert_below_all:
            path = self._get_image_from_dialog()
            if path:
                index = self.host.vbox.indexOf(self)
                cmd = InsertRowCommand(self.host, index + 1, image_path=path, text="")
                self.host.host.push_command(cmd)
        elif action == act_delete:
            index = self.host.vbox.indexOf(self)
            cmd = DeleteRowCommand(self.host, index, self._image_path, self.text_edit.toPlainText())
            self.host.host.push_command(cmd)

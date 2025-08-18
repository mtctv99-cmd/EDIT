from PyQt5.QtWidgets import QDialog, QVBoxLayout, QDialogButtonBox, QWidget
from PyQt5.QtGui import QPainter, QPen, QBrush, QPolygonF, QPixmap
from PyQt5.QtCore import Qt, QRectF, QPointF
import numpy as np
import cv2, os, tempfile
from uuid import uuid4

HANDLE_SIZE = 12

class CropWidget(QWidget):
    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        self.image_path = image_path
        self.preview = QPixmap(image_path)  # preview pixmap
        # kích thước hiển thị (fit width ~ 700px giữ tỉ lệ)
        max_w = 700
        if self.preview.width() > max_w:
            self.preview = self.preview.scaledToWidth(max_w, Qt.SmoothTransformation)

        self.img_rect = QRectF(0, 0, self.preview.width(), self.preview.height())

        # Khung crop ban đầu = toàn bộ ảnh
        x0, y0 = 20, 20
        x1, y1 = self.img_rect.width() - 20, self.img_rect.height() - 20
        self.handles = [
            QPointF(x0, y0), QPointF(x1, y0),
            QPointF(x1, y1), QPointF(x0, y1)
        ]
        self.drag_index = None
        self.drag_mode = None # "handle" or "new_rect"
        self.start_pos = None
        self.setMinimumSize(self.preview.size())

    # ---- vẽ ----
    def paintEvent(self, ev):
        p = QPainter(self)
        p.drawPixmap(0, 0, self.preview)

        # overlay mờ ngoài vùng crop
        path = QPolygonF([self.handles[0], self.handles[1], self.handles[2], self.handles[3]])
        p.setBrush(QBrush(Qt.black, Qt.SolidPattern))
        p.setPen(Qt.NoPen)
        p.setOpacity(0.45)
        # ngoài polygon
        p.drawRect(self.rect())
        p.setOpacity(1.0)

        # viền polygon
        p.setBrush(Qt.NoBrush)
        p.setPen(QPen(Qt.green, 2))
        p.drawPolygon(path)

        # handles
        p.setBrush(QBrush(Qt.yellow))
        for pt in self.handles:
            r = QRectF(pt.x() - HANDLE_SIZE/2, pt.y() - HANDLE_SIZE/2, HANDLE_SIZE, HANDLE_SIZE)
            p.drawRect(r)

    # ---- chuột ----
    def mousePressEvent(self, ev):
        pos = QPointF(ev.position()) if hasattr(ev, "position") else QPointF(ev.x(), ev.y())
        # Check if a handle is hit
        for i, pt in enumerate(self.handles):
            r = QRectF(pt.x()-HANDLE_SIZE/2, pt.y()-HANDLE_SIZE/2, HANDLE_SIZE, HANDLE_SIZE)
            if r.contains(pos):
                self.drag_index = i
                self.drag_mode = "handle"
                return

        # If no handle is hit, start drawing a new rectangle
        self.drag_mode = "new_rect"
        self.start_pos = pos
        self.handles = [pos, pos, pos, pos] # Reset handles for new rectangle
        self.drag_index = 2 # Drag the opposite corner
        self.update()

    def mouseMoveEvent(self, ev):
        if self.drag_index is None:
            return
        pos = QPointF(ev.position()) if hasattr(ev, "position") else QPointF(ev.x(), ev.y())
        # clamp vào ảnh
        pos.setX(max(0, min(self.img_rect.width(), pos.x())))
        pos.setY(max(0, min(self.img_rect.height(), pos.y())))

        if self.drag_mode == "handle":
            i = self.drag_index
            self.handles[i] = pos
            # cập nhật 4 điểm còn lại để thành hình chữ nhật kín
            # i=0 -> đối diện 2; i=1 -> đối diện 3; ...
            opp = (i + 2) % 4
            # 2 điểm còn lại chia sẻ x/y
            if i in (0, 2):
                self.handles[(i+1)%4].setY(pos.y())
                self.handles[(i+3)%4].setX(pos.x())
            else:
                self.handles[(i+1)%4].setX(pos.x())
                self.handles[(i+3)%4].setY(pos.y())
        elif self.drag_mode == "new_rect":
            self.handles[0] = self.start_pos
            self.handles[1] = QPointF(pos.x(), self.start_pos.y())
            self.handles[2] = pos
            self.handles[3] = QPointF(self.start_pos.x(), pos.y())
        self.update()

    def mouseReleaseEvent(self, ev):
        self.drag_index = None
        self.update()

    # ---- lấy ảnh crop ở kích thước gốc ----
    def get_cropped_image(self):
        img = cv2.imread(self.image_path)
        if img is None:
            return None

        # scale preview -> ảnh gốc
        ph, pw = self.preview.height(), self.preview.width()
        ih, iw = img.shape[:2]
        sx, sy = iw / pw, ih / ph

        pts = np.array([[pt.x()*sx, pt.y()*sy] for pt in self.handles], dtype=np.float32)
        x_min, y_min = np.floor(pts[:,0].min()).astype(int), np.floor(pts[:,1].min()).astype(int)
        x_max, y_max = np.ceil(pts[:,0].max()).astype(int), np.ceil(pts[:,1].max()).astype(int)

        x_min = max(0, min(iw-1, x_min))
        x_max = max(0, min(iw-1, x_max))
        y_min = max(0, min(ih-1, y_min))
        y_max = max(0, min(ih-1, y_max))

        if x_max <= x_min or y_max <= y_min:
            return None

        # mask polygon (đề phòng sau này méo)
        mask = np.zeros((ih, iw), dtype=np.uint8)
        cv2.fillPoly(mask, [pts.astype(np.int32)], 255)
        cropped = cv2.bitwise_and(img, img, mask=mask)[y_min:y_max, x_min:x_max]
        return cropped


class ImageCropDialog(QDialog):
    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Cắt ảnh")
        self.result_path = None
        self.crop_widget = CropWidget(image_path, self)
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self._accept)
        btns.rejected.connect(self.reject)

        lay = QVBoxLayout(self)
        lay.addWidget(self.crop_widget)
        lay.addWidget(btns)

    def _accept(self):
        img = self.crop_widget.get_cropped_image()
        if img is None:
            self.reject()
            return
        tmp = os.path.join(tempfile.gettempdir(), f"crop_{uuid4().hex}.png")
        cv2.imwrite(tmp, img)
        self.result_path = tmp
        self.accept()
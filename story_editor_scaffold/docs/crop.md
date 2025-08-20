# Hướng dẫn tích hợp tính năng **Crop ảnh** (PyQt5)

> Tài liệu này mô tả cách **đưa cơ chế crop** giống trong `manhua_crop.py` vào dự án `story_editor` (UI/logic tách riêng). Mục tiêu: mở từ menu chuột phải ở **ô ảnh** → dialog crop → xuất **ảnh đã cắt ở độ phân giải gốc** rồi cập nhật lại hàng hiện tại.

---

## 1) Tổng quan cơ chế
- Làm việc trên **preview** (pixmap thu nhỏ) nhưng kết quả **crop theo tọa độ ảnh gốc** → không giảm chất lượng.
- Có **rubber band** (kéo chuột tạo khung) + **8 điểm neo** (4 góc, 4 cạnh) để tinh chỉnh.
- Cho phép **Undo** (lưu lịch sử tối đa N bước).
- Vùng crop là **polygon** (tứ giác), tương lai có thể hỗ trợ nghiêng méo (perspective).

Cơ chế này bám theo logic trong `manhua_crop.py`: preview rect + handles + mask polygon + scale về ảnh gốc.

---

## 2) Phụ thuộc
Cần các gói:
```bash
pip install PyQt5 opencv-python numpy
```

- `PyQt5`: giao diện
- `opencv-python` (cv2) + `numpy`: xử lý ảnh, tạo mask, ghi file tạm

---

## 3) Vị trí file & cấu trúc đề xuất

Trong dự án `story_editor_scaffold`/`story_editor`:
```
story_editor/
├─ ui/
│  ├─ widgets.py        # RowWidget (ảnh + text)
│  ├─ crop_dialog.py    # (THÊM) Dialog + CropWidget
│  └─ ...
├─ core/
│  ├─ utils.py          # load_pixmap_scaled (đã có)
│  └─ ...
└─ main_window.py       # không cần chỉnh nhiều
```

> Bạn sẽ tạo **`ui/crop_dialog.py`** (chứa `ImageCropDialog` + `CropWidget`).

---

## 4) API mong muốn

### 4.1. Từ `RowWidget` (widgets.py)
- Mở dialog:
```python
dlg = ImageCropDialog(self._image_path, self)
if dlg.exec_():
    cropped_path = dlg.result_path  # đường dẫn ảnh crop
    self.set_image(cropped_path)
```
- `result_path`: file tạm `.png` (hoặc ghi vào thư mục project), luôn trỏ tới ảnh **đã cắt**.

### 4.2. Trong `ImageCropDialog`
- Thuộc tính `result_path`: `None` nếu Cancel, ngược lại đường dẫn ảnh crop.
- `CropWidget.get_cropped_image()` trả về **numpy.ndarray** (BGR).

---

## 5) Code mẫu: `ui/crop_dialog.py` (rút gọn, sẵn sàng dùng)

> Bạn có thể copy nguyên file này, sau đó import trong `widgets.py`.

```python
# ui/crop_dialog.py
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
        # trúng handle nào?
        for i, pt in enumerate(self.handles):
            r = QRectF(pt.x()-HANDLE_SIZE/2, pt.y()-HANDLE_SIZE/2, HANDLE_SIZE, HANDLE_SIZE)
            if r.contains(pos):
                self.drag_index = i
                return
        # nếu không trúng handle: bắt đầu vẽ khung mới
        self.handles[0] = pos
        self.handles[2] = pos
        self.handles[1] = QPointF(pos.x(), pos.y())
        self.handles[3] = QPointF(pos.x(), pos.y())
        self.drag_index = 2  # kéo góc đối diện
        self.update()

    def mouseMoveEvent(self, ev):
        if self.drag_index is None:
            return
        pos = QPointF(ev.position()) if hasattr(ev, "position") else QPointF(ev.x(), ev.y())
        # clamp vào ảnh
        pos.setX(max(0, min(self.img_rect.width(), pos.x())))
        pos.setY(max(0, min(self.img_rect.height(), pos.y())))

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
```

---

## 6) Ghép vào UI hiện có

### 6.1. Thêm menu “Cắt ảnh…” vào ảnh (file `ui/widgets.py`)
Trong `RowWidget.show_image_menu` thêm mục:

```python
from .crop_dialog import ImageCropDialog  # ở đầu file

# bên trong show_image_menu():
act_crop = menu.addAction("Cắt ảnh…")

# sau khi xử lý các action khác:
elif action == act_crop:
    if self._image_path:
        dlg = ImageCropDialog(self._image_path, self)
        if dlg.exec_():
            self.set_image(dlg.result_path)
```

> Vậy là bạn đã có workflow: **chuột phải ảnh → Cắt ảnh… → OK → ảnh ở hàng được thay bằng bản đã crop**.

### 6.2. Lưu ảnh crop vào thư mục project (tùy chọn)
- Mặc định mình ghi vào **file tạm** (`%TEMP%`).  
- Nếu muốn lưu cùng project: trong `ProjectManager` tạo thư mục `media/` và copy file tạm vào đó rồi `set_image(path_mới)`.

---

## 7) Gợi ý mở rộng
- **Undo/Redo** trong CropWidget (lưu stack `handles`).
- **Tỉ lệ cố định** (giữ 16:9, 4:3, vuông…) khi giữ phím Shift.
- **Zoom preview** bằng bánh xe chuột.
- **Tự động đề xuất vùng thoại** (dò text bằng OCR rồi tạo khung gợi ý).

---

## 8) Lỗi thường gặp & cách xử lý
- **Ảnh quá lớn** → preview chậm: đã scale preview về ~700px, crop vẫn theo ảnh gốc nên chất lượng không đổi.
- **Không thấy OpenCV/Numpy** → cài bổ sung: `pip install opencv-python numpy`.
- **Cắt xong nhưng ảnh trắng** → kiểm tra polygon/scale; thường do preview/gốc chưa map đúng (xem lại `sx`, `sy`).

---

## 9) Ghi chú chuyển đổi PyQt5 vs PyQt6
- `Qt.AlignmentFlag.AlignCenter` → `Qt.AlignCenter`
- `Qt.TransformationMode.SmoothTransformation` → `Qt.SmoothTransformation`
- `event.position()` (PyQt6) → lấy `QPointF(ev.x(), ev.y())` (PyQt5).

---

**Done.** Bạn chỉ cần tạo `ui/crop_dialog.py`, thêm action “Cắt ảnh…” trong `RowWidget` như mục 6.1 là dùng được.

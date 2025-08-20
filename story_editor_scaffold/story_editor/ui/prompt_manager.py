from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QPushButton, QTextEdit, QLineEdit
from . import __init__  # keep package
from ..core.prompt_store import PromptStore

class PromptManagerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Prompt Manager")
        self.resize(600, 400)

        self.list = QListWidget()
        self.title = QLineEdit()
        self.title.setPlaceholderText("Tên prompt")
        self.text = QTextEdit()
        self.text.setPlaceholderText("Nội dung prompt...")

        btn_add = QPushButton("Thêm")
        btn_save = QPushButton("Lưu")
        btn_delete = QPushButton("Xóa")
        btn_close = QPushButton("Đóng")

        btn_add.clicked.connect(self.add_prompt)
        btn_save.clicked.connect(self.save_prompt)
        btn_delete.clicked.connect(self.delete_prompt)
        btn_close.clicked.connect(self.accept)

        left = QVBoxLayout()
        left.addWidget(self.list)

        right = QVBoxLayout()
        right.addWidget(self.title)
        right.addWidget(self.text)

        buttons = QHBoxLayout()
        buttons.addWidget(btn_add)
        buttons.addWidget(btn_save)
        buttons.addWidget(btn_delete)
        buttons.addStretch(1)
        buttons.addWidget(btn_close)
        right.addLayout(buttons)

        root = QHBoxLayout(self)
        root.addLayout(left, 1)
        root.addLayout(right, 2)

        self.list.currentRowChanged.connect(self.on_select)
        self.load()

    def load(self):
        self.list.clear()
        self.prompts = PromptStore.list_prompts()
        for p in self.prompts:
            self.list.addItem(p.get("name", "Untitled"))
        if self.prompts:
            self.list.setCurrentRow(0)

    def on_select(self, row):
        if row < 0 or row >= len(self.prompts): 
            self.title.clear(); self.text.clear(); return
        p = self.prompts[row]
        self.title.setText(p.get("name",""))
        self.text.setText(p.get("text",""))

    def add_prompt(self):
        self.prompts.append({"name": "Prompt mới", "text": ""})
        PromptStore.save_prompts(self.prompts)
        self.load()
        self.list.setCurrentRow(len(self.prompts)-1)

    def save_prompt(self):
        row = self.list.currentRow()
        if row < 0: return
        self.prompts[row]["name"] = self.title.text().strip() or "Untitled"
        self.prompts[row]["text"] = self.text.toPlainText()
        PromptStore.save_prompts(self.prompts)
        self.load()
        self.list.setCurrentRow(row)

    def delete_prompt(self):
        row = self.list.currentRow()
        if row < 0: return
        self.prompts.pop(row)
        PromptStore.save_prompts(self.prompts)
        self.load()

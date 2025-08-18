from PyQt5.QtWidgets import QDialog, QFormLayout, QLineEdit, QDialogButtonBox, QTextEdit
from ..core.settings import Settings

class ApiManagerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("API Manager")
        self.resize(480, 200)

        self.cfg = Settings.load_api_config()

        self.ed_gemini_key = QTextEdit("\n".join(self.cfg.get("gemini_api_keys", [])))
        self.ed_gemini_key.setPlaceholderText("Mỗi dòng một API key")
        self.ed_gemini_key.setFixedHeight(80)

        self.ed_openai_key = QTextEdit("\n".join(self.cfg.get("openai_api_keys", [])))
        self.ed_openai_key.setPlaceholderText("Mỗi dòng một API key")
        self.ed_openai_key.setFixedHeight(80)

        form = QFormLayout(self)
        form.addRow("Gemini API Key:", self.ed_gemini_key)
        form.addRow("OpenAI API Key:", self.ed_openai_key)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        form.addRow(buttons)
        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)

    def save(self):
        self.cfg["gemini_api_keys"] = [k.strip() for k in self.ed_gemini_key.toPlainText().splitlines() if k.strip()]
        self.cfg["openai_api_keys"] = [k.strip() for k in self.ed_openai_key.toPlainText().splitlines() if k.strip()]
        Settings.save_api_config(self.cfg)
        self.accept()

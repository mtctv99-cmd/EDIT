from PyQt5.QtWidgets import QDialog, QFormLayout, QLineEdit, QDialogButtonBox
from ..core.settings import Settings

class ApiManagerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("API Manager")
        self.resize(480, 200)

        self.cfg = Settings.load_api_config()

        self.ed_gemini_key = QLineEdit(self.cfg.get("gemini_api_key",""))
        self.ed_openai_key = QLineEdit(self.cfg.get("openai_api_key",""))
        self.ed_openai_key.setEchoMode(QLineEdit.Password)
        self.ed_gemini_key.setEchoMode(QLineEdit.Password)

        form = QFormLayout(self)
        form.addRow("Gemini API Key:", self.ed_gemini_key)
        form.addRow("OpenAI API Key:", self.ed_openai_key)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        form.addRow(buttons)
        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)

    def save(self):
        self.cfg["gemini_api_key"] = self.ed_gemini_key.text().strip()
        self.cfg["openai_api_key"] = self.ed_openai_key.text().strip()
        Settings.save_api_config(self.cfg)
        self.accept()

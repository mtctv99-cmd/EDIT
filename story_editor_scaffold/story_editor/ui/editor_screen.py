from PyQt5.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QMessageBox
from .widgets import RowWidget
from ..core.prompt_store import PromptStore
from ..core.settings import Settings
from ..core.ai_client import AIClient
import os

class EditorScreen(QWidget):
    def __init__(self, host: 'MainWindow'):
        super().__init__()
        self.host = host
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.container = QWidget()
        self.vbox = QVBoxLayout(self.container)
        self.vbox.setContentsMargins(8, 8, 8, 50)
        self.vbox.setSpacing(6)
        self.scroll.setWidget(self.container)

        layout = QVBoxLayout(self)
        layout.addWidget(self.scroll)

    def load_from_manager(self):
        while self.vbox.count():
            w = self.vbox.takeAt(0).widget()
            if w: w.deleteLater()
        for img, txt in self.host.project_manager.data:
            self.vbox.addWidget(RowWidget(self, image_path=img, text=txt))
        if not self.host.project_manager.data:
            self.vbox.addWidget(RowWidget(self))

    def add_row(self, image_path=None, text=""):
        self.add_row_at_index(self.vbox.count(), image_path, text)

    def add_row_at_index(self, index, image_path=None, text=""):
        new_row = RowWidget(self, image_path, text)
        self.vbox.insertWidget(index, new_row)
        # Update project manager data
        self.host.project_manager.data.insert(index, (image_path, text))
        return new_row

    def insert_row(self, ref_row, above: bool, image_path=None, text=""):
        index = self.vbox.indexOf(ref_row)
        if index == -1: return
        target = index if above else index + 1
        self.add_row_at_index(target, image_path, text)

    def delete_row(self, row):
        index = self.vbox.indexOf(row)
        if index == -1: return
        row.setParent(None)
        row.deleteLater()
        # Update project manager data
        self.host.project_manager.data.pop(index)

    def delete_row_at_index(self, index):
        if index < 0 or index >= self.vbox.count(): return
        row = self.vbox.itemAt(index).widget()
        if row:
            row.setParent(None)
            row.deleteLater()
            # Update project manager data
            self.host.project_manager.data.pop(index)

    def run_single_row(self, target_row: RowWidget):
        # Get prompt and API config from MainWindow
        main_window = self.host
        provider = main_window.combo_tool.currentText()
        keep_ctx = main_window.chk_context.isChecked()

        if provider != "Gemini":
            QMessageBox.information(main_window, "Run", "Hiện chỉ demo Gemini (CLI)")
            return

        prompt_name = main_window.combo_prompt.currentText()
        base_prompt = ""
        for p in PromptStore.list_prompts():
            if p.get("name") == prompt_name:
                base_prompt = p.get("text", "")
                break

        if not base_prompt or prompt_name == "(chưa có prompt)":
            QMessageBox.warning(main_window, "Prompt", "Chưa chọn prompt hợp lệ.")
            return

        cfg = Settings.load_api_config()
        cmd_template = cfg.get("gemini_cmd_template", "python gemini_cli_wrapper.py --model {model} --prompt {prompt} --image {image}")
        model = cfg.get("gemini_model", "gemini-1.5-pro")
        env = {}
        api_keys = cfg.get("gemini_api_keys", [])

        # Prepare context from preceding rows
        current_row_index = self.vbox.indexOf(target_row)
        context_texts = []
        for i in range(max(0, current_row_index - 6), current_row_index): # Last 6 rows before target
            row_widget = self.vbox.itemAt(i).widget()
            if row_widget and row_widget.text_edit:
                context_texts.append(row_widget.text_edit.toPlainText())
        
        context_str = "\n\n[Ngữ cảnh trước đó]:\n" + "\n".join(context_texts) if context_texts else ""

        # Build final prompt
        prompt = base_prompt
        if keep_ctx:
            prompt += context_str
        prompt += f"\n\n[Ảnh hiện tại]: {os.path.basename(target_row._image_path)}"

        # Call AIClient
        ok, out, err, code = AIClient.run_cmd_template(
            cmd_template=cmd_template,
            model=model, prompt=prompt, image=target_row._image_path,
            env_vars=env,
            prompt_file_mode=False,
            api_keys=api_keys
        )

        # Update target row's text
        if ok:
            target_row.text_edit.setPlainText(out)
            # Update context history in ProjectManager (optional, but good for consistency)
            main_window.project_manager.context_history.append({
                "prompt": prompt,
                "response": out,
                "images": [target_row._image_path],
            })
            main_window.project_manager.context_history = main_window.project_manager.context_history[-20:]
        else:
            target_row.text_edit.append(f"\n\n[ERROR CLI {code}]\n{err}")

    

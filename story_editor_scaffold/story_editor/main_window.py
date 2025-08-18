import sys
import os
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QStackedWidget,
    QToolBar,
    QAction,
    QFileDialog,
    QMessageBox,
    QComboBox,
    QCheckBox,
    QWidget,
    QLabel,
    QInputDialog,
)
from PyQt5.QtCore import QSize
from .ui.start_screen import StartScreen
from .ui.editor_screen import EditorScreen
from .ui.prompt_manager import PromptManagerDialog
from .ui.api_manager import ApiManagerDialog
from .core.project_manager import ProjectManager
from .core.prompt_store import PromptStore
from .core.settings import Settings
from .core.ai_client import AIClient
from .core.utils import parse_srt_to_text_blocks, split_txt_to_paragraphs
from .core.image_fetcher import fetch_images


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Story Editor")
        self.resize(1280, 840)

        self.project_manager = ProjectManager()

        self.undo_stack = []
        self.redo_stack = []

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.start_screen = StartScreen(self)
        self.editor_screen = EditorScreen(self)

        self.stack.addWidget(self.start_screen)
        self.stack.addWidget(self.editor_screen)
        self.stack.setCurrentWidget(self.start_screen)

        self._build_menu()
        self._build_toolbar()

        # Apply stylesheet
        self.setStyleSheet("""
#HeroTitle {
    font-size: 44px;
    font-weight: 800;
    color: #0f172a;
}
#HeroSubtitle {
    color: #5b6476;
    font-size: 14px;
}
#ActionCard {
    background: #ffffff;
    border: 1px solid #e6e8ef;
    border-radius: 14px;
}
#PrimaryButton {
    background: #2563eb;
    color: white;
    border-radius: 10px;
    padding: 10px 18px;
}
#RecentList {
    background: #ffffff;
    border: 1px solid #e6e8ef;
    border-radius: 12px;
}
QListWidget::item:selected {
    background: #eef2ff;
    color: #111827;
}
""")

    # ---------- Menus ----------
    def _build_menu(self):
        # File
        m_file = self.menuBar().addMenu("&File")
        act_new = QAction("New", self); act_new.triggered.connect(lambda: self.open_editor(new=True))
        act_open = QAction("Open...", self); act_open.triggered.connect(self._action_open_file)
        act_save = QAction("Save", self); act_save.triggered.connect(self._action_save)
        act_save_as = QAction("Save As...", self); act_save_as.triggered.connect(self._action_save_as)
        act_close = QAction("Close Project", self); act_close.triggered.connect(self._action_close_project)
        act_import_images = QAction("Import Ảnh...", self); act_import_images.triggered.connect(self._action_import_images)
        act_fetch_images = QAction("Lấy ảnh...", self); act_fetch_images.triggered.connect(self._action_fetch_images)
        act_import_text = QAction("Import Văn bản...", self); act_import_text.triggered.connect(self._action_import_text)
        act_export = QAction("Export...", self); act_export.triggered.connect(lambda: QMessageBox.information(self, "Export", "Stub Export"))
        act_exit = QAction("Exit", self); act_exit.triggered.connect(self.close)
        for a in [
            act_new,
            act_open,
            act_save,
            act_save_as,
            act_close,
            act_import_images,
            act_fetch_images,
            act_import_text,
            act_export,
            act_exit,
        ]:
            m_file.addAction(a)

        # Edit
        m_edit = self.menuBar().addMenu("&Edit")
        act_undo = QAction("Undo", self); act_undo.setShortcut("Ctrl+Z"); act_undo.triggered.connect(self._action_undo)
        act_redo = QAction("Redo", self); act_redo.setShortcut("Ctrl+Y"); act_redo.triggered.connect(self._action_redo)
        m_edit.addAction(act_undo)
        m_edit.addAction(act_redo)
        m_edit.addSeparator()
        m_edit.addAction(QAction("Insert Row Above (stub)", self))
        m_edit.addAction(QAction("Insert Row Below (stub)", self))
        m_edit.addAction(QAction("Delete Row (stub)", self))

        # Tools
        m_tools = self.menuBar().addMenu("&Tools")
        act_api = QAction("API Manager...", self); act_api.triggered.connect(self._open_api_manager)
        act_prompt = QAction("Prompt Manager...", self); act_prompt.triggered.connect(self._open_prompt_manager)
        m_tools.addAction(act_api); m_tools.addAction(act_prompt)

        # About
        m_about = self.menuBar().addMenu("&About")
        act_about = QAction("About Story Editor", self); act_about.triggered.connect(lambda: QMessageBox.information(self, "About", "Story Editor - UI scaffold ready."))
        m_about.addAction(act_about)

    # ---------- Toolbar ----------
    def _build_toolbar(self):
        tb = QToolBar("Main")
        tb.setIconSize(QSize(18, 18))
        self.addToolBar(tb)

        act_import_images_tb = QAction("Import Ảnh", self); act_import_images_tb.triggered.connect(self._action_import_images)
        tb.addAction(act_import_images_tb)
        act_fetch_images_tb = QAction("Lấy ảnh", self); act_fetch_images_tb.triggered.connect(self._action_fetch_images)
        tb.addAction(act_fetch_images_tb)

        tb.addSeparator()

        # Tool provider dropdown (Gemini, OCR, ...)
        self.combo_tool = QComboBox()
        self.combo_tool.addItems(["Chọn công cụ...", "Gemini", "OCR"])
        self.combo_tool.currentTextChanged.connect(self._on_tool_changed)
        tb.addWidget(self.combo_tool)

        # Prompt dropdown (hidden unless Gemini)
        self.lbl_prompt = QLabel("  Prompt: ")  # Store label as instance variable
        tb.addWidget(self.lbl_prompt)
        self.combo_prompt = QComboBox()
        self.combo_prompt.setMinimumWidth(220)
        self._reload_prompt_combo()
        tb.addWidget(self.combo_prompt)
        # Ensure prompt controls are hidden until Gemini is selected
        self._on_tool_changed(self.combo_tool.currentText())

        # Keep context checkbox
        self.chk_context = QCheckBox("Giữ ngữ cảnh")
        self.chk_context.setChecked(False)
        tb.addWidget(self.chk_context)

        # Run button (stub)
        act_run = QAction("Run", self)
        act_run.triggered.connect(self._action_run)
        tb.addAction(act_run)

        tb.addSeparator()

        act_save = QAction("Save", self); act_save.triggered.connect(self._action_save)
        tb.addAction(act_save)

        act_close_tb = QAction("Close", self)
        act_close_tb.triggered.connect(self._action_close_project)
        tb.addAction(act_close_tb)

        act_undo_tb = QAction("Undo", self); act_undo_tb.triggered.connect(self._action_undo)
        tb.addAction(act_undo_tb)

        act_redo_tb = QAction("Redo", self); act_redo_tb.triggered.connect(self._action_redo)
        tb.addAction(act_redo_tb)

    def _reload_prompt_combo(self):
        self.combo_prompt.clear()
        prompts = PromptStore.list_prompts()
        if prompts:
            self.combo_prompt.addItems([p.get("name","Untitled") for p in prompts])
        else:
            self.combo_prompt.addItem("(chưa có prompt)")

    def sync_ui_to_pm(self):
        data = []
        L = self.editor_screen.vbox
        for i in range(L.count()):
            w = L.itemAt(i).widget()
            if not hasattr(w, "_image_path"): continue
            text = w.text_edit.toPlainText()
            data.append((w._image_path, text))
        self.project_manager.data = data

    # ---------- File actions ----------
    def _action_open_file(self):
        last_dir = Settings.get_last_dir("open_project")
        file, _ = QFileDialog.getOpenFileName(self, "Open Project", last_dir, "Project (*.json)")
        if file:
            Settings.set_last_dir("open_project", os.path.dirname(file))
            Settings.add_recent(file)
            self.open_editor(new=False, filepath=file)

    def _action_save(self):
        try:
            # Sync editor to project data (stub: gather from UI later)
            self.sync_ui_to_pm()
            if not self.project_manager.file_path:
                self._action_save_as()
                return
            self.project_manager.save_project()
            QMessageBox.information(self, "Save", "Đã lưu (stub).")
        except Exception as e:
            QMessageBox.warning(self, "Save error", str(e))

    def _action_save_as(self):
        last_dir = Settings.get_last_dir("save_project")
        file, _ = QFileDialog.getSaveFileName(self, "Save Project As", last_dir, "Project (*.json)")
        if file:
            Settings.set_last_dir("save_project", os.path.dirname(file))
            self.sync_ui_to_pm()
            self.project_manager.save_project(file)
            Settings.add_recent(file)
            QMessageBox.information(self, "Save As", "Đã lưu (stub).")

    def _action_import_images(self):
        last_dir = Settings.get_last_dir("import_images")
        files, _ = QFileDialog.getOpenFileNames(self, "Import Ảnh", last_dir, "Ảnh (*.png *.jpg *.jpeg *.bmp *.webp)")
        if files:
            Settings.set_last_dir("import_images", os.path.dirname(files[0]))
            for f in files:
                self.project_manager.add_row(image_path=f)
            self.editor_screen.load_from_manager()
            QMessageBox.information(self, "Import Ảnh", f"Đã nhập {len(files)} ảnh.")

    def _action_fetch_images(self):
        url, ok = QInputDialog.getText(self, "Lấy ảnh", "URL chương:")
        if not ok or not url:
            return
        last_dir = Settings.get_last_dir("import_images")
        out_dir = QFileDialog.getExistingDirectory(self, "Chọn thư mục lưu ảnh", last_dir)
        if not out_dir:
            return
        Settings.set_last_dir("import_images", out_dir)
        try:
            files = fetch_images(url, out_dir)
        except Exception as e:
            QMessageBox.warning(self, "Lấy ảnh", str(e))
            return
        if files:
            for f in files:
                self.project_manager.add_row(image_path=f)
            self.editor_screen.load_from_manager()
            QMessageBox.information(self, "Lấy ảnh", f"Đã lấy {len(files)} ảnh.")
        else:
            QMessageBox.warning(self, "Lấy ảnh", "Không lấy được ảnh nào.")

    def _action_import_text(self):
        last_dir = Settings.get_last_dir("import_text")
        file, _ = QFileDialog.getOpenFileName(self, "Import Văn bản", last_dir, "Văn bản (*.txt *.srt)")
        if file:
            Settings.set_last_dir("import_text", os.path.dirname(file))
            with open(file, "r", encoding="utf-8") as f:
                content = f.read()
            
            if file.endswith(".srt"):
                blocks = parse_srt_to_text_blocks(content)
            else:
                blocks = split_txt_to_paragraphs(content)

            for i, block in enumerate(blocks):
                if i < len(self.project_manager.data):
                    # Update existing row
                    img_path, _ = self.project_manager.data[i]
                    self.project_manager.data[i] = (img_path, block)
                else:
                    # Add new text-only row
                    self.project_manager.add_row(text=block)
            self.editor_screen.load_from_manager()
            QMessageBox.information(self, "Import Văn bản", f"Đã nhập {len(blocks)} khối văn bản.")

    # ---------- Tools actions ----------
    def _open_api_manager(self):
        dlg = ApiManagerDialog(self)
        if dlg.exec_():
            QMessageBox.information(self, "API", "Đã lưu API config.")

    def _open_prompt_manager(self):
        dlg = PromptManagerDialog(self)
        if dlg.exec_():
            self._reload_prompt_combo()

    def _on_tool_changed(self, text):
        is_gemini = (text == "Gemini")
        self.lbl_prompt.setVisible(is_gemini)
        self.combo_prompt.setVisible(is_gemini)

    

    def push_command(self, cmd):
        self.undo_stack.append(cmd)
        self.redo_stack.clear()

    def _action_undo(self):
        if not self.undo_stack: return
        cmd = self.undo_stack.pop()
        cmd.undo()
        self.redo_stack.append(cmd)
        self.editor_screen.load_from_manager() # Refresh UI

    def _action_redo(self):
        if not self.redo_stack: return
        cmd = self.redo_stack.pop()
        cmd.redo()
        self.undo_stack.append(cmd)
        self.editor_screen.load_from_manager() # Refresh UI

    def _action_run(self):
        provider = self.combo_tool.currentText()
        keep_ctx = self.chk_context.isChecked()

        if provider != "Gemini":
            QMessageBox.information(self, "Run", "Hiện chỉ demo Gemini (CLI)")
            return

        # 1) Lấy prompt
        prompt_name = self.combo_prompt.currentText()
        base_prompt = ""
        for p in PromptStore.list_prompts():
            if p.get("name") == prompt_name:
                base_prompt = p.get("text", "")
                break

        if not base_prompt or prompt_name == "(chưa có prompt)":
            QMessageBox.warning(self, "Prompt", "Chưa chọn prompt hợp lệ.")
            return

        # 2) Tham số CLI từ Settings (API Manager có thể đã lưu model, template)
        cfg = Settings.load_api_config()
        cmd_template = cfg.get("gemini_cmd_template", "python gemini_cli_wrapper.py --model {model} --prompt {prompt} --image {image}")
        model = cfg.get("gemini_model", "gemini-1.5-pro")
        # Nếu CLI cần key trong ENV:
        env = {}
        api_keys = cfg.get("gemini_api_keys", []) # Get list of keys

        # 3) Gom hàng cần xử lý
        rows = []
        L = self.editor_screen.vbox
        for i in range(L.count()):
            w = L.itemAt(i).widget()
            if getattr(w, "_image_path", None):
                rows.append(w)

        if not rows:
            QMessageBox.information(self, "Run", "Không có ảnh để xử lý.")
            return

        # 4) Chạy từng hàng
        for idx, row in enumerate(rows):
            prompt = base_prompt
            if keep_ctx:
                # ví dụ ghép ngữ cảnh đơn giản
                history = self.project_manager.context_history[-6:]
                for turn in history:
                    prompt += f"\n\n[Trước đó] Prompt: {turn['prompt']}\nKết quả: {turn['response']}\n"
            prompt += f"\n\n[Ảnh hiện tại]: {os.path.basename(row._image_path)}"

            ok, out, err, code = AIClient.run_cmd_template(
                cmd_template=cmd_template,
                model=model, prompt=prompt, image=row._image_path,
                env_vars=env, # Changed to env_vars
                prompt_file_mode=False,
                api_keys=api_keys # Pass the list of API keys
            )

            # 5) Ghi kết quả
            if ok:
                row.text_edit.setPlainText(out)
                # Lưu context đơn giản
                self.project_manager.context_history.append({
                    "prompt": prompt,
                    "response": out,
                    "images": [row._image_path],
                })
                # Cắt lịch sử
                self.project_manager.context_history = self.project_manager.context_history[-20:]
            else:
                row.text_edit.append(f"\n\n[ERROR CLI {code}]\n{err}")

    def _action_close_project(self):
        self.sync_ui_to_pm()
        if self.project_manager.file_path:
            self.project_manager.save_project()
        self.stack.setCurrentWidget(self.start_screen)
        self.start_screen.refresh_recent()

    # ---------- Navigation ----------
    def open_editor(self, new=True, filepath=None):
        if new:
            self.project_manager.new_project()
        else:
            if not self.project_manager.load_project(filepath):
                QMessageBox.warning(self, "Lỗi tải dự án", "Không thể tải dự án. Tệp có thể bị hỏng hoặc không hợp lệ.")
                return
        self.editor_screen.load_from_manager()
        self.stack.setCurrentWidget(self.editor_screen)


def main():
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())

from .core.commands import CropImageCommand, SetTextCommand, ReplaceImageCommand, ClearImageCommand, ClearTextCommand, InsertRowCommand, DeleteRowCommand

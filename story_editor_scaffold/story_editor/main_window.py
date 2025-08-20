import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QStackedWidget, QToolBar, QAction, QFileDialog, QMessageBox, QComboBox, QCheckBox, QWidget, QLabel
from PyQt5.QtCore import QSize
from .ui.start_screen import StartScreen
from .ui.editor_screen import EditorScreen
from .ui.prompt_manager import PromptManagerDialog
from .ui.api_manager import ApiManagerDialog
from .core.project_manager import ProjectManager
from .core.prompt_store import PromptStore
from .core.settings import Settings


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Story Editor")
        self.resize(1280, 840)

        self.project_manager = ProjectManager()

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.start_screen = StartScreen(self)
        self.editor_screen = EditorScreen(self)

        self.stack.addWidget(self.start_screen)
        self.stack.addWidget(self.editor_screen)
        self.stack.setCurrentWidget(self.start_screen)

        self._build_menu()
        self._build_toolbar()

    # ---------- Menus ----------
    def _build_menu(self):
        # File
        m_file = self.menuBar().addMenu("&File")
        act_new = QAction("New", self); act_new.triggered.connect(lambda: self.open_editor(new=True))
        act_open = QAction("Open...", self); act_open.triggered.connect(self._action_open_file)
        act_save = QAction("Save", self); act_save.triggered.connect(self._action_save)
        act_save_as = QAction("Save As...", self); act_save_as.triggered.connect(self._action_save_as)
        act_export = QAction("Export...", self); act_export.triggered.connect(lambda: QMessageBox.information(self, "Export", "Stub Export"))
        act_exit = QAction("Exit", self); act_exit.triggered.connect(self.close)
        for a in [act_new, act_open, act_save, act_save_as, act_export, act_exit]:
            m_file.addAction(a)

        # Edit
        m_edit = self.menuBar().addMenu("&Edit")
        m_edit.addAction(QAction("Undo (stub)", self))
        m_edit.addAction(QAction("Redo (stub)", self))
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

        act_save = QAction("Save", self); act_save.triggered.connect(self._action_save)
        tb.addAction(act_save)

        tb.addSeparator()

        # Tool provider dropdown (Gemini, OCR, ...)
        self.combo_tool = QComboBox()
        self.combo_tool.addItems(["Chọn công cụ...", "Gemini", "OCR"])
        self.combo_tool.currentTextChanged.connect(self._on_tool_changed)
        tb.addWidget(self.combo_tool)

        # Prompt dropdown (hidden unless Gemini)
        tb.addWidget(QLabel("  Prompt: "))
        self.combo_prompt = QComboBox()
        self.combo_prompt.setMinimumWidth(220)
        self._reload_prompt_combo()
        self.combo_prompt.setVisible(False)  # ẩn mặc định
        tb.addWidget(self.combo_prompt)

        # Keep context checkbox
        self.chk_context = QCheckBox("Giữ ngữ cảnh")
        self.chk_context.setChecked(False)
        tb.addWidget(self.chk_context)

        # Run button (stub)
        act_run = QAction("Run", self)
        act_run.triggered.connect(self._action_run_stub)
        tb.addAction(act_run)

    def _reload_prompt_combo(self):
        self.combo_prompt.clear()
        prompts = PromptStore.list_prompts()
        if prompts:
            self.combo_prompt.addItems([p.get("name","Untitled") for p in prompts])
        else:
            self.combo_prompt.addItem("(chưa có prompt)")

    # ---------- File actions ----------
    def _action_open_file(self):
        file, _ = QFileDialog.getOpenFileName(self, "Open Project", "", "Project (*.json)")
        if file:
            Settings.add_recent(file)
            self.open_editor(new=False, filepath=file)

    def _action_save(self):
        try:
            # Sync editor to project data (stub: gather from UI later)
            # For now keep existing data structure.
            if not self.project_manager.file_path:
                self._action_save_as()
                return
            self.project_manager.save_project()
            QMessageBox.information(self, "Save", "Đã lưu (stub).")
        except Exception as e:
            QMessageBox.warning(self, "Save error", str(e))

    def _action_save_as(self):
        file, _ = QFileDialog.getSaveFileName(self, "Save Project As", "", "Project (*.json)")
        if file:
            self.project_manager.save_project(file)
            Settings.add_recent(file)
            QMessageBox.information(self, "Save As", "Đã lưu (stub).")

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
        # Show prompt combo only when Gemini
        self.combo_prompt.setVisible(text == "Gemini")

    def _action_run_stub(self):
        provider = self.combo_tool.currentText()
        keep_ctx = self.chk_context.isChecked()
        prompt_name = None
        if provider == "Gemini":
            prompt_name = self.combo_prompt.currentText()
        QMessageBox.information(
            self, "Run (stub)",
            f"Provider: {provider}\nPrompt: {prompt_name}\nGiữ ngữ cảnh: {keep_ctx}\n\n(Chưa gọi API thật)"
        )

    # ---------- Navigation ----------
    def open_editor(self, new=True, filepath=None):
        if new:
            self.project_manager.new_project()
        else:
            self.project_manager.load_project(filepath)
        self.editor_screen.load_from_manager()
        self.stack.setCurrentWidget(self.editor_screen)


def main():
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())

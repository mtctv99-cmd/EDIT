import json

class ProjectManager:
    def __init__(self):
        # list of (image_path, text)
        self.data = []
        self.file_path = None
        self.context_history = []  # for 'keep context' mode

    def new_project(self):
        self.data = []
        self.file_path = None
        self.context_history = []

    def load_project(self, path):
        with open(path, "r", encoding="utf-8") as f:
            self.data = json.load(f)
        self.file_path = path
        self.context_history = []

    def save_project(self, path=None):
        if path:
            self.file_path = path
        if not self.file_path:
            raise ValueError("No file path provided")
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

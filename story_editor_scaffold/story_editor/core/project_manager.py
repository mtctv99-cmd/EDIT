import json

class ProjectManager:
    def __init__(self):
        # list of (image_path, text)
        self.data = []
        self.file_path = None
        self.context_history = []  # for 'keep context' mode

        self._history_stack = []
        self._history_index = -1
        self._save_state() # Save initial state

    def new_project(self):
        self.data = []
        self.file_path = None
        self.context_history = []
        self._save_state()

    def load_project(self, path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                self.data = json.load(f)
            self.file_path = path
            self.context_history = []
            self._save_state()
            return True
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading project: {e}")
            return False

    def save_project(self, path=None):
        if path:
            self.file_path = path
        if not self.file_path:
            raise ValueError("No file path provided")
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def add_row(self, image_path=None, text=""):
        self.data.append((image_path, text))
        self._save_state()

    def _save_state(self):
        # Clear any redo history if a new action is performed
        if self._history_index < len(self._history_stack) - 1:
            self._history_stack = self._history_stack[:self._history_index + 1]
        
        # Save a deep copy of the current data and context_history
        self._history_stack.append({
            "data": [list(row) for row in self.data], # Convert tuples to lists for deep copy
            "context_history": [dict(item) for item in self.context_history]
        })
        self._history_index = len(self._history_stack) - 1

    

from types import SimpleNamespace

class CropImageCommand:
    def __init__(self, row, old_path, new_path):
        self.row = row
        self.old = old_path
        self.new = new_path
    def undo(self):
        self.row.set_image(self.old)
    def redo(self):
        self.row.set_image(self.new)

class SetTextCommand:
    def __init__(self, row, old_text, new_text):
        self.row = row
        self.old = old_text
        self.new = new_text
    def undo(self):
        self.row.text_edit.setPlainText(self.old)
    def redo(self):
        self.row.text_edit.setPlainText(self.new)

class ReplaceImageCommand:
    def __init__(self, row, old_path, new_path):
        self.row = row
        self.old = old_path
        self.new = new_path
        self.index = self.row.host.vbox.indexOf(self.row)

    def undo(self):
        self.row.set_image(self.old)
        img, txt = self.row.host.host.project_manager.data[self.index]
        self.row.host.host.project_manager.data[self.index] = (self.old, txt)

    def redo(self):
        self.row.set_image(self.new)
        img, txt = self.row.host.host.project_manager.data[self.index]
        self.row.host.host.project_manager.data[self.index] = (self.new, txt)

class ClearImageCommand:
    def __init__(self, row, old_path):
        self.row = row
        self.old = old_path
        self.index = self.row.host.vbox.indexOf(self.row) # Get index of the row

    def undo(self):
        self.row.set_image(self.old)
        # Update project_manager.data
        img, txt = self.row.host.host.project_manager.data[self.index]
        self.row.host.host.project_manager.data[self.index] = (self.old, txt)

    def redo(self):
        self.row.clear_image()
        # Update project_manager.data
        img, txt = self.row.host.host.project_manager.data[self.index]
        self.row.host.host.project_manager.data[self.index] = (None, txt)

class ClearTextCommand:
    def __init__(self, row, old_text):
        self.row = row
        self.old = old_text
        self.index = self.row.host.vbox.indexOf(self.row)

    def undo(self):
        self.row.text_edit.setPlainText(self.old)
        img, txt = self.row.host.host.project_manager.data[self.index]
        self.row.host.host.project_manager.data[self.index] = (img, self.old)

    def redo(self):
        self.row.clear_text()
        img, txt = self.row.host.host.project_manager.data[self.index]
        self.row.host.host.project_manager.data[self.index] = (img, "")

class InsertRowCommand:
    def __init__(self, editor_screen, index, image_path=None, text=""):
        self.editor_screen = editor_screen
        self.index = index
        self.image_path = image_path
        self.text = text

    def undo(self):
        self.editor_screen.delete_row_at_index(self.index)
        self.editor_screen.load_from_manager() # Refresh UI

    def redo(self):
        self.editor_screen.add_row_at_index(self.index, self.image_path, self.text)
        self.editor_screen.load_from_manager() # Refresh UI

class DeleteRowCommand:
    def __init__(self, editor_screen, index, image_path, text):
        self.editor_screen = editor_screen
        self.index = index
        self.image_path = image_path
        self.text = text

    def undo(self):
        self.editor_screen.add_row_at_index(self.index, self.image_path, self.text)
        self.editor_screen.load_from_manager() # Refresh UI

    def redo(self):
        self.editor_screen.delete_row_at_index(self.index)
        self.editor_screen.load_from_manager() # Refresh UI

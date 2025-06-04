# t:\Work\xml_input_ui\command_manager.py

class CommandManager:
    def __init__(self, editor_ref):
        self.editor = editor_ref  # Reference to XmlReportEditor for callbacks
        self.undo_stack = []
        self.redo_stack = []

    def execute_command(self, command):
        command.execute()
        self.undo_stack.append(command)
        self.redo_stack.clear()
        
        if self.editor:
            # Callbacks to editor
            self.editor._log_history(f"Executed: {command}")
            self.editor._set_dirty_flag(True)
            self.editor._update_undo_redo_actions_state()
        return command # Return for editor to handle post-execution UI if needed

    def undo(self):
        if not self.can_undo():
            return None
        command = self.undo_stack.pop()
        command.unexecute()
        self.redo_stack.append(command)
        
        if self.editor:
            # Callbacks to editor
            self.editor._log_history(f"Undone: {command}")
            self.editor._set_dirty_flag(True) # Undoing makes it dirty
            self.editor._update_undo_redo_actions_state()
        return command # Return for editor to handle post-unexecution UI

    def redo(self):
        if not self.can_redo():
            return None
        command = self.redo_stack.pop()
        command.execute()
        self.undo_stack.append(command)
        
        if self.editor:
            # Callbacks to editor
            self.editor._log_history(f"Redone: {command}")
            self.editor._set_dirty_flag(True) # Redoing makes it dirty
            self.editor._update_undo_redo_actions_state()
        return command # Return for editor to handle post-re-execution UI

    def can_undo(self):
        return bool(self.undo_stack)

    def can_redo(self):
        return bool(self.redo_stack)

    def clear_stacks(self):
        self.undo_stack.clear()
        self.redo_stack.clear()
        if self.editor: # Ensure editor ref exists (e.g. during initial setup)
            self.editor._update_undo_redo_actions_state()
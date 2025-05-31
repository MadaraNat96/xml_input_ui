# t:\Work\xml_input_ui\custom_widgets.py
from PyQt6.QtWidgets import QLineEdit, QGroupBox
from PyQt6.QtCore import pyqtSignal, Qt

class HighlightableGroupBox(QGroupBox):
    def __init__(self, company_name="", title="", parent=None):
        super().__init__(title, parent)
        self.company_name = company_name
        self.setProperty("highlighted", False) # Initialize property

    def setHighlightedState(self, highlight):
        if self.property("highlighted") != highlight:
            self.setProperty("highlighted", highlight)
            self._refresh_style()

    def _refresh_style(self):
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()

class FocusAwareLineEdit(QLineEdit):
    # Signal to notify the main application about focus changes with company context
    focusGainedSignal = pyqtSignal(str, QLineEdit) # company_name, self
    focusLostSignal = pyqtSignal(str, QLineEdit)   # company_name, self

    def __init__(self, company_name, text="", parent=None):
        super().__init__(text, parent)
        self.company_name = company_name

    def focusInEvent(self, event):
        self.focusGainedSignal.emit(self.company_name, self)
        super().focusInEvent(event)

    def focusOutEvent(self, event):
        # Important: Check if the new focus widget is still within the same group box.
        # This simple version doesn't do that, so tabbing between LineEdits in the same
        # group box will cause a brief unhighlight/highlight flicker.
        # A more complex solution would involve checking event.reason() or new focus widget.
        self.focusLostSignal.emit(self.company_name, self)
        super().focusOutEvent(event)
# t:\Work\xml_input_ui\ui_components\quote_selection_widget.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton,
    QLineEdit, QApplication, QStyle, QCompleter
)
from PyQt6.QtCore import pyqtSignal, Qt, QStringListModel

class QuoteSelectionWidget(QWidget):
    selectQuoteClicked = pyqtSignal(str)
    addQuoteClicked = pyqtSignal(str)
    removeQuoteClicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self.update_quote_list([]) # Initialize with empty list

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)

        quote_selection_group = QGroupBox("Select or Add Quote")
        quote_selection_layout = QVBoxLayout(quote_selection_group)
        quote_selection_layout.setContentsMargins(5, 5, 5, 5)
        quote_selection_layout.setSpacing(3)

        search_actions_layout = QHBoxLayout()

        self.quote_search_edit = QLineEdit()
        self.quote_search_edit.setPlaceholderText("Enter Quote Name to Select/Add")
        self.completer = QCompleter()
        self.quote_search_edit.setCompleter(self.completer)
        self.quote_list_model = QStringListModel()
        self.completer.setModel(self.quote_list_model)
        search_actions_layout.addWidget(self.quote_search_edit, 1)

        self.select_quote_button = QPushButton(icon=QApplication.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogContentsView))
        self.select_quote_button.setToolTip("Select/View Quote (using name in text box)")
        self.select_quote_button.setFixedSize(20,20)
        self.select_quote_button.clicked.connect(self._on_select_clicked)
        search_actions_layout.addWidget(self.select_quote_button)

        self.remove_quote_button = QPushButton(icon=QApplication.style().standardIcon(QStyle.StandardPixmap.SP_DialogCancelButton))
        self.remove_quote_button.setToolTip("Remove Displayed Quote")
        self.remove_quote_button.setFixedSize(20, 20)
        self.remove_quote_button.clicked.connect(self.removeQuoteClicked)
        search_actions_layout.addWidget(self.remove_quote_button)

        self.add_quote_button = QPushButton(icon=QApplication.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogNewFolder))
        self.add_quote_button.setToolTip("Add New Quote (using name in text box above)")
        self.add_quote_button.setFixedSize(20,20)
        self.add_quote_button.clicked.connect(self._on_add_clicked)
        search_actions_layout.addWidget(self.add_quote_button)

        search_actions_layout.addStretch(0)
        quote_selection_layout.addLayout(search_actions_layout)
        layout.addWidget(quote_selection_group)

    def _on_select_clicked(self):
        self.selectQuoteClicked.emit(self.quote_search_edit.text().strip())

    def _on_add_clicked(self):
        self.addQuoteClicked.emit(self.quote_search_edit.text().strip())

    def get_quote_name_input(self):
        return self.quote_search_edit.text().strip()

    def set_quote_name_input(self, name):
        self.quote_search_edit.setText(name)

    def update_quote_list(self, quote_names):
        """Updates the suggestions for quote names based on filtering."""
        self.quote_list_model.setStringList(quote_names)
        self.completer.popup().setMinimumWidth(self.quote_search_edit.width()) # Adjust popup width
        self.completer.setCompletionMode(QCompleter.CompletionMode.UnfilteredPopupCompletion) # Show all options

    def clear_input(self):
        self.quote_search_edit.clear()

    def setEnabled(self, enabled):
        self.quote_search_edit.setEnabled(enabled)
        self.select_quote_button.setEnabled(enabled)
        self.add_quote_button.setEnabled(enabled)
        self.remove_quote_button.setEnabled(enabled)
        super().setEnabled(enabled)
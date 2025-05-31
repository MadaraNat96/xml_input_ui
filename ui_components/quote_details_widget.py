# t:\Work\xml_input_ui\ui_components\quote_details_widget.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QFormLayout, QLineEdit, QLabel
)
from PyQt6.QtCore import pyqtSignal

class QuoteDetailsWidget(QWidget):
    quoteNameChanged = pyqtSignal(str, str)
    quotePriceChanged = pyqtSignal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_name = ""
        self._current_price = ""
        self._init_ui()

    def _init_ui(self):
        self.details_group = QGroupBox("Quote Details")
        self.details_group.setEnabled(False)
        details_form_layout = QFormLayout(self.details_group)
        self.name_edit = QLineEdit()
        self.price_edit = QLineEdit()
        details_form_layout.addRow(QLabel("Quote Name:"), self.name_edit)
        details_form_layout.addRow(QLabel("Quote Price:"), self.price_edit)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0,0,0,0)
        main_layout.addWidget(self.details_group)

        self.name_edit.editingFinished.connect(self._handle_name_editing_finished)
        self.name_edit.returnPressed.connect(self._handle_name_editing_finished)
        self.price_edit.editingFinished.connect(self._handle_price_editing_finished)
        self.price_edit.returnPressed.connect(self._handle_price_editing_finished)

    def _handle_name_editing_finished(self):
        new_name = self.name_edit.text().strip()
        if not self.name_edit.isReadOnly() and new_name != self._current_name:
            self.quoteNameChanged.emit(self._current_name, new_name)

    def _handle_price_editing_finished(self):
        new_price = self.price_edit.text().strip()
        if not self.price_edit.isReadOnly() and new_price != self._current_price:
            self.quotePriceChanged.emit(self._current_price, new_price)

    def load_data(self, name, price, is_new_quote):
        self.name_edit.setText(name)
        self.price_edit.setText(price)
        self._current_name = name
        self._current_price = price
        self.name_edit.setReadOnly(not is_new_quote)
        self.price_edit.setReadOnly(False)
        self.details_group.setEnabled(True)

    def get_data(self):
        return self.name_edit.text(), self.price_edit.text()

    def clear_data(self):
        self.name_edit.blockSignals(True)
        self.price_edit.blockSignals(True)
        self.name_edit.clear()
        self.price_edit.clear()
        self.name_edit.blockSignals(False)
        self.price_edit.blockSignals(False)
        self._current_name = ""
        self._current_price = ""
        self.details_group.setEnabled(False)

    def update_field_value(self, field_name, value, from_command=False):
        if field_name == "name":
            self.name_edit.blockSignals(True)
            self.name_edit.setText(value)
            self.name_edit.blockSignals(False)
            self._current_name = value
        elif field_name == "price":
            self.price_edit.blockSignals(True)
            self.price_edit.setText(value)
            self.price_edit.blockSignals(False)
            self._current_price = value

    def setEnabled(self, enabled):
        self.details_group.setEnabled(enabled)
        super().setEnabled(enabled)
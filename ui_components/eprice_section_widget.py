# t:\Work\xml_input_ui\ui_components\eprice_section_widget.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton,
    QFormLayout, QLineEdit, QDialog # QDialog for EPriceCompanySelectionDialog
)
from PyQt6.QtCore import Qt, pyqtSignal
from dialogs import EPriceCompanySelectionDialog
from custom_widgets import FocusAwareLineEdit, HighlightableGroupBox
from .ui_utils import _clear_qt_layout # Import from the new ui_utils

class EPriceSectionWidget(QWidget):
    companyFocusGained = pyqtSignal(str, QLineEdit)
    companyFocusLost = pyqtSignal(str, QLineEdit)
    ePriceValueChanged = pyqtSignal(str, str, str)

    def __init__(self, fixed_companies_provider_func, parent=None):
        super().__init__(parent)
        self.fixed_companies_provider_func = fixed_companies_provider_func
        self.eprice_entries = []
        self.selected_eprice_companies_to_display = []
        self._init_ui()

    def _init_ui(self):
        self.eprice_group = QGroupBox("E-Price Companies")
        eprice_main_layout = QVBoxLayout(self.eprice_group)
        eprice_main_layout.setContentsMargins(2, 5, 5, 5)
        eprice_main_layout.setSpacing(3)

        actions_layout = QHBoxLayout()
        actions_layout.addStretch()
        self.choose_companies_button = QPushButton("Choose Companies")
        self.choose_companies_button.setToolTip("Select which E-Price companies to display")
        self.choose_companies_button.setFixedSize(120, 20)
        self.choose_companies_button.clicked.connect(self._handle_choose_eprice_companies)
        actions_layout.addWidget(self.choose_companies_button)
        eprice_main_layout.addLayout(actions_layout)

        self.eprice_items_layout = QHBoxLayout()
        self.eprice_items_layout.setSpacing(4)
        eprice_main_layout.addLayout(self.eprice_items_layout)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0,0,0,0)
        main_layout.addWidget(self.eprice_group)
        self.refresh_structure()

    def _create_company_ui(self, company_name_str, value_str=""):
        company_gbox = HighlightableGroupBox(company_name=company_name_str, title=company_name_str)
        company_gbox.setFixedWidth(62)
        gbox_layout = QVBoxLayout(company_gbox)
        gbox_layout.setContentsMargins(5, 5, 5, 5)
        gbox_layout.setSpacing(2)
        form = QFormLayout()
        form.setContentsMargins(0,0,0,0)
        value_edit = FocusAwareLineEdit(company_name_str, value_str)
        value_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        entry_data = {"name": company_name_str, "value_edit": value_edit, "widget": company_gbox, "current_value": value_str}
        value_edit.focusGainedSignal.connect(self.companyFocusGained)
        value_edit.focusLostSignal.connect(self.companyFocusLost)
        value_edit.editingFinished.connect(lambda le=value_edit, ed=entry_data: self._handle_eprice_value_changed(le, ed))
        value_edit.returnPressed.connect(lambda le=value_edit, ed=entry_data: self._handle_eprice_value_changed(le, ed))
        form.addRow(value_edit)
        gbox_layout.addLayout(form)
        self.eprice_items_layout.addWidget(company_gbox)
        self.eprice_entries.append(entry_data)

    def refresh_structure(self, new_fixed_companies=None):
        fixed_companies = new_fixed_companies if new_fixed_companies is not None else self.fixed_companies_provider_func()
        current_vals = {e["name"]: e["value_edit"].text() for e in self.eprice_entries}
        _clear_qt_layout(self.eprice_items_layout)
        self.eprice_entries.clear()
        self.selected_eprice_companies_to_display = list(fixed_companies)
        for name in fixed_companies:
            self._create_company_ui(name, current_vals.get(name, ""))
        self._update_visible_companies()

    def _handle_eprice_value_changed(self, line_edit, entry_data):
        new_val = line_edit.text().strip()
        old_val = entry_data.get("current_value", "")
        if new_val != old_val:
            self.ePriceValueChanged.emit(entry_data["name"], old_val, new_val)

    def load_data(self, eprice_data_list):
        loaded_map = {item["name"]: item["value"] for item in eprice_data_list}
        for entry in self.eprice_entries:
            entry["value_edit"].setText(loaded_map.get(entry["name"], ""))
            entry["current_value"] = loaded_map.get(entry["name"], "")

    def get_data(self):
        return [{"name": e["name"], "value": e["value_edit"].text().strip()} for e in self.eprice_entries if e["value_edit"].text().strip()]

    def clear_data(self):
        for entry in self.eprice_entries:
            entry["value_edit"].clear()
            entry["current_value"] = ""

    def update_company_value(self, company_name, value, from_command=False):
        for entry in self.eprice_entries:
            if entry["name"] == company_name:
                entry["value_edit"].blockSignals(True)
                entry["value_edit"].setText(value)
                entry["value_edit"].blockSignals(False)
                entry["current_value"] = value
                break

    def _handle_choose_eprice_companies(self):
        fixed_companies = self.fixed_companies_provider_func()
        dialog = EPriceCompanySelectionDialog(fixed_companies, self.selected_eprice_companies_to_display, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.selected_eprice_companies_to_display = dialog.get_selected_companies()
            self._update_visible_companies()

    def _update_visible_companies(self):
        fixed_companies = self.fixed_companies_provider_func()
        self.choose_companies_button.setEnabled(len(fixed_companies) > 0)
        for entry in self.eprice_entries:
            widget = entry.get("widget")
            if widget: widget.setVisible(entry["name"] in self.selected_eprice_companies_to_display)

    def update_company_highlight_state(self, company_name, highlight_state):
        for entry in self.eprice_entries:
            if entry.get("name") == company_name:
                gbox = entry.get("widget")
                if isinstance(gbox, HighlightableGroupBox): gbox.setHighlightedState(highlight_state)

    def setEnabled(self, enabled):
        self.eprice_group.setEnabled(enabled)
        super().setEnabled(enabled)
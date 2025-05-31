# t:\Work\xml_input_ui\ui_components\pe_section_widget.py
from PyQt6.QtWidgets import (
    QVBoxLayout, QFormLayout, QLineEdit # Minimal specific imports
)
from PyQt6.QtCore import Qt, pyqtSignal
from .eprice_section_widget import EPriceSectionWidget # Import base class
from custom_widgets import FocusAwareLineEdit, HighlightableGroupBox

class PESectionWidget(EPriceSectionWidget):
    peValueChanged = pyqtSignal(str, str, str)
    
    def __init__(self, fixed_companies_provider_func, parent=None):
        super().__init__(fixed_companies_provider_func, parent)
        self.eprice_group.setTitle("PE Companies")
        self.choose_companies_button.setToolTip("Select which PE companies to display")

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
        
        entry_data = {
            "name": company_name_str, 
            "value_edit": value_edit, 
            "widget": company_gbox,
            "current_value": value_str 
        }

        value_edit.focusGainedSignal.connect(self.companyFocusGained)
        value_edit.focusLostSignal.connect(self.companyFocusLost)
        value_edit.editingFinished.connect(lambda le=value_edit, ed=entry_data: self._handle_pe_value_changed(le, ed))
        value_edit.returnPressed.connect(lambda le=value_edit, ed=entry_data: self._handle_pe_value_changed(le, ed))
        form.addRow(value_edit)
        gbox_layout.addLayout(form)
        self.eprice_items_layout.addWidget(company_gbox)
        self.eprice_entries.append(entry_data)

    def _handle_pe_value_changed(self, line_edit, entry_data):
        new_val = line_edit.text().strip()
        old_val = entry_data.get("current_value", "")
        if new_val != old_val:
            self.peValueChanged.emit(entry_data["name"], old_val, new_val)
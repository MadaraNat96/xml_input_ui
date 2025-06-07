# t:\Work\xml_input_ui\ui_components\sectors_section_widget.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton,
    QFormLayout, QComboBox, QDialog, QLineEdit, QLabel # Added QLabel
)
from PyQt6.QtCore import Qt, pyqtSignal
from dialogs import EPriceCompanySelectionDialog # Reuse dialog, adapt as needed
from custom_widgets import HighlightableGroupBox
from .ui_utils import _clear_qt_layout

class SectorsSectionWidget(QWidget):
    sectorValueChanged = pyqtSignal(str, str, str) # sector name, field (type/name), new value

    def __init__(self, sectors_provider_func, parent=None):
        super().__init__(parent)
        self.sectors_provider_func = sectors_provider_func
        self.sectors_entries = []
        self.selected_sectors_to_display = []  # Initially display all sectors
        self._init_ui()

    def _init_ui(self):
        self.sectors_group = QGroupBox("Sectors")
        sectors_main_layout = QVBoxLayout(self.sectors_group)
        sectors_main_layout.setContentsMargins(2, 5, 5, 5)
        sectors_main_layout.setSpacing(3)

        actions_layout = QHBoxLayout()
        actions_layout.addStretch()
        self.choose_sectors_button = QPushButton("Choose Sectors")
        self.choose_sectors_button.setToolTip("Select which sectors to display")
        self.choose_sectors_button.setFixedSize(120, 20)
        self.choose_sectors_button.clicked.connect(self._handle_choose_sectors)
        actions_layout.addWidget(self.choose_sectors_button)
        sectors_main_layout.addLayout(actions_layout)

        self.sectors_items_layout = QVBoxLayout()  # Changed to QVBoxLayout
        self.sectors_items_layout.setSpacing(4)
        sectors_main_layout.addLayout(self.sectors_items_layout)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.sectors_group)
        self.setLayout(main_layout)
        self.refresh_structure()

    def _create_sector_ui(self, sector_name_str, sector_type_str="main"):
        sector_gbox = HighlightableGroupBox(title="", company_name=sector_name_str) # Removed title
        sector_gbox.setMinimumHeight(25) # Adjust as needed.

        gbox_layout = QFormLayout(sector_gbox)
        gbox_layout.setContentsMargins(5, 2, 5, 2) # Reduced margins for tighter packing
        gbox_layout.setSpacing(3)
        
        type_combo = QComboBox()
        type_combo.addItems(["main", "sub"])
        type_combo.setCurrentText(sector_type_str)
        type_combo.setFixedWidth(55) # Adjust as needed

        name_label = QLabel(sector_name_str)

        entry_data = {
            "name": sector_name_str,
            "type_combo": type_combo,
            "widget": sector_gbox,
            "current_type": sector_type_str,  # Initial values
        }
        
        # Directly connect signals here for clarity
        type_combo.currentTextChanged.connect(lambda new_type, ed=entry_data: self._handle_sector_value_changed(ed, "type", new_type))

        # Adjust layout for tighter packing (combobox + label)
        h_layout = QHBoxLayout()
        h_layout.setSpacing(3)
        h_layout.setContentsMargins(0,0,0,0)
        h_layout.addWidget(type_combo, 0, Qt.AlignmentFlag.AlignLeft)
        h_layout.addWidget(name_label, 1, Qt.AlignmentFlag.AlignLeft)

        gbox_layout.addRow(h_layout)
        self.sectors_items_layout.addWidget(sector_gbox)  # Add directly to vertical layout
        self.sectors_entries.append(entry_data)

    def refresh_structure(self, new_sectors=None):
        all_sectors = new_sectors if new_sectors is not None else self.sectors_provider_func()
        current_types = {e["name"]: e["type_combo"].currentText() for e in self.sectors_entries}

        _clear_qt_layout(self.sectors_items_layout)
        self.sectors_entries.clear()

        # Initially display all sectors by default
        self.selected_sectors_to_display = list(all_sectors)
        for sector_name in all_sectors:
            self._create_sector_ui(sector_name, current_types.get(sector_name, "main"))
        self._update_visible_sectors()

    def _handle_sector_value_changed(self, entry_data, field_name, new_val):
        old_val = entry_data.get(f"current_{field_name}", "")
        if new_val != old_val:
            self.sectorValueChanged.emit(entry_data["name"], field_name, new_val)

    def load_data(self, sectors_data_list):
        loaded_map = {item["name"]: item["type"] for item in sectors_data_list}
        for entry in self.sectors_entries:
            if entry["name"] in loaded_map:
                entry["type_combo"].setCurrentText(loaded_map[entry["name"]])
                entry["current_type"] = loaded_map[entry["name"]]

    def get_data(self):
        return [{"name": e["name"], "type": e["type_combo"].currentText()}
                for e in self.sectors_entries if e["widget"].isVisible()]

    def clear_data(self):
        for entry in self.sectors_entries:
            entry["type_combo"].setCurrentText("main") # Default selection
            entry["current_type"] = "main" # Resetting the current type

    def update_sector_value(self, sector_name, field, value, from_command=False):
        # In this version, only 'type' is a supported editable field.
        if field != "type": return

        for entry in self.sectors_entries:
            if entry["name"] == sector_name:
                if field == "type":
                    entry["type_combo"].blockSignals(True)
                    entry["type_combo"].setCurrentText(value)
                    entry["type_combo"].blockSignals(False)
                    entry["current_type"] = value
                break

    def _handle_choose_sectors(self):
        all_sectors = self.sectors_provider_func()
        dialog = EPriceCompanySelectionDialog(all_sectors, self.selected_sectors_to_display, self) # Reuse, for now.
        dialog.setWindowTitle("Choose Sectors to Display")
        dialog.findChild(QLabel, "label").setText("Select sectors to display from the list below:") # Customize label

        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.selected_sectors_to_display = dialog.get_selected_companies()
            self._update_visible_sectors()

    def _update_visible_sectors(self):
        # Update sector visibility based on current selection
        all_sectors = self.sectors_provider_func() # Get all sectors (for enabling button)
        self.choose_sectors_button.setEnabled(len(all_sectors) > 0)
        for entry in self.sectors_entries:
            widget = entry.get("widget")
            if widget: widget.setVisible(entry["name"] in self.selected_sectors_to_display)

    def setEnabled(self, enabled):
        self.sectors_group.setEnabled(enabled)
        super().setEnabled(enabled)
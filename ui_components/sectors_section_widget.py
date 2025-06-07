# t:\Work\xml_input_ui\ui_components\sectors_section_widget.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton,
    QStyle, QApplication,
    QFormLayout, QComboBox, QDialog, QLineEdit, QLabel, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from custom_widgets import HighlightableGroupBox
from .ui_utils import _clear_qt_layout
from typing import List, Dict
class SectorsSectionWidget(QWidget):
    sectorValueChanged = pyqtSignal(str, str, str) # sector name, field (type/name), new value

    def __init__(self, sectors_provider_func, parent=None):
        super().__init__(parent)
        self.sectors_provider_func = sectors_provider_func
        self.sectors_entries = []
        self.MAX_SECTORS_DISPLAYED = 5
        # self.selected_sectors_to_display = []  # Initially display all sectors - Not needed with the new design
        self._init_ui()

    def _init_ui(self):
        self.sectors_group = QGroupBox("Sectors")
        sectors_main_layout = QVBoxLayout(self.sectors_group)
        sectors_main_layout.setContentsMargins(2, 5, 5, 5)
        sectors_main_layout.setSpacing(3)

        actions_layout = QHBoxLayout()
        add_sector_button = QPushButton("Add Sector")
        add_sector_button.setToolTip("Add a sector to the quote")
        add_sector_button.setFixedSize(100, 20)
        add_sector_button.clicked.connect(self._add_new_sector)
        actions_layout.addWidget(add_sector_button)
        actions_layout.addStretch(1)
        sectors_main_layout.addLayout(actions_layout)

        self.sectors_items_layout = QVBoxLayout()  # Changed to QVBoxLayout
        self.sectors_items_layout.setSpacing(4)
        sectors_main_layout.addLayout(self.sectors_items_layout)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.sectors_group)
        self.setLayout(main_layout)
        self.refresh_structure()
    
    def _create_sector_ui(self, sector_name_str="", sector_type_str="main"): # Allow empty sector name initially
        sector_gbox = HighlightableGroupBox(title="", company_name=sector_name_str)
        sector_gbox.setMinimumHeight(25)
        gbox_layout = QFormLayout(sector_gbox)
        gbox_layout.setContentsMargins(5, 2, 5, 2) # Reduced margins for tighter packing
        gbox_layout.setSpacing(3)
        
        type_combo = QComboBox()
        type_combo.addItems(["main", "sub"])
        type_combo.setCurrentText(sector_type_str)
        type_combo.setFixedWidth(55)

        name_combo = QComboBox() # Replace label with combo

        # Entry data - Initialize with the provided name, even if empty
        entry_data = {
            "name": sector_name_str,
            "type_combo": type_combo,
            "widget": sector_gbox,
            "current_type": sector_type_str,
        }
        self.sectors_entries.append(entry_data)
        # Populate the name combo box *after* entry_data is created to use _handle_sector_value_changed.
        # (Otherwise, lambda will capture the combo rather than its current value.)
        all_sectors = self.sectors_provider_func()
        if all_sectors:
            name_combo.addItems(all_sectors)
            if sector_name_str in all_sectors:
                name_combo.setCurrentText(sector_name_str)
            else:
                name_combo.setCurrentIndex(-1)  # No selection if not in the list

        name_combo.currentTextChanged.connect(lambda new_name, ed=entry_data: self._handle_sector_value_changed(ed, "name", new_name))
        type_combo.currentTextChanged.connect(lambda new_type, ed=entry_data: self._handle_sector_value_changed(ed, "type", new_type))

        h_layout = self._create_sector_entry_layout(type_combo, name_combo)

        gbox_layout.addRow(h_layout)
        self.sectors_items_layout.addWidget(sector_gbox)  # Add directly to vertical layout

        # If this is a new sector (empty name), it needs to be visible.

    def refresh_structure(self, new_sectors=None):
        all_sectors = new_sectors if new_sectors is not None else self.sectors_provider_func()
        current_data = {e["name"]: e["type_combo"].currentText() for e in self.sectors_entries if "type_combo" in e}

        _clear_qt_layout(self.sectors_items_layout)
        self.sectors_entries.clear()
        
        if not all_sectors:
            return  # Exit if there are no sectors to display, preventing errors

        for sector_name in all_sectors:  # Use sectors from provider, not initial selection
            # In refresh_structure, we want a fully populated UI for each sector name,
            # so the user can modify it if needed. The name_combo should allow selection of any sector, 
            # but default to the existing type (if available from current_data).
            self._create_sector_ui(sector_name, sector_type_str=current_data.get(sector_name, "main"))

    def _create_sector_entry_layout(self, type_combo, name_combo): # Keep as is to improve readability
        h_layout = QHBoxLayout()
        h_layout.setSpacing(3)
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.addWidget(type_combo, 0, Qt.AlignmentFlag.AlignLeft)
        h_layout.addWidget(name_combo, 1, Qt.AlignmentFlag.AlignLeft)
        # Remove button
        remove_sector_button = QPushButton(icon=QApplication.style().standardIcon(QStyle.StandardPixmap.SP_DialogCancelButton))
        remove_sector_button.setToolTip("Remove this sector")
        remove_sector_button.setFixedSize(16, 16)  # Reduced size for icon button
        remove_sector_button.clicked.connect(lambda: self._handle_remove_sector(name_combo.currentText()))
        h_layout.addWidget(remove_sector_button)
        return h_layout


    def load_sectors_from_db(self, quote_name):
        """Loads sector data from the database for the given quote.

        Args:
            quote_name: The name of the quote for which to load sectors.
        """
        # Assume you have a method in your data_utils or a separate module
        # to fetch sector data from the database. This is a placeholder.
        # Replace this with your actual database interaction.
        sectors_data: List[Dict] = self.fetch_sectors_from_db(quote_name)  # See fetch_sectors_from_db.

        if sectors_data:
            # Clear existing sectors in the UI before loading from the database.
            self.clear_sectors()
            for sector_data in sectors_data:
                sector_name = sector_data.get("name")
                sector_type = sector_data.get("type", "main") 
                if sector_name:
                    self._create_sector_ui(sector_name, sector_type)
        else: # If no sectors are found, refresh the structure with an empty list (to show no sectors).
            self.refresh_structure(new_sectors=[])

    def clear_sectors(self):
        """Clears all existing sector entries from the UI."""
        _clear_qt_layout(self.sectors_items_layout)
        self.sectors_entries.clear()



    def load_data(self, sectors_data_list):
        # sectors_data_list = sectors_data_list or []  # Ensure it's not None
        loaded_map = {item["name"]: item["type"] for item in sectors_data_list}

        # Update existing entries based on loaded data.
        for entry in self.sectors_entries:
            if entry["name"] in loaded_map:
                # Block signals during update to prevent triggering value change events.
                entry["type_combo"].blockSignals(True)
                entry["type_combo"].setCurrentText(loaded_map[entry["name"]])
                entry["type_combo"].blockSignals(False)
                entry["current_type"] = loaded_map[entry["name"]]
            else:
                # If a sector from the provider isn't in loaded data, it implies
                # it should be the default "main" type.
                entry["type_combo"].blockSignals(True)
                entry["type_combo"].setCurrentText("")  # Set to empty string instead of "main"
                entry["type_combo"].blockSignals(False)
                entry["current_type"] = "main"


    def get_data(self):
        # Collect only the sectors and their types from the UI.
        return [{"name": e["name"], "type": e["type_combo"].currentText()}
                for e in self.sectors_entries]

    def clear_data(self):
        for entry in self.sectors_entries:
            if "type_combo" in entry:  # Add a check to ensure the key exists
                entry["type_combo"].blockSignals(True)
                entry["type_combo"].setCurrentText("")  # Clear the selection
                entry["type_combo"].blockSignals(False)
                entry["current_type"] = ""  # Resetting the current type

    def _add_new_sector(self):
        all_sectors = self.sectors_provider_func()
        if not all_sectors:
            QMessageBox.warning(self, "No Sectors Available", "No sectors are defined in the configuration.")
            return

        # Call _create_sector_ui without any arguments. The defaults defined in that method will be used.
        self._create_sector_ui()

    def _handle_remove_sector(self, sector_name):
        if not sector_name:  # Handle empty sector name case gracefully
            return
        reply = QMessageBox.question(self, "Remove Sector", f"Are you sure you want to remove sector '{sector_name}'?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self._remove_sector_ui(sector_name)

    def _remove_sector_ui(self, sector_name):
        """Removes the sector entry from the UI."""
        for entry in list(self.sectors_entries):  # Iterate over a copy
            if entry["name"] == sector_name:
                widget = entry.get("widget")
                if widget:
                    self.sectors_items_layout.removeWidget(widget)
                    widget.deleteLater()
                self.sectors_entries.remove(entry)
                break  # Assuming sector names are unique, so we can stop after removing

    def update_sector_name_in_ui(self, old_name, new_name):
        for entry in self.sectors_entries:
            if entry["name"] == old_name:
                entry["name"] = new_name  # Update stored name

    # Placeholder for fetching sector data from the database.
    # Replace with your actual database interaction logic.
    def fetch_sectors_from_db(self, quote_name) -> List[Dict]:
        """Fetches sectors for the given quote from the database.

        Args:
            quote_name: The name of the quote.

        Returns:
            A list of dictionaries, where each dictionary represents a sector
            and has "name" and "type" keys.
            Returns an empty list if no sectors are found.
        """
        # Example using a hypothetical function in data_utils:
        # return data_utils.get_sectors_for_quote_from_db(quote_name)

        # Placeholder return:
        return [] # Replace with actual database query

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
        dialog = SectorSelectionDialog(all_sectors, self.selected_sectors_to_display, self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.selected_sectors_to_display = dialog.get_selected_sectors()
            self._update_visible_sectors()

    def _update_visible_sectors(self):
        # Update sector visibility based on current selection
        all_sectors = self.sectors_provider_func() # Get all sectors (for enabling button)
        self.choose_sectors_button.setEnabled(len(all_sectors) > 0)
        for entry in self.sectors_entries:
            widget = entry.get("widget")
            if widget: widget.setVisible(entry["name"] in self.selected_sectors_to_display)
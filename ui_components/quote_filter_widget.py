from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton, 
    QComboBox, QLabel
)
from PyQt6.QtCore import pyqtSignal, Qt


class QuoteFilterWidget(QWidget):
    filterChanged = pyqtSignal(str)

    def __init__(self, sectors_list_provider, parent=None):
            super().__init__(parent)
            self.sectors_list_provider = sectors_list_provider
            self.selected_sector = None  # Keep as None for "All Sectors"
            self._init_ui()
            self._populate_sector_combo()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        filter_group = QGroupBox("Filter Quotes")
        filter_layout = QHBoxLayout(filter_group)
        filter_layout.setContentsMargins(5, 5, 5, 5)
        filter_layout.setSpacing(3)

        sector_label = QLabel("Filter by Sector:")
        filter_layout.addWidget(sector_label)

        self.sector_combo = QComboBox(self)
        self.sector_combo.addItem("All Sectors", None)  # Use None as data for "All Sectors"
        self.sector_combo.currentIndexChanged.connect(self._on_sector_changed)
        filter_layout.addWidget(self.sector_combo)

        layout.addWidget(filter_group)

    def _populate_sector_combo(self):
            sectors_list = self.sectors_list_provider()  # Call the provider to get the list
            if sectors_list:
                for sector_name in sorted(sectors_list):
                    self.sector_combo.addItem(sector_name, sector_name)  # Use sector name as both text and data

    def refresh_sectors(self):
            self.sector_combo.clear()
            self.sector_combo.addItem("All Sectors", None)
            self._populate_sector_combo()

    def _on_sector_changed(self, index):
            # Use itemData to retrieve the associated sector name
            selected_sector = self.sector_combo.itemData(index)
            # Update self.selected_sector only if it has actually changed
            if self.selected_sector != selected_sector:
                self.selected_sector = selected_sector
                self.filterChanged.emit(selected_sector)

    def clear_filter(self):
            self.sector_combo.setCurrentIndex(0)  # Reset to "All Sectors", triggers signal

    def get_selected_sector(self):
        return self.selected_sector

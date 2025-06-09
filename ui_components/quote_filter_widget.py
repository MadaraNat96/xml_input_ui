from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QComboBox, QLabel, QListWidget
)
from PyQt6.QtCore import pyqtSignal, Qt, QObject
from PyQt6.QtGui import QKeyEvent


class QuoteFilterWidget(QWidget):
    filterChanged = pyqtSignal(list)  # Signal now emits the filtered quote list
    quoteSelected = pyqtSignal(str)  # New signal for quote selection

    def __init__(self, sectors_list_provider, all_quotes_data_provider, parent=None):  # Add callback
        super().__init__(parent)
        self.sectors_list_provider = sectors_list_provider
        self.all_quotes_data_provider = all_quotes_data_provider
        self.selected_sector = None  # Keep as None for "All Sectors"
        self._init_ui()
        self._populate_sector_combo()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        filter_group = QGroupBox("Filter Quotes")
        filter_layout = QVBoxLayout(filter_group)  # Changed to QVBoxLayout
        filter_layout.setContentsMargins(5, 5, 5, 5)  
        filter_layout.setSpacing(3)  

        sector_label = QLabel("Filter by Sector:")
        filter_layout.addWidget(sector_label)

        self.sector_combo = QComboBox(self)
        self.sector_combo.addItem("All Sectors", None)  
        self.sector_combo.currentIndexChanged.connect(self._on_sector_changed)
        
        filter_layout.addWidget(self.sector_combo)

        # Add List Widget to display filtered quotes - Inside the group box, below the label and combo
        self.filtered_quotes_list = QListWidget()
        self.filtered_quotes_list.keyPressEvent = self.list_key_press_event
        self.filtered_quotes_list.itemClicked.connect(self._on_filtered_quote_clicked) # Connect click signal
        filter_layout.addWidget(self.filtered_quotes_list)
        layout.addWidget(filter_group)

    def _populate_sector_combo(self):
        sectors_list = self.sectors_list_provider()
        if sectors_list:
            for sector_name in sorted(sectors_list):
                self.sector_combo.addItem(sector_name, sector_name)  

    def refresh_sectors(self):
        self.sector_combo.clear()
        self.sector_combo.addItem("All Sectors", None)
        self._populate_sector_combo()

    def _filter_quotes(self, selected_sector):
        all_quotes_data = self.all_quotes_data_provider
        if not all_quotes_data:
            return []
        if selected_sector:
            filtered_quotes = [name for name, data in all_quotes_data.items()
                                if "sectors" in data and any(s.get("name") == selected_sector for s in data["sectors"])]
        else:
            filtered_quotes = list(all_quotes_data.keys())
        filtered_quotes.sort()
        if "date" in filtered_quotes: filtered_quotes.remove("date")
        return filtered_quotes

    def _on_sector_changed(self, index):
        if index is None:
            selected_sector = "All Sectors"
        else:
            selected_sector = self.sector_combo.itemData(index)
        if self.selected_sector != selected_sector:
            self.selected_sector = selected_sector
            if selected_sector == "All Sectors":
                filtered_quotes = self._filter_quotes(None)
            else:
                filtered_quotes = self._filter_quotes(selected_sector)
            # if filtered_quotes:
            self.filterChanged.emit(filtered_quotes)            
            self._update_filtered_quotes_list_ui(filtered_quotes)
    
    def list_key_press_event(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Up:
            new_row = max(0, self.filtered_quotes_list.currentRow() - 1)
            self.filtered_quotes_list.setCurrentRow(new_row)
            if self.filtered_quotes_list.currentItem():
                self._on_filtered_quote_clicked(self.filtered_quotes_list.currentItem())
        elif event.key() == Qt.Key.Key_Down:
            new_row = min(self.filtered_quotes_list.count() - 1, self.filtered_quotes_list.currentRow() + 1)
            self.filtered_quotes_list.setCurrentRow(new_row)
            if self.filtered_quotes_list.currentItem():
                self._on_filtered_quote_clicked(self.filtered_quotes_list.currentItem())

    def _on_filtered_quote_clicked(self, item):
        selected_quote = item.text()  # Get the text of the selected item (quote name)
        self.quoteSelected.emit(selected_quote)  # Emit the new signal

    def _update_filtered_quotes_list_ui(self, filtered_quotes):
        self.filtered_quotes_list.clear()
        for quote_name in filtered_quotes:
            self.filtered_quotes_list.addItem(quote_name)

    def clear_filter(self):
        self.sector_combo.setCurrentIndex(0)  

    def get_selected_sector(self):
        return self.selected_sector
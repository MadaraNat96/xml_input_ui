# t:\Work\xml_input_ui\chart_sub_window.py
from PyQt6.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QTableWidget, QHeaderView, QTableWidgetItem, QLabel, QCheckBox
from PyQt6.QtWidgets import QPushButton, QHBoxLayout, QDialog, QListWidget, QDialogButtonBox
from PyQt6.QtCore import Qt, QSettings
import os
import xml.etree.ElementTree as ET


class ChartSubWindow(QMainWindow):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Chart Sub Window")
        self.setGeometry(200, 200, 600, 400)  # Adjust size as needed
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.Window)
        self.FA_LIST_DISPLAY = ("EPS", "PE", "ROE", "BLNR", "BLNG")        
        self.config_path = os.path.join(os.path.dirname(__file__), "chart_time.cfg")        
        self.settings = QSettings(self.config_path, QSettings.Format.IniFormat)
        self.selected_years = self.settings.value("selected_years", [], type=list)
        self.selected_quarters = self.settings.value("selected_quarters", [], type=list)

        self.init_ui()

    def _create_button_layout(self):
        button_layout = QHBoxLayout()
        button_layout.addStretch(1)  # Push buttons to the right
        self.choose_years_button = QPushButton("Choose Years", self)
        self.choose_quarters_button = QPushButton("Choose Quarters", self)
        self.choose_years_button.clicked.connect(self.choose_years)
        self.choose_quarters_button.clicked.connect(self.choose_quarters)
        button_layout.addWidget(self.choose_years_button)
        button_layout.addWidget(self.choose_quarters_button)
        return button_layout

    def choose_years(self):
        available_years = self._get_available_time_periods("yearly")
        selected = self._show_selection_dialog("Choose Years", available_years, self.selected_years)
        if selected is not None:            
            self.selected_years = selected
            self.settings.setValue("selected_years", self.selected_years)
            self.load_data(self.current_quote, self.current_xml_file_path)  # Reload data with new selection

    def choose_quarters(self):
        available_quarters = self._get_available_time_periods("quarterly")
        selected = self._show_selection_dialog("Choose Quarters", available_quarters, self.selected_quarters)
        if selected is not None:            
            self.selected_quarters = selected
            self.settings.setValue("selected_quarters", self.selected_quarters)
            self.load_data(self.current_quote, self.current_xml_file_path)  # Reload data with new selection

    def _get_available_time_periods(self, period_type):
        periods = []
        try:
            tree = ET.parse(self.current_xml_file_path)
            root = tree.getroot()
            if not self.current_quote:
                return []
            quote = root.find(f".//quote[name='{self.current_quote}']")
            data = quote.find(f"stat/{period_type}")
            if data is not None:
                fa = data.find(f"EPS")
                if fa.tag:
                    for elem in fa.findall("*"):
                        periods.append(elem.tag)
        except (FileNotFoundError, ET.ParseError):
            return []  # Handle errors gracefully
        return sorted(list(periods), reverse=True)        

    def _show_selection_dialog(self, title, items, current_selection):
        """
        Displays a dialog for selecting multiple items with checkboxes.
        """
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        layout = QVBoxLayout(dialog)

        # Create checkboxes for each item
        checkboxes = {}
        for item in items:
            checkbox = QCheckBox(item, dialog)
            checkbox.setChecked(item in current_selection)
            layout.addWidget(checkbox)
            checkboxes[item] = checkbox

        # Add OK and Cancel buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, dialog)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Return a list of checked items
            return [item for item, checkbox in checkboxes.items() if checkbox.isChecked()]
        return None





    def init_ui(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        self.tables = {}

        # Add buttons at the top
        button_layout = self._create_button_layout()
        layout.addLayout(button_layout)

        for fa in self.FA_LIST_DISPLAY:
             label = QLabel(fa)
             layout.addWidget(label)

             table = QTableWidget(self)
             self.tables[fa] = table
             layout.addWidget(table)
             table.setRowCount(1)
             table.setVerticalHeaderLabels([fa])

    def load_data(self, quote_name, xml_file_path):  # Add quote_name and xml_file_path params
        self.current_quote = quote_name  # Store current quote and xml file path
        self.current_xml_file_path = xml_file_path
        try:
            tree = ET.parse(xml_file_path)
            root = tree.getroot()
            
            quote_element = root.find(f".//quote[name='{quote_name}']")
            if quote_element is None:
                 print(f"Quote {quote_name} not found in XML")
                 return
            for fa, table in self.tables.items():
                self._load_table_data(table, quote_element, fa)
        
        except FileNotFoundError:
            print(f"Error: XML file not found at {xml_file_path}")
        except ET.ParseError as e:
            print(f"Error parsing XML: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

            # Clear the table in case of an error to prevent stale data
            for table in list(self.tables.values()):
                table.setRowCount(0)
                table.setColumnCount(0)
                table.setHorizontalHeaderLabels([])

    def _load_table_data(self, table_widget, quote_element, fa):
        yearly_data = quote_element.find(f"stat/yearly/{fa}")
        quarterly_data = quote_element.find(f"stat/quarterly/{fa}")
        
        yearly_values = []
        if yearly_data is not None:            
            yearly_values = [(elem.tag, elem.text) for elem in yearly_data.findall("*") if elem.tag]
            if self.selected_years:                
                yearly_values = [(year, val) for year, val in yearly_values if year in self.selected_years]
            yearly_values.sort(key=lambda x: x[0])  # Ascending order
            yearly_values = yearly_values[:5]  # Take latest 5 after filtering & sorting
            
        quarterly_values = []
        if quarterly_data is not None:                        
             quarterly_values = [(elem.tag, elem.text) for elem in quarterly_data.findall("*") if elem.tag]
             if self.selected_quarters:  # Apply filter only for EPS
                 quarterly_values = [(quarter, val) for quarter, val in quarterly_values if quarter in self.selected_quarters]
             quarterly_values.sort(key=lambda x: x[0])  # Ascending order
             quarterly_values = quarterly_values[:4]  # Take latest 4 after filtering & sorting
            
        combined_values = yearly_values + quarterly_values
        headers = [f"{year}" for year, val in yearly_values] + [f"{quarter}" for quarter, val in quarterly_values]

        num_cols = len(headers)
        table_widget.setColumnCount(num_cols)        
        table_widget.setHorizontalHeaderLabels(headers)        
        for col, (period, value) in enumerate(combined_values):
            table_widget.setItem(0, col, QTableWidgetItem(str(value)))
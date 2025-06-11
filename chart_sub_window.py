# t:\Work\xml_input_ui\chart_sub_window.py
from PyQt6.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QTableWidget, QHeaderView, QTableWidgetItem, QLabel
from PyQt6.QtCore import Qt
import xml.etree.ElementTree as ET


class ChartSubWindow(QMainWindow):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Chart Sub Window")
        self.setGeometry(200, 200, 600, 400)  # Adjust size as needed
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.Window)  # Ensure it's a separate window
        self.FA_LIST_DISPLAY = ("EPS", "PE", "ROE", "BLNR", "BLNG")
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        self.tables = {}
        for fa in self.FA_LIST_DISPLAY:
            label = QLabel(fa)
            layout.addWidget(label)            

            table = QTableWidget(self)
            self.tables[fa] = table
            layout.addWidget(table)
            table.setRowCount(1)
            table.setVerticalHeaderLabels([fa])

    def load_data(self, quote_name, xml_file_path):
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
             yearly_values = [(elem.tag, elem.text) for elem in yearly_data.findall("*")]
             yearly_values.sort(key=lambda x: x[0])  # Ascending order
             yearly_values = yearly_values[:5]
            
        quarterly_values = []
        if quarterly_data is not None:            
             quarterly_values = [(elem.tag, elem.text) for elem in quarterly_data.findall("*")]
             quarterly_values.sort(key=lambda x: x[0])  # Ascending order
             quarterly_values = quarterly_values[:4]
            
        combined_values = yearly_values + quarterly_values
        headers = [f"{year}" for year, val in yearly_values] + [f"{quarter}" for quarter, val in quarterly_values]

        num_cols = len(headers)
        table_widget.setColumnCount(num_cols)
        table_widget.setHorizontalHeaderLabels(headers)

        for col, (period, value) in enumerate(combined_values):
            table_widget.setItem(0, col, QTableWidgetItem(str(value)))
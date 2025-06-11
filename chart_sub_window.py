# t:\Work\xml_input_ui\chart_sub_window.py
from PyQt6.QtWidgets import QMainWindow, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt


class ChartSubWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Chart Sub Window")
        self.setGeometry(200, 200, 600, 400)  # Adjust size as needed
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.Window)  # Ensure it's a separate window
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        # Add your chart widget here:
        # self.chart_widget = YourChartWidget()  # Replace with your actual chart widget
        # layout.addWidget(self.chart_widget)
        # You might need to pass relevant data to your chart widget
        # Example: self.chart_widget.load_data(some_data)

        # For now, it's an empty window.  Add your chart widget as shown above.
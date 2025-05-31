# t:\Work\xml_input_ui\ui_components\eps_growth_chart_widget.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton,
    QInputDialog, QMessageBox
)
from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtCharts import (
    QChart, QChartView, QBarSet, QBarCategoryAxis, QValueAxis,
    QStackedBarSeries, QLineSeries
)
from PyQt6.QtGui import QColor, QPen


class EPSGrowthChartWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._all_eps_data_for_current_quote = [] # Stores the full EPS structure for the selected quote
        self._available_eps_years_for_chart = []
        self._selected_year_for_chart = None
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.chart_group_box = QGroupBox("EPS Growth Chart")
        chart_group_layout = QVBoxLayout(self.chart_group_box)
        chart_group_layout.setContentsMargins(5, 5, 5, 5)
        chart_group_layout.setSpacing(3)

        # --- Top Actions ---
        actions_layout = QHBoxLayout()
        self.choose_year_button = QPushButton("Choose Year for Chart")
        self.choose_year_button.setFixedHeight(20)
        self.choose_year_button.clicked.connect(self._handle_choose_year_for_chart_dialog)
        actions_layout.addWidget(self.choose_year_button)
        actions_layout.addStretch()
        chart_group_layout.addLayout(actions_layout)

        # --- Chart View ---
        self.chart_view = QChartView()
        self.chart_view.setMinimumHeight(300) # Increased height
        self.chart_view.chart().setTitle("Select a year to view EPS Growth")
        chart_group_layout.addWidget(self.chart_view)

        main_layout.addWidget(self.chart_group_box)
        self.setLayout(main_layout)
        self.setEnabled(False) # Initially disabled

    def load_data(self, eps_data_for_quote):
        """
        Loads all EPS data for the currently selected quote.
        eps_data_for_quote is a list of dicts, e.g.,
        [{"name": "2024", "companies": [{"name": "CMPA", "value": "10", "growth": "5"}, ...]}, ...]
        """
        self.clear_data() # Clear previous chart and data
        self._all_eps_data_for_current_quote = eps_data_for_quote if eps_data_for_quote else []
        self._available_eps_years_for_chart = sorted(
            [year_data.get("name") for year_data in self._all_eps_data_for_current_quote if year_data.get("name")]
        )
        self.choose_year_button.setEnabled(bool(self._available_eps_years_for_chart))

        if not self._available_eps_years_for_chart:
            self.chart_view.chart().setTitle("No EPS data available for chart")


    def _handle_choose_year_for_chart_dialog(self):
        if not self._available_eps_years_for_chart:
            QMessageBox.information(self, "No EPS Years", "No EPS years with data are available for charting.")
            return

        year_name, ok = QInputDialog.getItem(self, "Select EPS Year for Chart",
                                             "Year:", self._available_eps_years_for_chart, 0, False)
        if ok and year_name:
            self.update_chart(year_name)

    def update_chart(self, year_name):
        self._selected_year_for_chart = year_name
        chart = QChart()
        chart.setTitle(f"EPS Growth (%) for {year_name}")
        chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)

        stacked_series = QStackedBarSeries()
        positive_growth_set = QBarSet("Positive Growth")
        negative_growth_set = QBarSet("Negative Growth")

        positive_growth_set.setColor(QColor("green"))
        negative_growth_set.setColor(QColor("red"))

        categories = []
        year_data_to_chart = next((yd for yd in self._all_eps_data_for_current_quote if yd.get("name") == year_name), None)
        
        has_data_to_plot = False

        if year_data_to_chart and year_data_to_chart.get("companies"):
            for company_data in year_data_to_chart["companies"]:
                company_name = company_data.get("name", "N/A")
                categories.append(company_name)
                growth_str = company_data.get("growth", "").replace('%', '')
                growth_val = 0.0 
                if growth_str: 
                    try:
                        growth_val = float(growth_str)
                        has_data_to_plot = True
                    except ValueError:
                        growth_val = 0.0
                
                if growth_val > 0:
                    positive_growth_set.append(growth_val)
                    negative_growth_set.append(0)
                elif growth_val < 0:
                    negative_growth_set.append(growth_val)
                    positive_growth_set.append(0)
                else:
                    positive_growth_set.append(0)
                    negative_growth_set.append(0)
            
            if positive_growth_set.count() > 0: stacked_series.append(positive_growth_set)
            if negative_growth_set.count() > 0: stacked_series.append(negative_growth_set)
        
        chart.setTitle(f"No growth data available for EPS {year_name}" if not categories else \
                       f"No numerical growth data for EPS {year_name}" if not has_data_to_plot else \
                       f"EPS Growth (%) for {year_name}")

        chart.addSeries(stacked_series)
        axis_x = QBarCategoryAxis()
        axis_x.append(categories if categories else ["No Data"])
        chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        stacked_series.attachAxis(axis_x)

        axis_y = QValueAxis()
        axis_y.setTitleText("Growth (%)")
        chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        stacked_series.attachAxis(axis_y)

        if categories:
            zero_line_series = QLineSeries()
            zero_line_series.append(QPointF(-0.5, 0))
            zero_line_series.append(QPointF(len(categories) - 0.5, 0))
            pen = QPen(Qt.GlobalColor.black)
            pen.setWidth(1)
            zero_line_series.setPen(pen)
            chart.addSeries(zero_line_series)
            zero_line_series.attachAxis(axis_x)
            zero_line_series.attachAxis(axis_y)

        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignmentFlag.AlignBottom)
        self.chart_view.setChart(chart)

    def clear_data(self):
        self._all_eps_data_for_current_quote = []
        self._available_eps_years_for_chart = []
        self._selected_year_for_chart = None
        new_chart = QChart()
        new_chart.setTitle("Select a year to view EPS Growth")
        self.chart_view.setChart(new_chart)
        self.choose_year_button.setEnabled(False)

    def setEnabled(self, enabled):
        self.chart_group_box.setEnabled(enabled)
        self.choose_year_button.setEnabled(enabled and bool(self._available_eps_years_for_chart))
        super().setEnabled(enabled)
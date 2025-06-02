# t:\Work\xml_input_ui\ui_components\record_report_section_widget.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox, QPushButton,
    QFormLayout, QComboBox, QDateEdit, QStyle, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
import data_utils # For default date and potentially other utilities
from .ui_utils import _clear_qt_layout # Import from the new ui_utils

class RecordReportSectionWidget(QWidget):
    MAX_REPORTS_DISPLAYED = 6 # Changed to 6
    recordReportAddRequested = pyqtSignal()
    recordReportRemoveRequested = pyqtSignal(object)
    recordReportDetailChanged = pyqtSignal(object, str, str, str)
    manualRefreshRequested = pyqtSignal() # New signal for manual refresh

    def __init__(self, fixed_companies_provider_func, parent=None):
        super().__init__(parent)
        self.fixed_companies_provider_func = fixed_companies_provider_func
        self.report_entries = []
        self._init_ui()

    def _init_ui(self):
        self.record_group = QGroupBox("Record Reports")
        record_main_layout = QVBoxLayout(self.record_group)
        record_main_layout.setContentsMargins(2, 5, 5, 5)
        record_main_layout.setSpacing(3)

        actions_layout = QHBoxLayout()
        actions_layout.addStretch()

        refresh_button = QPushButton(icon=QApplication.style().standardIcon(QStyle.StandardPixmap.SP_BrowserReload))
        refresh_button.setToolTip("Refresh Record Reports from current data")
        refresh_button.setFixedSize(20, 20)
        refresh_button.clicked.connect(self.manualRefreshRequested.emit) # Emit the new signal
        actions_layout.addWidget(refresh_button)

        add_button = QPushButton(icon=QApplication.style().standardIcon(QStyle.StandardPixmap.SP_DialogApplyButton))
        add_button.setToolTip("Add Report")
        add_button.setFixedSize(20, 20)
        add_button.clicked.connect(self.recordReportAddRequested)
        actions_layout.addWidget(add_button)

        record_main_layout.addLayout(actions_layout)

        self.record_items_layout = QGridLayout() # Changed to QGridLayout
        record_main_layout.addLayout(self.record_items_layout)


        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0,0,0,0)
        main_layout.addWidget(self.record_group)

    # This method creates the UI and data for a single report entry.
    def _create_single_report_entry_ui_data(self, company_str="", date_str="", color_str=""):
        entry_gbox = QGroupBox()
        entry_gbox.setObjectName("recordReportEntryBox")
        entry_layout = QVBoxLayout(entry_gbox)
        entry_layout.setContentsMargins(4, 8, 4, 4)
        entry_layout.setSpacing(3)

        top_bar = QHBoxLayout()
        top_bar.addStretch()
        
        # Initial entry_data structure
        entry_data = {
            "widget": entry_gbox,
            "current_color": color_str or "default",
            # current_company and current_date will be refined after widgets are created
        }

        for btn_txt, c_name in [("R", "red"), ("G", "green"), ("Y", "yellow"), ("W", "white")]:
            c_btn = QPushButton(btn_txt)
            c_btn.setFixedSize(16, 16)
            c_btn.setToolTip(f"Set color to {c_name}")
            c_btn.clicked.connect(lambda chk=False, ed=entry_data, cn=c_name: self._handle_report_color_change(ed, cn))
            top_bar.addWidget(c_btn)
        
        top_bar.addSpacing(5)
        remove_btn = QPushButton(icon=QApplication.style().standardIcon(QStyle.StandardPixmap.SP_DialogCancelButton))
        remove_btn.setToolTip("Remove this report entry")
        remove_btn.setFixedSize(16, 16)
        top_bar.addWidget(remove_btn)
        entry_layout.addLayout(top_bar)

        form = QFormLayout()
        form.setContentsMargins(0,0,0,0)
        combo = QComboBox()
        fixed_comps = self.fixed_companies_provider_func()
        if fixed_comps: # Ensure fixed_comps is not None or empty before adding
            combo.addItems(fixed_comps)
        
        if company_str and company_str in fixed_comps: 
            combo.setCurrentText(company_str)
        elif fixed_comps and combo.count() > 0: # If not found or empty, select first if available
            combo.setCurrentIndex(0)

        date_edit = QDateEdit()
        date_edit.setDisplayFormat("MM/dd/yyyy")
        date_edit.setCalendarPopup(True)
        q_date = QDate.fromString(date_str, "MM/dd/yyyy") if date_str else data_utils.get_default_working_date()
        date_edit.setDate(q_date if q_date.isValid() else data_utils.get_default_working_date())
        entry_data["current_date"] = date_edit.date().toString("MM/dd/yyyy")
        entry_data["current_company"] = combo.currentText() # Get actual initial company from combo

        form.addRow("Company:", combo)
        form.addRow("Date:", date_edit)
        entry_layout.addLayout(form)

        # Store all relevant widgets in entry_data for signal connection and access
        entry_data.update({"company_combo": combo, "date_edit": date_edit, "remove_button": remove_btn})

        # Connect signals for this entry
        combo.currentTextChanged.connect(lambda txt, ed=entry_data: self._handle_report_detail_change(ed, "company", txt))
        date_edit.dateChanged.connect(lambda qd, ed=entry_data: self._handle_report_detail_change(ed, "date", qd.toString("MM/dd/yyyy")))
        date_edit.editingFinished.connect(lambda ed=entry_data, de=date_edit: self._handle_report_detail_change(ed, "date", de.date().toString("MM/dd/yyyy")))
        remove_btn.clicked.connect(lambda checked=False, ed=entry_data: self.recordReportRemoveRequested.emit(ed))
        # Connect color buttons (assuming this was implicitly part of the original add_report_entry)
        # This loop was already present, just ensuring it's clear it connects to _handle_report_color_change

        self._apply_report_color_style(entry_gbox, entry_data["current_color"])
        return entry_data

    def _handle_report_detail_change(self, entry_data, field, new_val):
        old_val = entry_data.get(f"current_{field}", "")
        if new_val != old_val:
            self.recordReportDetailChanged.emit(entry_data, field, old_val, new_val)

    def _remove_report_entry(self, entry_data):
        if entry_data in self.report_entries:
            self.report_entries.remove(entry_data)
            widget = entry_data.get("widget")
            # Explicitly remove from layout before deleting, though _clear_qt_layout in refresh would also handle it.
            if widget and self.record_items_layout:
                self.record_items_layout.removeWidget(widget)
            if widget: widget.deleteLater()

    def _handle_report_color_change(self, entry_data, color_name):
        old_color = entry_data.get("current_color", "default")
        if color_name != old_color:
            self.recordReportDetailChanged.emit(entry_data, "color", old_color, color_name)

    def _apply_report_color_style(self, gbox, color_name):
        gbox.setProperty("report_color", color_name or "default")
        gbox.style().unpolish(gbox); gbox.style().polish(gbox); gbox.update()

    # _apply_report_display_limit is no longer needed as load_data handles the limit.

    def load_data(self, record_list_from_model):
        self.clear_data()

        all_created_ui_entries = []
        for r_data in record_list_from_model: # Process all reports from the data model
            entry_ui_data = self._create_single_report_entry_ui_data(
                company_str=r_data.get("company",""), 
                date_str=r_data.get("date",""), 
                color_str=r_data.get("color","")
            )
            all_created_ui_entries.append(entry_ui_data)

        # Sort all created UI entries by their date (latest first)
        def get_date_key_for_ui_entry(ui_entry):
            # Use the 'current_date' from the entry_data, which is derived from the QDateEdit widget
            d = QDate.fromString(ui_entry.get("current_date", ""), "MM/dd/yyyy")
            return d if d.isValid() else QDate(1900,1,1)
        
        all_created_ui_entries.sort(key=get_date_key_for_ui_entry, reverse=True)

        # Now, populate self.report_entries with the top MAX_REPORTS_DISPLAYED
        # and schedule deletion for widgets of entries that won't be displayed.
        for i, entry_to_process in enumerate(all_created_ui_entries):
            if i < self.MAX_REPORTS_DISPLAYED:
                self.report_entries.append(entry_to_process) # Add to the list of entries to be displayed
            else:
                # This entry won't be displayed, so clean up its widget
                if entry_to_process.get("widget"):
                    entry_to_process["widget"].deleteLater()
        
        self._refresh_report_grid_layout()

    def _refresh_report_grid_layout(self):
        # 1. Remove all widgets currently in the layout without deleting them.
        #    The widgets in self.report_entries are new, so old ones in layout can be cleared.
        #    self.clear_data() (called by load_data) should have already invoked _clear_qt_layout.
        #    This loop ensures the layout is empty before repopulating.
        while self.record_items_layout.count():
            item = self.record_items_layout.takeAt(0) # takeAt(0) removes the item from layout
            if item and item.widget():
                # Set parent to None to detach; actual deletion is handled by clear_data or if widget is no longer needed
                item.widget().setParent(None) 

        # 2. Re-add widgets from self.report_entries (which is the source of truth)
        for idx, entry_data in enumerate(self.report_entries): # self.report_entries is already sorted and limited
            widget = entry_data.get("widget")
            if widget: # Ensure widget exists in the entry_data
                row, col = divmod(idx, 2) # 2 columns
                self.record_items_layout.addWidget(widget, row, col)
        
        # Force layout update and parent resizing
        self.record_items_layout.activate() # Activate the grid layout
        if self.record_group.layout():
            self.record_group.layout().activate() # Activate the group box's main layout
        self.record_group.adjustSize()      # Tell the group box to resize based on content
        self.record_group.updateGeometry()  # Request a geometry update for the group box

    def get_data(self):
        return [{"company": e["company_combo"].currentText(),
                 "date": e["date_edit"].date().toString("MM/dd/yyyy"),
                 "color": e.get("current_color", "default")} for e in self.report_entries]

    def clear_data(self):
        _clear_qt_layout(self.record_items_layout)
        self.report_entries.clear()
        # self._refresh_report_grid_layout() # Optionally call to ensure grid is visually empty

    def update_company_dropdowns(self):
        fixed_comps = self.fixed_companies_provider_func()
        for entry in self.report_entries:
            combo = entry.get("company_combo")
            if combo:
                sel = combo.currentText()
                combo.clear()
                combo.addItems(fixed_comps)
                if sel in fixed_comps: combo.setCurrentText(sel)
                elif fixed_comps: combo.setCurrentIndex(0)

    def update_report_entry_detail(self, entry_data, field, new_val, from_command=False):
        # Signals are now connected in add_report_entry.
        # This method only updates the UI and internal 'current_whatever' values.
        if entry_data not in self.report_entries: return
        if field == "company":
            entry_data["company_combo"].blockSignals(True)
            entry_data["company_combo"].setCurrentText(new_val)
            entry_data["company_combo"].blockSignals(False)
            entry_data["current_company"] = new_val
        elif field == "date":
            q_date = QDate.fromString(new_val, "MM/dd/yyyy")
            if q_date.isValid():
                entry_data["date_edit"].blockSignals(True)
                entry_data["date_edit"].setDate(q_date)
                entry_data["date_edit"].blockSignals(False)
                entry_data["current_date"] = new_val
        elif field == "color":
            entry_data["current_color"] = new_val
            self._apply_report_color_style(entry_data["widget"], new_val)

    def setEnabled(self, enabled):
        self.record_group.setEnabled(enabled)
        super().setEnabled(enabled)
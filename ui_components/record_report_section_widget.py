# t:\Work\xml_input_ui\ui_components\record_report_section_widget.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton,
    QFormLayout, QComboBox, QDateEdit, QStyle, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
import data_utils # For default date and potentially other utilities
from .ui_utils import _clear_qt_layout # Import from the new ui_utils

class RecordReportSectionWidget(QWidget):
    MAX_REPORTS_DISPLAYED = 5
    recordReportAddRequested = pyqtSignal()
    recordReportRemoveRequested = pyqtSignal(object)
    recordReportDetailChanged = pyqtSignal(object, str, str, str)

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
        add_button = QPushButton(icon=QApplication.style().standardIcon(QStyle.StandardPixmap.SP_DialogApplyButton))
        add_button.setToolTip("Add Report")
        add_button.setFixedSize(20, 20)
        add_button.clicked.connect(self.recordReportAddRequested)
        actions_layout.addWidget(add_button)
        record_main_layout.addLayout(actions_layout)

        self.record_items_layout = QVBoxLayout()
        record_main_layout.addLayout(self.record_items_layout)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0,0,0,0)
        main_layout.addWidget(self.record_group)

    def add_report_entry(self, company_str="", date_str="", color_str="", insert_at_index=0):
        entry_gbox = QGroupBox()
        entry_gbox.setObjectName("recordReportEntryBox")
        entry_layout = QVBoxLayout(entry_gbox)
        entry_layout.setContentsMargins(4, 8, 4, 4)
        entry_layout.setSpacing(3)

        top_bar = QHBoxLayout()
        top_bar.addStretch()
        entry_data = {"widget": entry_gbox, "current_color": color_str or "default",
                      "current_company": company_str, "current_date": date_str}

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
        combo.addItems(fixed_comps)
        init_comp = company_str
        if company_str and company_str in fixed_comps: combo.setCurrentText(company_str)
        elif fixed_comps:
            combo.setCurrentIndex(0)
            init_comp = combo.currentText() if combo.count() > 0 else ""
        entry_data["current_company"] = init_comp

        date_edit = QDateEdit()
        date_edit.setDisplayFormat("MM/dd/yyyy")
        date_edit.setCalendarPopup(True)
        q_date = QDate.fromString(date_str, "MM/dd/yyyy") if date_str else data_utils.get_default_working_date()
        date_edit.setDate(q_date if q_date.isValid() else data_utils.get_default_working_date())
        entry_data["current_date"] = date_edit.date().toString("MM/dd/yyyy")
        
        form.addRow("Company:", combo)
        form.addRow("Date (MM/DD/YYYY):", date_edit)
        entry_layout.addLayout(form)

        self.record_items_layout.insertWidget(insert_at_index, entry_gbox)
        entry_data.update({"company_combo": combo, "date_edit": date_edit})
        self.report_entries.insert(insert_at_index, entry_data)

        combo.currentTextChanged.connect(lambda txt, ed=entry_data: self._handle_report_detail_change(ed, "company", txt))
        date_edit.dateChanged.connect(lambda qd, ed=entry_data: self._handle_report_detail_change(ed, "date", qd.toString("MM/dd/yyyy")))
        date_edit.editingFinished.connect(lambda ed=entry_data, de=date_edit: self._handle_report_detail_change(ed, "date", de.date().toString("MM/dd/yyyy")))
        remove_btn.clicked.connect(lambda: self.recordReportRemoveRequested.emit(entry_data))
        
        self._apply_report_color_style(entry_gbox, entry_data["current_color"])
        self._apply_report_display_limit()
        return entry_data

    def _handle_report_detail_change(self, entry_data, field, new_val):
        old_val = entry_data.get(f"current_{field}", "")
        if new_val != old_val:
            self.recordReportDetailChanged.emit(entry_data, field, old_val, new_val)

    def _remove_report_entry(self, entry_data):
        if entry_data in self.report_entries:
            self.report_entries.remove(entry_data)
            widget = entry_data.get("widget")
            if widget: widget.deleteLater()

    def _handle_report_color_change(self, entry_data, color_name):
        old_color = entry_data.get("current_color", "default")
        if color_name != old_color:
            self.recordReportDetailChanged.emit(entry_data, "color", old_color, color_name)

    def _apply_report_color_style(self, gbox, color_name):
        gbox.setProperty("report_color", color_name or "default")
        gbox.style().unpolish(gbox); gbox.style().polish(gbox); gbox.update()

    def _apply_report_display_limit(self):
        while len(self.report_entries) > self.MAX_REPORTS_DISPLAYED:
            oldest = self.report_entries.pop()
            if oldest.get("widget"): oldest["widget"].deleteLater()

    def load_data(self, record_list):
        self.clear_data()
        def get_date_key(r):
            d = QDate.fromString(r.get("date", ""), "MM/dd/yyyy")
            return d if d.isValid() else QDate(1900,1,1)
        record_list.sort(key=get_date_key, reverse=True)
        for idx, r_data in enumerate(record_list[:self.MAX_REPORTS_DISPLAYED]):
            self.add_report_entry(r_data.get("company",""), r_data.get("date",""), r_data.get("color",""), idx)

    def get_data(self):
        return [{"company": e["company_combo"].currentText(),
                 "date": e["date_edit"].date().toString("MM/dd/yyyy"),
                 "color": e.get("current_color", "default")} for e in self.report_entries]

    def clear_data(self):
        _clear_qt_layout(self.record_items_layout)
        self.report_entries.clear()

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

    def update_report_entry_detail(self, entry_data, field, new_val, from_cmd=False):
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
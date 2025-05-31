# t:\Work\xml_input_ui\ui_components\eps_section_widget.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton,
    QFormLayout, QLineEdit, QInputDialog, QMessageBox, QStyle, QApplication,
    QDialog # QDialog might be used if EPSYearSelectionDialog is moved here or for other internal dialogs
)
from PyQt6.QtCore import Qt, pyqtSignal
from dialogs import EPSYearSelectionDialog, EPriceCompanySelectionDialog # Assuming dialogs.py remains separate
from custom_widgets import FocusAwareLineEdit, HighlightableGroupBox
from .ui_utils import _clear_qt_layout # Import from the new ui_utils

class EPSSectionWidget(QWidget):
    companyLineEditFocusGained = pyqtSignal(str, QLineEdit)
    companyLineEditFocusLost = pyqtSignal(str, QLineEdit)
    epsYearAddRequested = pyqtSignal(str)
    epsYearRemoveRequested = pyqtSignal(str)
    epsYearDisplayChangeRequested = pyqtSignal(list, list)
    epsCompaniesForYearDisplayChangeRequested = pyqtSignal(str, list, list)
    epsValueChanged = pyqtSignal(str, str, str, str, str)

    def __init__(self, fixed_companies_provider, parent=None):
        super().__init__(parent)
        self.eps_year_entries = []
        self.selected_eps_years_to_display = []
        self.fixed_companies_provider = fixed_companies_provider
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0,0,0,0)
        self.eps_group_box = QGroupBox("EPS Years")
        eps_main_layout = QVBoxLayout(self.eps_group_box)
        eps_main_layout.setContentsMargins(2, 5, 5, 5)
        eps_main_layout.setSpacing(3)

        eps_top_actions_layout = QHBoxLayout()
        eps_top_actions_layout.addStretch()
        self.choose_year_button = QPushButton("Choose Year")
        self.choose_year_button.setToolTip("Select which EPS year to display")
        self.choose_year_button.setFixedSize(80, 20)
        self.choose_year_button.clicked.connect(self._handle_choose_eps_year_dialog)
        eps_top_actions_layout.addWidget(self.choose_year_button)

        add_eps_year_button = QPushButton()
        add_eps_year_button.setToolTip("Add New EPS Year Entry")
        add_eps_year_button.setIcon(QApplication.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogNewFolder))
        add_eps_year_button.setFixedSize(20,20)
        add_eps_year_button.clicked.connect(self._handle_add_new_eps_year_dialog)
        eps_top_actions_layout.addWidget(add_eps_year_button)
        eps_main_layout.addLayout(eps_top_actions_layout)
        
        self.eps_items_layout = QVBoxLayout()
        eps_main_layout.addLayout(self.eps_items_layout)
        main_layout.addWidget(self.eps_group_box)
        self.setLayout(main_layout)
        self._update_visible_eps_years()

    def load_data(self, eps_data_list):
        self.clear_data()
        eps_data_list = eps_data_list or []
        for year_data in eps_data_list:
            self._add_eps_year_fields(
                year_name_str=year_data.get("name", ""),
                companies_data_list=year_data.get("companies", [])
            )
        self._update_visible_eps_years()

    def get_data(self):
        return [
            {"name": ye.get("year_name",""),
             "companies": [{"name": ce.get("name",""), "value": ce["value_edit"].text(), "growth": ce["growth_edit"].text()}
                           for ce in ye["company_entries"]]}
            for ye in self.eps_year_entries
        ]

    def clear_data(self):
        _clear_qt_layout(self.eps_items_layout)
        self.eps_year_entries.clear()
        self.selected_eps_years_to_display.clear()
        self._update_visible_eps_years()

    def refresh_structure_with_new_fixed_companies(self, new_fixed_companies_list):
        self.fixed_companies_provider = new_fixed_companies_list
        stored_selections = {e["year_name"]: list(e["selected_companies_to_display_for_year"]) for e in self.eps_year_entries}
        current_data = self.get_data()
        _clear_qt_layout(self.eps_items_layout)
        self.eps_year_entries.clear()
        self.load_data(current_data)
        for ye in self.eps_year_entries:
            if ye["year_name"] in stored_selections:
                original_selection = stored_selections[ye["year_name"]]
                ye["selected_companies_to_display_for_year"] = [c for c in original_selection if c in self.fixed_companies_provider]
            self._update_visible_eps_companies_for_year(ye)

    def _add_eps_year_fields(self, year_name_str="", companies_data_list=None):
        if not year_name_str:
            QMessageBox.warning(self, "Input Error", "Year name is required for EPS entry.")
            return
        companies_data_list = companies_data_list or []
        selected_companies_for_this_year = list(self.fixed_companies_provider)

        eps_year_group_box = QGroupBox(f"EPS {year_name_str}")
        year_main_layout = QVBoxLayout(eps_year_group_box)
        year_main_layout.setContentsMargins(2, 2, 2, 2)
        year_main_layout.setSpacing(3)

        year_title_bar_layout = QHBoxLayout()
        year_title_bar_layout.addStretch()
        remove_year_button = QPushButton(icon=QApplication.style().standardIcon(QStyle.StandardPixmap.SP_DialogCancelButton))
        remove_year_button.setToolTip("Delete this EPS Year")
        remove_year_button.setFixedSize(20, 20)

        choose_companies_button = QPushButton("Choose Companies")
        choose_companies_button.setToolTip(f"Select which companies to display for EPS {year_name_str}")
        choose_companies_button.setFixedHeight(20)
        
        refresh_button = QPushButton(icon=QApplication.style().standardIcon(QStyle.StandardPixmap.SP_BrowserReload))
        refresh_button.setToolTip("Manually refresh the layout of the companies list below.")
        refresh_button.setFixedSize(20,20)
        
        year_entry_data = {
            "year_name": year_name_str, "companies_layout": QHBoxLayout(),
            "company_entries": [], "widget": eps_year_group_box,
            "selected_companies_to_display_for_year": selected_companies_for_this_year,
            "choose_companies_button": choose_companies_button
        }
        year_entry_data["companies_layout"].setContentsMargins(0,0,0,0)
        year_entry_data["companies_layout"].setSpacing(4)

        refresh_button.clicked.connect(lambda: self._update_eps_year_companies_area_size(year_entry_data))
        choose_companies_button.clicked.connect(lambda checked=False, y_data=year_entry_data: self._handle_choose_eps_companies_for_year(y_data))
        remove_year_button.clicked.connect(lambda: self.epsYearRemoveRequested.emit(year_entry_data["year_name"]))

        year_title_bar_layout.addWidget(choose_companies_button)
        year_title_bar_layout.addWidget(refresh_button)
        year_title_bar_layout.addWidget(remove_year_button)
        year_main_layout.addLayout(year_title_bar_layout)
        year_main_layout.addLayout(year_entry_data["companies_layout"])

        self.eps_items_layout.addWidget(eps_year_group_box)
        self.eps_year_entries.append(year_entry_data)

        companies_data_dict = {c.get("name"): c for c in companies_data_list}
        for fixed_name in self.fixed_companies_provider:
            xml_data = companies_data_dict.get(fixed_name, {})
            self._add_eps_company_to_year_ui(year_entry_data, fixed_name, xml_data.get("value", ""), xml_data.get("growth", ""))
        self._update_visible_eps_companies_for_year(year_entry_data)
        self._update_visible_eps_years()

    def _remove_dynamic_list_entry(self, entry_data_dict, entry_list):
        if entry_data_dict in entry_list:
            entry_list.remove(entry_data_dict)
        widget = entry_data_dict.get("widget")
        if widget: widget.deleteLater()

    def _handle_add_new_eps_year_dialog(self):
        name, ok = QInputDialog.getText(self, "New EPS Year", "Enter Year Name (e.g., 2024):")
        if ok and name: self.epsYearAddRequested.emit(name.strip())

    def _add_eps_company_to_year_ui(self, year_entry_data, company_name_str, company_value_str="", company_growth_str=""):
        company_gbox = HighlightableGroupBox(company_name=company_name_str, title=company_name_str)
        company_gbox.setFixedWidth(62)
        gbox_layout = QVBoxLayout(company_gbox)
        gbox_layout.setContentsMargins(5, 5, 5, 5)
        gbox_layout.setSpacing(2)
        
        form = QFormLayout()
        form.setContentsMargins(0,0,0,0)
        form.setSpacing(5)
        
        val_edit = FocusAwareLineEdit(company_name_str, company_value_str)
        val_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
        val_edit.focusGainedSignal.connect(self.companyLineEditFocusGained)
        val_edit.focusLostSignal.connect(self.companyLineEditFocusLost)
        
        growth_edit = FocusAwareLineEdit(company_name_str, company_growth_str)
        growth_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
        growth_edit.focusGainedSignal.connect(self.companyLineEditFocusGained)
        growth_edit.focusLostSignal.connect(self.companyLineEditFocusLost)
        
        form.addRow("Value:", val_edit)
        form.addRow("Growth:", growth_edit)
        gbox_layout.addLayout(form)

        company_data = {"name": company_name_str, "value_edit": val_edit, "growth_edit": growth_edit,
                        "widget": company_gbox, "current_value": company_value_str, "current_growth": company_growth_str}
        
        val_edit.editingFinished.connect(lambda le=val_edit, ed=company_data, yn=year_entry_data["year_name"], fn="value": self._handle_eps_value_changed(le, ed, yn, fn))
        val_edit.returnPressed.connect(lambda le=val_edit, ed=company_data, yn=year_entry_data["year_name"], fn="value": self._handle_eps_value_changed(le, ed, yn, fn))
        growth_edit.editingFinished.connect(lambda le=growth_edit, ed=company_data, yn=year_entry_data["year_name"], fn="growth": self._handle_eps_value_changed(le, ed, yn, fn))
        growth_edit.returnPressed.connect(lambda le=growth_edit, ed=company_data, yn=year_entry_data["year_name"], fn="growth": self._handle_eps_value_changed(le, ed, yn, fn))

        year_entry_data["companies_layout"].addWidget(company_gbox)
        year_entry_data["company_entries"].append(company_data)
        self._update_eps_year_companies_area_size(year_entry_data)

    def _handle_choose_eps_companies_for_year(self, year_entry_data):
        if not year_entry_data: return
        dialog = EPriceCompanySelectionDialog(self.fixed_companies_provider, year_entry_data["selected_companies_to_display_for_year"], self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_sel = dialog.get_selected_companies()
            old_sel = list(year_entry_data["selected_companies_to_display_for_year"])
            self.epsCompaniesForYearDisplayChangeRequested.emit(year_entry_data["year_name"], old_sel, new_sel)

    def _handle_eps_value_changed(self, line_edit, company_entry, year_name, field_name):
        new_val = line_edit.text().strip()
        old_val = company_entry.get("current_value" if field_name == "value" else "current_growth", "")
        if new_val != old_val:
            self.epsValueChanged.emit(year_name, company_entry["name"], field_name, old_val, new_val)

    def update_company_eps_field(self, year_name, company_name, field_name, value, from_command=False):
        for ye in self.eps_year_entries:
            if ye["year_name"] == year_name:
                for ce in ye["company_entries"]:
                    if ce["name"] == company_name:
                        target_edit, current_key = (ce["value_edit"], "current_value") if field_name == "value" else (ce["growth_edit"], "current_growth")
                        if target_edit:
                            target_edit.blockSignals(True)
                            target_edit.setText(value)
                            target_edit.blockSignals(False)
                            ce[current_key] = value
                        return

    def _update_visible_eps_companies_for_year(self, year_entry_data):
        if not year_entry_data or "company_entries" not in year_entry_data: return
        year_entry_data["choose_companies_button"].setEnabled(len(self.fixed_companies_provider) > 0)
        for ce in year_entry_data["company_entries"]:
            widget = ce.get("widget")
            if widget: widget.setVisible(ce["name"] in year_entry_data["selected_companies_to_display_for_year"])
        self._update_eps_year_companies_area_size(year_entry_data)

    def _update_eps_year_companies_area_size(self, year_entry_data):
        companies_layout = year_entry_data.get("companies_layout")
        if companies_layout: companies_layout.activate()
        year_gbox = year_entry_data.get("widget")
        if year_gbox:
            if year_gbox.layout(): year_gbox.layout().activate()
            year_gbox.adjustSize()
            year_gbox.updateGeometry()
        
    def _get_eps_year_sort_key(self, year_name_str):
        try: return (0, int(year_name_str))
        except ValueError: return (1, year_name_str)

    def _update_visible_eps_years(self):
        self.eps_year_entries.sort(key=lambda e: self._get_eps_year_sort_key(e.get("year_name", "")))
        while self.eps_items_layout.count():
            item = self.eps_items_layout.takeAt(0)
            if item.widget(): item.widget().setParent(None)
        for ye_data in self.eps_year_entries:
            widget = ye_data.get("widget")
            if widget: self.eps_items_layout.addWidget(widget)
        
        self.choose_year_button.setEnabled(len(self.eps_year_entries) > 0)
        target_visible = [n for n in self.selected_eps_years_to_display if any(e.get("year_name") == n for e in self.eps_year_entries)][:2]
        if len(target_visible) < 2:
            for ye_data in self.eps_year_entries:
                if len(target_visible) >= 2: break
                name = ye_data.get("year_name")
                if name and name not in target_visible: target_visible.append(name)
        
        for ye_data in self.eps_year_entries:
            widget, name = ye_data.get("widget"), ye_data.get("year_name")
            if widget and name: widget.setVisible(name in target_visible)

        if self.eps_group_box.layout():
            self.eps_group_box.layout().activate()
            self.eps_group_box.adjustSize()

    def update_company_highlight_state(self, company_name, highlight_state):
        for ye in self.eps_year_entries:
            if ye.get("widget") and ye["widget"].isVisible():
                for ce in ye.get("company_entries", []):
                    if ce.get("name") == company_name:
                        gbox = ce.get("widget")
                        if isinstance(gbox, HighlightableGroupBox): gbox.setHighlightedState(highlight_state)

    def _handle_choose_eps_year_dialog(self):
        if not self.eps_year_entries:
            QMessageBox.information(self, "No EPS Years", "There are no EPS years to choose from.")
            return
        all_names = sorted([e.get("year_name") for e in self.eps_year_entries if e.get("year_name")], key=self._get_eps_year_sort_key)
        dialog = EPSYearSelectionDialog(all_names, self.selected_eps_years_to_display, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_sel = dialog.get_selected_years()
            old_sel = list(self.selected_eps_years_to_display)
            self.epsYearDisplayChangeRequested.emit(old_sel, new_sel)

    def setEnabled(self, enabled):
        self.eps_group_box.setEnabled(enabled)
        super().setEnabled(enabled)
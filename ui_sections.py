# t:\Work\xml_input_ui\ui_sections.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QGroupBox, QPushButton,
    QFormLayout, QLineEdit, QLabel, QInputDialog, QMessageBox, QStyle, QApplication, QComboBox,
    QDialog, QDateEdit
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from dialogs import EPSYearSelectionDialog, EPriceCompanySelectionDialog # Reusing for EPS companies
from custom_widgets import FocusAwareLineEdit, HighlightableGroupBox # Import custom widgets
import data_utils # For default date

# Helper function to clear widgets from a layout
def _clear_qt_layout(layout):
    """Recursively clears all widgets and sub-layouts from a given layout."""
    if layout is not None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            else:
                sub_layout = item.layout()
                if sub_layout is not None:
                    _clear_qt_layout(sub_layout) # Recursive call


class EPSSectionWidget(QWidget):
    # Signals to be connected by the main editor for global highlight sync
    # Defined as class attributes for clarity and standard practice
    companyLineEditFocusGained = pyqtSignal(str, QLineEdit) # company_name, QLineEdit instance
    companyLineEditFocusLost = pyqtSignal(str, QLineEdit)   # company_name, QLineEdit instance
    epsYearAddRequested = pyqtSignal(str) # year_name
    epsYearRemoveRequested = pyqtSignal(str) # year_name
    epsYearDisplayChangeRequested = pyqtSignal(list, list) # old_selected_years, new_selected_years
    epsCompaniesForYearDisplayChangeRequested = pyqtSignal(str, list, list) # year_name, old_list, new_list
    epsValueChanged = pyqtSignal(str, str, str, str, str) # year_name, company_name, field_name, old_value, new_value

    def __init__(self, fixed_companies_provider, parent=None):
        super().__init__(parent)
        self.eps_year_entries = [] # Stores data for each EPS year group
        self.selected_eps_years_to_display = [] # Stores names of EPS years to show
        self.fixed_companies_provider = fixed_companies_provider # Reference to the main list
        self._init_ui()


    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0,0,0,0) # No margins for the widget itself

        self.eps_group_box = QGroupBox("EPS Years") # The main container
        eps_main_layout = QVBoxLayout(self.eps_group_box)
        eps_main_layout.setContentsMargins(2, 5, 5, 5)
        eps_main_layout.setSpacing(3)

        # --- Top Actions for EPS Section (Choose Year, Add Year) ---
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
        
        # --- Layout for individual EPS Year items ---
        self.eps_items_layout = QVBoxLayout() 
        eps_main_layout.addLayout(self.eps_items_layout)

        main_layout.addWidget(self.eps_group_box)
        self.setLayout(main_layout)
        self._update_visible_eps_years() # Initial state for choose button

    def load_data(self, eps_data_list):
        self.clear_data() # Clear previous data and UI
        if eps_data_list is None:
            eps_data_list = []
        for year_data in eps_data_list:
            self._add_eps_year_fields(
                year_name_str=year_data.get("name", ""),
                companies_data_list=year_data.get("companies", [])
            )
        self._update_visible_eps_years()

    def get_data(self):
        return [
            {
                "name": year_entry.get("year_name",""),
                "companies": [
                    {"name": comp_entry.get("name",""), 
                     "value": comp_entry["value_edit"].text(),
                     "growth": comp_entry["growth_edit"].text()}
                    for comp_entry in year_entry["company_entries"]
                ]
            } for year_entry in self.eps_year_entries
        ]

    def clear_data(self):
        _clear_qt_layout(self.eps_items_layout)
        self.eps_year_entries.clear()
        self.selected_eps_years_to_display.clear()
        self._update_visible_eps_years()

    def refresh_structure_with_new_fixed_companies(self, new_fixed_companies_list):
        """
        Rebuilds the internal structure of all EPS years to match the
        current self.fixed_companies_provider list.
        Preserves existing data.
        """
        self.fixed_companies_provider = new_fixed_companies_list # Update internal reference

        # Store current per-year company selections
        stored_per_year_selections = {
            entry["year_name"]: list(entry["selected_companies_to_display_for_year"])
            for entry in self.eps_year_entries
        }

        current_eps_data = self.get_data() # Get data in the format suitable for load_data

        # Clear existing UI elements and internal state related to year entries
        _clear_qt_layout(self.eps_items_layout)
        self.eps_year_entries.clear()

        # Reload the data. load_data will use the new fixed_companies_provider
        # to structure the company boxes within each year.
        # _add_eps_year_fields (called by load_data) will initialize
        # selected_companies_to_display_for_year to the new full fixed_companies_provider list.
        self.load_data(current_eps_data)

        # Restore and filter per-year selections
        for year_entry in self.eps_year_entries:
            year_name = year_entry["year_name"]
            if year_name in stored_per_year_selections:
                original_selection = stored_per_year_selections[year_name]
                year_entry["selected_companies_to_display_for_year"] = [
                    comp for comp in original_selection if comp in self.fixed_companies_provider
                ]
            self._update_visible_eps_companies_for_year(year_entry) # Update UI for this year

    def _add_eps_year_fields(self, year_name_str="", companies_data_list=None):
        if not year_name_str: 
            QMessageBox.warning(self, "Input Error", "Year name is required for EPS entry.")
            return
        if companies_data_list is None: companies_data_list = []

        # Initialize selected companies for this year to all fixed companies
        # This list will be modified by the year-specific "Choose Companies" button
        selected_companies_for_this_year = list(self.fixed_companies_provider)


        eps_year_group_box = QGroupBox(f"EPS {year_name_str}") 
        year_main_layout = QVBoxLayout(eps_year_group_box) 
        year_main_layout.setContentsMargins(2, 2, 2, 2) 
        year_main_layout.setSpacing(3)

        year_title_bar_layout = QHBoxLayout()
        year_title_bar_layout.addStretch()
        remove_year_button = QPushButton()
        remove_year_button.setToolTip("Delete this EPS Year")
        remove_year_button.setIcon(QApplication.style().standardIcon(QStyle.StandardPixmap.SP_DialogCancelButton))
        remove_year_button.setFixedSize(20, 20) 

        choose_companies_for_year_button = QPushButton("Choose Companies")
        choose_companies_for_year_button.setToolTip(f"Select which companies to display for EPS {year_name_str}")
        choose_companies_for_year_button.setFixedHeight(20)
        # choose_companies_for_year_button.setFixedWidth(120) # Optional: if you want fixed width

                
        refresh_companies_button = QPushButton()
        refresh_companies_button.setIcon(QApplication.style().standardIcon(QStyle.StandardPixmap.SP_BrowserReload))
        refresh_companies_button.setToolTip("Manually refresh the layout of the companies list below.")
        refresh_companies_button.setFixedSize(20,20) 
        
        year_entry_data = {
            "year_name": year_name_str, "companies_layout": None, 
            "company_entries": [], "widget": eps_year_group_box,
            "selected_companies_to_display_for_year": selected_companies_for_this_year,
            "choose_companies_button": choose_companies_for_year_button
        }
        refresh_companies_button.clicked.connect(lambda: self._update_eps_year_companies_area_size(year_entry_data))
        choose_companies_for_year_button.clicked.connect(lambda checked=False, y_data=year_entry_data: self._handle_choose_eps_companies_for_year(y_data))

        year_title_bar_layout.addWidget(choose_companies_for_year_button)
        year_title_bar_layout.addWidget(refresh_companies_button)
        year_title_bar_layout.addWidget(remove_year_button)
        year_main_layout.addLayout(year_title_bar_layout)
        
        # Create the QHBoxLayout for companies directly
        companies_layout = QHBoxLayout() 
        companies_layout.setContentsMargins(0,0,0,0)
        companies_layout.setSpacing(4) # Set gap between company boxes to 4px

        year_entry_data["companies_layout"] = companies_layout

        remove_year_button.clicked.connect(
            lambda: self.epsYearRemoveRequested.emit(year_entry_data["year_name"])
        )

        year_main_layout.addLayout(companies_layout) # Add the companies layout directly

        self.eps_items_layout.addWidget(eps_year_group_box)
        self.eps_year_entries.append(year_entry_data)

        # Populate with fixed companies
        # companies_data_list is the data loaded from XML for this specific year.
        # Convert it to a dictionary for easier lookup
        companies_data_dict = {comp.get("name"): comp for comp in (companies_data_list or [])}

        for fixed_company_name in self.fixed_companies_provider:
            company_xml_data = companies_data_dict.get(fixed_company_name, {}) # Get data if exists
            self._add_eps_company_to_year_ui(
                year_entry_data,
                company_name_str=fixed_company_name,
                company_value_str=company_xml_data.get("value", ""),
                company_growth_str=company_xml_data.get("growth", "")
            )
        self._update_visible_eps_companies_for_year(year_entry_data) # Apply initial visibility
        self._update_visible_eps_years()


    def _remove_dynamic_list_entry(self, entry_data_dict, entry_list):
        if entry_data_dict in entry_list:
            entry_list.remove(entry_data_dict)
        widget_to_remove = entry_data_dict.get("widget")
        if widget_to_remove:
            widget_to_remove.deleteLater()

    def _handle_add_new_eps_year_dialog(self):
        year_name, ok = QInputDialog.getText(self, "New EPS Year", "Enter Year Name (e.g., 2024):")
        if ok and year_name:
            self.epsYearAddRequested.emit(year_name.strip())

    def _add_eps_company_to_year_ui(self, year_entry_data, company_name_str, company_value_str="", company_growth_str=""):
        # company_name_str is now guaranteed by fixed_companies_provider
        company_group_box = HighlightableGroupBox(company_name=company_name_str, title=company_name_str) # Use custom GroupBox
        company_group_box.setFixedWidth(62) # Set company box width to 62px

        gbox_main_layout = QVBoxLayout(company_group_box) 
        gbox_main_layout.setContentsMargins(5, 5, 5, 5) # Increased internal padding
        gbox_main_layout.setSpacing(2) 

        top_bar_layout = QHBoxLayout()
        top_bar_layout.setContentsMargins(0,0,0,0) 
        top_bar_layout.setSpacing(0)
        top_bar_layout.addStretch() 
        # Removed: remove_company_button from top_bar_layout
        gbox_main_layout.addLayout(top_bar_layout)

        form_layout = QFormLayout() 
        form_layout.setContentsMargins(0,0,0,0) 
        form_layout.setSpacing(5)
        
        # Use custom LineEdit, passing the parent GroupBox
        company_value_edit = FocusAwareLineEdit(company_name=company_name_str, text=company_value_str)
        company_value_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
        company_value_edit.focusGainedSignal.connect(self.companyLineEditFocusGained)
        company_value_edit.focusLostSignal.connect(self.companyLineEditFocusLost)
        
        
        company_growth_edit = FocusAwareLineEdit(company_name=company_name_str, text=company_growth_str)
        company_growth_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
        company_growth_edit.focusGainedSignal.connect(self.companyLineEditFocusGained)
        company_growth_edit.focusLostSignal.connect(self.companyLineEditFocusLost)
        form_layout.addRow("Value:", company_value_edit)
        form_layout.addRow("Growth:", company_growth_edit)

        company_data = {
            "name": company_name_str,  
            "value_edit": company_value_edit,
            "growth_edit": company_growth_edit, "widget": company_group_box,
            "current_value": company_value_str, # Track current value for "value" field
            "current_growth": company_growth_str # Track current value for "growth" field
        }
        
        # Connect editingFinished for value and growth
        company_value_edit.editingFinished.connect(
            lambda le=company_value_edit, ed=company_data, y_name=year_entry_data["year_name"], f_name="value":
            self._handle_eps_value_changed(le, ed, y_name, f_name)
        )
        company_value_edit.returnPressed.connect(
             lambda le=company_value_edit, ed=company_data, y_name=year_entry_data["year_name"], f_name="value":
            self._handle_eps_value_changed(le, ed, y_name, f_name)
        )
        company_growth_edit.editingFinished.connect(
            lambda le=company_growth_edit, ed=company_data, y_name=year_entry_data["year_name"], f_name="growth":
            self._handle_eps_value_changed(le, ed, y_name, f_name)
        )
        company_growth_edit.returnPressed.connect(
            lambda le=company_growth_edit, ed=company_data, y_name=year_entry_data["year_name"], f_name="growth":
            self._handle_eps_value_changed(le, ed, y_name, f_name)
        )
        gbox_main_layout.addLayout(form_layout)

        # Removed: connect for remove_company_button
        year_entry_data["companies_layout"].addWidget(company_group_box)
        year_entry_data["company_entries"].append(company_data)
        self._update_eps_year_companies_area_size(year_entry_data)

    def _handle_choose_eps_companies_for_year(self, year_entry_data):
        if not year_entry_data: return

        dialog = EPriceCompanySelectionDialog(
            self.fixed_companies_provider, # All available fixed companies
            year_entry_data["selected_companies_to_display_for_year"], # Currently selected for this year
            self
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_selection = dialog.get_selected_companies()
            old_selection = list(year_entry_data["selected_companies_to_display_for_year"]) # Make a copy
            self.epsCompaniesForYearDisplayChangeRequested.emit(year_entry_data["year_name"], old_selection, new_selection)

    def _handle_eps_value_changed(self, line_edit_widget, company_entry_data, year_name, field_name):
        new_value = line_edit_widget.text().strip()
        old_value = ""
        if field_name == "value":
            old_value = company_entry_data.get("current_value", "")
        elif field_name == "growth":
            old_value = company_entry_data.get("current_growth", "")

        if new_value != old_value:
            self.epsValueChanged.emit(year_name, company_entry_data["name"], field_name, old_value, new_value)
            # The command will update current_value/current_growth via update_company_eps_field

    def update_company_eps_field(self, year_name, company_name, field_name, value, from_command=False):
        """Updates a specific EPS field (value or growth) for a company in a year and its internal tracker."""
        for year_entry in self.eps_year_entries:
            if year_entry["year_name"] == year_name:
                for company_entry in year_entry["company_entries"]:
                    if company_entry["name"] == company_name:
                        target_line_edit = None
                        current_value_key = None
                        if field_name == "value":
                            target_line_edit = company_entry["value_edit"]
                            current_value_key = "current_value"
                        elif field_name == "growth":
                            target_line_edit = company_entry["growth_edit"]
                            current_value_key = "current_growth"
                        
                        if target_line_edit and current_value_key:
                            target_line_edit.blockSignals(True)
                            target_line_edit.setText(value)
                            target_line_edit.blockSignals(False)
                            company_entry[current_value_key] = value
                        return # Found and updated

    def _update_visible_eps_companies_for_year(self, year_entry_data):
        if not year_entry_data or "company_entries" not in year_entry_data:
            return
        
        year_entry_data["choose_companies_button"].setEnabled(len(self.fixed_companies_provider) > 0)

        for company_entry in year_entry_data["company_entries"]:
            widget = company_entry.get("widget")
            if widget:
                widget.setVisible(company_entry["name"] in year_entry_data["selected_companies_to_display_for_year"])
        self._update_eps_year_companies_area_size(year_entry_data) # Refresh scroll area size

    def _update_eps_year_companies_area_size(self, year_entry_data):
        # This method now primarily ensures the year group box adjusts its size
        # after company visibility changes or if companies are added/removed.
        
        companies_layout = year_entry_data.get("companies_layout")
        if companies_layout:
            companies_layout.activate() # Ensure layout calculations are up-to-date

        year_gbox_widget = year_entry_data.get("widget")
        if year_gbox_widget:
            if year_gbox_widget.layout():
                year_gbox_widget.layout().activate()
            year_gbox_widget.adjustSize() # Adjust to content
            year_gbox_widget.updateGeometry()
        
    def _get_eps_year_sort_key(self, year_name_str):
        try: return (0, int(year_name_str)) 
        except ValueError: return (1, year_name_str)      

    def _update_visible_eps_years(self):
        self.eps_year_entries.sort(key=lambda entry: self._get_eps_year_sort_key(entry.get("year_name", "")))
        
        while self.eps_items_layout.count():
            item = self.eps_items_layout.takeAt(0)
            if item.widget(): item.widget().setParent(None) 
        
        for year_entry_data in self.eps_year_entries: 
            widget = year_entry_data.get("widget") 
            if widget: self.eps_items_layout.addWidget(widget)
        
        num_years = len(self.eps_year_entries)
        self.choose_year_button.setEnabled(num_years > 0)

        target_visible_names = []
        if self.selected_eps_years_to_display:
            valid_selected_names = [
                name for name in self.selected_eps_years_to_display 
                if any(entry.get("year_name") == name for entry in self.eps_year_entries)
            ]
            target_visible_names = valid_selected_names[:2]
        
        if len(target_visible_names) < 2: 
            for year_entry_data in self.eps_year_entries:
                if len(target_visible_names) >= 2: break
                year_name = year_entry_data.get("year_name")
                if year_name and year_name not in target_visible_names: 
                    target_visible_names.append(year_name)
        
        for year_entry_data in self.eps_year_entries: 
            widget = year_entry_data.get("widget")
            year_name = year_entry_data.get("year_name")
            if widget and year_name:
                widget.setVisible(year_name in target_visible_names)

        if self.eps_group_box.layout():
            self.eps_group_box.layout().activate() 
            self.eps_group_box.adjustSize()       

    def update_company_highlight_state(self, company_name_to_update, highlight_state):
        """Called by the main editor to update highlight state of company boxes."""
        for year_entry in self.eps_year_entries:
            if year_entry.get("widget") and year_entry["widget"].isVisible(): # Only update visible years
                for company_entry in year_entry.get("company_entries", []):
                    if company_entry.get("name") == company_name_to_update:
                        group_box_widget = company_entry.get("widget")
                        if isinstance(group_box_widget, HighlightableGroupBox):
                            group_box_widget.setHighlightedState(highlight_state)

    def _handle_choose_eps_year_dialog(self):
        if not self.eps_year_entries:
            QMessageBox.information(self, "No EPS Years", "There are no EPS years to choose from.")
            return

        all_year_names = [entry.get("year_name") for entry in self.eps_year_entries if entry.get("year_name")]
        all_year_names.sort(key=self._get_eps_year_sort_key)
        
        dialog = EPSYearSelectionDialog(all_year_names, self.selected_eps_years_to_display, self)
        
        if dialog.exec() == QDialog.DialogCode.Accepted: 
            new_selection = dialog.get_selected_years()
            old_selection = list(self.selected_eps_years_to_display) # Make a copy
            self.epsYearDisplayChangeRequested.emit(old_selection, new_selection)

    def setEnabled(self, enabled):
        """Override setEnabled to control the group box."""
        self.eps_group_box.setEnabled(enabled)
        super().setEnabled(enabled)

class QuoteSelectionWidget(QWidget):
    selectQuoteClicked = pyqtSignal(str)
    addQuoteClicked = pyqtSignal(str)
    removeQuoteClicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)

        quote_selection_group = QGroupBox("Select or Add Quote")
        quote_selection_layout = QVBoxLayout(quote_selection_group)
        quote_selection_layout.setContentsMargins(5, 5, 5, 5)
        quote_selection_layout.setSpacing(3)

        search_and_actions_layout = QHBoxLayout()
        self.quote_search_edit = QLineEdit()
        self.quote_search_edit.setPlaceholderText("Enter Quote Name to Select/Add")
        search_and_actions_layout.addWidget(self.quote_search_edit, 1)

        self.select_quote_button = QPushButton()
        self.select_quote_button.setIcon(QApplication.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogContentsView))
        self.select_quote_button.setToolTip("Select/View Quote (using name in text box)")
        self.select_quote_button.setFixedSize(20,20)
        self.select_quote_button.clicked.connect(self._on_select_clicked)
        search_and_actions_layout.addWidget(self.select_quote_button)

        self.remove_quote_button = QPushButton()
        self.remove_quote_button.setToolTip("Remove Displayed Quote")
        self.remove_quote_button.setIcon(QApplication.style().standardIcon(QStyle.StandardPixmap.SP_DialogCancelButton))
        self.remove_quote_button.setFixedSize(20, 20)
        self.remove_quote_button.clicked.connect(self.removeQuoteClicked) # Direct signal emission
        search_and_actions_layout.addWidget(self.remove_quote_button)

        self.add_quote_button = QPushButton()
        self.add_quote_button.setToolTip("Add New Quote (using name in text box above)")
        self.add_quote_button.setIcon(QApplication.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogNewFolder))
        self.add_quote_button.setFixedSize(20,20)
        self.add_quote_button.clicked.connect(self._on_add_clicked)
        search_and_actions_layout.addWidget(self.add_quote_button)

        search_and_actions_layout.addStretch(0)
        quote_selection_layout.addLayout(search_and_actions_layout)
        layout.addWidget(quote_selection_group)

    def _on_select_clicked(self):
        self.selectQuoteClicked.emit(self.quote_search_edit.text().strip())

    def _on_add_clicked(self):
        self.addQuoteClicked.emit(self.quote_search_edit.text().strip())

    def get_quote_name_input(self):
        return self.quote_search_edit.text().strip()

    def set_quote_name_input(self, name):
        self.quote_search_edit.setText(name)

    def clear_input(self):
        self.quote_search_edit.clear()

    def setEnabled(self, enabled):
        # The group box itself doesn't need to be disabled, just its interactive children
        self.quote_search_edit.setEnabled(enabled)
        self.select_quote_button.setEnabled(enabled)
        self.add_quote_button.setEnabled(enabled)
        self.remove_quote_button.setEnabled(enabled) # This should be enabled based on whether a quote is selected
        super().setEnabled(enabled)

class QuoteDetailsWidget(QWidget):
    # Signals to inform the main editor about confirmed changes
    quoteNameChanged = pyqtSignal(str, str)  # old_name, new_name
    quotePriceChanged = pyqtSignal(str, str) # old_price, new_price

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_name = ""
        self._current_price = ""
        self._init_ui()

    def _init_ui(self):
        self.details_group = QGroupBox("Quote Details")
        self.details_group.setEnabled(False) # Initially disabled
        details_form_layout = QFormLayout(self.details_group)
        self.name_edit = QLineEdit()
        self.price_edit = QLineEdit()
        details_form_layout.addRow(QLabel("Quote Name:"), self.name_edit)
        details_form_layout.addRow(QLabel("Quote Price:"), self.price_edit)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0,0,0,0)
        main_layout.addWidget(self.details_group)

        # Connect editingFinished signals
        self.name_edit.editingFinished.connect(self._handle_name_editing_finished)
        self.name_edit.returnPressed.connect(self._handle_name_editing_finished) # Explicitly handle Enter
        self.price_edit.editingFinished.connect(self._handle_price_editing_finished)
        self.price_edit.returnPressed.connect(self._handle_price_editing_finished) # Explicitly handle Enter

    def _handle_name_editing_finished(self):
        new_name = self.name_edit.text().strip()
        if not self.name_edit.isReadOnly() and new_name != self._current_name:
            self.quoteNameChanged.emit(self._current_name, new_name)
            # self._current_name will be updated by the command execution via update_field_value

    def _handle_price_editing_finished(self):
        new_price = self.price_edit.text().strip()
        if not self.price_edit.isReadOnly() and new_price != self._current_price:
            self.quotePriceChanged.emit(self._current_price, new_price)
            # self._current_price will be updated by the command execution via update_field_value

    def load_data(self, name, price, is_new_quote):
        self.name_edit.setText(name)
        self.price_edit.setText(price)
        self._current_name = name
        self._current_price = price

        self.name_edit.setReadOnly(not is_new_quote)
        self.price_edit.setReadOnly(False) # Price is always editable when a quote is displayed
        self.details_group.setEnabled(True)

    def get_data(self):
        return self.name_edit.text(), self.price_edit.text()

    def clear_data(self):
        self.name_edit.blockSignals(True)
        self.price_edit.blockSignals(True)
        self.name_edit.clear()
        self.price_edit.clear()
        self.name_edit.blockSignals(False)
        self.price_edit.blockSignals(False)
        self._current_name = ""
        self._current_price = ""
        self.details_group.setEnabled(False)

    def update_field_value(self, field_name, value, from_command=False):
        """
        Updates a field's value and its internal tracker.
        Called by commands during execute/unexecute.
        """
        if field_name == "name":
            self.name_edit.blockSignals(True)
            self.name_edit.setText(value)
            self.name_edit.blockSignals(False)
            self._current_name = value
        elif field_name == "price":
            self.price_edit.blockSignals(True)
            self.price_edit.setText(value)
            self.price_edit.blockSignals(False)
            self._current_price = value

    def setEnabled(self, enabled):
        self.details_group.setEnabled(enabled)
        # The QLineEdit read-only state is managed by load_data
        super().setEnabled(enabled)


class EPriceSectionWidget(QWidget):
    companyFocusGained = pyqtSignal(str, QLineEdit)
    companyFocusLost = pyqtSignal(str, QLineEdit)
    ePriceValueChanged = pyqtSignal(str, str, str) # company_name, old_value, new_value

    def __init__(self, fixed_companies_provider_func, parent=None):
        super().__init__(parent)
        self.fixed_companies_provider_func = fixed_companies_provider_func # Function to get current fixed companies
        self.eprice_entries = []
        self.selected_eprice_companies_to_display = []
        self._init_ui()

    def _init_ui(self):
        self.eprice_group = QGroupBox("E-Price Companies")
        eprice_main_layout = QVBoxLayout(self.eprice_group)
        eprice_main_layout.setContentsMargins(2, 5, 5, 5)
        eprice_main_layout.setSpacing(3)

        eprice_actions_layout = QHBoxLayout()
        eprice_actions_layout.addStretch()
        self.choose_companies_button = QPushButton("Choose Companies")
        self.choose_companies_button.setToolTip("Select which E-Price companies to display")
        self.choose_companies_button.setFixedSize(120, 20)
        self.choose_companies_button.clicked.connect(self._handle_choose_eprice_companies)
        eprice_actions_layout.addWidget(self.choose_companies_button)
        eprice_main_layout.addLayout(eprice_actions_layout)

        self.eprice_items_layout = QHBoxLayout()
        self.eprice_items_layout.setSpacing(4)
        eprice_main_layout.addLayout(self.eprice_items_layout)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0,0,0,0)
        main_layout.addWidget(self.eprice_group)
        self.refresh_structure() # Initial build


    def _create_company_ui(self, company_name_str, value_str=""):
        company_group_box = HighlightableGroupBox(company_name=company_name_str, title=company_name_str)
        company_group_box.setFixedWidth(62)
        gbox_main_layout = QVBoxLayout(company_group_box)
        gbox_main_layout.setContentsMargins(5, 5, 5, 5)
        gbox_main_layout.setSpacing(2)
        form_layout = QFormLayout()
        form_layout.setContentsMargins(0,0,0,0)
        value_edit = FocusAwareLineEdit(company_name=company_name_str, text=value_str)
        value_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        entry_data = {
            "name": company_name_str, 
            "value_edit": value_edit, 
            "widget": company_group_box,
            "current_value": value_str # Initialize current_value
        }

        value_edit.focusGainedSignal.connect(self.companyFocusGained)
        value_edit.focusLostSignal.connect(self.companyFocusLost)
        # Connect editingFinished to handle value changes
        value_edit.editingFinished.connect(lambda le=value_edit, ed=entry_data: self._handle_eprice_value_changed(le, ed))
        value_edit.returnPressed.connect(lambda le=value_edit, ed=entry_data: self._handle_eprice_value_changed(le, ed))
        form_layout.addRow(value_edit)
        gbox_main_layout.addLayout(form_layout)
        self.eprice_items_layout.addWidget(company_group_box)
        self.eprice_entries.append(entry_data)

    def refresh_structure(self, new_fixed_companies=None):
        fixed_companies = new_fixed_companies if new_fixed_companies is not None else self.fixed_companies_provider_func()
        
        current_values = {entry["name"]: entry["value_edit"].text() for entry in self.eprice_entries}
        _clear_qt_layout(self.eprice_items_layout)
        self.eprice_entries.clear()

        self.selected_eprice_companies_to_display = list(fixed_companies) # Default to all

        for company_name in fixed_companies:
            self._create_company_ui(company_name, current_values.get(company_name, ""))
        self._update_visible_companies()

    def _handle_eprice_value_changed(self, line_edit_widget, entry_data):
        new_value = line_edit_widget.text().strip()
        old_value = entry_data.get("current_value", "")
        if new_value != old_value:
            self.ePriceValueChanged.emit(entry_data["name"], old_value, new_value)
            # entry_data["current_value"] will be updated by the command via update_company_value

    def load_data(self, eprice_data_list_for_quote):
        loaded_data_map = {item["name"]: item["value"] for item in eprice_data_list_for_quote}
        for entry in self.eprice_entries:
            entry["value_edit"].setText(loaded_data_map.get(entry["name"], ""))
            entry["current_value"] = loaded_data_map.get(entry["name"], "") # Update internal tracker

    def get_data(self):
        data = []
        for entry in self.eprice_entries:
            value = entry["value_edit"].text().strip()
            if value: # Only save if there's a value
                data.append({"name": entry["name"], "value": value})
        return data

    def clear_data(self):
        for entry in self.eprice_entries:
            entry["value_edit"].clear()
            entry["current_value"] = "" # Clear internal tracker

    def update_company_value(self, company_name, value, from_command=False):
        """Updates a company's E-Price value and its internal tracker."""
        for entry_data in self.eprice_entries:
            if entry_data["name"] == company_name:
                value_edit_widget = entry_data["value_edit"]
                value_edit_widget.blockSignals(True)
                value_edit_widget.setText(value)
                value_edit_widget.blockSignals(False)
                entry_data["current_value"] = value
                break



    def _handle_choose_eprice_companies(self):
        fixed_companies = self.fixed_companies_provider_func()
        dialog = EPriceCompanySelectionDialog(fixed_companies, self.selected_eprice_companies_to_display, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.selected_eprice_companies_to_display = dialog.get_selected_companies()
            self._update_visible_companies()

    def _update_visible_companies(self):
        fixed_companies = self.fixed_companies_provider_func()
        self.choose_companies_button.setEnabled(len(fixed_companies) > 0)
        for entry in self.eprice_entries:
            widget = entry.get("widget")
            if widget:
                widget.setVisible(entry["name"] in self.selected_eprice_companies_to_display)

    def update_company_highlight_state(self, company_name, highlight_state):
        for entry in self.eprice_entries:
            if entry.get("name") == company_name:
                group_box_widget = entry.get("widget")
                if isinstance(group_box_widget, HighlightableGroupBox):
                    group_box_widget.setHighlightedState(highlight_state)

    def setEnabled(self, enabled):
        self.eprice_group.setEnabled(enabled)
        super().setEnabled(enabled)

# PESectionWidget would be very similar to EPriceSectionWidget.
# For brevity in this response, I'll assume it's structured almost identically,
# just with "PE" instead of "E-Price" in titles and variable names.
# You would create PESectionWidget by copying and adapting EPriceSectionWidget.

class PESectionWidget(EPriceSectionWidget): # Inherit and override if needed
    # PESectionWidget does not need to re-declare companyFocusGained/Lost as they are inherited.
    # Define a distinct signal for PE value changes
    peValueChanged = pyqtSignal(str, str, str) # company_name, old_value, new_value
    
    def __init__(self, fixed_companies_provider_func, parent=None):
        # Call the base class (EPriceSectionWidget) __init__
        super().__init__(fixed_companies_provider_func, parent)
        # The following lines were in the original __init__ of EPriceSectionWidget,
        # so they are effectively called by super().
        # self.fixed_companies_provider_func = fixed_companies_provider_func
        # self.eprice_entries = []
        # self.selected_eprice_companies_to_display = []
        self.eprice_group.setTitle("PE Companies") # Override title from base
        self.choose_companies_button.setToolTip("Select which PE companies to display") # Override tooltip

    def _create_company_ui(self, company_name_str, value_str=""):
        # This method is overridden from EPriceSectionWidget to connect
        # the value_edit signals to _handle_pe_value_changed instead of _handle_eprice_value_changed.
        company_group_box = HighlightableGroupBox(company_name=company_name_str, title=company_name_str)
        company_group_box.setFixedWidth(62)
        gbox_main_layout = QVBoxLayout(company_group_box)
        gbox_main_layout.setContentsMargins(5, 5, 5, 5)
        gbox_main_layout.setSpacing(2)
        form_layout = QFormLayout()
        form_layout.setContentsMargins(0,0,0,0)
        value_edit = FocusAwareLineEdit(company_name=company_name_str, text=value_str)
        value_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        entry_data = {
            "name": company_name_str, 
            "value_edit": value_edit, 
            "widget": company_group_box,
            "current_value": value_str 
        }

        value_edit.focusGainedSignal.connect(self.companyFocusGained) # Inherited signal
        value_edit.focusLostSignal.connect(self.companyFocusLost)   # Inherited signal
        # Connect editingFinished to handle PE value changes specifically
        value_edit.editingFinished.connect(lambda le=value_edit, ed=entry_data: self._handle_pe_value_changed(le, ed))
        value_edit.returnPressed.connect(lambda le=value_edit, ed=entry_data: self._handle_pe_value_changed(le, ed))
        form_layout.addRow(value_edit)
        gbox_main_layout.addLayout(form_layout)
        self.eprice_items_layout.addWidget(company_group_box) # eprice_items_layout is from base
        self.eprice_entries.append(entry_data) # eprice_entries is from base

    def _handle_pe_value_changed(self, line_edit_widget, entry_data):
        new_value = line_edit_widget.text().strip()
        old_value = entry_data.get("current_value", "")
        if new_value != old_value:
            self.peValueChanged.emit(entry_data["name"], old_value, new_value)
            # current_value will be updated by the command via update_company_value (inherited)
class RecordReportSectionWidget(QWidget):
    MAX_REPORTS_DISPLAYED = 5 # Class constant for this section
    recordReportAddRequested = pyqtSignal()
    recordReportRemoveRequested = pyqtSignal(object) # Passes the entry_data dict of the UI element
    recordReportDetailChanged = pyqtSignal(object, str, str, str) # entry_data_dict, field_name, old_value, new_value

    def __init__(self, fixed_companies_provider_func, parent=None):
        super().__init__(parent) # Call QWidget's __init__
        self.fixed_companies_provider_func = fixed_companies_provider_func
        self.report_entries = [] # List of dicts: {"widget": QGroupBox, "company_combo": QComboBox, "date_edit": QDateEdit, "color": str}
        self._init_ui()

    def _init_ui(self):
        self.record_group = QGroupBox("Record Reports")
        record_main_layout = QVBoxLayout(self.record_group)
        record_main_layout.setContentsMargins(2, 5, 5, 5)
        record_main_layout.setSpacing(3)

        record_actions_layout = QHBoxLayout()
        record_actions_layout.addStretch()
        add_report_button = QPushButton()
        add_report_button.setToolTip("Add Report")
        add_report_button.setIcon(QApplication.style().standardIcon(QStyle.StandardPixmap.SP_DialogApplyButton))
        add_report_button.setFixedSize(20, 20)
        add_report_button.clicked.connect(self.recordReportAddRequested)
        record_actions_layout.addWidget(add_report_button)
        record_main_layout.addLayout(record_actions_layout)

        self.record_items_layout = QVBoxLayout() # Where individual report boxes go
        record_main_layout.addLayout(self.record_items_layout)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0,0,0,0)
        main_layout.addWidget(self.record_group)

    def add_report_entry(self, company_str="", date_str="", color_str="", insert_at_index=0):
        report_entry_group = QGroupBox()
        report_entry_group.setObjectName("recordReportEntryBox") # For styling
        
        report_entry_main_layout = QVBoxLayout(report_entry_group)
        report_entry_main_layout.setContentsMargins(4, 8, 4, 4)
        report_entry_main_layout.setSpacing(3)

        # Store current values for change detection
        top_bar_layout = QHBoxLayout()
        top_bar_layout.addStretch()

        current_entry_data = {"widget": report_entry_group, 
                              "current_color": color_str if color_str else "default",
                              "current_company": company_str, "current_date": date_str}

        colors_to_add = [("R", "red"), ("G", "green"), ("Y", "yellow"), ("W", "white")]
        for btn_text, color_name in colors_to_add:
            color_button = QPushButton(btn_text)
            color_button.setFixedSize(16, 16)
            color_button.setToolTip(f"Set color to {color_name}")
            color_button.clicked.connect(lambda checked=False, ed=current_entry_data, cn=color_name: self._handle_report_color_change(ed, cn))
            top_bar_layout.addWidget(color_button)
        
        top_bar_layout.addSpacing(5)
        remove_report_button = QPushButton()
        remove_report_button.setToolTip("Remove this report entry")
        remove_report_button.setIcon(QApplication.style().standardIcon(QStyle.StandardPixmap.SP_DialogCancelButton))
        remove_report_button.setFixedSize(16, 16)
        top_bar_layout.addWidget(remove_report_button)
        report_entry_main_layout.addLayout(top_bar_layout)

        form_layout = QFormLayout()
        form_layout.setContentsMargins(0,0,0,0)
        company_combo = QComboBox()
        fixed_companies = self.fixed_companies_provider_func()
        company_combo.addItems(fixed_companies)
        initial_company_for_combo = company_str
        if company_str and company_str in fixed_companies:
            company_combo.setCurrentText(company_str)
        elif fixed_companies:
            company_combo.setCurrentIndex(0)
            initial_company_for_combo = company_combo.currentText() if company_combo.count() > 0 else ""
        
        current_entry_data["current_company"] = initial_company_for_combo # Update based on combo actual

        date_edit = QDateEdit()
        date_edit.setDisplayFormat("MM/dd/yyyy")
        date_edit.setCalendarPopup(True)
        if date_str:
            q_date = QDate.fromString(date_str, "MM/dd/yyyy")
            date_edit.setDate(q_date if q_date.isValid() else data_utils.get_default_working_date())
        else:
            date_edit.setDate(data_utils.get_default_working_date())
        current_entry_data["current_date"] = date_edit.date().toString("MM/dd/yyyy") # Update based on date_edit actual
        
        form_layout.addRow("Company:", company_combo)
        form_layout.addRow("Date (MM/DD/YYYY):", date_edit)
        report_entry_main_layout.addLayout(form_layout)

        self.record_items_layout.insertWidget(insert_at_index, report_entry_group)
        # Store references to widgets for later access if needed by commands or updates
        current_entry_data["company_combo"] = company_combo
        current_entry_data["date_edit"] = date_edit
        self.report_entries.insert(insert_at_index, current_entry_data)

        # Connect signals for changes
        company_combo.currentTextChanged.connect(
            lambda text, ed=current_entry_data: self._handle_report_detail_change(ed, "company", text)
        )
        date_edit.dateChanged.connect( # Use dateChanged for calendar popup
            lambda q_date, ed=current_entry_data: self._handle_report_detail_change(ed, "date", q_date.toString("MM/dd/yyyy"))
        )
        # For manual date edits, editingFinished is also good
        date_edit.editingFinished.connect(
            lambda ed=current_entry_data, de=date_edit: self._handle_report_detail_change(ed, "date", de.date().toString("MM/dd/yyyy"))
        )

        remove_report_button.clicked.connect(lambda: self.recordReportRemoveRequested.emit(current_entry_data))
        
        self._apply_report_color_style(report_entry_group, current_entry_data["current_color"])
        self._apply_report_display_limit()
        return current_entry_data # Return the created entry data

    def _handle_report_detail_change(self, entry_data_dict, field_name, new_value_str):
        old_value_str = ""
        if field_name == "company": old_value_str = entry_data_dict.get("current_company", "")
        elif field_name == "date": old_value_str = entry_data_dict.get("current_date", "")
        # Color is handled by _handle_report_color_change

        if new_value_str != old_value_str:
            self.recordReportDetailChanged.emit(entry_data_dict, field_name, old_value_str, new_value_str)
            # The command will update the "current_*" field in entry_data_dict via update_report_entry_detail

    def _remove_report_entry(self, entry_data_dict):
        if entry_data_dict in self.report_entries:
            self.report_entries.remove(entry_data_dict)
            widget_to_remove = entry_data_dict.get("widget")
            if widget_to_remove:
                widget_to_remove.deleteLater()
        # No need to call _apply_report_display_limit here, as removal might bring it under limit

    def _handle_report_color_change(self, entry_data, color_name):
        old_color = entry_data.get("current_color", "default")
        if color_name != old_color:
            self.recordReportDetailChanged.emit(entry_data, "color", old_color, color_name)
            # Command will call update_report_entry_detail which calls _apply_report_color_style

    def _apply_report_color_style(self, group_box_widget, color_name):
        group_box_widget.setProperty("report_color", color_name if color_name else "default")
        group_box_widget.style().unpolish(group_box_widget); group_box_widget.style().polish(group_box_widget); group_box_widget.update()

    def _apply_report_display_limit(self):
        if len(self.report_entries) <= self.MAX_REPORTS_DISPLAYED:
            return
        num_to_remove = len(self.report_entries) - self.MAX_REPORTS_DISPLAYED
        for _ in range(num_to_remove):
            if self.report_entries: # Should always be true here
                oldest_entry = self.report_entries.pop() # Assumes latest is at index 0, oldest at end
                if oldest_entry.get("widget"):
                    oldest_entry["widget"].deleteLater()

    def load_data(self, record_list_for_quote):
        self.clear_data()
        # Sort all reports by date, latest first
        def get_report_date_key(report_dict):
            date_str = report_dict.get("date", "")
            q_date = QDate.fromString(date_str, "MM/dd/yyyy")
            return q_date if q_date.isValid() else QDate(1900, 1, 1)

        record_list_for_quote.sort(key=get_report_date_key, reverse=True)
        reports_to_display = record_list_for_quote[:self.MAX_REPORTS_DISPLAYED]

        for idx, report_data in enumerate(reports_to_display):
            self.add_report_entry(
                company_str=report_data.get("company", ""),
                date_str=report_data.get("date", ""),
                color_str=report_data.get("color", ""),
                insert_at_index=idx # Latest at top
            )

    def get_data(self):
        return [
            {"company": entry["company_combo"].currentText(),
             "date": entry["date_edit"].date().toString("MM/dd/yyyy"),
             "color": entry.get("current_color", "default")} # Use current_color for data model
            for entry in self.report_entries
        ]

    def clear_data(self):
        while self.record_items_layout.count():
            item = self.record_items_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.report_entries.clear()

    def update_company_dropdowns(self):
        fixed_companies = self.fixed_companies_provider_func()
        for entry_data in self.report_entries:
            company_combo = entry_data.get("company_combo")
            if company_combo:
                current_selection = company_combo.currentText()
                company_combo.clear()
                company_combo.addItems(fixed_companies)
                if current_selection in fixed_companies:
                    company_combo.setCurrentText(current_selection)
                elif fixed_companies:
                    company_combo.setCurrentIndex(0)

    def update_report_entry_detail(self, report_ui_entry_data, field_name, new_value, from_command=False):
        """Updates a specific detail of a report entry UI and its internal 'current_*' tracker."""
        if report_ui_entry_data not in self.report_entries:
            print(f"Error: Report UI entry data not found for update: {report_ui_entry_data}")
            return

        if field_name == "company":
            report_ui_entry_data["company_combo"].blockSignals(True)
            report_ui_entry_data["company_combo"].setCurrentText(new_value)
            report_ui_entry_data["company_combo"].blockSignals(False)
            report_ui_entry_data["current_company"] = new_value
        elif field_name == "date":
            q_date = QDate.fromString(new_value, "MM/dd/yyyy")
            if q_date.isValid():
                report_ui_entry_data["date_edit"].blockSignals(True)
                report_ui_entry_data["date_edit"].setDate(q_date)
                report_ui_entry_data["date_edit"].blockSignals(False)
                report_ui_entry_data["current_date"] = new_value
        elif field_name == "color":
            report_ui_entry_data["current_color"] = new_value
            self._apply_report_color_style(report_ui_entry_data["widget"], new_value)
        
        # Ensure the main data model (all_quotes_data) is updated by the command itself.

    def setEnabled(self, enabled):
        self.record_group.setEnabled(enabled)
        super().setEnabled(enabled)

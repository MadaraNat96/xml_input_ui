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



class EPSSectionWidget(QWidget):
    # Signals to be connected by the main editor for global highlight sync
    # Defined as class attributes for clarity and standard practice
    companyLineEditFocusGained = pyqtSignal(str, QLineEdit) # company_name, QLineEdit instance
    companyLineEditFocusLost = pyqtSignal(str, QLineEdit)   # company_name, QLineEdit instance

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
        self._clear_layout_widgets(self.eps_items_layout)
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
        current_eps_data = self.get_data() # Get data in the format suitable for load_data
        
        # Clear existing UI elements and internal state related to year entries
        # but keep self.selected_eps_years_to_display
        self._clear_layout_widgets(self.eps_items_layout)
        self.eps_year_entries.clear()
        
        # For each year in current_eps_data, we need to re-initialize its
        # selected_companies_to_display_for_year to the new fixed_companies_provider list.
        # This will be handled naturally by load_data -> _add_eps_year_fields
        # which initializes selected_companies_to_display_for_year.
        
        # Reload the data. load_data will use the new fixed_companies_provider
        # to structure the company boxes within each year.
        self.load_data(current_eps_data)
        # After loading, ensure visibility per year is updated based on their individual selections
        # (which would have been reset to all fixed companies during load_data)
        # _update_visible_eps_years is called at the end of load_data

    def _clear_layout_widgets(self, layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None: widget.deleteLater() 
                else:
                    sub_layout = item.layout()
                    if sub_layout is not None: self._clear_layout_widgets(sub_layout)

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
            lambda: (self._remove_dynamic_list_entry(year_entry_data, self.eps_year_entries), 
                     self._update_visible_eps_years())
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
            self._add_eps_year_fields(year_name_str=year_name.strip())

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
        gbox_main_layout.addLayout(form_layout)

        company_data = {
            "name": company_name_str,  
            "value_edit": company_value_edit,
            "growth_edit": company_growth_edit, "widget": company_group_box
        }
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
            year_entry_data["selected_companies_to_display_for_year"] = dialog.get_selected_companies()
            self._update_visible_eps_companies_for_year(year_entry_data)

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
            self.selected_eps_years_to_display = dialog.get_selected_years()
            self._update_visible_eps_years()

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
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        self.details_group = QGroupBox("Quote Details")
        details_form_layout = QFormLayout(self.details_group)
        self.name_edit = QLineEdit()
        self.price_edit = QLineEdit()
        details_form_layout.addRow(QLabel("Quote Name:"), self.name_edit)
        details_form_layout.addRow(QLabel("Quote Price:"), self.price_edit)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0,0,0,0)
        main_layout.addWidget(self.details_group)

    def load_data(self, name, price, is_new_quote):
        self.name_edit.setText(name)
        self.price_edit.setText(price)
        self.name_edit.setReadOnly(not is_new_quote)
        self.price_edit.setReadOnly(not is_new_quote) # Price should also be editable for new quote

    def get_data(self):
        return self.name_edit.text(), self.price_edit.text()

    def clear_data(self):
        self.name_edit.clear()
        self.price_edit.clear()

    def setEnabled(self, enabled):
        self.details_group.setEnabled(enabled)
        super().setEnabled(enabled)


class EPriceSectionWidget(QWidget):
    companyFocusGained = pyqtSignal(str, QLineEdit)
    companyFocusLost = pyqtSignal(str, QLineEdit)

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

    def _clear_layout_widgets(self, layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None: widget.deleteLater()

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
        value_edit.focusGainedSignal.connect(self.companyFocusGained)
        value_edit.focusLostSignal.connect(self.companyFocusLost)
        form_layout.addRow(value_edit)
        gbox_main_layout.addLayout(form_layout)
        entry_data = {"name": company_name_str, "value_edit": value_edit, "widget": company_group_box}
        self.eprice_items_layout.addWidget(company_group_box)
        self.eprice_entries.append(entry_data)

    def refresh_structure(self, new_fixed_companies=None):
        fixed_companies = new_fixed_companies if new_fixed_companies is not None else self.fixed_companies_provider_func()
        
        current_values = {entry["name"]: entry["value_edit"].text() for entry in self.eprice_entries}
        self._clear_layout_widgets(self.eprice_items_layout)
        self.eprice_entries.clear()

        self.selected_eprice_companies_to_display = list(fixed_companies) # Default to all

        for company_name in fixed_companies:
            self._create_company_ui(company_name, current_values.get(company_name, ""))
        self._update_visible_companies()

    def load_data(self, eprice_data_list_for_quote):
        loaded_data_map = {item["name"]: item["value"] for item in eprice_data_list_for_quote}
        for entry in self.eprice_entries:
            entry["value_edit"].setText(loaded_data_map.get(entry["name"], ""))

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
        # self.refresh_structure() # This might be too much, just clearing values is enough

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
    def __init__(self, fixed_companies_provider_func, parent=None):
        super().__init__(fixed_companies_provider_func, parent)
        self.eprice_group.setTitle("PE Companies") # Override title
        self.choose_companies_button.setToolTip("Select which PE companies to display")

# RecordReportSectionWidget - This one is more distinct
class RecordReportSectionWidget(QWidget):
    MAX_REPORTS_DISPLAYED = 5 # Class constant for this section

    def __init__(self, fixed_companies_provider_func, parent=None):
        super().__init__(parent)
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
        add_report_button.setFixedSize(20,20)
        add_report_button.clicked.connect(lambda: self.add_report_entry()) # Default add to top
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

        top_bar_layout = QHBoxLayout()
        top_bar_layout.addStretch()

        current_entry_data = {"widget": report_entry_group, "color": color_str if color_str else "default"}

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
        if company_str and company_str in fixed_companies:
            company_combo.setCurrentText(company_str)
        elif fixed_companies:
            company_combo.setCurrentIndex(0)
            
        date_edit = QDateEdit()
        date_edit.setDisplayFormat("MM/dd/yyyy")
        date_edit.setCalendarPopup(True)
        if date_str:
            q_date = QDate.fromString(date_str, "MM/dd/yyyy")
            date_edit.setDate(q_date if q_date.isValid() else data_utils.get_default_working_date())
        else:
            date_edit.setDate(data_utils.get_default_working_date())
        
        form_layout.addRow("Company:", company_combo)
        form_layout.addRow("Date (MM/DD/YYYY):", date_edit)
        report_entry_main_layout.addLayout(form_layout)

        self.record_items_layout.insertWidget(insert_at_index, report_entry_group)
        current_entry_data["company_combo"] = company_combo
        current_entry_data["date_edit"] = date_edit
        self.report_entries.insert(insert_at_index, current_entry_data)

        remove_report_button.clicked.connect(lambda: self._remove_report_entry(current_entry_data))
        
        self._apply_report_color_style(report_entry_group, current_entry_data["color"])
        self._apply_report_display_limit()

    def _remove_report_entry(self, entry_data_dict):
        if entry_data_dict in self.report_entries:
            self.report_entries.remove(entry_data_dict)
        widget_to_remove = entry_data_dict.get("widget")
        if widget_to_remove:
            widget_to_remove.deleteLater()
        # No need to call _apply_report_display_limit here, as removal might bring it under limit

    def _handle_report_color_change(self, entry_data, color_name):
        entry_data["color"] = color_name
        self._apply_report_color_style(entry_data["widget"], color_name)

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
             "color": entry.get("color", "default")}
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

    def setEnabled(self, enabled):
        self.record_group.setEnabled(enabled)
        super().setEnabled(enabled)

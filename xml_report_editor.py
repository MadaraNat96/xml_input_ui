# t:\Work\xml_input_ui\xml_report_editor.py
import sys
import os # Keep os for os.path.basename and os.getcwd
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QInputDialog, QMenu,
    QFormLayout, QLineEdit, QPushButton, QLabel, QScrollArea, QDateEdit, QDialog, QComboBox,
    QGroupBox, QMessageBox, QFileDialog, QStyle)
from PyQt6.QtGui import QIcon, QAction, QKeySequence
from PyQt6.QtCore import Qt, QDate, QPoint
from dialogs import EPSYearSelectionDialog, EPriceCompanySelectionDialog, ManageEPriceCompaniesDialog
from ui_sections import (EPSSectionWidget, QuoteSelectionWidget, QuoteDetailsWidget,
                         EPriceSectionWidget, PESectionWidget, RecordReportSectionWidget)
from custom_widgets import FocusAwareLineEdit, HighlightableGroupBox # Import custom widgets
import data_utils 


class XmlReportEditor(QMainWindow):
    MAX_REPORTS_DISPLAYED = 5
    def __init__(self):
        super().__init__()
        self.setWindowTitle("XML Report Editor")
        self.current_file_path = None
        self.setGeometry(100, 100, 800, 700)

        self.all_quotes_data = {}
        self.selected_quote_name = None
        # self.displayed_quote_ui = None # This will be replaced by individual section widgets
        
        # This list acts as the default if eprice_companies.cfg is missing/empty
        self.EPRICE_FIXED_COMPANIES = ["VCSC", "SSI", "MBS", "AGR", "BSC", "FPT", "CTG"] 
        self.globally_focused_company_widgets = {} # {company_name: set(QLineEdit_widgets)}
        self.active_highlighted_company = None

        
        self.init_ui() 
        self.load_initial_data() 
        self._load_eprice_config_and_update_ui()
        self._apply_global_styles()

    def _apply_global_styles(self):
        self.setStyleSheet("""
            HighlightableGroupBox { 
                border: 1px solid silver;
                margin-top: 1.8ex; /* Adjusted space for title */
            }
            HighlightableGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left; /* Position at the top-left */
                padding: 0 3px;
            }
            HighlightableGroupBox[highlighted="true"] {
                border: 2px solid #FFBF00; /* Amber/Orange */
                background-color: #FFFACD; /* LemonChiffon for background highlight */
            }

            /* Styles for individual Record Report Boxes */
            QGroupBox#recordReportEntryBox {
                border: 1px solid silver; 
                margin-top: 0.5ex;
            }
            /* Note: The ::title part from the original inline style is omitted here */
            /* as report_entry_group is created with QGroupBox() (no title). */
            /* If it were to have a title, styles would be QGroupBox#recordReportEntryBox::title { ... } */

            QGroupBox#recordReportEntryBox[report_color="red"] {
                background-color: #FFCCCC; /* Light Red */
            }
            QGroupBox#recordReportEntryBox[report_color="green"] {
                background-color: #CCFFCC; /* Light Green */
            }
            QGroupBox#recordReportEntryBox[report_color="yellow"] {
                background-color: #FFFFCC; /* Light Yellow */
            }
            QGroupBox#recordReportEntryBox[report_color="white"] {
                background-color: #FFFFFF; /* White */
            }
            /* For default, no specific background rule is needed; it will be transparent or inherit from QGroupBox#recordReportEntryBox. */
        """)


    def init_ui(self): 
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        self.setCentralWidget(scroll_area)

        main_content_widget = QWidget()
        # Set a minimum width for the main content to encourage scrollbar appearance sooner if needed
        # This helps if the content inside the columns is very wide.
        # main_content_widget.setMinimumWidth(780) # Example, adjust as needed

        scroll_area.setWidget(main_content_widget)
        
        self.main_layout = QVBoxLayout(main_content_widget)
        main_content_widget.setLayout(self.main_layout)

        date_group = QGroupBox("Global Report Date")
        date_layout = QFormLayout()
        self.root_date_edit = QDateEdit()
        self.root_date_edit.setDisplayFormat("MM/dd/yyyy")
        self.root_date_edit.setCalendarPopup(True)
        date_layout.addRow(QLabel("Date (MM/DD/YYYY):"), self.root_date_edit)
        date_group.setLayout(date_layout)
        self.main_layout.addWidget(date_group)

        # Instantiate section widgets
        self.quote_selection_widget = QuoteSelectionWidget(self)
        self.quote_selection_widget.selectQuoteClicked.connect(self.handle_select_quote_button)
        self.quote_selection_widget.addQuoteClicked.connect(self.handle_add_new_quote_button)
        self.quote_selection_widget.removeQuoteClicked.connect(self.handle_remove_displayed_quote_button)

        self.quote_details_widget = QuoteDetailsWidget(self)
        self.eprice_section_widget = EPriceSectionWidget(lambda: self.EPRICE_FIXED_COMPANIES, self)
        self.eps_section_widget = EPSSectionWidget(fixed_companies_provider=self.EPRICE_FIXED_COMPANIES, parent=self)
        self.pe_section_widget = PESectionWidget(lambda: self.EPRICE_FIXED_COMPANIES, self) # PE uses same fixed list
        self.record_report_section_widget = RecordReportSectionWidget(lambda: self.EPRICE_FIXED_COMPANIES, self)

        # Connect focus signals for global highlighting
        self.eprice_section_widget.companyFocusGained.connect(self.handle_company_widget_focus_gained)
        self.eprice_section_widget.companyFocusLost.connect(self.handle_company_widget_focus_lost)
        self.eps_section_widget.companyLineEditFocusGained.connect(self.handle_company_widget_focus_gained)
        self.eps_section_widget.companyLineEditFocusLost.connect(self.handle_company_widget_focus_lost)
        self.pe_section_widget.companyFocusGained.connect(self.handle_company_widget_focus_gained)
        self.pe_section_widget.companyFocusLost.connect(self.handle_company_widget_focus_lost)

        two_column_main_layout = QHBoxLayout()
        column1_widget = QWidget() 
        column1_layout = QVBoxLayout(column1_widget)
        column1_layout.addWidget(date_group)
        column1_layout.addWidget(self.quote_selection_widget)
        column1_layout.addWidget(self.quote_details_widget)
        column1_layout.addSpacing(50) 
        column1_layout.addWidget(self.record_report_section_widget)
        column1_layout.addStretch() 
        
        column2_widget = QWidget() 
        column2_layout = QVBoxLayout(column2_widget)
        column2_layout.addWidget(self.eprice_section_widget)
        column2_layout.addWidget(self.eps_section_widget)
        column2_layout.addWidget(self.pe_section_widget)
        column2_layout.addStretch() # Add stretch to push content upwards
        
        two_column_main_layout.addWidget(column1_widget, 3) 
        two_column_main_layout.addWidget(column2_widget, 17) 
        self.main_layout.addLayout(two_column_main_layout) 

        self._set_displayed_quote_ui_enabled(False) 

        self._create_menu_bar()

    def _set_displayed_quote_ui_enabled(self, enabled):
        self.quote_details_widget.setEnabled(enabled)
        self.eprice_section_widget.setEnabled(enabled)
        self.eps_section_widget.setEnabled(enabled)
        self.pe_section_widget.setEnabled(enabled)
        self.record_report_section_widget.setEnabled(enabled)
        self.quote_selection_widget.remove_quote_button.setEnabled(enabled and bool(self.selected_quote_name))

    def _create_menu_bar(self):
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("&File")
        open_action = QAction("&Open...", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self.open_xml_file)
        file_menu.addAction(open_action)
        save_action = QAction("&Save", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self.save_xml_file) 
        file_menu.addAction(save_action)
        save_as_action = QAction("Save &As...", self)
        save_as_action.setShortcut(QKeySequence.StandardKey.SaveAs)
        save_as_action.triggered.connect(self.save_xml_file_as)
        file_menu.addAction(save_as_action)
        file_menu.addSeparator()
        exit_action = QAction("E&xit", self)
        exit_action.triggered.connect(self.close) 
        file_menu.addAction(exit_action)

        edit_menu = menu_bar.addMenu("&Edit")
        manage_eprice_action = QAction("Manage E-Price Companies...", self)
        manage_eprice_action.triggered.connect(self._handle_manage_eprice_companies_dialog)
        edit_menu.addAction(manage_eprice_action)

    def _load_eprice_config_and_update_ui(self):
        # Load the shared list of companies. EPRICE_FIXED_COMPANIES here is the default.
        self.EPRICE_FIXED_COMPANIES = data_utils.load_eprice_config(self.EPRICE_FIXED_COMPANIES)

        # Update all sections that depend on the fixed company list
        self.eprice_section_widget.refresh_structure(self.EPRICE_FIXED_COMPANIES)
        self.pe_section_widget.refresh_structure(self.EPRICE_FIXED_COMPANIES) # PE uses the same list
        self.eps_section_widget.refresh_structure_with_new_fixed_companies(self.EPRICE_FIXED_COMPANIES)
        self.record_report_section_widget.update_company_dropdowns()

    def _handle_manage_eprice_companies_dialog(self):
        dialog = ManageEPriceCompaniesDialog(self.EPRICE_FIXED_COMPANIES, self)
        if dialog.exec() == QDialog.DialogCode.Accepted: 
            new_fixed_list = dialog.get_updated_companies()
            if new_fixed_list != self.EPRICE_FIXED_COMPANIES:
                self.EPRICE_FIXED_COMPANIES = new_fixed_list
                # Reload/rebuild UI elements that depend on this list
                self._load_eprice_config_and_update_ui() # This will refresh all relevant sections
                data_utils.save_eprice_config(self.EPRICE_FIXED_COMPANIES) 
                QMessageBox.information(self, "Fixed Companies List Updated", 
                                        "The list of fixed companies (for E-Price and PE sections) has been updated.")

    def handle_company_widget_focus_gained(self, company_name, line_edit_widget):
        # Add the widget to the set of focused widgets for this company
        if company_name not in self.globally_focused_company_widgets:
            self.globally_focused_company_widgets[company_name] = set()
        self.globally_focused_company_widgets[company_name].add(line_edit_widget)

        # If this company is not already the active highlighted one, update highlighting
        if self.active_highlighted_company != company_name:
            if self.active_highlighted_company is not None:
                self._update_highlight_for_company(self.active_highlighted_company, False)
            
            self.active_highlighted_company = company_name
            self._update_highlight_for_company(self.active_highlighted_company, True)

    def handle_company_widget_focus_lost(self, company_name, line_edit_widget):
        # Remove the widget from the set of focused widgets for this company
        if company_name in self.globally_focused_company_widgets:
            if line_edit_widget in self.globally_focused_company_widgets[company_name]:
                self.globally_focused_company_widgets[company_name].remove(line_edit_widget)
            if not self.globally_focused_company_widgets[company_name]: # Set is now empty
                del self.globally_focused_company_widgets[company_name]

        # If this company was the active highlighted one and now has no focused widgets, unhighlight it
        if self.active_highlighted_company == company_name and \
           company_name not in self.globally_focused_company_widgets:
            self._update_highlight_for_company(self.active_highlighted_company, False)
            self.active_highlighted_company = None

    def _update_highlight_for_company(self, company_name_to_update, highlight_state):
        self.eprice_section_widget.update_company_highlight_state(company_name_to_update, highlight_state)
        self.eps_section_widget.update_company_highlight_state(company_name_to_update, highlight_state)
        self.pe_section_widget.update_company_highlight_state(company_name_to_update, highlight_state)

    # Methods like add_record_report_fields, _handle_report_color_change, 
    # _apply_report_color_style, _apply_report_display_limit are now part of RecordReportSectionWidget

    # _update_record_report_company_dropdowns is now part of RecordReportSectionWidget.update_company_dropdowns

    # _remove_dynamic_list_entry is now handled within each section widget if needed, or can be a static utility

    def _clear_layout_widgets(self, layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None: widget.deleteLater() 
                else:
                    sub_layout = item.layout()
                    if sub_layout is not None: self._clear_layout_widgets(sub_layout)
    
    def clear_all_fields(self):
        initial_root_date = data_utils.get_default_working_date()
        if initial_root_date.isValid(): self.root_date_edit.setDate(initial_root_date)
        
        # self._load_eprice_config_and_update_ui() # Called during init, not needed here unless config changed

        self._clear_displayed_quote_ui() 
        self.all_quotes_data.clear()
        self.selected_quote_name = None
        
        self.quote_selection_widget.clear_input()
        self._set_displayed_quote_ui_enabled(False)
        self.current_file_path = None
        self.setWindowTitle("XML Report Editor")

    def _clear_displayed_quote_ui(self):
        self.quote_details_widget.clear_data()
        self.eprice_section_widget.clear_data()
        self.eprice_section_widget.refresh_structure() # Rebuild with fixed companies, clear values
        self.eps_section_widget.clear_data()
        self.pe_section_widget.clear_data()
        self.pe_section_widget.refresh_structure() # Rebuild with fixed companies, clear values
        self.record_report_section_widget.clear_data()

    def _display_quote(self, quote_name, is_new_quote=False):
        self._save_displayed_quote_data() 
        self._clear_displayed_quote_ui() 
        
        if quote_name not in self.all_quotes_data:
            # This case should be handled by the calling function (handle_select_quote_button)
            self.quote_selection_widget.clear_input()
            self.selected_quote_name = None
            self._set_displayed_quote_ui_enabled(False)
            return

        self.selected_quote_name = quote_name
        quote_data = self.all_quotes_data[quote_name]

        self.quote_details_widget.load_data(quote_data.get("name", ""), quote_data.get("price", ""), is_new_quote)
        self.eprice_section_widget.load_data(quote_data.get("e_price", []))
        self.eps_section_widget.load_data(quote_data.get("eps", []))
        self.pe_section_widget.load_data(quote_data.get("pe", []))
        self.record_report_section_widget.load_data(quote_data.get("record", []))
        
        self.quote_selection_widget.set_quote_name_input(quote_name)
        self._set_displayed_quote_ui_enabled(True)

    def _save_displayed_quote_data(self):
        if not self.selected_quote_name or self.selected_quote_name not in self.all_quotes_data:
            return 
        current_quote_data_entry = self.all_quotes_data[self.selected_quote_name]
        
        name, price = self.quote_details_widget.get_data()
        current_quote_data_entry["name"] = name
        current_quote_data_entry["price"] = price
        current_quote_data_entry["e_price"] = self.eprice_section_widget.get_data()
        current_quote_data_entry["eps"] = self.eps_section_widget.get_data()
        current_quote_data_entry["pe"] = self.pe_section_widget.get_data()
        current_quote_data_entry["record"] = self.record_report_section_widget.get_data()

    def handle_select_quote_button(self, quote_name_to_select): # Parameter from signal
        if not quote_name_to_select:
            QMessageBox.information(self, "Info", "Please enter a quote name to select.")
            return
        if quote_name_to_select == self.selected_quote_name: return
        if quote_name_to_select in self.all_quotes_data:
            self._display_quote(quote_name_to_select, is_new_quote=False)
        else:
            QMessageBox.warning(self, "Not Found", f"Quote '{quote_name_to_select}' not found. Use 'Add New Quote' to create it.")

    def handle_add_new_quote_button(self, new_quote_name): # Parameter from signal
        if not new_quote_name:
            QMessageBox.warning(self, "Input Error", "Please enter a name for the new quote in the text box.")
            return
        if new_quote_name in self.all_quotes_data:
            QMessageBox.information(self, "Exists", f"Quote '{new_quote_name}' already exists. Displaying it now.")
            self._display_quote(new_quote_name, is_new_quote=False) 
            return
        self._save_displayed_quote_data() 
        self.all_quotes_data[new_quote_name] = { 
            "name": new_quote_name, "price": "",
            "e_price": [], "eps": [], "pe": [], "record": []}
        self._display_quote(new_quote_name, is_new_quote=True) 
        QMessageBox.information(self, "Quote Added", f"New quote '{new_quote_name}' added and displayed. Fill in its details.")

    def handle_remove_displayed_quote_button(self):
        if not self.selected_quote_name:
            QMessageBox.warning(self, "No Quote", "No quote is currently displayed to remove.")
            return
        reply = QMessageBox.question(self, "Confirm Removal",
                                     f"Are you sure you want to remove the quote '{self.selected_quote_name}'?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            del self.all_quotes_data[self.selected_quote_name]
            self.selected_quote_name = None
            self._clear_displayed_quote_ui()
            self.quote_selection_widget.clear_input()
            self._set_displayed_quote_ui_enabled(False)
            QMessageBox.information(self, "Removed", "The quote has been removed.")
            if self.all_quotes_data:
                first_remaining_quote = next(iter(self.all_quotes_data))
                self._display_quote(first_remaining_quote, is_new_quote=False)

    def load_initial_data(self):
        initial_root_date = data_utils.get_default_working_date()
        if initial_root_date.isValid():
            self.root_date_edit.setDate(initial_root_date)

    def closeEvent(self, event):
        data_utils.save_eprice_config(self.EPRICE_FIXED_COMPANIES) 
        super().closeEvent(event)

    def open_xml_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open XML File", "", "XML Files (*.xml);;All Files (*)")
        if file_path:
            self.load_xml_file_data(file_path) 

    def load_xml_file_data(self, file_path): 
        self.clear_all_fields() 

        root_date_qdate, all_quotes_data_dict = data_utils.parse_xml_data(file_path)

        if root_date_qdate is None and all_quotes_data_dict is None: 
            return

        self.root_date_edit.setDate(root_date_qdate)
        self.all_quotes_data = all_quotes_data_dict if all_quotes_data_dict is not None else {}


        first_quote_name_loaded = None
        if self.all_quotes_data:
            first_quote_name_loaded = next(iter(self.all_quotes_data), None) 
        
        if first_quote_name_loaded:
            self._display_quote(first_quote_name_loaded, is_new_quote=False)
        else: 
            self._set_displayed_quote_ui_enabled(False) 

        self.current_file_path = file_path
        self.setWindowTitle(f"XML Report Editor - {os.path.basename(file_path)}")

    def collect_data_for_xml(self): 
        self._save_displayed_quote_data() 
        all_data = {"quotes": []}
        all_data["date"] = self.root_date_edit.date().toString("MM/dd/yyyy")
        for quote_name, quote_data_dict in self.all_quotes_data.items():
            if not quote_data_dict.get("name"):
                 QMessageBox.warning(self, "Data Error", f"Quote '{quote_name}' missing name. Skipping.")
                 continue 
            all_data["quotes"].append(quote_data_dict)
        return all_data

    def _perform_save(self, file_path_to_save):
        collected_data = self.collect_data_for_xml() 
        root_element = data_utils.build_xml_tree(collected_data)
        
        if data_utils.save_xml_to_file(file_path_to_save, root_element):
            QMessageBox.information(self, "Success", f"XML saved to {file_path_to_save}")
            self.current_file_path = file_path_to_save 
            self.setWindowTitle(f"XML Report Editor - {os.path.basename(file_path_to_save)}")
            return True
        return False 

    def save_xml_file(self):
        file_path_to_save = self.current_file_path
        if not file_path_to_save: 
            default_save_path = os.path.join(os.getcwd(), "report_output.xml") 
            file_path_dialog, _ = QFileDialog.getSaveFileName(
                self, "Save XML File As", default_save_path, "XML Files (*.xml);;All Files (*)")
            if not file_path_dialog: return
            file_path_to_save = file_path_dialog
        self._perform_save(file_path_to_save)

    def save_xml_file_as(self):
        default_save_path = self.current_file_path if self.current_file_path else os.path.join(os.getcwd(), "report_output.xml")
        file_path_dialog, _ = QFileDialog.getSaveFileName(
            self, "Save XML File As", default_save_path, "XML Files (*.xml);;All Files (*)")
        if not file_path_dialog: return
        self._perform_save(file_path_dialog)

def main():
    app = QApplication(sys.argv)
    editor = XmlReportEditor()
    editor.showMaximized() 
    sys.exit(app.exec())

if __name__ == '__main__':
    main()

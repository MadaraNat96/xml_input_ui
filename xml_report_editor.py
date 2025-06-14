# t:\Work\xml_input_ui\xml_report_editor.py
import sys
import os # Keep os for os.path.basename and os.getcwd
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QInputDialog, QMenu, QTextEdit,
    QFormLayout, QLineEdit, QPushButton, QLabel, QScrollArea, QDateEdit, QDialog, QComboBox,
    QGroupBox, QMessageBox, QFileDialog, QStyle)
from PyQt6.QtGui import QIcon, QAction, QKeySequence
from PyQt6.QtCore import Qt, QDate, QPoint
from dialogs import ManageEPriceCompaniesDialog, ManageSectorsDialog
from ui_components.eps_section_widget import EPSSectionWidget
from ui_components.quote_selection_widget import QuoteSelectionWidget
from ui_components.quote_details_widget import QuoteDetailsWidget
from ui_components.eprice_section_widget import EPriceSectionWidget
from ui_components.pe_section_widget import PESectionWidget
from ui_components.sectors_section_widget import SectorsSectionWidget 
from ui_components.record_report_section_widget import RecordReportSectionWidget
from ui_components.eps_growth_chart_widget import EPSGrowthChartWidget
from custom_widgets import FocusAwareLineEdit, HighlightableGroupBox  # Import custom widgets
from commands import (Command, ChangeRootDateCommand, ChangeQuoteDetailCommand, 
                      ChangeEPriceValueCommand, ChangePEValueCommand, AddQuoteCommand, RemoveQuoteCommand,
                      ChangeEPSValueCommand, AddEPSYearCommand, RemoveEPSYearCommand,
                      ChangeEPSYearDisplayCommand, ChangeEPSCompaniesForYearDisplayCommand,
                      AddRecordReportCommand, RemoveRecordReportCommand, ChangeRecordReportDetailCommand,
                      ChangeEPriceFixedCompaniesCommand, ChangeSectorsListCommand)
from ui_components.quote_filter_widget import QuoteFilterWidget
from command_manager import CommandManager
from editor_action_handler import EditorActionHandler # Import the new handler class
from ui_managers import GlobalHighlightManager # Import the new manager
from file_manager import FileManager # Import the new FileManager
from chart_sub_window import ChartSubWindow  # Import the sub window
import data_utils 


class XmlReportEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("XML Report Editor")
        # self.current_file_path = None # Now managed by FileManager
        self.setGeometry(100, 100, 800, 700)

        self.all_quotes_data = {}
        self.selected_quote_name = None
        # self.displayed_quote_ui = None # This will be replaced by individual section widgets
        
        # This list acts as the default if eprice_companies.cfg is missing/empty
        self.EPRICE_FIXED_COMPANIES = ["VCSC", "SSI", "MBS", "AGR", "BSC", "FPT", "CTG"] 

        self.file_manager = FileManager(self) # Instantiate FileManager
        self.SECTOR_LIST = []  # Initialize SECTOR_LIST before it's used
        self.command_manager = CommandManager(self) # Instantiate CommandManager
        self.action_handler = EditorActionHandler(self)  # Instantiate ActionHandler
        
        self.init_ui() 
        self.load_initial_data() 
        self._load_eprice_config_and_update_ui()
        self._apply_global_styles()
        self._load_sectors_config_and_update_ui()

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
        # Store initial date for command creation
        self._current_root_date_str = self.root_date_edit.date().toString("MM/dd/yyyy") # action_handler will need this
        self.root_date_edit.editingFinished.connect(self.action_handler.handle_root_date_changed)
        # Also connect dateChanged for calendar popup changes
        self.root_date_edit.dateChanged.connect(self.action_handler.handle_root_date_changed_by_calendar)
        date_layout.addRow(QLabel("Date (MM/DD/YYYY):"), self.root_date_edit)
        date_group.setLayout(date_layout)
        self.main_layout.addWidget(date_group)

        # Instantiate section widgets
        self.quote_selection_widget = QuoteSelectionWidget(self)
        self.quote_selection_widget.selectQuoteClicked.connect(self.handle_select_quote_button) # Stays in editor
        self.quote_selection_widget.addQuoteClicked.connect(self.handle_add_new_quote_button)   # Stays in editor
        self.quote_selection_widget.removeQuoteClicked.connect(self.handle_remove_displayed_quote_button) # Stays in editor

        self.quote_details_widget = QuoteDetailsWidget(self)
        self.quote_details_widget.quoteNameChanged.connect(self.action_handler.handle_quote_name_changed)
        self.quote_details_widget.quotePriceChanged.connect(self.action_handler.handle_quote_price_changed)

        self.eprice_section_widget = EPriceSectionWidget(lambda: self.EPRICE_FIXED_COMPANIES, self)
        self.eprice_section_widget.ePriceValueChanged.connect(self.action_handler.handle_eprice_value_changed)
        self.eps_section_widget = EPSSectionWidget(fixed_companies_provider=self.EPRICE_FIXED_COMPANIES, parent=self)
        self.eps_section_widget.epsValueChanged.connect(self.action_handler.handle_eps_value_changed)
        self.eps_section_widget.epsYearAddRequested.connect(self.action_handler.handle_eps_year_add_requested)
        self.eps_section_widget.epsYearRemoveRequested.connect(self.action_handler.handle_eps_year_remove_requested)
        self.eps_section_widget.epsYearDisplayChangeRequested.connect(self.action_handler.handle_eps_year_display_change_requested)
        self.eps_section_widget.epsCompaniesForYearDisplayChangeRequested.connect(self.action_handler.handle_eps_companies_for_year_display_change_requested)
        self.eps_section_widget.epsGrowthDataPotentiallyChanged.connect(self.action_handler.handle_eps_growth_data_changed_for_chart)
        
        self.pe_section_widget = PESectionWidget(lambda: self.EPRICE_FIXED_COMPANIES, self) # PE uses same fixed list
        self.pe_section_widget.peValueChanged.connect(self.action_handler.handle_pe_value_changed) # Connect PE specific signal
        self.record_report_section_widget = RecordReportSectionWidget(lambda: self.EPRICE_FIXED_COMPANIES, self)

        self.sectors_section_widget = SectorsSectionWidget(lambda: self.SECTOR_LIST, self) # Now SECTOR_LIST is initialized
        self.sectors_section_widget.sectorValueChanged.connect(self.action_handler.handle_sector_value_changed)
        self.eps_growth_chart_widget = EPSGrowthChartWidget(self) # Instantiate the chart widget
        self.sectors_section_widget.sectorRemoved.connect(self.action_handler.handle_remove_sector)

        # Instantiate Quote Filter Widget
        self.quote_filter_widget = QuoteFilterWidget(lambda: self.SECTOR_LIST, self.all_quotes_data)
        self.quote_filter_widget.quoteSelected.connect(self.handle_filtered_quote_selected)  # Connect to new signal
        
        self.record_report_section_widget.recordReportAddRequested.connect(self.action_handler.handle_record_report_add_requested)
        self.record_report_section_widget.recordReportRemoveRequested.connect(self.action_handler.handle_record_report_remove_requested)
        self.record_report_section_widget.recordReportDetailChanged.connect(self.action_handler.handle_record_report_detail_changed)
        self.record_report_section_widget.manualRefreshRequested.connect(self.action_handler.handle_record_report_manual_refresh) # Connect new signal

        # Instantiate GlobalHighlightManager
        self.highlight_manager = GlobalHighlightManager(
            self.eprice_section_widget, self.eps_section_widget, self.pe_section_widget
        )
        # Connect focus signals for global highlighting
        self.eprice_section_widget.companyFocusGained.connect(self.highlight_manager.handle_company_widget_focus_gained)
        self.eprice_section_widget.companyFocusLost.connect(self.highlight_manager.handle_company_widget_focus_lost)
        self.eps_section_widget.companyLineEditFocusGained.connect(self.highlight_manager.handle_company_widget_focus_gained)
        self.eps_section_widget.companyLineEditFocusLost.connect(self.highlight_manager.handle_company_widget_focus_lost)
        self.pe_section_widget.companyFocusGained.connect(self.highlight_manager.handle_company_widget_focus_gained)
        self.pe_section_widget.companyFocusLost.connect(self.highlight_manager.handle_company_widget_focus_lost)

        two_column_main_layout = QHBoxLayout()
        column1_widget = QWidget() 
        column1_layout = QVBoxLayout(column1_widget)
        column1_layout.addWidget(date_group)
        column1_layout.addWidget(self.quote_selection_widget)
        column1_layout.addWidget(self.quote_details_widget)
        column1_layout.addWidget(self.sectors_section_widget)  # Add Sectors Section here
        column1_layout.addWidget(self.quote_filter_widget)  # Add Quote Filter Section here
        column1_layout.addStretch()

        # Add button above history log
        self.new_window_button = QPushButton("Chart Window")
        column1_layout.addWidget(self.new_window_button)

        column2_widget = QWidget() 
        column2_layout = QVBoxLayout(column2_widget)
        column2_layout.addWidget(self.eprice_section_widget)
        column2_layout.addWidget(self.eps_section_widget)
        column2_layout.addWidget(self.pe_section_widget)

        # Create a horizontal layout for Chart and Record Reports
        chart_and_record_layout = QHBoxLayout()
        chart_and_record_layout.addWidget(self.eps_growth_chart_widget, 17) # Chart takes 85%
        chart_and_record_layout.addWidget(self.record_report_section_widget, 3) # Record section takes 15%
        
        column2_layout.addLayout(chart_and_record_layout) # Add this horizontal layout to the second column
        column2_layout.addStretch() # Add stretch to push content upwards
        
        two_column_main_layout.addWidget(column1_widget, 3) 
        two_column_main_layout.addWidget(column2_widget, 17) 
        self.main_layout.addLayout(two_column_main_layout) 
        
        # History Log (Optional, for demonstration)
        history_group = QGroupBox("History Log")
        history_layout = QVBoxLayout(history_group)
        self.history_log_text_edit = QTextEdit()
        self.history_log_text_edit.setReadOnly(True)
        history_layout.addWidget(self.history_log_text_edit)
        # Add history log to one of the columns or a new area
        # For simplicity, adding to column1 for now
        column1_layout.addWidget(history_group)
        column1_layout.addStretch() # Ensure it doesn't take too much space initially

        self.new_window_button.clicked.connect(self.open_chart_sub_window)
        self._set_displayed_quote_ui_enabled(False) 
        self._create_menu_bar()
        self._load_sectors_config_and_update_ui()
        self.quote_filter_widget.refresh_sectors()

    def _set_displayed_quote_ui_enabled(self, enabled):
        self.quote_details_widget.setEnabled(enabled)
        self.eprice_section_widget.setEnabled(enabled)
        self.eps_section_widget.setEnabled(enabled)
        self.pe_section_widget.setEnabled(enabled)
        self.record_report_section_widget.setEnabled(enabled)
        self.eps_growth_chart_widget.setEnabled(enabled)
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
        self.undo_action = QAction("&Undo", self)
        self.undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        self.undo_action.triggered.connect(self.undo)
        self.undo_action.setEnabled(False)
        edit_menu.addAction(self.undo_action)

        self.redo_action = QAction("&Redo", self)
        self.redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        self.redo_action.triggered.connect(self.redo)
        self.redo_action.setEnabled(False)
        edit_menu.addAction(self.redo_action)
        edit_menu.addSeparator()

        manage_eprice_action = QAction("Manage E-Price Companies...", self)
        manage_eprice_action.triggered.connect(self._handle_manage_eprice_companies_dialog)
        edit_menu.addAction(manage_eprice_action)

        manage_sectors_action = QAction("Manage Sectors...", self)
        manage_sectors_action.triggered.connect(self._handle_manage_sectors_dialog)
        edit_menu.addAction(manage_sectors_action)

    def _log_history(self, message):
        self.history_log_text_edit.append(message)

    def execute_command(self, command: Command):
        """
        Executes a command and handles any editor-specific updates.

        Args:
            command (Command): The command to execute.
        """

        # Callbacks to editor
        self.command_manager.execute_command(command)
        if isinstance(command, ChangeSectorsListCommand):
            self._load_sectors_config_and_update_ui()
            self.quote_filter_widget.refresh_sectors()

    def handle_filtered_quote_selected(self, quote_name):
        """Handles the selection of a quote from the filtered list."""
        # Update the QuoteSelectionWidget's input field with the selected quote name.
        self.quote_selection_widget.set_quote_name_input(quote_name)
        self.handle_select_quote_button(quote_name)
    
    def _set_dirty_flag(self, dirty):
        title = "XML Report Editor"
        if self.file_manager.get_current_file_path():
            title += f" - {os.path.basename(self.file_manager.get_current_file_path())}"
        if dirty:
            title += "*"
        self.setWindowTitle(title)

    def _load_eprice_config_and_update_ui(self):
        """Loads eprice config and updates related UI sections."""
        # Load the shared list of companies.  EPRICE_FIXED_COMPANIES here is the default.
        self.EPRICE_FIXED_COMPANIES = data_utils.load_eprice_config(self.EPRICE_FIXED_COMPANIES)

        # Update all sections that depend on the fixed company list
        self.eprice_section_widget.refresh_structure(self.EPRICE_FIXED_COMPANIES)
        self.pe_section_widget.refresh_structure(self.EPRICE_FIXED_COMPANIES) # PE uses the same list
        self.eps_section_widget.refresh_structure_with_new_fixed_companies(self.EPRICE_FIXED_COMPANIES)
        self.record_report_section_widget.update_company_dropdowns()

    def _load_sectors_config_and_update_ui(self):
        """Loads sector configuration and refreshes the UI."""
        self.SECTOR_LIST = data_utils.load_sectors_config(self.SECTOR_LIST)
        # self.sectors_section_widget.refresh_structure(self.SECTOR_LIST)

    def _handle_manage_eprice_companies_dialog(self):
        """Handles the dialog for managing E-Price companies."""
        dialog = ManageEPriceCompaniesDialog(self.EPRICE_FIXED_COMPANIES, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_fixed_list = dialog.get_updated_companies()
            old_fixed_list = list(self.EPRICE_FIXED_COMPANIES)  # Make a copy for the command

            if new_fixed_list != old_fixed_list:
                cmd = ChangeEPriceFixedCompaniesCommand(self, old_fixed_list, new_fixed_list)
                self.execute_command(cmd)
                # The command's execute method now handles updating self.EPRICE_FIXED_COMPANIES,
                # calling _load_eprice_config_and_update_ui(), and saving the config.
                QMessageBox.information(self, "Fixed Companies List Updated",
                                        "The list of fixed companies (for E-Price and PE sections) has been updated.")

    def _handle_manage_sectors_dialog(self):
        """Handles the dialog for managing sectors."""
        dialog = ManageSectorsDialog(self.SECTOR_LIST, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_sectors_list = dialog.get_updated_sectors()
            old_sectors_list = list(self.SECTOR_LIST)
            if new_sectors_list != old_sectors_list:
                cmd = ChangeSectorsListCommand(self, old_sectors_list, new_sectors_list)
                self.execute_command(cmd)
                self._load_sectors_config_and_update_ui()

    def open_chart_sub_window(self):
                """Opens the Chart Sub Window."""
                self.chart_sub_window = ChartSubWindow(self)
                self.chart_sub_window.load_data(self.quote_selection_widget.get_quote_name_input(), "sample/fa_db_main.xml")
                # You can pass initial data or connect signals here if needed
                # Example: self.chart_sub_window.chart_widget.load_data(some_data)
                self.chart_sub_window.show()
    
    def save_current_eprice_config(self):
        """Saves the current EPRICE_FIXED_COMPANIES list to the config file."""
        data_utils.save_eprice_config(self.EPRICE_FIXED_COMPANIES)

    def _find_data_model_for_record_report(self, quote_data, ui_entry_data_ref, field_name_being_changed, old_value_of_field):
        """
        Helper to find the corresponding data model dictionary for a record report UI entry.
        This is used when a detail of a record report is changed.
        Args:
            quote_data: The data dictionary for the current quote from self.all_quotes_data.
            ui_entry_data_ref: The dictionary from RecordReportSectionWidget.report_entries.
            field_name_being_changed: The name of the field that was just changed ("company", "date", or "color").
            old_value_of_field: The value of the field *before* it was changed.
        Returns:
            The matching dictionary from quote_data["record"] or None if not found.
        """
        for idx, data_model_entry in enumerate(quote_data["record"]):
            # Match based on old values to find the correct model entry
            # The ui_entry_data_ref.get("current_...") holds the state *before* the current change was applied to it by the widget.
            # So, if field_name_being_changed is "company", its old value is old_value_of_field.
            # The other fields in ui_entry_data_ref.get("current_...") are their original values.

            original_ui_company = old_value_of_field if field_name_being_changed == "company" else ui_entry_data_ref.get("current_company")
            original_ui_date = old_value_of_field if field_name_being_changed == "date" else ui_entry_data_ref.get("current_date")
            original_ui_color = old_value_of_field if field_name_being_changed == "color" else ui_entry_data_ref.get("current_color", "default")
            
            if (data_model_entry.get("company") == original_ui_company and
                data_model_entry.get("date") == original_ui_date and
                data_model_entry.get("color", "default") == original_ui_color):
                return data_model_entry
        return None

    def _update_undo_redo_actions_state(self):
        self.undo_action.setEnabled(self.command_manager.can_undo())
        self.redo_action.setEnabled(self.command_manager.can_redo())

    def clear_all_fields(self):
        initial_root_date = data_utils.get_default_working_date()
        if initial_root_date.isValid(): self.root_date_edit.setDate(initial_root_date)
        
        # self._load_eprice_config_and_update_ui() # Called during init, not needed here unless config changed

        self._clear_displayed_quote_ui() 
        self.all_quotes_data.clear()
        self.selected_quote_name = None
        
        self.quote_selection_widget.clear_input()
        self._set_displayed_quote_ui_enabled(False)
        # self.current_file_path = None # This is managed by FileManager, but reset it here too for consistency
        # if self.file_manager: self.file_manager.current_file_path = None
        self.command_manager.clear_stacks()
        self._set_dirty_flag(False)

    def _clear_displayed_quote_ui(self):
        self.quote_details_widget.clear_data()
        self.eprice_section_widget.clear_data()
        self.eprice_section_widget.refresh_structure() # Rebuild with fixed companies, clear values
        self.eps_section_widget.clear_data()
        self.pe_section_widget.clear_data()
        self.pe_section_widget.refresh_structure() # Rebuild with fixed companies, clear values
        self.eps_growth_chart_widget.clear_data()
        self.record_report_section_widget.clear_data()
        if hasattr(self, 'highlight_manager'): # Clear any active highlight
            self.highlight_manager.clear_active_highlight()

    def _display_quote(self, quote_name, is_new_quote=False):
        # _save_displayed_quote_data() should ideally not be needed here if all changes
        # are immediately captured by commands. If there are pending uncommitted changes
        # (e.g. from a line edit that hasn't lost focus), they should be committed first.
        # For now, we keep it to ensure data consistency before switching.
        self._save_displayed_quote_data()
        self._clear_displayed_quote_ui() 
        if hasattr(self, 'highlight_manager'): # Clear any active highlight before displaying new quote
            self.highlight_manager.clear_active_highlight()
        
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
        self.eps_growth_chart_widget.load_data(quote_data.get("eps", [])) # Load data into chart
        self.record_report_section_widget.load_data(quote_data.get("record", []))
        
        self.quote_selection_widget.set_quote_name_input(quote_name)        
        # Load sectors from the quote data in XML.
        self.sectors_section_widget.load_sectors_from_db(quote_name, self.all_quotes_data)
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
        # For "record" data, current_quote_data_entry["record"] (which is a reference to
        # self.all_quotes_data[self.selected_quote_name]["record"]) should already contain
        # the complete list of records managed by Add/RemoveRecordReportCommands.
        # The RecordReportSectionWidget.get_data() only returns the displayed subset.
        # So, we don't overwrite current_quote_data_entry["record"] here.

    def handle_select_quote_button(self, quote_name_to_select): # Parameter from signal
        if not quote_name_to_select:
            QMessageBox.information(self, "Info", "Please enter a quote name to select.")
            return
        if quote_name_to_select == self.selected_quote_name: return
        if quote_name_to_select in self.all_quotes_data:
            self._display_quote(quote_name_to_select, is_new_quote=False) # Not a new quote, just selecting existing
        else:
            QMessageBox.warning(self, "Not Found", f"Quote '{quote_name_to_select}' not found. Use 'Add New Quote' to create it.")

    def handle_add_new_quote_button(self, new_quote_name): # Parameter from signal
        if not new_quote_name:
            QMessageBox.warning(self, "Input Error", "Please enter a name for the new quote in the text box.")
            return
        
        # If quote already exists, display it and return (no command needed for just displaying)
        if new_quote_name in self.all_quotes_data:
            QMessageBox.information(self, "Exists", f"Quote '{new_quote_name}' already exists. Displaying it now.")
            if self.selected_quote_name != new_quote_name: # Only switch if not already selected
                self._display_quote(new_quote_name, is_new_quote=False)
            return

        self._save_displayed_quote_data() 
        
        quote_data_to_add = {
            "name": new_quote_name, "price": "",
            "e_price": [], "eps": [], "pe": [], "record": []
        }
        
        cmd = AddQuoteCommand(self.all_quotes_data, new_quote_name, quote_data_to_add, self)
        self.execute_command(cmd)
        
        # After command execution, all_quotes_data is updated. Now display the new quote.
        self._display_quote(new_quote_name, is_new_quote=True) # is_new_quote=True for initial editability of name
        QMessageBox.information(self, "Quote Added", f"New quote '{new_quote_name}' added and displayed. Fill in its details.")

    def handle_remove_displayed_quote_button(self):
        if not self.selected_quote_name:
            QMessageBox.warning(self, "No Quote", "No quote is currently displayed to remove.")
            return
        
        quote_to_remove = self.selected_quote_name
        removed_quote_data = self.all_quotes_data.get(quote_to_remove) # Get data before removal for undo

        if not removed_quote_data: # Should not happen if selected_quote_name is valid
            QMessageBox.critical(self, "Error", "Could not find data for the selected quote to remove.")
            return

        reply = QMessageBox.question(self, "Confirm Removal",
                                     f"Are you sure you want to remove the quote '{self.selected_quote_name}'?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            cmd = RemoveQuoteCommand(self.all_quotes_data, quote_to_remove, removed_quote_data, self)
            self.execute_command(cmd)

            # After command execution, all_quotes_data is updated.
            # Now handle UI: clear or select another quote.
            self.selected_quote_name = None
            self._clear_displayed_quote_ui()
            self.quote_selection_widget.clear_input()
            self._set_displayed_quote_ui_enabled(False)
            QMessageBox.information(self, "Removed", f"The quote '{quote_to_remove}' has been removed.")

            # Optionally, display the first remaining quote
            if self.all_quotes_data:
                first_remaining_quote = next(iter(self.all_quotes_data))
                self._display_quote(first_remaining_quote, is_new_quote=False)
            else:
                self._set_displayed_quote_ui_enabled(False) # Ensure UI is disabled if no quotes left

    def load_initial_data(self):
        initial_root_date = data_utils.get_default_working_date()
        if initial_root_date.isValid():
            self.root_date_edit.setDate(initial_root_date)
            self._current_root_date_str = initial_root_date.toString("MM/dd/yyyy")
            # Initialize the date in all_quotes_data if it's not there
            if "date" not in self.all_quotes_data:
                self.all_quotes_data["date"] = self._current_root_date_str

    def closeEvent(self, event):
        if self.command_manager.can_undo(): # Check if there are unsaved changes by checking the undo stack
            reply = QMessageBox.question(self, "Unsaved Changes",
                                         "There are unsaved changes. Do you want to save before exiting?",
                                         QMessageBox.StandardButton.Save | 
                                         QMessageBox.StandardButton.Discard | 
                                         QMessageBox.StandardButton.Cancel)
            if reply == QMessageBox.StandardButton.Save:
                if not self.save_xml_file(): # If save fails (e.g., user cancels Save As)
                    event.ignore()
                    return
            elif reply == QMessageBox.StandardButton.Cancel:
                event.ignore()
                return
        # If Discard or Save was successful, proceed to save config and close
        data_utils.save_eprice_config(self.EPRICE_FIXED_COMPANIES) 
        super().closeEvent(event)


    def open_xml_file(self): # sourcery skip: extract-method
        file_path, root_date_qdate, all_quotes_data_dict = self.file_manager.open_file()
        if file_path:
            self._load_data_into_ui(root_date_qdate, all_quotes_data_dict)
            self._set_dirty_flag(False) # Freshly loaded file is not dirty
            self.command_manager.clear_stacks()
            self.quote_filter_widget.all_quotes_data_provider = all_quotes_data_dict
            self.quote_filter_widget._on_sector_changed(None) # Refresh sectors in the filter widget

    def _load_data_into_ui(self, root_date_qdate, all_quotes_data_dict):
        """Helper to load parsed data into the UI elements."""
        self.clear_all_fields() 

        self.root_date_edit.setDate(root_date_qdate)
        self._current_root_date_str = root_date_qdate.toString("MM/dd/yyyy")
        self.all_quotes_data = all_quotes_data_dict if all_quotes_data_dict is not None else {}
        # Ensure global date is in all_quotes_data if not present from XML
        if "date" not in self.all_quotes_data:
            self.all_quotes_data["date"] = self._current_root_date_str

        first_quote_name_loaded = None
        if self.all_quotes_data:
            first_quote_name_loaded = next(iter(self.all_quotes_data), None) 
        
        if first_quote_name_loaded:
            self._display_quote(first_quote_name_loaded, is_new_quote=False) # Display the first quote
        else: 
            self._set_displayed_quote_ui_enabled(False) 
        # Window title will be updated by _set_dirty_flag via open_xml_file

    def collect_data_for_xml(self): 
        self._save_displayed_quote_data() 
        
        # Initialize the structure for XML generation
        xml_output_data = {"quotes": []}
        
        # Get the global date directly from the UI element
        xml_output_data["date"] = self.root_date_edit.date().toString("MM/dd/yyyy")
        
        # Iterate over items in self.all_quotes_data
        for key, value in self.all_quotes_data.items():
            # If the key is "date", it's the global date string stored in self.all_quotes_data,
            # skip it as the XML date is already sourced from root_date_edit.
            if key == "date":
                continue
            
            # Otherwise, the key is a quote_name and the value should be the quote_data_dict
            quote_name = key
            quote_data_dict = value
            
            # Ensure the name in the dict matches the key, or use the key if name is missing
            if isinstance(quote_data_dict, dict):
                if "name" not in quote_data_dict or not quote_data_dict["name"]:
                    quote_data_dict["name"] = quote_name # Ensure consistency
                xml_output_data["quotes"].append(quote_data_dict)
            else:
                # This case should ideally not be reached if only "date" and quote dicts are in self.all_quotes_data
                print(f"Warning: Skipping unexpected data type for key '{quote_name}' in collect_data_for_xml. Found type: {type(quote_data_dict)}")
                
        return xml_output_data
    
    def _perform_save_operation(self, save_function_callable):
        """
        Helper method to perform a save operation (save or save as)
        and handle post-save UI updates.
        Args:
            save_function_callable: The FileManager method to call (e.g., self.file_manager.save_file)
        Returns:
            bool: True if save was successful, False otherwise.
        """
        if save_function_callable(self.collect_data_for_xml):
            self.command_manager.clear_stacks() # Consider saved state as clean for undo
            self._set_dirty_flag(False)
            return True
        return False # Return False if save_function_callable failed

    def save_xml_file(self):
        return self._perform_save_operation(self.file_manager.save_file)

    def save_xml_file_as(self):
        return self._perform_save_operation(self.file_manager.save_file_as)

    def undo(self):
        command = self.command_manager.undo()
        if not command:
            return

        # CommandManager has already called command.unexecute() and updated stacks/dirty flag/log.
        # Now, handle editor-specific UI updates based on the command type.

        # Update the internal state only if it's a root date command
        if isinstance(command, ChangeRootDateCommand):
            self._current_root_date_str = command.old_date_qdate.toString("MM/dd/yyyy")
        
        # After command.unexecute(), the data model is reverted.
        # For quote name changes, the command itself handles the key change in all_quotes_data.
        # We now need to update the editor's selected_quote_name if it was affected.
        if isinstance(command, ChangeQuoteDetailCommand):
            # command.unexecute() already called quote_details_widget.update_field_value
            if command.field_name == "name":
                # If the selected quote was the one whose name was 'command.new_value' (before unexecute),
                # it means its name has now been reverted to 'command.old_value'.
                if self.selected_quote_name == command.new_value:
                    self.selected_quote_name = command.old_value
                    self.quote_selection_widget.set_quote_name_input(command.old_value)
        elif isinstance(command, ChangeEPriceValueCommand):
            # Ensure the EPriceSectionWidget's internal state and UI are correct
            command.eprice_section_widget.update_company_value(command.company_name, command.old_value, from_command=True)
        elif isinstance(command, ChangePEValueCommand):
            # Ensure the PESectionWidget's internal state and UI are correct
            command.pe_section_widget.update_company_value(command.company_name, command.old_value, from_command=True)
        elif isinstance(command, ChangeEPSValueCommand):
            command.eps_section_widget.update_company_eps_field(
                command.year_name, command.company_name, command.field_name, command.old_value, from_command=True
            )
        elif isinstance(command, AddQuoteCommand):
            # Quote was removed by unexecute. If it was the selected one, clear UI.
            if self.selected_quote_name == command.quote_name:
                self.selected_quote_name = None
                self._clear_displayed_quote_ui()
                self.quote_selection_widget.clear_input()
                self._set_displayed_quote_ui_enabled(False)
                if self.all_quotes_data: # Optionally, select another quote
                    self._display_quote(next(iter(self.all_quotes_data)), is_new_quote=False)
        elif isinstance(command, RemoveQuoteCommand):
            # Quote was re-added by unexecute. Display it.
            self._display_quote(command.quote_name_to_remove, is_new_quote=False) # is_new_quote=False as it's restored

        elif isinstance(command, AddEPSYearCommand): # Undo an add = remove
            # Command's unexecute handles data model and UI
            pass
        elif isinstance(command, RemoveEPSYearCommand): # Undo a remove = add
            # Command's unexecute handles data model and UI
            pass
        elif isinstance(command, AddRecordReportCommand):
            # Command's unexecute handles data model and UI removal
            pass
        elif isinstance(command, RemoveRecordReportCommand): # Undo a remove = re-add
            # Command's unexecute calls load_data on the record_widget, so UI is updated.
            pass
        elif isinstance(command, ChangeRecordReportDetailCommand):
            # Command's unexecute calls update_report_entry_detail on the widget
            pass
        elif isinstance(command, ChangeEPSYearDisplayCommand):
            # Command's unexecute handles updating widget's list and calling _update_visible_eps_years
            pass
        elif isinstance(command, ChangeEPSCompaniesForYearDisplayCommand):
            # Command's unexecute handles updating widget's year_entry and calling _update_visible_eps_companies_for_year
            pass
        elif isinstance(command, ChangeEPriceFixedCompaniesCommand):
            # Command's unexecute handles reverting EPRICE_FIXED_COMPANIES,
            # calling _load_eprice_config_and_update_ui(), and saving config.
            pass
        # _update_undo_redo_actions_state, _log_history, _set_dirty_flag already called by command_manager

    def redo(self): # sourcery skip: extract-method
        command = self.command_manager.redo()
        if not command:
            return
        
        # CommandManager has already called command.execute() and updated stacks/dirty flag/log.
        # Now, handle editor-specific UI updates based on the command type.

        # Update the internal state only if it's a root date command
        if isinstance(command, ChangeRootDateCommand):
            self._current_root_date_str = command.new_date_qdate.toString("MM/dd/yyyy")
        if isinstance(command, ChangeQuoteDetailCommand):
            # command.execute() already called quote_details_widget.update_field_value
            if command.field_name == "name":
                # If the selected quote was the one whose name was 'command.old_value' (before execute),
                # it means its name has now been changed to 'command.new_value'.
                if self.selected_quote_name == command.old_value:
                    self.selected_quote_name = command.new_value
                    self.quote_selection_widget.set_quote_name_input(command.new_value)
        elif isinstance(command, ChangeEPriceValueCommand):
            # Ensure the EPriceSectionWidget's internal state and UI are correct
            command.eprice_section_widget.update_company_value(command.company_name, command.new_value, from_command=True)
        elif isinstance(command, ChangePEValueCommand):
            # Ensure the PESectionWidget's internal state and UI are correct
            command.pe_section_widget.update_company_value(command.company_name, command.new_value, from_command=True)
        elif isinstance(command, ChangeEPSValueCommand):
            command.eps_section_widget.update_company_eps_field(
                command.year_name, command.company_name, command.field_name, command.new_value, from_command=True
            )
        elif isinstance(command, AddQuoteCommand):
            # Quote was re-added by execute. Display it.
            self._display_quote(command.quote_name, is_new_quote=True) # is_new_quote=True as it's newly added by redo
        elif isinstance(command, RemoveQuoteCommand):
            # Quote was removed by execute. If it was the selected one, clear UI.
            if self.selected_quote_name == command.quote_name_to_remove:
                self.selected_quote_name = None
                self._clear_displayed_quote_ui()
                self.quote_selection_widget.clear_input()
                self._set_displayed_quote_ui_enabled(False)
                if self.all_quotes_data: # Optionally, select another quote
                    self._display_quote(next(iter(self.all_quotes_data)), is_new_quote=False)
        
        elif isinstance(command, AddEPSYearCommand): # Redo an add
            # Command's execute handles data model and UI
            pass
        elif isinstance(command, RemoveEPSYearCommand): # Redo a remove
            # Command's execute handles data model and UI
            pass
        elif isinstance(command, AddRecordReportCommand):
            # Command's execute calls load_data on the record_widget, so UI is updated.
            pass
        elif isinstance(command, RemoveRecordReportCommand):
            # Command's execute handles data model and UI removal.
            pass # UI is handled by command
        elif isinstance(command, ChangeRecordReportDetailCommand):
            # Command's execute calls update_report_entry_detail on the widget
            pass
        elif isinstance(command, ChangeEPSYearDisplayCommand):
            # Command's execute handles updating widget's list and calling _update_visible_eps_years
            pass
        elif isinstance(command, ChangeEPSCompaniesForYearDisplayCommand):
            # Command's execute handles updating widget's year_entry and calling _update_visible_eps_companies_for_year
            pass
        elif isinstance(command, ChangeEPriceFixedCompaniesCommand):
            # Command's execute handles updating EPRICE_FIXED_COMPANIES,
            # calling _load_eprice_config_and_update_ui(), and saving config.
            pass
        # _update_undo_redo_actions_state, _log_history, _set_dirty_flag already called by command_manager

def main():
    app = QApplication(sys.argv)
    editor = XmlReportEditor()
    editor.showMaximized() 
    sys.exit(app.exec())

if __name__ == '__main__':
    main()

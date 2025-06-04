# t:\Work\xml_input_ui\tests\test_editor_action_handler.py
import unittest
from unittest.mock import MagicMock, patch, ANY, call
from PyQt6.QtCore import QDate
from editor_action_handler import EditorActionHandler
# Import Command classes that are instantiated by the handler
from commands import (
    ChangeRootDateCommand, ChangeQuoteDetailCommand, ChangeEPriceValueCommand,
    ChangePEValueCommand, ChangeEPSValueCommand,
    AddEPSYearCommand, RemoveEPSYearCommand, ChangeEPSYearDisplayCommand,
    ChangeEPSCompaniesForYearDisplayCommand, AddRecordReportCommand,
    RemoveRecordReportCommand, ChangeRecordReportDetailCommand
)

# Patch the actual command classes with MagicMock (default behavior of @patch)
# Individual command patches will be applied at the method level for clarity and isolation.
# Patch ChangeRootDateCommand directly on the relevant test methods below
class TestEditorActionHandler(unittest.TestCase):
    def setUp(self):
        self.mock_editor = MagicMock()
        # Simulate the editor's state
        self.mock_editor.all_quotes_data = {
            "AAPL": {"name": "AAPL", "price": "170.0", "e_price": [], "eps": [], "pe": [], "record": []},
            "date": "10/26/2023" # Simulate initial date
        }
        self.mock_editor._current_root_date_str = "10/26/2023"
        self.mock_editor.selected_quote_name = "AAPL"
        self.mock_editor.EPRICE_FIXED_COMPANIES = ["VCSC", "SSI"] # Simulate fixed companies list

        # Mocks for UI widgets referenced by the handler
        self.mock_editor.root_date_edit = MagicMock()
        self.mock_editor.quote_details_widget = MagicMock()
        self.mock_editor.eprice_section_widget = MagicMock()
        self.mock_editor.pe_section_widget = MagicMock()
        self.mock_editor.eps_section_widget = MagicMock()
        self.mock_editor.record_report_section_widget = MagicMock()
        self.mock_editor.eps_growth_chart_widget = MagicMock()
        self.mock_editor.quote_selection_widget = MagicMock() # Needed for name change handler

        # For testing handle_eps_companies_for_year_display_change_requested
        self.mock_editor.eps_section_widget.eps_year_entries = [
            {"year_name": "2023", "widget": MagicMock(), "selected_companies_to_display_for_year": ["MSFT"]}
        ]
        # For testing record report detail change
        self.mock_editor._find_data_model_for_record_report = MagicMock()


        self.handler = EditorActionHandler(self.mock_editor)

    # --- Root Date Handlers ---
    # Patch ChangeRootDateCommand here specifically for this test
    @patch('editor_action_handler.ChangeRootDateCommand')
    def test_handle_root_date_changed_by_calendar(self, MockChangeRootDateCommand):
        new_qdate = QDate(2023, 10, 27)
        mock_cmd_instance = MockChangeRootDateCommand.return_value

        self.handler.handle_root_date_changed_by_calendar(new_qdate)

        MockChangeRootDateCommand.assert_called_once_with(
            self.mock_editor.root_date_edit,
            self.mock_editor.all_quotes_data,
            "10/26/2023", # Expect the actual old date string before the change
            "10/27/2023"
        )
        self.mock_editor.execute_command.assert_called_once_with(mock_cmd_instance)
        self.assertEqual(self.mock_editor._current_root_date_str, "10/27/2023")

    # Patch ChangeRootDateCommand here specifically for this test
    @patch('editor_action_handler.ChangeRootDateCommand')
    def test_handle_root_date_changed(self, MockChangeRootDateCommand):
        self.mock_editor.root_date_edit.date.return_value = QDate(2023, 10, 27) # Simulate new date from widget
        mock_cmd_instance = MockChangeRootDateCommand.return_value

        self.handler.handle_root_date_changed()

        MockChangeRootDateCommand.assert_called_once_with(
            self.mock_editor.root_date_edit,
            self.mock_editor.all_quotes_data,
            "10/26/2023", # Explicitly expect the old date string
            "10/27/2023"
        )
        self.mock_editor.execute_command.assert_called_once_with(mock_cmd_instance)
        self.assertEqual(self.mock_editor._current_root_date_str, "10/27/2023")

    # Patch ChangeRootDateCommand here specifically for this test
    @patch('editor_action_handler.ChangeRootDateCommand')
    def test_handle_root_date_changed_no_date_key(self, MockChangeRootDateCommand):
        # Test when "date" key is missing in all_quotes_data
        del self.mock_editor.all_quotes_data["date"] # Remove date key
        self.mock_editor.root_date_edit.date.return_value = QDate(2023, 10, 27) # New date
        mock_cmd_instance = MockChangeRootDateCommand.return_value

        self.handler.handle_root_date_changed()

        self.assertIn("date", self.mock_editor.all_quotes_data) # Date key should be added
        self.assertEqual(self.mock_editor.all_quotes_data["date"], "10/26/2023") # With old value
        MockChangeRootDateCommand.assert_called_once_with(
            self.mock_editor.root_date_edit,
            self.mock_editor.all_quotes_data,
            "10/26/2023",
            "10/27/2023"
        )
        self.mock_editor.execute_command.assert_called_once_with(mock_cmd_instance)
        self.assertEqual(self.mock_editor._current_root_date_str, "10/27/2023")

    # Remove the unnecessary patches for commands not used by the handler
    # @patch('editor_action_handler.RemoveQuoteCommand', new=MockCommand) # REMOVE
    # @patch('editor_action_handler.AddQuoteCommand', new=MockCommand)    # REMOVE



    # --- Quote Details Handlers ---
    # Patch ChangeQuoteDetailCommand here specifically for this test
    @patch('editor_action_handler.ChangeQuoteDetailCommand')
    def test_handle_quote_name_changed(self, MockChangeQuoteDetailCommand):
        self.mock_editor.selected_quote_name = "AAPL"
        old_name = "AAPL"
        new_name = "AAPL_NEW"
        mock_cmd_instance = MockChangeQuoteDetailCommand.return_value

        self.handler.handle_quote_name_changed(old_name, new_name)

        MockChangeQuoteDetailCommand.assert_called_once_with(
            self.mock_editor.quote_details_widget,
            self.mock_editor.all_quotes_data,
            old_name, "name", old_name, new_name
        )
        self.mock_editor.execute_command.assert_called_once_with(mock_cmd_instance)
        # Assert editor state updated
        self.assertEqual(self.mock_editor.selected_quote_name, "AAPL_NEW")
        self.mock_editor.quote_selection_widget.set_quote_name_input.assert_called_once_with("AAPL_NEW")

    @patch('editor_action_handler.QMessageBox.warning')
    @patch('editor_action_handler.ChangeQuoteDetailCommand')
    def test_handle_quote_name_changed_empty_new_name(self, MockChangeCmd, mock_warning):
        self.mock_editor.selected_quote_name = "AAPL"
        old_name = "AAPL"
        self.handler.handle_quote_name_changed(old_name, "") # Empty new name
        mock_warning.assert_called_once()
        self.mock_editor.quote_details_widget.update_field_value.assert_called_once_with("name", old_name, from_command=False)
        MockChangeCmd.assert_not_called()

    @patch('editor_action_handler.ChangeQuoteDetailCommand')
    def test_handle_quote_price_changed(self, MockChangeQuoteDetailCommand):
        self.mock_editor.selected_quote_name = "AAPL"
        old_price = "170.0"
        new_price = "175.0"
        mock_cmd_instance = MockChangeQuoteDetailCommand.return_value

        self.handler.handle_quote_price_changed(old_price, new_price)

        MockChangeQuoteDetailCommand.assert_called_once_with(
            self.mock_editor.quote_details_widget,
            self.mock_editor.all_quotes_data,
            "AAPL", "price", old_price, new_price
        )
        self.mock_editor.execute_command.assert_called_once_with(mock_cmd_instance)

    # --- E-Price Handlers ---
    @patch('editor_action_handler.ChangeEPriceValueCommand')
    def test_handle_eprice_value_changed(self, MockChangeEPriceValueCommand):
        self.mock_editor.selected_quote_name = "AAPL"
        company_name = "VCSC"
        old_value = "4.5"
        new_value = "5.0"
        mock_cmd_instance = MockChangeEPriceValueCommand.return_value

        self.handler.handle_eprice_value_changed(company_name, old_value, new_value)

        MockChangeEPriceValueCommand.assert_called_once_with(
            self.mock_editor.eprice_section_widget,
            self.mock_editor.all_quotes_data,
            "AAPL", company_name, old_value, new_value
        )
        self.mock_editor.execute_command.assert_called_once_with(mock_cmd_instance)

    # --- PE Handlers ---
    @patch('editor_action_handler.ChangePEValueCommand')
    def test_handle_pe_value_changed(self, MockChangePEValueCommand):
        self.mock_editor.selected_quote_name = "AAPL"
        company_name = "MSFT"
        old_value = "25.0"
        new_value = "27.0"
        mock_cmd_instance = MockChangePEValueCommand.return_value

        self.handler.handle_pe_value_changed(company_name, old_value, new_value)

        MockChangePEValueCommand.assert_called_once_with(
            self.mock_editor.pe_section_widget,
            self.mock_editor.all_quotes_data,
            "AAPL", company_name, old_value, new_value
        )
        self.mock_editor.execute_command.assert_called_once_with(mock_cmd_instance)

    # --- EPS Handlers ---
    @patch('editor_action_handler.ChangeEPSValueCommand')
    def test_handle_eps_value_changed(self, MockChangeEPSValueCommand):
        self.mock_editor.selected_quote_name = "AAPL"
        year_name = "2024"
        company_name = "MSFT"
        field_name = "value"
        old_value = "1.0"
        new_value = "1.1"
        mock_cmd_instance = MockChangeEPSValueCommand.return_value

        self.handler.handle_eps_value_changed(year_name, company_name, field_name, old_value, new_value)

        MockChangeEPSValueCommand.assert_called_once_with(
            self.mock_editor.eps_section_widget,
            self.mock_editor.all_quotes_data,
            "AAPL", year_name, company_name, field_name, old_value, new_value
        )
        self.mock_editor.execute_command.assert_called_once_with(mock_cmd_instance)

    @patch('editor_action_handler.AddEPSYearCommand')
    def test_handle_eps_year_add_requested(self, MockAddEPSYearCommand):
        self.mock_editor.selected_quote_name = "AAPL"
        year_name = "2025"
        mock_cmd_instance = MockAddEPSYearCommand.return_value

        self.handler.handle_eps_year_add_requested(year_name)

        MockAddEPSYearCommand.assert_called_once_with(
            self.mock_editor.eps_section_widget,
            self.mock_editor.all_quotes_data,
            "AAPL", year_name, initial_companies_data=None
        )
        self.mock_editor.execute_command.assert_called_once_with(mock_cmd_instance)

    @patch('editor_action_handler.RemoveEPSYearCommand')
    def test_handle_eps_year_remove_requested(self, MockRemoveEPSYearCommand):
        self.mock_editor.selected_quote_name = "AAPL"
        year_to_remove = "2024"
        # Simulate data model having the year
        removed_year_data_model = {"name": year_to_remove, "companies": []}
        self.mock_editor.all_quotes_data["AAPL"]["eps"] = [removed_year_data_model]
        mock_cmd_instance = MockRemoveEPSYearCommand.return_value

        self.handler.handle_eps_year_remove_requested(year_to_remove)

        MockRemoveEPSYearCommand.assert_called_once_with(
            self.mock_editor.eps_section_widget,
            self.mock_editor.all_quotes_data,
            "AAPL", year_to_remove, removed_year_data_model
        )
        self.mock_editor.execute_command.assert_called_once_with(mock_cmd_instance)

    @patch('editor_action_handler.RemoveEPSYearCommand')
    @patch('editor_action_handler.QMessageBox.warning')
    def test_handle_eps_year_remove_requested_no_quote_data_or_eps(self, mock_warning, MockRemoveCmd):
        # Scenario 1: quote_data is None (quote not in all_quotes_data)
        self.mock_editor.selected_quote_name = "NON_EXISTENT"
        self.mock_editor.all_quotes_data = {}
        self.handler.handle_eps_year_remove_requested("2023")
        MockRemoveCmd.assert_not_called()
        mock_warning.assert_not_called() # No warning for missing quote/eps key

        # Scenario 2: "eps" key missing
        self.mock_editor.selected_quote_name = "AAPL"
        self.mock_editor.all_quotes_data = {"AAPL": {"name": "AAPL"}} # No "eps" key
        self.handler.handle_eps_year_remove_requested("2023")
        MockRemoveCmd.assert_not_called()
        mock_warning.assert_not_called() # No warning for missing quote/eps key

    @patch('editor_action_handler.RemoveEPSYearCommand')
    @patch('editor_action_handler.QMessageBox.warning') # To check for warnings
    def test_handle_eps_year_remove_requested_year_not_found_in_model(self, mock_warning, MockRemoveEPSYearCommand):
        self.mock_editor.selected_quote_name = "AAPL"
        year_to_remove = "2024"
        # Simulate data model NOT having the year
        self.mock_editor.all_quotes_data["AAPL"]["eps"] = [{"name": "2023", "companies": []}]

        self.handler.handle_eps_year_remove_requested(year_to_remove)

        mock_warning.assert_called_once_with(
            self.mock_editor, "Error", f"Could not find EPS year '{year_to_remove}' in data model to remove."
        )
        MockRemoveEPSYearCommand.assert_not_called()
        self.mock_editor.execute_command.assert_not_called()


    @patch('editor_action_handler.ChangeEPSYearDisplayCommand')
    def test_handle_eps_year_display_change_requested(self, MockChangeEPSYearDisplayCommand):
        self.mock_editor.selected_quote_name = "AAPL"
        old_years = ["2023"]
        new_years = ["2024", "2025"]
        mock_cmd_instance = MockChangeEPSYearDisplayCommand.return_value

        self.handler.handle_eps_year_display_change_requested(old_years, new_years)

        MockChangeEPSYearDisplayCommand.assert_called_once_with(
            self.mock_editor.eps_section_widget, old_years, new_years
        )
        self.mock_editor.execute_command.assert_called_once_with(mock_cmd_instance)

    @patch('editor_action_handler.ChangeEPSCompaniesForYearDisplayCommand')
    def test_handle_eps_companies_for_year_display_change_requested(self, MockChangeEPSCompaniesForYearDisplayCommand):
        self.mock_editor.selected_quote_name = "AAPL"
        year_name = "2023"
        old_companies = ["MSFT"]
        new_companies = ["GOOG", "MSFT"]
        mock_cmd_instance = MockChangeEPSCompaniesForYearDisplayCommand.return_value

        self.handler.handle_eps_companies_for_year_display_change_requested(year_name, old_companies, new_companies)

        MockChangeEPSCompaniesForYearDisplayCommand.assert_called_once_with(
            self.mock_editor.eps_section_widget, year_name, old_companies, new_companies # Ensure year_name is passed
        )
        self.mock_editor.execute_command.assert_called_once_with(mock_cmd_instance)

    @patch('commands.print') # Mock print in the command
    @patch('editor_action_handler.ChangeEPSCompaniesForYearDisplayCommand')
    def test_handle_eps_companies_for_year_display_change_requested_year_not_in_ui(self, MockCmd, mock_print_in_command):
        # Setup so the command's internal check for year_entry fails
        self.mock_editor.eps_section_widget.eps_year_entries = [] # No UI entries for any year
        self.mock_editor.selected_quote_name = "AAPL"
        mock_cmd_instance = MockCmd.return_value

        self.handler.handle_eps_companies_for_year_display_change_requested("MISSING_YEAR", ["A"], ["B"])
        # The handler itself doesn't check, but the command it creates will.
        # We assert the command is created. The command's test covers the print.
        MockCmd.assert_called_once_with(
             self.mock_editor.eps_section_widget, "MISSING_YEAR", ["A"], ["B"]
        )
        self.mock_editor.execute_command.assert_called_once_with(mock_cmd_instance)
        # We cannot easily assert the print from the command here without letting the command execute.
        # The test for ChangeEPSCompaniesForYearDisplayCommand covers the print.


    # --- Record Report Handlers ---
    # Patch AddRecordReportCommand here specifically for this test
    @patch('editor_action_handler.AddRecordReportCommand')
    @patch('data_utils.get_default_working_date') # To control the date
    def test_handle_record_report_add_requested(self, mock_get_date, MockAddRecordReportCommand):
        self.mock_editor.selected_quote_name = "AAPL"
        self.mock_editor.EPRICE_FIXED_COMPANIES = ["VCSC", "SSI"] # Ensure this is set
        mock_get_date.return_value = QDate(2024, 1, 15) # Simulate a date
        mock_cmd_instance = MockAddRecordReportCommand.return_value

        self.handler.handle_record_report_add_requested()

        expected_report_data = {
            "company": "VCSC", # First company from fixed list
            "date": "01/15/2024", # Mocked date
            "color": "default"
        }
        MockAddRecordReportCommand.assert_called_once_with(
            self.mock_editor.record_report_section_widget,
            self.mock_editor.all_quotes_data,
            "AAPL", expected_report_data, insert_at_index=0
        )
        self.mock_editor.execute_command.assert_called_once_with(mock_cmd_instance)

    # Patch RemoveRecordReportCommand here specifically for this test
    @patch('editor_action_handler.RemoveRecordReportCommand')
    def test_handle_record_report_remove_requested(self, MockRemoveRecordReportCommand):
        self.mock_editor.selected_quote_name = "AAPL"
        ui_entry_data_to_remove = {"current_company": "C1", "current_date": "d1", "current_color": "col1", "widget": MagicMock()}
        # Simulate data model having the matching report
        report_data_model_to_remove = {"company": "C1", "date": "d1", "color": "col1"}
        self.mock_editor.all_quotes_data["AAPL"]["record"] = [report_data_model_to_remove, {"company": "C2", "date": "d2", "color": "col2"}]
        original_index = 0 # Assuming it's the first one
        mock_cmd_instance = MockRemoveRecordReportCommand.return_value

        self.handler.handle_record_report_remove_requested(ui_entry_data_to_remove)

        MockRemoveRecordReportCommand.assert_called_once_with(
            self.mock_editor.record_report_section_widget,
            self.mock_editor.all_quotes_data,
            "AAPL", report_data_model_to_remove, ui_entry_data_to_remove, original_index
        )
        self.mock_editor.execute_command.assert_called_once_with(mock_cmd_instance)

    # Patch RemoveRecordReportCommand here specifically for this test
    @patch('editor_action_handler.RemoveRecordReportCommand')
    @patch('editor_action_handler.QMessageBox.warning')
    def test_handle_record_report_remove_requested_no_quote_or_record(self, mock_warning, MockRemoveCmd):
        ui_entry_data = {"current_company": "C1", "current_date": "d1", "current_color": "col1"}
        # Scenario 1: No selected quote
        self.mock_editor.selected_quote_name = None
        self.handler.handle_record_report_remove_requested(ui_entry_data)
        MockRemoveCmd.assert_not_called()
        mock_warning.assert_not_called()

        # Scenario 2: Selected quote has no "record" key
        self.mock_editor.selected_quote_name = "AAPL"
        self.mock_editor.all_quotes_data["AAPL"] = {"name": "AAPL"} # No "record"
        self.handler.handle_record_report_remove_requested(ui_entry_data)
        MockRemoveCmd.assert_not_called()
        mock_warning.assert_not_called()

    # Patch RemoveRecordReportCommand here specifically for this test
    @patch('editor_action_handler.RemoveRecordReportCommand')
    @patch('editor_action_handler.QMessageBox.warning')
    def test_handle_record_report_remove_requested_model_not_found(self, mock_warning, MockRemoveRecordReportCommand):
        self.mock_editor.selected_quote_name = "AAPL"
        ui_entry_data_to_remove = {"current_company": "C1", "current_date": "d1", "current_color": "col1", "widget": MagicMock()}
        # Simulate data model NOT having the matching report
        self.mock_editor.all_quotes_data["AAPL"]["record"] = [{"company": "C2", "date": "d2", "color": "col2"}]

        self.handler.handle_record_report_remove_requested(ui_entry_data_to_remove)

        mock_warning.assert_called_once_with(
            self.mock_editor, "Error", "Could not find the report entry in the data model to remove."
        )
        MockRemoveRecordReportCommand.assert_not_called()
        self.mock_editor.execute_command.assert_not_called()


    @patch('editor_action_handler.ChangeRecordReportDetailCommand')
    def test_handle_record_report_detail_changed(self, MockChangeRecordReportDetailCommand):
        self.mock_editor.selected_quote_name = "AAPL"
        ui_entry_ref = {"widget": MagicMock(), "current_company": "C1", "current_date": "d1", "current_color": "col1"}
        field_name = "company"
        old_value = "C1"
        new_value = "C1_NEW"
        # Simulate _find_data_model_for_record_report returning a valid reference
        data_model_ref = {"company": old_value, "date": "d1", "color": "col1"}
        self.mock_editor._find_data_model_for_record_report.return_value = data_model_ref
        mock_cmd_instance = MockChangeRecordReportDetailCommand.return_value

        self.handler.handle_record_report_detail_changed(ui_entry_ref, field_name, old_value, new_value)

        self.mock_editor._find_data_model_for_record_report.assert_called_once_with(
            self.mock_editor.all_quotes_data["AAPL"], ui_entry_ref, field_name, old_value
        )
        MockChangeRecordReportDetailCommand.assert_called_once_with(
            self.mock_editor.record_report_section_widget,
            self.mock_editor.all_quotes_data, # all_quotes_data is passed, though not strictly used by command
            "AAPL", data_model_ref, ui_entry_ref, field_name, old_value, new_value
        )
        self.mock_editor.execute_command.assert_called_once_with(mock_cmd_instance)

    # Patch ChangeRecordReportDetailCommand here specifically for this test
    @patch('editor_action_handler.ChangeRecordReportDetailCommand')
    @patch('editor_action_handler.QMessageBox.warning')
    def test_handle_record_report_detail_changed_model_not_found(self, mock_warning, MockChangeCmd):
        self.mock_editor.selected_quote_name = "AAPL"
        ui_entry_ref = {"widget": MagicMock(), "current_company": "C1", "current_date": "d1", "current_color": "col1"}
        field_name = "company"
        old_value = "C1"
        new_value = "C1_NEW"
        # Simulate _find_data_model_for_record_report returning None
        self.mock_editor._find_data_model_for_record_report.return_value = None

        self.handler.handle_record_report_detail_changed(ui_entry_ref, field_name, old_value, new_value)

        self.mock_editor._find_data_model_for_record_report.assert_called_once_with(
            self.mock_editor.all_quotes_data["AAPL"], ui_entry_ref, field_name, old_value
        )
        mock_warning.assert_called_once()
        self.mock_editor.record_report_section_widget.update_report_entry_detail.assert_called_once_with(
            ui_entry_ref, field_name, old_value, from_command=True # Revert UI
        )
        MockChangeCmd.assert_not_called()
        self.mock_editor.execute_command.assert_not_called()


    def test_handle_record_report_manual_refresh(self):
        self.mock_editor.selected_quote_name = "AAPL"
        self.mock_editor.all_quotes_data["AAPL"]["record"] = [{"company": "T1"}]
        self.mock_editor.record_report_section_widget.load_data = MagicMock()

        self.handler.handle_record_report_manual_refresh()
        self.mock_editor.record_report_section_widget.load_data.assert_called_once_with([{"company": "T1"}])
        self.mock_editor.record_report_section_widget.clear_data.assert_not_called()

    def test_handle_record_report_manual_refresh_no_quote(self):
        self.mock_editor.selected_quote_name = None
        self.mock_editor.record_report_section_widget.clear_data = MagicMock()
        self.mock_editor.record_report_section_widget.load_data = MagicMock()

        self.handler.handle_record_report_manual_refresh()
        self.mock_editor.record_report_section_widget.clear_data.assert_called_once()
        self.mock_editor.record_report_section_widget.load_data.assert_not_called()


    # --- Chart Handler ---
    def test_handle_eps_growth_data_changed_for_chart(self):
        self.mock_editor.selected_quote_name = "AAPL"
        self.mock_editor.eps_growth_chart_widget._selected_year_for_chart = "2023"
        year_name_changed = "2023" # Simulate the same year being changed
        mock_eps_data = [{"name": "2023", "companies": []}]
        self.mock_editor.all_quotes_data["AAPL"]["eps"] = mock_eps_data
        self.mock_editor.eps_growth_chart_widget.load_data = MagicMock()
        self.mock_editor.eps_growth_chart_widget.update_chart = MagicMock()

        self.handler.handle_eps_growth_data_changed_for_chart(year_name_changed)
        self.mock_editor.eps_growth_chart_widget.load_data.assert_called_once_with(mock_eps_data) # Should reload all eps data
        self.mock_editor.eps_growth_chart_widget.update_chart.assert_called_once_with(year_name_changed)

    def test_handle_eps_growth_data_changed_for_chart_no_quote(self):
        self.mock_editor.selected_quote_name = None
        self.mock_editor.eps_growth_chart_widget.load_data = MagicMock()
        self.mock_editor.eps_growth_chart_widget.update_chart = MagicMock()

        self.handler.handle_eps_growth_data_changed_for_chart("2023")
        self.mock_editor.eps_growth_chart_widget.load_data.assert_not_called()
        self.mock_editor.eps_growth_chart_widget.update_chart.assert_not_called()

    def test_handle_eps_growth_data_changed_for_chart_different_year(self):
        self.mock_editor.selected_quote_name = "AAPL"
        self.mock_editor.eps_growth_chart_widget._selected_year_for_chart = "2023"
        year_name_changed = "2024" # Simulate a different year being changed
        mock_eps_data = [{"name": "2023", "companies": []}, {"name": "2024", "companies": []}]
        self.mock_editor.all_quotes_data["AAPL"]["eps"] = mock_eps_data
        self.mock_editor.eps_growth_chart_widget.load_data = MagicMock()
        self.mock_editor.eps_growth_chart_widget.update_chart = MagicMock()

        self.handler.handle_eps_growth_data_changed_for_chart(year_name_changed)
        # Should still load all data but not update the chart if the changed year isn't the selected one
        self.mock_editor.eps_growth_chart_widget.load_data.assert_not_called()
        self.mock_editor.eps_growth_chart_widget.update_chart.assert_not_called()

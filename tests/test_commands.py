# t:\Work\xml_input_ui\tests\test_commands.py
import unittest
import copy # Import the copy module for deepcopy
from unittest.mock import MagicMock, patch, call
from commands import (
    Command, ChangeRootDateCommand, ChangeQuoteDetailCommand, AddQuoteCommand,
    RemoveQuoteCommand, ChangeEPriceValueCommand, ChangePEValueCommand,
    ChangeEPSValueCommand, AddEPSYearCommand, RemoveEPSYearCommand,
    ChangeEPSYearDisplayCommand, ChangeEPSCompaniesForYearDisplayCommand,
    AddRecordReportCommand, RemoveRecordReportCommand, ChangeRecordReportDetailCommand,
    ChangeEPriceFixedCompaniesCommand
)
from PyQt6.QtCore import QDate

# Minimal concrete command for testing base Command class features
class ConcreteTestCommand(Command):
    def execute(self):
        pass
    def unexecute(self):
        pass

class TestCommands(unittest.TestCase):
    def setUp(self):
        # Mock data structures
        self.mock_all_quotes_data = {
            "AAPL": {"name": "AAPL", "price": "170.0", "e_price": [], "eps": [], "pe": [], "record": []},
            "GOOG": {"name": "GOOG", "price": "130.0", "e_price": [], "eps": [], "pe": [], "record": []},
            "date": "10/26/2023"
        }
        self.mock_editor_ref = MagicMock()
        self.mock_editor_ref.EPRICE_FIXED_COMPANIES = ["VCSC", "SSI"]
        # Add a mock method needed by AddEPSYearCommand for sorting
        self.mock_editor_ref.eps_section_widget = MagicMock()
        self.mock_editor_ref.eps_section_widget._get_eps_year_sort_key = MagicMock(side_effect=lambda x: int(x) if x.isdigit() else 0)


        # Mocks for UI widgets
        self.mock_date_edit_widget = MagicMock()
        self.mock_quote_details_widget = MagicMock()
        self.mock_eprice_section_widget = MagicMock()
        self.mock_pe_section_widget = MagicMock()
        self.mock_eps_section_widget = MagicMock()
        self.mock_record_widget = MagicMock()
        self.mock_eps_section_widget.eps_year_entries = [] # Initialize for tests

    def test_command_base_str(self):
        cmd_with_desc = ConcreteTestCommand(description="Test Desc")
        self.assertEqual(str(cmd_with_desc), "Test Desc")
        cmd_no_desc = ConcreteTestCommand() # No description
        self.assertEqual(str(cmd_no_desc), "ConcreteTestCommand") # Should return class name

    def test_change_root_date_command(self):
        old_date_str = "10/26/2023"
        new_date_str = "10/27/2023"
        old_date_qdate = QDate.fromString(old_date_str, "MM/dd/yyyy")
        new_date_qdate = QDate.fromString(new_date_str, "MM/dd/yyyy")

        cmd = ChangeRootDateCommand(self.mock_date_edit_widget, self.mock_all_quotes_data, old_date_str, new_date_str)

        # Test execute
        cmd.execute()
        self.assertEqual(self.mock_all_quotes_data["date"], new_date_str)
        self.mock_date_edit_widget.assert_has_calls([call.blockSignals(True), call.setDate(new_date_qdate), call.blockSignals(False)])

        self.mock_date_edit_widget.blockSignals.reset_mock()
        self.mock_date_edit_widget.setDate.reset_mock()

        # Test unexecute
        cmd.unexecute()
        self.assertEqual(self.mock_all_quotes_data["date"], old_date_str)
        self.mock_date_edit_widget.assert_has_calls([call.blockSignals(True), call.setDate(old_date_qdate), call.blockSignals(False)])

    def test_change_quote_detail_command_name(self):
        old_name = "AAPL"
        new_name = "AAPL_NEW"
        field = "name"

        # Store initial state of the original data to verify it's not changed
        # as the command operates on a copy.
        initial_original_data = {
            k: v.copy() if isinstance(v, dict) else v 
            for k, v in self.mock_all_quotes_data.items()
        }
        original_price = self.mock_all_quotes_data[old_name]["price"]

        # For name change, quote_name_key is the old_name
        # Command is given a copy of the data.
        # quote_name_key = old_name (key to find the item)
        # old_value_for_field = old_name (the actual old name string)
        # new_value_for_field = new_name (the actual new name string)
        cmd = ChangeQuoteDetailCommand(
            self.mock_quote_details_widget, 
            copy.deepcopy(self.mock_all_quotes_data), # Command gets a deep copy
            old_name,  # quote_name_key
            field, 
            old_name,  # old_value (of the 'name' field)
            new_name   # new_value (for the 'name' field)
        )

        # --- Test execute ---
        cmd.execute()

        # Assertions on the command's internal data (cmd.all_quotes_data_ref)
        self.assertIn(new_name, cmd.all_quotes_data_ref, "New key should be in command's data after execute")
        self.assertNotIn(old_name, cmd.all_quotes_data_ref, "Old key should NOT be in command's data after execute")
        self.assertEqual(cmd.all_quotes_data_ref[new_name]["name"], new_name, "Name field under new key should be updated")
        self.assertEqual(cmd.all_quotes_data_ref[new_name]["price"], original_price, "Other data (price) should be preserved under new key")
        
        # Assert that the original self.mock_all_quotes_data is unchanged
        self.assertEqual(self.mock_all_quotes_data, initial_original_data, "Original data should not be modified by execute")

        # UI update check
        self.mock_quote_details_widget.update_field_value.assert_called_once_with(field, new_name, from_command=True)
        self.mock_quote_details_widget.update_field_value.reset_mock()

        # --- Test unexecute ---
        cmd.unexecute()
        self.assertIn(old_name, cmd.all_quotes_data_ref, "Old key should be restored in command's data after unexecute")
        self.assertNotIn(new_name, cmd.all_quotes_data_ref, "New key should NOT be in command's data after unexecute")
        self.assertEqual(cmd.all_quotes_data_ref[old_name]["name"], old_name, "Name field under old key should be restored")
        self.assertEqual(cmd.all_quotes_data_ref[old_name]["price"], original_price, "Other data (price) should be preserved under old key after unexecute")

        # Assert that the original self.mock_all_quotes_data is still unchanged
        self.assertEqual(self.mock_all_quotes_data, initial_original_data, "Original data should not be modified by unexecute")

        # UI update check
        self.mock_quote_details_widget.update_field_value.assert_called_once_with(field, old_name, from_command=True)

    def test_change_quote_detail_command_price(self):
        quote_name_key = "AAPL"
        field = "price"
        old_value = "170.0"
        new_value = "175.0"
        cmd = ChangeQuoteDetailCommand(self.mock_quote_details_widget, self.mock_all_quotes_data, quote_name_key, field, old_value, new_value)

        cmd.execute()
        self.assertEqual(self.mock_all_quotes_data[quote_name_key][field], new_value)
        self.mock_quote_details_widget.update_field_value.assert_called_once_with(field, new_value, from_command=True)

        self.mock_quote_details_widget.update_field_value.reset_mock()

        cmd.unexecute()
        self.assertEqual(self.mock_all_quotes_data[quote_name_key][field], old_value)
        self.mock_quote_details_widget.update_field_value.assert_called_with(field, old_value, from_command=True)

    @patch('commands.print')
    def test_change_quote_detail_command_name_key_not_found(self, mock_print):
        # Test when the quote key is not found during name change
        cmd_exec = ChangeQuoteDetailCommand(self.mock_quote_details_widget, {}, "NON_EXISTENT", "name", "NON_EXISTENT", "NEW_NAME")
        cmd_exec.execute()
        mock_print.assert_called_with("Error: Quote key 'NON_EXISTENT' not found during name change execute. Command: Change NON_EXISTENT's name from 'NON_EXISTENT' to 'NEW_NAME'")
        self.mock_quote_details_widget.update_field_value.assert_not_called() # Should not update UI if data change failed

        mock_print.reset_mock()
        self.mock_quote_details_widget.update_field_value.reset_mock()

        # Test unexecute when the new_name (which became the key) is not found
        cmd_unexec = ChangeQuoteDetailCommand(self.mock_quote_details_widget, {}, "OLD_NAME", "name", "OLD_NAME", "NEW_KEY_NOT_THERE")
        cmd_unexec.unexecute() # This assumes execute was successful and new_value is the key
        mock_print.assert_called_with("Error: Quote key 'NEW_KEY_NOT_THERE' not found during name change unexecute. Command: Change OLD_NAME's name from 'OLD_NAME' to 'NEW_KEY_NOT_THERE'")
        self.mock_quote_details_widget.update_field_value.assert_not_called()

    @patch('commands.print')
    def test_change_quote_detail_command_price_key_not_found(self, mock_print):
        cmd = ChangeQuoteDetailCommand(self.mock_quote_details_widget, {}, "NON_EXISTENT_PRICE", "price", "100", "110")
        cmd.execute()
        mock_print.assert_called_with("Error: Quote key 'NON_EXISTENT_PRICE' not found during price change execute. Command: Change NON_EXISTENT_PRICE's price from '100' to '110'")
        cmd.unexecute() # Should also call print

    def test_add_quote_command(self):
        quote_name = "MSFT"
        quote_data_to_add = {"name": "MSFT", "price": "300.0"} # Simplified for test
        cmd = AddQuoteCommand(self.mock_all_quotes_data, quote_name, quote_data_to_add, self.mock_editor_ref)

        cmd.execute()
        self.assertIn(quote_name, self.mock_all_quotes_data)
        self.assertEqual(self.mock_all_quotes_data[quote_name], quote_data_to_add)

        cmd.unexecute()
        self.assertNotIn(quote_name, self.mock_all_quotes_data)

    def test_remove_quote_command(self):
        quote_name_to_remove = "AAPL"
        removed_quote_data = self.mock_all_quotes_data[quote_name_to_remove].copy()
        cmd = RemoveQuoteCommand(self.mock_all_quotes_data, quote_name_to_remove, removed_quote_data, self.mock_editor_ref)

        cmd.execute()
        self.assertNotIn(quote_name_to_remove, self.mock_all_quotes_data)

        cmd.unexecute()
        self.assertIn(quote_name_to_remove, self.mock_all_quotes_data)
        self.assertEqual(self.mock_all_quotes_data[quote_name_to_remove], removed_quote_data)

    def test_change_eprice_value_command(self):
        quote_name_key = "AAPL"
        company_name = "VCSC"
        old_value = "4.5"
        new_value = "5.0"
        # Ensure the company exists in the mock data initially
        self.mock_all_quotes_data[quote_name_key]["e_price"] = [{"name": company_name, "value": old_value}]

        cmd = ChangeEPriceValueCommand(self.mock_eprice_section_widget, self.mock_all_quotes_data, quote_name_key, company_name, old_value, new_value)

        cmd.execute()
        self.assertEqual(self.mock_all_quotes_data[quote_name_key]["e_price"][0]["value"], new_value)
        self.mock_eprice_section_widget.update_company_value.assert_called_once_with(company_name, new_value, from_command=True)

        self.mock_eprice_section_widget.update_company_value.reset_mock()

        cmd.unexecute()
        self.assertEqual(self.mock_all_quotes_data[quote_name_key]["e_price"][0]["value"], old_value)
        self.mock_eprice_section_widget.update_company_value.assert_called_with(company_name, old_value, from_command=True)

    def test_change_eprice_value_command_add_new_company_on_execute(self):
        quote_name_key = "AAPL"
        new_company_name = "NEWCO"
        old_value = "" # Assuming it didn't exist
        new_value = "5.0"
        self.mock_all_quotes_data[quote_name_key]["e_price"] = [] # Start with no e_price companies

        cmd = ChangeEPriceValueCommand(self.mock_eprice_section_widget, self.mock_all_quotes_data, quote_name_key, new_company_name, old_value, new_value)
        cmd.execute()

        self.assertIn({"name": new_company_name, "value": new_value}, self.mock_all_quotes_data[quote_name_key]["e_price"])
        self.mock_eprice_section_widget.update_company_value.assert_called_once_with(new_company_name, new_value, from_command=True)


    def test_change_pe_value_command(self):
        quote_name_key = "AAPL"
        company_name = "MSFT"
        old_value = "25.0"
        new_value = "27.0"
        # Ensure the company exists in the mock data initially
        self.mock_all_quotes_data[quote_name_key]["pe"] = [{"name": company_name, "value": old_value}]

        cmd = ChangePEValueCommand(self.mock_pe_section_widget, self.mock_all_quotes_data, quote_name_key, company_name, old_value, new_value)

        cmd.execute()
        self.assertEqual(self.mock_all_quotes_data[quote_name_key]["pe"][0]["value"], new_value)
        self.mock_pe_section_widget.update_company_value.assert_called_once_with(company_name, new_value, from_command=True)

        self.mock_pe_section_widget.update_company_value.reset_mock()

        cmd.unexecute()
        self.assertEqual(self.mock_all_quotes_data[quote_name_key]["pe"][0]["value"], old_value)
        self.mock_pe_section_widget.update_company_value.assert_called_with(company_name, old_value, from_command=True)

    def test_change_pe_value_command_add_new_company_on_execute(self):
        quote_name_key = "AAPL"
        new_company_name = "NEWPECO"
        old_value = ""
        new_value = "22.0"
        self.mock_all_quotes_data[quote_name_key]["pe"] = [] # Start with no pe companies

        cmd = ChangePEValueCommand(self.mock_pe_section_widget, self.mock_all_quotes_data, quote_name_key, new_company_name, old_value, new_value)
        cmd.execute()

        self.assertIn({"name": new_company_name, "value": new_value}, self.mock_all_quotes_data[quote_name_key]["pe"])
        self.mock_pe_section_widget.update_company_value.assert_called_once_with(new_company_name, new_value, from_command=True)

    def test_change_eps_value_command(self):
        quote_name_key = "AAPL"
        year_name = "2024"
        company_name = "MSFT"
        field_name = "value"
        old_value = "1.0"
        new_value = "1.1"
        # Ensure the structure exists in the mock data initially
        self.mock_all_quotes_data[quote_name_key]["eps"] = [{"name": year_name, "companies": [{"name": company_name, "value": old_value, "growth": "5%"}]}]

        cmd = ChangeEPSValueCommand(self.mock_eps_section_widget, self.mock_all_quotes_data, quote_name_key,
                                    year_name, company_name, field_name, old_value, new_value)

        cmd.execute()
        self.assertEqual(self.mock_all_quotes_data[quote_name_key]["eps"][0]["companies"][0][field_name], new_value)
        self.mock_eps_section_widget.update_company_eps_field.assert_called_once_with(
            year_name, company_name, field_name, new_value, from_command=True
        )

        self.mock_eps_section_widget.update_company_eps_field.reset_mock()

        cmd.unexecute()
        self.assertEqual(self.mock_all_quotes_data[quote_name_key]["eps"][0]["companies"][0][field_name], old_value)
        self.mock_eps_section_widget.update_company_eps_field.assert_called_with(
            year_name, company_name, field_name, old_value, from_command=True
        )

    def test_change_eps_value_command_creates_structure(self):
        quote_name_key = "AAPL"
        year_name = "2025" # New year
        company_name = "NEW_EPS_CO" # New company
        field_name = "value"
        old_value = ""
        new_value = "2.50"

        # Ensure 'eps' key exists but is empty for the quote
        self.mock_all_quotes_data[quote_name_key]["eps"] = []

        cmd = ChangeEPSValueCommand(self.mock_eps_section_widget, self.mock_all_quotes_data, quote_name_key,
                                    year_name, company_name, field_name, old_value, new_value)
        cmd.execute()

        # Check if data structure was created
        quote_eps_data = self.mock_all_quotes_data[quote_name_key]["eps"]
        self.assertEqual(len(quote_eps_data), 1)
        self.assertEqual(quote_eps_data[0]["name"], year_name)
        self.assertEqual(len(quote_eps_data[0]["companies"]), 1)
        self.assertEqual(quote_eps_data[0]["companies"][0]["name"], company_name)
        self.assertEqual(quote_eps_data[0]["companies"][0][field_name], new_value)

        # Test creating company if year exists but company doesn't
        self.mock_all_quotes_data[quote_name_key]["eps"] = [{"name": "2026", "companies": []}]
        cmd2 = ChangeEPSValueCommand(self.mock_eps_section_widget, self.mock_all_quotes_data, quote_name_key,
                                     "2026", "ANOTHER_CO", "growth", "", "10%")
        cmd2.execute()
        year_2026_data = next(y for y in self.mock_all_quotes_data[quote_name_key]["eps"] if y["name"] == "2026")
        self.assertEqual(len(year_2026_data["companies"]), 1)
        self.assertEqual(year_2026_data["companies"][0]["name"], "ANOTHER_CO")
        self.assertEqual(year_2026_data["companies"][0]["growth"], "10%")

        # Test creating companies list if year exists but "companies" key is missing
        self.mock_all_quotes_data[quote_name_key]["eps"] = [{"name": "2027"}] # No "companies" key
        cmd3 = ChangeEPSValueCommand(self.mock_eps_section_widget, self.mock_all_quotes_data, quote_name_key, "2027", "CO_C", "value", "", "3.0")
        cmd3.execute()
        year_2027_data = next(y for y in self.mock_all_quotes_data[quote_name_key]["eps"] if y["name"] == "2027")
        self.assertIn("companies", year_2027_data)
        self.assertEqual(len(year_2027_data["companies"]), 1)
        self.assertEqual(year_2027_data["companies"][0]["name"], "CO_C")
        self.assertEqual(year_2027_data["companies"][0]["value"], "3.0")


    def test_add_eps_year_command(self):
        quote_name_key = "AAPL"
        year_to_add = "2025"
        # Mock the sort key method used by the command
        self.mock_eps_section_widget._get_eps_year_sort_key = MagicMock(side_effect=lambda x: int(x) if x.isdigit() else 0)
        # Add a mock UI entry for the year being added so unexecute can find it and remove it
        # Also add the existing year entry
        mock_ui_entry_for_added_year = {"year_name": year_to_add, "widget": MagicMock()}
        self.mock_eps_section_widget.eps_year_entries = [{"year_name": "2024", "widget": MagicMock()}, mock_ui_entry_for_added_year]
        self.mock_eps_section_widget._add_eps_year_fields = MagicMock() # Mock this to check calls
        self.mock_eps_section_widget._remove_dynamic_list_entry = MagicMock() # Mock this for unexecute

        cmd = AddEPSYearCommand(self.mock_eps_section_widget, self.mock_all_quotes_data, quote_name_key, year_to_add)

        cmd.execute()
        self.assertEqual(len(self.mock_all_quotes_data[quote_name_key]["eps"]), 1) # Assuming initial data had 0 eps years
        self.assertEqual(self.mock_all_quotes_data[quote_name_key]["eps"][0]["name"], year_to_add)
        self.mock_eps_section_widget._add_eps_year_fields.assert_called_once_with(year_to_add, []) # Should add with empty companies initially

        cmd.unexecute()
        self.assertEqual(len(self.mock_all_quotes_data[quote_name_key]["eps"]), 0) # Year should be removed from model
        self.mock_eps_section_widget._remove_dynamic_list_entry.assert_called_once_with(mock_ui_entry_for_added_year, self.mock_eps_section_widget.eps_year_entries)
        self.mock_eps_section_widget._update_visible_eps_years.assert_called_once()

    def test_add_eps_year_command_year_already_exists_in_model(self):
        quote_name_key = "AAPL"
        year_to_add = "2024" # This year already exists in the setup
        self.mock_all_quotes_data[quote_name_key]["eps"] = [{"name": "2024", "companies": [{"name": "MSFT", "value": "1.0", "growth": "5%"}]}]
        initial_eps_count = len(self.mock_all_quotes_data[quote_name_key]["eps"])
        self.mock_eps_section_widget._add_eps_year_fields = MagicMock() # Mock this to check calls

        cmd = AddEPSYearCommand(self.mock_eps_section_widget, self.mock_all_quotes_data, quote_name_key, year_to_add)
        cmd.execute()

        self.assertEqual(len(self.mock_all_quotes_data[quote_name_key]["eps"]), initial_eps_count) # No new year added to model
        self.mock_eps_section_widget._add_eps_year_fields.assert_called_once_with(year_to_add, []) # UI still updated

    def test_remove_eps_year_command(self):
        quote_name_key = "AAPL"
        year_to_remove = "2024"
        removed_year_data_model = {"name": year_to_remove, "companies": [{"name": "MSFT", "value": "1.0", "growth": "5%"}]}
        self.mock_all_quotes_data[quote_name_key]["eps"] = [removed_year_data_model] # Ensure year exists in model
        # Add a mock UI entry so execute can find and remove it
        mock_ui_entry_for_removed_year = {"year_name": year_to_remove, "widget": MagicMock()}
        self.mock_eps_section_widget.eps_year_entries = [mock_ui_entry_for_removed_year]
        self.mock_eps_section_widget._remove_dynamic_list_entry = MagicMock() # Mock this for execute
        self.mock_eps_section_widget._add_eps_year_fields = MagicMock() # Mock this for unexecute

        cmd = RemoveEPSYearCommand(self.mock_eps_section_widget, self.mock_all_quotes_data, quote_name_key, year_to_remove, removed_year_data_model)

        cmd.execute()
        self.assertEqual(len(self.mock_all_quotes_data[quote_name_key]["eps"]), 0) # Year removed from model
        self.mock_eps_section_widget._remove_dynamic_list_entry.assert_called_once_with(mock_ui_entry_for_removed_year, self.mock_eps_section_widget.eps_year_entries)
        self.mock_eps_section_widget._update_visible_eps_years.assert_called_once()

        cmd.unexecute()
        self.assertEqual(len(self.mock_all_quotes_data[quote_name_key]["eps"]), 1) # Year re-added to model
        self.assertEqual(self.mock_all_quotes_data[quote_name_key]["eps"][0], removed_year_data_model)
        self.mock_eps_section_widget._add_eps_year_fields.assert_called_once_with(year_to_remove, removed_year_data_model.get("companies", []))


    def test_change_eps_year_display_command(self):
        old_selected_years = ["2023"]
        new_selected_years = ["2024", "2025"]
        self.mock_eps_section_widget.selected_eps_years_to_display = list(old_selected_years) # Set initial state
        self.mock_eps_section_widget._update_visible_eps_years = MagicMock()

        cmd = ChangeEPSYearDisplayCommand(self.mock_eps_section_widget, old_selected_years, new_selected_years)

        cmd.execute()
        self.assertEqual(self.mock_eps_section_widget.selected_eps_years_to_display, new_selected_years)
        self.mock_eps_section_widget._update_visible_eps_years.assert_called_once()

        self.mock_eps_section_widget._update_visible_eps_years.reset_mock()

        cmd.unexecute()
        self.assertEqual(self.mock_eps_section_widget.selected_eps_years_to_display, old_selected_years)
        self.mock_eps_section_widget._update_visible_eps_years.assert_called_with() # Called again

    @patch('commands.print')
    def test_change_eps_year_display_command_year_not_found_in_ui(self, mock_print):
        # This command doesn't directly interact with year_entries for its data model change,
        # but the _update_visible_eps_years might. The command itself should still function.
        # The print statements are in ChangeEPSCompaniesForYearDisplayCommand.
        # This test is more for completeness of the command itself.
        old_years = ["2023"]
        new_years = ["2024"]
        self.mock_eps_section_widget.selected_eps_years_to_display = list(old_years)
        self.mock_eps_section_widget.eps_year_entries = [] # No UI entries
        self.mock_eps_section_widget._update_visible_eps_years = MagicMock()

        cmd = ChangeEPSYearDisplayCommand(self.mock_eps_section_widget, old_years, new_years)
        cmd.execute()
        self.assertEqual(self.mock_eps_section_widget.selected_eps_years_to_display, new_years)
        cmd.unexecute()
        self.assertEqual(self.mock_eps_section_widget.selected_eps_years_to_display, old_years)


    def test_change_eps_companies_for_year_display_command(self):
        year = "2024"
        old_selected_companies = ["MSFT", "GOOG"]
        new_selected_companies = ["MSFT"]
        # Setup a mock year entry in the UI list
        mock_year_entry = {"year_name": year, "widget": MagicMock(), "selected_companies_to_display_for_year": list(old_selected_companies)}
        self.mock_eps_section_widget.eps_year_entries = [mock_year_entry]
        self.mock_eps_section_widget._update_visible_eps_companies_for_year = MagicMock()

        cmd = ChangeEPSCompaniesForYearDisplayCommand(self.mock_eps_section_widget, year, old_selected_companies, new_selected_companies)

        cmd.execute()
        self.assertEqual(mock_year_entry["selected_companies_to_display_for_year"], new_selected_companies)
        self.mock_eps_section_widget._update_visible_eps_companies_for_year.assert_called_once_with(mock_year_entry)

        self.mock_eps_section_widget._update_visible_eps_companies_for_year.reset_mock()

        cmd.unexecute()
        self.assertEqual(mock_year_entry["selected_companies_to_display_for_year"], old_selected_companies)
        self.mock_eps_section_widget._update_visible_eps_companies_for_year.assert_called_with(mock_year_entry) # Called again

    @patch('commands.print')
    def test_change_eps_companies_for_year_display_command_year_not_found_in_ui(self, mock_print):
        year_name = "NON_EXISTENT_YEAR"
        old_companies = ["A"]
        new_companies = ["B"]
        self.mock_eps_section_widget.eps_year_entries = [] # Year not in UI entries

        cmd = ChangeEPSCompaniesForYearDisplayCommand(self.mock_eps_section_widget, year_name, old_companies, new_companies)

        cmd.execute()
        mock_print.assert_called_with(f"Warning: Could not find EPS year '{year_name}' to change company display during execute.")

        mock_print.reset_mock()

        cmd.unexecute()
        mock_print.assert_called_with(f"Warning: Could not find EPS year '{year_name}' to change company display during unexecute.")


    def test_add_record_report_command(self):
        quote_name_key = "AAPL"
        report_data_to_add = {"company": "MSFT", "date": "01/01/2024", "color": "blue"}
        # Ensure the quote has a record list initially (can be empty)
        self.mock_all_quotes_data[quote_name_key]["record"] = []
        self.mock_record_widget.load_data = MagicMock() # Mock load_data

        cmd = AddRecordReportCommand(self.mock_record_widget, self.mock_all_quotes_data, quote_name_key, report_data_to_add)

        cmd.execute()
        self.assertIn(report_data_to_add, self.mock_all_quotes_data[quote_name_key]["record"])
        self.mock_record_widget.load_data.assert_called_once_with(self.mock_all_quotes_data[quote_name_key]["record"])
        self.assertNotEqual(cmd.description, "Add Record Report") # Check description updated

        self.mock_record_widget.load_data.reset_mock()

        cmd.unexecute()
        self.assertNotIn(report_data_to_add, self.mock_all_quotes_data[quote_name_key]["record"])
        self.mock_record_widget.load_data.assert_called_once_with(self.mock_all_quotes_data[quote_name_key]["record"])

    def test_add_record_report_command_quote_not_found(self):
        quote_name_key = "NON_EXISTENT_QUOTE"
        report_data_to_add = {"company": "MSFT", "date": "01/01/2024", "color": "blue"}
        self.mock_record_widget.clear_data = MagicMock()
        self.mock_record_widget.load_data = MagicMock()

        cmd = AddRecordReportCommand(self.mock_record_widget, self.mock_all_quotes_data, quote_name_key, report_data_to_add)

        cmd.execute()
        self.assertNotIn(quote_name_key, self.mock_all_quotes_data) # Data model unchanged
        self.mock_record_widget.clear_data.assert_called_once() # UI cleared
        self.mock_record_widget.load_data.assert_not_called()

        self.mock_record_widget.clear_data.reset_mock()
        self.mock_record_widget.load_data.reset_mock()

        cmd.unexecute()
        self.assertNotIn(quote_name_key, self.mock_all_quotes_data) # Data model unchanged
        self.mock_record_widget.clear_data.assert_called_once() # UI cleared again
        self.mock_record_widget.load_data.assert_not_called()


    def test_remove_record_report_command(self):
        quote_name_key = "AAPL"
        report_to_remove_model = {"company": "MSFT", "date": "01/01/2024", "color": "blue"}
        ui_entry_data = {"widget": MagicMock()} # Simplified UI entry
        # Ensure the report exists in the data model
        self.mock_all_quotes_data[quote_name_key]["record"] = [report_to_remove_model, {"company": "GOOG", "date": "01/02/2024", "color": "red"}]
        original_index = 0
        self.mock_record_widget.load_data = MagicMock()

        cmd = RemoveRecordReportCommand(self.mock_record_widget, self.mock_all_quotes_data, quote_name_key, report_to_remove_model, ui_entry_data, original_index)

        cmd.execute()
        self.assertNotIn(report_to_remove_model, self.mock_all_quotes_data[quote_name_key]["record"])
        self.mock_record_widget.load_data.assert_called_once_with(self.mock_all_quotes_data[quote_name_key]["record"])

        self.mock_record_widget.load_data.reset_mock()

        cmd.unexecute()
        self.assertIn(report_to_remove_model, self.mock_all_quotes_data[quote_name_key]["record"])
        # Check if it was inserted at the original index (assuming list wasn't modified otherwise)
        self.assertEqual(self.mock_all_quotes_data[quote_name_key]["record"][original_index], report_to_remove_model)
        self.mock_record_widget.load_data.assert_called_once_with(
            self.mock_all_quotes_data[quote_name_key]["record"]
        )

    def test_remove_record_report_command_quote_not_found(self):
        quote_name_key = "NON_EXISTENT_QUOTE"
        report_to_remove_model = {"company": "MSFT", "date": "01/01/2024", "color": "blue"}
        ui_entry_data = {"widget": MagicMock()}
        self.mock_record_widget.clear_data = MagicMock()
        self.mock_record_widget.load_data = MagicMock()

        cmd = RemoveRecordReportCommand(self.mock_record_widget, self.mock_all_quotes_data, quote_name_key, report_to_remove_model, ui_entry_data, 0)

        cmd.execute()
        self.mock_record_widget.clear_data.assert_called_once()
        self.mock_record_widget.load_data.assert_not_called()

        self.mock_record_widget.clear_data.reset_mock()
        self.mock_record_widget.load_data.reset_mock()

        cmd.unexecute() # Unexecute should still try to add, but won't find quote
        self.mock_record_widget.clear_data.assert_called_once() # Should still clear UI if quote not found
        self.mock_record_widget.load_data.assert_not_called()


    def test_remove_record_report_command_unexecute_no_record_key(self):
        quote_name_key = "AAPL"
        report_to_restore = {"company": "MSFT", "date": "01/01/2024", "color": "blue"}
        # Setup: quote exists but no "record" key
        self.mock_all_quotes_data[quote_name_key] = {"name": "AAPL"}
        self.mock_record_widget.load_data = MagicMock()

        cmd = RemoveRecordReportCommand(self.mock_record_widget, self.mock_all_quotes_data, quote_name_key, report_to_restore, {}, 0)

        cmd.unexecute() # Should create "record" list and add the report
        self.assertIn("record", self.mock_all_quotes_data[quote_name_key])
        self.assertIn(report_to_restore, self.mock_all_quotes_data[quote_name_key]["record"])
        self.mock_record_widget.load_data.assert_called_once_with(self.mock_all_quotes_data[quote_name_key]["record"])


    def test_remove_record_report_command_unexecute_invalid_index(self):
        quote_name_key = "AAPL"
        report_to_restore = {"company": "TSLA", "date": "02/02/2024", "color": "red"}
        self.mock_all_quotes_data[quote_name_key]["record"] = [{"company": "Existing", "date": "01/01/2024", "color": "blue"}]
        self.mock_record_widget.load_data = MagicMock()

        cmd = RemoveRecordReportCommand(self.mock_record_widget, self.mock_all_quotes_data, quote_name_key, report_to_restore, {}, -1) # Invalid index
        cmd.unexecute() # Should append
        self.assertEqual(self.mock_all_quotes_data[quote_name_key]["record"][-1], report_to_restore)
        self.mock_record_widget.load_data.assert_called_once_with(self.mock_all_quotes_data[quote_name_key]["record"])

        self.mock_record_widget.load_data.reset_mock()

        cmd2 = RemoveRecordReportCommand(self.mock_record_widget, self.mock_all_quotes_data, quote_name_key, report_to_restore, {}, 99) # Invalid index
        cmd2.unexecute() # Should append
        self.assertEqual(self.mock_all_quotes_data[quote_name_key]["record"][-1], report_to_restore)
        self.mock_record_widget.load_data.assert_called_once_with(self.mock_all_quotes_data[quote_name_key]["record"])


    def test_change_record_report_detail_command(self):
        quote_name_key = "AAPL"
        field_name = "company"
        old_value = "MSFT"
        new_value = "GOOG"
        # Setup mock data model and UI entry references
        report_data_model_ref = {"company": old_value, "date": "01/01/2024", "color": "blue"}
        ui_entry_data_ref = {"widget": MagicMock(), "current_company": old_value, "current_date": "01/01/2024", "current_color": "blue"}
        self.mock_all_quotes_data[quote_name_key]["record"] = [report_data_model_ref]
        self.mock_record_widget.report_entries = [ui_entry_data_ref] # Ensure UI entry exists
        self.mock_record_widget.update_report_entry_detail = MagicMock()

        cmd = ChangeRecordReportDetailCommand(self.mock_record_widget, self.mock_all_quotes_data, quote_name_key,
                                            report_data_model_ref, ui_entry_data_ref,
                                            field_name, old_value, new_value)

        cmd.execute()
        self.assertEqual(report_data_model_ref[field_name], new_value)
        self.mock_record_widget.update_report_entry_detail.assert_called_once_with(
            ui_entry_data_ref, field_name, new_value, from_command=True
        )

        self.mock_record_widget.update_report_entry_detail.reset_mock()

        cmd.unexecute()
        self.assertEqual(report_data_model_ref[field_name], old_value)
        self.mock_record_widget.update_report_entry_detail.assert_called_once_with(
            ui_entry_data_ref, field_name, old_value, from_command=True
        )


    def test_change_eps_year_display_command(self):
        old_selected_years = ["2023"]
        new_selected_years = ["2024", "2025"]
        self.mock_eps_section_widget.selected_eps_years_to_display = list(old_selected_years) # Set initial state
        self.mock_eps_section_widget._update_visible_eps_years = MagicMock()

        cmd = ChangeEPSYearDisplayCommand(self.mock_eps_section_widget, old_selected_years, new_selected_years)

        cmd.execute() # Corrected assertion method
        self.assertEqual(self.mock_eps_section_widget.selected_eps_years_to_display, new_selected_years)
        self.mock_eps_section_widget._update_visible_eps_years.assert_called_once()

        self.mock_eps_section_widget._update_visible_eps_years.reset_mock()

        cmd.unexecute()
        self.assertEqual(self.mock_eps_section_widget.selected_eps_years_to_display, old_selected_years)
        self.mock_eps_section_widget._update_visible_eps_years.assert_called_with() # Called again

    @patch('commands.print')
    def test_change_eps_year_display_command_year_not_found_in_ui(self, mock_print):
        # This command doesn't directly interact with year_entries for its data model change,
        # but the _update_visible_eps_years might. The command itself should still function.
        # The print statements are in ChangeEPSCompaniesForYearDisplayCommand.
        # This test is more for completeness of the command itself.
        old_years = ["2023"]
        new_years = ["2024"]
        self.mock_eps_section_widget.selected_eps_years_to_display = list(old_years)
        self.mock_eps_section_widget.eps_year_entries = [] # No UI entries
        self.mock_eps_section_widget._update_visible_eps_years = MagicMock()

        cmd = ChangeEPSYearDisplayCommand(self.mock_eps_section_widget, old_years, new_years)
        cmd.execute()
        self.assertEqual(self.mock_eps_section_widget.selected_eps_years_to_display, new_years)
        cmd.unexecute()
        self.assertEqual(self.mock_eps_section_widget.selected_eps_years_to_display, old_years)


    def test_change_eps_companies_for_year_display_command(self):
        year = "2024"
        old_selected_companies = ["MSFT", "GOOG"]
        new_selected_companies = ["MSFT"]
        # Setup a mock year entry in the UI list
        mock_year_entry = {"year_name": year, "widget": MagicMock(), "selected_companies_to_display_for_year": list(old_selected_companies)}
        self.mock_eps_section_widget.eps_year_entries = [mock_year_entry]
        self.mock_eps_section_widget._update_visible_eps_companies_for_year = MagicMock()

        cmd = ChangeEPSCompaniesForYearDisplayCommand(self.mock_eps_section_widget, year, old_selected_companies, new_selected_companies)

        cmd.execute() # Corrected assertion method
        self.assertEqual(mock_year_entry["selected_companies_to_display_for_year"], new_selected_companies)
        self.mock_eps_section_widget._update_visible_eps_companies_for_year.assert_called_once_with(mock_year_entry)

        self.mock_eps_section_widget._update_visible_eps_companies_for_year.reset_mock()

        cmd.unexecute()
        self.assertEqual(mock_year_entry["selected_companies_to_display_for_year"], old_selected_companies)
        self.mock_eps_section_widget._update_visible_eps_companies_for_year.assert_called_with(mock_year_entry) # Called again

    @patch('commands.print')
    def test_change_eps_companies_for_year_display_command_year_not_found_in_ui(self, mock_print):
        year_name = "NON_EXISTENT_YEAR"
        old_companies = ["A"]
        new_companies = ["B"]
        self.mock_eps_section_widget.eps_year_entries = [] # Year not in UI entries

        cmd = ChangeEPSCompaniesForYearDisplayCommand(self.mock_eps_section_widget, year_name, old_companies, new_companies)

        cmd.execute()
        mock_print.assert_called_with(f"Warning: Could not find EPS year '{year_name}' to change company display during execute.")

        mock_print.reset_mock()

        cmd.unexecute()
        mock_print.assert_called_with(f"Warning: Could not find EPS year '{year_name}' to change company display during unexecute.")

    def test_change_eprice_fixed_companies_command(self):
        old_list = ["A", "B"]
        new_list = ["C", "D"]
        self.mock_editor_ref.EPRICE_FIXED_COMPANIES = list(old_list) # Set initial state
        self.mock_editor_ref._load_eprice_config_and_update_ui = MagicMock()
        self.mock_editor_ref.save_current_eprice_config = MagicMock()

        cmd = ChangeEPriceFixedCompaniesCommand(self.mock_editor_ref, old_list, new_list)

        cmd.execute()
        self.assertEqual(self.mock_editor_ref.EPRICE_FIXED_COMPANIES, new_list)
        self.mock_editor_ref._load_eprice_config_and_update_ui.assert_called_once()
        self.mock_editor_ref.save_current_eprice_config.assert_called_once()

        self.mock_editor_ref._load_eprice_config_and_update_ui.reset_mock()
        self.mock_editor_ref.save_current_eprice_config.reset_mock()

        cmd.unexecute()
        self.assertEqual(self.mock_editor_ref.EPRICE_FIXED_COMPANIES, old_list)
        self.mock_editor_ref._load_eprice_config_and_update_ui.assert_called_once()
        self.mock_editor_ref.save_current_eprice_config.assert_called_once()

    def test_change_eprice_fixed_companies_command_no_editor(self):
        old_list = ["A", "B"]
        new_list = ["C", "D"]
        # editor_ref is None
        cmd = ChangeEPriceFixedCompaniesCommand(None, old_list, new_list)

        # Execute should not raise error
        cmd.execute()
        # Since editor_ref is None, no methods on it should be called.

        # Unexecute should not raise error
        cmd.unexecute()

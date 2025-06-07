# t:\Work\xml_input_ui\editor_action_handler.py
from PyQt6.QtWidgets import QMessageBox
# QDate might be needed if any handlers use it directly, but data_utils.get_default_working_date handles QDate creation.
import data_utils # For get_default_working_date
from commands import (
    ChangeRootDateCommand, ChangeQuoteDetailCommand, ChangeEPriceValueCommand,
    ChangePEValueCommand, ChangeEPSValueCommand,
    AddEPSYearCommand, RemoveEPSYearCommand,
    ChangeEPSYearDisplayCommand,
    ChangeEPSCompaniesForYearDisplayCommand, AddRecordReportCommand,
    RemoveRecordReportCommand, ChangeRecordReportDetailCommand
)

class EditorActionHandler:
    def __init__(self, editor):
        self.editor = editor # Reference to XmlReportEditor instance

    # --- Root Date Handlers ---
    def handle_root_date_changed_by_calendar(self, new_qdate):
        new_date_str = new_qdate.toString("MM/dd/yyyy")
        if new_date_str != self.editor._current_root_date_str:
            if "date" not in self.editor.all_quotes_data: # Ensure key exists
                 self.editor.all_quotes_data["date"] = self.editor._current_root_date_str
            cmd = ChangeRootDateCommand(self.editor.root_date_edit, self.editor.all_quotes_data,
                                        self.editor._current_root_date_str, new_date_str)
            self.editor.execute_command(cmd)
            self.editor._current_root_date_str = new_date_str

    def handle_root_date_changed(self):
        new_date_str = self.editor.root_date_edit.date().toString("MM/dd/yyyy")
        if new_date_str != self.editor._current_root_date_str:
            if "date" not in self.editor.all_quotes_data: # Ensure key exists
                 self.editor.all_quotes_data["date"] = self.editor._current_root_date_str
            cmd = ChangeRootDateCommand(self.editor.root_date_edit, self.editor.all_quotes_data,
                                        self.editor._current_root_date_str, new_date_str)
            self.editor.execute_command(cmd)
            self.editor._current_root_date_str = new_date_str

    # --- Quote Details Handlers ---
    def handle_quote_name_changed(self, old_name, new_name):
        if not self.editor.selected_quote_name: return
        if not new_name:
            QMessageBox.warning(self.editor, "Input Error", "Quote name cannot be empty.")
            self.editor.quote_details_widget.update_field_value("name", old_name, from_command=False)
            return
        # For a name change, the 'quote_name_key' passed to the command is the old_name.
        cmd = ChangeQuoteDetailCommand(self.editor.quote_details_widget, self.editor.all_quotes_data,
                                       old_name, "name", old_name, new_name)
        self.editor.execute_command(cmd)
        # Post-command execution logic for name change (updating editor's selected_quote_name)
        # is handled in XmlReportEditor.undo/redo or after execute_command if needed.
        # For direct execution, if the selected quote's name changed:
        if self.editor.selected_quote_name == old_name and old_name != new_name:
            self.editor.selected_quote_name = new_name
            self.editor.quote_selection_widget.set_quote_name_input(new_name)

    def handle_quote_price_changed(self, old_price, new_price):
        if not self.editor.selected_quote_name: return
        cmd = ChangeQuoteDetailCommand(self.editor.quote_details_widget, self.editor.all_quotes_data,
                                       self.editor.selected_quote_name, "price", old_price, new_price)
        self.editor.execute_command(cmd)

    # --- E-Price Handlers ---
    def handle_eprice_value_changed(self, company_name, old_value, new_value):
        if not self.editor.selected_quote_name: return
        cmd = ChangeEPriceValueCommand(self.editor.eprice_section_widget, self.editor.all_quotes_data,
                                       self.editor.selected_quote_name, company_name, old_value, new_value)
        self.editor.execute_command(cmd)

    # --- PE Handlers ---
    def handle_pe_value_changed(self, company_name, old_value, new_value):
        if not self.editor.selected_quote_name: return
        cmd = ChangePEValueCommand(self.editor.pe_section_widget, self.editor.all_quotes_data,
                                   self.editor.selected_quote_name, company_name, old_value, new_value)
        self.editor.execute_command(cmd)

    # --- EPS Handlers ---
    def handle_eps_value_changed(self, year_name, company_name, field_name, old_value, new_value):
        if not self.editor.selected_quote_name: return
        cmd = ChangeEPSValueCommand(self.editor.eps_section_widget, self.editor.all_quotes_data,
                                    self.editor.selected_quote_name, year_name, company_name,
                                    field_name, old_value, new_value)
        self.editor.execute_command(cmd)

    def handle_eps_year_add_requested(self, year_name):
        if not self.editor.selected_quote_name: return
        cmd = AddEPSYearCommand(self.editor.eps_section_widget, self.editor.all_quotes_data,
                                self.editor.selected_quote_name, year_name, initial_companies_data=None)
        self.editor.execute_command(cmd)

    def handle_eps_year_remove_requested(self, year_name_to_remove):
        if not self.editor.selected_quote_name: return
        quote_data = self.editor.all_quotes_data.get(self.editor.selected_quote_name)
        if not quote_data or "eps" not in quote_data: return
        removed_year_data_model = next((year for year in quote_data["eps"] if year.get("name") == year_name_to_remove), None)
        if not removed_year_data_model:
            QMessageBox.warning(self.editor, "Error", f"Could not find EPS year '{year_name_to_remove}' in data model to remove.")
            return
        cmd = RemoveEPSYearCommand(self.editor.eps_section_widget, self.editor.all_quotes_data,
                                   self.editor.selected_quote_name, year_name_to_remove, removed_year_data_model)
        self.editor.execute_command(cmd)

    def handle_eps_year_display_change_requested(self, old_selected_years, new_selected_years):
        if not self.editor.selected_quote_name: return
        cmd = ChangeEPSYearDisplayCommand(self.editor.eps_section_widget, old_selected_years, new_selected_years)
        self.editor.execute_command(cmd)

    def handle_eps_companies_for_year_display_change_requested(self, year_name, old_selected_companies, new_selected_companies):
        if not self.editor.selected_quote_name: return
        cmd = ChangeEPSCompaniesForYearDisplayCommand(self.editor.eps_section_widget, year_name, old_selected_companies, new_selected_companies)
        self.editor.execute_command(cmd)

    # --- Record Report Handlers ---
    def handle_record_report_add_requested(self):
        if not self.editor.selected_quote_name: return
        new_report_data = {
            "company": self.editor.EPRICE_FIXED_COMPANIES[0] if self.editor.EPRICE_FIXED_COMPANIES else "",
            "date": data_utils.get_default_working_date().toString("MM/dd/yyyy"),
            "color": "default"
        }
        cmd = AddRecordReportCommand(self.editor.record_report_section_widget, self.editor.all_quotes_data,
                                     self.editor.selected_quote_name, new_report_data, insert_at_index=0)
        self.editor.execute_command(cmd)

    def handle_record_report_remove_requested(self, ui_entry_data_to_remove):
        if not self.editor.selected_quote_name or self.editor.selected_quote_name not in self.editor.all_quotes_data:
            return
        quote_data = self.editor.all_quotes_data[self.editor.selected_quote_name]
        if "record" not in quote_data: return

        report_data_model_to_remove = None
        original_data_model_index = -1
        match_company = ui_entry_data_to_remove.get("current_company")
        match_date = ui_entry_data_to_remove.get("current_date")
        match_color = ui_entry_data_to_remove.get("current_color")

        for idx, data_model_entry in enumerate(quote_data["record"]):
            if (data_model_entry.get("company") == match_company and
                data_model_entry.get("date") == match_date and
                data_model_entry.get("color", "default") == match_color):
                report_data_model_to_remove = data_model_entry
                original_data_model_index = idx
                break
        if report_data_model_to_remove is None:
            QMessageBox.warning(self.editor, "Error", "Could not find the report entry in the data model to remove.")
            return
        cmd = RemoveRecordReportCommand(self.editor.record_report_section_widget, self.editor.all_quotes_data,
                                        self.editor.selected_quote_name, report_data_model_to_remove,
                                        ui_entry_data_to_remove, original_data_model_index)
        self.editor.execute_command(cmd)

    def handle_record_report_detail_changed(self, ui_entry_data_ref, field_name, old_value, new_value):
        if not self.editor.selected_quote_name or self.editor.selected_quote_name not in self.editor.all_quotes_data:
            return
        quote_data = self.editor.all_quotes_data[self.editor.selected_quote_name]
        data_model_ref = self.editor._find_data_model_for_record_report(quote_data, ui_entry_data_ref, field_name, old_value)
        
        if data_model_ref is None:
            QMessageBox.warning(self.editor, "Error", f"Could not find matching record in data model for update: {old_value} -> {new_value}")
            self.editor.record_report_section_widget.update_report_entry_detail(ui_entry_data_ref, field_name, old_value, from_command=True) # Revert UI
            return
        cmd = ChangeRecordReportDetailCommand(self.editor.record_report_section_widget, self.editor.all_quotes_data,
                                            self.editor.selected_quote_name, data_model_ref, ui_entry_data_ref,
                                            field_name, old_value, new_value)
        self.editor.execute_command(cmd)

    def handle_record_report_manual_refresh(self):
        if self.editor.selected_quote_name and self.editor.selected_quote_name in self.editor.all_quotes_data:
            quote_data = self.editor.all_quotes_data[self.editor.selected_quote_name]
            records_to_load = quote_data.get("record", [])
            self.editor.record_report_section_widget.load_data(records_to_load)
        else:
            self.editor.record_report_section_widget.clear_data()

    # --- Chart Handler ---
    def handle_eps_growth_data_changed_for_chart(self, year_name_changed):
        if not self.editor.selected_quote_name: return
        if self.editor.eps_growth_chart_widget._selected_year_for_chart == year_name_changed:
            # Ensure the chart has the latest full EPS data for the current quote
            current_quote_eps_data = self.editor.all_quotes_data.get(self.editor.selected_quote_name, {}).get("eps", [])
            self.editor.eps_growth_chart_widget.load_data(current_quote_eps_data) # Reload data for safety
            self.editor.eps_growth_chart_widget.update_chart(year_name_changed) # Then update with specific year

    # --- Sector Handlers ---
    def handle_sector_value_changed(self, sector_name, field, new_value):
        if not self.editor.selected_quote_name: return
        quote_name = self.editor.selected_quote_name
        old_value = next((s.get(field, "") for s in self.editor.all_quotes_data.get(quote_name, {}).get("sectors", []) if s.get("name") == sector_name), "")
        cmd = commands.ChangeSectorsCommand(self.editor.sectors_section_widget, self.editor.all_quotes_data,
                                            quote_name, sector_name, field, old_value, new_value)
        self.editor.execute_command(cmd)

    # --- Sector Handlers ---
    def handle_sector_value_changed(self, sector_name, field, new_value):
        if not self.editor.selected_quote_name: return
        quote_name = self.editor.selected_quote_name
        old_value = next((s.get(field, "") for s in self.editor.all_quotes_data.get(quote_name, {}).get("sectors", []) if s.get("name") == sector_name), "")
        cmd = commands.ChangeSectorsCommand(self.editor.sectors_section_widget, self.editor.all_quotes_data,
                                            quote_name, sector_name, field, old_value, new_value)
        self.editor.execute_command(cmd)
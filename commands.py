# t:\Work\xml_input_ui\commands.py
from abc import ABC, abstractmethod
from PyQt6.QtCore import QDate

class Command(ABC):
    """Abstract base class for commands."""
    def __init__(self, description=""):
        self.description = description

    @abstractmethod
    def execute(self):
        pass

    @abstractmethod
    def unexecute(self):
        pass

    def __str__(self):
        return self.description if self.description else self.__class__.__name__

class ChangeRootDateCommand(Command):
    def __init__(self, date_edit_widget, all_quotes_data_ref, old_date_str, new_date_str, description="Change Global Date"):
        super().__init__(description)
        self.date_edit_widget = date_edit_widget
        self.all_quotes_data_ref = all_quotes_data_ref # Reference to the main data structure
        self.old_date_qdate = QDate.fromString(old_date_str, "MM/dd/yyyy")
        self.new_date_qdate = QDate.fromString(new_date_str, "MM/dd/yyyy")
        self.description = f"Change Global Date from {old_date_str} to {new_date_str}"


    def execute(self):
        # Update the data model first
        if "date" in self.all_quotes_data_ref: # Assuming root date is stored at top level of all_quotes_data
             self.all_quotes_data_ref["date"] = self.new_date_qdate.toString("MM/dd/yyyy")
        # Then update the UI
        # Block signals to prevent re-triggering command creation during programmatic change
        self.date_edit_widget.blockSignals(True)
        self.date_edit_widget.setDate(self.new_date_qdate)
        self.date_edit_widget.blockSignals(False)

    def unexecute(self):
        # Update the data model first
        if "date" in self.all_quotes_data_ref:
            self.all_quotes_data_ref["date"] = self.old_date_qdate.toString("MM/dd/yyyy")
        # Then update the UI
        self.date_edit_widget.blockSignals(True)
        self.date_edit_widget.setDate(self.old_date_qdate)
        self.date_edit_widget.blockSignals(False)

class ChangeQuoteDetailCommand(Command):
    def __init__(self, quote_details_widget, all_quotes_data_ref, quote_name_key, field_name, old_value, new_value):
        """
        Command to change a detail (name or price) of a quote.
        Args:
            quote_details_widget: The QuoteDetailsWidget instance.
            all_quotes_data_ref: Reference to the main self.all_quotes_data.
            quote_name_key: The key of the quote in all_quotes_data_ref at the time of command creation.
                            For a name change, quote_name_key == old_value.
                            For a price change, quote_name_key is the quote's (unchanging) name.
            field_name: The name of the field being changed (e.g., "name", "price").
            old_value: The original value of the field.
            new_value: The new value for the field.
        """
        super().__init__(description=f"Change {quote_name_key}'s {field_name} from '{old_value}' to '{new_value}'")
        self.quote_details_widget = quote_details_widget
        self.all_quotes_data_ref = all_quotes_data_ref
        self.quote_name_key_at_creation = quote_name_key # The key used to find the quote initially
        self.field_name = field_name
        self.old_value = old_value
        self.new_value = new_value
    
    def execute(self):
        if self.field_name == "name":
            # old_value is the original key, new_value is the new key
            if self.old_value in self.all_quotes_data_ref:
                quote_data = self.all_quotes_data_ref.pop(self.old_value)
                quote_data["name"] = self.new_value # Update the name field within the dict
                self.all_quotes_data_ref[self.new_value] = quote_data
            else: # Should not happen if editor logic is correct before command creation
                print(f"Error: Quote key '{self.old_value}' not found during name change execute. Command: {self.description}")
                return # Or raise an exception
        else: # field_name is "price"
            if self.quote_name_key_at_creation in self.all_quotes_data_ref:
                self.all_quotes_data_ref[self.quote_name_key_at_creation][self.field_name] = self.new_value
            else: # Should not happen
                print(f"Error: Quote key '{self.quote_name_key_at_creation}' not found during price change execute. Command: {self.description}")
                return # Or raise an exception
    
        self.quote_details_widget.update_field_value(self.field_name, self.new_value, from_command=True)
    
    def unexecute(self):
        if self.field_name == "name":
            # new_value is the current key (after execute), old_value is the key to revert to
            if self.new_value in self.all_quotes_data_ref:
                quote_data = self.all_quotes_data_ref.pop(self.new_value)
                quote_data["name"] = self.old_value # Revert the name field within the dict
                self.all_quotes_data_ref[self.old_value] = quote_data
            else: # Should not happen
                print(f"Error: Quote key '{self.new_value}' not found during name change unexecute. Command: {self.description}")
                return # Or raise an exception
        else: # field_name is "price"
            if self.quote_name_key_at_creation in self.all_quotes_data_ref:
                self.all_quotes_data_ref[self.quote_name_key_at_creation][self.field_name] = self.old_value
            else: # Should not happen
                print(f"Error: Quote key '{self.quote_name_key_at_creation}' not found during price change unexecute. Command: {self.description}")
                return # Or raise an exception
    
        self.quote_details_widget.update_field_value(self.field_name, self.old_value, from_command=True)

class AddQuoteCommand(Command):
    def __init__(self, all_quotes_data_ref, quote_name, quote_data_to_add, editor_ref):
        super().__init__(description=f"Add quote '{quote_name}'")
        self.all_quotes_data_ref = all_quotes_data_ref
        self.quote_name = quote_name
        self.quote_data_to_add = quote_data_to_add # This is the initial empty data structure for the quote
        self.editor_ref = editor_ref # Reference to XmlReportEditor instance, if needed for callbacks

    def execute(self):
        self.all_quotes_data_ref[self.quote_name] = self.quote_data_to_add
        # The editor will handle displaying the new quote after command execution

    def unexecute(self):
        if self.quote_name in self.all_quotes_data_ref:
            del self.all_quotes_data_ref[self.quote_name]
        # Editor needs to handle UI update (e.g. clear or select another quote)

class RemoveQuoteCommand(Command):
    def __init__(self, all_quotes_data_ref, quote_name_to_remove, removed_quote_data, editor_ref):
        super().__init__(description=f"Remove quote '{quote_name_to_remove}'")
        self.all_quotes_data_ref = all_quotes_data_ref
        self.quote_name_to_remove = quote_name_to_remove
        self.removed_quote_data = removed_quote_data # Store the data for undo
        self.editor_ref = editor_ref

    def execute(self):
        if self.quote_name_to_remove in self.all_quotes_data_ref:
            del self.all_quotes_data_ref[self.quote_name_to_remove]
        # Editor needs to handle UI update

    def unexecute(self):
        self.all_quotes_data_ref[self.quote_name_to_remove] = self.removed_quote_data
        # Editor needs to handle UI update (e.g. re-display this quote)

class ChangeEPriceValueCommand(Command):
    def __init__(self, eprice_section_widget, all_quotes_data_ref, quote_name_key, company_name, old_value, new_value):
        """
        Command to change an E-Price value for a specific company in a quote.
        Args:
            eprice_section_widget: The EPriceSectionWidget instance.
            all_quotes_data_ref: Reference to the main self.all_quotes_data.
            quote_name_key: The name of the quote being modified.
            company_name: The name of the E-Price company.
            old_value: The original E-Price value.
            new_value: The new E-Price value.
        """
        super().__init__(description=f"Change {quote_name_key}'s E-Price for {company_name} from '{old_value}' to '{new_value}'")
        self.eprice_section_widget = eprice_section_widget
        self.all_quotes_data_ref = all_quotes_data_ref
        self.quote_name_key = quote_name_key
        self.company_name = company_name
        self.old_value = old_value
        self.new_value = new_value

    def execute(self):
        if self.quote_name_key in self.all_quotes_data_ref:
            quote_data = self.all_quotes_data_ref[self.quote_name_key]
            if "e_price" not in quote_data:
                quote_data["e_price"] = []
            
            # Find and update the company, or add it if not present
            found = False
            for company_data in quote_data["e_price"]:
                if company_data.get("name") == self.company_name:
                    company_data["value"] = self.new_value
                    found = True
                    break
            if not found: # Should not happen if UI is built from fixed list, but good for robustness
                quote_data["e_price"].append({"name": self.company_name, "value": self.new_value})
        
        self.eprice_section_widget.update_company_value(self.company_name, self.new_value, from_command=True)

    def unexecute(self):
        # Similar logic to execute, but sets old_value
        # For simplicity, this assumes the entry always exists after execute. A more robust unexecute might remove it if old_value was empty.
        if self.quote_name_key in self.all_quotes_data_ref and "e_price" in self.all_quotes_data_ref[self.quote_name_key]:
            for company_data in self.all_quotes_data_ref[self.quote_name_key]["e_price"]:
                if company_data.get("name") == self.company_name:
                    company_data["value"] = self.old_value
                    break
        self.eprice_section_widget.update_company_value(self.company_name, self.old_value, from_command=True)

class ChangePEValueCommand(Command):
    def __init__(self, pe_section_widget, all_quotes_data_ref, quote_name_key, company_name, old_value, new_value):
        """
        Command to change a PE value for a specific company in a quote.
        Args:
            pe_section_widget: The PESectionWidget instance.
            all_quotes_data_ref: Reference to the main self.all_quotes_data.
            quote_name_key: The name of the quote being modified.
            company_name: The name of the PE company.
            old_value: The original PE value.
            new_value: The new PE value.
        """
        super().__init__(description=f"Change {quote_name_key}'s PE for {company_name} from '{old_value}' to '{new_value}'")
        self.pe_section_widget = pe_section_widget
        self.all_quotes_data_ref = all_quotes_data_ref
        self.quote_name_key = quote_name_key
        self.company_name = company_name
        self.old_value = old_value
        self.new_value = new_value

    def execute(self):
        if self.quote_name_key in self.all_quotes_data_ref:
            quote_data = self.all_quotes_data_ref[self.quote_name_key]
            if "pe" not in quote_data: # Ensure 'pe' list exists
                quote_data["pe"] = []
            
            found = False
            for company_data in quote_data["pe"]:
                if company_data.get("name") == self.company_name:
                    company_data["value"] = self.new_value
                    found = True
                    break
            if not found:
                quote_data["pe"].append({"name": self.company_name, "value": self.new_value})
        
        self.pe_section_widget.update_company_value(self.company_name, self.new_value, from_command=True)

    def unexecute(self):
        if self.quote_name_key in self.all_quotes_data_ref and "pe" in self.all_quotes_data_ref[self.quote_name_key]:
            for company_data in self.all_quotes_data_ref[self.quote_name_key]["pe"]:
                if company_data.get("name") == self.company_name:
                    company_data["value"] = self.old_value
                    break
        self.pe_section_widget.update_company_value(self.company_name, self.old_value, from_command=True)

class ChangeEPSValueCommand(Command):
    def __init__(self, eps_section_widget, all_quotes_data_ref, quote_name_key,
                 year_name, company_name, field_name, old_value, new_value):
        super().__init__(description=f"Change {quote_name_key}'s EPS {year_name} for {company_name} {field_name} from '{old_value}' to '{new_value}'")
        self.eps_section_widget = eps_section_widget
        self.all_quotes_data_ref = all_quotes_data_ref
        self.quote_name_key = quote_name_key
        self.year_name = year_name
        self.company_name = company_name
        self.field_name = field_name # "value" or "growth"
        self.old_value = old_value
        self.new_value = new_value

    def _find_eps_company_data(self, quote_data):
        if "eps" not in quote_data:
            quote_data["eps"] = []
            
        for year_data_entry in quote_data["eps"]:
            if year_data_entry.get("name") == self.year_name:
                if "companies" not in year_data_entry:
                    year_data_entry["companies"] = []
                for company_data_entry in year_data_entry["companies"]:
                    if company_data_entry.get("name") == self.company_name:
                        return company_data_entry
                # Company not found in this year, create it
                new_comp_data = {"name": self.company_name, "value": "", "growth": ""}
                year_data_entry["companies"].append(new_comp_data)
                return new_comp_data
        # Year not found, create year and company structure
        new_comp_data_for_year = {"name": self.company_name, "value": "", "growth": ""}
        new_year_data = {"name": self.year_name, "companies": [new_comp_data_for_year]}
        quote_data["eps"].append(new_year_data)
        return new_comp_data_for_year

    def execute(self):
        if self.quote_name_key in self.all_quotes_data_ref:
            quote_data = self.all_quotes_data_ref[self.quote_name_key]
            company_eps_data = self._find_eps_company_data(quote_data)
            company_eps_data[self.field_name] = self.new_value
        
        self.eps_section_widget.update_company_eps_field(
            self.year_name, self.company_name, self.field_name, self.new_value, from_command=True
        )

    def unexecute(self):
        if self.quote_name_key in self.all_quotes_data_ref:
            quote_data = self.all_quotes_data_ref[self.quote_name_key]
            company_eps_data = self._find_eps_company_data(quote_data) 
            company_eps_data[self.field_name] = self.old_value
        
        self.eps_section_widget.update_company_eps_field(
            self.year_name, self.company_name, self.field_name, self.old_value, from_command=True
        )

class AddEPSYearCommand(Command):
    def __init__(self, eps_section_widget, all_quotes_data_ref, quote_name_key, year_name_to_add, initial_companies_data=None):
        super().__init__(description=f"Add EPS Year '{year_name_to_add}' to quote '{quote_name_key}'")
        self.eps_section_widget = eps_section_widget
        self.all_quotes_data_ref = all_quotes_data_ref
        self.quote_name_key = quote_name_key
        self.year_name_to_add = year_name_to_add
        # initial_companies_data is the list of company dicts for this year, used when undoing a remove.
        # If None, it's a fresh add, and _add_eps_year_fields will populate with fixed companies.
        self.initial_companies_data = initial_companies_data if initial_companies_data is not None else []

    def execute(self):
        if self.quote_name_key in self.all_quotes_data_ref:
            quote_data = self.all_quotes_data_ref[self.quote_name_key]
            if "eps" not in quote_data:
                quote_data["eps"] = []
            
            # Check if year already exists in data model to prevent duplicates from rapid commands
            if not any(y.get("name") == self.year_name_to_add for y in quote_data["eps"]):
                new_year_data_model = {"name": self.year_name_to_add, "companies": list(self.initial_companies_data)}
                quote_data["eps"].append(new_year_data_model)
                # Sort EPS years in data model (optional, but good for consistency)
                quote_data["eps"].sort(key=lambda y: self.eps_section_widget._get_eps_year_sort_key(y.get("name", "")))

        # UI update
        self.eps_section_widget._add_eps_year_fields(self.year_name_to_add, self.initial_companies_data)
        # _add_eps_year_fields calls _update_visible_eps_years internally

    def unexecute(self):
        removed_year_data_for_redo = None
        if self.quote_name_key in self.all_quotes_data_ref:
            quote_data = self.all_quotes_data_ref[self.quote_name_key]
            if "eps" in quote_data:
                year_to_remove_model = next((y for y in quote_data["eps"] if y.get("name") == self.year_name_to_add), None)
                if year_to_remove_model:
                    removed_year_data_for_redo = year_to_remove_model # Save for potential redo
                    quote_data["eps"].remove(year_to_remove_model)
        
        # UI update
        year_entry_ui_data = next((entry for entry in self.eps_section_widget.eps_year_entries if entry["year_name"] == self.year_name_to_add), None)
        if year_entry_ui_data:
            self.eps_section_widget._remove_dynamic_list_entry(year_entry_ui_data, self.eps_section_widget.eps_year_entries)
            self.eps_section_widget._update_visible_eps_years()
        
        # Store the removed data's companies if we didn't have it initially (for redo of this unexecute)
        if removed_year_data_for_redo and not self.initial_companies_data:
             self.initial_companies_data = removed_year_data_for_redo.get("companies", [])


class RemoveEPSYearCommand(Command):
    def __init__(self, eps_section_widget, all_quotes_data_ref, quote_name_key, year_name_to_remove, removed_year_data_model):
        super().__init__(description=f"Remove EPS Year '{year_name_to_remove}' from quote '{quote_name_key}'")
        self.eps_section_widget = eps_section_widget
        self.all_quotes_data_ref = all_quotes_data_ref
        self.quote_name_key = quote_name_key
        self.year_name_to_remove = year_name_to_remove
        self.removed_year_data_model = removed_year_data_model # e.g., {"name": "2024", "companies": [...]}

    def execute(self): # Same logic as AddEPSYearCommand.unexecute
        if self.quote_name_key in self.all_quotes_data_ref:
            quote_data = self.all_quotes_data_ref[self.quote_name_key]
            if "eps" in quote_data:
                year_to_remove_model = next((y for y in quote_data["eps"] if y.get("name") == self.year_name_to_remove), None)
                if year_to_remove_model:
                    quote_data["eps"].remove(year_to_remove_model)
        
        year_entry_ui_data = next((entry for entry in self.eps_section_widget.eps_year_entries if entry["year_name"] == self.year_name_to_remove), None)
        if year_entry_ui_data:
            self.eps_section_widget._remove_dynamic_list_entry(year_entry_ui_data, self.eps_section_widget.eps_year_entries)
            self.eps_section_widget._update_visible_eps_years()

    def unexecute(self): # Same logic as AddEPSYearCommand.execute
        if self.quote_name_key in self.all_quotes_data_ref:
            quote_data = self.all_quotes_data_ref[self.quote_name_key]
            if "eps" not in quote_data:
                quote_data["eps"] = []
            
            if not any(y.get("name") == self.year_name_to_remove for y in quote_data["eps"]):
                quote_data["eps"].append(self.removed_year_data_model)
                quote_data["eps"].sort(key=lambda y: self.eps_section_widget._get_eps_year_sort_key(y.get("name", "")))

        self.eps_section_widget._add_eps_year_fields(self.year_name_to_remove, self.removed_year_data_model.get("companies", []))


class AddRecordReportCommand(Command):
    def __init__(self, record_widget, all_quotes_data_ref, quote_name_key, report_data_to_add, insert_at_index=0):
        # Description will be set more accurately after UI entry is created
        super().__init__(description="Add Record Report") 
        self.record_widget = record_widget
        self.all_quotes_data_ref = all_quotes_data_ref
        self.quote_name_key = quote_name_key
        self.report_data_to_add = report_data_to_add # dict: {"company": ..., "date": ..., "color": ...}
        self.insert_at_index = insert_at_index # For UI consistency, data model will be sorted
        self.created_ui_entry_data = None # Will store the dict returned by add_report_entry

    def execute(self):
        if self.quote_name_key in self.all_quotes_data_ref:
            quote_data = self.all_quotes_data_ref[self.quote_name_key]
            if "record" not in quote_data:
                quote_data["record"] = []
            quote_data["record"].append(self.report_data_to_add)
            # The main editor's _display_quote or load_data in widget will handle sorting for display
        
        # Add to UI and store the created UI entry data
        self.created_ui_entry_data = self.record_widget.add_report_entry(
            company_str=self.report_data_to_add.get("company", ""),
            date_str=self.report_data_to_add.get("date", ""),
            color_str=self.report_data_to_add.get("color", "default"),
            insert_at_index=self.insert_at_index
        )
        # Update description now that we have more details
        self.description = f"Add Record Report ({self.report_data_to_add.get('company', '')} on {self.report_data_to_add.get('date', '')}) to '{self.quote_name_key}'"

    def unexecute(self):
        if self.quote_name_key in self.all_quotes_data_ref:
            quote_data = self.all_quotes_data_ref[self.quote_name_key]
            if "record" in quote_data and self.report_data_to_add in quote_data["record"]:
                quote_data["record"].remove(self.report_data_to_add)
        
        # Remove the specific UI entry that was created by this command's execute()
        if self.created_ui_entry_data:
            self.record_widget._remove_report_entry(self.created_ui_entry_data)
            self.created_ui_entry_data = None # Clear it after removal
        else:
            # Fallback if created_ui_entry_data wasn't stored (should not happen with new logic)
            # or if trying to unexecute a command that wasn't properly executed.
            print(f"Warning: Could not find specific UI for record report to unexecute add: {self.report_data_to_add}")


class RemoveRecordReportCommand(Command):
    def __init__(self, record_widget, all_quotes_data_ref, quote_name_key, 
                 report_data_model_to_remove, ui_entry_data_to_remove, original_data_model_index):
        super().__init__(description=f"Remove Record Report ({report_data_model_to_remove.get('company', '')} on {report_data_model_to_remove.get('date', '')}) from '{quote_name_key}'")
        self.record_widget = record_widget
        self.all_quotes_data_ref = all_quotes_data_ref
        self.quote_name_key = quote_name_key
        self.report_data_model_to_remove = report_data_model_to_remove # The actual dict from all_quotes_data["record"]
        self.ui_entry_data_to_remove = ui_entry_data_to_remove # The dict from record_widget.report_entries
        self.original_data_model_index = original_data_model_index # Index in all_quotes_data["record"]

    def execute(self):
        # Remove from data model
        if self.quote_name_key in self.all_quotes_data_ref:
            quote_data = self.all_quotes_data_ref[self.quote_name_key]
            if "record" in quote_data and self.report_data_model_to_remove in quote_data["record"]:
                quote_data["record"].remove(self.report_data_model_to_remove)
        
        # Remove from UI
        self.record_widget._remove_report_entry(self.ui_entry_data_to_remove)

    def unexecute(self):
        # Re-add to data model at original index
        if self.quote_name_key in self.all_quotes_data_ref:
            quote_data = self.all_quotes_data_ref[self.quote_name_key]
            if "record" not in quote_data:
                quote_data["record"] = []
            
            # Insert at original index if possible, otherwise append
            if 0 <= self.original_data_model_index <= len(quote_data["record"]):
                quote_data["record"].insert(self.original_data_model_index, self.report_data_model_to_remove)
            else:
                quote_data["record"].append(self.report_data_model_to_remove)
            # The editor's _display_quote or load_data in widget will handle sorting for display if needed

        # Re-add to UI. The add_report_entry method in widget will handle creating new UI elements.
        # We need to determine the correct UI insertion index.
        # For simplicity, we can re-add to top (index 0) or try to match original_data_model_index.
        # However, the widget's load_data will typically rebuild the UI based on sorted data model.
        # So, simply re-adding to data model and letting main editor refresh might be enough,
        # or we can call add_report_entry directly.
        # For now, let widget's load_data handle it after data model is updated.
        # The main editor will call _display_quote which reloads the record section.
        # To be more direct, we can call add_report_entry:
        self.ui_entry_data_to_remove = self.record_widget.add_report_entry( # Re-capture the new UI entry
            company_str=self.report_data_model_to_remove.get("company", ""),
            date_str=self.report_data_model_to_remove.get("date", ""),
            color_str=self.report_data_model_to_remove.get("color", "default"),
            insert_at_index=self.original_data_model_index # Try to insert at a similar position
        )


class ChangeRecordReportDetailCommand(Command):
    def __init__(self, record_widget, all_quotes_data_ref, quote_name_key,
                 report_data_model_ref, # Direct reference to the dict in all_quotes_data["record"]
                 ui_entry_data_ref,     # Direct reference to the dict in record_widget.report_entries
                 field_name, old_value, new_value):
        super().__init__(description=f"Change Record Report {field_name} for '{quote_name_key}' from '{old_value}' to '{new_value}'")
        self.record_widget = record_widget
        self.all_quotes_data_ref = all_quotes_data_ref # Not strictly needed if report_data_model_ref is used
        self.quote_name_key = quote_name_key
        self.report_data_model_ref = report_data_model_ref # The actual dict in the data model
        self.ui_entry_data_ref = ui_entry_data_ref         # The actual dict for the UI entry
        self.field_name = field_name # "company", "date", or "color"
        self.old_value = old_value
        self.new_value = new_value

    def execute(self):
        # Update data model
        self.report_data_model_ref[self.field_name] = self.new_value
        # Update UI
        self.record_widget.update_report_entry_detail(self.ui_entry_data_ref, self.field_name, self.new_value, from_command=True)

    def unexecute(self):
        # Update data model
        self.report_data_model_ref[self.field_name] = self.old_value
        # Update UI
        self.record_widget.update_report_entry_detail(self.ui_entry_data_ref, self.field_name, self.old_value, from_command=True)

class ChangeEPSYearDisplayCommand(Command):
    def __init__(self, eps_section_widget, old_selected_years, new_selected_years):
        super().__init__(description=f"Change displayed EPS years from {old_selected_years} to {new_selected_years}")
        self.eps_section_widget = eps_section_widget
        self.old_selected_years = list(old_selected_years) # Store copies
        self.new_selected_years = list(new_selected_years) # Store copies

    def execute(self):
        self.eps_section_widget.selected_eps_years_to_display = list(self.new_selected_years)
        self.eps_section_widget._update_visible_eps_years()

    def unexecute(self):
        self.eps_section_widget.selected_eps_years_to_display = list(self.old_selected_years)
        self.eps_section_widget._update_visible_eps_years()

class ChangeEPSCompaniesForYearDisplayCommand(Command):
    def __init__(self, eps_section_widget, year_name, old_selected_companies, new_selected_companies):
        super().__init__(description=f"Change displayed companies for EPS year '{year_name}'")
        self.eps_section_widget = eps_section_widget
        self.year_name = year_name
        self.old_selected_companies = list(old_selected_companies) # Store copies
        self.new_selected_companies = list(new_selected_companies) # Store copies

    def execute(self):
        year_entry = next((entry for entry in self.eps_section_widget.eps_year_entries if entry["year_name"] == self.year_name), None)
        if year_entry:
            year_entry["selected_companies_to_display_for_year"] = list(self.new_selected_companies)
            self.eps_section_widget._update_visible_eps_companies_for_year(year_entry)
        else:
            print(f"Warning: Could not find EPS year '{self.year_name}' to change company display during execute.")

    def unexecute(self):
        year_entry = next((entry for entry in self.eps_section_widget.eps_year_entries if entry["year_name"] == self.year_name), None)
        if year_entry:
            year_entry["selected_companies_to_display_for_year"] = list(self.old_selected_companies)
            self.eps_section_widget._update_visible_eps_companies_for_year(year_entry)
        else:
            # This could happen if the year itself was removed by another command then undone.
            # The command to re-add the year should restore its company selections.
            # If this command is undone *after* the year is removed, there's no UI to update.
            # This is generally okay as the state of selected_companies_to_display_for_year
            # is part of the year_entry_data which would be restored by AddEPSYearCommand.unexecute.
            print(f"Warning: Could not find EPS year '{self.year_name}' to change company display during unexecute.")

class ChangeEPriceFixedCompaniesCommand(Command):
    def __init__(self, editor_ref, old_fixed_companies, new_fixed_companies):
        super().__init__(description=f"Change E-Price Fixed Companies List")
        self.editor_ref = editor_ref # Reference to XmlReportEditor instance
        self.old_fixed_companies = list(old_fixed_companies) # Store copies
        self.new_fixed_companies = list(new_fixed_companies) # Store copies

    def execute(self):
        # Update the editor's list
        self.editor_ref.EPRICE_FIXED_COMPANIES = list(self.new_fixed_companies)
        # Trigger UI refresh and save config through editor's methods
        self.editor_ref._load_eprice_config_and_update_ui() # This refreshes all relevant sections
        # data_utils.save_eprice_config is called within _load_eprice_config_and_update_ui
        # if the list actually changed and needs saving, or we can call it explicitly.
        # For clarity and to ensure it's always saved with the command:
        self.editor_ref.save_current_eprice_config() # New method in editor

    def unexecute(self):
        # Revert the editor's list
        self.editor_ref.EPRICE_FIXED_COMPANIES = list(self.old_fixed_companies)
        # Trigger UI refresh and save config
        self.editor_ref._load_eprice_config_and_update_ui()
        self.editor_ref.save_current_eprice_config() # New method in editor

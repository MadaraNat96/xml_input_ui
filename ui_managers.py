# t:\Work\xml_input_ui\ui_managers.py

class GlobalHighlightManager:
    def __init__(self, eprice_widget, eps_widget, pe_widget):
        self.eprice_section_widget = eprice_widget
        self.eps_section_widget = eps_widget
        self.pe_section_widget = pe_widget

        self.globally_focused_company_widgets = {}  # {company_name: set(QLineEdit_widgets)}
        self.active_highlighted_company = None

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
            if not self.globally_focused_company_widgets[company_name]:  # Set is now empty
                del self.globally_focused_company_widgets[company_name]

        # If this company was the active highlighted one and now has no focused widgets, unhighlight it
        if self.active_highlighted_company == company_name and \
           company_name not in self.globally_focused_company_widgets:
            self._update_highlight_for_company(self.active_highlighted_company, False)
            self.active_highlighted_company = None

    def _update_highlight_for_company(self, company_name_to_update, highlight_state):
        if self.eprice_section_widget:
            self.eprice_section_widget.update_company_highlight_state(company_name_to_update, highlight_state)
        if self.eps_section_widget:
            self.eps_section_widget.update_company_highlight_state(company_name_to_update, highlight_state)
        if self.pe_section_widget:
            self.pe_section_widget.update_company_highlight_state(company_name_to_update, highlight_state)

    def clear_active_highlight(self):
        if self.active_highlighted_company:
            self._update_highlight_for_company(self.active_highlighted_company, False)
            self.active_highlighted_company = None
        self.globally_focused_company_widgets.clear()
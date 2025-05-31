# t:\Work\xml_input_ui\dialogs.py
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QListWidget, QAbstractItemView,
    QDialogButtonBox, QMessageBox, QHBoxLayout, QLineEdit, QPushButton
)
from PyQt6.QtCore import Qt # Though Qt might not be directly used in all dialogs after splitting

class EPSYearSelectionDialog(QDialog):
    def __init__(self, available_year_names, currently_selected_names, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Choose EPS Years to Display")
        self.setMinimumWidth(300)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Select up to two EPS years to display from the list below:"))

        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        
        for name in available_year_names:
            self.list_widget.addItem(name)
            if name in currently_selected_names:
                items = self.list_widget.findItems(name, Qt.MatchFlag.MatchExactly)
                if items:
                    items[0].setSelected(True)
        
        layout.addWidget(self.list_widget)

        self.instruction_label = QLabel("You can select up to 2 years.")
        layout.addWidget(self.instruction_label)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def get_selected_years(self):
        selected_items = [item.text() for item in self.list_widget.selectedItems()]
        if len(selected_items) > 2:
            QMessageBox.warning(self, "Selection Limit", 
                                "You selected more than two years. Only the first two selected will be used.")
            return selected_items[:2]
        return selected_items

class EPriceCompanySelectionDialog(QDialog):
    def __init__(self, all_fixed_company_names, currently_selected_names, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Choose E-Price Companies to Display")
        self.setMinimumWidth(300)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Select companies to display from the list below:"))

        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        
        for name in all_fixed_company_names: # These are already in the desired order
            self.list_widget.addItem(name)
            if name in currently_selected_names:
                items = self.list_widget.findItems(name, Qt.MatchFlag.MatchExactly)
                if items:
                    items[0].setSelected(True)
        
        layout.addWidget(self.list_widget)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def get_selected_companies(self):
        return [item.text() for item in self.list_widget.selectedItems()]

class ManageEPriceCompaniesDialog(QDialog):
    def __init__(self, current_companies, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Manage Fixed E-Price Companies")
        self.setMinimumSize(400, 300)
        self.companies = [c.upper() for c in current_companies] 

        main_layout = QVBoxLayout(self)

        self.list_widget = QListWidget()
        self.list_widget.addItems(self.companies)
        main_layout.addWidget(self.list_widget)

        add_layout = QHBoxLayout()
        self.new_company_edit = QLineEdit()
        self.new_company_edit.setPlaceholderText("Enter new company name")
        add_button = QPushButton("Add Company")
        add_button.clicked.connect(self._add_company)
        add_layout.addWidget(self.new_company_edit)
        add_layout.addWidget(add_button)
        main_layout.addLayout(add_layout)

        actions_layout = QHBoxLayout()
        remove_button = QPushButton("Remove Selected Company")
        remove_button.clicked.connect(self._remove_company)
        actions_layout.addWidget(remove_button)

        move_up_button = QPushButton("Move Up")
        move_up_button.clicked.connect(self._move_item_up)
        actions_layout.addWidget(move_up_button)

        move_down_button = QPushButton("Move Down")
        move_down_button.clicked.connect(self._move_item_down)
        actions_layout.addWidget(move_down_button)
        
        main_layout.addLayout(actions_layout)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)

    def _add_company(self):
        company_name = self.new_company_edit.text().strip().upper() 
        if company_name:
            if company_name not in [self.list_widget.item(i).text() for i in range(self.list_widget.count())]:
                self.list_widget.addItem(company_name) 
                self.new_company_edit.clear()
            else:
                QMessageBox.information(self, "Duplicate", f"Company '{company_name}' already in the list.")
        else:
            QMessageBox.warning(self, "Input Error", "Company name cannot be empty.")

    def _remove_company(self):
        selected_items = self.list_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Selection Error", "Please select a company to remove.")
            return
        for item in selected_items:
            self.list_widget.takeItem(self.list_widget.row(item)) 

    def _move_item_up(self):
        current_item = self.list_widget.currentItem()
        if current_item:
            current_row = self.list_widget.row(current_item)
            if current_row > 0:
                item = self.list_widget.takeItem(current_row)
                self.list_widget.insertItem(current_row - 1, item)
                self.list_widget.setCurrentItem(item) 

    def _move_item_down(self):
        current_item = self.list_widget.currentItem()
        if current_item:
            current_row = self.list_widget.row(current_item)
            if current_row < self.list_widget.count() - 1:
                item = self.list_widget.takeItem(current_row)
                self.list_widget.insertItem(current_row + 1, item)
                self.list_widget.setCurrentItem(item) 

    def get_updated_companies(self):
        return [self.list_widget.item(i).text() for i in range(self.list_widget.count())]

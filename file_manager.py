# t:\Work\xml_input_ui\file_manager.py
import os
from PyQt6.QtWidgets import QFileDialog, QMessageBox
import data_utils

class FileManager:
    def __init__(self, editor_ref):
        """
        Manages file operations for the XmlReportEditor.
        Args:
            editor_ref: A reference to the XmlReportEditor instance.
        """
        self.editor = editor_ref  # To call editor methods like collect_data_for_xml, _set_dirty_flag etc.
        self.current_file_path = None

    def get_current_file_path(self):
        return self.current_file_path

    def open_file(self):
        """
        Opens an XML file using a dialog, parses it, and returns the data.
        Returns:
            tuple: (file_path, root_date_qdate, all_quotes_data_dict) or (None, None, None) on failure/cancel.
        """
        file_path, _ = QFileDialog.getOpenFileName(
            self.editor, "Open XML File", "", "XML Files (*.xml);;All Files (*)"
        )
        if not file_path:
            return None, None, None

        file_path, root_date, quotes_data = data_utils.parse_xml_data(file_path)
        if root_date is not None or quotes_data is not None: # Allow opening even if one part is missing but file is valid
            self.current_file_path = file_path
            return self.current_file_path, root_date, quotes_data
        # If parse_xml_data returned None, None (e.g. critical error), it would have shown a message.
        return None, None, None

    def save_file(self, data_for_xml_func):
        """
        Saves the current data to the current_file_path or prompts for Save As if no path exists.
        Args:
            data_for_xml_func: A callable that returns the data to be saved.
        Returns:
            bool: True if save was successful, False otherwise.
        """
        if not self.current_file_path:
            return self.save_file_as(data_for_xml_func)
        
        return self._perform_save_internal(self.current_file_path, data_for_xml_func)

    def save_file_as(self, data_for_xml_func):
        """
        Prompts the user for a file path and saves the data.
        Args:
            data_for_xml_func: A callable that returns the data to be saved.
        Returns:
            bool: True if save was successful, False otherwise.
        """
        default_path = self.current_file_path if self.current_file_path else os.path.join(os.getcwd(), "report_output.xml")
        file_path_dialog, _ = QFileDialog.getSaveFileName(
            self.editor, "Save XML File As", default_path, "XML Files (*.xml);;All Files (*)"
        )
        if not file_path_dialog:
            return False # User cancelled
        
        return self._perform_save_internal(file_path_dialog, data_for_xml_func)

    def _perform_save_internal(self, file_path_to_save, data_for_xml_func):
        collected_data = data_for_xml_func()
        root_element = data_utils.build_xml_tree(collected_data)
        
        if data_utils.save_xml_to_file(file_path_to_save, root_element):
            QMessageBox.information(self.editor, "Success", f"XML saved to {file_path_to_save}")
            self.current_file_path = file_path_to_save
            return True
        # data_utils.save_xml_to_file shows its own error message
        return False
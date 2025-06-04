# t:\Work\xml_input_ui\tests\test_data_utils.py
import unittest
import os
from unittest.mock import patch, mock_open, MagicMock, call
import xml.etree.ElementTree as ET
from PyQt6.QtCore import QDate
from PyQt6.QtWidgets import QMessageBox # For mocking
import data_utils

class TestDataUtils(unittest.TestCase):

    @patch('data_utils.QDate.currentDate')
    def test_get_default_working_date(self, mock_current_date):
        # Test weekday
        mock_current_date.return_value = QDate(2023, 10, 27) # Friday
        self.assertEqual(data_utils.get_default_working_date(), QDate(2023, 10, 27))

        # Test Saturday
        mock_current_date.return_value = QDate(2023, 10, 28) # Saturday
        self.assertEqual(data_utils.get_default_working_date(), QDate(2023, 10, 27)) # Should be Friday

        # Test Sunday
        mock_current_date.return_value = QDate(2023, 10, 29) # Sunday
        self.assertEqual(data_utils.get_default_working_date(), QDate(2023, 10, 27)) # Should be Friday

        # Test Monday
        mock_current_date.return_value = QDate(2023, 10, 30) # Monday
        self.assertEqual(data_utils.get_default_working_date(), QDate(2023, 10, 30))

    @patch('data_utils.os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    @patch('data_utils.QMessageBox.warning') # Mock QMessageBox
    @patch('data_utils.save_eprice_config') # Mock save to check if it's called
    def test_load_eprice_config_success(self, mock_save_config, mock_qmessagebox, mock_file_open, mock_exists):
        mock_exists.return_value = True
        default_list = ["DEFAULT1", "DEFAULT2"]
        
        # Configure the mock file handle (mock_file_open.return_value)
        mock_file_handle = mock_file_open.return_value
        mock_file_handle.__iter__.return_value = iter(["CompanyA\n", "CompanyB\n", "CompanyA\n"])
        mock_file_handle.readlines.return_value = ["CompanyA\n", "CompanyB\n", "CompanyA\n"] # Keep for completeness

        companies = data_utils.load_eprice_config(default_list)

        self.assertEqual(companies, ["COMPANYA", "COMPANYB"]) # Should be unique and uppercase
        mock_exists.assert_called_once_with(data_utils.EPRICE_CONFIG_FILE)
        mock_file_open.assert_called_once_with(data_utils.EPRICE_CONFIG_FILE, 'r', encoding='utf-8')
        mock_qmessagebox.assert_not_called()
        mock_save_config.assert_not_called()

    @patch('data_utils.os.path.exists') # mock_exists
    @patch('builtins.open', new_callable=mock_open) # mock_file_open
    @patch('data_utils.QMessageBox.warning') # mock_qmessagebox
    @patch('data_utils.save_eprice_config') # mock_save_config
    def test_load_eprice_config_file_not_found(self, mock_save_config, mock_qmessagebox, mock_file_open, mock_exists):
        # Test file not found
        mock_exists.return_value = False
        default_list = ["DEFAULT1", "DEFAULT2"]
        companies = data_utils.load_eprice_config(default_list)

        self.assertEqual(companies, default_list)
        mock_exists.assert_called_once_with(data_utils.EPRICE_CONFIG_FILE)
        mock_file_open.assert_not_called() # File not found, so open is not called
        mock_qmessagebox.assert_not_called()
        mock_save_config.assert_called_once_with(default_list) # Should save default
        
    @patch('data_utils.os.path.exists') # mock_exists
    @patch('builtins.open', new_callable=mock_open) # mock_file_open
    @patch('data_utils.QMessageBox.warning') # mock_qmessagebox
    @patch('data_utils.save_eprice_config') # mock_save_config
    def test_load_eprice_config_file_empty(self, mock_save_config, mock_qmessagebox, mock_file_open, mock_exists):
        # Test file is empty
        default_list = ["DEFAULT1", "DEFAULT2"] # Define default_list here
        mock_exists.return_value = True
        mock_file_open.return_value.readlines.return_value = [] # Simulate empty file
        companies = data_utils.load_eprice_config(default_list)

        self.assertEqual(companies, default_list)
        mock_exists.assert_called_once_with(data_utils.EPRICE_CONFIG_FILE)
        mock_file_open.assert_called_once_with(data_utils.EPRICE_CONFIG_FILE, 'r', encoding='utf-8')
        mock_qmessagebox.assert_not_called() # QMessageBox.warning should not be called for empty file
        mock_save_config.assert_called_once_with(default_list) # Should save default if file is empty
        
    @patch('data_utils.os.path.exists', return_value=True)
    @patch('builtins.open', side_effect=IOError("Test error"))
    @patch('data_utils.QMessageBox.warning')
    @patch('data_utils.save_eprice_config')
    def test_load_eprice_config_file_read_error(self, mock_save_config, mock_qmessagebox, mock_file_open, mock_exists):
        default_list = ["DEFAULT1", "DEFAULT2"]
        companies = data_utils.load_eprice_config(default_list)

        self.assertEqual(companies, default_list)
        mock_qmessagebox.assert_called_once()
        # Check that save_eprice_config was called with the default list upon error
        mock_save_config.assert_called_once_with(default_list)


    @patch('builtins.open', new_callable=mock_open)
    @patch('data_utils.QMessageBox.warning') # Mock QMessageBox
    def test_save_eprice_config_success(self, mock_warning, mock_file):
        fixed_list = ["CompanyA", "CompanyB"]
        data_utils.save_eprice_config(fixed_list)

        mock_file.assert_called_once_with(data_utils.EPRICE_CONFIG_FILE, 'w', encoding='utf-8')
        mock_file().write.assert_has_calls([call("CompanyA\n"), call("CompanyB\n")])
        mock_warning.assert_not_called()

    @patch('builtins.open', side_effect=IOError("Test save error"))
    @patch('data_utils.QMessageBox.warning')
    def test_save_eprice_config_error(self, mock_warning, mock_file_open):
        fixed_list = ["CompanyA", "CompanyB"]
        data_utils.save_eprice_config(fixed_list)

        mock_warning.assert_called_once()
        mock_file_open.assert_called_once_with(data_utils.EPRICE_CONFIG_FILE, 'w', encoding='utf-8')


    @patch('data_utils.ET.parse')
    @patch('data_utils.QMessageBox.critical')
    def test_parse_xml_data_file_not_found(self, mock_critical, mock_parse):
        mock_parse.side_effect = FileNotFoundError
        file_path, root_date, quotes_data = data_utils.parse_xml_data("non_existent_file.xml")
        self.assertIsNone(file_path)
        self.assertIsNone(root_date) # parse_xml_data returns None on error
        self.assertIsNone(quotes_data) # parse_xml_data returns None on error
        mock_critical.assert_called_once()

    @patch('data_utils.ET.parse')
    @patch('data_utils.QMessageBox.critical')
    def test_parse_xml_data_parse_error(self, mock_critical, mock_parse):
        mock_parse.side_effect = ET.ParseError("Invalid XML")
        file_path, root_date, quotes_data = data_utils.parse_xml_data("invalid_file.xml")
        self.assertIsNone(file_path)
        self.assertIsNone(root_date) # parse_xml_data returns None on error
        self.assertIsNone(quotes_data) # parse_xml_data returns None on error
        mock_critical.assert_called_once()

    @patch('data_utils.QMessageBox.warning')
    def test_parse_xml_data_quote_without_name(self, mock_warning):
        xml_content_no_name = """
        <root>
            <date>10/26/2023</date>
            <quotes>
                <quote><price>100</price></quote>
            </quotes>
        </root>
        """
        # Use a temporary file to simulate reading
        tmp_file_path = "temp_test_no_name.xml"
        with open(tmp_file_path, "w") as f:
            f.write(xml_content_no_name)

        file_path, root_date, quotes_data = data_utils.parse_xml_data(tmp_file_path)

        self.assertEqual(file_path, tmp_file_path)
        self.assertIsNotNone(root_date) # Default date is returned even on parse error
        self.assertEqual(len(quotes_data), 0) # Quote should be skipped
        mock_warning.assert_called_once_with(None, "XML Warning", "Found a quote without a name. Skipping.")

        os.remove(tmp_file_path)


    def test_parse_xml_data_success(self):
        xml_content = """
        <root>
            <date>10/26/2023</date>
            <quotes>
                <quote>
                    <name>AAPL</name>
                    <price>175.0</price>
                    <e_price>
                        <company><name>VCSC</name><value>5.0</value></company>
                    </e_price>
                    <eps>
                        <year><name>2023</name><company><name>MSFT</name><value>1.0</value><growth>5%</growth></company></year>
                    </eps>
                    <pe>
                        <company><name>MSFT</name><value>27.0</value></company>
                    </pe>
                    <record>
                        <report><company>MSFT</company><date>01/01/2023</date><color>red</color></report>
                    </record>
                </quote>
            </quotes>
        </root>
        """
        # Use a temporary file to simulate reading
        tmp_file_path = "temp_test.xml"
        with open(tmp_file_path, "w") as f:
            f.write(xml_content)

        file_path, root_date, quotes_data = data_utils.parse_xml_data(tmp_file_path)

        self.assertEqual(file_path, tmp_file_path)
        self.assertEqual(root_date, QDate(2023, 10, 26))
        self.assertIn("AAPL", quotes_data)
        self.assertEqual(quotes_data["AAPL"]["name"], "AAPL")
        self.assertEqual(quotes_data["AAPL"]["price"], "175.0")
        self.assertEqual(quotes_data["AAPL"]["e_price"][0]["name"], "VCSC")
        self.assertEqual(quotes_data["AAPL"]["e_price"][0]["value"], "5.0")
        self.assertEqual(quotes_data["AAPL"]["eps"][0]["name"], "2023") # Check year name
        self.assertEqual(quotes_data["AAPL"]["eps"][0]["companies"][0]["name"], "MSFT")
        self.assertEqual(quotes_data["AAPL"]["eps"][0]["companies"][0]["value"], "1.0")
        self.assertEqual(quotes_data["AAPL"]["eps"][0]["companies"][0]["growth"], "5%")
        self.assertEqual(quotes_data["AAPL"]["pe"][0]["name"], "MSFT")
        self.assertEqual(quotes_data["AAPL"]["pe"][0]["value"], "27.0")
        self.assertEqual(quotes_data["AAPL"]["record"][0]["company"], "MSFT")
        self.assertEqual(quotes_data["AAPL"]["record"][0]["date"], "01/01/2023")
        self.assertEqual(quotes_data["AAPL"]["record"][0]["color"], "red")


        os.remove(tmp_file_path)

    def test_build_xml_tree(self):
        data_for_xml = {
            "date": "10/27/2023",
            "quotes": [
                {
                    "name": "AAPL",
                    "price": "175.0",
                    "e_price": [{"name": "VCSC", "value": "5.0"}],
                    "eps": [{"name": "2023", "companies": [{"name": "MSFT", "value": "1.0", "growth": "15%"}]}],
                    "pe": [{"name": "MSFT", "value": "27.0"}],
                    "record": [{"company": "MSFT", "date": "01/01/2023", "color": "green"},
                               {"company": "GOOG", "date": "01/02/2023", "color": "red"}, # Added color
                               {"company": "AMZN", "date": "01/03/2023", "color": "default"}] # Default color
                },
                 { # Quote with missing optional data
                    "name": "GOOG",
                    "price": "135.0",
                    "e_price": [],
                    "eps": [],
                    "pe": [],
                    "record": []
                }
            ]
        }

        root_el = data_utils.build_xml_tree(data_for_xml)

        self.assertEqual(root_el.findtext("date"), "10/27/2023")
        quotes_el = root_el.find("quotes")
        self.assertIsNotNone(quotes_el)
        self.assertEqual(len(quotes_el.findall("quote")), 2)

        # Check AAPL data
        aapl_el = next(q for q in quotes_el.findall("quote") if q.findtext("name") == "AAPL")
        self.assertIsNotNone(aapl_el)
        self.assertEqual(aapl_el.findtext("price"), "175.0")
        self.assertEqual(aapl_el.find("e_price/company/name").text, "VCSC")
        self.assertEqual(aapl_el.find("eps/year/company/growth").text, "15%")
        self.assertEqual(aapl_el.find("pe/company/value").text, "27.0")
        self.assertEqual(aapl_el.find("record/report/color").text, "green")
        # Check that the report with "default" color does not have a <color> tag
        report_elements = aapl_el.findall("record/report")
        amazon_report = next(r for r in report_elements if r.findtext("company") == "AMZN")
        self.assertIsNone(amazon_report.find("color"))


        # Check GOOG data (should have minimal elements)
        goog_el = next(q for q in quotes_el.findall("quote") if q.findtext("name") == "GOOG")
        self.assertIsNotNone(goog_el)
        self.assertEqual(goog_el.findtext("price"), "135.0")
        self.assertIsNone(goog_el.find("e_price"))
        self.assertIsNone(goog_el.find("eps"))
        self.assertIsNone(goog_el.find("pe"))
        self.assertIsNone(goog_el.find("record"))


    @patch('xml.dom.minidom.parseString')
    @patch('builtins.open', new_callable=mock_open)
    @patch('data_utils.QMessageBox.critical')
    def test_save_xml_to_file_success(self, mock_critical, mock_open, mock_dom_parse):
        mock_dom = MagicMock()
        mock_dom.toprettyxml.return_value = "<pretty/>"
        mock_dom_parse.return_value = mock_dom

        mock_root_element = ET.Element("root") # Mock root element
        success = data_utils.save_xml_to_file("dummy_path.xml", mock_root_element)

        self.assertTrue(success)
        mock_open.assert_called_once_with("dummy_path.xml", "w", encoding="utf-8")
        mock_open().write.assert_called_once_with("<pretty/>")
        mock_critical.assert_not_called()

    @patch('xml.dom.minidom.parseString')
    @patch('builtins.open', new_callable=mock_open)
    @patch('data_utils.QMessageBox.critical')
    def test_save_xml_to_file_error(self, mock_critical, mock_open, mock_dom_parse):
        mock_dom = MagicMock()
        mock_dom.toprettyxml.return_value = "<pretty/>"
        mock_dom_parse.return_value = mock_dom

        mock_open.side_effect = IOError("Disk full")

        mock_root_element = ET.Element("root")

        success = data_utils.save_xml_to_file("dummy_path.xml", mock_root_element)

        self.assertFalse(success)
        mock_open.assert_called_once_with("dummy_path.xml", "w", encoding="utf-8")
        mock_critical.assert_called_once()

# t:\Work\xml_input_ui\data_utils.py
import os
import xml.etree.ElementTree as ET
from xml.dom import minidom
from PyQt6.QtCore import QDate
from PyQt6.QtWidgets import QMessageBox # For error messages directly from utils

EPRICE_CONFIG_FILE = "eprice_companies.cfg"

def get_default_working_date():
    """Returns the current date, or the preceding Friday if today is a weekend."""
    today = QDate.currentDate()
    day_of_week = today.dayOfWeek()  # Monday = 1, ..., Sunday = 7
    if day_of_week == 6:  # Saturday
        return today.addDays(-1)
    elif day_of_week == 7:  # Sunday
        return today.addDays(-2)
    return today

def load_eprice_config(default_fixed_list):
    """Loads E-Price companies from config or uses/saves defaults."""
    loaded_companies = []
    if os.path.exists(EPRICE_CONFIG_FILE):
        try:
            with open(EPRICE_CONFIG_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    company_name = line.strip().upper()
                    if company_name:
                        loaded_companies.append(company_name)
        except Exception as e:
            QMessageBox.warning(None, "Config Load Error",
                                f"Could not load E-Price companies from '{EPRICE_CONFIG_FILE}': {e}\n"
                                "Using default list.")
            # Fallback to default and attempt to save it
            save_eprice_config(default_fixed_list)
            return list(default_fixed_list) # Return a copy

    # Ensure uniqueness while preserving order from file
    unique_ordered_companies = []
    seen = set()
    for comp in loaded_companies:
        if comp not in seen:
            unique_ordered_companies.append(comp)
            seen.add(comp)
    
    if unique_ordered_companies:
        return unique_ordered_companies
    else:
        # File was empty or had no valid names, use default and save it
        save_eprice_config(default_fixed_list)
        return list(default_fixed_list) # Return a copy

def save_eprice_config(fixed_list):
    """Saves the list of E-Price companies to the config file."""
    try:
        with open(EPRICE_CONFIG_FILE, 'w', encoding='utf-8') as f:
            for company_name in fixed_list: # Assumes fixed_list is already ordered and unique
                f.write(f"{company_name}\n")
    except Exception as e:
        QMessageBox.warning(None, "Config Save Error",
                            f"Could not save E-Price companies to '{EPRICE_CONFIG_FILE}': {e}")

def parse_xml_data(file_path):
    """Parses the XML report file and extracts data."""
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
    except FileNotFoundError:
        QMessageBox.critical(None, "Error", f"File not found: {file_path}")
        return None, None
    except ET.ParseError as e:
        QMessageBox.critical(None, "Error", f"Error parsing XML file: {file_path}\n{e}")
        return None, None

    root_date_qdate = get_default_working_date()
    date_el = root.find("date")
    if date_el is not None and date_el.text:
        parsed_date = QDate.fromString(date_el.text, "MM/dd/yyyy")
        if parsed_date.isValid():
            root_date_qdate = parsed_date

    all_quotes_data_dict = {}
    quotes_el = root.find("quotes")
    if quotes_el is not None:
        for quote_el in quotes_el.findall("quote"):
            quote_name = quote_el.findtext("name", default="")
            if not quote_name:
                QMessageBox.warning(None, "XML Warning", "Found a quote without a name. Skipping.")
                continue
            
            current_quote_data_entry = {
                "name": quote_name,
                "price": quote_el.findtext("price", default=""),
                "e_price": [], "eps": [], "pe": [], "record": []
            }
            
            eprice_parent_el = quote_el.find("e_price")
            if eprice_parent_el is not None:
                for company_el in eprice_parent_el.findall("company"):
                    current_quote_data_entry["e_price"].append({
                        "name": company_el.findtext("name", default=""),
                        "value": company_el.findtext("value", default="")
                    })
            
            eps_parent_el = quote_el.find("eps")
            if eps_parent_el is not None:
                for year_el in eps_parent_el.findall("year"):
                    year_eps_data = {
                        "name": year_el.findtext("name", default=""),
                        "companies": []
                    }
                    for company_sub_el in year_el.findall("company"):
                        year_eps_data["companies"].append({
                            "name": company_sub_el.findtext("name", default=""),
                            "value": company_sub_el.findtext("value", default=""),
                            "growth": company_sub_el.findtext("growth", default="")
                        })
                    current_quote_data_entry["eps"].append(year_eps_data)

            pe_parent_el = quote_el.find("pe")
            if pe_parent_el is not None:
                for company_el in pe_parent_el.findall("company"):
                    current_quote_data_entry["pe"].append({
                        "name": company_el.findtext("name", default=""),
                        "value": company_el.findtext("value", default="")
                    })
            
            record_parent_el = quote_el.find("record")
            if record_parent_el is not None:
                for report_el in record_parent_el.findall("report"):
                    current_quote_data_entry["record"].append({
                        "company": report_el.findtext("company", default=""),
                        "date": report_el.findtext("date", default=""),
                        "color": report_el.findtext("color", default="") # Read color
                    })
            all_quotes_data_dict[quote_name] = current_quote_data_entry
            
    return root_date_qdate, all_quotes_data_dict

def build_xml_tree(data_for_xml):
    """Generates an XML ElementTree from the collected data."""
    root_el = ET.Element("root")
    ET.SubElement(root_el, "date").text = data_for_xml.get("date", "")
    quotes_el = ET.SubElement(root_el, "quotes")

    for quote_data in data_for_xml.get("quotes", []):
        if not quote_data.get("name"): 
            continue
        quote_el = ET.SubElement(quotes_el, "quote")
        ET.SubElement(quote_el, "name").text = quote_data.get("name", "")
        ET.SubElement(quote_el, "price").text = quote_data.get("price", "")

        eprice_data_list = quote_data.get("e_price", [])
        if eprice_data_list:
            eprice_el_parent = ET.SubElement(quote_el, "e_price")
            for company_data in eprice_data_list:
                company_el = ET.SubElement(eprice_el_parent, "company")
                ET.SubElement(company_el, "name").text = company_data.get("name", "")
                ET.SubElement(company_el, "value").text = company_data.get("value", "")
        
        eps_data_list = quote_data.get("eps", [])
        if eps_data_list:
            eps_el_parent = ET.SubElement(quote_el, "eps")
            for year_data in eps_data_list:
                year_el = ET.SubElement(eps_el_parent, "year")
                ET.SubElement(year_el, "name").text = year_data.get("name", "")
                companies_list_for_year = year_data.get("companies", [])
                for company_data_eps in companies_list_for_year:
                    company_el = ET.SubElement(year_el, "company")
                    ET.SubElement(company_el, "name").text = company_data_eps.get("name", "")
                    ET.SubElement(company_el, "value").text = company_data_eps.get("value", "")
                    ET.SubElement(company_el, "growth").text = company_data_eps.get("growth", "")

        pe_data_list = quote_data.get("pe", [])
        if pe_data_list:
            pe_el_parent = ET.SubElement(quote_el, "pe")
            for company_data in pe_data_list:
                company_el = ET.SubElement(pe_el_parent, "company")
                ET.SubElement(company_el, "name").text = company_data.get("name", "")
                ET.SubElement(company_el, "value").text = company_data.get("value", "")

        record_data_list = quote_data.get("record", [])
        if record_data_list:
            record_el_parent = ET.SubElement(quote_el, "record")
            for report_data in record_data_list:
                report_el = ET.SubElement(record_el_parent, "report")
                ET.SubElement(report_el, "company").text = report_data.get("company", "")
                ET.SubElement(report_el, "date").text = report_data.get("date", "")
                color_value = report_data.get("color")
                if color_value and color_value != "default": # Write color only if it's set and not "default"
                    ET.SubElement(report_el, "color").text = color_value
    return root_el

def save_xml_to_file(file_path_to_save, root_element):
    """Saves the XML ElementTree to a file with pretty printing."""
    xml_str = ET.tostring(root_element, encoding='unicode')
    dom = minidom.parseString(xml_str)
    pretty_xml_str = dom.toprettyxml(indent="    ")
    try:
        with open(file_path_to_save, "w", encoding="utf-8") as f:
            f.write('\n'.join(line for line in pretty_xml_str.split('\n') if line.strip()))
        return True
    except Exception as e:
        QMessageBox.critical(None, "Error Saving File", f"Could not save file: {e}")
        return False

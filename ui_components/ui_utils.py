# t:\Work\xml_input_ui\ui_components\ui_utils.py

def _clear_qt_layout(layout):
    """Recursively clears all widgets and sub-layouts from a given layout."""
    if layout is not None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            else:
                sub_layout = item.layout()
                if sub_layout is not None:
                    _clear_qt_layout(sub_layout) # Recursive call

import zipfile
import xml.etree.ElementTree as ET


def _get_creating_app(file_path):
    """Return the creating application string from docProps/app.xml, or empty string."""
    try:
        with zipfile.ZipFile(file_path, 'r') as z:
            if 'docProps/app.xml' not in z.namelist():
                return ""
            with z.open('docProps/app.xml') as app_xml:
                root = ET.parse(app_xml).getroot()
                ns = {'ep': 'http://schemas.openxmlformats.org/officeDocument/2006/extended-properties'}
                app_elem = root.find('ep:Application', ns)
                if app_elem is not None and app_elem.text:
                    return app_elem.text
    except Exception:
        pass
    return ""


def check_gdocs(file_path):
    """
    Detects if a .docx was exported from Google Docs and adds contextual notes
    about the limitations of analysis for such files.

    Args:
        file_path (str): Path to the .docx file.

    Returns:
        list: [GDOCS]-prefixed finding strings, or empty list if not a Google Docs file.
    """
    app_name = _get_creating_app(file_path)
    if "google" not in app_name.lower():
        return []

    return [
        "[GDOCS] Exported from Google Docs — RSID sessions will be absent "
        "(Google Docs does not use Word's RSID revision system).",
        "[GDOCS] Revision count in metadata reflects the export count, not actual editing history.",
        "[GDOCS] Timestamps represent the export date from Google Docs, not the original creation date.",
        "[GDOCS] Tracked changes will not appear — Google Docs change tracking is not preserved "
        "in .docx exports.",
    ]

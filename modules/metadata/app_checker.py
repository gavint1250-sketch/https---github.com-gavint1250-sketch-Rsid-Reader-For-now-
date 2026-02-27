
import zipfile
import xml.etree.ElementTree as ET


def check_app_properties(file_path):
    """
    Reads docProps/app.xml from inside the .docx ZIP to report the
    application that created the document (e.g. 'Google Docs', 'Microsoft Word').

    Args:
        file_path (str): The path to the .docx file.

    Returns:
        list: Finding strings with the application name and version, if available.
    """
    findings = []
    try:
        with zipfile.ZipFile(file_path, 'r') as z:
            if 'docProps/app.xml' not in z.namelist():
                findings.append("[APP] docProps/app.xml not found — creating application unknown.")
                return findings

            with z.open('docProps/app.xml') as app_xml:
                root = ET.parse(app_xml).getroot()
                ns = {'ep': 'http://schemas.openxmlformats.org/officeDocument/2006/extended-properties'}

                app_elem    = root.find('ep:Application', ns)
                version_elem = root.find('ep:AppVersion', ns)

                if app_elem is not None and app_elem.text:
                    findings.append(f"[APP] Created with: {app_elem.text}")
                else:
                    findings.append("[APP] Application field is blank.")

                if version_elem is not None and version_elem.text:
                    findings.append(f"[APP] App version: {version_elem.text}")

    except zipfile.BadZipFile:
        findings.append("[APP] Could not read app properties — file is not a valid .docx.")
    except Exception as e:
        findings.append(f"[APP] Error reading app properties: {e}")

    return findings

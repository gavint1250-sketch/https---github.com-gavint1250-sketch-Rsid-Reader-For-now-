
import zipfile
import xml.etree.ElementTree as ET


def check_track_changes(file_path):
    """
    Checks for tracked insertions (w:ins) and deletions (w:del) in the document XML.

    Args:
        file_path (str): The path to the .docx file.

    Returns:
        list: Finding strings reporting tracked change counts.
    """
    findings = []
    try:
        with zipfile.ZipFile(file_path, 'r') as z:
            if 'word/document.xml' not in z.namelist():
                findings.append("[TRACK] word/document.xml not found.")
                return findings

            with z.open('word/document.xml') as doc_xml:
                root = ET.parse(doc_xml).getroot()
                w = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'

                insertions = root.findall(f'.//{w}ins')
                deletions  = root.findall(f'.//{w}del')

                if insertions or deletions:
                    findings.append(f"[TRACK] Tracked insertions found: {len(insertions)}")
                    findings.append(f"[TRACK] Tracked deletions found: {len(deletions)}")
                else:
                    findings.append("[TRACK] No tracked changes found in document.")

    except zipfile.BadZipFile:
        findings.append("[TRACK] Could not read document — file is not a valid .docx.")
    except Exception as e:
        findings.append(f"[TRACK] Error checking track changes: {e}")

    return findings

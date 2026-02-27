
import zipfile
import xml.etree.ElementTree as ET
from collections import Counter

def scrape_rsids(file_path):
    """
    Analyzes the RSID tags within a .docx file. 
    
    Args:
        file_path (str): The path to the .docx file.

    Returns:
        list: A list of strings containing the RSID analysis findings.
    """
    findings = []
    try:
        with zipfile.ZipFile(file_path, 'r') as z:
            namelist = z.namelist()
            nsmap = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
            w = f"{{{nsmap['w']}}}"

            # --- Master RSID list from word/settings.xml ---
            findings.append("\n--- RSID (Revision Save ID) Analysis ---")
            if 'word/settings.xml' in namelist:
                with z.open('word/settings.xml') as settings_xml:
                    settings_root = ET.parse(settings_xml).getroot()
                    rsids_elem = settings_root.find(f"{w}rsids")
                    if rsids_elem is not None:
                        master_rsids = [
                            child.attrib.get(f"{w}val")
                            for child in rsids_elem
                            if child.attrib.get(f"{w}val")
                        ]
                        findings.append(f"[RSID] Unique revision sessions recorded in settings: {len(master_rsids)}")
                    else:
                        findings.append("[RSID] No revision session list found in word/settings.xml.")
                        findings.append("[RSID] Note: This is common for documents not authored in Microsoft Word (e.g. Google Docs exports).")
            else:
                findings.append("[RSID] word/settings.xml not found — revision session history unavailable.")

            # --- Per-element RSID breakdown from word/document.xml ---
            if 'word/document.xml' in namelist:
                with z.open('word/document.xml') as doc_xml:
                    root = ET.parse(doc_xml).getroot()
                    rsids = [
                        elem.attrib.get(f"{w}rsidR")
                        for elem in root.iter()
                        if elem.attrib.get(f"{w}rsidR")
                    ]

                    if rsids:
                        rsid_counts = Counter(rsids)
                        findings.append(f"[RSID] Unique RSIDs found in document body: {len(rsid_counts)}")
                        for rsid, count in rsid_counts.items():
                            findings.append(f"  Session '{rsid}': {count} item(s) created.")
                    else:
                        findings.append("[RSID] No rsidR attributes found in document body.")
            else:
                findings.append("[RSID] word/document.xml not found.")

    except zipfile.BadZipFile:
        findings.append("Error: The file is not a valid .docx file or it is corrupted. RSID scan failed.")
    except Exception as e:
        findings.append(f"An unexpected error occurred during RSID scan: {e}")
    
    return findings

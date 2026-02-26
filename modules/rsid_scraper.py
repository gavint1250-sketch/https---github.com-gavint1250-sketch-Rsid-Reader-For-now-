
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
            if 'word/document.xml' in z.namelist():
                with z.open('word/document.xml') as doc_xml:
                    tree = ET.parse(doc_xml)
                    root = tree.getroot()
                    # Namespace for Word documents
                    nsmap = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
                    rsids = [elem.attrib.get(f"{{{nsmap['w']}}}rsidR") for elem in root.iter() if elem.attrib.get(f"{{{nsmap['w']}}}rsidR")]
                    
                    if rsids:
                        findings.append("\n--- RSID (Revision Save ID) Analysis ---")
                        rsid_counts = Counter(rsids)
                        for rsid, count in rsid_counts.items():
                            findings.append(f"Session RSID '{rsid}': {count} item(s) created.")
                    else:
                        findings.append("No RSID tags found in document.xml.")
            else:
                findings.append("Could not find 'word/document.xml' in the .docx file.")
    except zipfile.BadZipFile:
        # This error is handled here so the metadata scan can still run if the zip is just corrupted.
        findings.append("Error: The file is not a valid .docx file or it is corrupted. RSID scan failed.")
    except Exception as e:
        findings.append(f"An unexpected error occurred during RSID scan: {e}")
    
    return findings


import os
import docx
import zipfile
import xml.etree.ElementTree as ET
from collections import Counter

def detect_ai_and_rsid(file_path):
    """
    Analyzes a .docx or .xml file for AI characteristics and RSID tags.
    
    Args:
        file_path (str): The path to the file to analyze.

    Returns:
        list: A list of strings containing the analysis findings.
    """
    if not os.path.exists(file_path):
        return ["Error: File not found. Please check the path."]

    findings = []

    if file_path.lower().endswith('.docx'):
        try:
            # --- Metadata Analysis ---
            document = docx.Document(file_path)
            core_properties = document.core_properties
            ai_keywords = ["ai", "artificial intelligence", "chatgpt", "gpt-3", "gpt-4", "dall-e", "midjourney", "stable diffusion", "copilot"]

            if core_properties.author and any(k in core_properties.author.lower() for k in ai_keywords):
                findings.append(f"Potential AI keyword found in author: {core_properties.author}")
            if core_properties.last_modified_by and any(k in core_properties.last_modified_by.lower() for k in ai_keywords):
                findings.append(f"Potential AI keyword found in last_modified_by: {core_properties.last_modified_by}")
            if core_properties.comments and any(k in core_properties.comments.lower() for k in ai_keywords):
                findings.append(f"Potential AI keyword found in comments: {core_properties.comments}")

            # --- RSID Analysis (from word/document.xml) ---
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

        except PermissionError:
            return ["Error: You do not have permission to access this file. Please check file permissions or close the file if it's open in another program."]
        except zipfile.BadZipFile:
            return ["Error: The file is not a valid .docx file or it is corrupted."]
        except Exception as e:
            return [f"An unexpected error occurred while processing the .docx file: {e}"]

    elif file_path.lower().endswith('.xml'):
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            findings.append("--- XML Analysis ---")
            findings.append("Successfully parsed XML file. (No specific AI/RSID analysis for generic XML)")
        except Exception as e:
            return [f"Error processing .xml file: {e}"]
    else:
        return ["Error: This tool accepts .docx and .xml files only."]

    return findings if findings else ["No obvious AI characteristics or RSID tags found."]

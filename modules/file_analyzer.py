
import os
from .metadata import scrape_metadata
from .rsid_scraper import scrape_rsids
from .content import analyze_content

def analyze_file(file_path):
    """
    Orchestrates the analysis of a file by calling different scrapers.
    """
    if not os.path.exists(file_path):
        return ["Error: File not found. Please check the path."]

    findings = []
    if file_path.lower().endswith('.docx'):
        findings.extend(scrape_metadata(file_path))
        findings.extend(scrape_rsids(file_path))
        findings.extend(analyze_content(file_path))
    elif file_path.lower().endswith('.pdf'):
        from .pdf import analyze_pdf
        findings.extend(analyze_pdf(file_path))
    elif file_path.lower().endswith('.xml'):
        # For now, we can just have a simple message for XMLs
        findings.append("--- XML Analysis ---")
        findings.append("Successfully parsed XML file. (No specific AI/RSID analysis for generic XML)")
    else:
        return ["Error: This tool accepts .docx, .pdf, and .xml files only."]

    # Check if any meaningful findings were made besides headers
    if not any(finding for finding in findings if "---" not in finding and "No " not in finding):
        return ["No specific AI characteristics or RSID sessions found."]
        
    return findings

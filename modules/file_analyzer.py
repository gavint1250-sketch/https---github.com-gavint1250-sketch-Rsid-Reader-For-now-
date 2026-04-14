import os
from .metadata import scrape_metadata
from .rsid_scraper import scrape_rsids
from .content import analyze_content


def analyze_file(file_path):
    """
    Orchestrates the analysis of a file by calling the appropriate scrapers.

    Args:
        file_path (str): Path to the file to analyze.

    Returns:
        tuple[list[str], list[dict]]:
          findings          — flat list of tagged finding strings for GUI display
          report_paragraphs — per-paragraph structured data for the HTML report
                              (empty list for PDF / XML files)
    """
    if not os.path.exists(file_path):
        return (["Error: File not found. Please check the path."], [])

    findings = []
    report_paragraphs = []

    if file_path.lower().endswith('.docx'):
        findings.extend(scrape_metadata(file_path))
        findings.extend(scrape_rsids(file_path))
        content_findings, report_paragraphs = analyze_content(file_path)
        findings.extend(content_findings)

    elif file_path.lower().endswith('.pdf'):
        from .pdf import analyze_pdf
        pdf_findings, report_paragraphs = analyze_pdf(file_path)
        findings.extend(pdf_findings)

    elif file_path.lower().endswith('.xml'):
        findings.append("--- XML Analysis ---")
        findings.append(
            "Successfully parsed XML file. "
            "(No specific AI/RSID analysis for generic XML)"
        )

    else:
        return (["Error: This tool accepts .docx, .pdf, and .xml files only."], [])

    if not any(f for f in findings if "---" not in f and "No " not in f):
        return (["No specific AI characteristics or RSID sessions found."], report_paragraphs)

    return (findings, report_paragraphs)

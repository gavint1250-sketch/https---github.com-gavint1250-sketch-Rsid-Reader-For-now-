from .metadata_checker import check_pdf_metadata
from .content_checker import check_pdf_content


def analyze_pdf(file_path):
    """
    Orchestrates the analysis of a PDF file.

    Checks performed:
      - PDF metadata (creator app, producer, author, timestamps, AI keywords)
      - Full content analysis (readability, perplexity, AI vocab, stats, burstiness)

    Args:
        file_path (str): Path to the PDF file.

    Returns:
        tuple[list[str], list[dict]]:
          findings          — flat finding strings for GUI display
          report_paragraphs — per-paragraph structured data for the HTML report
    """
    findings = ["--- PDF Metadata Analysis ---"]
    try:
        findings += check_pdf_metadata(file_path)
    except Exception as e:
        findings.append(f"An unexpected error occurred during PDF metadata scan: {e}")

    findings.append("--- PDF Content Analysis ---")
    report_paragraphs = []
    try:
        content_findings, report_paragraphs = check_pdf_content(file_path)
        findings += content_findings
    except Exception as e:
        findings.append(f"An unexpected error occurred during PDF content analysis: {e}")

    return findings, report_paragraphs

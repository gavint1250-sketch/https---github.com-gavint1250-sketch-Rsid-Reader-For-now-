
from .metadata_checker import check_pdf_metadata
from .content_checker import check_pdf_content


def analyze_pdf(file_path):
    """
    Orchestrates the analysis of a PDF file.

    Checks performed:
      - PDF metadata (creator app, producer, author, timestamps, AI keywords)
      - Content statistics (page count, word count, paragraph estimate)

    Args:
        file_path (str): Path to the PDF file.

    Returns:
        list: Finding strings.
    """
    findings = ["--- PDF Metadata Analysis ---"]
    try:
        findings += check_pdf_metadata(file_path)
    except Exception as e:
        findings.append(f"An unexpected error occurred during PDF metadata scan: {e}")

    findings.append("--- PDF Content Analysis ---")
    try:
        findings += check_pdf_content(file_path)
    except Exception as e:
        findings.append(f"An unexpected error occurred during PDF content analysis: {e}")

    return findings

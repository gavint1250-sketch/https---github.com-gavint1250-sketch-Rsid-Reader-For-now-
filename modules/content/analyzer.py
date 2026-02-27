
import docx
from .stats_checker import check_stats
from .track_changes_checker import check_track_changes
from .comment_extractor import extract_comments
from .formatting_checker import check_formatting


def analyze_content(file_path):
    """
    Analyzes the body content of a .docx file and reports raw findings.

    Checks performed:
      - Word and paragraph statistics
      - Tracked insertions and deletions
      - Inline comment extraction
      - Paragraph style distribution

    Args:
        file_path (str): The path to the .docx file.

    Returns:
        list: A list of strings containing the content analysis findings.
    """
    findings = ["--- Content Analysis ---"]
    try:
        document = docx.Document(file_path)

        findings += check_stats(document)
        findings += check_track_changes(file_path)
        findings += extract_comments(file_path)
        findings += check_formatting(document)

        if len(findings) == 1:
            findings.append("No content characteristics found.")

    except Exception as e:
        findings.append(f"An unexpected error occurred during content analysis: {e}")

    return findings

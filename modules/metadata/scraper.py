
import docx
from .keyword_checker import check_keywords
from .revision_checker import check_revision
from .timestamp_checker import check_timestamps
from .author_checker import check_author
from .app_checker import check_app_properties
from .scrape_detector import check_scrape_indicators
from .gdocs_checker import check_gdocs


def scrape_metadata(file_path):
    """
    Analyzes the core metadata of a .docx file and reports raw findings.

    Checks performed:
      - Creating application (from docProps/app.xml)
      - Metadata scrape/removal indicators
      - AI keyword scan across 7 text fields
      - Revision count
      - Creation and last-modification timestamps with elapsed time
      - Author field completeness

    Args:
        file_path (str): The path to the .docx file.

    Returns:
        list: A list of strings containing the metadata analysis findings.
    """
    findings = ["--- Metadata Analysis ---"]
    try:
        props = docx.Document(file_path).core_properties

        findings += check_app_properties(file_path)
        findings += check_gdocs(file_path)
        findings += check_scrape_indicators(file_path, props)
        findings += check_keywords(props)
        findings += check_revision(props)
        findings += check_timestamps(props)
        findings += check_author(props)

        if len(findings) == 1:
            findings.append("No additional metadata characteristics found.")

    except Exception as e:
        findings.append(f"An unexpected error occurred during metadata scan: {e}")

    return findings


import pypdf


def check_pdf_content(file_path):
    """
    Extracts text from a PDF and reports basic content statistics.

    Reports:
      - Page count
      - Total word count
      - Estimated paragraph count (blank-line-separated blocks)
      - Average words per page

    Args:
        file_path (str): Path to the PDF file.

    Returns:
        list: Finding strings.
    """
    findings = []
    try:
        reader = pypdf.PdfReader(file_path)
        page_count = len(reader.pages)
        findings.append(f"[CONTENT] Page count: {page_count}")

        full_text = ""
        for page in reader.pages:
            page_text = page.extract_text() or ""
            full_text += page_text + "\n"

        if not full_text.strip():
            findings.append("[CONTENT] No extractable text found (PDF may be image-based or encrypted).")
            return findings

        words = full_text.split()
        word_count = len(words)
        findings.append(f"[CONTENT] Total word count: {word_count}")

        # Estimate paragraph count by counting non-empty blocks separated by blank lines
        paragraphs = [b.strip() for b in full_text.split("\n\n") if b.strip()]
        para_count = len(paragraphs)
        findings.append(f"[CONTENT] Estimated paragraph blocks: {para_count}")

        if page_count > 0:
            avg_words = round(word_count / page_count)
            findings.append(f"[CONTENT] Average words per page: {avg_words}")

    except pypdf.errors.PdfReadError as e:
        findings.append(f"[CONTENT] Could not extract text — file may be corrupt or encrypted: {e}")
    except Exception as e:
        findings.append(f"[CONTENT] Error during PDF content analysis: {e}")

    return findings

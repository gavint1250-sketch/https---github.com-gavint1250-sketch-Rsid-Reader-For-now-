
import pypdf

# AI-related keywords to scan for in PDF metadata fields
_AI_KEYWORDS = [
    "chatgpt", "gpt-4", "gpt-3", "openai", "dall-e", "midjourney",
    "stable diffusion", "copilot", "claude", "gemini", "bard", "llm",
    "artificial intelligence", "ai-generated",
]


def _scan_for_ai_keywords(fields):
    """Scan a dict of {field_name: value} for AI-related keywords."""
    findings = []
    for field, value in fields.items():
        if not value:
            continue
        lower = value.lower()
        for kw in _AI_KEYWORDS:
            if kw in lower:
                findings.append(f"[KEYWORD] AI keyword '{kw}' found in PDF {field}: {value}")
    return findings


def check_pdf_metadata(file_path):
    """
    Extracts and reports metadata from a PDF file.

    Reports:
      - Creator application (/Creator field)
      - Producer (PDF engine/library)
      - Author
      - Title, Subject, Keywords
      - Creation and modification timestamps
      - AI keyword scan across all metadata text fields

    Args:
        file_path (str): Path to the PDF file.

    Returns:
        list: Finding strings.
    """
    findings = []
    try:
        reader = pypdf.PdfReader(file_path)
        meta = reader.metadata

        if meta is None:
            findings.append("[APP] No metadata found in PDF.")
            return findings

        # Creator (originating application, e.g. "Google Docs", "Microsoft Word")
        creator = meta.creator or ""
        if creator:
            findings.append(f"[APP] Created with: {creator}")
        else:
            findings.append("[APP] Creator application field is blank.")

        # Producer (PDF engine, e.g. "Adobe PDF Library", "Skia/PDF", "pdfTeX")
        producer = meta.producer or ""
        if producer:
            findings.append(f"[APP] PDF producer: {producer}")

        # Author
        author = meta.author or ""
        if author:
            findings.append(f"[AUTHOR] Author: {author}")
        else:
            findings.append("[AUTHOR] Author field is blank.")

        # Title / Subject / Keywords (informational)
        title = meta.title or ""
        subject = meta.subject or ""
        keywords = meta.get("/Keywords", "") or ""
        if title:
            findings.append(f"[CONTENT] PDF title: {title}")
        if subject:
            findings.append(f"[CONTENT] PDF subject: {subject}")
        if keywords:
            findings.append(f"[CONTENT] PDF keywords: {keywords}")

        # Timestamps
        creation = meta.creation_date
        modification = meta.modification_date
        if creation:
            findings.append(f"[TIMESTAMP] PDF created: {creation}")
        if modification:
            findings.append(f"[TIMESTAMP] PDF modified: {modification}")

        # AI keyword scan
        scan_fields = {
            "Creator": creator,
            "Producer": producer,
            "Author": author,
            "Title": title,
            "Subject": subject,
            "Keywords": keywords,
        }
        findings += _scan_for_ai_keywords(scan_fields)

    except pypdf.errors.PdfReadError as e:
        findings.append(f"[APP] Could not read PDF — file may be corrupt or encrypted: {e}")
    except Exception as e:
        findings.append(f"[APP] Error reading PDF metadata: {e}")

    return findings

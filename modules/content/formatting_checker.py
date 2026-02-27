
from collections import Counter


# Styles that are considered "body" content (not structural headings/lists)
_HEADING_PREFIXES = ("heading", "title", "subtitle", "toc")


def check_formatting(document):
    """
    Reports the distribution of paragraph styles used in the document.
    Flags if all body paragraphs share a single style.

    Args:
        document: A python-docx Document object.

    Returns:
        list: Finding strings describing style usage.
    """
    findings = []

    style_counts = Counter()
    for para in document.paragraphs:
        if para.text.strip():
            style_counts[para.style.name] += 1

    if not style_counts:
        findings.append("[FORMAT] No non-empty paragraphs found for style analysis.")
        return findings

    findings.append("[FORMAT] Paragraph style distribution:")
    for style, count in style_counts.most_common():
        findings.append(f"[FORMAT]   {style}: {count} paragraph(s)")

    body_styles = {
        s for s in style_counts
        if not any(s.lower().startswith(p) for p in _HEADING_PREFIXES)
    }
    if len(body_styles) == 1:
        only_style = next(iter(body_styles))
        findings.append(
            f"[FORMAT] All body paragraphs use a single style: '{only_style}'"
        )

    return findings

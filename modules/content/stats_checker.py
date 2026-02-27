
def check_stats(document):
    """
    Reports basic word and paragraph statistics for the document body.

    Args:
        document: A python-docx Document object.

    Returns:
        list: Finding strings with counts and length metrics.
    """
    findings = []

    word_counts = []
    for para in document.paragraphs:
        text = para.text.strip()
        if text:
            word_counts.append(len(text.split()))

    total_paragraphs = len(word_counts)
    total_words = sum(word_counts)

    findings.append(f"[CONTENT] Non-empty paragraphs: {total_paragraphs}")
    findings.append(f"[CONTENT] Total words: {total_words}")

    if total_paragraphs > 0:
        avg = total_words / total_paragraphs
        findings.append(f"[CONTENT] Average words per paragraph: {avg:.1f}")
        findings.append(f"[CONTENT] Shortest paragraph: {min(word_counts)} word(s)")
        findings.append(f"[CONTENT] Longest paragraph: {max(word_counts)} word(s)")

    return findings

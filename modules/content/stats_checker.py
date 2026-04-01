import re as _re


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


def check_vocabulary_diversity(document):
    """
    Compute Type-Token Ratio (TTR) and, for documents over 500 words,
    Moving Average TTR (MATTR, window=100) to measure vocabulary richness.

    Low TTR / MATTR values suggest repetitive, AI-like vocabulary use.
    Human writing typically exhibits MATTR > 0.72; AI text tends to cluster
    in the 0.45–0.62 range.

    Args:
        document: A python-docx Document object.

    Returns:
        A 2-tuple:
          findings : list[str]  — [CONTENT]-tagged finding strings for GUI display
          summary  : dict with keys 'ttr', 'mattr', 'total_words', 'unique_words'
    """
    all_words = []
    for para in document.paragraphs:
        text = para.text.strip()
        if text:
            all_words.extend(_re.findall(r"[a-z]+", text.lower()))

    total_words = len(all_words)
    unique_words = len(set(all_words))

    if total_words == 0:
        return [], {"ttr": None, "mattr": None, "total_words": 0, "unique_words": 0}

    ttr = unique_words / total_words
    findings = [
        f"[CONTENT] Vocabulary diversity (TTR): {ttr:.4f} "
        f"({unique_words} unique / {total_words} total words)"
    ]

    mattr = None
    if total_words > 500:
        window = 100
        window_ttrs = [
            len(set(all_words[i : i + window])) / window
            for i in range(total_words - window + 1)
        ]
        mattr = sum(window_ttrs) / len(window_ttrs)
        flag = "low — AI-like" if mattr < 0.72 else "normal range"
        findings.append(
            f"[CONTENT] MATTR (window=100): {mattr:.4f} — {flag}"
        )

    summary = {
        "ttr": ttr,
        "mattr": mattr,
        "total_words": total_words,
        "unique_words": unique_words,
    }
    return findings, summary


"""
AI Vocabulary Fingerprint Checker

Scans document text for words and phrases statistically associated with
AI-generated text, based on empirical analysis of LLM output corpora.
Returns per-paragraph hit lists (index-aligned with document.paragraphs)
for integration with the HTML report.
"""

import re
from collections import Counter
from .citation_utils import is_citation_paragraph


# ---------------------------------------------------------------------------
# Curated AI vocabulary fingerprint list
# Words and phrases disproportionately common in GPT-family model output.
# ---------------------------------------------------------------------------
AI_VOCAB_TERMS = [
    # High-signal single words
    "delve", "delves", "delving",
    "comprehensive", "crucial",
    "leverage", "leveraging",
    "nuanced", "multifaceted",
    "furthermore", "moreover",
    "paramount", "pivotal",
    "robust",
    "streamline", "streamlining",
    "utilize", "utilizes", "utilizing",
    "underscore", "underscores",
    "foster", "fosters",
    "facilitate", "facilitates",
    "transformative", "holistic",
    "synergy", "synergies",
    "actionable", "scalable",
    "seamlessly", "proactively",
    "empower", "empowers",
    "groundbreaking", "reimagine",
    "paradigm", "ecosystem",
    # Multi-word phrases (checked as case-insensitive substrings)
    "cutting-edge",
    "it is worth noting",
    "it is important to note",
    "it is essential to",
    "plays a crucial role",
    "plays an important role",
    "in the realm of",
    "it should be noted",
    "a wide range of",
    "a myriad of",
    "in conclusion",
    "in summary",
    "to summarize",
]

# Partition into single-word and phrase sets for efficient matching
_SINGLE_TERMS = frozenset(t for t in AI_VOCAB_TERMS if " " not in t and "-" not in t)
_PHRASE_TERMS = [t for t in AI_VOCAB_TERMS if " " in t or "-" in t]


def _tokenize(text):
    """Lower-case alpha tokenizer (strips punctuation, returns list of words)."""
    return re.findall(r"[a-z]+(?:[-'][a-z]+)*", text.lower())


def _find_hits(text):
    """
    Return a flat list of all AI vocabulary matches found in *text*.
    Single words are matched at token boundaries; phrases as substrings.
    Duplicate occurrences are each included as a separate list entry.
    """
    hits = []
    lower = text.lower()

    for word in _tokenize(text):
        if word in _SINGLE_TERMS:
            hits.append(word)

    for phrase in _PHRASE_TERMS:
        start = 0
        while True:
            idx = lower.find(phrase, start)
            if idx == -1:
                break
            hits.append(phrase)
            start = idx + len(phrase)

    return hits


def check_ai_vocabulary(document):
    """
    Scan every paragraph for AI vocabulary fingerprint terms.

    Args:
        document: A python-docx Document object.

    Returns:
        A 3-tuple:
          findings       : list[str]       — [VOCAB]-tagged finding strings for GUI display
          per_para_hits  : list[list[str]] — one list per paragraph in document.paragraphs,
                           containing matched terms (empty list for paragraphs with no hits
                           or no text). Index-aligned with document.paragraphs.
          summary        : dict with keys:
                             'vocab_found_terms'  → dict {term: count}
                             'vocab_density'      → float (flagged tokens / total alpha tokens)
                             'total_words'        → int
    """
    per_para_hits = []
    all_hits = []
    total_words = 0

    for para in document.paragraphs:
        text = para.text.strip()
        if not text or is_citation_paragraph(para):
            per_para_hits.append([])
            continue
        words = _tokenize(text)
        total_words += len(words)
        hits = _find_hits(text)
        per_para_hits.append(hits)
        all_hits.extend(hits)

    term_counts = Counter(all_hits)
    density = len(all_hits) / total_words if total_words else 0.0

    findings = []
    if term_counts:
        findings.append(
            f"[VOCAB] AI vocabulary fingerprint: {len(all_hits)} flagged token(s) "
            f"across {len(term_counts)} distinct term(s) "
            f"(density: {density * 100:.2f}%)"
        )
        for term, count in term_counts.most_common(10):
            findings.append(f"[VOCAB]   '{term}': {count} occurrence(s)")
    else:
        findings.append("[VOCAB] No AI vocabulary fingerprint terms detected.")

    summary = {
        "vocab_found_terms": dict(term_counts),
        "vocab_density": density,
        "total_words": total_words,
    }

    return findings, per_para_hits, summary

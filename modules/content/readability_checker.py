
"""
Readability Score Checker

Computes Flesch Reading Ease and Flesch-Kincaid Grade Level using a
heuristic syllable counter. No external dependencies required.

AI-generated text typically clusters in:
  Flesch Reading Ease : 40 – 65
  FK Grade Level      : 8  – 12

Human writing shows considerably wider variation in both metrics.
"""

import re

# Known English diphthongs/digraphs that form a single syllable.
# Vowel pairs NOT in this set are treated as hiatus (two separate syllables).
_DIPHTHONGS = frozenset([
    'ai', 'au', 'ay', 'ea', 'ee', 'ei', 'eu', 'ew', 'ey',
    'ie', 'oa', 'oe', 'oi', 'oo', 'ou', 'ow', 'oy', 'ue', 'ui', 'uy'
])
_SILENT_E_RE = re.compile(r'[^aeiouy]e$', re.IGNORECASE)
_CONS_LE_RE  = re.compile(r'[^aeiouy]le$', re.IGNORECASE)

# Patterns to strip before readability scoring
_URL_RE     = re.compile(r'https?://\S+|www\.\S+', re.IGNORECASE)
_XML_TAG_RE = re.compile(r'<[^>]+>')
_CURLY_RE   = re.compile(r'\{[^}]*\}')
_DASHES_RE  = re.compile(r'-{2,}[^-]*-{2,}')  # --- PAGE 1 --- style markers

from .citation_utils import is_citation_paragraph as _is_citation_paragraph


def _clean_text_for_readability(text):
    """Strip metadata, tags, URLs, and structural markers before scoring."""
    text = _URL_RE.sub(' ', text)
    text = _XML_TAG_RE.sub(' ', text)
    text = _CURLY_RE.sub(' ', text)
    text = _DASHES_RE.sub(' ', text)
    return text


def _count_syllables(word):
    """
    Heuristic syllable counter with diphthong/hiatus awareness.
      1. Walk character by character; each vowel starts a new syllable.
      2. Two-vowel pairs in _DIPHTHONGS count as ONE syllable (advance by 2).
      3. Other adjacent vowel pairs (hiatus: ia, io, eo, ua…) count as TWO.
      4. Subtract 1 for a silent trailing 'e' (if not the only syllable).
      5. Add 1 for a consonant+'le' ending (e.g. "ta-ble", "lit-tle").
      6. Return at least 1.
    """
    word = word.lower().strip(".,;:!?\"'()-")
    if not word:
        return 0

    count = 0
    i = 0
    while i < len(word):
        if word[i] in 'aeiouy':
            if i + 1 < len(word) and word[i + 1] in 'aeiouy':
                pair = word[i:i + 2]
                if pair in _DIPHTHONGS:
                    count += 1   # known diphthong → one syllable
                    i += 2
                else:
                    count += 1   # hiatus first vowel; second handled next loop
                    i += 1
            else:
                count += 1
                i += 1
        else:
            i += 1

    # Silent trailing e (e.g. "make", "hope")
    if count > 1 and _SILENT_E_RE.search(word):
        count -= 1

    # Consonant + le ending is its own syllable (e.g. "ta-ble", "sim-ple")
    if _CONS_LE_RE.search(word):
        count += 1

    return max(1, count)


def _split_sentences(text):
    """Split text on sentence-ending punctuation; return non-empty strips."""
    return [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]


def _score_text(text):
    """
    Compute Flesch ease and FK grade for a text block.

    Returns (ease, grade, word_count, sentence_count, syllable_count).
    Returns all-zeros tuple when there is insufficient text.
    """
    text = _clean_text_for_readability(text)
    words = re.findall(r"[a-zA-Z'-]+", text)
    sentences = _split_sentences(text)
    wc = len(words)
    sc = len(sentences)
    syls = sum(_count_syllables(w) for w in words)

    if wc < 3 or sc == 0:
        return 0.0, 0.0, wc, sc, syls

    avg_wps = wc / sc
    avg_spw = syls / wc
    ease = 206.835 - 1.015 * avg_wps - 84.6 * avg_spw
    grade = 0.39 * avg_wps + 11.8 * avg_spw - 15.59
    return ease, grade, wc, sc, syls


def check_readability(document):
    """
    Compute Flesch Reading Ease and Flesch-Kincaid Grade Level for the
    whole document and for each individual paragraph.

    Args:
        document: A python-docx Document object.

    Returns:
        A 3-tuple:
          findings        : list[str]                  — [READABILITY]-tagged GUI strings
          per_para_scores : list[tuple[float, float]]  — (ease, grade) per paragraph,
                            index-aligned with document.paragraphs.
                            (0.0, 0.0) for paragraphs too short to score.
          summary         : dict with keys:
                              'doc_readability_ease'  → float
                              'doc_fk_grade'          → float
                              'total_sentences'       → int
                              'total_syllables'       → int
    """
    per_para_scores = []
    doc_words = doc_sents = doc_syls = 0

    for para in document.paragraphs:
        text = para.text.strip()
        if not text or _is_citation_paragraph(para):
            per_para_scores.append((0.0, 0.0))
            continue
        ease, grade, wc, sc, syls = _score_text(text)
        per_para_scores.append((ease, grade))
        doc_words += wc
        doc_sents += sc
        doc_syls += syls

    # Document-level scores re-computed from aggregated raw counts
    if doc_words >= 3 and doc_sents > 0:
        avg_wps = doc_words / doc_sents
        avg_spw = doc_syls / doc_words
        doc_ease = 206.835 - 1.015 * avg_wps - 84.6 * avg_spw
        doc_grade = 0.39 * avg_wps + 11.8 * avg_spw - 15.59
    else:
        doc_ease = doc_grade = 0.0

    ease_flag = "AI-range (40–65)" if 40 <= doc_ease <= 65 else "outside typical AI range"
    grade_flag = "AI-range (8–12)" if 8 <= doc_grade <= 12 else "outside typical AI range"

    findings = [
        f"[READABILITY] Flesch Reading Ease: {doc_ease:.1f} — {ease_flag}",
        f"[READABILITY] Flesch-Kincaid Grade Level: {doc_grade:.1f} — {grade_flag}",
        f"[READABILITY] {doc_words} words · {doc_sents} sentences · {doc_syls} syllables",
    ]

    summary = {
        "doc_readability_ease": doc_ease,
        "doc_fk_grade": doc_grade,
        "total_sentences": doc_sents,
        "total_syllables": doc_syls,
    }

    return findings, per_para_scores, summary

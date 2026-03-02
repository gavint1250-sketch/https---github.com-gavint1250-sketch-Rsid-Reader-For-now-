
import docx
from .stats_checker import check_stats, check_vocabulary_diversity
from .track_changes_checker import check_track_changes
from .comment_extractor import extract_comments
from .formatting_checker import check_formatting
from .ai_vocabulary_checker import check_ai_vocabulary
from .readability_checker import check_readability
from .perplexity_checker import check_perplexity_and_burstiness, get_cached_paragraph_scores


def analyze_content(file_path):
    """
    Analyzes the body content of a .docx file.

    Checks performed:
      - Word / paragraph statistics
      - Vocabulary diversity (TTR / MATTR)
      - AI vocabulary fingerprint
      - Readability scores (Flesch / FK)
      - GPT-2 perplexity and burstiness (per paragraph)
      - Tracked insertions / deletions
      - Inline comment extraction
      - Paragraph style distribution

    Args:
        file_path (str): Path to the .docx file.

    Returns:
        tuple[list[str], list[dict]]:
          findings          — tagged finding strings for GUI display
          report_paragraphs — per-paragraph structured data for the HTML report,
                              with a summary dict as the final element
    """
    findings = ["--- Content Analysis ---"]
    report_paragraphs = []

    try:
        document = docx.Document(file_path)
        paragraphs = document.paragraphs

        # --- Existing checkers ---
        findings += check_stats(document)
        findings += check_track_changes(file_path)
        findings += extract_comments(file_path)
        findings += check_formatting(document)

        # --- Vocabulary diversity ---
        vd_findings, vd_summary = check_vocabulary_diversity(document)
        findings += vd_findings

        # --- AI vocabulary fingerprint ---
        vocab_findings, per_para_vocab, vocab_summary = check_ai_vocabulary(document)
        findings += vocab_findings

        # --- Readability ---
        read_findings, per_para_read, read_summary = check_readability(document)
        findings += read_findings

        # --- GPT-2 perplexity + burstiness ---
        # check_perplexity_and_burstiness caches per-paragraph scores internally.
        perp_burst_findings = check_perplexity_and_burstiness(document)
        findings += perp_burst_findings
        perp_cache = get_cached_paragraph_scores()  # list[dict], indexed by para position

        # Build a lookup from paragraph index → cached perplexity entry.
        # perp_cache only contains non-empty paragraphs, so we match by tracking
        # a separate counter for non-empty paragraphs.
        perp_by_para_idx = {}
        non_empty_count = 0
        for i, para in enumerate(paragraphs):
            if para.text.strip():
                if non_empty_count < len(perp_cache):
                    perp_by_para_idx[i] = perp_cache[non_empty_count]
                non_empty_count += 1

        # --- Assemble per-paragraph report data ---
        for i, para in enumerate(paragraphs):
            text = para.text.strip()
            perp_entry = perp_by_para_idx.get(i, {})
            ease, grade = per_para_read[i] if i < len(per_para_read) else (0.0, 0.0)

            report_paragraphs.append({
                "index": i,
                "text": text,
                "word_count": len(text.split()) if text else 0,
                "perplexity": perp_entry.get("perplexity"),
                "label": perp_entry.get("label"),
                "vocab_hits": per_para_vocab[i] if i < len(per_para_vocab) else [],
                "readability_ease": ease if text else None,
                "fk_grade": grade if text else None,
            })

        # --- Summary entry (last item, identified by '_summary': True) ---
        # Burstiness is document-level; extract from the findings string if possible.
        burst_score = None
        burst_interp = ""
        for line in findings:
            if line.startswith("[BURST] Score:"):
                # e.g. "[BURST] Score: 0.123 — High burstiness..."
                try:
                    parts = line.split("—", 1)
                    burst_score = float(parts[0].split("Score:")[1].strip())
                    burst_interp = parts[1].strip() if len(parts) > 1 else ""
                except (IndexError, ValueError):
                    pass
                break

        report_paragraphs.append({
            "_summary": True,
            "filename": file_path,
            "total_words": vd_summary.get("total_words", 0),
            "ttr": vd_summary.get("ttr"),
            "mattr": vd_summary.get("mattr"),
            "vocab_density": vocab_summary.get("vocab_density", 0.0),
            "vocab_found_terms": vocab_summary.get("vocab_found_terms", {}),
            "doc_readability_ease": read_summary.get("doc_readability_ease", 0.0),
            "doc_fk_grade": read_summary.get("doc_fk_grade", 0.0),
            "total_sentences": read_summary.get("total_sentences", 0),
            "burstiness_score": burst_score,
            "burstiness_interp": burst_interp,
        })

        if len(findings) == 1:
            findings.append("No content characteristics found.")

    except Exception as e:
        findings.append(f"An unexpected error occurred during content analysis: {e}")

    return findings, report_paragraphs

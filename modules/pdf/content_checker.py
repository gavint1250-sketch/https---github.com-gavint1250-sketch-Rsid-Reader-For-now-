import pypdf

from .paragraph_adapter import build_pdf_document
from ..content.stats_checker import check_stats, check_vocabulary_diversity
from ..content.ai_vocabulary_checker import check_ai_vocabulary
from ..content.readability_checker import check_readability
from ..content.perplexity_checker import check_perplexity_and_burstiness, get_cached_paragraph_scores
from ..content.citation_utils import is_citation_paragraph


def check_pdf_content(file_path):
    """
    Extracts text from a PDF, runs all content-analysis checkers, and returns
    per-paragraph report data alongside flat finding strings.

    Returns:
        tuple[list[str], list[dict]]:
          findings          — [CONTENT]-tagged finding strings for GUI display
          report_paragraphs — per-paragraph structured data (same schema as
                              the DOCX pipeline), with a summary dict as the
                              final element.  Empty list on extraction failure.
    """
    findings = []
    report_paragraphs = []

    try:
        reader = pypdf.PdfReader(file_path)
        page_count = len(reader.pages)
        findings.append(f"[CONTENT] Page count: {page_count}")

        full_text = ""
        for page in reader.pages:
            full_text += (page.extract_text() or "") + "\n"

        if not full_text.strip():
            findings.append(
                "[CONTENT] No extractable text found "
                "(PDF may be image-based or encrypted)."
            )
            return findings, report_paragraphs

        # Basic word / page stats (before running the full checkers so that
        # the raw counts appear at the top of the findings list).
        words = full_text.split()
        word_count = len(words)
        findings.append(f"[CONTENT] Total word count: {word_count}")
        if page_count > 0:
            findings.append(
                f"[CONTENT] Average words per page: {round(word_count / page_count)}"
            )

        # Build a paragraph-object model from the plain text so all existing
        # checkers can be reused without modification.
        document = build_pdf_document(full_text)
        paragraphs = document.paragraphs
        findings.append(
            f"[CONTENT] Estimated paragraph blocks: {len(paragraphs)}"
        )

        # --- Stats / vocab diversity ---
        findings += check_stats(document)
        vd_findings, vd_summary = check_vocabulary_diversity(document)
        findings += vd_findings

        # --- AI vocabulary fingerprint ---
        vocab_findings, per_para_vocab, vocab_summary = check_ai_vocabulary(document)
        findings += vocab_findings

        # --- Readability ---
        read_findings, per_para_read, read_summary = check_readability(document)
        findings += read_findings

        # --- GPT-2 perplexity + burstiness ---
        perp_burst_findings = check_perplexity_and_burstiness(document)
        findings += perp_burst_findings
        perp_cache = get_cached_paragraph_scores()

        # Build paragraph-index → perplexity cache mapping.
        # The cache only contains non-empty, non-citation paragraphs, so we
        # advance the cache pointer only for those paragraphs.
        perp_by_para_idx = {}
        cache_idx = 0
        for i, para in enumerate(paragraphs):
            if para.text.strip() and not is_citation_paragraph(para):
                if cache_idx < len(perp_cache):
                    perp_by_para_idx[i] = perp_cache[cache_idx]
                    cache_idx += 1

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

        # --- Summary entry ---
        burst_score = None
        burst_interp = ""
        for line in findings:
            if line.startswith("[BURST] Score:"):
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

    except pypdf.errors.PdfReadError as e:
        findings.append(
            f"[CONTENT] Could not extract text — file may be corrupt or encrypted: {e}"
        )
    except Exception as e:
        findings.append(f"[CONTENT] Error during PDF content analysis: {e}")

    return findings, report_paragraphs

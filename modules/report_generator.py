
"""
HTML Report Generator

Produces a self-contained HTML file from the structured per-paragraph analysis
data returned by analyze_content().  Uses only Python stdlib — no extra deps.
The resulting file opens correctly in every major browser on Windows, macOS,
and Linux via Python's webbrowser module.
"""

import html as _html
import os
from datetime import datetime

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_VOCAB_BG = "#FFE4B5"     # moccasin  — inline highlight for AI vocab words
_VOCAB_FG = "#8B0000"     # dark red
_AI_ROW_BG = "#FFF0F0"    # misty rose — row background for low-perplexity paras
_NORMAL_ROW_BG = "#FFFFFF"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _esc(text):
    """HTML-escape a string."""
    return _html.escape(str(text))


def _highlight_vocab(text, vocab_hits):
    """
    Return HTML with AI vocabulary terms wrapped in coloured <span> tags.
    Processes longest phrases first to avoid partial-match collisions.
    """
    if not vocab_hits:
        return _esc(text)

    # Sort descending by length so longer phrases are matched before substrings
    terms = sorted(set(vocab_hits), key=len, reverse=True)

    # Represent the text as a list of (already_html: bool, fragment: str) pairs
    segments = [(False, text)]

    for term in terms:
        new_segments = []
        for is_html, frag in segments:
            if is_html:
                new_segments.append((True, frag))
                continue
            lower_frag = frag.lower()
            lower_term = term.lower()
            start = 0
            while True:
                idx = lower_frag.find(lower_term, start)
                if idx == -1:
                    new_segments.append((False, frag[start:]))
                    break
                if idx > start:
                    new_segments.append((False, frag[start:idx]))
                matched = frag[idx: idx + len(term)]
                new_segments.append((True,
                    f'<span style="background:{_VOCAB_BG};color:{_VOCAB_FG};'
                    f'font-weight:bold" title="AI vocabulary term">'
                    f'{_esc(matched)}</span>'
                ))
                start = idx + len(term)
        segments = new_segments

    return "".join(frag if is_html else _esc(frag) for is_html, frag in segments)


def _fmt(value, decimals=2, suffix="", fallback="—"):
    """Format a numeric value or return a dash for None / zero."""
    if value is None:
        return fallback
    try:
        return f"{value:.{decimals}f}{suffix}"
    except (TypeError, ValueError):
        return fallback


def _card(title, *rows):
    """Build a summary metric card from (label, value) row tuples."""
    inner = "".join(
        f'<div style="display:flex;justify-content:space-between;'
        f'padding:4px 0;border-bottom:1px solid #eee">'
        f'<span style="color:#555;font-size:0.9em">{_esc(label)}</span>'
        f'<span style="font-weight:600;color:#2c3e50">{_esc(str(value))}</span>'
        f'</div>'
        for label, value in rows
    )
    return (
        f'<div style="background:#fff;border-radius:8px;padding:16px;'
        f'box-shadow:0 2px 6px rgba(0,0,0,.1)">'
        f'<h3 style="margin:0 0 10px;font-size:.85em;text-transform:uppercase;'
        f'letter-spacing:.5px;color:#2980b9">{_esc(title)}</h3>'
        f'{inner}</div>'
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_html_report(report_data, findings):
    """
    Generate a self-contained HTML AI analysis report.

    Args:
        report_data : list[dict]
            Per-paragraph dicts from analyze_content(), with the summary dict
            (identified by '_summary': True) as the final element.
            Multiple files can be included; each file's summary marks the boundary.
        findings    : list[str]
            The flat findings list from analyze_file(), shown verbatim in a
            'Raw Findings' section at the bottom of the report.

    Returns:
        str — Complete HTML document ready to write to a .html file.
    """
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # --- Split report_data into per-file groups --------------------------------
    # Each group ends with its summary dict.
    file_groups = []
    current_paras = []
    for item in report_data:
        if item.get("_summary"):
            file_groups.append({"summary": item, "paragraphs": current_paras})
            current_paras = []
        else:
            current_paras.append(item)

    # --- Build HTML for each file group ---------------------------------------
    file_sections_html = ""
    for group in file_groups:
        summary = group["summary"]
        paragraphs = group["paragraphs"]

        filename = _esc(os.path.basename(summary.get("filename", "Unknown file")))
        total_words = summary.get("total_words", 0)
        total_sents = summary.get("total_sentences", 0)
        ttr = summary.get("ttr")
        mattr = summary.get("mattr")
        ease = summary.get("doc_readability_ease", 0.0)
        grade = summary.get("doc_fk_grade", 0.0)
        vocab_density = summary.get("vocab_density", 0.0)
        vocab_terms = summary.get("vocab_found_terms", {})
        burst_score = summary.get("burstiness_score")
        burst_interp = summary.get("burstiness_interp", "")

        # Summary cards
        cards_html = (
            '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));'
            'gap:16px;margin-bottom:24px">'
            + _card("Document Stats",
                    ("Total words", total_words),
                    ("Total sentences", total_sents))
            + _card("Vocabulary Diversity",
                    ("TTR", _fmt(ttr, 4)),
                    ("MATTR (window=100)", _fmt(mattr, 4) if mattr else "N/A (<500 words)"))
            + _card("Readability",
                    ("Flesch Ease (AI: 40–65)", _fmt(ease, 1)),
                    ("FK Grade (AI: 8–12)", _fmt(grade, 1)))
            + _card("AI Vocabulary",
                    ("Density", f"{vocab_density * 100:.2f}%"),
                    ("Distinct terms found", len(vocab_terms)))
            + _card("Burstiness",
                    ("B-index", _fmt(burst_score, 3)),
                    ("", burst_interp[:50] if burst_interp else "—"))
            + "</div>"
        )

        # Top vocab terms table (up to 20)
        vocab_table_html = ""
        if vocab_terms:
            rows = "".join(
                f"<tr><td style='padding:4px 8px'>{_esc(t)}</td>"
                f"<td style='padding:4px 8px;text-align:center'>{c}</td></tr>"
                for t, c in sorted(vocab_terms.items(), key=lambda x: -x[1])[:20]
            )
            vocab_table_html = (
                '<h3 style="color:#34495e">Top AI Vocabulary Terms</h3>'
                '<table style="border-collapse:collapse;width:100%;margin-bottom:24px">'
                '<tr style="background:#2c3e50;color:#fff">'
                '<th style="padding:6px 8px;text-align:left">Term</th>'
                '<th style="padding:6px 8px">Occurrences</th></tr>'
                + rows + "</table>"
            )

        # Paragraph table
        para_rows_html = ""
        for para in paragraphs:
            if not para.get("text"):
                continue
            perp = para.get("perplexity")
            row_bg = _AI_ROW_BG if (perp is not None and perp < 50) else _NORMAL_ROW_BG
            text_html = _highlight_vocab(para["text"], para.get("vocab_hits", []))
            ease_p, grade_p = para.get("readability_ease"), para.get("fk_grade")
            vocab_count = len(para.get("vocab_hits", []))

            para_rows_html += (
                f'<tr style="background:{row_bg};vertical-align:top">'
                f'<td style="padding:6px;border:1px solid #ddd;text-align:center;'
                f'color:#888;font-size:.85em">#{para["index"] + 1}</td>'
                f'<td style="padding:6px;border:1px solid #ddd;line-height:1.5">{text_html}</td>'
                f'<td style="padding:6px;border:1px solid #ddd;text-align:center">'
                f'{_fmt(perp, 1)}</td>'
                f'<td style="padding:6px;border:1px solid #ddd;text-align:center">'
                f'{vocab_count if vocab_count else "—"}</td>'
                f'<td style="padding:6px;border:1px solid #ddd;text-align:center">'
                f'{_fmt(ease_p, 1)}</td>'
                f'<td style="padding:6px;border:1px solid #ddd;text-align:center">'
                f'{_fmt(grade_p, 1)}</td>'
                f'</tr>'
            )

        para_table_html = (
            '<h3 style="color:#34495e">Paragraph Analysis</h3>'
            '<p style="font-size:.82em;color:#888;margin-bottom:8px">'
            f'<span style="background:{_AI_ROW_BG};padding:2px 6px;border-radius:3px">'
            f'Pink rows</span> = low perplexity (AI-likely, &lt;50). '
            f'<span style="background:{_VOCAB_BG};color:{_VOCAB_FG};padding:2px 6px;'
            f'border-radius:3px;font-weight:bold">Highlighted words</span> = '
            f'AI vocabulary terms.</p>'
            '<table style="border-collapse:collapse;width:100%;margin-bottom:32px">'
            '<tr style="background:#2c3e50;color:#fff">'
            '<th style="padding:6px 8px">#</th>'
            '<th style="padding:6px 8px;text-align:left">Paragraph Text</th>'
            '<th style="padding:6px 8px">Perplexity</th>'
            '<th style="padding:6px 8px">Vocab Hits</th>'
            '<th style="padding:6px 8px">Ease</th>'
            '<th style="padding:6px 8px">FK Grade</th>'
            '</tr>'
            + para_rows_html
            + "</table>"
        )

        file_sections_html += (
            f'<section style="margin-bottom:48px">'
            f'<h2 style="border-bottom:2px solid #3498db;padding-bottom:8px;'
            f'color:#2c3e50">{filename}</h2>'
            + cards_html
            + vocab_table_html
            + para_table_html
            + "</section>"
        )

    # --- Raw findings panel ---------------------------------------------------
    raw_lines = "".join(
        f'<div style="margin:1px 0">{_esc(line)}</div>' for line in findings
    )
    raw_panel_html = (
        '<h2 style="color:#2c3e50">Raw Findings</h2>'
        '<div style="background:#1e1e1e;color:#d4d4d4;padding:16px;border-radius:8px;'
        'font-family:monospace;font-size:12px;max-height:400px;overflow-y:auto;'
        'white-space:pre-wrap">'
        + raw_lines + "</div>"
    )

    # --- Assemble full HTML ---------------------------------------------------
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AI Detection Report</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif;
      max-width: 1100px;
      margin: 0 auto;
      padding: 32px 24px 64px;
      background: #f4f6f8;
      color: #333;
      line-height: 1.5;
    }}
    h1 {{ color: #1a252f; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
    h2 {{ color: #2c3e50; }}
    table {{ width: 100%; }}
    th {{ text-align: center; }}
  </style>
</head>
<body>
  <h1>AI Detection Report</h1>
  <p style="color:#888;margin-bottom:32px">Generated: {generated_at}</p>
  {file_sections_html}
  {raw_panel_html}
</body>
</html>"""

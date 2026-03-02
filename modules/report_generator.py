
"""
report_generator.py — Generates a self-contained HTML AI analysis report.

Uses only Python stdlib (html, pathlib, datetime) — no extra dependencies.
The produced file opens correctly in every major browser on Windows, macOS, and Linux.
"""

import html
from datetime import datetime


# ── color palette ──────────────────────────────────────────────────────────────
_LABEL_STYLE = {
    'ai_suspected': ('AI Suspected',  '#E74C3C', '#FFEEEE'),
    'inconclusive':  ('Inconclusive',  '#F39C12', '#FFF9EE'),
    'human':         ('Human',         '#27AE60', '#EEFFEE'),
    'too_short':     ('Too Short',     '#AAAAAA', '#F5F5F5'),
    'error':         ('Error',         '#999999', '#F9F9F9'),
}


def _badge(label):
    """Return an inline HTML badge for a paragraph label."""
    name, color, _ = _LABEL_STYLE.get(label, ('Unknown', '#999', '#fff'))
    return (
        f'<span style="display:inline-block;padding:2px 9px;border-radius:12px;'
        f'font-size:0.75em;font-weight:600;color:#fff;background:{color};'
        f'margin-left:8px;vertical-align:middle">{html.escape(name)}</span>'
    )


def _paragraph_html(entry, index):
    """Render a single paragraph entry as an HTML block."""
    label = entry.get('label', 'error')
    _, border_color, bg_color = _LABEL_STYLE.get(label, ('#999', '#F9F9F9', '#F9F9F9'))
    text = html.escape(entry.get('text', ''))
    word_count = entry.get('word_count', 0)
    perplexity = entry.get('perplexity')

    score_html = ''
    if perplexity is not None:
        score_html = (
            f'<span style="font-size:0.78em;color:#555;margin-left:6px">'
            f'Perplexity: <strong>{perplexity}</strong></span>'
        )

    return (
        f'<div style="background:{bg_color};border-left:5px solid {border_color};'
        f'padding:12px 16px;margin:8px 0;border-radius:4px">'
        f'<div style="margin-bottom:6px">'
        f'<span style="font-size:0.78em;color:#888">#{index + 1} &nbsp;·&nbsp; '
        f'{word_count} word{"s" if word_count != 1 else ""}</span>'
        f'{_badge(label)}{score_html}'
        f'</div>'
        f'<p style="margin:0;line-height:1.6">{text}</p>'
        f'</div>'
    )


def _summary_block(paragraph_scores):
    """Build the summary stats block from a list of scored paragraph dicts."""
    total = len(paragraph_scores)
    ai_count = sum(1 for p in paragraph_scores if p['label'] == 'ai_suspected')
    inconclusive = sum(1 for p in paragraph_scores if p['label'] == 'inconclusive')
    human_count = sum(1 for p in paragraph_scores if p['label'] == 'human')
    too_short = sum(1 for p in paragraph_scores if p['label'] == 'too_short')
    scored = [p for p in paragraph_scores if p['perplexity'] is not None]
    avg_ppl = round(sum(p['perplexity'] for p in scored) / len(scored), 2) if scored else 'N/A'
    pct = round(ai_count / total * 100, 1) if total else 0

    def row(label, count, color='#333'):
        return (
            f'<tr><td style="padding:4px 12px 4px 0;color:{color}">{html.escape(label)}</td>'
            f'<td style="padding:4px 0;font-weight:600;color:{color}">{count}</td></tr>'
        )

    return (
        f'<table style="border-collapse:collapse;font-size:0.92em">'
        f'{row("Total paragraphs analysed:", total)}'
        f'{row("AI-suspected:", f"{ai_count} ({pct}%)", "#E74C3C")}'
        f'{row("Inconclusive:", inconclusive, "#F39C12")}'
        f'{row("Likely human:", human_count, "#27AE60")}'
        f'{row("Too short to score:", too_short, "#AAAAAA")}'
        f'{row("Average perplexity (scored paras):", avg_ppl)}'
        f'</table>'
    )


def _legend_html():
    return (
        '<div style="display:flex;flex-wrap:wrap;gap:10px;margin:12px 0">'
        + ''.join(
            f'<span style="display:flex;align-items:center;gap:6px">'
            f'<span style="width:14px;height:14px;border-radius:3px;'
            f'background:{border};display:inline-block"></span>'
            f'<span style="font-size:0.85em">{html.escape(name)}</span></span>'
            for name, border, _ in _LABEL_STYLE.values()
        )
        + '</div>'
    )


# ── public API ─────────────────────────────────────────────────────────────────

def generate_html_report(files):
    """
    Generate a self-contained HTML AI analysis report.

    Parameters
    ----------
    files : list[dict]
        Each entry must have:
          'filename' : str              — display name for the file
          'scores'   : list[dict]       — paragraph scores from perplexity_checker

    Returns
    -------
    str
        Complete HTML document as a string.  Write it to a .html file and open
        it with webbrowser.open(pathlib.Path(path).as_uri()).
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    file_sections = []
    for entry in files:
        filename = html.escape(entry.get('filename', 'Unknown file'))
        scores = entry.get('scores', [])

        paras_html = ''.join(
            _paragraph_html(p, i) for i, p in enumerate(scores)
        ) or '<p style="color:#999">No paragraphs could be scored for this file.</p>'

        file_sections.append(
            f'<section style="margin-bottom:48px">'
            f'<h2 style="border-bottom:2px solid #E0E0E0;padding-bottom:8px;color:#2C3E50">'
            f'{filename}</h2>'
            f'<div style="background:#F8F8F8;border-radius:8px;padding:16px 20px;margin-bottom:20px">'
            f'<h3 style="margin:0 0 10px 0;color:#2C3E50;font-size:1em">Summary</h3>'
            f'{_summary_block(scores)}'
            f'</div>'
            f'<h3 style="color:#2C3E50;font-size:1em;margin-bottom:8px">Paragraph Breakdown</h3>'
            f'{paras_html}'
            f'</section>'
        )

    all_files_html = '\n'.join(file_sections)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AI Analysis Report</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif;
      max-width: 900px;
      margin: 40px auto;
      padding: 0 24px 60px;
      color: #333;
      line-height: 1.5;
    }}
    h1 {{ color: #1A252F; margin-bottom: 4px; }}
    .meta {{ color: #888; font-size: 0.88em; margin-bottom: 32px; }}
    .legend-title {{ font-weight: 600; font-size: 0.88em; color: #555;
                     margin-bottom: 4px; }}
  </style>
</head>
<body>
  <h1>AI Analysis Report</h1>
  <p class="meta">Generated: {timestamp}</p>

  <div style="background:#F0F4F8;border-radius:8px;padding:14px 18px;margin-bottom:32px">
    <div class="legend-title">Legend</div>
    {_legend_html()}
    <p style="margin:8px 0 0;font-size:0.82em;color:#666">
      Perplexity is scored using GPT-2. Lower values indicate more predictable,
      AI-like text. Human writing typically scores &gt;&nbsp;100; AI-generated text
      typically scores &lt;&nbsp;30. Burstiness measures sentence-length variance —
      human writing is more varied.
    </p>
  </div>

  {all_files_html}
</body>
</html>"""

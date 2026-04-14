import re

_CITATION_STYLES = frozenset([
    'bibliography', 'list paragraph', 'footnote text', 'endnote text'
])
_CITATION_SIGNALS_RE = re.compile(
    r'doi:'
    r'|https?://doi\.org'
    r'|\bpp\.\s*\d'
    r'|\bvol\.\s*\d'
    r'|\bet\s+al\b'
    r'|\bRetrieved\s+from\b'
    r'|\bPublished\s+by\b',
    re.IGNORECASE
)
_YEAR_PARENS_RE  = re.compile(r'\((?:19|20)\d{2}\)')
_AUTHOR_START_RE = re.compile(r'^[A-Z][a-zA-Z\-]+,\s+[A-Z]')


def is_citation_paragraph(para):
    """Return True if this paragraph looks like a bibliographic citation entry."""
    style = para.style.name.lower() if para.style else ''
    if any(s in style for s in _CITATION_STYLES):
        return True
    text = para.text
    signals = len(_CITATION_SIGNALS_RE.findall(text))
    if _YEAR_PARENS_RE.search(text):
        signals += 1
    if _AUTHOR_START_RE.match(text):
        signals += 1
    return signals >= 2

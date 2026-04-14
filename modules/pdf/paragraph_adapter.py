"""
Thin adapter that wraps PDF plain-text paragraphs in a python-docx-compatible
interface so all existing content checkers (readability, perplexity, vocabulary,
stats) can be reused without modification.

PdfParagraph exposes:
  .text  — the paragraph text
  .style — a stub with .name == '' (no Word styles in PDFs)

PdfDocument exposes:
  .paragraphs — list[PdfParagraph]
"""


class _FakeStyle:
    name = ''


class PdfParagraph:
    style = _FakeStyle()

    def __init__(self, text):
        self.text = text


class PdfDocument:
    def __init__(self, paragraphs):
        self.paragraphs = paragraphs


def build_pdf_document(full_text):
    """
    Split extracted PDF text into paragraph blocks and wrap in a PdfDocument.

    Paragraphs are separated by blank lines (\n\n). Single line-breaks within a
    block are collapsed to spaces to avoid sentence-splitting artifacts.
    """
    blocks = full_text.split('\n\n')
    paras = []
    for block in blocks:
        text = ' '.join(block.split())   # normalise whitespace / line breaks
        if text:
            paras.append(PdfParagraph(text))
    return PdfDocument(paras)

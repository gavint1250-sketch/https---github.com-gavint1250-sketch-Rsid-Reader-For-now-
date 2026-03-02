
import os
import math
import statistics

# GPT-2 model and tokenizer are cached at module level so batch processing
# only pays the load cost once.
_gpt2_model = None
_gpt2_tokenizer = None

# Per-paragraph scores from the most recent analysis, for the report generator.
_cached_paragraph_scores = []


def _get_libs_dir():
    """Return the app-local libs/ directory (two levels above modules/content/)."""
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(here, '..', '..', 'libs')


def _get_document_text(document):
    """Concatenate all non-empty paragraph text from a docx Document."""
    return ' '.join(p.text.strip() for p in document.paragraphs if p.text.strip())


def _compute_burstiness(document):
    """
    Compute the burstiness index B = (σ − μ) / (σ + μ) over sentence word-counts.

    Interpretation:
      B > 0.4   → High burstiness — consistent with human writing
      -0.1–0.4  → Moderate burstiness — inconclusive
      B < -0.1  → Low burstiness — consistent with AI-generated text
    """
    try:
        import nltk

        nltk_data_dir = os.path.join(_get_libs_dir(), 'nltk_data')
        os.makedirs(nltk_data_dir, exist_ok=True)
        if nltk_data_dir not in nltk.data.path:
            nltk.data.path.insert(0, nltk_data_dir)

        try:
            nltk.data.find('tokenizers/punkt_tab')
        except LookupError:
            nltk.download('punkt_tab', download_dir=nltk_data_dir, quiet=True)

        text = _get_document_text(document)
        sentences = nltk.sent_tokenize(text)
        lengths = [len(s.split()) for s in sentences if s.strip()]

        if len(lengths) < 2:
            return None, "Not enough sentences to compute burstiness."

        mean = statistics.mean(lengths)
        std = statistics.stdev(lengths)
        denom = std + mean

        if denom == 0:
            return None, "Cannot compute burstiness (all sentences identical length)."

        score = round((std - mean) / denom, 3)

        if score > 0.4:
            interpretation = "High burstiness — consistent with human writing"
        elif score < -0.1:
            interpretation = "Low burstiness — consistent with AI-generated text"
        else:
            interpretation = "Moderate burstiness — inconclusive"

        return score, interpretation

    except Exception as e:
        return None, f"Burstiness error: {e}"


def _load_gpt2():
    """
    Load GPT-2 model and tokenizer on first call, caching them in module globals.
    Model weights are stored in libs/hf_cache/ via the HF_HOME env var set in Main.py.
    Returns True on success, False on failure.
    """
    global _gpt2_model, _gpt2_tokenizer
    if _gpt2_model is not None:
        return True
    try:
        from transformers import GPT2LMHeadModel, GPT2TokenizerFast
        cache_dir = os.path.join(_get_libs_dir(), 'hf_cache')
        _gpt2_tokenizer = GPT2TokenizerFast.from_pretrained('gpt2', cache_dir=cache_dir)
        _gpt2_model = GPT2LMHeadModel.from_pretrained('gpt2', cache_dir=cache_dir)
        _gpt2_model.eval()
        return True
    except Exception:
        return False


def _score_paragraphs_internal(document):
    """
    Score every paragraph in the document individually using GPT-2 perplexity.

    Returns a list of dicts:
      {
        'text':        str,         paragraph text
        'word_count':  int,
        'perplexity':  float|None,  GPT-2 perplexity (None if too short / error)
        'label':       str          'ai_suspected' | 'inconclusive' | 'human' |
                                    'too_short'    | 'error'
      }
    """
    import torch

    results = []
    for para in document.paragraphs:
        text = para.text.strip()
        if not text:
            continue

        words = text.split()
        word_count = len(words)

        if word_count < 5:
            results.append({
                'text': text,
                'word_count': word_count,
                'perplexity': None,
                'label': 'too_short',
            })
            continue

        try:
            encodings = _gpt2_tokenizer(
                text,
                return_tensors='pt',
                truncation=True,
                max_length=1024,
            )
            input_ids = encodings.input_ids
            with torch.no_grad():
                outputs = _gpt2_model(input_ids, labels=input_ids)
                score = round(math.exp(outputs.loss.item()), 2)

            if score < 30:
                label = 'ai_suspected'
            elif score > 100:
                label = 'human'
            else:
                label = 'inconclusive'

            results.append({
                'text': text,
                'word_count': word_count,
                'perplexity': score,
                'label': label,
            })

        except Exception as e:
            results.append({
                'text': text,
                'word_count': word_count,
                'perplexity': None,
                'label': 'error',
            })

    return results


def get_cached_paragraph_scores():
    """Return the paragraph scores from the most recent analysis (copy)."""
    return list(_cached_paragraph_scores)


def check_perplexity_and_burstiness(document):
    """
    Run perplexity and burstiness checks on a docx Document object.

    Computes per-paragraph GPT-2 perplexity scores (cached in _cached_paragraph_scores
    for the report generator) and derives summary statistics for GUI display.

    Returns a list of finding strings tagged [PERPLEXITY] and [BURST].
    """
    global _cached_paragraph_scores
    findings = []

    # Burstiness — lightweight; uses only NLTK sentence tokenisation
    b_score, b_interp = _compute_burstiness(document)
    if b_score is not None:
        findings.append(f"[BURST] Score: {b_score} — {b_interp}")
    else:
        findings.append(f"[BURST] {b_interp}")

    # Per-paragraph perplexity — requires GPT-2
    if not _load_gpt2():
        _cached_paragraph_scores = []
        findings.append(
            "[PERPLEXITY] GPT-2 model could not be loaded. "
            "Ensure transformers and torch are installed in libs/."
        )
        return findings

    _cached_paragraph_scores = _score_paragraphs_internal(document)

    # Derive summary stats from the per-paragraph cache
    scored = [p for p in _cached_paragraph_scores if p['perplexity'] is not None]
    total = len(_cached_paragraph_scores)
    ai_count = sum(1 for p in _cached_paragraph_scores if p['label'] == 'ai_suspected')

    if scored:
        avg = round(sum(p['perplexity'] for p in scored) / len(scored), 2)
        findings.append(
            f"[PERPLEXITY] {ai_count} of {total} paragraph(s) flagged as AI-suspected "
            f"(avg score: {avg}) — download AI Report for full breakdown"
        )
    else:
        findings.append("[PERPLEXITY] No paragraphs long enough to score.")

    return findings

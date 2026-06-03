"""GloVe vocabulary loading and out-of-vocabulary (OOV) coverage analysis.

The promotor flagged that GloVe can struggle with colloquial words. These
helpers quantify how many tokens in the cleaned corpus fall outside the GloVe
vocabulary, so the result can be reported rather than buried in a notebook.

Tokenization matches the planned model side (CLAUDE.md): lower-case + `[a-z]+`.
"""

import re
from collections import Counter
from pathlib import Path

import pandas as pd

TOKEN_RE = re.compile(r"[a-z]+")


def load_glove_vocab(path: Path) -> set[str]:
    """Load the set of words present in a GloVe text file.

    Args:
        path: Path to a GloVe `.txt` file (each line: ``word v1 v2 ...``).

    Returns:
        Set of vocabulary words (first whitespace-delimited token per line).
    """
    vocab: set[str] = set()
    with path.open(encoding="utf-8") as f:
        for line in f:
            vocab.add(line.split(" ", 1)[0])
    return vocab


def tokenize(text: str) -> list[str]:
    """Lower-case and split into `[a-z]+` tokens (same scheme as the model)."""
    return TOKEN_RE.findall(text.lower())


def oov_report(
    texts: pd.Series, glove_vocab: set[str], top_n: int = 20
) -> dict[str, object]:
    """Compute out-of-vocabulary statistics for a corpus against GloVe.

    Args:
        texts: Series of document strings to analyse.
        glove_vocab: Vocabulary returned by ``load_glove_vocab``.
        top_n: Number of most frequent OOV word types to return.

    Returns:
        Dict with token/type counts, OOV counts, their percentages, and a
        ``top_oov`` list of ``(word, frequency)`` tuples sorted by frequency.
    """
    freq: Counter[str] = Counter()
    for text in texts.fillna(""):
        freq.update(tokenize(text))

    n_types = len(freq)
    n_tokens = sum(freq.values())
    oov_types = [w for w in freq if w not in glove_vocab]
    oov_token_count = sum(freq[w] for w in oov_types)

    top_oov = sorted(
        ((w, freq[w]) for w in oov_types), key=lambda wc: wc[1], reverse=True
    )[:top_n]

    return {
        "n_types": n_types,
        "n_tokens": n_tokens,
        "oov_types": len(oov_types),
        "oov_tokens": oov_token_count,
        "oov_type_pct": round(len(oov_types) / n_types * 100, 2) if n_types else 0.0,
        "oov_token_pct": round(oov_token_count / n_tokens * 100, 2)
        if n_tokens
        else 0.0,
        "top_oov": top_oov,
    }

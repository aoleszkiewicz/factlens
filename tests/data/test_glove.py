"""Tests for GloVe vocab loading and OOV coverage reporting."""

from pathlib import Path

import pandas as pd

from src.data.glove import load_glove_vocab, oov_report, tokenize


def test_tokenize_scheme() -> None:
    # Lower-cases and keeps only [a-z]+ runs; digits/punct split tokens.
    assert tokenize("Hello, WORLD! 2024 covid-19") == [
        "hello",
        "world",
        "covid",
    ]


def test_load_glove_vocab(tmp_path: Path) -> None:
    f = tmp_path / "glove.txt"
    f.write_text("the 0.1 0.2 0.3\ncat 0.4 0.5 0.6\n", encoding="utf-8")
    vocab = load_glove_vocab(f)
    assert vocab == {"the", "cat"}


def test_oov_report_counts() -> None:
    texts = pd.Series(["the cat the dog", "the zzz"])
    vocab = {"the", "cat", "dog"}
    rep = oov_report(texts, vocab, top_n=5)
    # Types: the, cat, dog, zzz -> 4; only zzz is OOV.
    assert rep["n_types"] == 4
    assert rep["oov_types"] == 1
    # Tokens: the x3, cat, dog, zzz -> 6; OOV tokens = 1 (zzz).
    assert rep["n_tokens"] == 6
    assert rep["oov_tokens"] == 1
    assert rep["top_oov"] == [("zzz", 1)]
    assert rep["oov_type_pct"] == 25.0


def test_oov_report_empty_series() -> None:
    rep = oov_report(pd.Series([], dtype=str), {"the"})
    assert rep["n_types"] == 0
    assert rep["oov_type_pct"] == 0.0
    assert rep["oov_token_pct"] == 0.0

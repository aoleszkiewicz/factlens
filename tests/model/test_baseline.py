"""Tests for the TF-IDF + Logistic Regression baseline.

Trains on a tiny, linearly separable toy corpus so the assertions are about
contract and shape (pipeline structure, metric keys/ranges, feature output),
not about real-world accuracy.
"""

import pandas as pd
from sklearn.pipeline import Pipeline

from src.model.baseline import build_baseline, evaluate, top_features

# Toy corpus: "real" vocabulary vs "fake" vocabulary, perfectly separable.
_REAL = ["senate passed the bill", "economy grew this quarter", "court issued ruling"]
_FAKE = [
    "shocking secret they hide",
    "miracle cure doctors hate",
    "wake up sheeple now",
]
_X = pd.Series(_REAL + _FAKE)
_Y = pd.Series([1, 1, 1, 0, 0, 0])


def _fitted() -> Pipeline:
    pipe = build_baseline(max_features=100, ngram_range=(1, 1), min_df=1)
    pipe.fit(_X, _Y)
    return pipe


def test_build_baseline_structure() -> None:
    pipe = build_baseline()
    assert list(pipe.named_steps) == ["tfidf", "clf"]


def test_evaluate_keys_and_ranges() -> None:
    metrics = evaluate(_fitted(), _X, _Y)
    expected = {"accuracy", "precision", "recall", "f1", "roc_auc", "confusion_matrix"}
    assert set(metrics) == expected
    for key in ("accuracy", "precision", "recall", "f1", "roc_auc"):
        assert 0.0 <= metrics[key] <= 1.0
    # Separable toy data -> perfect fit on the training set.
    assert metrics["accuracy"] == 1.0
    cm = metrics["confusion_matrix"]
    assert len(cm) == 2 and len(cm[0]) == 2


def test_top_features_shape() -> None:
    real, fake = top_features(_fitted(), n=3)
    assert len(real) == 3
    assert len(fake) == 3
    # Real features carry positive weight, fake features negative.
    assert all(coef > 0 for _, coef in real)
    assert all(coef < 0 for _, coef in fake)

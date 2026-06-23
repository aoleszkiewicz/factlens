"""Tests for the TF-IDF -> MLP classifier.

Trains on a tiny, linearly separable toy corpus so the assertions are about
contract and shape (forward shape, metric keys/ranges, that the training loop
actually learns, determinism), not about real-world accuracy. Everything runs
on CPU and stays small enough to be fast.
"""

import numpy as np
import pandas as pd
import torch

from src.model.baseline import make_tfidf_vectorizer
from src.model.mlp import (
    MLPClassifier,
    TfidfDataset,
    evaluate_mlp,
    predict_proba,
    set_seed,
    train_mlp,
)

# Toy corpus: "real" vocabulary vs "fake" vocabulary, perfectly separable.
_REAL = ["senate passed the bill", "economy grew this quarter", "court issued ruling"]
_FAKE = [
    "shocking secret they hide",
    "miracle cure doctors hate",
    "wake up sheeple now",
]
_X = pd.Series(_REAL + _FAKE)
_Y = pd.Series([1, 1, 1, 0, 0, 0])


def _vectorizer_and_datasets() -> tuple:
    """Fit the shared vectorizer on the toy corpus and build a dataset."""
    vectorizer = make_tfidf_vectorizer(max_features=100, ngram_range=(1, 1), min_df=1)
    features = vectorizer.fit_transform(_X)
    dataset = TfidfDataset(features, _Y)
    return vectorizer, features, dataset


def _trained() -> tuple:
    """Train an MLP to convergence on the toy corpus (train == val here)."""
    set_seed(0)
    vectorizer, features, dataset = _vectorizer_and_datasets()
    model = MLPClassifier(input_dim=features.shape[1], hidden_dims=(16,))
    history = train_mlp(
        model,
        dataset,
        dataset,
        epochs=50,
        batch_size=4,
        lr=1e-2,
        patience=50,
        device="cpu",
    )
    return vectorizer, model, history


def test_forward_shape() -> None:
    _, features, _ = _vectorizer_and_datasets()
    model = MLPClassifier(input_dim=features.shape[1], hidden_dims=(8,))
    batch = torch.zeros((4, features.shape[1]))
    assert model(batch).shape == (4, 1)


def test_training_learns_toy_data() -> None:
    _, _, history = _trained()
    # Loss should fall from the first to the last recorded epoch.
    assert history["train_loss"][-1] < history["train_loss"][0]
    # Separable toy data -> the loop should reach a perfect validation F1.
    assert max(history["val_f1"]) == 1.0


def test_evaluate_keys_and_ranges() -> None:
    vectorizer, model, _ = _trained()
    metrics = evaluate_mlp(model, vectorizer, _X, _Y, device="cpu")
    expected = {"accuracy", "precision", "recall", "f1", "roc_auc", "confusion_matrix"}
    assert set(metrics) == expected
    for key in ("accuracy", "precision", "recall", "f1", "roc_auc"):
        assert 0.0 <= metrics[key] <= 1.0
    cm = metrics["confusion_matrix"]
    assert len(cm) == 2 and len(cm[0]) == 2


def test_predict_proba_shape_and_range() -> None:
    _, model, _ = _trained()
    _, _, dataset = _vectorizer_and_datasets()
    proba = predict_proba(model, dataset, device="cpu")
    assert proba.shape == (len(_X),)
    assert np.all((proba >= 0.0) & (proba <= 1.0))


def test_determinism() -> None:
    vectorizer_a, model_a, _ = _trained()
    proba_a = evaluate_mlp(model_a, vectorizer_a, _X, _Y, device="cpu")
    vectorizer_b, model_b, _ = _trained()
    proba_b = evaluate_mlp(model_b, vectorizer_b, _X, _Y, device="cpu")
    assert proba_a == proba_b

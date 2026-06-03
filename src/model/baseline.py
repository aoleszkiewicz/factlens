"""TF-IDF + Logistic Regression baseline for fake-news classification.

A classic, interpretable reference point for the target BiLSTM + Attention
model (added per promotor feedback). Operates on the same `text` column and
label convention (1 = Real, 0 = Fake) as the rest of the project, reading the
CSV splits written by ``src.data.splits.make_splits``.

The logistic-regression coefficients double as explainability: ``top_features``
surfaces the n-grams that push a prediction toward Real vs Fake.
"""

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline

from src.data.splits import RANDOM_STATE


def build_baseline(
    max_features: int = 50_000,
    ngram_range: tuple[int, int] = (1, 2),
    min_df: int = 5,
    C: float = 1.0,  # noqa: N803 — sklearn hyperparameter name
    random_state: int = RANDOM_STATE,
) -> Pipeline:
    """Build a TF-IDF + Logistic Regression pipeline.

    Args:
        max_features: Vocabulary cap for the TF-IDF vectorizer.
        ngram_range: Lower/upper bound on n-gram size.
        min_df: Minimum document frequency for a term to be kept.
        C: Inverse regularization strength for the logistic regression.
        random_state: Seed for reproducibility.

    Returns:
        An unfitted sklearn ``Pipeline`` with steps ``tfidf`` and ``clf``.
    """
    return Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(
                    max_features=max_features,
                    ngram_range=ngram_range,
                    min_df=min_df,
                    sublinear_tf=True,
                    strip_accents="unicode",
                ),
            ),
            (
                "clf",
                LogisticRegression(
                    C=C,
                    max_iter=1000,
                    random_state=random_state,
                ),
            ),
        ]
    )


def evaluate(pipeline: Pipeline, X: pd.Series, y: pd.Series) -> dict[str, object]:  # noqa: N803 — sklearn convention
    """Evaluate a fitted pipeline on a labelled set.

    Args:
        pipeline: A fitted baseline pipeline.
        X: Series of document strings.
        y: Series of binary labels (1 = Real, 0 = Fake).

    Returns:
        Dict with accuracy, precision, recall, f1, roc_auc and the 2x2
        confusion matrix (as a nested list, rows = true, cols = predicted).
    """
    y_pred = pipeline.predict(X)
    y_proba = pipeline.predict_proba(X)[:, 1]
    return {
        "accuracy": round(float(accuracy_score(y, y_pred)), 4),
        "precision": round(float(precision_score(y, y_pred)), 4),
        "recall": round(float(recall_score(y, y_pred)), 4),
        "f1": round(float(f1_score(y, y_pred)), 4),
        "roc_auc": round(float(roc_auc_score(y, y_proba)), 4),
        "confusion_matrix": confusion_matrix(y, y_pred).tolist(),
    }


def top_features(
    pipeline: Pipeline, n: int = 20
) -> tuple[list[tuple[str, float]], list[tuple[str, float]]]:
    """Return the n-grams most indicative of each class (explainability).

    Uses the logistic-regression coefficients over the TF-IDF vocabulary.
    Positive coefficients push toward class 1 (Real), negative toward class 0
    (Fake).

    Args:
        pipeline: A fitted baseline pipeline.
        n: Number of top features to return per class.

    Returns:
        Tuple ``(real, fake)``; each is a list of ``(term, coefficient)``
        sorted by descending strength for that class.
    """
    vectorizer: TfidfVectorizer = pipeline.named_steps["tfidf"]
    clf: LogisticRegression = pipeline.named_steps["clf"]

    feature_names = vectorizer.get_feature_names_out()
    coefs = clf.coef_[0]

    order = np.argsort(coefs)
    fake = [(str(feature_names[i]), float(coefs[i])) for i in order[:n]]
    real = [(str(feature_names[i]), float(coefs[i])) for i in order[-n:][::-1]]
    return real, fake

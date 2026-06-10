"""Tests for the stratified train/val/test split helper.

Guarantees that matter for the thesis: correct proportions (60/20/20), class
balance preserved in every split, no row leakage across splits, and determinism
for a fixed ``random_state``.
"""

from pathlib import Path

import pandas as pd

from src.data.splits import make_splits


def _make_df(n: int = 1000) -> pd.DataFrame:
    # 60% Real (1), 40% Fake (0); unique id per row to detect leakage.
    labels = [1] * int(n * 0.6) + [0] * (n - int(n * 0.6))
    return pd.DataFrame({"id": range(n), "label": labels})


def test_split_proportions() -> None:
    df = _make_df(1000)
    train, test, val = make_splits(df, write_to_file=False)
    assert len(train) == 600
    assert len(test) == 200
    assert len(val) == 200


def test_stratification_preserved() -> None:
    df = _make_df(1000)
    base = df["label"].mean()
    for split in make_splits(df, write_to_file=False):
        assert abs(split["label"].mean() - base) < 0.02


def test_no_row_leakage_between_splits() -> None:
    df = _make_df(1000)
    train, test, val = make_splits(df, write_to_file=False)
    ids = [set(s["id"]) for s in (train, test, val)]
    assert ids[0] & ids[1] == set()
    assert ids[0] & ids[2] == set()
    assert ids[1] & ids[2] == set()
    assert ids[0] | ids[1] | ids[2] == set(df["id"])


def test_determinism_for_fixed_seed() -> None:
    df = _make_df(500)
    a = make_splits(df, write_to_file=False, random_state=7)
    b = make_splits(df, write_to_file=False, random_state=7)
    for sa, sb in zip(a, b, strict=True):
        pd.testing.assert_frame_equal(sa, sb)


def test_indices_are_reset() -> None:
    df = _make_df(500)
    for split in make_splits(df, write_to_file=False):
        assert list(split.index) == list(range(len(split)))


def test_write_to_file(tmp_path: Path) -> None:
    df = _make_df(200)
    make_splits(df, output_dir=tmp_path, write_to_file=True)
    for name in ("train", "test", "val"):
        assert (tmp_path / f"{name}.csv").exists()

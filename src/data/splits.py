"""Module for creating train/val/test splits."""

from pathlib import Path
from typing import cast

import pandas as pd
from sklearn.model_selection import (
    train_test_split,
)

from src.config import RANDOM_STATE
from src.paths import DATA_SPLITS


def make_splits(
    df: pd.DataFrame,
    output_dir: Path = DATA_SPLITS,
    write_to_file: bool = True,
    random_state: int = RANDOM_STATE,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Split a labelled DataFrame into stratified train, test, and val sets.

    Args:
        df: DataFrame with a 'label' column used for stratification.
        output_dir: Directory to write CSV files when write_to_file is True.
        write_to_file: Write each split to a CSV file in output_dir.
        random_state: Seed for reproducible splits.

    Returns:
        Tuple of (train, test, val) DataFrames with reset indices.
    """
    _train_full, _test = train_test_split(
        df, test_size=0.2, stratify=df["label"], random_state=random_state
    )
    train_full = cast("pd.DataFrame", _train_full)

    _train, _val = train_test_split(
        train_full,
        test_size=0.25,
        stratify=train_full["label"],
        random_state=random_state,
    )

    train = cast("pd.DataFrame", _train).reset_index(drop=True)
    test = cast("pd.DataFrame", _test).reset_index(drop=True)
    val = cast("pd.DataFrame", _val).reset_index(drop=True)

    if write_to_file:
        for name, split in [("train", train), ("test", test), ("val", val)]:
            split.to_csv(output_dir / f"{name}.csv", index=False)

    return train, test, val

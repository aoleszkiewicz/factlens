from pathlib import Path

from sklearn.model_selection import train_test_split

import os
import pandas as pd

from src.paths import DATA_SPLITS

RANDOM_STATE = int(os.environ.get("RANDOM_STATE", 42))


def make_splits(
    df: pd.DataFrame,
    output_dir: Path = DATA_SPLITS,
    write_to_file: bool = True,
    random_state: int = RANDOM_STATE,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    y = df["label"]

    train, test = train_test_split(
        df, test_size=0.2, train_size=0.8, stratify=y, random_state=random_state
    )

    y = train["label"]

    train, val = train_test_split(
        train, test_size=0.25, train_size=0.75, stratify=y, random_state=random_state
    )

    for name, split in [("train", train), ("test", test), ("val", val)]:
        split = split.reset_index(drop=True)

        if write_to_file:
            split.to_csv(output_dir / f"{name}.csv", index=False)

    return (train, test, val)

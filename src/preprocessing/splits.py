from pathlib import Path
from sklearn.model_selection import train_test_split

import os
import pandas as pd

RANDOM_STATE = os.environ.get("RANDOM_STATE")


def make_splits(
    df: pd.DataFrame,
    output_dir="data/processed/splited",
    write_to_file=True,
    random_state: int = RANDOM_STATE,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    y = df["label"]

    train, test = train_test_split(
        df, test_size=0.2, train_size=0.8, stratify=y, random_state=random_state
    )

    y = train["label"]

    train, val = train_test_split(
        train, test_size=0.25, train_size=0.75, stratify=y, random_state=random_state
    )

    for name, split in [("train", train), ("test", test), ("val", val)]:
        split.reset_index(drop=True)

        if write_to_file:
            split.to_parquet(output_dir / f"{name}.parquet", index=False)

    return (train, test, val)

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_RAW = REPO_ROOT / "data" / "raw"
DATA_PROCESSED = REPO_ROOT / "data" / "processed"
DATA_SPLITS = DATA_PROCESSED / "splited"
DATA_GLOVE = REPO_ROOT / "data" / "glove"

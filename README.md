# factlens

Binary **fake-news classifier** on the Kaggle *Fake and Real News Dataset*
(`clmentbisaillon/fake-and-real-news-dataset`). BSc thesis (SSN — sieci neuronowe).
Target architecture: **BiLSTM + Attention** with **GloVe 300d** embeddings, in strict
PyTorch. A **TF-IDF + Logistic Regression** baseline is already implemented.

Label convention: **`1 = Real`, `0 = Fake`**. Only the `text` column is used for
modelling (`title`, `subject`, `date` are dropped as leakage).

## Setup

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync                  # install deps from uv.lock
cp example.env .env      # RANDOM_STATE etc.
```

External assets (not in the repo):
- **Kaggle dataset** — fetched at notebook runtime via `kagglehub`; needs Kaggle
  credentials configured.
- **GloVe 6B 300d** — place at `data/glove/glove_2024_wikigiga_300d.txt`
  (see <https://nlp.stanford.edu/projects/glove/>).

## Pipeline

Run the notebooks under `notebooks/explore/` in order, then `notebooks/report/`:

1. `01_eda.ipynb` — EDA on raw `True.csv` / `Fake.csv`.
2. `02_leakage.ipynb` — leakage analysis → regex marker list.
3. `03_cleaning.ipynb` — applies `clean_text` + `filter_short_articles` → `data/processed/news_cleaned.csv`.
4. `04_post_cleaning.ipynb` — sanity checks on the cleaned corpus.
5. `05_splits.ipynb` — `make_splits` → `data/processed/splited/{train,val,test}.csv`.
6. `report/01_raport.ipynb` — consolidated thesis report.
7. `report/02_baseline_tfidf_lr.ipynb` — baseline metrics + explainability.

Reusable logic lives in `src/` (imported by the notebooks):

| Module | Responsibility |
| --- | --- |
| `src/paths.py` | Repo-relative data paths (single source of truth). |
| `src/data/cleaning.py` | Regex cleaning pipeline + short-article filter. |
| `src/data/splits.py` | Stratified train/val/test split. |
| `src/data/glove.py` | GloVe vocab loading + OOV coverage report. |
| `src/model/baseline.py` | TF-IDF + LogReg baseline (build / evaluate / top features). |

## Data layout

```
data/raw/                 True.csv, Fake.csv          (kagglehub)
data/processed/           news_cleaned.csv
data/processed/splited/   train.csv, val.csv, test.csv
data/glove/               glove_2024_wikigiga_300d.txt (not tracked)
```

## Development

```bash
uv run pytest            # unit tests (src cleaning / splits / glove / baseline)
uv run ruff check .      # lint
uv run ruff format .     # format
uv run jupyter lab       # notebooks against the project venv
```

A pre-commit hook (`uv run pre-commit install`) and a GitHub Actions workflow run
ruff + pytest to keep the tree green.

More detail: thesis brief in `docs/project_description_ssn.md`; contributor/agent
guidance in `CLAUDE.md`.
